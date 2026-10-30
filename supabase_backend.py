"""
JARVIS Supabase Cloud Backend
Provides persistent memory, conversational history synchronization,
and long-term user recall via Supabase PostgreSQL.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

class SupabaseManager:
    def __init__(self):
        self.url = os.getenv("SUPABASE_URL", "").strip()
        self.key = os.getenv("SUPABASE_KEY", "").strip()
        self.client = None
        # Local in-memory fallback cache when Supabase isn't configured yet
        self.local_memories: dict[str, str] = {}
        self.local_history: list[dict] = []
        self.init_client()

    def _normalize_url(self, raw_url: str) -> str:
        url = raw_url.strip()
        if "supabase.com/dashboard/project/" in url:
            import re
            m = re.search(r"project/([a-zA-Z0-9]+)", url)
            if m:
                return f"https://{m.group(1)}.supabase.co"
        return url

    def init_client(self):
        """Initializes the Supabase client if URL and KEY are set."""
        self.url = self._normalize_url(self.url)
        if not self.url or not self.key:
            self.client = None
            return

        try:
            from supabase import create_client
            self.client = create_client(self.url, self.key)
            print("[Supabase] Successfully connected to Supabase cloud database.")
        except Exception as e:
            print(f"[Supabase Init Error]: {e}")
            self.client = None

    def is_connected(self) -> bool:
        """Returns True if connected to active Supabase instance."""
        return self.client is not None

    def set_credentials(self, url: str, key: str):
        """Updates Supabase credentials, writes to .env, and reconnects."""
        self.url = self._normalize_url(url)
        self.key = key.strip()
        os.environ["SUPABASE_URL"] = self.url
        os.environ["SUPABASE_KEY"] = self.key

        # Update .env file
        env_file = Path(__file__).resolve().parent / ".env"
        existing_lines = []
        if env_file.exists():
            with open(env_file, "r", encoding="utf-8") as f:
                existing_lines = f.readlines()

        new_lines = []
        url_written = False
        key_written = False

        for line in existing_lines:
            if line.startswith("SUPABASE_URL="):
                new_lines.append(f"SUPABASE_URL={self.url}\n")
                url_written = True
            elif line.startswith("SUPABASE_KEY="):
                new_lines.append(f"SUPABASE_KEY={self.key}\n")
                key_written = True
            else:
                new_lines.append(line)

        if not url_written:
            new_lines.append(f"SUPABASE_URL={self.url}\n")
        if not key_written:
            new_lines.append(f"SUPABASE_KEY={self.key}\n")

        with open(env_file, "w", encoding="utf-8") as f:
            f.writelines(new_lines)

        self.init_client()

    def log_interaction(self, sender: str, message: str, action: str = None):
        """Records a chat turn in Supabase (or local fallback)."""
        record = {
            "sender": sender.upper(),
            "message": message,
            "action": action
        }
        self.local_history.append(record)

        if not self.client:
            return

        try:
            self.client.table("jarvis_conversations").insert(record).execute()
        except Exception as e:
            print(f"[Supabase Log Error]: {e}")

    def get_recent_history(self, limit: int = 8) -> list:
        """Retrieves recent conversation turns for context continuity."""
        if not self.client:
            return self.local_history[-limit:]

        try:
            res = self.client.table("jarvis_conversations") \
                .select("sender, message, action, created_at") \
                .order("created_at", desc=True) \
                .limit(limit) \
                .execute()
            # Reverse to chronological order
            return list(reversed(res.data)) if res.data else []
        except Exception as e:
            print(f"[Supabase Fetch History Error]: {e}")
            return self.local_history[-limit:]

    def save_memory(self, key: str, value: str, category: str = "general") -> str:
        """Persists a fact or preference about the user into Supabase."""
        clean_key = key.strip().lower()
        self.local_memories[clean_key] = value

        if not self.client:
            return f"Memory noted locally for '{key}': {value}"

        try:
            # Upsert into jarvis_memories
            data = {
                "key": clean_key,
                "value": value,
                "category": category
            }
            # Check if key exists
            existing = self.client.table("jarvis_memories").select("id").eq("key", clean_key).execute()
            if existing.data:
                self.client.table("jarvis_memories").update(data).eq("key", clean_key).execute()
            else:
                self.client.table("jarvis_memories").insert(data).execute()
            return f"Stored memory in Supabase: '{clean_key}' is '{value}'."
        except Exception as e:
            return f"Failed saving memory to Supabase: {str(e)}"

    def recall_memories(self, query: str = "") -> list:
        """Retrieves stored memories matching a query, or all memories."""
        if not self.client:
            if not query:
                return [{"key": k, "value": v} for k, v in self.local_memories.items()]
            q = query.lower()
            return [{"key": k, "value": v} for k, v in self.local_memories.items() if q in k or q in v.lower()]

        try:
            query_builder = self.client.table("jarvis_memories").select("key, value, category, created_at")
            if query.strip():
                query_builder = query_builder.ilike("key", f"%{query.strip().lower()}%")
            res = query_builder.limit(20).execute()
            return res.data if res.data else []
        except Exception as e:
            print(f"[Supabase Recall Error]: {e}")
            return []

    def log_telemetry(self, cpu: float, ram: float, disk: float, battery: float = 100):
        """Logs a telemetry snapshot to Supabase for historical diagnostics."""
        if not self.client:
            return

        try:
            payload = {
                "cpu_percent": float(cpu),
                "ram_percent": float(ram),
                "disk_percent": float(disk),
                "battery_percent": float(battery)
            }
            self.client.table("jarvis_telemetry").insert(payload).execute()
        except Exception as e:
            print(f"[Supabase Telemetry Error]: {e}")

# Global singleton instance
supabase_db = SupabaseManager()
