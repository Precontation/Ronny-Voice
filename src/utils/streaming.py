# Copyright 2026 The Ronny Voice Foundation

"""
Handles both the TTS generation and text generation at the same time, streamed to be faster.
"""
import json
import sounddevice as sd
import queue
from google.cloud import texttospeech
import threading
from datetime import datetime, timezone
from rich import console

# moonshotai/Kimi-K2-Instruct-0905
model = 'moonshotai/Kimi-K2-Instruct-0905' # TODO: have a router to use groq/compound for search results and stuff
system_prompt = open("src/utils/system_prompt.txt").read()
utc_dt = datetime.now(timezone.utc) # UTC time
dt = utc_dt.astimezone() # local time

# Note: the voice can also be specified by name.
# Names of voices can be retrieved with client.list_voices().
voice = texttospeech.VoiceSelectionParams(
    name="en-US-Chirp3-HD-Puck",
    language_code="en-US",
)

audio_config = texttospeech.AudioConfig(
    audio_encoding=texttospeech.AudioEncoding.LINEAR16,
    sample_rate_hertz=24000,
    speaking_rate = 2 # 1.0 is default
)

q = queue.Queue()

from .tools import calculate, dt, weather, clipboard

# Map function names to implementations
available_functions = {
    "calculate": calculate.calculate,
    "get_weather_now": weather.get_weather_now,
    "get_weather_today": weather.get_weather_today,
    "get_forcast": weather.get_weather_forecast,
    "get_datetime": dt.get_datetime,
    "get_clipboard": clipboard.get_clipboard
}

available_tools = [calculate.tool_schema, weather.today_tool_schema, weather.now_tool_schema, weather.forcast_tool_schema, dt.tool_schema, clipboard.tool_schema]


def execute_tool_call(tool_call):
    """Parse and execute a single tool call"""
    function_name = tool_call.function.name
    function_to_call = available_functions[function_name]
    function_args = json.loads(tool_call.function.arguments)
    
    # Call the function with unpacked arguments
    return function_to_call(**function_args)

def call_with_tools_and_retry(client, messages, tools, console: console.Console, max_retries=3):
    """Call model with tools, retrying with adjusted temperature on failure"""
    
    # Start with moderate temperature
    temperature = 1.0
    
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                tools=tools,
                tool_choice="auto",
                temperature=temperature
            )
            return response
        except Exception as e:
            # Check if this is a tool call generation error
            if hasattr(e, 'status_code') and e.status_code == 400: # type: ignore
                if attempt < max_retries - 1:
                    # Decrease temperature for next attempt to reduce hallucinations
                    temperature = max(temperature - 0.2, 0.2)
                    console.print(f"Tool call failed, retrying with lower temperature {temperature}")
                    continue
            # If not a tool call error or out of retries, raise
            raise e
    raise Exception("Failed to generate valid tool calls after retries")

def stream_response_to_tts(groq_client, context, console: console.Console):
    """
    Request a response from Groq, streaming the result to tts.py
    
    :param client: The client for the script to connect to.
    :param context: The context for the model, including the current question.
    """

    try:
        response = call_with_tools_and_retry(groq_client, context, available_tools, console, 4)

        if response.choices[0].message.tool_calls:
            # 3. Execute each tool call (using the helper function from step 2)
            for tool_call in response.choices[0].message.tool_calls:
                console.print(f"Tool being used: {tool_call.function.name}")
                function_response = execute_tool_call(tool_call)
                # Add tool result to messages
                context.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": tool_call.function.name,
                    "content": str(function_response)
                })
    except Exception as e:
        context.append({
            "role": "tool",
            "tool_call_id": "0",
            "name": "Tool error handler",
            "content": "Tool error!"
        })
        console.print("Model tool had an error: " + str(e))

    # 4. Send results back and get final response
    final = groq_client.chat.completions.create(
        model=model,
        messages =
        [{
            'role': 'system',
            'content': system_prompt,
        }] + context, # Just add all the context passed in! Very easy :D
        temperature=0.6,
        max_completion_tokens=300, # System prompt says it only has 200 tokens, so we just lie just in case to make it so it won't cut off
        top_p=1,
        stream=True,
        stop=None,
    )

    for chunk in final:
        q.put(chunk.choices[0].delta.content or "")
        console.print(chunk.choices[0].delta.content or "", end="")
    
    q.put(None)

def stream_data(groq_client, google_client, context, console: console.Console):
    global q

    """Synthesizes speech from a stream of input text."""
    from google.cloud import texttospeech

    # See https://cloud.google.com/text-to-speech/docs/voices for all voices.
    streaming_config = texttospeech.StreamingSynthesizeConfig(
        voice=voice
    )

    # Set the config for your stream. The first request must contain your config, and then each subsequent request must contain text.
    config_request = texttospeech.StreamingSynthesizeRequest(
        streaming_config=streaming_config
    )

    # Request generator. Consider using Gemini or another LLM with output streaming as a generator.
    def request_generator():
        yield config_request
        is_tts_running = True
        
        while is_tts_running:
            try:
                data = q.get(timeout=3) # Get the data from the queue!
                if data == None:
                    is_tts_running = False
                    return
                yield texttospeech.StreamingSynthesizeRequest(
                    input=texttospeech.StreamingSynthesisInput(markup=data)
                )
            except queue.Empty:
                console.print("Empty queue! Telling TTS to just say nothing so it doesn't error out.")
                yield texttospeech.StreamingSynthesizeRequest(
                    input=texttospeech.StreamingSynthesisInput(markup="")
                )
    
    q = queue.Queue()
    response_thread = threading.Thread(target=stream_response_to_tts, args=(groq_client, context, console))
    response_thread.start()
    
    console.print('Started TTS!', )

    streaming_responses = google_client.streaming_synthesize(request_generator())

    with sd.RawOutputStream(samplerate=audio_config.sample_rate_hertz, channels=1, dtype='int16') as stream: # And this is to actually record the input in general.
        for response in streaming_responses:
            stream.write(response.audio_content)