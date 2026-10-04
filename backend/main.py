from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import json, os, uuid, hashlib, io, tempfile, sqlite3, base64
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

# ── SQLite Database Setup ──────────────────────────────
DATABASE_FILE = "gramsetu.db"

def init_database():
    """Initialize SQLite database and create tables if they don't exist"""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    
    # Create users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            language TEXT DEFAULT 'hindi',
            state TEXT,
            token TEXT UNIQUE,
            created_at TEXT NOT NULL,
            last_login TEXT,
            login_count INTEGER DEFAULT 0
        )
    ''')
    
    # Create visits table for tracking user visits
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS visits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            ip_address TEXT,
            user_agent TEXT,
            endpoint TEXT,
            timestamp TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Create a table for general statistics
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS stats (
            key TEXT PRIMARY KEY,
            value TEXT,
            updated_at TEXT
        )
    ''')
    
    conn.commit()
    conn.close()

def migrate_from_json():
    """Migrate existing users from JSON file to SQLite database"""
    if not os.path.exists("users.json"):
        return
    
    try:
        with open("users.json", "r") as f:
            users_data = json.load(f)
        
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        
        for email, user in users_data.items():
            cursor.execute('''
                INSERT OR REPLACE INTO users 
                (id, name, email, password, language, state, token, created_at, login_count)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                user.get('id'),
                user.get('name'),
                user.get('email'),
                user.get('password'),
                user.get('language', 'hindi'),
                user.get('state'),
                user.get('token'),
                user.get('created_at', datetime.now().isoformat()),
                user.get('login_count', 0)
            ))
        
        conn.commit()
        conn.close()
        
        # Backup the old file
        os.rename("users.json", "users.json.backup")
        print("✓ Migrated users from JSON to SQLite database")
        
    except Exception as e:
        print(f"⚠️ Migration failed: {e}")

# Initialize database on startup
init_database()
migrate_from_json()

import threading

@app.on_event("startup")
async def startup_warmup():
    """Warm up RAG Vector DB and LLM into memory so user queries are instant"""
    def _warm():
        try:
            print("[WARMUP] Pre-loading FAISS Vector DB and LLM into memory...")
            from rag_pipeline import load_vector_db, get_llm
            load_vector_db()
            get_llm()
            print("[WARMUP] Background RAG warm-up complete! Responses will now be instant.")
        except Exception as ex:
            print(f"[WARMUP] Background warm-up error: {ex}")
    
    t = threading.Thread(target=_warm, daemon=True)
    t.start()

# ── User Management Functions ──────────────────────────────
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def get_user_by_email(email: str):
    """Get user by email from database"""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return {
            'id': row[0],
            'name': row[1],
            'email': row[2],
            'password': row[3],
            'language': row[4],
            'state': row[5],
            'token': row[6],
            'created_at': row[7],
            'last_login': row[8],
            'login_count': row[9]
        }
    return None

def get_user_by_token(token: str):
    """Get user by token from database"""
    print(f"🔍 Looking up token: {token[:20]}...")
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE token = ?", (token,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        user = {
            'id': row[0],
            'name': row[1],
            'email': row[2],
            'password': row[3],
            'language': row[4],
            'state': row[5],
            'token': row[6],
            'created_at': row[7],
            'last_login': row[8],
            'login_count': row[9]
        }
        print(f"✓ Found user: {user.get('email')}")
        return user
    
    print("❌ Token not found")
    return None

def create_user(name: str, email: str, password: str, language: str = "hindi", state: str = ""):
    """Create a new user in database"""
    user_id = str(uuid.uuid4())
    token = str(uuid.uuid4())
    hashed_password = hash_password(password)
    created_at = datetime.now().isoformat()
    
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO users (id, name, email, password, language, state, token, created_at, login_count)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0)
    ''', (user_id, name, email, hashed_password, language, state, token, created_at))
    conn.commit()
    conn.close()
    
    return {
        'id': user_id,
        'name': name,
        'email': email,
        'password': hashed_password,
        'language': language,
        'state': state,
        'token': token,
        'created_at': created_at,
        'login_count': 0
    }

