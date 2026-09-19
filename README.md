# IRIS — Intelligent Real-time Interactive System
> **An Autonomous Voice-Controlled Desktop Assistant built with Python, Google Gemini Function Calling, and Multithreaded System Monitoring.**

---

## 📌 Overview
**IRIS** (Intelligent Real-time Interactive System) is an advanced voice assistant designed to automate local system controls, monitor hardware metrics, search the live web, and run proactive background timers. Unlike static voice scripts that rely on rigid keyword matching, IRIS uses LLM-driven tool calling to dynamically choose and execute Python functions based on natural spoken language. With the latest updates, IRIS has evolved to include **Active Screen Awareness** and a **Transparent Holographic Desktop UI**.

---

## ✨ Key Capabilities

- 🧠 **Dynamic Tool Calling:** Powered by the Google Gemini 2.5 Flash API to interpret complex, natural language commands and execute Python functions automatically with ultra-low latency.
- 👁️ **Active Screen Awareness (Vision Mode):** Uses Gemini's multimodal capabilities to silently capture the active monitor, allowing visual analysis of code, diagrams, or UI designs currently visible on the screen.
- 💽 **Long-Term Memory Engine:** Integrates a local ChromaDB vector database to persistently save, search, and retrieve facts and user preferences across sessions.
- 🌐 **Real-time Web & Image Search:** Integrates DuckDuckGo (`ddgs` engine) to retrieve live weather, news, factual information, and download high-resolution images without rate-limiting blocks.
- 🖥️ **Transparent Hologram UI:** A borderless, click-through PyQt6 HTML/CSS desktop widget that displays real-time tasks, weather, and a reactive status ring indicating current states (Sleeping, Listening, Thinking, Vision, Speaking).
- ⚙️ **Local OS Automation:** Launches and terminates applications, adjusts system volume, captures screenshots, and inspects hardware stats using Python `psutil` and `pyautogui`.
- ⏱️ **Multithreaded Proactive Agent:** Features a background daemon thread that runs non-blocking timers, reminders, battery warnings, and CPU load monitors concurrently with the voice loop.
- 🛡️ **Robust Master Architecture:** A master launcher (`main.py`) supervises asynchronous WebSocket communication between the backend Python brain and the frontend UI, ensuring perfect synchronization and resolving multi-process termination issues.

---

## 🏗️ System Architecture

```text
                   +-----------------------+
                   | Spoken Audio Input    |
                   +-----------+-----------+
                               |
                               v
                   +-----------------------+
                   | Wake-Word Engine      |
                   +-----------+-----------+
                               |
                               v
                   +-----------------------+
                   | Speech-To-Text (STT)  |
                   +-----------+-----------+
                               |
                               v
             +-----------------+-----------------+
             |  Gemini 2.5 Flash (ai_brain.py)   |
             |  - Context & Intent Resolution    |
             |  - Multimodal Vision Processing   |
             |  - Function / Tool Matching       |
             +-----------------+-----------------+
                               |
             +-----------------+-----------------+
             |                                   |
             v                                   v
   +-------------------+               +-------------------+
   | System Tools      |               | Proactive Agent   |
   | (system_control)  |               | (background_agent)|
   | - Apps/Volume/Web |               | - Timers & Stats  |
   | - Active Vision   |               +-------------------+
   +-------------------+                         |
             |                                   |
             +-----------------+-----------------+
                               |
                               v
                   +-----------------------+
                   | Voice Output (TTS) &  |
                   | WebSocket UI Trigger  |
                   +-----------+-----------+
                               |
                               v
                   +-----------------------+
                   | Holographic Desktop   |
                   | Interface (PyQt6 UI)  |
                   +-----------------------+