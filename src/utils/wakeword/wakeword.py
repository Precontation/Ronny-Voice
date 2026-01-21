# Copyright 2026 The Ronny Voice Foundation

from pvporcupine import Porcupine
from pvrecorder import PvRecorder

async def wait_for_wake_word(client: Porcupine):
    recorder = PvRecorder(frame_length=512)
    recorder.start()
    while recorder.is_recording:
        frame = recorder.read()
        keyword_index = client.process(frame)
        if (keyword_index >= 0):
            recorder.delete()
            return