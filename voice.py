import speech_recognition as sr
import random
import pygame
import os
import uuid
import time
import threading
import edge_tts
import re

# ----------------------------
# INIT AUDIO
# ----------------------------
pygame.mixer.init()
time.sleep(0.5)

speech_lock = threading.Lock()

# Global Recognizer
recognizer = sr.Recognizer()  
recognizer.pause_threshold = 0.8           
recognizer.non_speaking_duration = 0.5     
recognizer.dynamic_energy_threshold = True 

def clean_markdown_for_speech(raw_text: str) -> str:
    """Strips Markdown symbols, bullet asterisks, and formatting so TTS speaks naturally."""
    if not raw_text:
        return ""
    
    text = str(raw_text)
    
    # 1. Remove Markdown headers (###), horizontal lines (---), bold/italic (*, _)
    text = re.sub(r'#+\s*', '', text)           # Remove ###
    text = re.sub(r'(\*\*|\*|__|_)', '', text)  # Remove bold/italic asterisks & underscores
    text = re.sub(r'~~.*?~~', '', text)         # Remove strikethroughs
    text = re.sub(r'`{1,3}.*?`{1,3}', '', text) # Remove inline code blocks
    text = re.sub(r'---+', '', text)            # Remove horizontal rules
    
    # 2. Clean bullet points, brackets, and quotes
    text = re.sub(r'^\s*[\*\-\+]\s+', '', text, flags=re.MULTILINE)
    text = text.replace('"', '').replace("'", "").replace('\n', ' ')
    
    # 3. Collapse multiple whitespace into a single space
    text = re.sub(r'\s+', ' ', text).strip()
    return text

# ----------------------------
# SPEAK (HUMAN NEURAL VOICE)
# ----------------------------
on_speech_start = None

def speak(text):
    if not text:
        return
        
    try:
        # Clean markdown symbols and prepare natural spoken string
        clean_text = clean_markdown_for_speech(text)
        if not clean_text:
            return

        print("IRIS:", clean_text)

        #  Trigger UI Animation BEFORE the audio blocks the thread
        if on_speech_start:
            on_speech_start()

        with speech_lock:
            filename = f"voice_{uuid.uuid4().hex}.mp3"
            voice_model = "en-GB-SoniaNeural" 
            communicate = edge_tts.Communicate(clean_text, voice_model, rate="+2%")
            communicate.save_sync(filename)

            if os.path.exists(filename):
                try:
                    pygame.mixer.music.load(filename)
                    pygame.mixer.music.play()
                    
                    while pygame.mixer.music.get_busy():
                        time.sleep(0.05)
                        
                    pygame.mixer.music.unload()
                finally:
                    for _ in range(5):
                        try:
                            if os.path.exists(filename):
                                os.remove(filename)
                            break
                        except PermissionError:
                            time.sleep(0.05)
                        except Exception:
                            break
                
                # Echo Guard Buffer
                time.sleep(0.4)

    except Exception as e:
        print("Speech error:", e)

# ----------------------------
# GREETING
# ----------------------------
def greet():
    responses = ["Yes?", "How can I help?", "I'm listening", "Tell me"]
    speak(random.choice(responses))

# ----------------------------
# LISTEN
# ----------------------------
def listen(source):
    try:
        audio = recognizer.listen(source, timeout=5, phrase_time_limit=8)
        return recognizer.recognize_google(audio).lower()
    except sr.WaitTimeoutError:
        return ""
    except Exception:
        return ""

# ----------------------------
# WAKE WORD
# ----------------------------
def wait_for_wake_word(source):
    print("Waiting for wake word...")
    while True:
        try:
            audio = recognizer.listen(source, timeout=None, phrase_time_limit=3)
            text = recognizer.recognize_google(audio).lower()

            print("Heard:", text)

            if any(word in text for word in ["hey iris", "iris", "irish"]):
                print("ACTIVATED")
                return True  

            if "exit" in text:
                return False
        except Exception:
            continue