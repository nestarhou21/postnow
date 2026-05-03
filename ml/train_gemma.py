"""
ml/train_gemma.py
──────────────────
Fine-tunes Google Gemma 4 on the POSTNOW 2,500-caption bilingual dataset
using QLoRA (4-bit quantisation + LoRA adapters) via HuggingFace PEFT + TRL.

Architecture difference from mBART:
  mBART  → encoder-decoder (Seq2SeqTrainer)
  Gemma  → decoder-only causal LM (SFTTrainer, next-token prediction)

The model learns to complete prompts of the form:
  [user]  → category + metadata (product, mood, occasion…)
  [model] → [EN] caption + [KH] caption + [TAGS]

──────────────────────────────────────────────────────────────
RECOMMENDED: Run on Google Colab with a free T4/A100 GPU.

Quick start (Colab):
  1. Upload this file + postnow_training_data_2500.json to Colab
  2. !pip install -q -r requirements_gemma.txt
  3. Log in: !huggingface-cli login   (need access to google/gemma-4-it)
  4. !python train_gemma.py

Local (needs ≥16 GB VRAM for 4-bit):
  python train_gemma.py --output_dir model/gemma_postnow

Args:
  --data_file     path to postnow_training_data_2500.json
  --output_dir    where to save LoRA adapter weights
  --model_id      HuggingFace model ID  (default: google/gemma-4-it)
  --epochs        training epochs       (default: 3)
  --batch_size    per-device batch size (default: 2)
  --grad_accum    gradient accumulation (default: 8)
  --lr            learning rate         (default: 2e-4)
  --max_seq_len   max token length      (default: 768)
  --lora_r        LoRA rank             (default: 16)
  --lora_alpha    LoRA alpha            (default: 32)
  --val_ratio     validation split      (default: 0.10)
  --smoke_test    run 20 steps only to verify setup
──────────────────────────────────────────────────────────────
"""

import os
import sys
import json
import random
import argparse
from pathlib import Path

# ── Dependency check ───────────────────────────────────────────────────────────
def _check_deps():
    missing = []
    for pkg in ("transformers", "peft", "trl", "bitsandbytes", "accelerate", "datasets"):
        try:
            __import__(pkg)
        except ImportError:
            missing.append(pkg)
    if missing:
        print("❌  Missing packages:", ", ".join(missing))
        print("   Run:  pip install -r ml/requirements_gemma.txt")
        sys.exit(1)

_check_deps()

import torch
from datasets import Dataset
from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    BitsAndBytesConfig,
    TrainingArguments,
)
from peft import LoraConfig, get_peft_model, TaskType, prepare_model_for_kbit_training
from trl import SFTTrainer, SFTConfig

# ──────────────────────────────────────────────────────────────────────────────
# Defaults
# ──────────────────────────────────────────────────────────────────────────────

DEFAULT_MODEL   = "google/gemma-4-E4B-it"   # 4B active params — fits on Colab T4 with QLoRA
# Other options:
#   google/gemma-4-E2B-it     → smallest, fastest (2B active params)
#   google/gemma-4-26B-A4B-it → 26B MoE, 4B active — needs A100
#   google/gemma-4-31B-it     → 31B dense — needs A100 80GB
DEFAULT_DATA    = str(Path(__file__).parent / "data_gemini" / "postnow_training_data_2500.json")
DEFAULT_OUTPUT  = str(Path(__file__).parent / "model" / "gemma_postnow")

SYSTEM_PROMPT = (
    "You are a bilingual social media copywriter for Cambodian coffee shops. "
    "Generate creative, natural-sounding captions in both English and Khmer. "
    "Use mixed Khmer-English for coffee terms (Latte, Cold Brew, Espresso…). "
    "Never translate word-for-word — always adapt the tone for a Cambodian audience."
)


# ──────────────────────────────────────────────────────────────────────────────
# Dataset helpers
# ──────────────────────────────────────────────────────────────────────────────

def build_instruction(entry: dict) -> str:
    """Build the user-turn instruction from a caption entry."""
    meta = entry.get("metadata", {})
    cat  = entry.get("category", "general")
    lines = [
        f"Category: {cat.replace('_', ' ').title()}",
        f"Product: {meta.get('product', '')}",
    ]
    if meta.get("promotion"):
        lines.append(f"Promotion: {meta['promotion']}")
    lines += [
        f"Mood: {meta.get('mood', '')}",
        f"Occasion: {meta.get('occasion', '')}",
        f"Target audience: {meta.get('target_audience', '')}",
    ]
    return "\n".join(lines)


def build_response(entry: dict) -> str:
    """Build the model-turn response: [EN] + [KH] + [TAGS]."""
    cap  = entry.get("caption", {})
    tags = entry.get("hashtags", {})
    en_tags = " ".join(tags.get("en", []))
    km_tags = " ".join(tags.get("km", []))
    all_tags = (en_tags + " " + km_tags).strip()
    return (
        f"[EN]\n{cap.get('en', '')}\n\n"
        f"[KH]\n{cap.get('km', '')}\n\n"
        f"[TAGS]\n{all_tags}"
    )


