"""
Handles both the TTS generation and text generation at the same time, streamed to be faster.
"""
import sounddevice as sd
import queue
from google.cloud import texttospeech
import threading
model = 'moonshotai/Kimi-K2-Instruct-0905' # TODO: have a router to use groq/compound for search results and stuff
system_prompt = open("src/utils/system_prompt.txt").read()

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

def stream_response_to_tts(groq_client, context):
    """
    Request a response from Groq, streaming the result to tts.py
    
    :param client: The client for the script to connect to.
    :param context: The context for the model, including the current question.
    """

    completion = groq_client.chat.completions.create(
        model=model,
        messages =
        [{
            'role': 'system',
            'content': system_prompt,
        }] + context, # Just add all the context passed in! Very easy :D
        temperature=0.6,
        max_completion_tokens=4096,
        top_p=1,
        stream=True,
        stop=None,
    )

    for chunk in completion:
        q.put(chunk.choices[0].delta.content or "")
        print(chunk.choices[0].delta.content or "", end="", flush=True)
    
    q.put(None)

def stream_data(groq_client, google_client, context):
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
                print("Empty queue! Telling TTS to just say nothing so it doesn't error out.", flush=True)
                yield texttospeech.StreamingSynthesizeRequest(
                    input=texttospeech.StreamingSynthesisInput(markup="")
                )
    
    q = queue.Queue()
    response_thread = threading.Thread(target=stream_response_to_tts, args=(groq_client, context))
    response_thread.start()
    
    print('Started TTS!', flush=True)

    streaming_responses = google_client.streaming_synthesize(request_generator())

    with sd.RawOutputStream(samplerate=audio_config.sample_rate_hertz, channels=1, dtype='int16') as stream: # And this is to actually record the input in general.
        for response in streaming_responses:
            stream.write(response.audio_content)