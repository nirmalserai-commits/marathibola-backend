# Marathibola Backend — Deployment Guide
# Jai Shri Krishna | marathibola.com

## Files in this folder:
- main.py — Nora's brain — main server
- session_manager.py — manages student sessions
- dump_generator.py — auto class dump + weekly dump
- requirements.txt — Python packages needed
- railway.toml — Railway.app deployment config

## How to Deploy on Railway.app:

### Step 1 — GitHub
1. Create free GitHub account at github.com
2. Create new repository — name it "marathibola-backend"
3. Upload all 5 files from this folder

### Step 2 — Railway
1. Go to railway.app — login
2. New Project → GitHub Repository
3. Select marathibola-backend
4. Railway auto-detects Python and deploys

### Step 3 — Environment Variables (IMPORTANT)
In Railway dashboard → your project → Variables → Add:
- CLAUDE_API_KEY = your Claude API key (sk-ant-...)
- HF_TOKEN = your Hugging Face token

### Step 4 — Done!
Railway gives you a live URL like:
https://marathibola-backend-production.up.railway.app

This is your backend URL — use it in the frontend app.

## API Endpoints:

GET  /                          — Health check
POST /start_session             — Start student session
POST /chat                      — Student message → Nora response
POST /end_session               — End session, trigger dumps
GET  /student/{student_id}/progress — Get student progress

## Environment Variables needed:
- CLAUDE_API_KEY — from console.anthropic.com
- HF_TOKEN — from huggingface.co/settings/tokens

## Notes:
- Class dump generated automatically after every session
- Weekly dump generated automatically every Sunday
- No button needed — everything is automatic
- Rs.8-15 per 15 minute session on Claude API

Jai Shri Krishna — Nora is ready. Maharashtra is waiting!
