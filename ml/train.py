"""
ml/train.py
───────────
Fine-tunes facebook/mbart-large-50 on the POSTNOW synthetic coffee-shop
bilingual caption dataset.

Usage (local / Colab)
-----
    # Quick smoke test (10 steps)
    python train.py --data_dir data/raw --output_dir model --epochs 1 --max_steps 10

    # Full training run
    python train.py --data_dir data/raw --output_dir model --epochs 5 --batch_size 4

Colab recommended for full training (T4/A100 GPU).

Requirements
------------
    pip install transformers==4.40.0 datasets sentencepiece torch sacrebleu accelerate

Model card
----------
    facebook/mbart-large-50
    - 610M parameters
    - Pre-trained on CC-25 in 50 languages (includes km_KH and en_XX)
    - Fine-tuned here for structured bilingual caption generation
"""

import os
import re
import json
import argparse
import random
from pathlib import Path

# Remove MPS memory cap so the full 16 GB unified memory is available for training
os.environ.setdefault("PYTORCH_MPS_HIGH_WATERMARK_RATIO", "0.0")

import torch
from torch.utils.data import Dataset, DataLoader
from transformers import (
    MBartForConditionalGeneration,
    MBart50TokenizerFast,
    Seq2SeqTrainer,
    Seq2SeqTrainingArguments,
    DataCollatorForSeq2Seq,
)
from datasets import load_dataset

# ──────────────────────────────────────────────────────────────────────────────
# Constants
# ──────────────────────────────────────────────────────────────────────────────

BASE_MODEL = "facebook/mbart-large-50"

# mBART language tokens
SRC_LANG = "en_XX"   # Input is English marketing text
TGT_LANG = "en_XX"   # Output starts with EN caption; model handles KH internally

MAX_SOURCE_LEN = 128
MAX_TARGET_LEN = 256   # captions are ~100-150 tokens; 256 is safe and halves decoder memory


# ──────────────────────────────────────────────────────────────────────────────
# Dataset
# ──────────────────────────────────────────────────────────────────────────────

class CaptionDataset(Dataset):
    """Loads JSONL records: {"input": str, "output": str}"""

    def __init__(self, records: list[dict], tokenizer, max_src: int, max_tgt: int):
        self.records   = records
        self.tokenizer = tokenizer
        self.max_src   = max_src
        self.max_tgt   = max_tgt

    def __len__(self):
        return len(self.records)

    def __getitem__(self, idx):
        rec = self.records[idx]
        src = rec["input"]
        tgt = rec["output"]

        # Tokenise source
        self.tokenizer.src_lang = SRC_LANG
        model_inputs = self.tokenizer(
            src,
            max_length=self.max_src,
            truncation=True,
            padding=False,
        )

        # Tokenise target (use text_target= — as_target_tokenizer() removed in 4.47)
        labels = self.tokenizer(
            text_target=tgt,
            max_length=self.max_tgt,
            truncation=True,
            padding=False,
        )

        model_inputs["labels"] = labels["input_ids"]
        return model_inputs


