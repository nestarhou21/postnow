"""
ml/infer.py
───────────
Inference wrapper for the fine-tuned mBART-large-50 POSTNOW model.

This module is imported by the FastAPI backend at startup.
It exposes a single function: generate_caption()

Usage (standalone test)
-----------------------
    python infer.py --model_path model/final \
                    --shop "Slow Drip Café" \
                    --aesthetic Cozy \
                    --colors "#C8A27C,#5A3E2B,#FFF8F0" \
                    --prompt "Buy 1 Get 1 Latte this weekend"

Usage (from backend)
--------------------
    from ml.infer import CaptionModel
    _model = CaptionModel("ml/model/final")   # loaded once at startup
    result = _model.generate_caption(prompt, shop_name, aesthetic, colors)
    # result = {"en_caption": ..., "kh_caption": ..., "hashtags": ...}
"""

import os
import re
import argparse
from pathlib import Path

import torch
from transformers import MBartForConditionalGeneration, MBart50TokenizerFast

# ──────────────────────────────────────────────────────────────────────────────
# Constants (must match train.py)
# ──────────────────────────────────────────────────────────────────────────────

SRC_LANG       = "en_XX"
TGT_LANG       = "en_XX"
MAX_SOURCE_LEN = 128
MAX_TARGET_LEN = 512

# Beam search defaults
NUM_BEAMS       = 4
LENGTH_PENALTY  = 1.2
NO_REPEAT_NGRAM = 3


# ──────────────────────────────────────────────────────────────────────────────
# Model class
# ──────────────────────────────────────────────────────────────────────────────

class CaptionModel:
    """
    Wraps the fine-tuned mBART model for POSTNOW caption generation.

    Parameters
    ----------
    model_path : str | Path
        Path to the directory created by train.py (contains config.json,
        pytorch_model.bin / model.safetensors, tokenizer_config.json, etc.)
    device : str | None
        "cuda", "mps", or "cpu". Auto-detected if None.
    """

    def __init__(self, model_path: str | Path, device: str | None = None):
        model_path = Path(model_path)
        if not model_path.exists():
            raise FileNotFoundError(
                f"Model directory not found: {model_path}\n"
                "Run ml/train.py first, or set USE_LOCAL_MODEL=false to use Claude fallback."
            )

        if device is None:
            if torch.cuda.is_available():
                device = "cuda"
            elif torch.backends.mps.is_available():
                device = "mps"
            else:
                device = "cpu"

        self.device = device
        print(f"[infer] Loading model from {model_path} on {device} ...")

        self.tokenizer = MBart50TokenizerFast.from_pretrained(
            str(model_path),
            src_lang=SRC_LANG,
            tgt_lang=TGT_LANG,
        )
        self.model = MBartForConditionalGeneration.from_pretrained(str(model_path))
        self.model.eval()
        self.model.to(device)

        # Forced BOS token for the decoder (target language start)
        self._tgt_lang_id = self.tokenizer.lang_code_to_id[TGT_LANG]

        print(f"[infer] Model ready.")

    # ── Public API ────────────────────────────────────────────────────────────

    def generate_caption(
        self,
        promotion_prompt: str,
        shop_name: str,
        aesthetic: str,
        colors: list[str],
    ) -> dict:
        """
        Generate a bilingual caption for a promotion.

        Returns
        -------
        dict with keys: en_caption, kh_caption, hashtags
        """
        input_text = self._build_input(shop_name, aesthetic, colors, promotion_prompt)
        raw_output = self._generate(input_text)
        return self._parse(raw_output)

    # ── Private helpers ───────────────────────────────────────────────────────

    @staticmethod
    def _build_input(
        shop_name: str, aesthetic: str, colors: list[str], promotion: str
    ) -> str:
        color_str = ",".join(colors)
        return f"{shop_name} | {aesthetic} | {color_str} | {promotion}"

    def _generate(self, input_text: str) -> str:
        self.tokenizer.src_lang = SRC_LANG
        inputs = self.tokenizer(
            input_text,
            return_tensors="pt",
            max_length=MAX_SOURCE_LEN,
            truncation=True,
        ).to(self.device)

        with torch.no_grad():
            output_ids = self.model.generate(
                **inputs,
                forced_bos_token_id=self._tgt_lang_id,
                max_new_tokens=MAX_TARGET_LEN,
                num_beams=NUM_BEAMS,
                length_penalty=LENGTH_PENALTY,
                no_repeat_ngram_size=NO_REPEAT_NGRAM,
                early_stopping=True,
            )

        return self.tokenizer.decode(output_ids[0], skip_special_tokens=True)

    @staticmethod
    def _parse(raw: str) -> dict:
        """
        Extract [EN] / [KH] / [TAGS] sections from the model output.
        Falls back to empty strings if a section is missing.
        """
        en_match  = re.search(r"\[EN\]\s*(.*?)\s*(?=\[KH\]|\[TAGS\]|$)", raw, re.DOTALL)
        kh_match  = re.search(r"\[KH\]\s*(.*?)\s*(?=\[EN\]|\[TAGS\]|$)", raw, re.DOTALL)
        tag_match = re.search(r"\[TAGS\]\s*(.*?)$", raw, re.DOTALL)

        return {
            "en_caption": en_match.group(1).strip()  if en_match  else "",
            "kh_caption": kh_match.group(1).strip()  if kh_match  else "",
            "hashtags":   tag_match.group(1).strip() if tag_match else "",
        }

    def confidence_score(self, output: dict) -> float:
        """
        Heuristic confidence score 0–1.
        Used by the backend to decide whether to fall back to Claude.
        Returns 0.0 if any section is empty or suspiciously short.
        """
        en   = output.get("en_caption", "")
        kh   = output.get("kh_caption", "")
        tags = output.get("hashtags",   "")

        if not en or not kh or not tags:
            return 0.0
        if len(en) < 30 or len(kh) < 10:
            return 0.0
        if tags.count("#") < 3:
            return 0.3

        # Simple length-based heuristic (good outputs are 80–300 chars per section)
        score = min(1.0, (len(en) + len(kh)) / 400)
        return round(score, 3)


