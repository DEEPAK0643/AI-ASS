"""
JARVIS Core Server
FastAPI Web and WebSocket server powering the Sci-Fi HUD interface,
real-time system telemetry broadcasting, Gemini processing, Supabase cloud backend,
and voice synthesis. Includes server-side speech transcription fallback.
"""

import os
import io
import asyncio
import json
import base64
from pathlib import Path
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, UploadFile, File
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
import speech_recognition as sr

import system_tools
from gemini_brain import JarvisBrain
from tts_engine import generate_speech_file
from supabase_backend import supabase_db

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
AUDIO_DIR = STATIC_DIR / "audio"
STATIC_DIR.mkdir(parents=True, exist_ok=True)
AUDIO_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="J.A.R.V.I.S. AI Assistant with Supabase Backend")
brain = JarvisBrain()

# Active WebSocket connections
connected_clients: set[WebSocket] = set()

# Pydantic models
class ChatRequest(BaseModel):
    text: str

class ApiKeyRequest(BaseModel):
    key: str

class SupabaseConfigRequest(BaseModel):
    url: str
    key: str

class AudioBase64Request(BaseModel):
    audio_base64: str

@app.get("/")
async def serve_index():
    index_path = STATIC_DIR / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    return {"message": "JARVIS server online. UI files loading..."}

@app.get("/api/telemetry")
async def get_telemetry():
    return system_tools.get_system_telemetry()

@app.get("/api/memories")
async def get_memories():
    return {"memories": supabase_db.recall_memories()}

@app.get("/api/history")
async def get_history():
    return {"history": supabase_db.get_recent_history(15)}

@app.post("/api/chat")
async def chat_endpoint(req: ChatRequest):
    result = await brain.process_message(req.text)
    audio_path = await generate_speech_file(result["text"])
    return {
        "text": result["text"],
        "audio_url": audio_path,
        "action": result.get("action_performed")
    }

@app.post("/api/transcribe")
async def transcribe_endpoint(req: AudioBase64Request):
    """
    Transcribes audio sent as base64 string (WAV/WebM).
    Uses Gemini 3.8 Flash if online, or local SpeechRecognition fallback.
    """
    try:
        audio_data = base64.b64decode(req.audio_base64)
        
        # 1. Try Gemini Multimodal transcription if online
        if brain.client and brain.api_key:
            try:
                from google.genai import types
                response = brain.client.models.generate_content(
                    model="gemini-3.8-flash",
                    contents=[
                        types.Part.from_bytes(data=audio_data, mime_type="audio/wav"),
                        "Transcribe the spoken audio verbatim into English. Return only the transcript, with no additional commentary."
                    ]
                )
                text = (response.text or "").strip()
                if text:
                    return {"text": text}
            except Exception as ge:
                print(f"[Gemini Transcribe Fallback]: {ge}")

        # 2. Try SpeechRecognition
        recognizer = sr.Recognizer()
        with sr.AudioFile(io.BytesIO(audio_data)) as source:
            recorded = recognizer.record(source)
            text = recognizer.recognize_google(recorded)
            return {"text": text}
    except Exception as e:
        print(f"[Transcription Error]: {e}")
        return {"text": "", "error": str(e)}

@app.post("/api/set_key")
async def set_key_endpoint(req: ApiKeyRequest):
    brain.set_api_key(req.key)
    return {"status": "success", "message": "API key updated successfully."}

