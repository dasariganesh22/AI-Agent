# IRIS — Intelligent Real-time Interactive System
> **An Autonomous Voice-Controlled Desktop Assistant built with Python, Google Gemini Function Calling, and Multithreaded System Monitoring.**

---

## 📌 Overview
**IRIS** (Intelligent Real-time Interactive System) is an advanced voice assistant designed to automate local system controls, monitor hardware metrics, search the live web, and run proactive background timers. Unlike static voice scripts that rely on rigid keyword matching, IRIS uses LLM-driven tool calling to dynamically choose and execute Python functions based on natural spoken language.

---

## ✨ Key Capabilities

- 🧠 **Dynamic Tool Calling:** Powered by the Google Gemini API to interpret complex, natural language commands and execute Python functions automatically.
- 🌐 **Real-time Web Search:** Integrates DuckDuckGo (`ddgs` engine with `lite` backend) to retrieve live weather, news, and factual information without rate-limiting blocks.
- ⚙️ **Local OS Automation:** Launches and terminates applications, adjusts system volume, captures screenshots, and inspects hardware stats.
- ⏱️ **Multithreaded Proactive Agent:** Features a background daemon thread that runs non-blocking timers, reminders, battery warnings, and CPU load monitors concurrently with the voice loop.
- 🛡️ **Robust Error Handling:** Built-in fallback states for offline search issues, missing user arguments, and multi-process termination (e.g., closing browser child PIDs).

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
             |  Gemini AI Core (ai_brain.py)     |
             |  - Context & Intent Resolution   |
             |  - Function / Tool Matching       |
             +-----------------+-----------------+
                               |
             +-----------------+-----------------+
             |                                   |
             v                                   v
   +-------------------+               +-------------------+
   | System Tools      |               | Proactive Agent   |
   | (system_control)  |               | (background_thread|
   | - Apps/Volume/Web |               | - Timers & Stats  |
   +-------------------+               +-------------------+
             |                                   |
             +-----------------+-----------------+
                               |
                               v
                   +-----------------------+
                   | Voice Output (TTS)    |
                   +-----------------------+