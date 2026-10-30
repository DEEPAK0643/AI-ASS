"""
JARVIS Text-to-Speech Engine
Utilizes Microsoft Edge Neural TTS with British Ryan / Thomas neural voices.
Produces crisp, natural, Paul Bettany-esque JARVIS vocal responses.
"""

import os
import hashlib
import edge_tts
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
AUDIO_DIR = BASE_DIR / "static" / "audio"
AUDIO_DIR.mkdir(parents=True, exist_ok=True)

# Signature JARVIS voice: en-GB-RyanNeural (British, sophisticated, calm)
DEFAULT_VOICE = "en-GB-RyanNeural"

async def generate_speech_file(text: str, voice: str = DEFAULT_VOICE) -> str:
    """
    Generates an MP3 file from text using Edge-TTS.
    Returns relative web path (e.g., '/audio/{hash}.mp3') for web playback.
    """
    if not text.strip():
        return ""
    
    # Hash text and voice for cache key
    cache_key = hashlib.md5(f"{voice}:{text}".encode("utf-8")).hexdigest()
    filename = f"{cache_key}.mp3"
    filepath = AUDIO_DIR / filename
    
    # Return cached if already generated
    if not filepath.exists():
        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(str(filepath))
        
    return f"/audio/{filename}"