def load_jsonl_files(data_dir: Path) -> list[dict]:
    """Load all .jsonl files from data_dir and return combined record list."""
    records = []
    for p in sorted(data_dir.glob("*.jsonl")):
        with open(p, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        records.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass
        print(f"  Loaded {p.name}")
    return records


def train_val_split(records: list[dict], val_ratio: float = 0.1, seed: int = 42):
    """Shuffle and split records into train/val sets."""
    random.seed(seed)
    shuffled = records.copy()
    random.shuffle(shuffled)
    n_val = max(1, int(len(shuffled) * val_ratio))
    return shuffled[n_val:], shuffled[:n_val]


# ──────────────────────────────────────────────────────────────────────────────
# NaN-safe trainer (MPS workaround)
# ──────────────────────────────────────────────────────────────────────────────

class NaNSafeTrainer(Seq2SeqTrainer):
    """
    Cleans NaN/Inf gradients once per backward pass instead of using per-parameter
    hooks (hooks fire on every tensor and are 10-20× slower on MPS).
    """

    def training_step(self, model, inputs, num_items_in_batch=None):
        loss = super().training_step(model, inputs, num_items_in_batch)
        with torch.no_grad():
            for param in model.parameters():
                if param.grad is not None:
                    param.grad.nan_to_num_(nan=0.0, posinf=0.0, neginf=0.0)
        return loss


# ──────────────────────────────────────────────────────────────────────────────
# Main training loop
# ──────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Fine-tune mBART for POSTNOW caption generation")
    parser.add_argument("--data_dir",    default="data/raw",  help="Directory with .jsonl training files")
    parser.add_argument("--output_dir",  default="model",     help="Where to save the fine-tuned model")
    parser.add_argument("--base_model",  default=BASE_MODEL,  help="HuggingFace model name or local path")
    parser.add_argument("--epochs",      type=int,   default=5)
    parser.add_argument("--batch_size",  type=int,   default=4,   help="Per-device train batch size")
    parser.add_argument("--grad_accum",  type=int,   default=4,   help="Gradient accumulation steps")
    parser.add_argument("--lr",          type=float, default=5e-5)
    parser.add_argument("--warmup_steps",type=int,   default=200)
    parser.add_argument("--max_steps",   type=int,   default=-1,  help="Override epochs with a fixed step count (for smoke tests)")
    parser.add_argument("--eval_steps",  type=int,   default=0,   help="Evaluate every N steps (0 = epoch-based)")
    parser.add_argument("--val_ratio",   type=float, default=0.10)
    parser.add_argument("--fp16",        action="store_true",     help="Enable FP16 mixed precision (GPU only)")
    parser.add_argument("--seed",        type=int,   default=42)
    args = parser.parse_args()

    data_dir   = Path(args.data_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # ── Load data ────────────────────────────────────────────────────────────
    print(f"\n📂  Loading training data from {data_dir} ...")
    all_records = load_jsonl_files(data_dir)
    if not all_records:
        print("❌  No .jsonl files found in data_dir. Run generate_data.py first.")
        return

    train_records, val_records = train_val_split(all_records, val_ratio=args.val_ratio, seed=args.seed)
    print(f"✅  {len(all_records)} total records → {len(train_records)} train / {len(val_records)} val")

    # ── Load tokenizer & model ───────────────────────────────────────────────
    print(f"\n🤖  Loading {args.base_model} ...")
    tokenizer = MBart50TokenizerFast.from_pretrained(args.base_model, src_lang=SRC_LANG, tgt_lang=TGT_LANG)
    model     = MBartForConditionalGeneration.from_pretrained(args.base_model)

    # Gradient checkpointing is disabled: it causes NaN gradients on MPS (Apple Silicon).
    # With MAX_TARGET_LEN=256 and batch_size=1 the 16 GB unified memory is sufficient.

    # ── Build datasets ───────────────────────────────────────────────────────
    train_dataset = CaptionDataset(train_records, tokenizer, MAX_SOURCE_LEN, MAX_TARGET_LEN)
    val_dataset   = CaptionDataset(val_records,   tokenizer, MAX_SOURCE_LEN, MAX_TARGET_LEN)

    data_collator = DataCollatorForSeq2Seq(
        tokenizer,
        model=model,
        label_pad_token_id=-100,
        pad_to_multiple_of=8 if args.fp16 else None,
    )

    # ── Training arguments ───────────────────────────────────────────────────
    training_args = Seq2SeqTrainingArguments(
        output_dir=str(output_dir),
        num_train_epochs=args.epochs,
        max_steps=args.max_steps,
        per_device_train_batch_size=args.batch_size,
        per_device_eval_batch_size=args.batch_size,
        gradient_accumulation_steps=args.grad_accum,
        learning_rate=args.lr,
        warmup_steps=args.warmup_steps,
        weight_decay=0.01,
        max_grad_norm=1.0,

        # Evaluation disabled during training: model.eval() causes NaN loss on
        # PyTorch MPS (Apple Silicon) due to attention mask handling differences.
        # Run evaluate.py manually after training to check BLEU scores.
        eval_strategy="no",
        save_strategy="steps",
        save_steps=500,
        save_total_limit=2,

        predict_with_generate=False,
        fp16=args.fp16,
        seed=args.seed,

        logging_dir=str(output_dir / "logs"),
        logging_steps=50,
        report_to="none",

        dataloader_num_workers=0,
    )

    trainer = NaNSafeTrainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=val_dataset,
        processing_class=tokenizer,
        data_collator=data_collator,
    )

    # ── Train ────────────────────────────────────────────────────────────────
    print(f"\n🚀  Starting training ({args.epochs} epochs, effective batch {args.batch_size * args.grad_accum}) ...")
    trainer.train()

    # ── Save final model ─────────────────────────────────────────────────────
    final_path = output_dir / "final"
    final_path.mkdir(exist_ok=True)
    trainer.save_model(str(final_path))
    tokenizer.save_pretrained(str(final_path))
    print(f"\n✅  Model saved to {final_path}")

    # ── Save training metadata ───────────────────────────────────────────────
    meta = {
        "base_model":    args.base_model,
        "train_records": len(train_records),
        "val_records":   len(val_records),
        "epochs":        args.epochs,
        "batch_size":    args.batch_size,
        "grad_accum":    args.grad_accum,
        "lr":            args.lr,
        "src_lang":      SRC_LANG,
        "tgt_lang":      TGT_LANG,
        "max_src_len":   MAX_SOURCE_LEN,
        "max_tgt_len":   MAX_TARGET_LEN,
    }
    with open(final_path / "training_meta.json", "w") as f:
        json.dump(meta, f, indent=2)
    print(f"📄  Training metadata saved to {final_path}/training_meta.json")


if __name__ == "__main__":
    main()
