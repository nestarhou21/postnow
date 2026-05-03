"""
routes/auth.py — Register, Login, /me
"""
import os
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
import bcrypt
from jose import jwt, JWTError
from db import get_db

router = APIRouter(prefix="/auth", tags=["auth"])

SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
ALGORITHM = "HS256"
EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 1440))

bearer = HTTPBearer()


# ── Schemas ───────────────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


# ── Helpers ───────────────────────────────────────────────────────────────────

def create_token(user_id: int) -> str:
    expire = datetime.utcnow() + timedelta(minutes=EXPIRE_MINUTES)
    return jwt.encode({"sub": str(user_id), "exp": expire}, SECRET_KEY, ALGORITHM)


def get_current_user(creds: HTTPAuthorizationCredentials = Depends(bearer)) -> int:
    try:
        payload = jwt.decode(creds.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        return int(payload["sub"])
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


# ── Routes ────────────────────────────────────────────────────────────────────

@router.post("/register")
def register(body: RegisterRequest):
    hashed = bcrypt.hashpw(body.password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    try:
        with get_db() as conn:
            cur = conn.execute(
                "INSERT INTO users (email, password) VALUES (?, ?)",
                (body.email, hashed),
            )
            user_id = cur.lastrowid
    except Exception:
        raise HTTPException(status_code=400, detail="Email already registered")

    return {"token": create_token(user_id), "user_id": user_id}


@router.post("/login")
def login(body: LoginRequest):
    with get_db() as conn:
        row = conn.execute("SELECT * FROM users WHERE email = ?", (body.email,)).fetchone()
    if not row or not bcrypt.checkpw(body.password.encode('utf-8'), row["password"].encode('utf-8')):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    return {"token": create_token(row["id"]), "user_id": row["id"]}


@router.get("/me")
def me(user_id: int = Depends(get_current_user)):
    with get_db() as conn:
        user = conn.execute("SELECT id, email, created_at FROM users WHERE id = ?", (user_id,)).fetchone()
        profile = conn.execute("SELECT * FROM brand_profiles WHERE user_id = ?", (user_id,)).fetchone()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {
        "user": dict(user),
        "has_profile": profile is not None,
        "profile": dict(profile) if profile else None,
    }
