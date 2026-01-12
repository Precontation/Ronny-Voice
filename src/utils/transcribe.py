# Copyright 2026 The Ronny Voice Foundation

import soundfile as sf
import io

model = 'whisper-large-v3-turbo'
def start(client, sample_rate, audio_data):
    """
    Use a model from Groq to extract the text out of an audio clip.
    
    :param audio_data: The file to get the text from
    """
    
    buffer = io.BytesIO()
    buffer.name = "audio.wav"  # Groq needs this extension to identify the format. The name doesn't matter (I don't think)
    sf.write(buffer, audio_data, sample_rate, format='WAV')
    buffer.seek(0)             # Reset pointer so Groq reads from the start

    transcription = client.audio.transcriptions.create(model=model, file=buffer)
    return transcription.text