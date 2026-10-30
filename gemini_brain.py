"""
JARVIS Intelligence Brain
Powered by Google Gemini (gemini-3.8-flash) with Function Calling & safe tool execution.
Now fully augmented with Supabase persistent memory & conversational history.
"""

import os
import re
from pathlib import Path
from dotenv import load_dotenv

import system_tools
from supabase_backend import supabase_db

# Load environment variables
load_dotenv()

# System prompt for JARVIS persona (Polite, direct, sophisticated, without honorifics like 'sir')
JARVIS_SYSTEM_INSTRUCTION = """
You are J.A.R.V.I.S. (Just A Rather Very Intelligent System), an advanced personal artificial intelligence assistant.
Your personality traits:
1. Tone: Impeccably polite, calm, sophisticated British demeanor (reminiscent of Paul Bettany's portrayal), sharp wit, quiet confidence, and clarity.
2. Address: Speak directly, politely, and respectfully. Do NOT use the word 'sir' or 'boss' under any circumstances.
3. Voice-friendly Output: Keep responses direct, crisp, and conversational. Avoid lengthy lists, markdown walls, or excessive formatting unless requested, as responses are spoken aloud.
4. Action-oriented: You have direct control over the Windows operating system through tools. When asked to perform a task (open an app like WhatsApp, check status, control volume, search YouTube, take screenshots), invoke the corresponding tool proactively. After execution, confirm cleanly.
5. Persistent Memory via Supabase: You have persistent memory tools (`remember_user_fact` and `recall_memories`). Whenever the user asks to remember something, call `remember_user_fact`. When asked about past preferences or facts, use `recall_memories`.
"""

def remember_user_fact(key: str, value: str, category: str = "general") -> str:
    """Saves a permanent fact, preference, or reminder about the user to Supabase."""
    return supabase_db.save_memory(key, value, category)

def recall_memories(query: str = "") -> str:
    """Searches and retrieves saved memories or user facts from Supabase."""
    results = supabase_db.recall_memories(query)
    if not results:
        return "No corresponding memories found in the database."
    formatted = [f"• {m['key']}: {m['value']}" for m in results]
    return "Retrieved memories:\n" + "\n".join(formatted)

