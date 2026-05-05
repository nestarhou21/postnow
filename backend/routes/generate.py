"""
routes/generate.py — Orchestrates caption_agent + image_agent in parallel

POST /generate  →  returns poster + EN caption + KH caption + hashtags

Caption generation priority
───────────────────────────
1. Fine-tuned local model (ml/infer.py or ml/infer_gemma.py depending on LOCAL_MODEL_TYPE)
   — if USE_LOCAL_MODEL=true AND model loaded.
   Falls back to Claude if model confidence is below CONFIDENCE_THRESHOLD.
2. Claude API fallback (agents/caption_agent.py) — always available.
"""

import os
import sys
import json
import asyncio
from concurrent.futures import ThreadPoolExecutor
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from db import get_db
from routes.auth import get_current_user
from agents.caption_agent import generate_gemini_caption
from agents.image_agent import generate_poster

router   = APIRouter(prefix="/generate", tags=["generate"])
executor = ThreadPoolExecutor(max_workers=4)

# ── Local model bootstrap ─────────────────────────────────────────────────────

USE_LOCAL_MODEL      = os.getenv("USE_LOCAL_MODEL", "true").lower() == "true"
LOCAL_MODEL_TYPE     = os.getenv("LOCAL_MODEL_TYPE", "mbart")   # "mbart" or "gemma"
LOCAL_MODEL_PATH     = os.getenv("LOCAL_MODEL_PATH", "ml/model/final")
CONFIDENCE_THRESHOLD = float(os.getenv("CONFIDENCE_THRESHOLD", "0.4"))

_infer_module = None
_model_loaded = False


def _try_load_local_model():
    """
    Attempt to import ml.infer (mBART) or ml.infer_gemma (Gemma 4) and load the model.
    Which module is used is controlled by LOCAL_MODEL_TYPE env var.
    Called once at startup. Silently degrades if model not found.
    """
    global _infer_module, _model_loaded

    if not USE_LOCAL_MODEL:
        print("[generate] USE_LOCAL_MODEL=false — using Claude fallback only.")
        return

    # The backend runs from the backend/ directory; go one level up to find ml/
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

    module_name = "ml.infer_gemma" if LOCAL_MODEL_TYPE == "gemma" else "ml.infer"
    label       = "Gemma 4"        if LOCAL_MODEL_TYPE == "gemma" else "mBART"

    try:
        import importlib
        infer_module = importlib.import_module(module_name)
        # Use HF Hub ID directly if it looks like one (e.g. "Nestar2107/postnow_model")
        # Otherwise treat as a local path relative to project root
        if "/" in LOCAL_MODEL_PATH and not LOCAL_MODEL_PATH.startswith((".", "/")):
            model_path = LOCAL_MODEL_PATH
        else:
            model_path = os.path.join(project_root, LOCAL_MODEL_PATH)
        success      = infer_module.load_model(model_path)
        if success:
            _infer_module = infer_module
            _model_loaded = True
            print(f"[generate] ✅  Local {label} model loaded from {model_path}")
        else:
            print(f"[generate] ⚠  Local model not found at {model_path} — Claude fallback active.")
    except ImportError as e:
        print(f"[generate] ⚠  Could not import {module_name}: {e} — Claude fallback active.")
    except Exception as e:
        print(f"[generate] ⚠  Model load error: {e} — Claude fallback active.")


# Load model at import time (i.e., at FastAPI startup)
_try_load_local_model()


# ── Caption dispatch ──────────────────────────────────────────────────────────

def _generate_caption_dispatch(
    promotion_prompt: str,
    shop_name: str,
    aesthetic: str,
    colors: list,
) -> dict:
    if _model_loaded and _infer_module is not None:
        return _infer_module.generate_caption(promotion_prompt, shop_name, aesthetic, colors)
    # Local model not available — use Gemini API
    return generate_gemini_caption(promotion_prompt, shop_name, aesthetic, colors)


# ── Pydantic schemas ──────────────────────────────────────────────────────────

class GenerateRequest(BaseModel):
    prompt: str
    template_id: str = "centered"           # centered | text_banner | lifestyle | minimal
    reference_image_base64: str | None = None   # user-uploaded coffee photo (base64, no data: prefix)
    reference_image_mime: str = "image/jpeg"


class GuestGenerateRequest(BaseModel):
    prompt: str
    template_id: str = "centered"
    shop_name: str = "My Café"
    aesthetic: str = "Cozy"
    colors: list[str] = ["#C8A27C", "#5A3E2B"]
    reference_image_base64: str | None = None
    reference_image_mime: str = "image/jpeg"