def update_user_login(email: str):
    """Update user's last login time and increment login count"""
    now = datetime.now().isoformat()
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE users 
        SET last_login = ?, login_count = login_count + 1 
        WHERE email = ?
    ''', (now, email))
    conn.commit()
    conn.close()

def record_visit(user_id: str = None, ip_address: str = None, user_agent: str = None, endpoint: str = None):
    """Record a visit to the application"""
    timestamp = datetime.now().isoformat()
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO visits (user_id, ip_address, user_agent, endpoint, timestamp)
        VALUES (?, ?, ?, ?, ?)
    ''', (user_id, ip_address, user_agent, endpoint, timestamp))
    conn.commit()
    conn.close()

def get_visit_stats():
    """Get visit statistics"""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    
    # Total visits
    cursor.execute("SELECT COUNT(*) FROM visits")
    total_visits = cursor.fetchone()[0]
    
    # Unique users
    cursor.execute("SELECT COUNT(DISTINCT user_id) FROM visits WHERE user_id IS NOT NULL")
    unique_users = cursor.fetchone()[0]
    
    # Today's visits
    today = datetime.now().date().isoformat()
    cursor.execute("SELECT COUNT(*) FROM visits WHERE DATE(timestamp) = ?", (today,))
    today_visits = cursor.fetchone()[0]
    
    # User count
    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0]
    
    conn.close()
    
    return {
        'total_visits': total_visits,
        'unique_users': unique_users,
        'today_visits': today_visits,
        'total_users': total_users
    }

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
    # Check if user already exists
    existing_user = get_user_by_email(req.email)
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered. Please login.")
    
    if len(req.password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters.")
    
    # Create new user
    user = create_user(req.name, req.email, req.password, req.language, req.state)
    
    # Record the registration visit
    record_visit(user_id=user['id'], endpoint='/auth/register')
    
    return {
        "token": user['token'],
        "user": {
            "id": user["id"], 
            "name": user["name"], 
            "email": user["email"], 
            "language": user["language"], 
            "state": user["state"]
        }
    }

@app.post("/auth/login")
async def login(req: LoginRequest):
    user = get_user_by_email(req.email)
    if not user:
        raise HTTPException(status_code=401, detail="Email not found. Please register first.")
    
    if user["password"] != hash_password(req.password):
        raise HTTPException(status_code=401, detail="Incorrect password. Please try again.")
    
    # Generate new token on each login
    new_token = str(uuid.uuid4())
    
    # Update user token and login info
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE users 
        SET token = ?, last_login = ?, login_count = login_count + 1 
        WHERE email = ?
    ''', (new_token, datetime.now().isoformat(), req.email))
    conn.commit()
    conn.close()
    
    # Record the login visit
    record_visit(user_id=user['id'], endpoint='/auth/login')
    
    return {
        "token": new_token,
        "user": {
            "id": user["id"], 
            "name": user["name"], 
            "email": user["email"], 
            "language": user["language"], 
            "state": user["state"]
        }
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
        user_id = None
        if credentials:
            user = get_user_by_token(credentials.credentials)
            if user:
                user_id = user.get("id")
                language = user.get("language", "hindi") if not language else language
        
        answer, detected_lang = get_answer(req.question, preferred_language=language)
        
        # Record the ask visit
        record_visit(user_id=user_id, endpoint='/ask')
        
        return {"answer": answer, "language": detected_lang, "question": req.question}
    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail=f"❌ Error: {str(e)}")

# ── Voice Ask Endpoint ─────────────────────────────────────────
import re

_whisper_model = None

def get_whisper_model():
    global _whisper_model
    if _whisper_model is None:
        print("🎙️ Loading Whisper base model into memory...")
        import whisper
        _whisper_model = whisper.load_model("base")
        print("✅ Whisper base model loaded!")
    return _whisper_model

def clean_text_for_tts(text: str, language: str = "hindi") -> str:
    if not text:
        return ""
    t = text

    # 1. Ranges 2-3 -> 2 से 3 (Hindi) / 2 ते 3 (Marathi) / 2 to 3 (English)
    lang_lower = language.lower() if language else "hindi"
    if lang_lower == "marathi":
        t = re.sub(r'(\d+)\s*[-–—]\s*(\d+)', r'\1 ते \2', t)
    elif lang_lower == "hindi":
        t = re.sub(r'(\d+)\s*[-–—]\s*(\d+)', r'\1 से \2', t)
    else:
        t = re.sub(r'(\d+)\s*[-–—]\s*(\d+)', r'\1 to \2', t)

    # 2. Numbered points 1. 2. 3.
    hi_ordinals = {1: "पहला", 2: "दूसरा", 3: "तीसरा", 4: "चौथा", 5: "पांचवां", 6: "छठा", 7: "सातवां", 8: "आठवां", 9: "नौवां", 10: "दसवां"}
    mr_ordinals = {1: "पहिला मुद्दा", 2: "दूसरा मुद्दा", 3: "तिसरा मुद्दा", 4: "चौथा मुद्दा", 5: "पांचवा मुद्दा", 6: "सहावा मुद्दा", 7: "सातवा मुद्दा", 8: "आठवा मुद्दा", 9: "नववा मुद्दा", 10: "दहावा मुद्दा"}
    en_ordinals = {1: "First", 2: "Second", 3: "Third", 4: "Fourth", 5: "Fifth", 6: "Sixth", 7: "Seventh", 8: "Eighth", 9: "Ninth", 10: "Tenth"}

    def repl_num(m):
        n = int(m.group(1))
        if lang_lower == "marathi":
            return f"{mr_ordinals.get(n, f'मुद्दा {n}')}, "
        elif lang_lower == "hindi":
            return f"{hi_ordinals.get(n, f'पॉइंट {n}')}, "
        return f"{en_ordinals.get(n, f'Point {n}')}, "

    t = re.sub(r'^\s*(\d+)\.\s+', repl_num, t, flags=re.MULTILINE)

    # 3. Clean Markdown tables, links, headers, formatting
    t = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', t)
    t = re.sub(r'http[s]?://\S+', '', t)
    t = re.sub(r'#+\s*', '', t)
    t = re.sub(r'[*_~`|]', '', t)
    t = re.sub(r'^\s*[\-\*•]+\s*', ', ', t, flags=re.MULTILINE)
    t = re.sub(r'\n+', ', ', t)
    t = re.sub(r'\s*,\s*,+', ', ', t)
    t = re.sub(r'\s+', ' ', t)
    return t.strip()

async def process_voice_audio(audio, credentials):
    print(f"🎤 Starting voice processing...")
    from gtts import gTTS
    from rag_pipeline import get_answer
    
    # Get user info for visit tracking
    user_id = None
    if credentials:
        user = get_user_by_token(credentials.credentials)
        if user:
            user_id = user.get("id")

    audio_bytes = await audio.read()
    print(f"✓ Received audio: {len(audio_bytes)} bytes")
    
    if len(audio_bytes) == 0:
        raise Exception("Received empty audio file")
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
        tmp.write(audio_bytes)
        tmp_path = tmp.name
    print(f"✓ Temp file created: {tmp_path}")
    
    # Verify file was written
    if not os.path.exists(tmp_path):
        raise Exception(f"Temp file was not created: {tmp_path}")
    
    file_size = os.path.getsize(tmp_path)
    print(f"✓ Temp file size: {file_size} bytes")
    
    # Define sanitize_header function - base64 encode to handle non-ASCII characters
    def sanitize_header(value: str) -> str:
        # Remove newlines and limit length
        clean_value = value.replace("\n", " ").replace("\r", " ")[:200]
        # Base64 encode to handle any Unicode characters
        return base64.b64encode(clean_value.encode('utf-8')).decode('ascii')
    
    try:
        model = get_whisper_model()
        print("✓ Using cached Whisper model")
        
        result = model.transcribe(tmp_path)
        question = result["text"].strip()
        print(f"✓ Transcribed: {question}")

        user = get_user_by_token(credentials.credentials) if credentials else None
        language = user.get("language", "hindi") if user else "hindi"
        print(f"✓ User language: {language}")

        answer, detected_lang = get_answer(question, preferred_language=language)
        print(f"✓ Got answer in {detected_lang}")

        lang_map = {"hindi": "hi", "marathi": "mr", "english": "en"}
        tts_lang = lang_map.get(detected_lang, "hi")
        print(f"✓ Converting to speech ({tts_lang})")
        
        clean_ans = clean_text_for_tts(answer[:600], detected_lang)
        tts = gTTS(text=clean_ans, lang=tts_lang)
        audio_buffer = io.BytesIO()
        tts.write_to_fp(audio_buffer)
        audio_buffer.seek(0)
        audio_size = len(audio_buffer.getvalue())
        print(f"✓ Audio generated: {audio_size} bytes")
        
        if audio_size == 0:
            raise Exception("Generated audio is empty")

        # Record the voice visit
        record_visit(user_id=user_id, endpoint='/voice-ask-upload')
        print("✓ Creating streaming response...")
        return StreamingResponse(
            audio_buffer,
            media_type="audio/mpeg",
            headers={
                "x-question": sanitize_header(question),
                "x-answer": sanitize_header(answer[:300]),
                "x-language": detected_lang
            }
        )
    finally:
        if os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
                print(f"✓ Cleaned up: {tmp_path}")
            except OSError:
                pass

from fastapi import UploadFile, File

@app.post("/voice-ask")
async def voice_ask(audio: UploadFile = File(...), credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        return await process_voice_audio(audio, credentials)
    except Exception as e:
        print(f"❌ Voice-ask error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/voice-ask-upload")
async def voice_ask_upload(audio: UploadFile = File(...), credentials: HTTPAuthorizationCredentials = Depends(security)):
    print(f"🔍 Voice-ask-upload called with file: {audio.filename if audio else 'None'}")
    print(f"🔍 Credentials: {credentials.credentials[:20] if credentials else 'None'}...")
    try:
        return await process_voice_audio(audio, credentials)
    except Exception as e:
        print(f"❌ Voice-ask-upload error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/tts")
async def text_to_speech_endpoint(text: str, language: str = "hindi"):
    """Convert text to clean audio stream using gTTS"""
    try:
        from gtts import gTTS
        lang_map = {"hindi": "hi", "marathi": "mr", "english": "en"}
        tts_lang = lang_map.get(language.lower(), "hi")
        clean_ans = clean_text_for_tts(text[:600], language)
        if not clean_ans:
            clean_ans = "No text provided"
        tts = gTTS(text=clean_ans, lang=tts_lang)
        audio_buffer = io.BytesIO()
        tts.write_to_fp(audio_buffer)
        audio_buffer.seek(0)
        return StreamingResponse(audio_buffer, media_type="audio/mpeg")
    except Exception as e:
        print(f"❌ TTS Endpoint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ── Health check ──────────────────────────────────────────────
@app.get("/")
async def root():
    return {"message": "GramSetu AI API", "status": "running", "version": "2.0"}

@app.get("/health")
async def health():
    return {"status": "healthy", "api": "GramSetu AI"}

# ── Statistics Endpoint ────────────────────────────────────────
@app.get("/stats")
async def get_stats():
    """Get application statistics"""
    try:
        stats = get_visit_stats()
        return {
            "total_users": stats['total_users'],
            "total_visits": stats['total_visits'],
            "unique_users": stats['unique_users'],
            "today_visits": stats['today_visits']
        }
    except Exception as e:
        print(f"Stats error: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve statistics")