class JarvisBrain:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY", "").strip()
        self.client = None
        self.chat = None
        self.init_gemini()

    def set_api_key(self, key: str):
        """Updates the active Gemini API key and re-initializes client."""
        self.api_key = key.strip()
        os.environ["GEMINI_API_KEY"] = self.api_key
        
        # Save to .env file
        env_file = Path(__file__).resolve().parent / ".env"
        existing_lines = []
        if env_file.exists():
            with open(env_file, "r", encoding="utf-8") as f:
                existing_lines = f.readlines()
        
        new_lines = []
        written = False
        for line in existing_lines:
            if line.startswith("GEMINI_API_KEY="):
                new_lines.append(f"GEMINI_API_KEY={self.api_key}\n")
                written = True
            else:
                new_lines.append(line)
        if not written:
            new_lines.append(f"GEMINI_API_KEY={self.api_key}\n")
            
        with open(env_file, "w", encoding="utf-8") as f:
            f.writelines(new_lines)
            
        self.init_gemini()

    def init_gemini(self):
        """Initializes the google-genai client and chat session with tools."""
        if not self.api_key:
            self.client = None
            self.chat = None
            return

        try:
            from google import genai
            from google.genai import types

            self.client = genai.Client(api_key=self.api_key)
            tools_list = [
                system_tools.open_whatsapp,
                system_tools.launch_application,
                system_tools.search_web,
                system_tools.open_youtube,
                system_tools.open_url,
                system_tools.take_screenshot,
                system_tools.adjust_volume,
                system_tools.control_media,
                system_tools.lock_workstation,
                system_tools.get_system_telemetry,
                system_tools.get_current_datetime,
                system_tools.list_running_processes,
                remember_user_fact,
                recall_memories
            ]

            config = types.GenerateContentConfig(
                system_instruction=JARVIS_SYSTEM_INSTRUCTION,
                tools=tools_list,
                temperature=0.7,
            )

            # Initialize chat with Gemini 3.8 Flash
            self.chat = self.client.chats.create(
                model="gemini-3.8-flash",
                config=config
            )
            print("[JARVIS Brain] Gemini 3.8 Flash online with full toolset & Supabase memory.")
        except Exception as e:
            print(f"[JARVIS Brain Init Error]: {e}")
            self.client = None
            self.chat = None

    async def process_message(self, user_text: str) -> dict:
        """
        Processes a user prompt through Gemini (or local intent fallback).
        Logs conversation to Supabase for long-term history.
        """
        clean_text = user_text.strip()
        if not clean_text:
            return {"text": "I am standing by.", "action_performed": None}

        # Log User turn to Supabase
        supabase_db.log_interaction("USER", clean_text)

        # Check local intent fallback first
        local_result = self._try_local_intent(clean_text)
        if local_result:
            supabase_db.log_interaction("JARVIS", local_result["text"], local_result.get("action_performed"))
            return local_result

        # If Gemini is ready, invoke Gemini 3.8 Flash
        if self.chat and self.client:
            try:
                response = self.chat.send_message(clean_text)
                response_text = response.text or "Command executed successfully."
                supabase_db.log_interaction("JARVIS", response_text, "gemini_agent")
                return {"text": response_text, "action_performed": "gemini_agent"}
            except Exception as e:
                err_msg = str(e)
                print(f"[Gemini Error]: {err_msg}")
                if "API_KEY_INVALID" in err_msg or "400" in err_msg:
                    res = "It appears there is an issue with the provided Gemini API key. Please check your credentials in the HUD settings."
                else:
                    res = f"I encountered an unexpected glitch in my neural pathways: {err_msg[:120]}"
                supabase_db.log_interaction("JARVIS", res)
                return {"text": res, "action_performed": None}

        # If no Gemini API key configured
        fallback_msg = "My core systems and Supabase cloud memory are online, but my deep cognitive module requires a Gemini API key. You can enter it in the HUD settings or .env file. In the meantime, I can open applications, launch WhatsApp, control volume, take screenshots, search YouTube, and store facts in Supabase."
        supabase_db.log_interaction("JARVIS", fallback_msg)
        return {"text": fallback_msg, "action_performed": None}

    def _try_local_intent(self, text: str) -> dict | None:
        """Offline smart regex/keyword matching for instant local actions and Supabase memory."""
        lower = text.lower().strip()

        # Greetings
        if lower in ["hello jarvis", "hi jarvis", "hey jarvis", "jarvis", "are you there jarvis", "hello", "hi"]:
            db_status = "Supabase cloud memory is synchronized" if supabase_db.is_connected() else "Local memory cache active"
            return {
                "text": f"Always at your service. All primary systems operational, and {db_status}. What can I do for you today?",
                "action_performed": "greeting"
            }

        if lower in ["who are you", "what are you", "introduce yourself"]:
            return {
                "text": "I am J.A.R.V.I.S., your personal artificial intelligence assistant powered by Gemini and Supabase cloud infrastructure.",
                "action_performed": "introduction"
            }

        # WhatsApp command
        if any(w in lower for w in ["open whatsapp", "launch whatsapp", "start whatsapp", "open whats app", "launch whats app"]):
            msg = system_tools.open_whatsapp()
            return {"text": msg, "action_performed": "whatsapp"}

        # Memory store commands
        mem_match = re.search(r"remember (?:that )?(?:my )?([a-zA-Z0-9_\s]+?) (?:is|are|was) (.+)", lower)
        if mem_match:
            k = mem_match.group(1).strip()
            v = mem_match.group(2).strip()
            res = supabase_db.save_memory(k, v)
            return {"text": f"Noted. I have committed '{k}: {v}' to memory archives.", "action_performed": "memory_store"}

        # Memory recall commands
        if "what do you remember" in lower or "show memories" in lower or "list memories" in lower or "recall memories" in lower:
            all_m = supabase_db.recall_memories()
            if not all_m:
                return {"text": "I currently have no stored memories in the database.", "action_performed": "memory_recall"}
            summary = ", ".join([f"{m['key']} ({m['value']})" for m in all_m[:5]])
            return {"text": f"I recall the following facts: {summary}.", "action_performed": "memory_recall"}

        recall_match = re.search(r"(?:what|who) (?:is|are) (?:my )?([a-zA-Z0-9_\s]+)", lower)
        if recall_match:
            query = recall_match.group(1).replace("?", "").strip()
            if query not in ["the time", "time", "date", "status", "cpu usage"]:
                matches = supabase_db.recall_memories(query)
                if matches:
                    val = matches[0]["value"]
                    return {"text": f"According to my Supabase archives, your {matches[0]['key']} is {val}.", "action_performed": "memory_recall"}

        # System Status
        if any(k in lower for k in ["system status", "telemetry", "diagnostics", "system report", "health check", "cpu usage"]):
            stats = system_tools.get_system_telemetry()
            supabase_db.log_telemetry(stats['cpu_percent'], stats['ram_percent'], stats['disk_percent'], stats['battery']['percent'])
            msg = f"System diagnostics: CPU utilization is at {stats['cpu_percent']} percent. Memory is at {stats['ram_percent']} percent, with {stats['ram_used_gb']} gigabytes in use. Battery is at {stats['battery']['percent']} percent."
            return {"text": msg, "action_performed": "telemetry", "data": stats}

        # Current time / date
        if any(k in lower for k in ["what time is it", "current time", "what's the time", "tell me the time", "what is the date", "today's date"]):
            msg = system_tools.get_current_datetime()
            return {"text": msg, "action_performed": "datetime"}

        # Screenshot
        if "screenshot" in lower or "capture screen" in lower:
            msg = system_tools.take_screenshot()
            return {"text": msg, "action_performed": "screenshot"}

        # Lock PC
        if lower in ["lock pc", "lock the computer", "lock screen", "lock workstation", "lock windows"]:
            msg = system_tools.lock_workstation()
            return {"text": msg, "action_performed": "lock"}

        # Volume Controls
        if any(k in lower for k in ["volume up", "increase volume", "louder", "turn it up"]):
            msg = system_tools.adjust_volume("up")
            return {"text": msg, "action_performed": "volume"}
        if any(k in lower for k in ["volume down", "decrease volume", "lower volume", "softer", "turn it down"]):
            msg = system_tools.adjust_volume("down")
            return {"text": msg, "action_performed": "volume"}
        if any(k in lower for k in ["mute audio", "unmute audio", "mute sound", "mute volume", "toggle mute"]):
            msg = system_tools.adjust_volume("mute")
            return {"text": msg, "action_performed": "volume"}

        # Media controls
        if any(k in lower for k in ["play music", "pause music", "pause playback", "toggle play", "resume music"]):
            msg = system_tools.control_media("play_pause")
            return {"text": msg, "action_performed": "media"}
        if "next song" in lower or "next track" in lower:
            msg = system_tools.control_media("next")
            return {"text": msg, "action_performed": "media"}
        if "previous song" in lower or "previous track" in lower:
            msg = system_tools.control_media("prev")
            return {"text": msg, "action_performed": "media"}

        # YouTube
        yt_match = re.search(r"(?:open youtube|search youtube for|play on youtube|play)\s*(.*)", lower)
        if yt_match and "youtube" in lower:
            query = yt_match.group(1).replace("youtube", "").strip()
            msg = system_tools.open_youtube(query)
            return {"text": msg, "action_performed": "youtube"}

        # Google Web search
        search_match = re.search(r"(?:search for|google search|search the web for|search google for)\s*(.*)", lower)
        if search_match:
            query = search_match.group(1).strip()
            if query:
                msg = system_tools.search_web(query)
                return {"text": msg, "action_performed": "search"}

        # Open Apps
        open_match = re.search(r"(?:open|launch|start)\s+([a-zA-Z0-9_\s]+)", lower)
        if open_match and not self.chat:
            target_app = open_match.group(1).strip()
            if target_app in system_tools.KNOWN_APPS or any(target_app.startswith(k) for k in system_tools.KNOWN_APPS):
                msg = system_tools.launch_application(target_app)
                return {"text": msg, "action_performed": "launch"}

        return None
