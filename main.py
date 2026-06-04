# marathibola.com — Nora AI Marathi Teacher
# Backend Server — Version 2
# Built with Claude | Jai Shri Krishna

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import anthropic
import httpx
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
DEEPGRAM_API_KEY = os.environ.get("DEEPGRAM_API_KEY")

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
6. End of session summary — all sentences
