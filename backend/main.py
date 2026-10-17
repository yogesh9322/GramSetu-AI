from fastapi import FastAPI, HTTPException, Depends, status, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import json, os, uuid, hashlib, io, tempfile, sqlite3, base64, secrets, smtplib, re
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="GramSetu AI API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://gram-setu-ai.vercel.app",
        "https://gramsetu-ai.vercel.app"
    ],
    allow_origin_regex=r"https://.*\.vercel\.app",
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

    # Create password resets table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS password_resets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL,
            token_hash TEXT NOT NULL,
            expires_at TEXT NOT NULL,
            is_used INTEGER DEFAULT 0,
            created_at TEXT NOT NULL
        )
    ''')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_pw_reset_hash ON password_resets (token_hash)')
    
    # Seed default demo account so demo login works immediately out of the box
    cursor.execute("SELECT id FROM users WHERE email = 'demo@gramsetu.ai'")
    if not cursor.fetchone():
        demo_id = str(uuid.uuid4())
        demo_token = str(uuid.uuid4())
        demo_hash = hashlib.sha256("demo123".encode()).hexdigest()
        cursor.execute('''
            INSERT INTO users (id, name, email, password, language, state, token, created_at, login_count)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0)
        ''', (demo_id, "Demo Citizen", "demo@gramsetu.ai", demo_hash, "hindi", "Maharashtra", demo_token, datetime.now().isoformat()))
        print("[INFO] Created default demo user: demo@gramsetu.ai / demo123")

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
        print("[INFO] Migrated users from JSON to SQLite database")
        
    except Exception as e:
        print(f"[WARN] Migration failed: {e}")

# Initialize database on startup
init_database()
migrate_from_json()

import threading

@app.on_event("startup")
async def startup_warmup():
    """Warm up schemes cache and LLM into memory so user queries are instant"""
    def _warm():
        try:
            print("[WARMUP] Pre-loading schemes cache and Groq LLM...")
            from rag_pipeline import get_all_schemes, get_llm
            get_all_schemes()
            get_llm()
            print("[WARMUP] Background warm-up complete! Responses will now be instant.")
        except Exception as ex:
            print(f"[WARMUP] Background warm-up notice: {ex}")
    
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
    print(f"[INFO] Looking up token: {token[:20]}...")
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
        print(f"[INFO] Found user: {user.get('email')}")
        return user
    
    print("[INFO] Token not found")
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
    language: Optional[str] = None
    scheme_id: Optional[str] = None
    scheme_name: Optional[str] = None
    history: Optional[List[Dict[str, Any]]] = None

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

# ── Email & Password Reset Configuration ──────────────────────
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
EMAILS_FROM = os.getenv("EMAILS_FROM", os.getenv("SMTP_FROM", SMTP_USER or "GramSetu AI <noreply@gramsetu.ai>"))
RESEND_API_KEY = os.getenv("RESEND_API_KEY", "")
RESEND_FROM = os.getenv("RESEND_FROM", "GramSetu AI <onboarding@resend.dev>")
BREVO_API_KEY = os.getenv("BREVO_API_KEY", "")
FRONTEND_URL = os.getenv("FRONTEND_URL", "https://gram-setu-ai.vercel.app").rstrip("/")

def send_password_reset_email(to_email: str, reset_url: str) -> bool:
    """
    Send a professional HTML and plain-text password reset email.
    Supports Resend HTTP API (recommended for Render free tier), Brevo API, or standard SMTP.
    Returns True if sent successfully, False otherwise.
    """
    subject = "Reset Your Password - GramSetu AI"
    
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Reset Your Password</title>
</head>
<body style="font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; background-color: #070a08; margin: 0; padding: 24px 12px; color: #ffffff;">
  <div style="max-width: 560px; margin: 0 auto; background: #0f1712; border: 1px solid rgba(76, 175, 80, 0.3); border-radius: 20px; overflow: hidden; box-shadow: 0 16px 40px rgba(0,0,0,0.6);">
    <div style="background: linear-gradient(135deg, #1b5e20 0%, #2e7d32 100%); padding: 32px 24px; text-align: center;">
      <div style="width: 52px; height: 52px; margin: 0 auto 12px; background: rgba(255,255,255,0.2); border-radius: 14px; display: flex; align-items: center; justify-content: center; font-size: 28px; line-height: 52px;">🌾</div>
      <span style="display: inline-block; background: rgba(255,255,255,0.2); padding: 4px 12px; border-radius: 100px; font-size: 11px; font-weight: 700; color: #e8f5e9; text-transform: uppercase; letter-spacing: 1px;">GramSetu AI Security</span>
      <h1 style="margin: 12px 0 0; font-size: 26px; font-weight: 800; color: #ffffff; letter-spacing: -0.5px;">Reset Your Password</h1>
    </div>
    <div style="padding: 32px 28px; font-size: 15px; line-height: 1.7; color: #d1d5db;">
      <p style="margin: 0 0 16px;">Hello,</p>
      <p style="margin: 0 0 18px;">We received a request to reset the password for your GramSetu AI account registered with <strong style="color: #4caf50;">{to_email}</strong>.</p>
      <p style="margin: 0 0 24px;">Click the secure button below to set a new password:</p>
      
      <div style="text-align: center; margin: 28px 0;">
        <a href="{reset_url}" target="_blank" style="display: inline-block; background: linear-gradient(135deg, #2e7d32 0%, #4caf50 100%); color: #ffffff !important; text-decoration: none; padding: 14px 34px; font-size: 16px; font-weight: 700; border-radius: 12px; box-shadow: 0 4px 20px rgba(76, 175, 80, 0.4);">
          Reset My Password →
        </a>
      </div>

      <div style="background: rgba(76, 175, 80, 0.08); border-left: 4px solid #4caf50; padding: 14px 16px; border-radius: 8px; margin: 24px 0; font-size: 13px; color: #a5d6a7;">
        ⏱️ <strong>Expiration Notice:</strong> This link is valid for <strong>20 minutes</strong> and can only be used once.
      </div>

      <p style="font-size: 13px; color: #9ca3af; margin: 20px 0 8px;">If the button above does not work, copy and paste this link into your browser:</p>
      <div style="background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.1); border-radius: 10px; padding: 12px; word-break: break-all; font-size: 12px; color: #81c784; font-family: monospace;">
        {reset_url}
      </div>

      <p style="margin-top: 28px; font-size: 13px; color: #9ca3af; border-top: 1px solid rgba(255,255,255,0.08); padding-top: 18px;">
        🔒 <strong>Security Notice:</strong> If you did not request this password reset, please ignore this email. Your current password will remain unchanged and your account is completely safe.
      </p>
    </div>
    <div style="padding: 20px 24px; background: #070a08; border-top: 1px solid rgba(255,255,255,0.06); text-align: center; font-size: 12px; color: #6b7280;">
      <p style="margin: 0 0 6px;">© {datetime.now().year} GramSetu AI • Bridging Villages to 63+ Government Schemes</p>
      <p style="margin: 0;">Multilingual AI Village Advisory Assistant • 100% Free & Open Access</p>
    </div>
  </div>
</body>
</html>"""

    plain_text = f"""Reset Your Password - GramSetu AI

Hello,

We received a request to reset the password for your GramSetu AI account ({to_email}).

Please visit the link below to choose a new password:
{reset_url}

This link is valid for 20 minutes and can only be used once.

Security Notice: If you did not request a password reset, you can safely ignore this email. Your account remains secure.

--
GramSetu AI Team
Multilingual Government Scheme Assistant
https://gram-setu-ai.vercel.app
"""

    print(f"[AUTH] Generated password reset link for {to_email}: {reset_url}")

    # 1. Try Resend HTTP API (Port 443 - Recommended for Render free tier where SMTP ports are blocked)
    resend_key = os.getenv("RESEND_API_KEY") or RESEND_API_KEY
    if resend_key:
        try:
            headers = {
                "Authorization": f"Bearer {resend_key}",
                "Content-Type": "application/json"
            }
            sender = os.getenv("RESEND_FROM") or RESEND_FROM
            payload = {
                "from": sender,
                "to": [to_email],
                "subject": subject,
                "html": html_content,
                "text": plain_text
            }
            resp = requests.post("https://api.resend.com/emails", json=payload, headers=headers, timeout=12)
            if resp.status_code in (200, 201):
                print(f"[AUTH] Successfully sent password reset email via Resend to {to_email}")
                return True
            else:
                print(f"[AUTH] Resend API error ({resp.status_code}): {resp.text}")
        except Exception as e:
            print(f"[AUTH] Exception sending email via Resend: {e}")

    # 2. Try Brevo HTTP API (Port 443)
    brevo_key = os.getenv("BREVO_API_KEY") or BREVO_API_KEY
    if brevo_key:
        try:
            headers = {
                "api-key": brevo_key,
                "Content-Type": "application/json"
            }
            payload = {
                "sender": {"name": "GramSetu AI", "email": os.getenv("BREVO_FROM_EMAIL", SMTP_USER or "support@gramsetu.ai")},
                "to": [{"email": to_email}],
                "subject": subject,
                "htmlContent": html_content,
                "textContent": plain_text
            }
            resp = requests.post("https://api.brevo.com/v3/smtp/email", json=payload, headers=headers, timeout=12)
            if resp.status_code in (200, 201):
                print(f"[AUTH] Successfully sent password reset email via Brevo to {to_email}")
                return True
            else:
                print(f"[AUTH] Brevo API error ({resp.status_code}): {resp.text}")
        except Exception as e:
            print(f"[AUTH] Exception sending email via Brevo: {e}")

    # 3. Fallback to standard SMTP (Gmail / Custom SMTP)
    smtp_user = os.getenv("SMTP_USER") or SMTP_USER
    smtp_pass = os.getenv("SMTP_PASSWORD") or SMTP_PASSWORD
    if smtp_user and smtp_pass:
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = os.getenv("EMAILS_FROM") or EMAILS_FROM or smtp_user
            msg["To"] = to_email

            part1 = MIMEText(plain_text, "plain")
            part2 = MIMEText(html_content, "html")
            msg.attach(part1)
            msg.attach(part2)

            host = os.getenv("SMTP_HOST") or SMTP_HOST
            port = int(os.getenv("SMTP_PORT") or SMTP_PORT)

            if port == 465:
                with smtplib.SMTP_SSL(host, port, timeout=12) as server:
                    server.login(smtp_user, smtp_pass)
                    server.sendmail(msg["From"], to_email, msg.as_string())
            else:
                with smtplib.SMTP(host, port, timeout=12) as server:
                    server.starttls()
                    server.login(smtp_user, smtp_pass)
                    server.sendmail(msg["From"], to_email, msg.as_string())

            print(f"[AUTH] Successfully sent password reset email via SMTP to {to_email}")
            return True
        except Exception as e:
            print(f"[AUTH] Failed to send email via SMTP ({host}:{port}): {e}")

    print("[AUTH] (Notice) No email service credentials configured. Set RESEND_API_KEY or SMTP_USER/SMTP_PASSWORD in Render Environment Variables.")
    return False

class ForgotPasswordRequest(BaseModel):
    email: str

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str

@app.post("/auth/forgot-password")
async def forgot_password(req: ForgotPasswordRequest):
    email = req.email.strip().lower()
    if not email or "@" not in email or "." not in email:
        raise HTTPException(status_code=400, detail="Please enter a valid email address.")

    user = get_user_by_email(email)

    has_email_service = bool(
        os.getenv("RESEND_API_KEY") or 
        os.getenv("BREVO_API_KEY") or 
        (os.getenv("SMTP_USER") and os.getenv("SMTP_PASSWORD"))
    )

    if user:
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        # Invalidate any existing unused reset tokens for this user
        cursor.execute("UPDATE password_resets SET is_used = 1 WHERE email = ? AND is_used = 0", (email,))
        
        # Generate cryptographically secure single-use token
        token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        expires_at = (datetime.utcnow() + timedelta(minutes=25)).isoformat()
        created_at = datetime.utcnow().isoformat()
        
        cursor.execute('''
            INSERT INTO password_resets (email, token_hash, expires_at, is_used, created_at)
            VALUES (?, ?, ?, 0, ?)
        ''', (email, token_hash, expires_at, created_at))
        conn.commit()
        conn.close()

        reset_link = f"{FRONTEND_URL}/reset-password?token={token}"

        if has_email_service:
            # Dispatch email asynchronously in background thread
            threading.Thread(target=send_password_reset_email, args=(email, reset_link), daemon=True).start()
            return {
                "status": "success",
                "email_sent": True,
                "message": f"A password reset link has been dispatched to {email}. Please check your inbox and spam folder."
            }
        else:
            print(f"[AUTH] (No email provider configured on Render) Reset link: {reset_link}")
            return {
                "status": "success",
                "email_sent": False,
                "dev_reset_url": reset_link,
                "message": "Password reset link generated! Since an automated email service is not yet configured on the server, you can use the direct link below to reset your password immediately."
            }
    else:
        print(f"[AUTH] Password reset requested for non-existent email: {email}")
        return {
            "status": "success",
            "email_sent": False,
            "message": "If an account is associated with this email, a password reset link has been sent. Please check your inbox and spam folder."
        }

@app.post("/auth/reset-password")
async def reset_password(req: ResetPasswordRequest):
    token = req.token.strip()
    new_password = req.new_password

    if not token:
        raise HTTPException(status_code=400, detail="Password reset token is missing or invalid.")

    if len(new_password) < 6:
        raise HTTPException(status_code=400, detail="New password must be at least 6 characters.")

    token_hash = hashlib.sha256(token.encode()).hexdigest()

    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, email, expires_at, is_used 
        FROM password_resets 
        WHERE token_hash = ?
    ''', (token_hash,))
    row = cursor.fetchone()

    if not row:
        conn.close()
        raise HTTPException(status_code=400, detail="Invalid or non-existent password reset link. Please request a new one.")

    reset_id, email, expires_at, is_used = row

    if is_used:
        conn.close()
        raise HTTPException(status_code=400, detail="This password reset link has already been used. Please request a new one.")

    try:
        exp_time = datetime.fromisoformat(expires_at)
        if datetime.utcnow() > exp_time:
            conn.close()
            raise HTTPException(status_code=400, detail="This password reset link has expired (valid for 20 minutes). Please request a new one.")
    except Exception:
        pass

    user = get_user_by_email(email)
    if not user:
        conn.close()
        raise HTTPException(status_code=400, detail="User account associated with this reset link was not found.")

    # Hash new password and update user record
    hashed_pwd = hash_password(new_password)
    new_auth_token = str(uuid.uuid4())

    cursor.execute('''
        UPDATE users 
        SET password = ?, token = ? 
        WHERE email = ?
    ''', (hashed_pwd, new_auth_token, email))

    # Mark token as used
    cursor.execute("UPDATE password_resets SET is_used = 1 WHERE id = ?", (reset_id,))
    conn.commit()
    conn.close()

    print(f"[AUTH] Successfully reset password for: {email}")

    return {
        "status": "success",
        "message": "Your password has been successfully reset! You can now log in with your new password."
    }

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
        print(f"Error in /ask: {e}")
        raise HTTPException(status_code=500, detail=f"❌ Error: {str(e)}")

