"""
ml/infer_gemma.py
──────────────────
Inference wrapper for the fine-tuned Gemma 4 (LoRA adapter) POSTNOW model.

Imported by the FastAPI backend at startup — same public API as infer.py
so the backend can swap between mBART and Gemma without code changes.

Usage (standalone test)
-----------------------
    python infer_gemma.py \
        --adapter_path model/gemma_postnow/lora_adapter \
        --shop "Slow Drip Café" --aesthetic Cozy \
        --colors "#C8A27C,#5A3E2B" \
        --prompt "Buy 1 Get 1 Latte this weekend"

Usage (from backend)
--------------------
    from ml.infer_gemma import load_model, generate_caption, get_confidence
    loaded = load_model("ml/model/gemma_postnow/lora_adapter", base_model_id="google/gemma-4-it")
    result = generate_caption(prompt, shop_name, aesthetic, colors)
    # result = {"en_caption": ..., "kh_caption": ..., "hashtags": ...}
"""

import re
import argparse
from pathlib import Path

import torch

# ──────────────────────────────────────────────────────────────────────────────
# Constants
# ──────────────────────────────────────────────────────────────────────────────

DEFAULT_BASE_MODEL = "google/gemma-4-E4B-it"
MAX_NEW_TOKENS     = 600

SYSTEM_PROMPT = (
    "You are a bilingual social media copywriter for Cambodian coffee shops. "
    "Generate creative, natural-sounding captions in both English and Khmer. "
    "Use mixed Khmer-English for coffee terms (Latte, Cold Brew, Espresso…). "
    "Never translate word-for-word — always adapt the tone for a Cambodian audience."
)


# ──────────────────────────────────────────────────────────────────────────────
# Model class
# ──────────────────────────────────────────────────────────────────────────────

class GemmaCaptionModel:
    """
    Wraps the fine-tuned Gemma 4 LoRA adapter for POSTNOW caption generation.

    Parameters
    ----------
    adapter_path   : path to the saved LoRA adapter directory
    base_model_id  : HuggingFace base model ID (must match training)
    device         : "cuda", "mps", "cpu", or None (auto-detect)
    use_4bit       : load base model in 4-bit to save VRAM
    """

    def __init__(
        self,
        adapter_path: str | Path,
        base_model_id: str = DEFAULT_BASE_MODEL,
        device: str | None = None,
        use_4bit: bool = True,
    ):
        from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
        from peft import PeftModel

        adapter_path_str = str(adapter_path)
        is_hub_id = "/" in adapter_path_str and not adapter_path_str.startswith((".", "/"))
        adapter_path = Path(adapter_path_str)
        if not is_hub_id and not adapter_path.exists():
            raise FileNotFoundError(
                f"LoRA adapter not found: {adapter_path}\n"
                "Run ml/train_gemma.py first, or set USE_LOCAL_MODEL=false."
            )
        # For HF Hub IDs, use the string form directly in from_pretrained calls
        adapter_ref = adapter_path_str if is_hub_id else str(adapter_path)

        # Auto-detect device
        if device is None:
            device = (
                "cuda"  if torch.cuda.is_available() else
                "mps"   if torch.backends.mps.is_available() else
                "cpu"
            )
        self.device = device
        print(f"[infer_gemma] Loading base model {base_model_id} on {device} ...")

        # Tokenizer (load from adapter dir or HF Hub)
        self.tokenizer = AutoTokenizer.from_pretrained(
            adapter_ref, trust_remote_code=True
        )
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token

        # Base model (optionally quantised)
        if use_4bit and device == "cuda":
            bnb_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_use_double_quant=True,
                bnb_4bit_compute_dtype=torch.bfloat16,
            )
            base = AutoModelForCausalLM.from_pretrained(
                base_model_id,
                quantization_config=bnb_config,
                device_map="auto",
                trust_remote_code=True,
            )
        else:
            base = AutoModelForCausalLM.from_pretrained(
                base_model_id,
                torch_dtype=torch.float16 if device != "cpu" else torch.float32,
                device_map="auto" if device == "cuda" else None,
                trust_remote_code=True,
            )
            if device != "cuda":
                base = base.to(device)

        # Load LoRA adapter on top
        print(f"[infer_gemma] Loading LoRA adapter from {adapter_ref} ...")
        self.model = PeftModel.from_pretrained(base, adapter_ref)
        self.model.eval()
        print("[infer_gemma] Model ready.")

    # ── Public API ────────────────────────────────────────────────────────────

    def generate_caption(
        self,
        promotion_prompt: str,
        shop_name: str,
        aesthetic: str,
        colors: list[str],
    ) -> dict:
        """
        Generate a bilingual caption.

        Returns dict: {en_caption, kh_caption, hashtags}
        """
        user_msg = self._build_user_message(promotion_prompt, shop_name, aesthetic, colors)
        raw      = self._generate(user_msg)
        return self._parse(raw)

    # ── Private helpers ───────────────────────────────────────────────────────

    @staticmethod
    def _build_user_message(
        promotion: str, shop_name: str, aesthetic: str, colors: list[str]
    ) -> str:
        color_str = ", ".join(colors)
        return (
            "Generate a coffee shop social media caption:\n\n"
            f"Shop name: {shop_name}\n"
            f"Aesthetic: {aesthetic}\n"
            f"Brand colors: {color_str}\n"
            f"Promotion: {promotion}"
        )

    def _generate(self, user_msg: str) -> str:
        messages = [
            {"role": "system",    "content": SYSTEM_PROMPT},
            {"role": "user",      "content": user_msg},
        ]
        # Use chat template to build the prompt
        prompt = self.tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,   # adds the assistant turn prefix
        )
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)

        with torch.no_grad():
            output_ids = self.model.generate(
                **inputs,
                max_new_tokens=MAX_NEW_TOKENS,
                do_sample=True,
                temperature=0.7,
                top_p=0.9,
                repetition_penalty=1.1,
                pad_token_id=self.tokenizer.eos_token_id,
            )

        # Decode only the newly generated tokens (skip the prompt)
        new_tokens = output_ids[0][inputs["input_ids"].shape[1]:]
        return self.tokenizer.decode(new_tokens, skip_special_tokens=True)

    @staticmethod
    def _parse(raw: str) -> dict:
        """Extract [EN] / [KH] / [TAGS] from generated text."""
        en_match  = re.search(r"\[EN\]\s*(.*?)\s*(?=\[KH\]|\[TAGS\]|$)",  raw, re.DOTALL)
        kh_match  = re.search(r"\[KH\]\s*(.*?)\s*(?=\[EN\]|\[TAGS\]|$)",  raw, re.DOTALL)
        tag_match = re.search(r"\[TAGS\]\s*(.*?)$",                         raw, re.DOTALL)
        return {
            "en_caption": en_match.group(1).strip()  if en_match  else "",
            "kh_caption": kh_match.group(1).strip()  if kh_match  else "",
            "hashtags":   tag_match.group(1).strip() if tag_match else "",
        }

    def confidence_score(self, output: dict) -> float:
        """Heuristic 0–1 confidence score used by the backend fallback logic."""
        en   = output.get("en_caption", "")
        kh   = output.get("kh_caption", "")
        tags = output.get("hashtags",   "")
        if not en or not kh or not tags:
            return 0.0
        if len(en) < 30 or len(kh) < 10:
            return 0.0
        if tags.count("#") < 3:
            return 0.3
        return round(min(1.0, (len(en) + len(kh)) / 400), 3)


