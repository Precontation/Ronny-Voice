# Copyright 2026 The Ronny Voice Foundation

DEMO_MODE = True # Make this false if on a Raspberry Pi

# Other scripts
# import pvporcupine
import pvporcupine
from utils import recorder, transcribe, streaming

# Environment variables
from dotenv import load_dotenv
import os

# TUI stuff
from rich import print
from rich.console import Console
from rich_gradient import Gradient

# Loading files
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent

load_dotenv()

# Google stuff (text-to-speech)
from google.cloud import texttospeech
google_client = texttospeech.TextToSpeechClient() # Doing this here to prevent a race condition with load_dotenv()

# Groq stuff (text-to-text and speech-to-text)
from groq import Groq
GROQ_API_KEY = os.environ['GROQ_API_KEY']
groq_client = Groq(api_key=GROQ_API_KEY)
context = []
max_context_message_count = 15

# PVPorcupine stuff (wake word detection)
PORCUPINE_KEY = os.environ['PVPORCUPINE_KEY']
MODEL_PATH = BASE_DIR / "utils" / "wakeword" / "model" / "model_mac.ppn"
porcupine_client = None
try:
    porcupine_client = pvporcupine.create(
        access_key=PORCUPINE_KEY,
        keyword_paths=[MODEL_PATH.as_posix()]
    )
except pvporcupine.PorcupineActivationError as e:
    print(f"Failed to activate Porcupine: {e}")
    exit(1)


def append_context(is_user, response):
    """
    Adds a message from either the user or assistant to the context of the bot.
    
    :param is_user: If true, this message is from the user, and if false, the message is from the assistant.
    :param response: This is the message content.
    """
    if is_user:
        context.append({'role': 'user', 'content': response})
    else:
        context.append({'role': 'assistant', 'content': response})

    if len(context) > max_context_message_count: # Based on this setup, you only need to check once and it won't go over.
        del context[0] # Item 0 is always the oldest in the list

recorder.find_sample_rate()

is_running = False

allowed_onewords = ['yes', 'no', 'what', 'sure', 'yeah', 'nah', 'ok', 'okay', 'alright', 'maybe', 'great', 'fine', 'hi', 'hello', 'time', 'clock', 'whattup', 'yo', 'why', 'test', 'same', 'clanker', 'clinker'] # Add to this list if any one-word answer comes to mind that probably isn't a mistake


from utils.wakeword import wakeword

console = Console()

async def main():
    console.clear()
    print("\n")
    print(Gradient(""":::::::..       ...   :::.    :::.:::.    :::..-:.     ::-.    :::      .::.  ...     :::  .,-::::: .,::::::  
;;;;``;;;;   .;;;;;;;.`;;;;,  `;;;`;;;;,  `;;; ';;.   ;;;;'    ';;,   ,;;;'.;;;;;;;.  ;;;,;;;'````' ;;;;''''  
 [[[,/[[['  ,[[     \\[[,[[[[[. '[[  [[[[[. '[[   '[[,[[['       \\[[  .[[/ ,[[     \\[[,[[[[[[         [[cccc   
 $$$$$$c    $$$,     $$$$$$ \"Y$c$$  $$$ \"Y$c$$     c$$\"          Y$c.$$\"  $$$,     $$$$$$$$$         $$\"\"\"\"   
 888b "88bo,"888,_ _,88P888    Y88  888    Y88   ,8P"`            Y88P    "888,_ _,88P888`88bo,__,o, 888oo,__ 
 MMMM   \"W\"   \"YMMMMMP\" MMM     YM  MMM     YM  mM\"                MP       \"YMMMMMP\" MMM  \"YUMMMMMP\"\"\"\"\"YUMMM""", colors=["red", "orange", "blue"], justify='center'))
    console.rule(style="red")
    while True:
        print("[italic]Waiting for wake word[white]...[/white][/italic]")

        if porcupine_client:
            await wakeword.wait_for_wake_word(porcupine_client)
            print("[bold green]Detected wakeword![/bold green] [italic]Waking up[white]...[/white][italic]")
        else:
            print("[red bold]WARNING:[/red bold] Wakeword system disabled!!")

        is_running = True

        while is_running:
            with console.status("Listening...", spinner="dots") as status:
                audio = recorder.start_recording()

                if audio is None:
                    print("\n[red bold]WARNING:[/red bold] Audio not found! [italic]Going back to listening for wake word[white]...[/white][/italic]")
                    break

                status.update("Transcribing...\n", spinner_style="yellow")

                question = transcribe.start(groq_client, recorder.sample_rate, audio)
                print('[yellow bold]Transcribed question:[/yellow bold] [italic]' + question + "[/italic]")
                
                trimmed_question = question.replace(" ", "").replace(".", "").replace("!", "").replace("?", "").replace(",", "").lower()
                if trimmed_question == "thankyou":
                    print('Warning: it said "thank you" which either means the user actually said something short or that they said nothing.')
                    is_running = False
                    break

                if len(question.split()) == 1 and trimmed_question not in allowed_onewords:
                    print('Warning: it said a single word that wasn\'t in the allowed words list! This hopefully was a mistake in transcription.')
                    is_running = False
                    break
                
                append_context(True, question)

            ai_response = streaming.stream_data(groq_client, google_client, context, console)
            append_context(False, ai_response)
            print("\n")
            console.rule(style="blue")

import asyncio
loop = asyncio.get_event_loop()
loop.run_until_complete(main())