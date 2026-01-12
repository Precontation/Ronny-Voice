# Some code partly taken from the Google Cloud documentation: https://docs.cloud.google.com/text-to-speech/docs/chirp3-hd
from google.cloud import texttospeech
import sounddevice as sd
import numpy as np

# Note: the voice can also be specified by name.
# Names of voices can be retrieved with client.list_voices().
voice = texttospeech.VoiceSelectionParams(
    name="en-US-Chirp3-HD-Puck",
    language_code="en-US",
)

audio_config = texttospeech.AudioConfig(
    audio_encoding=texttospeech.AudioEncoding.LINEAR16,
    sample_rate_hertz=24000
)

def generate_speech(client, text):
    """
    Uses the Google Cloud API to generate a message when the FULL TEXT has been generated. Not streaming!
    
    :param client: The Google client
    :param text: The text to generate the audio of
    """
    input_text = texttospeech.SynthesisInput(text=text)
    response = client.synthesize_speech(
        input=input_text,
        voice=voice,
        audio_config=audio_config,
    )

    # The response's audio_content is binary.
    with open("temp_output.mp3", "wb") as out:
        out.write(response.audio_content)
        print('Audio content written to file "temp_output.mp3"')

def speak():
    """
    Takes the !!already made!! output and reads it out loud
    """
    with open("temp_output.mp3", "rb") as out:
        if out:
            audio = np.frombuffer(out.read(), dtype=np.int16)
            sd.play(audio, samplerate=24000) # Default for many Google voices is 24kHz
            sd.wait()
        else:
            print("Output not found!")