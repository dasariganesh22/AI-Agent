from ai_brain import ask_ai
from voice import listen, speak, wait_for_wake_word, recognizer
import time
import os
import speech_recognition as sr
from background_agent import start_background_agent

def handle_commands(source):
    # 🔥 Speak exactly once when activated
    speak("Yes boss, what can I do for you?")
    
    last_active = time.time()

    while True:
        raw_command = listen(source)
        
        if raw_command == "":
            if time.time() - last_active > 15:
                speak("Going to sleep.")
                return
            continue

        last_active = time.time()
        print("Heard:", raw_command)

        if any(word in raw_command for word in ["hey iris", "iris", "irish"]):
            speak("Yes?")
            continue 

        if any(word in raw_command for word in ["exit", "close program", "shut down", "exit assistant"]):
            speak("Shutting down. Goodbye.")
            os._exit(0)

        ask_ai(raw_command)

def main():
    start_background_agent()
    speak("Iris is ready")
    
    mic = sr.Microphone()
    with mic as source:
        recognizer.adjust_for_ambient_noise(source, duration=1.0)
        
        while True:
            if wait_for_wake_word(source):
                handle_commands(source)
            else:
                break

if __name__ == "__main__":
    main()