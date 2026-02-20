# Copyright 2026 The Ronny Voice Foundation

import pyttsx3

engine = pyttsx3.init()

def speak(text):
    """
    Run the local (os-specific) TTS engine.
    
    :param text: The words to speak
    """
    engine.say(text)
    engine.runAndWait()