def format_chat(tokenizer, entry: dict) -> str:
    """
    Format one entry as a full Gemma chat string using the tokenizer's
    apply_chat_template so the special tokens are correct for the model version.
    """
    instruction = build_instruction(entry)
    response    = build_response(entry)

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user",   "content": f"Generate a coffee shop social media caption:\n\n{instruction}"},
        {"role": "assistant", "content": response},
    ]

    # apply_chat_template adds <bos>, turn tokens, <eos> correctly for Gemma
    return tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=False,
    )


def load_and_prepare(data_file: str, tokenizer, val_ratio: float = 0.10, seed: int = 42):
    """Load JSON → format as chat strings → HuggingFace Dataset → train/val split."""
    with open(data_file, encoding="utf-8") as f:
        raw = json.load(f)

    entries = raw.get("captions", raw) if isinstance(raw, dict) else raw
    print(f"  Loaded {len(entries)} entries from {data_file}")

    texts = [{"text": format_chat(tokenizer, e)} for e in entries]

    # Shuffle + split
    random.seed(seed)
    random.shuffle(texts)
    n_val   = max(1, int(len(texts) * val_ratio))
    train_t = texts[n_val:]
    val_t   = texts[:n_val]

    train_ds = Dataset.from_list(train_t)
    val_ds   = Dataset.from_list(val_t)
    print(f"  Split → {len(train_ds)} train / {len(val_ds)} val")
    return train_ds, val_ds


# ──────────────────────────────────────────────────────────────────────────────
# Model loading
# ──────────────────────────────────────────────────────────────────────────────

def load_model_and_tokenizer(model_id: str, use_4bit: bool = True):
    """Load Gemma with optional 4-bit QLoRA quantisation."""
    print(f"\n  Loading tokenizer: {model_id}")
    tokenizer = AutoTokenizer.from_pretrained(model_id, trust_remote_code=True)

    # Gemma tokenizer may not have a pad token by default
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "right"  # required for causal LM fine-tuning

    if use_4bit:
        print("  Using 4-bit QLoRA quantisation (bitsandbytes)")
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_use_double_quant=True,
            bnb_4bit_compute_dtype=torch.bfloat16,
        )
        model = AutoModelForCausalLM.from_pretrained(
            model_id,
            quantization_config=bnb_config,
            device_map="auto",
            trust_remote_code=True,
        )
        model = prepare_model_for_kbit_training(model)
    else:
        print("  Loading in full precision (no quantisation)")
        model = AutoModelForCausalLM.from_pretrained(
            model_id,
            torch_dtype=torch.bfloat16,
            device_map="auto",
            trust_remote_code=True,
        )

    return model, tokenizer


# ──────────────────────────────────────────────────────────────────────────────
# LoRA config
# ──────────────────────────────────────────────────────────────────────────────

def apply_lora(model, r: int = 16, alpha: int = 32, dropout: float = 0.05):
    """
    Wrap model with LoRA adapters.

    Gemma 4 uses a Mixture-of-Experts (MoE) architecture — expert layer names
    differ across model sizes. Using target_modules="all-linear" auto-detects
    every nn.Linear in the model, covering attention AND expert MLP layers
    regardless of naming convention.
    """
    lora_config = LoraConfig(
        task_type=TaskType.CAUSAL_LM,
        r=r,
        lora_alpha=alpha,
        lora_dropout=dropout,
        bias="none",
        target_modules="all-linear",   # handles MoE + dense Gemma 4 variants
        inference_mode=False,
    )
    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()
    return model


# ──────────────────────────────────────────────────────────────────────────────
# Training
# ──────────────────────────────────────────────────────────────────────────────