# ── Voice Ask Endpoint ─────────────────────────────────────────
import re

_whisper_model = None

def get_whisper_model():
    global _whisper_model
    if _whisper_model is None:
        print("[INFO] Loading Whisper base model into memory...")
        import whisper
        _whisper_model = whisper.load_model("base")
        print("[INFO] Whisper base model loaded!")
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
        print(f"[INFO] Audio generated: {audio_size} bytes")
        
        if audio_size == 0:
            raise Exception("Generated audio is empty")

        # Record the voice visit
        record_visit(user_id=user_id, endpoint='/voice-ask-upload')
        print("[INFO] Creating streaming response...")
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
                print(f"[INFO] Cleaned up: {tmp_path}")
            except OSError:
                pass


@app.post("/voice-ask")
async def voice_ask(audio: UploadFile = File(...), credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        return await process_voice_audio(audio, credentials)
    except Exception as e:
        print(f"[ERROR] Voice-ask error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/voice-ask-upload")
async def voice_ask_upload(audio: UploadFile = File(...), credentials: HTTPAuthorizationCredentials = Depends(security)):
    print(f"[INFO] Voice-ask-upload called with file: {audio.filename if audio else 'None'}")
    print(f"[INFO] Credentials: {credentials.credentials[:20] if credentials else 'None'}...")
    try:
        return await process_voice_audio(audio, credentials)
    except Exception as e:
        print(f"[ERROR] Voice-ask-upload error: {e}")
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

# ── Health check (Supports GET and HEAD for Render healthcheck probes) ──
@app.api_route("/", methods=["GET", "HEAD"])
async def root():
    return {"message": "GramSetu AI API", "status": "running", "version": "2.0"}

@app.api_route("/health", methods=["GET", "HEAD"])
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
