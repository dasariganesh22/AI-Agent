import asyncio
import websockets
import json
import threading
import time
import os
import speech_recognition as sr

from background_agent import start_background_agent
from voice import wait_for_wake_word, listen, speak, recognizer
from ai_brain import ask_ai

# ---------------------------------------------
#  GLOBAL STATE (The Brain's current status)
# ---------------------------------------------
current_state = {
    "status": "SLEEPING", 
    "tasks": 0,
    "volume": 0
}

def update_state(status, tasks=None, volume=None):
    """Updates the dictionary that the frontend reads."""
    global current_state
    current_state["status"] = status
    if tasks is not None: current_state["tasks"] = tasks
    if volume is not None: current_state["volume"] = volume

# ---------------------------------------------
# 🔌 WEBSOCKET SERVER (The Bridge)
# ---------------------------------------------
async def send_state(websocket):
    print("\n[SERVER] Web UI Successfully Connected!")
    try:
        while True:
            await websocket.send(json.dumps(current_state))
            await asyncio.sleep(0.1)
    except websockets.exceptions.ConnectionClosed:
        print("[SERVER] Web UI Disconnected.")

async def start_server():
    try:
        async with websockets.serve(send_state, "127.0.0.1", 8765):
            print("[SERVER] Websocket Port 8765 is OPEN.")
            await asyncio.Future()  
    except Exception as e:
        print(f"\n[CRITICAL ERROR] UI Server failed to start! Port 8765 might be in use: {e}\n") 

def run_server_thread():
    asyncio.run(start_server())

# ---------------------------------------------
#  AI VOICE LOOP
# ---------------------------------------------
def run_ai_loop():
    print("[AI] System Booting...")
    update_state("SPEAKING", tasks=1, volume=80)
    speak("Iris neural server is online.")
    
    mic = sr.Microphone()
    print("[SERVER] Initializing Hardware Audio Stream...")
    
    with mic as source:
        recognizer.adjust_for_ambient_noise(source, duration=1.0)
        
        while True:
            update_state("SLEEPING", tasks=0, volume=0)
            
            if wait_for_wake_word(source):
                
                # Speak EXACTLY ONCE before the command loop starts
                update_state("LISTENING", tasks=1, volume=40)
                speak("Yes boss, what can I do for you?")
                
                while True:
                    update_state("LISTENING", tasks=1, volume=40)
                    
                    command = listen(source)
                    
                    if not command:
                        continue 
                    
                    if "exit" in command or "shut down" in command or "shutdown" in command:
                        update_state("SPEAKING", tasks=0, volume=80)
                        speak("Shutting down. Goodbye.")
                        os._exit(0) 
                        
                    if "stop listening" in command or "go to sleep" in command:
                        update_state("SPEAKING", tasks=0, volume=80)
                        speak("Going to sleep.")
                        break 
                        
                    if any(phrase in command for phrase in ["look at screen", "check my screen", "analyze screen", "see my screen", "look at my screen"]):
                        update_state("VISION", tasks=2, volume=0)
                    else:
                        update_state("THINKING", tasks=2, volume=0)
                        
                    ask_ai(command)
                    
                    update_state("SPEAKING", tasks=1, volume=80)
                    time.sleep(0.5)

if __name__ == "__main__":
    start_background_agent()
    
    # Register the callback so voice.py can dynamically trigger the web UI
    import voice
    def trigger_speaking_ui():
        update_state("SPEAKING", tasks=1, volume=80)
    voice.on_speech_start = trigger_speaking_ui
    
    server_thread = threading.Thread(target=run_server_thread, daemon=True)
    server_thread.start()
    
    try:
        run_ai_loop()
    except KeyboardInterrupt:
        print("\n[SERVER] Force quitting via keyboard. Releasing hardware...")
        os._exit(0)