def train(args):
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    use_4bit = torch.cuda.is_available()   # skip quantisation on CPU-only machines
    if not torch.cuda.is_available():
        print("⚠   No GPU detected — training on CPU (very slow). Use Colab for GPU.")

    # ── Load model ────────────────────────────────────────────────────────────
    print(f"\n🤖  Loading {args.model_id} ...")
    model, tokenizer = load_model_and_tokenizer(args.model_id, use_4bit=use_4bit)

    # ── Apply LoRA ────────────────────────────────────────────────────────────
    print("\n🔧  Applying LoRA adapters ...")
    model = apply_lora(model, r=args.lora_r, alpha=args.lora_alpha)

    # ── Prepare dataset ───────────────────────────────────────────────────────
    print(f"\n📂  Preparing dataset from {args.data_file} ...")
    train_ds, val_ds = load_and_prepare(
        args.data_file, tokenizer, val_ratio=args.val_ratio
    )

    # ── SFT config ────────────────────────────────────────────────────────────
    max_steps = 20 if args.smoke_test else -1

    sft_config = SFTConfig(
        output_dir=str(output_dir),
        num_train_epochs=args.epochs,
        max_steps=max_steps,

        per_device_train_batch_size=args.batch_size,
        per_device_eval_batch_size=args.batch_size,
        gradient_accumulation_steps=args.grad_accum,

        learning_rate=args.lr,
        warmup_ratio=0.05,
        lr_scheduler_type="cosine",
        weight_decay=0.01,
        optim="paged_adamw_8bit" if use_4bit else "adamw_torch",

        bf16=torch.cuda.is_available() and torch.cuda.is_bf16_supported(),
        fp16=torch.cuda.is_available() and not torch.cuda.is_bf16_supported(),

        max_seq_length=args.max_seq_len,
        dataset_text_field="text",
        packing=False,             # set True to pack short sequences (faster, needs more RAM)

        eval_strategy="epoch",
        save_strategy="epoch",
        save_total_limit=2,
        load_best_model_at_end=True,
        metric_for_best_model="eval_loss",

        logging_steps=10,
        report_to="none",

        seed=42,
        dataset_num_proc=1,        # safe for Colab
    )

    # ── Trainer ───────────────────────────────────────────────────────────────
    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        args=sft_config,
        train_dataset=train_ds,
        eval_dataset=val_ds,
    )

    # ── Train ─────────────────────────────────────────────────────────────────
    mode = "SMOKE TEST (20 steps)" if args.smoke_test else f"{args.epochs} epochs"
    eff_batch = args.batch_size * args.grad_accum
    print(f"\n🚀  Starting training — {mode} | effective batch {eff_batch} | lr {args.lr}")
    trainer.train()

    # ── Save LoRA adapter ─────────────────────────────────────────────────────
    adapter_path = output_dir / "lora_adapter"
    trainer.model.save_pretrained(str(adapter_path))
    tokenizer.save_pretrained(str(adapter_path))
    print(f"\n✅  LoRA adapter saved → {adapter_path}")
    print("    To load for inference:  PeftModel.from_pretrained(base_model, adapter_path)")

    # ── Save training metadata ────────────────────────────────────────────────
    meta = {
        "base_model":   args.model_id,
        "train_size":   len(train_ds),
        "val_size":     len(val_ds),
        "epochs":       args.epochs,
        "batch_size":   args.batch_size,
        "grad_accum":   args.grad_accum,
        "eff_batch":    eff_batch,
        "lr":           args.lr,
        "lora_r":       args.lora_r,
        "lora_alpha":   args.lora_alpha,
        "max_seq_len":  args.max_seq_len,
        "quantisation": "4-bit QLoRA" if use_4bit else "none (CPU)",
        "adapter_path": str(adapter_path),
    }
    with open(output_dir / "training_meta.json", "w") as f:
        json.dump(meta, f, indent=2)
    print(f"📄  Metadata → {output_dir}/training_meta.json")


# ──────────────────────────────────────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────────────────────────────────────

def parse_args():
    p = argparse.ArgumentParser(description="Fine-tune Gemma 4 for POSTNOW caption generation")
    p.add_argument("--model_id",    default=DEFAULT_MODEL,  help="HuggingFace model ID")
    p.add_argument("--data_file",   default=DEFAULT_DATA,   help="Path to postnow_training_data_2500.json")
    p.add_argument("--output_dir",  default=DEFAULT_OUTPUT, help="Output directory for LoRA adapter")
    p.add_argument("--epochs",      type=int,   default=3)
    p.add_argument("--batch_size",  type=int,   default=2,   help="Per-device train batch size")
    p.add_argument("--grad_accum",  type=int,   default=8,   help="Gradient accumulation steps")
    p.add_argument("--lr",          type=float, default=2e-4)
    p.add_argument("--max_seq_len", type=int,   default=768)
    p.add_argument("--lora_r",      type=int,   default=16,  help="LoRA rank")
    p.add_argument("--lora_alpha",  type=int,   default=32,  help="LoRA alpha")
    p.add_argument("--val_ratio",   type=float, default=0.10)
    p.add_argument("--smoke_test",  action="store_true",    help="Run 20 steps only to verify setup")
    return p.parse_args()


if __name__ == "__main__":
    args = parse_args()
    print("=" * 60)
    print("POSTNOW — Gemma 4 Fine-tuning (QLoRA)")
    print("=" * 60)
    print(f"  Model      : {args.model_id}")
    print(f"  Data file  : {args.data_file}")
    print(f"  Output dir : {args.output_dir}")
    print(f"  Epochs     : {args.epochs}")
    print(f"  Batch size : {args.batch_size} × {args.grad_accum} (eff {args.batch_size * args.grad_accum})")
    print(f"  LR         : {args.lr}")
    print(f"  LoRA r/α   : {args.lora_r}/{args.lora_alpha}")
    print(f"  Max seq    : {args.max_seq_len}")
    print()
    train(args)
