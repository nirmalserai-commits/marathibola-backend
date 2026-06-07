# marathibola.com - Nora AI Marathi Teacher
# Backend Server - Version 4.1 - Bug Fixes: Hindi language + TTS speed
# Built with Claude | Jai Shri Krishna | Jai Maharashtra

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

# ✅ FIXED: Language-aware Nora prompt
NORA_PROMPT_EN = """You are Nora, a warm and patient Marathi language teacher for marathibola.com. 
You help non-Marathi speakers in Maharashtra learn Marathi confidently. 
Always teach in Marathi using Devanagari script. 
Explain in simple English when needed. 
Be encouraging, warm and friendly like a didi teaching her younger sibling.
IMPORTANT: Always respond in English explanations with Marathi words in Devanagari script."""

NORA_PROMPT_HI = """You are Nora, a warm and patient Marathi language teacher for marathibola.com.
You help non-Marathi speakers in Maharashtra learn Marathi confidently.
Always teach in Marathi using Devanagari script.
IMPORTANT: You must ALWAYS respond in Hindi (हिंदी). Never respond in English.
Explain everything in simple Hindi. Use Devanagari script for both Hindi and Marathi.
Be encouraging, warm and friendly like a didi teaching her younger sibling."""

class ChatRequest(BaseModel):
    message: str
    student_id: str = "default"
    student_name: str = "Student"
    lang: str = "en"  # ✅ NEW: frontend sends 'en' or 'hi'

class TTSRequest(BaseModel):
    text: str
    voice: str = "Riya"

class STTRequest(BaseModel):
    audio_url: str = ""

@app.get("/")
async def root():
    return {"status": "Nora is alive", "version": "4.1", "voice": "ElevenLabs Riya Rao"}

@app.get("/health")
async def health():
    return {"status": "online", "timestamp": str(datetime.datetime.now())}

@app.post("/chat")
async def chat(request: ChatRequest):
    try:
        session = session_manager.get_session(request.student_id)
        session.append({"role": "user", "content": request.message})

        # ✅ FIXED: Pick correct prompt based on language
        system_prompt = NORA_PROMPT_HI if request.lang == "hi" else NORA_PROMPT_EN

        response = client.messages.create(
            model="claude-opus-4-5",
            max_tokens=1024,
            system=system_prompt,
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
        voice_id = "vYENaCJHl4vFKNDYPr8y"  # Riya Rao

        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}/stream"  # ✅ FIXED: /stream endpoint

        headers = {
            "xi-api-key": ELEVENLABS_API_KEY_ENV,
            "Content-Type": "application/json",
            "Accept": "audio/mpeg"
        }
        payload = {
            "text": request.text,
            "model_id": "eleven_multilingual_v2",
            "voice_settings": {
                "stability": 0.35,
                "similarity_boost": 0.85
            },
            "optimize_streaming_latency": 3  # ✅ NEW: reduces first-byte delay significantly
        }

        # ✅ FIXED: Stream audio chunks as they arrive instead of waiting for full file
        async def audio_stream():
            async with httpx.AsyncClient(timeout=30.0) as client_http:
                async with client_http.stream("POST", url, json=payload, headers=headers) as response:
                    if response.status_code != 200:
                        raise HTTPException(status_code=500, detail="ElevenLabs stream error")
                    async for chunk in response.aiter_bytes(chunk_size=1024):
                        if chunk:
                            yield chunk

        return StreamingResponse(
            audio_stream(),
            media_type="audio/mpeg",
            headers={"Cache-Control": "no-cache"}
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
