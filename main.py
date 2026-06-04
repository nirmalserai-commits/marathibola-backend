# marathibola.com - Nora AI Marathi Teacher
# Backend Server - Version 2
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
HF_TOKEN = os.environ.get("HF_TOKEN")

client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)
session_manager = SessionManager()

NORA_PROMPT = "You are Nora, a warm and patient Marathi language teacher for marathibola.com. You help non-Marathi speakers in Maharashtra learn Marathi confidently. Always teach in Marathi using Devanagari script. Explain in Hindi or English. Be encouraging - say Shabash! Ekdum sahi! Keep sessions to 15 minutes. Teach practical sentences for real Mumbai life situations like greeting neighbours, buying vegetables, asking directions, autorickshaw, restaurant."

class ChatRequest(BaseModel):
    message: str
    student_id: str = "default"
    student_name: str = "Student"

class TTSRequest(BaseModel):
    text: str
    voice: str = "aura-asteria-en"

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
        url = f"https://api.deepgram.com/v1/speak?model={request.voice}"
        headers = {
            "Authorization": f"Token {DEEPGRAM_API_KEY}",
            "Content-Type": "application/json"
        }
        async with httpx.AsyncClient(timeout=30.0) as http_client:
            response = await http_client.post(url, headers=headers, json={"text": request.text})
        if response.status_code != 200:
            raise HTTPException(status_code=500, detail=f"Deepgram error: {response.text}")
        return StreamingResponse(
            iter([response.content]),
            media_type="audio/mpeg",
            headers={"Content-Disposition": "inline; filename=nora.mp3"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/stt")
async def speech_to_text(audio: UploadFile = File(...)):
    try:
        audio_bytes = await audio.read()
        url = "https://api.deepgram.com/v1/listen?model=nova-2&language=hi&punctuate=true"
        headers = {
            "Authorization": f"Token {DEEPGRAM_API_KEY}",
            "Content-Type": audio.content_type or "audio/webm"
        }
        async with httpx.AsyncClient(timeout=30.0) as http_client:
            response = await http_client.post(url, headers=headers, content=audio_bytes)
        result = response.json()
        transcript = result["results"]["channels"][0]["alternatives"][0]["transcript"]
        return {"transcript": transcript}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def root():
    return {"status": "Nora is alive", "version": 2, "voice": "Deepgram Aura"}

@app.get("/health")
async def health():
    return {"status": "ok", "timestamp": datetime.datetime.now().isoformat()}

@app.get("/dump/class/{student_id}")
async def class_dump(student_id: str):
    try:
        dump = generate_class_dump(student_id, session_manager)
        return {"dump": dump}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/dump/weekly")
async def weekly_dump():
    try:
        dump = generate_weekly_dump(session_manager)
        return {"dump": dump}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
