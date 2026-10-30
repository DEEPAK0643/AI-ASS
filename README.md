# 🤖 J.A.R.V.I.S. // Mark VII Neural Assistant

[![Python](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg)](https://fastapi.tiangolo.com/)
[![Supabase](https://img.shields.io/badge/Supabase-Database-3ECF8E.svg)](https://supabase.com/)
[![Google Gemini](https://img.shields.io/badge/Gemini_API-3.8_Flash-4285F4.svg)](https://ai.google.dev/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

An advanced, Iron Man-inspired desktop voice assistant powered by **Google Gemini 3.8 Flash**, **Supabase Cloud Backend**, and a **Cybernetic Sci-Fi HUD**.

---

## ⚡ Core Capabilities

- **🧠 Google Gemini 3.8 Flash Intelligence**: Autonomous reasoning and function calling for system automation and live dialogue (without honorifics).
- **☁️ Supabase Cloud Backend**:
  - Persistent cross-session user memories (`jarvis_memories`).
  - Full conversational interaction audit history (`jarvis_conversations`).
  - Real-time hardware telemetry logging (`jarvis_telemetry`).
- **🎙️ Paul Bettany Voice Matrix**: Natural British neural speech synthesis powered by Microsoft Edge-TTS (`en-GB-RyanNeural`).
- **🔊 Responsive Arc Reactor Visualizer**: 60 FPS HTML5 canvas HUD featuring dynamic concentric technical rings, pulse cores, and Web Audio API spectrum analysis.
- **🖥️ Full Windows Automation**:
  - **WhatsApp Automation**: Launch WhatsApp Desktop or WhatsApp Web on command.
  - **App Launcher**: Chrome, Notepad, VS Code, Spotify, Calculator, Terminal, etc.
  - **System Diagnostics**: Live CPU, RAM, Battery, and Disk telemetry.
  - **Volume & Media Controls**: Play/Pause, Skip, Mute, Volume Up/Down.
  - **Screen Capture**: Instant screenshot capture and archival.
  - **Workstation Security**: Instant Windows PC lock.
  - **Web & YouTube**: Automated Google and YouTube searches.

---

## 📁 Project Architecture

```
jarvis-ai/
├── server.py              # FastAPI Web & WebSocket server + live telemetry streaming
├── gemini_brain.py        # Gemini 3.8 Flash agent + function calling tools
├── supabase_backend.py    # Supabase cloud database manager (memories, logs, telemetry)
├── supabase_schema.sql    # 1-Click database migration script for Supabase SQL Editor
├── system_tools.py        # Windows system automation engine (WhatsApp, media, diagnostics)
├── tts_engine.py          # Microsoft Edge Neural TTS synthesizer
├── requirements.txt       # Python dependencies
├── run.bat                # Windows 1-click launcher
├── .gitignore             # Protects .env, caches, and media files
├── .env.example           # Environment variables template
└── static/
    ├── index.html         # Cybernetic Iron Man HUD interface
    ├── style.css          # Holographic sci-fi theme stylesheet
    ├── app.js             # 60fps Arc Reactor canvas, Web Audio analyzer & voice STT
    └── audio/             # Generated voice cache
```

---

## 🚀 Quick Start Guide

### 1. Database Setup (Supabase)
1. Go to [Supabase](https://supabase.com) and create a free project.
2. Open the **SQL Editor** tab in your Supabase dashboard.
3. Copy the contents of `supabase_schema.sql` and click **Run**.
4. Retrieve your **Project URL** and **API Key** from **Project Settings > API**.

### 2. Configure Credentials
Copy `.env.example` to `.env`:
```env
GEMINI_API_KEY=your_gemini_api_key_here
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_KEY=your_supabase_anon_or_service_key
```
*(Or enter them directly via the ⚙️ Settings Modal in the browser HUD).*

### 3. Launch JARVIS
Simply double-click:
```cmd
run.bat
```
Or start manually via terminal:
```cmd
python server.py
```
Open **`http://127.0.0.1:8000`** in Google Chrome or Microsoft Edge.

---

## 🐙 How to Host This on GitHub

### Step 1: Initialize Git
In your terminal, navigate to the project directory:
```bash
git init
git add .
git commit -m "feat: Initial commit for J.A.R.V.I.S. Mark VII"
```

### Step 2: Push to GitHub
1. Create a new repository on [GitHub](https://github.com/new) (e.g. `jarvis-ai`).
2. Run the following commands:
```bash
git branch -M main
git remote add origin https://github.com/<YOUR_GITHUB_USERNAME>/jarvis-ai.git
git push -u origin main
```

*(Note: Your `.env` containing your real secret keys is automatically excluded by `.gitignore` so your credentials are kept 100% private and safe).*

---

## 🗣️ Voice & Text Command Cheatsheet

| Command | Action |
| :--- | :--- |
| `"Hello Jarvis"` | System greeting and status check |
| `"Open WhatsApp"` | Launches WhatsApp Desktop or WhatsApp Web |
| `"Remember that my car is a black Tesla"` | Stores fact in Supabase cloud memory |
| `"What is my car?"` | Recalls saved memory from Supabase |
| `"What do you remember?"` | Lists recent stored memories |
| `"System status"` / `"Diagnostics"` | Reports CPU, RAM, and Battery |
| `"Take screenshot"` | Captures screen to `screenshots/` |
| `"Open Chrome"` / `"Launch Notepad"` | Opens Windows applications |
| `"Search YouTube for Iron Man theme"` | Plays video on YouTube |
| `"Volume up"` / `"Mute audio"` | Adjusts Windows system audio |
| `"Play music"` / `"Next song"` | Windows multimedia controls |
| `"Lock PC"` | Locks your Windows workstation |
| `"What time is it?"` | Reports current date and time |
