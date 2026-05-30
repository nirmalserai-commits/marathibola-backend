# marathibola.com — Nora AI Marathi Teacher
# Backend Server — Version 1
# Built with Claude | Jai Shri Krishna

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import anthropic
import json
import os
import datetime
from session_manager import SessionManager
from dump_generator import generate_class_dump, generate_weekly_dump

app = FastAPI(title="Marathibola — Nora AI Marathi Teacher")

# Allow frontend to talk to backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Keys — set these as environment variables on Railway.app
CLAUDE_API_KEY = os.environ.get("CLAUDE_API_KEY")
HF_TOKEN = os.environ.get("HF_TOKEN")  # Hugging Face token

client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)
session_manager = SessionManager()

# ================================================
# NORA'S SYSTEM PROMPT
# ================================================
NORA_SYSTEM_PROMPT = """
You are Nora, a warm, patient, and encouraging Marathi language teacher for marathibola.com.
You help non-Marathi speakers living in Maharashtra learn to speak Marathi confidently.

YOUR PERSONALITY:
- Warm, encouraging, never judgmental
- Like a kind elder sister or friendly teacher
- Celebrate every small success — "Shabash!" "Ekdum sahi!"
- Patient — never rush the student
- Available 24/7, always happy to teach

YOUR TEACHING RULES:
- Always teach IN MARATHI
- Correct and explain in Hindi or English (based on student preference)
- NEVER teach Marathi using English letters (no romanisation)
- YOU speak first — student repeats — NEVER reversed
- Word by word breakdown after every sentence — always
- No strict pronunciation scoring — keyword recognition and encouragement
- Maximum 3 attempts per sentence — if still wrong, simplify and move on

SESSION STRUCTURE (15 minutes max):
1. Warm greeting — ask how student feels
2. Recap last 2-3 sentences from previous session
3. Introduce today's situation clearly
4. Teach 3-5 new sentences — one by one
5. Short role play of the full situation
6. End of session summary — all sentences learned today
7. Tell student what comes next time
8. Strong encouraging close

CORRECTION STYLE:
- Never say "wrong" or "galat" harshly
- Say "Arey, thoda changla karu — parat ek veyla bola" (Let's try again nicely)
- Always model correct sentence before asking student to repeat

SITUATIONS AVAILABLE:
1. Vegetable Market (Bhaaji Baazaar)
2. Auto Rickshaw (Auto Stand)  
3. Neighbour / Building
4. Kirana Shop
5. Office / Workplace
6. Bank / Post Office

At the END of every session, output a JSON block like this (after your normal response):
###CLASS_DUMP###
{
  "situation": "situation name",
  "sentences_taught": ["sentence 1", "sentence 2"],
  "sentences_with_meaning": [{"marathi": "...", "hindi": "..."}],
  "nora_note": "personal encouraging note to student",
  "next_situation": "next situation name"
}
###END_DUMP###
"""

# ================================================
# MODELS
# ================================================
class StartSession(BaseModel):
    student_name: str
    correction_language: str  # "Hindi" or "English"
    student_id: str

class StudentMessage(BaseModel):
    student_id: str
    message: str  # text from speech-to-text

class SessionEnd(BaseModel):
    student_id: str

# ================================================
# ROUTES
# ================================================

@app.get("/")
def root():
    return {"message": "Marathibola — Nora is ready. Maharashtra is waiting!"}

@app.post("/start_session")
def start_session(data: StartSession):
    """Start a new learning session for a student"""
    
    # Get student's current lesson from session manager
    student_data = session_manager.get_student(data.student_id)
    current_situation = student_data.get("current_situation", "Vegetable Market")
    sessions_completed = student_data.get("sessions_completed", 0)
    last_sentences = student_data.get("last_sentences", [])
    
    # Build opening message context
    context = f"""
Student name: {data.student_name}
Correction language: {data.correction_language}
Current situation to teach: {current_situation}
Sessions completed so far: {sessions_completed}
Last sentences learned: {', '.join(last_sentences) if last_sentences else 'None — this is first session'}
"""
    
    # Get Nora's opening message
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1000,
        system=NORA_SYSTEM_PROMPT,
        messages=[
            {"role": "user", "content": f"Start a new session. {context}"}
        ]
    )
    
    nora_message = response.content[0].text
    
    # Save session to manager
    session_manager.start_session(data.student_id, {
        "student_name": data.student_name,
        "correction_language": data.correction_language,
        "current_situation": current_situation,
        "history": [{"role": "assistant", "content": nora_message}],
        "session_start": datetime.datetime.now().isoformat()
    })
    
    return {
        "nora_message": nora_message,
        "session_id": data.student_id,
        "situation": current_situation
    }

@app.post("/chat")
def chat(data: StudentMessage):
    """Student speaks — Nora responds"""
    
    session = session_manager.get_session(data.student_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found. Start a session first.")
    
    # Add student message to history
    session["history"].append({"role": "user", "content": data.message})
    
    # Get Nora's response
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1000,
        system=NORA_SYSTEM_PROMPT,
        messages=session["history"]
    )
    
    nora_message = response.content[0].text
    
    # Add Nora's response to history
    session["history"].append({"role": "assistant", "content": nora_message})
    session_manager.update_session(data.student_id, session)
    
    # Check if this is end of session (class dump present)
    class_dump = None
    if "###CLASS_DUMP###" in nora_message:
        class_dump = extract_class_dump(nora_message)
        nora_message = nora_message.split("###CLASS_DUMP###")[0].strip()
        
        # Save class dump automatically
        if class_dump:
            generate_class_dump(data.student_id, class_dump, session)
    
    return {
        "nora_message": nora_message,
        "class_dump": class_dump
    }

@app.post("/end_session")
def end_session(data: SessionEnd):
    """End session — trigger class dump — check if weekly dump needed"""
    
    session = session_manager.get_session(data.student_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")
    
    # Update student record
    student_data = session_manager.get_student(data.student_id)
    student_data["sessions_completed"] = student_data.get("sessions_completed", 0) + 1
    student_data["last_session_date"] = datetime.datetime.now().isoformat()
    session_manager.update_student(data.student_id, student_data)
    
    # Check if weekly dump needed (every Sunday)
    weekly_dump = None
    if datetime.datetime.now().weekday() == 6:  # Sunday
        weekly_dump = generate_weekly_dump(data.student_id, student_data)
    
    # Clear session
    session_manager.end_session(data.student_id)
    
    return {
        "message": "Session ended. Shabash! Great work today!",
        "weekly_dump": weekly_dump
    }

@app.get("/student/{student_id}/progress")
def get_progress(student_id: str):
    """Get student's full progress"""
    student_data = session_manager.get_student(student_id)
    return student_data

# ================================================
# HELPER
# ================================================
def extract_class_dump(nora_message: str) -> dict:
    """Extract class dump JSON from Nora's message"""
    try:
        start = nora_message.find("###CLASS_DUMP###") + len("###CLASS_DUMP###")
        end = nora_message.find("###END_DUMP###")
        json_str = nora_message[start:end].strip()
        return json.loads(json_str)
    except:
        return None
