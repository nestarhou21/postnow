"""
routes/profile.py — Save and retrieve brand profile
"""
import json
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List
from db import get_db
from routes.auth import get_current_user

router = APIRouter(prefix="/profile", tags=["profile"])


class ProfileRequest(BaseModel):
    shop_name: str
    aesthetic: str          # Cozy | Bold | Minimalist
    colors: List[str]       # e.g. ["#F5A623", "#FFFFFF", "#2C1A0E"]


@router.post("")
def save_profile(body: ProfileRequest, user_id: int = Depends(get_current_user)):
    colors_json = json.dumps(body.colors)
    with get_db() as conn:
        existing = conn.execute(
            "SELECT id FROM brand_profiles WHERE user_id = ?", (user_id,)
        ).fetchone()
        if existing:
            conn.execute(
                """UPDATE brand_profiles
                   SET shop_name=?, aesthetic=?, colors=?, updated_at=datetime('now')
                   WHERE user_id=?""",
                (body.shop_name, body.aesthetic, colors_json, user_id),
            )
        else:
            conn.execute(
                "INSERT INTO brand_profiles (user_id, shop_name, aesthetic, colors) VALUES (?,?,?,?)",
                (user_id, body.shop_name, body.aesthetic, colors_json),
            )
    return {"message": "Profile saved"}


@router.get("")
def get_profile(user_id: int = Depends(get_current_user)):
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM brand_profiles WHERE user_id = ?", (user_id,)
        ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="No profile found")
    data = dict(row)
    data["colors"] = json.loads(data["colors"])
    return data