# ──────────────────────────────────────────────────────────────────────────────
# Module-level singleton (loaded once by the backend)
# ──────────────────────────────────────────────────────────────────────────────

_model_instance: GemmaCaptionModel | None = None


def load_model(
    adapter_path: str,
    base_model_id: str = DEFAULT_BASE_MODEL,
    use_4bit: bool = True,
) -> bool:
    global _model_instance
    try:
        _model_instance = GemmaCaptionModel(adapter_path, base_model_id, use_4bit=use_4bit)
        return True
    except FileNotFoundError as e:
        print(f"[infer_gemma] ⚠  {e}")
        return False
    except Exception as e:
        print(f"[infer_gemma] ⚠  Failed to load model: {e}")
        return False


def generate_caption(
    promotion_prompt: str,
    shop_name: str,
    aesthetic: str,
    colors: list[str],
) -> dict:
    if _model_instance is None:
        raise RuntimeError("Gemma model not loaded. Call load_model() first.")
    return _model_instance.generate_caption(promotion_prompt, shop_name, aesthetic, colors)


def get_confidence(output: dict) -> float:
    if _model_instance is None:
        return 0.0
    return _model_instance.confidence_score(output)


# ──────────────────────────────────────────────────────────────────────────────
# CLI test
# ──────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test Gemma 4 inference")
    parser.add_argument("--adapter_path",  default="model/gemma_postnow/lora_adapter")
    parser.add_argument("--base_model_id", default=DEFAULT_BASE_MODEL)
    parser.add_argument("--shop",      default="Slow Drip Café")
    parser.add_argument("--aesthetic", default="Cozy")
    parser.add_argument("--colors",    default="#C8A27C,#5A3E2B")
    parser.add_argument("--prompt",    default="Buy 1 Get 1 Latte this weekend")
    args = parser.parse_args()

    model  = GemmaCaptionModel(args.adapter_path, args.base_model_id)
    colors = [c.strip() for c in args.colors.split(",")]
    result = model.generate_caption(args.prompt, args.shop, args.aesthetic, colors)

    print("\n─── Generated Caption ───────────────────────────────")
    print(f"[EN]\n{result['en_caption']}\n")
    print(f"[KH]\n{result['kh_caption']}\n")
    print(f"[TAGS]\n{result['hashtags']}")
    print(f"\nConfidence: {model.confidence_score(result)}")
