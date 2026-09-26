from google.genai import types
from gemini_client import client
from voice import speak
import time
import os
from background_agent import set_reminder
from system_control import (
    open_app, close_app, set_volume, get_volume, get_system_status, take_screenshot, 
    search_local_file, search_the_web, find_image, show_next_image, 
    download_current_image, analyze_screen
)
from music import play_music, pause_song, resume_song, next_song, previous_song, close_music
from memory_engine import save_memory, search_memory

def exit_assistant():
    speak("Shutting down. Goodbye.")
    os._exit(0)

# Register all tools available to Iris
IRIS_TOOLS = [
    open_app,
    close_app,
    set_volume,
    get_volume,
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

SYSTEM_INSTRUCTION = (
    "You are Iris, a fast, intelligent neural voice assistant. "
    "You speak your answers aloud to the user. "
    "Rules for responses: "
    "1. Always respond in plain, conversational text. Never use Markdown formatting, asterisks (*), bullet points, or headers (###). "
    "2. Calibrate response length strictly to the question: For simple questions or confirmations, provide a direct 1 to 2 sentence answer. Only give detailed explanations when the user explicitly asks for a comprehensive answer or an in-depth breakdown. "
    "3. When the user asks to look at their screen, explain visual errors, or inspect UI designs, use the analyze_screen tool."
)

GENERATION_CONFIG = types.GenerateContentConfig(
    tools=IRIS_TOOLS,
    system_instruction=SYSTEM_INSTRUCTION
)

def _execute_tool(name: str, args: dict, prompt: str) -> dict:
    """Executes a requested IRIS tool safely and returns a response dictionary."""
    try:
        # System & App Controls
        if name == "open_app":
            res = open_app(args.get("command", prompt))
            return {"status": "success", "result": res or f"Opened {args.get('command', prompt)}"}
        elif name == "close_app":
            res = close_app(args.get("command", prompt))
            return {"status": "success", "result": res or f"Closed {args.get('command', prompt)}"}
        elif name == "set_volume":
            res = set_volume(args.get("command", prompt))
            return {"status": "success", "result": res or "Volume adjusted successfully"}
        elif name == "get_volume":
            return {"volume": get_volume()}
        elif name == "get_system_status":
            return {"system_status": get_system_status()}
        elif name == "take_screenshot":
            return {"result": take_screenshot()}
        elif name == "search_local_file":
            return {"result": search_local_file(args.get("filename", prompt))}
        elif name == "search_the_web":
            return {"result": search_the_web(args.get("query", prompt))}
        elif name == "exit_assistant":
            exit_assistant()
            return {"status": "exiting"}

        # Vision Tool Execution
        elif name == "analyze_screen":
            query_text = args.get("query", prompt)
            speak("Analyzing your screen now.")
            return {"screen_analysis": analyze_screen(query_text)}

        # Music Controls
        elif name == "play_music":
            res = play_music(args.get("query", prompt))
            return {"status": "success", "result": res or f"Playing {args.get('query', prompt)}"}
        elif name == "pause_song":
            pause_song()
            return {"status": "success", "result": "Music paused"}
        elif name == "resume_song":
            resume_song()
            return {"status": "success", "result": "Music resumed"}
        elif name == "next_song":
            next_song()
            return {"status": "success", "result": "Skipped to next song"}
        elif name == "previous_song":
            previous_song()
            return {"status": "success", "result": "Returned to previous song"}
        elif name == "close_music":
            close_music()
            return {"status": "success", "result": "Music closed"}

        # Reminders & Images
        elif name == "set_reminder":
            seconds = args.get("seconds", 10)
            msg = args.get("message", "Timer completed")
            return {"result": set_reminder(seconds=seconds, message=msg)}
        elif name == "find_image":
            return {"result": find_image(args.get("query", prompt))}
        elif name == "show_next_image":
            return {"result": show_next_image()}
        elif name == "download_current_image":
            return {"result": download_current_image()}

        # Long-Term Memory Tools
        elif name == "save_memory":
            fact = args.get("fact", prompt)
            return {"result": save_memory(fact)}
        elif name == "search_memory":
            query_text = args.get("query", prompt)
            return {"memory_results": search_memory(query_text)}

        else:
            return {"error": f"Unknown tool: {name}"}

    except Exception as e:
        print(f"[IRIS Tool Error] {name} execution failed: {e}")
        return {"error": f"Tool execution failed: {type(e).__name__}"}

# Bounded in-memory short-term conversation history
# Each entry is an atomic list of types.Content objects representing one full interaction turn
MAX_HISTORY_TURNS = 5
_conversation_turns: list[list[types.Content]] = []

def reset_conversation():
    """Resets the short-term in-memory conversation context."""
    global _conversation_turns
    _conversation_turns.clear()

def get_conversation_turns() -> list:
    """Returns a shallow copy of the current short-term conversation turns."""
    return list(_conversation_turns)

def _add_turn(turn: list[types.Content]):
    """Appends an atomic turn and ensures history remains bounded."""
    global _conversation_turns
    _conversation_turns.append(turn)
    if len(_conversation_turns) > MAX_HISTORY_TURNS:
        _conversation_turns = _conversation_turns[-MAX_HISTORY_TURNS:]

def ask_ai(prompt: str):
    """Sends user voice commands to Gemini with conversational context and two-way tool execution."""
    lower_prompt = prompt.lower().strip()
    if lower_prompt in ("clear conversation", "reset conversation", "clear context", "forget conversation"):
        reset_conversation()
        msg = "Conversation context has been cleared."
        speak(msg)
        return msg

    try:
        # Build contents from prior turns + current user message
        user_content = types.Content(role="user", parts=[types.Part.from_text(text=prompt)])
        request_contents = [c for turn in _conversation_turns for c in turn] + [user_content]

        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=request_contents,
            config=GENERATION_CONFIG
        )

        # Handle tool/function calling with two-way round-trip
        if response.function_calls:
            function_response_parts = []
            for call in response.function_calls:
                name = call.name
                args = call.args or {}
                print(f"[IRIS Tool Triggered] Executing: {name} with args: {args}")
                tool_result = _execute_tool(name, args, prompt)
                function_response_parts.append(
                    types.Part.from_function_response(
                        name=name,
                        response=tool_result
                    )
                )

            model_call_content = response.candidates[0].content if (response.candidates and response.candidates[0].content) else types.Content(role="model", parts=[types.Part(function_call=call) for call in response.function_calls])
            tool_response_content = types.Content(role="user", parts=function_response_parts)

            # Send tool results back to Gemini for the final natural-language response
            follow_up_contents = list(request_contents) + [
                model_call_content,
                tool_response_content
            ]

            final_response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=follow_up_contents,
                config=GENERATION_CONFIG
            )

            answer = final_response.text
            model_final_content = final_response.candidates[0].content if (final_response.candidates and final_response.candidates[0].content) else types.Content(role="model", parts=[types.Part.from_text(text=answer or "")])

            # Record the atomic 4-part turn into bounded conversation history
            _add_turn([user_content, model_call_content, tool_response_content, model_final_content])

            if answer:
                speak(answer)
            return answer

        # Standard conversation response without tools
        answer = response.text
        model_content = response.candidates[0].content if (response.candidates and response.candidates[0].content) else types.Content(role="model", parts=[types.Part.from_text(text=answer or "")])

        # Record the atomic 2-part turn into bounded conversation history
        _add_turn([user_content, model_content])

        if answer:
            speak(answer)
        return answer

    except Exception as e:
        error_str = str(e)
        print("[IRIS Error]:", error_str)
        if "429" in error_str:
            speak("Rate limit reached. Please wait a moment before sending another request.")
        else:
            speak("I encountered an issue processing that request.")
        return None