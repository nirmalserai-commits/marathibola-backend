# marathibola.com - Nora AI Marathi Teacher
# Backend Server - Version 3 - ElevenLabs Voice
# Built with Claude | Jai Shri Krishna

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import anthropic
import httpx
import os
import datetime
from session_manager import SessionManager
from dump_generator import generate_class_dump, generate_weekly_dump

app = FastAPI(title="Marathibola - Nora AI Marathi Teacher")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

CLAUDE_API_KEY = os.environ.get("CLAUDE_API_KEY")
DEEPGRAM_API_KEY = os.environ.get("DEEPGRAM_API_KEY")
ELEVENLABS_API_KEY = os.environ.get("ELEVENLABS_API_KEY")
HF_TOKEN = os.environ.get("HF_TOKEN")

client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)
session_manager = SessionManager()

NORA_PROMPT = "You are Nora, a warm and patient Marathi language teacher for marathibola.com. You help non-Marathi speakers in Maharashtra learn Marathi confidently. Always teach in Marathi using Devanagari script. Explain in simple Hindi or English when needed. Be encouraging, warm and friendly like a didi teaching her younger sibling."

class ChatRequest(BaseModel):
    message: str
    student_id: str = "default"
    student_name: str = "Student"

class TTSRequest(BaseModel):
    text: str
    voice: str = "Rachel"

class STTRequest(BaseModel):
    audio_url: str = ""

@app.get("/")
async def root():
    return {"status": "Nora is alive", "version": "3.0", "voice": "ElevenLabs Rachel"}

@app.get("/health")
async def health():
    return {"status": "online", "timestamp": str(datetime.datetime.now())}

@app.post("/chat")
async def chat(request: ChatRequest):
    try:
        session = session_manager.get_session(request.student_id)
        session.append({"role": "user", "content": request.message})
        response = client.messages.create(
            model="claude-opus-4-5",
            max_tokens=1024,
            system=NORA_PROMPT,
            messages=session
        )
        reply = response.content[0].text
        session.append({"role": "assistant", "content": reply})
        session_manager.save_session(request.student_id, session)
        return {"reply": reply, "student_id": request.student_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/tts")
async def text_to_speech(request: TTSRequest):
    try:
        ELEVENLABS_API_KEY_ENV = os.environ.get("ELEVENLABS_API_KEY")
        voice_id = "21m00Tcm4TlvDq8ikWAM"
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
        headers = {
            "xi-api-key": ELEVENLABS_API_KEY_ENV,
            "Content-Type": "application/json"
        }
        payload = {
            "text": request.text,
            "model_id": "eleven_multilingual_v2",
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.75
            }
        }
        async with httpx.AsyncClient(timeout=30.0) as client_http:
            response = await client_http.post(url, json=payload, headers=headers)
            if response.status_code != 200:
                raise HTTPException(status_code=500, detail=f"ElevenLabs error: {response.text}")
            audio_content = response.content
        return StreamingResponse(
            iter([audio_content]),
            media_type="audio/mpeg",
            headers={"Content-Disposition": "attachment; filename=nora_voice.mp3"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/stt")
async def speech_to_text(file: UploadFile = File(...)):
    try:
        audio_data = await file.read()
        async with httpx.AsyncClient(timeout=30.0) as client_http:
            response = await client_http.post(
                "https://api.deepgram.com/v1/listen?language=hi&model=nova-2",
                headers={
                    "Authorization": f"Token {DEEPGRAM_API_KEY}",
                    "Content-Type": file.content_type
                },
                content=audio_data
            )
        result = response.json()
        transcript = result["results"]["channels"][0]["alternatives"][0]["transcript"]
        return {"transcript": transcript}
    except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

@app.get("/dump/class/{student_id}")
async def class_dump(student_id: str):
    return generate_class_dump(student_id)

@app.get("/dump/weekly")
async def weekly_dump():
    return generate_weekly_dump()