class GenerateResponse(BaseModel):
    generation_id: int
    en_caption: str
    kh_caption: str
    hashtags: str
    image_data_url: str
    prompt_used: str


# ── DB helpers ────────────────────────────────────────────────────────────────

def _load_profile(user_id: int) -> dict:
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM brand_profiles WHERE user_id = ?", (user_id,)
        ).fetchone()
    if not row:
        raise HTTPException(
            status_code=400,
            detail="Brand profile not found. Please complete onboarding first.",
        )
    profile = dict(row)
    profile["colors"] = json.loads(profile["colors"])
    return profile


def _save_generation(user_id, prompt, template_id, caption_result, image_result) -> int:
    with get_db() as conn:
        cur = conn.execute(
            """INSERT INTO generations
               (user_id, prompt, template_id, en_caption, kh_caption, hashtags, image_url)
               VALUES (?,?,?,?,?,?,?)""",
            (
                user_id,
                prompt,
                template_id,
                caption_result["en_caption"],
                caption_result["kh_caption"],
                caption_result["hashtags"],
                image_result["image_data_url"][:500],
            ),
        )
        return cur.lastrowid


# ── Routes ────────────────────────────────────────────────────────────────────

@router.post("", response_model=GenerateResponse)
async def generate(body: GenerateRequest, user_id: int = Depends(get_current_user)):
    profile = _load_profile(user_id)

    loop = asyncio.get_event_loop()

    caption_future = loop.run_in_executor(
        executor,
        _generate_caption_dispatch,
        body.prompt,
        profile["shop_name"],
        profile["aesthetic"],
        profile["colors"],
    )

    image_future = loop.run_in_executor(
        executor,
        generate_poster,
        body.prompt,
        profile["shop_name"],
        profile["aesthetic"],
        profile["colors"],
        body.template_id,
        body.reference_image_base64,
        body.reference_image_mime,
    )

    try:
        caption_result, image_result = await asyncio.gather(caption_future, image_future)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")

    gen_id = _save_generation(user_id, body.prompt, body.template_id, caption_result, image_result)

    return GenerateResponse(
        generation_id=gen_id,
        en_caption=caption_result["en_caption"],
        kh_caption=caption_result["kh_caption"],
        hashtags=caption_result["hashtags"],
        image_data_url=image_result["image_data_url"],
        prompt_used=image_result["prompt_used"],
    )


@router.get("/history")
def get_history(user_id: int = Depends(get_current_user)):
    with get_db() as conn:
        rows = conn.execute(
            """SELECT id, prompt, template_id, en_caption, kh_caption, hashtags, created_at
               FROM generations WHERE user_id = ? ORDER BY created_at DESC LIMIT 20""",
            (user_id,),
        ).fetchall()
    return [dict(r) for r in rows]


@router.post("/guest")
async def generate_guest(body: GuestGenerateRequest):
    """No auth required — for public demo / free trial."""
    loop = asyncio.get_event_loop()

    caption_future = loop.run_in_executor(
        executor,
        _generate_caption_dispatch,
        body.prompt,
        body.shop_name,
        body.aesthetic,
        body.colors,
    )

    image_future = loop.run_in_executor(
        executor,
        generate_poster,
        body.prompt,
        body.shop_name,
        body.aesthetic,
        body.colors,
        body.template_id,
        body.reference_image_base64,
        body.reference_image_mime,
    )

    try:
        caption_result, image_result = await asyncio.gather(caption_future, image_future)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")

    return {
        "generation_id": 0,
        "en_caption":    caption_result["en_caption"],
        "kh_caption":    caption_result["kh_caption"],
        "hashtags":      caption_result["hashtags"],
        "image_data_url": image_result["image_data_url"],
        "prompt_used":   image_result["prompt_used"],
    }


@router.get("/model-status")
def model_status():
    """Debug endpoint: reports which caption model is active."""
    label = "Gemma 4" if LOCAL_MODEL_TYPE == "gemma" else "mBART"
    return {
        "use_local_model":      USE_LOCAL_MODEL,
        "local_model_type":     LOCAL_MODEL_TYPE,
        "local_model_loaded":   _model_loaded,
        "model_path":           LOCAL_MODEL_PATH,
        "confidence_threshold": CONFIDENCE_THRESHOLD,
        "active_caption_model": f"{label} (local)" if _model_loaded else "Claude API",
    }
