from google.genai import errors, types
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
MAX_TOOL_ITERATIONS = 5
MAX_API_ATTEMPTS = 2
RETRY_BACKOFF_SECONDS = 0.5
RETRYABLE_STATUS_CODES = {500, 502, 503, 504}
NON_RETRYABLE_STATUS_CODES = {400, 401, 403, 404, 429}

try:
    import httpx
    HTTPX_NETWORK_ERRORS = (httpx.RequestError, httpx.TimeoutException)
except ImportError:
    HTTPX_NETWORK_ERRORS = ()

TRANSIENT_NETWORK_ERRORS = (ConnectionError, TimeoutError, OSError) + HTTPX_NETWORK_ERRORS

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

def _is_retryable_error(e: Exception) -> bool:
    """Determines whether a Gemini API error is plausibly temporary and eligible for retry."""
    if isinstance(e, errors.APIError):
        code = getattr(e, "code", None)
        if code in RETRYABLE_STATUS_CODES:
            return True
        if code in NON_RETRYABLE_STATUS_CODES:
            return False
        if isinstance(e, errors.ServerError):
            return True
        return False

    if isinstance(e, TRANSIENT_NETWORK_ERRORS):
        return True

    # Fallback string pattern inspection
    err_str = str(e).lower()
    if any(k in err_str for k in ("503", "502", "504", "500", "service unavailable", "timeout", "connection reset", "connection refused")):
        if not any(k in err_str for k in ("429", "401", "403", "quota", "resource_exhausted", "unauthenticated", "permission_denied")):
            return True

    return False

def _get_error_message(e: Exception) -> str:
    """Translates a Gemini exception into a natural, concise spoken message without exposing secrets."""
    if isinstance(e, errors.APIError):
        code = getattr(e, "code", None)
        status = getattr(e, "status", "")
        if code == 429 or status == "RESOURCE_EXHAUSTED":
            return "The AI service rate limit has been reached. Please try again later."
        if code in (401, 403) or status in ("UNAUTHENTICATED", "PERMISSION_DENIED"):
            return "The AI service configuration needs attention."
        if code in RETRYABLE_STATUS_CODES or isinstance(e, errors.ServerError):
            return "I'm having trouble reaching the AI service right now. Please try again."

    if isinstance(e, TRANSIENT_NETWORK_ERRORS):
        return "I'm having trouble reaching the AI service right now. Please try again."

    err_str = str(e).lower()
    if "429" in err_str or "resource_exhausted" in err_str or "quota" in err_str:
        return "The AI service rate limit has been reached. Please try again later."
    if "401" in err_str or "403" in err_str or "unauthenticated" in err_str or "permission_denied" in err_str or "api_key" in err_str:
        return "The AI service configuration needs attention."
    if any(k in err_str for k in ("503", "502", "504", "500", "unavailable", "timeout", "connection")):
        return "I'm having trouble reaching the AI service right now. Please try again."

    return "I couldn't complete that request right now."

def _generate_with_retry(contents, model: str = 'gemini-3.8-flash'):
    """Executes client.models.generate_content with bounded retry for transient errors."""
    for attempt in range(1, MAX_API_ATTEMPTS + 1):
        try:
            return client.models.generate_content(
                model=model,
                contents=contents,
                config=GENERATION_CONFIG
            )
        except Exception as e:
            if attempt < MAX_API_ATTEMPTS and _is_retryable_error(e):
                status_info = getattr(e, "code", None) or getattr(e, "status", None) or type(e).__name__
                print(f"[IRIS Gemini] Attempt {attempt}/{MAX_API_ATTEMPTS} failed with {status_info}. Retrying...")
                time.sleep(RETRY_BACKOFF_SECONDS)
                continue

            if attempt > 1:
                print(f"[IRIS Gemini] Attempt {attempt}/{MAX_API_ATTEMPTS} failed. Giving up.")
            else:
                status_info = getattr(e, "code", None) or getattr(e, "status", None) or type(e).__name__
                print(f"[IRIS Gemini] Request failed with {status_info} (not retryable).")
            raise e

def ask_ai(prompt: str):
    """Sends user voice commands to Gemini with conversational context, reliability retries, and multi-step tool execution."""
    lower_prompt = prompt.lower().strip()
    if lower_prompt in ("clear conversation", "reset conversation", "clear context", "forget conversation"):
        reset_conversation()
        msg = "Conversation context has been cleared."
        speak(msg)
        return msg

    try:
        # Build contents from prior turns + current user message
        user_content = types.Content(role="user", parts=[types.Part.from_text(text=prompt)])
        current_turn_contents = [user_content]
        history_prefix = [c for turn in _conversation_turns for c in turn]

        response = _generate_with_retry(history_prefix + current_turn_contents)

        iteration_count = 0
        while response.function_calls:
            if iteration_count >= MAX_TOOL_ITERATIONS:
                print(f"[IRIS Agent] Reached MAX_TOOL_ITERATIONS ({MAX_TOOL_ITERATIONS}). Stopping tool execution.")
                limit_msg = "I have reached the maximum number of tool steps for this request. Please let me know how you would like to proceed."
                model_limit_content = types.Content(role="model", parts=[types.Part.from_text(text=limit_msg)])
                current_turn_contents.append(model_limit_content)
                _add_turn(current_turn_contents)
                speak(limit_msg)
                return limit_msg

            iteration_count += 1
            print(f"[IRIS Agent] Tool iteration {iteration_count}/{MAX_TOOL_ITERATIONS} with {len(response.function_calls)} call(s)")

            # Execute all requested tools in this Gemini response
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

            model_call_content = (
                response.candidates[0].content
                if (response.candidates and response.candidates[0].content)
                else types.Content(role="model", parts=[types.Part(function_call=call) for call in response.function_calls])
            )
            tool_response_content = types.Content(role="user", parts=function_response_parts)

            current_turn_contents.append(model_call_content)
            current_turn_contents.append(tool_response_content)

            # Request next Gemini turn through the retry helper
            response = _generate_with_retry(history_prefix + current_turn_contents)

        # Standard final conversation response (after tool loop completes or if no tools were called)
        answer = response.text
        model_final_content = (
            response.candidates[0].content
            if (response.candidates and response.candidates[0].content)
            else types.Content(role="model", parts=[types.Part.from_text(text=answer or "")])
        )
        current_turn_contents.append(model_final_content)

        # Record the complete atomic turn into bounded conversation history
        _add_turn(current_turn_contents)

        if answer:
            speak(answer)
        return answer

    except Exception as e:
        error_msg = _get_error_message(e)
        status_info = getattr(e, "code", None) or type(e).__name__
        print(f"[IRIS Error] Request failed ({status_info}): {error_msg}")
        speak(error_msg)
        return None