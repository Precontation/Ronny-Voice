# Copyright 2026 The Ronny Voice Foundation

import sounddevice as sd
import numpy as np
import queue
import soundfile as sf
from typing import Any, cast # For casting the sounddevice's input devices to a dict
import time as timeButDifferentNameAA

is_recording = False
probably_talked = False
q = queue.Queue() # Create a queue for the queue to queue to (yes i know)
finished_speaking_time = 1.5 # For the alexa-like "answer when done asking question"
not_talking_time = 5 # Add a better feel if you haven't started to talk yet
time_since_last_zero_volume_norm = timeButDifferentNameAA.time() # For the alexa-like "answer when done asking question"

# Settings
sample_rate = 44100
channels = 1
file_name = 'temp_recording.wav' # Make sure to include .wav!
audio_sensitivity = 15

def callback(indata, frames, time, status):
    global is_recording
    global time_since_last_zero_volume_norm
    global probably_talked

    """This is called for every audio block"""
    if status:
        print(status)

    current_time = timeButDifferentNameAA.time()
    volume_norm = int(np.linalg.norm(indata) * audio_sensitivity)
    if volume_norm > 5:
        time_since_last_zero_volume_norm = current_time
        probably_talked = True

    time_difference = current_time - time_since_last_zero_volume_norm
    if (probably_talked and time_difference > finished_speaking_time) or (not probably_talked and time_difference > not_talking_time):
        is_recording = False

    try:
        q.put(indata.copy()) # Save to a queue as it's more reliable than an array or something off the main thread.
    except Exception as e:
        print(f"Callback error: {e}")

def find_sample_rate():
    global sample_rate

    # Use the discovered sample rate from the device info
    try:
        device_info = cast(dict[str, Any], sd.query_devices(kind='input'))
        sample_rate = int(device_info['default_samplerate'])
        print(f"Recording at {sample_rate} Hz (Device: {device_info['name']})")
    except Exception:
        sample_rate = 44100
        print(f"Unable to find sample rate of device! Using default ({sample_rate})")

def start_recording():
    global is_recording
    global time_since_last_zero_volume_norm
    global probably_talked
    
    """
    Start recording with all the fun auto-turn-off and more features
    """

    recorded_chunks = []
    q.queue.clear()
    time_since_last_zero_volume_norm = timeButDifferentNameAA.time() # For the alexa-like "answer when done asking question"

    with sf.SoundFile(file_name, mode='w', samplerate=sample_rate, channels=channels) as file: # This is to save the audio as a file,
        with sd.InputStream(samplerate=sample_rate, channels=channels, callback=callback): # And this is to actually record the input in general.
            is_recording = True
            probably_talked = False
            while is_recording:
                try:
                    data = q.get() # Get the data from the queue!
                    recorded_chunks.append(data)
                except queue.Empty:
                    continue # If there's no queue just don't really do anything
                except KeyboardInterrupt:
                    is_recording = False # Ctrl+C to close otherwise it'l be recording forever!

    if recorded_chunks and probably_talked:
        print("Finished recording!")
        return np.concatenate(recorded_chunks, axis=0)
    else:
        print("No recording data found!")
        return None