"""
ml/compare_models.py
────────────────────
3-model comparison for POSTNOW caption generation:

  Model 1 — mBART-large-50 fine-tuned   (your trained model)
  Model 2 — mBART-large-50 zero-shot    (no fine-tuning, proves fine-tuning helps)
  Model 3 — Claude API zero-shot        (state-of-the-art LLM baseline)

Usage:
    cd ml
    source venv/bin/activate
    python compare_models.py \
        --finetuned_path model/final \
        --test_file      data/raw/postnow_2500.jsonl \
        --n_samples      100 \
        --output_file    results/comparison.json

    # Skip a model (e.g. no Claude key):
    python compare_models.py --finetuned_path model/final --skip_claude

Requirements:
    pip install transformers sentencepiece sacrebleu torch tqdm anthropic
"""

import os
import re
import json
import time
import random
import argparse
from pathlib import Path

import torch
import sacrebleu
from tqdm import tqdm
from transformers import MBartForConditionalGeneration, MBart50TokenizerFast

# ── Constants (must match train.py / infer.py) ─────────────────────────────────

SRC_LANG       = "en_XX"
TGT_LANG       = "en_XX"
MAX_SOURCE_LEN = 128
MAX_TARGET_LEN = 512
BASE_MODEL     = "facebook/mbart-large-50"


# ── Shared helpers ─────────────────────────────────────────────────────────────

def parse_sections(text: str) -> dict:
    en_m  = re.search(r"\[EN\]\s*(.*?)\s*(?=\[KH\]|\[TAGS\]|$)",  text, re.DOTALL)
    kh_m  = re.search(r"\[KH\]\s*(.*?)\s*(?=\[EN\]|\[TAGS\]|$)",  text, re.DOTALL)
    tag_m = re.search(r"\[TAGS\]\s*(.*?)$", text, re.DOTALL)
    return {
        "en":   en_m.group(1).strip()  if en_m  else "",
        "kh":   kh_m.group(1).strip()  if kh_m  else "",
        "tags": tag_m.group(1).strip() if tag_m else "",
    }


def corpus_bleu(hyps: list[str], refs: list[str]) -> float:
    if not hyps or not any(hyps):
        return 0.0
    return round(sacrebleu.corpus_bleu(hyps, [refs]).score, 2)


def section_complete_pct(predictions: list[dict]) -> float:
    n = len(predictions)
    if n == 0:
        return 0.0
    complete = sum(1 for p in predictions if p["en"] and p["kh"] and p["tags"])
    return round(complete / n * 100, 1)


def compute_metrics(predictions: list[dict], references: list[dict]) -> dict:
    en_hyps  = [p["en"]   for p in predictions]
    en_refs  = [r["en"]   for r in references]
    kh_hyps  = [p["kh"]   for p in predictions]
    kh_refs  = [r["kh"]   for r in references]
    tag_hyps = [p["tags"] for p in predictions]
    tag_refs = [r["tags"] for r in references]

    en_lengths = [len(p["en"].split()) for p in predictions if p["en"]]
    kh_lengths = [len(p["kh"])         for p in predictions if p["kh"]]

    return {
        "bleu_en":              corpus_bleu(en_hyps,  en_refs),
        "bleu_kh":              corpus_bleu(kh_hyps,  kh_refs),
        "bleu_tags":            corpus_bleu(tag_hyps, tag_refs),
        "section_complete_pct": section_complete_pct(predictions),
        "avg_en_words":         round(sum(en_lengths) / len(en_lengths), 1) if en_lengths else 0,
        "avg_kh_chars":         round(sum(kh_lengths) / len(kh_lengths), 1) if kh_lengths else 0,
    }


def load_jsonl(path: Path, n: int, seed: int) -> list[dict]:
    records = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    if n > 0 and n < len(records):
        random.seed(seed)
        records = random.sample(records, n)
    return records


# ── Model 1 & 2 — mBART (fine-tuned OR zero-shot) ─────────────────────────────

class MBartPredictor:
    def __init__(self, model_path: str, label: str):
        device = "mps" if torch.backends.mps.is_available() else \
                 "cuda" if torch.cuda.is_available() else "cpu"
        self.device = device
        self.label  = label
        print(f"\n[{label}] Loading from {model_path} on {device} ...")
        self.tokenizer = MBart50TokenizerFast.from_pretrained(
            model_path, src_lang=SRC_LANG, tgt_lang=TGT_LANG
        )
        self.model = MBartForConditionalGeneration.from_pretrained(model_path)
        self.model.eval().to(device)
        self._tgt_id = self.tokenizer.lang_code_to_id[TGT_LANG]
        print(f"[{label}] Ready.")

    def predict(self, input_text: str) -> str:
        self.tokenizer.src_lang = SRC_LANG
        inputs = self.tokenizer(
            input_text, return_tensors="pt",
            max_length=MAX_SOURCE_LEN, truncation=True,
        ).to(self.device)
        with torch.no_grad():
            out = self.model.generate(
                **inputs,
                forced_bos_token_id=self._tgt_id,
                max_new_tokens=MAX_TARGET_LEN,
                num_beams=4,
                length_penalty=1.2,
                no_repeat_ngram_size=3,
                early_stopping=True,
            )
        return self.tokenizer.decode(out[0], skip_special_tokens=True)

    def run(self, records: list[dict]) -> tuple[list[dict], float]:
        preds = []
        t0 = time.time()
        for rec in tqdm(records, desc=self.label):
            raw  = self.predict(rec["input"])
            preds.append(parse_sections(raw))
        elapsed = time.time() - t0
        return preds, elapsed