# ──────────────────────────────────────────────────────────────────────────────
# Module-level singleton (loaded once by the backend)
# ──────────────────────────────────────────────────────────────────────────────

_model_instance: CaptionModel | None = None


def load_model(model_path: str) -> bool:
    """
    Load the model into the module-level singleton.
    Called once at backend startup.

    Returns True on success, False if model_path doesn't exist.
    """
    global _model_instance
    try:
        _model_instance = CaptionModel(model_path)
        return True
    except FileNotFoundError as e:
        print(f"[infer] ⚠  {e}")
        return False
    except Exception as e:
        print(f"[infer] ⚠  Failed to load model: {e}")
        return False


def generate_caption(
    promotion_prompt: str,
    shop_name: str,
    aesthetic: str,
    colors: list[str],
) -> dict:
    """
    Top-level function called by the backend (mirrors caption_agent.generate_caption signature).
    Raises RuntimeError if model is not loaded.
    """
    if _model_instance is None:
        raise RuntimeError("Local model not loaded. Call load_model() first.")
    return _model_instance.generate_caption(promotion_prompt, shop_name, aesthetic, colors)


def get_confidence(output: dict) -> float:
    """Return a confidence score for the output from the singleton model."""
    if _model_instance is None:
        return 0.0
    return _model_instance.confidence_score(output)


# ──────────────────────────────────────────────────────────────────────────────
# CLI test
# ──────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test mBART inference")
    parser.add_argument("--model_path", default="model/final", help="Path to saved model directory")
    parser.add_argument("--shop",       default="Slow Drip Café",                  help="Shop name")
    parser.add_argument("--aesthetic",  default="Cozy",                             help="Cozy | Bold | Minimalist")
    parser.add_argument("--colors",     default="#C8A27C,#5A3E2B,#FFF8F0",         help="Comma-separated hex colors")
    parser.add_argument("--prompt",     default="Buy 1 Get 1 Latte this weekend",  help="Promotion prompt")
    args = parser.parse_args()

    model = CaptionModel(args.model_path)
    colors = [c.strip() for c in args.colors.split(",")]

    result = model.generate_caption(args.prompt, args.shop, args.aesthetic, colors)

    print("\n─── Generated Caption ───────────────────────────────")
    print(f"[EN]\n{result['en_caption']}\n")
    print(f"[KH]\n{result['kh_caption']}\n")
    print(f"[TAGS]\n{result['hashtags']}")
    print(f"\nConfidence: {model.confidence_score(result)}")
