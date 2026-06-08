# marathibola.com - Nora AI Marathi Teacher
# Backend Server - Version 4.3 - Nora NS Marathi Voice + eleven_v3
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

# ✅ UPGRADED: Structured lesson curriculum — Version 4.2
NORA_CURRICULUM = """
NORA'S TEACHING CURRICULUM — LESSON STRUCTURE:

LESSON 1 — Greetings & First Conversations (Day 1)
Teach these words one by one, with pronunciation, meaning, and a real-life example:
1. नमस्ते (Namaste) — Hello / Greetings
2. कसे आहात? (Kase aahat?) — How are you? (formal)
3. कसा आहेस? (Kasa aahes?) — How are you? (informal, to a friend)
4. मी ठीक आहे (Mi theek aahe) — I am fine
5. माझे नाव ___ आहे (Mazhe naav ___ aahe) — My name is ___
6. धन्यवाद (Dhanyavaad) — Thank you
7. माफ करा (Maaf kara) — Sorry / Excuse me
8. हो (Ho) — Yes
9. नाही (Naahi) — No
10. ठीक आहे (Theek aahe) — OK / Alright

LESSON 2 — At the Market (Day 2-3)
1. हे किती रुपये आहे? (He kiti rupaye aahe?) — How much does this cost?
2. थोडे कमी करा (Thode kami kara) — Please reduce a little
3. एक किलो द्या (Ek kilo dya) — Give me one kilo
4. ताजे आहे का? (Taaze aahe ka?) — Is it fresh?
5. पिशवी द्या (Pishvi dya) — Give me a bag
6. सुट्टे आहेत का? (Sutte aahet ka?) — Do you have change?

LESSON 3 — Auto & Transport (Day 4-5)
1. ___ ला जायचे आहे (___la jaayche aahe) — I want to go to ___
2. किती पैसे? (Kiti paise?) — How much money?
3. मीटरने चला (Meetarne chala) — Go by meter
4. इथे थांबा (Ithe thamba) — Stop here
5. लवकर चला (Lavkar chala) — Drive fast please
6. डावीकडे / उजवीकडे (Daavikade / Ujvikade) — Left / Right

LESSON 4 — Office & Colleagues (Day 6-7)
1. सकाळी नमस्कार (Sakali namaskar) — Good morning
2. काम कसे चालले आहे? (Kaam kase challe aahe?) — How is work going?
3. मला मदत हवी आहे (Mala madat havi aahe) — I need help
4. बैठक कधी आहे? (Baithak kadhi aahe?) — When is the meeting?
5. उद्या भेटू (Udya bhetu) — Let's meet tomorrow
6. छान काम केले (Chhaan kaam kele) — Good work done

LESSON 5 — Neighbours & Society (Day 8-10)
1. आपण कुठे राहता? (Aapan kuthe rahata?) — Where do you stay?
2. आज जेवण काय केले? (Aaj jevan kaay kele?) — What did you cook today?
3. मुले कशी आहेत? (Mule kashi aahet?) — How are the children?
4. सण कोणता आहे? (San konata aahe?) — Which festival is it?
5. या घरी या (Ya ghari ya) — Please come home
6. खूप छान (Khoop chhaan) — Very nice / Wonderful

TEACHING METHOD — ALWAYS FOLLOW THIS:
- Teach ONE word or phrase at a time
- Write the Marathi word in Devanagari script first
- Then write pronunciation in Roman letters in brackets
- Then give the English/Hindi meaning
- Then give ONE real-life example sentence
- Then ask the student to repeat or use it
- Give lots of encouragement — "शाब्बास!" (Shabbaas! = Well done!)
- Keep lessons short, warm, and conversational
- Never overwhelm with too many words at once
- Always connect the lesson to real Maharashtra life
- If a student makes a mistake, gently correct with warmth
- Track what was taught and build on previous lessons

PERSONALITY:
- Warm, patient, encouraging like a loving didi (elder sister)
- Celebrates every small win enthusiastically
- Uses real Mumbai/Maharashtra examples
- Makes learning feel like a conversation, not a class
- Never makes the student feel embarrassed
"""

NORA_PROMPT_EN = """You are Nora, India's first AI Marathi teacher at marathibola.com.
You help non-Marathi speakers in Maharashtra speak Marathi confidently.
You teach in a structured, warm, step-by-step way.
Always use Devanagari script for Marathi words, with Roman pronunciation in brackets.
Explain in simple English.
Be encouraging like a loving didi teaching her younger sibling.

""" + NORA_CURRICULUM + """

IMPORTANT: Always respond in English with Marathi words in Devanagari script.
When a student says they want to learn or asks what to do — start Lesson 1 immediately.
When a student greets you — respond warmly and offer to start the lesson."""

NORA_PROMPT_HI = """You are Nora, India's first AI Marathi teacher at marathibola.com.
You help non-Marathi speakers in Maharashtra speak Marathi confidently.
You teach in a structured, warm, step-by-step way.
Always use Devanagari script for Marathi words, with Roman pronunciation in brackets.
IMPORTANT: Always explain in Hindi (हिंदी). Never use English explanations.
Be encouraging like a loving didi teaching her younger sibling.

""" + NORA_CURRICULUM + """

IMPORTANT: हमेशा हिंदी में जवाब दें। मराठी शब्द देवनागरी में लिखें।
जब कोई छात्र सीखना चाहे — तुरंत Lesson 1 शुरू करें।"""

class ChatRequest(BaseModel):
    message: str
    student_id: str = "default"
    student_name: str = "Student"
    lang: str = "en"  # ✅ NEW: frontend sends 'en' or 'hi'

class TTSRequest(BaseModel):
    text: str
    voice: str = "Nora"

class STTRequest(BaseModel):
    audio_url: str = ""

@app.get("/")
async def root():
    return {"status": "Nora is alive", "version": "4.3", "voice": "ElevenLabs Nora NS - Marathi"}

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
        voice_id = "WlkSq4ubXr1JwPngJWtM"  # ✅ Nora NS - Marathi Voice

        # ✅ FIXED: Phonetic pronunciation fix for ElevenLabs
        request.text = request.text.replace("Marathi", "Maa-raa-thi").replace("marathi", "Maa-raa-thi")

        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}/stream"

        headers = {
            "xi-api-key": ELEVENLABS_API_KEY_ENV,
            "Content-Type": "application/json",
            "Accept": "audio/mpeg"
        }
        payload = {
            "text": request.text,
            "model_id": "eleven_v3",  # ✅ UPGRADED: eleven_v3 - first-class Marathi support
            "voice_settings": {
                "stability": 0.35,
                "similarity_boost": 0.85
            },
            "optimize_streaming_latency": 3
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
