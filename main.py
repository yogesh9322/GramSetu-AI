from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import json, os, uuid, hashlib, io
from datetime import datetime

app = FastAPI(title="GramSetu AI API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["x-question", "x-answer", "x-language"],
)

security = HTTPBearer(auto_error=False)

# ── Simple file-based user store ──────────────────────────────
USERS_FILE = "users.json"

def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r") as f:
            return json.load(f)
    # Default demo user
    demo = {
        "id": "demo",
        "name": "Demo User",
        "email": "demo@gramsetu.ai",
        "password": hashlib.sha256("demo123".encode()).hexdigest(),
        "language": "hindi",
        "state": "Maharashtra",
        "token": "demo-token-123",
        "created_at": datetime.now().isoformat()
    }
    users = {"demo@gramsetu.ai": demo}
    save_users(users)
    return users

def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=2)

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def get_user_by_token(token: str):
    users = load_users()
    for u in users.values():
        if u.get("token") == token:
            return u
    return None

# ── Auth Models ────────────────────────────────────────────────
class RegisterRequest(BaseModel):
    name: str
    email: str
    password: str
    language: str = "hindi"
    state: str = ""

class LoginRequest(BaseModel):
    email: str
    password: str

class AskRequest(BaseModel):
    question: str
    language: str = None

# ── Auth Endpoints ─────────────────────────────────────────────
@app.post("/auth/register")
async def register(req: RegisterRequest):
    users = load_users()
    if req.email in users:
        raise HTTPException(status_code=400, detail="Email already registered. Please login.")
    if len(req.password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters.")
    token = str(uuid.uuid4())
    user = {
        "id": str(uuid.uuid4()),
        "name": req.name,
        "email": req.email,
        "password": hash_password(req.password),
        "language": req.language,
        "state": req.state,
        "token": token,
        "created_at": datetime.now().isoformat()
    }
    users[req.email] = user
    save_users(users)
    return {
        "token": token,
        "user": {"id": user["id"], "name": user["name"], "email": user["email"], "language": user["language"], "state": user["state"]}
    }

@app.post("/auth/login")
async def login(req: LoginRequest):
    users = load_users()
    user = users.get(req.email)
    if not user:
        raise HTTPException(status_code=401, detail="Email not found. Please register first.")
    if user["password"] != hash_password(req.password):
        raise HTTPException(status_code=401, detail="Incorrect password. Please try again.")
    # Generate new token on each login
    token = str(uuid.uuid4())
    user["token"] = token
    users[req.email] = user
    save_users(users)
    return {
        "token": token,
        "user": {"id": user["id"], "name": user["name"], "email": user["email"], "language": user["language"], "state": user["state"]}
    }

@app.get("/auth/me")
async def get_me(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if not credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")
    user = get_user_by_token(credentials.credentials)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")
    return {"id": user["id"], "name": user["name"], "email": user["email"], "language": user["language"]}

# ── Ask Endpoint ───────────────────────────────────────────────
@app.post("/ask")
async def ask(req: AskRequest, credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        from rag_pipeline import get_answer
        language = req.language
        if not language:
            user = get_user_by_token(credentials.credentials) if credentials else None
            language = user.get("language", "hindi") if user else "hindi"
        answer, detected_lang = get_answer(req.question, preferred_language=language)
        return {"answer": answer, "language": detected_lang, "question": req.question}
    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail=f"❌ Error: {str(e)}")

# ── Voice Ask Endpoint ─────────────────────────────────────────
@app.post("/voice-ask")
async def voice_ask(credentials: HTTPAuthorizationCredentials = Depends(security)):
    from fastapi import UploadFile, File
    raise HTTPException(status_code=501, detail="Voice endpoint - use multipart form")

from fastapi import UploadFile, File
@app.post("/voice-ask-upload")
async def voice_ask_upload(audio: UploadFile = File(...), credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        import whisper
        from gtts import gTTS
        from rag_pipeline import get_answer

        audio_bytes = await audio.read()
        with open("/tmp/audio.wav", "wb") as f:
            f.write(audio_bytes)

        model = whisper.load_model("base")
        result = model.transcribe("/tmp/audio.wav")
        question = result["text"].strip()

        user = get_user_by_token(credentials.credentials) if credentials else None
        language = user.get("language", "hindi") if user else "hindi"

        answer, detected_lang = get_answer(question, preferred_language=language)

        lang_map = {"hindi": "hi", "marathi": "mr", "english": "en"}
        tts = gTTS(text=answer[:500], lang=lang_map.get(detected_lang, "hi"))
        audio_buffer = io.BytesIO()
        tts.write_to_fp(audio_buffer)
        audio_buffer.seek(0)

        return StreamingResponse(
            audio_buffer,
            media_type="audio/mpeg",
            headers={"x-question": question, "x-answer": answer[:300], "x-language": detected_lang}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ── Health check ───────────────────────────────────────────────
@app.get("/")
async def root():
    return {"message": "GramSetu AI API", "status": "running", "version": "2.0"}

@app.get("/health")
async def health():
    return {"status": "healthy", "api": "GramSetu AI"}