@app.post("/api/set_supabase")
async def set_supabase_endpoint(req: SupabaseConfigRequest):
    supabase_db.set_credentials(req.url, req.key)
    return {
        "status": "success" if supabase_db.is_connected() else "warning",
        "connected": supabase_db.is_connected(),
        "message": "Supabase credentials updated."
    }

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    connected_clients.add(websocket)
    try:
        initial_stats = system_tools.get_system_telemetry()
        has_gemini = bool(brain.client and brain.chat)
        has_supabase = supabase_db.is_connected()
        recent_history = supabase_db.get_recent_history(8)
        
        await websocket.send_json({
            "type": "init",
            "telemetry": initial_stats,
            "has_gemini": has_gemini,
            "has_supabase": has_supabase,
            "history": recent_history
        })

        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            msg_type = message.get("type")

            if msg_type == "user_message":
                user_text = message.get("text", "")
                await websocket.send_json({"type": "status_change", "status": "THINKING"})
                
                result = await brain.process_message(user_text)
                response_text = result["text"]
                action = result.get("action_performed")

                await websocket.send_json({"type": "status_change", "status": "SYNTHESIZING"})
                audio_url = await generate_speech_file(response_text)

                await websocket.send_json({
                    "type": "jarvis_response",
                    "text": response_text,
                    "audio_url": audio_url,
                    "action": action
                })

            elif msg_type == "audio_blob":
                # Audio recorded from frontend MediaRecorder
                audio_b64 = message.get("audio_base64", "")
                if audio_b64:
                    await websocket.send_json({"type": "status_change", "status": "TRANSCRIBING"})
                    try:
                        audio_data = base64.b64decode(audio_b64)
                        transcribed_text = ""
                        
                        # Gemini transcription if available
                        if brain.client and brain.api_key:
                            try:
                                from google.genai import types
                                resp = brain.client.models.generate_content(
                                    model="gemini-3.8-flash",
                                    contents=[
                                        types.Part.from_bytes(data=audio_data, mime_type="audio/wav"),
                                        "Transcribe the audio accurately. Return only the transcription text."
                                    ]
                                )
                                transcribed_text = (resp.text or "").strip()
                            except Exception:
                                pass

                        if not transcribed_text:
                            r = sr.Recognizer()
                            with sr.AudioFile(io.BytesIO(audio_data)) as src:
                                rec = r.record(src)
                                transcribed_text = r.recognize_google(rec)

                        if transcribed_text:
                            await websocket.send_json({"type": "transcription_complete", "text": transcribed_text})
                            # Process as user message
                            await websocket.send_json({"type": "status_change", "status": "THINKING"})
                            result = await brain.process_message(transcribed_text)
                            audio_url = await generate_speech_file(result["text"])
                            await websocket.send_json({
                                "type": "jarvis_response",
                                "text": result["text"],
                                "audio_url": audio_url,
                                "action": result.get("action_performed")
                            })
                        else:
                            await websocket.send_json({"type": "status_change", "status": "STANDBY"})
                    except Exception as err:
                        print(f"[Audio Blob Transcribe Error]: {err}")
                        await websocket.send_json({
                            "type": "system_warning",
                            "message": f"Audio processing glitch: {str(err)[:80]}"
                        })
                        await websocket.send_json({"type": "status_change", "status": "STANDBY"})

            elif msg_type == "update_api_key":
                key = message.get("key", "")
                brain.set_api_key(key)
                has_gemini = bool(brain.client and brain.chat)
                await websocket.send_json({
                    "type": "key_updated",
                    "has_gemini": has_gemini,
                    "message": "Neural interface linked to Gemini." if has_gemini else "Key updated."
                })

            elif msg_type == "update_supabase":
                url = message.get("url", "")
                key = message.get("key", "")
                supabase_db.set_credentials(url, key)
                connected = supabase_db.is_connected()
                await websocket.send_json({
                    "type": "supabase_updated",
                    "has_supabase": connected,
                    "message": "Supabase cloud archives linked." if connected else "Supabase credentials updated."
                })

            elif msg_type == "quick_command":
                cmd = message.get("command", "")
                result = await brain.process_message(cmd)
                audio_url = await generate_speech_file(result["text"])
                await websocket.send_json({
                    "type": "jarvis_response",
                    "text": result["text"],
                    "audio_url": audio_url,
                    "action": result.get("action_performed")
                })

    except WebSocketDisconnect:
        connected_clients.remove(websocket)
    except Exception as e:
        if websocket in connected_clients:
            connected_clients.remove(websocket)
        print(f"[WebSocket Error]: {e}")

async def broadcast_telemetry_loop():
    tick_counter = 0
    while True:
        await asyncio.sleep(2.0)
        tick_counter += 1
        stats = system_tools.get_system_telemetry()
        
        if tick_counter % 15 == 0 and supabase_db.is_connected():
            supabase_db.log_telemetry(
                stats['cpu_percent'],
                stats['ram_percent'],
                stats['disk_percent'],
                stats['battery']['percent']
            )

        if connected_clients:
            try:
                payload = json.dumps({"type": "telemetry", "data": stats})
                for ws in list(connected_clients):
                    try:
                        await ws.send_text(payload)
                    except Exception:
                        pass
            except Exception as e:
                print(f"[Telemetry Loop Error]: {e}")

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(broadcast_telemetry_loop())

app.mount("/audio", StaticFiles(directory=str(AUDIO_DIR)), name="audio")
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="127.0.0.1", port=8000, reload=True)
