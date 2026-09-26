# IRIS — Intelligent Real-time Interactive System

> A voice-controlled desktop AI agent built with Python, Google Gemini 2.5 Flash, system automation, memory, screen vision, and a transparent desktop HUD.

## Overview

IRIS is a Python-based desktop AI agent that understands natural-language voice commands and uses Gemini function calling to choose and execute tools on a Windows PC.

IRIS currently combines:
- Natural-language AI reasoning with Gemini 2.5 Flash
- Wake-word and speech interaction
- Two-way tool execution and response synthesis
- Short-term conversation context
- Windows system automation
- Screen vision
- Long-term ChromaDB memory
- Web and local file search
- Music controls and reminders
- Background monitoring
- A transparent PyQt6 holographic-style interface

## Current capabilities

### AI brain
- Gemini 2.5 Flash for reasoning and tool selection.
- Centralized Gemini client configuration.
- 22 registered tools.
- Tool results are sent back to Gemini so IRIS can produce a natural final response.
- Bounded in-memory conversation context for follow-up commands.
- Conversation context is reset between voice sessions.

### Voice
- Wake phrases such as Hey IRIS and IRIS.
- Speech-to-text with SpeechRecognition.
- Text-to-speech with Microsoft Edge TTS.

### Windows automation
- Open and close applications.
- Native Windows volume control using pycaw.
- Read current volume.
- Capture screenshots.
- Inspect system status.
- Search local files.
- Search the live web.
- Set reminders.
- Control music playback.

### Screen vision
- Captures the current screen.
- Uses Gemini multimodal capabilities to analyze visible applications, code, interfaces, and other on-screen content.

### Memory
IRIS has two separate memory systems.

Short-term conversation context:
- In-memory only.
- Limited to the most recent 5 conversation turns.
- Cleared when a session ends or the user explicitly resets the conversation.

Long-term memory:
- Stored locally with ChromaDB.
- Used for information explicitly saved through the memory tools.
- Available across application sessions.

### Background agent
- Runs reminders and timers.
- Monitors battery state.
- Monitors CPU load.

### Desktop HUD
- PyQt6 and Qt WebEngine.
- Transparent desktop interface.
- HTML/CSS visual layer.
- WebSocket communication with the Python backend.
- Visual states for listening, thinking, vision, speaking, and sleeping.

## Architecture

User Voice
  -> Wake-word and Speech Recognition
  -> AI Brain
  -> Gemini 2.5 Flash
  -> Tool Selection
  -> Python Tool Execution
  -> Tool Result
  -> Gemini Final Response
  -> Edge TTS
  -> User

The holographic HUD communicates with the backend through WebSockets.

## Core modules

| File | Responsibility |
|---|---|
| main.py | Master launcher and process supervisor |
| server.py | Backend server, voice loop, WebSocket communication, session lifecycle |
| ai_brain.py | Gemini reasoning, conversation context, tool definitions and execution |
| gemini_client.py | Shared Gemini API client |
| voice.py | Speech recognition and text-to-speech |
| system_control.py | Windows automation, volume, screenshots, system status, search and vision |
| music.py | Music playback and control |
| memory_engine.py | ChromaDB long-term memory |
| background_agent.py | Reminders and proactive monitoring |
| hologram.py | Transparent PyQt6 desktop interface |
| index.html | HUD markup |
| style.css | HUD styling |
| config.py | Local environment configuration |

## Tool set

IRIS currently exposes 22 tools to Gemini:

1. open_app
2. close_app
3. set_volume
4. get_volume
5. play_music
6. pause_song
7. resume_song
8. next_song
9. previous_song
10. close_music
11. exit_assistant
12. get_system_status
13. take_screenshot
14. search_local_file
15. search_the_web
16. set_reminder
17. find_image
18. show_next_image
19. download_current_image
20. analyze_screen
21. save_memory
22. search_memory

## Short-term conversation example

User: What is my current volume?
IRIS: Your volume is 40%.

User: Set it to 60%.
IRIS: Uses the previous context and calls the volume tool.
IRIS: The volume is now set to 60%.

This context is separate from long-term ChromaDB memory and is intentionally bounded to keep the session small.

## Project structure

IRIS/
├── ai_brain.py
├── background_agent.py
├── config.py
├── gemini_client.py
├── hologram.py
├── index.html
├── main.py
├── memory_engine.py
├── music.py
├── server.py
├── style.css
├── system_control.py
├── voice.py
├── requirements.txt
├── .env.example
├── .gitignore
└── LICENSE

Runtime data such as API keys, local memory databases, screenshots, logs, generated audio, and machine-specific files should remain outside version control.

## Requirements

- Windows PC
- Python 3.10+
- Working microphone and speakers
- Google Gemini API key
- Internet connection for Gemini, speech recognition, web search, and related services

Python dependencies are listed in requirements.txt.

## Setup

1. Clone the repository.
2. Create and activate a Python virtual environment.
3. Install dependencies with pip install -r requirements.txt.
4. Copy .env.example to .env.
5. Add your Gemini API key to .env.
6. Start IRIS with python main.py.

Never commit .env or expose your API key publicly.

## Security

IRIS keeps secrets outside the repository using environment variables.

The repository ignores environment secrets, local memory data, screenshots, generated media, logs, browser artifacts, and Python caches.

The Gemini API client is centralized so the API key is not duplicated across modules.

## Development progress

Completed foundation phases:
- Security and secrets hardening
- Stable native TTS
- Native Windows CoreAudio volume control
- Centralized Gemini client and configuration
- Two-way Gemini tool-response synthesis
- Bounded short-term conversation context
- Real-world voice and tool testing

Future development will focus on reliability, multi-step task execution, and stronger agent behavior while keeping the architecture maintainable.

## License

IRIS is released under the MIT License.

See LICENSE for the full license text.

## Author

D. Ganesh

Built as a personal AI-agent project for learning, experimentation, and practical desktop automation.