# ── Model 3 — Claude API zero-shot ────────────────────────────────────────────

CLAUDE_SYSTEM = """You generate bilingual marketing captions for Cambodian coffee shops.

Given: ShopName | Aesthetic | Colors | Promotion

Output EXACTLY this format (no extra text):
[EN]
<English caption, 2-4 sentences, marketing tone>

[KH]
<Khmer caption, same message>

[TAGS]
#Tag1 #Tag2 #Tag3 #Tag4 #Tag5"""


class ClaudePredictor:
    def __init__(self):
        import anthropic
        self.client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.label  = "Claude claude-sonnet-4-6 zero-shot"
        print(f"\n[{self.label}] Ready.")

    def predict(self, input_text: str) -> str:
        msg = self.client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=512,
            system=CLAUDE_SYSTEM,
            messages=[{"role": "user", "content": input_text}],
        )
        return msg.content[0].text

    def run(self, records: list[dict]) -> tuple[list[dict], float]:
        preds = []
        t0 = time.time()
        for rec in tqdm(records, desc=self.label):
            try:
                raw = self.predict(rec["input"])
                preds.append(parse_sections(raw))
            except Exception as e:
                print(f"  Claude error: {e}")
                preds.append({"en": "", "kh": "", "tags": ""})
            time.sleep(0.3)  # rate limit buffer
        elapsed = time.time() - t0
        return preds, elapsed


# ── Reporting ──────────────────────────────────────────────────────────────────

def print_table(results: dict):
    cols = ["bleu_en", "bleu_kh", "bleu_tags", "section_complete_pct", "avg_en_words", "avg_kh_chars", "inference_sec"]
    headers = ["Model", "BLEU-EN", "BLEU-KH", "BLEU-Tags", "Complete%", "EN words", "KH chars", "Time(s)"]

    col_w = 14
    print("\n" + "─" * (20 + col_w * len(cols)))
    print(f"{'Model':<20}" + "".join(f"{h:>{col_w}}" for h in headers[1:]))
    print("─" * (20 + col_w * len(cols)))
    for name, metrics in results.items():
        row = f"{name:<20}"
        for c in cols:
            val = metrics.get(c, "—")
            row += f"{val:>{col_w}}"
        print(row)
    print("─" * (20 + col_w * len(cols)))


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Compare 3 POSTNOW caption models")
    parser.add_argument("--finetuned_path", default="model/final",          help="Path to fine-tuned mBART model")
    parser.add_argument("--test_file",      default="data/raw/postnow_2500.jsonl", help="JSONL test data")
    parser.add_argument("--n_samples",      type=int, default=100,           help="Samples to evaluate (0=all)")
    parser.add_argument("--output_file",    default="results/comparison.json")
    parser.add_argument("--seed",           type=int, default=42)
    parser.add_argument("--skip_finetuned", action="store_true")
    parser.add_argument("--skip_zeroshot",  action="store_true")
    parser.add_argument("--skip_claude",    action="store_true")
    args = parser.parse_args()

    print(f"Loading {args.n_samples or 'all'} test samples from {args.test_file} ...")
    records = load_jsonl(Path(args.test_file), args.n_samples, args.seed)
    refs    = [parse_sections(r["output"]) for r in records]
    print(f"  {len(records)} records loaded")

    all_results = {}

    # ── Model 1: fine-tuned mBART ──────────────────────────────────────────────
    if not args.skip_finetuned:
        m1 = MBartPredictor(args.finetuned_path, "mBART fine-tuned")
        preds, elapsed = m1.run(records)
        metrics = compute_metrics(preds, refs)
        metrics["inference_sec"] = round(elapsed, 1)
        metrics["n_samples"]     = len(records)
        all_results["mBART fine-tuned"] = metrics
        del m1  # free memory before loading next model

    # ── Model 2: zero-shot mBART (base weights, no fine-tuning) ───────────────
    if not args.skip_zeroshot:
        m2 = MBartPredictor(BASE_MODEL, "mBART zero-shot")
        preds, elapsed = m2.run(records)
        metrics = compute_metrics(preds, refs)
        metrics["inference_sec"] = round(elapsed, 1)
        metrics["n_samples"]     = len(records)
        all_results["mBART zero-shot"] = metrics
        del m2

    # ── Model 3: Claude API zero-shot ─────────────────────────────────────────
    if not args.skip_claude:
        if not os.getenv("ANTHROPIC_API_KEY"):
            print("\n[Claude] ANTHROPIC_API_KEY not set — skipping. Use --skip_claude to suppress this warning.")
        else:
            m3 = ClaudePredictor()
            preds, elapsed = m3.run(records)
            metrics = compute_metrics(preds, refs)
            metrics["inference_sec"] = round(elapsed, 1)
            metrics["n_samples"]     = len(records)
            all_results["Claude zero-shot"] = metrics

    # ── Print table ────────────────────────────────────────────────────────────
    print_table(all_results)

    # ── Save ───────────────────────────────────────────────────────────────────
    out = Path(args.output_file)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w") as f:
        json.dump({"n_samples": len(records), "results": all_results}, f, indent=2)
    print(f"\nResults saved to {out}")


if __name__ == "__main__":
    main()
