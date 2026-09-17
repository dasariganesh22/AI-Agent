from google import genai
from google.genai import types
from config import GEMINI_API_KEY
from voice import speak
import time
import os
from background_agent import set_reminder
from system_control import (
    open_app, close_app, set_volume, get_system_status, take_screenshot, 
    search_local_file, search_the_web, find_image, show_next_image, 
    download_current_image, analyze_screen
)
from music import play_music, pause_song, resume_song, next_song, previous_song, close_music
from memory_engine import save_memory, search_memory

client = genai.Client(api_key=GEMINI_API_KEY)

def exit_assistant():
    speak("Shutting down. Goodbye.")
    os._exit(0)

# Register all tools available to Iris
IRIS_TOOLS = [
    open_app,
    close_app,
    set_volume,
    play_music,
    pause_song,
    resume_song,
    next_song,
    previous_song,
    close_music,
    exit_assistant,
    get_system_status,
    take_screenshot,
    search_local_file,
    search_the_web,
    set_reminder,
    find_image,
    show_next_image,
    download_current_image,
    analyze_screen,
    save_memory,
    search_memory
]

def ask_ai(prompt: str):
    """Sends user voice commands to Gemini with full tool execution support."""
    try:
        response = client.models.generate_content(
            model='gemini-3.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                tools=IRIS_TOOLS,
                system_instruction=(
                    "You are Iris, a fast, intelligent neural voice assistant. "
                    "You speak your answers aloud to the user. "
                    "Rules for responses: "
                    "1. Always respond in plain, conversational text. Never use Markdown formatting, asterisks (*), bullet points, or headers (###). "
                    "2. Calibrate response length strictly to the question: For simple questions or confirmations, provide a direct 1 to 2 sentence answer. Only give detailed explanations when the user explicitly asks for a comprehensive answer or an in-depth breakdown. "
                    "3. When the user asks to look at their screen, explain visual errors, or inspect UI designs, use the analyze_screen tool."
                )
            )
        )

        # Check if Gemini requested to execute a tool function
        if response.function_calls:
            for call in response.function_calls:
                name = call.name
                args = call.args
                print(f"[IRIS Tool Triggered] Executing: {name} with args: {args}")

                # System & App Controls
                if name == "open_app":
                    open_app(args.get("command", prompt))
                elif name == "close_app":
                    close_app(args.get("command", prompt))
                elif name == "set_volume":
                    set_volume(args.get("command", prompt))
                elif name == "get_system_status":
                    status = get_system_status()
                    speak(status)
                elif name == "take_screenshot":
                    result = take_screenshot()
                    speak(result)
                elif name == "search_local_file":
                    result = search_local_file(args.get("filename", prompt))
                    speak(result)
                elif name == "search_the_web":
                    result = search_the_web(args.get("query", prompt))
                    speak(result)
                elif name == "exit_assistant":
                    exit_assistant()
                
                # Vision Tool Execution
                elif name == "analyze_screen":
                    query_text = args.get("query", prompt)
                    speak("Analyzing your screen now.")
                    result = analyze_screen(query_text)
                    speak(result)
                

                # Music Controls
                elif name == "play_music":
                    play_music(args.get("query", prompt))
                elif name == "pause_song":
                    pause_song()
                elif name == "resume_song":
                    resume_song()
                elif name == "next_song":
                    next_song()
                elif name == "previous_song":
                    previous_song()
                elif name == "close_music":
                    close_music()

                # Reminders & Images
                elif name == "set_reminder":
                    seconds = args.get("seconds", 10)
                    msg = args.get("message", "Timer completed")
                    result = set_reminder(seconds=seconds, message=msg)
                    speak(result)
                elif name == "find_image":
                    result = find_image(args.get("query", prompt))
                    speak(result)
                elif name == "show_next_image":
                    result = show_next_image()
                    speak(result)
                elif name == "download_current_image":
                    result = download_current_image()
                    speak(result)

                # 🧠 LONG-TERM MEMORY TOOLS
                elif name == "save_memory":
                    fact = args.get("fact", prompt)
                    speak("Saving that to my long-term memory.")
                    result = save_memory(fact)
                    print(result)
                    
                elif name == "search_memory":
                    query_text = args.get("query", prompt)
                    speak("Searching my memory banks.")
                    result = search_memory(query_text)
                    
                    # Pass the raw memory data back to Gemini so she can formulate a natural spoken answer
                    follow_up = client.models.generate_content(
                        model='gemini-2.5-flash',
                        contents=f"You just searched your memory and found this data: '{result}'. Answer the user's original query: '{prompt}'. Speak naturally and concisely."
                    )
                    speak(follow_up.text)

            return "Tool executed successfully."

        # Standard conversation response
        answer = response.text
        if answer:
            speak(answer)
        return

    except Exception as e:
        error_str = str(e)
        print("[IRIS Error]:", error_str)
        if "429" in error_str:
            speak("Rate limit reached. Please wait a moment before sending another request.")
        else:
            speak("I encountered an issue processing that request.")