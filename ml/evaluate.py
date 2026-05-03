"""
ml/evaluate.py
──────────────
Evaluates the fine-tuned mBART model on a held-out test set.

Metrics
-------
  • BLEU-4  (sacrebleu) for English caption
  • BLEU-4  (sacrebleu) for Khmer caption
  • BLEU-4  for hashtags
  • Section presence rate  (how often all 3 sections appear in output)
  • Avg. English caption length
  • Avg. Khmer caption length

Usage
-----
    python evaluate.py \
        --model_path model/final \
        --test_file  data/raw/batch1.jsonl \
        --n_samples  100 \
        --output_file results/eval_results.json

Requirements
------------
    pip install transformers sentencepiece torch sacrebleu tqdm
"""

import os
import re
import json
import argparse
import random
from pathlib import Path

import torch
import sacrebleu
from tqdm import tqdm
from transformers import MBartForConditionalGeneration, MBart50TokenizerFast


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

SRC_LANG = "en_XX"
TGT_LANG = "en_XX"
MAX_SOURCE_LEN = 128
MAX_TARGET_LEN = 512


def parse_sections(text: str) -> dict:
    """Extract [EN], [KH], [TAGS] sections."""
    en_m  = re.search(r"\[EN\]\s*(.*?)\s*(?=\[KH\]|\[TAGS\]|$)",  text, re.DOTALL)
    kh_m  = re.search(r"\[KH\]\s*(.*?)\s*(?=\[EN\]|\[TAGS\]|$)",  text, re.DOTALL)
    tag_m = re.search(r"\[TAGS\]\s*(.*?)$", text, re.DOTALL)
    return {
        "en":   en_m.group(1).strip()  if en_m  else "",
        "kh":   kh_m.group(1).strip()  if kh_m  else "",
        "tags": tag_m.group(1).strip() if tag_m else "",
    }


def compute_bleu(hypotheses: list[str], references: list[str]) -> float:
    """Corpus BLEU-4 using sacrebleu."""
    if not hypotheses:
        return 0.0
    result = sacrebleu.corpus_bleu(hypotheses, [references])
    return round(result.score, 2)


def load_jsonl(path: Path) -> list[dict]:
    records = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    return records


# ──────────────────────────────────────────────────────────────────────────────
# Evaluator
# ──────────────────────────────────────────────────────────────────────────────

class Evaluator:
    def __init__(self, model_path: str):
        model_path = Path(model_path)
        if not model_path.exists():
            raise FileNotFoundError(f"Model not found at {model_path}")

        device = "cuda" if torch.cuda.is_available() else "cpu"
        self.device = device

        print(f"Loading model from {model_path} on {device} ...")
        self.tokenizer = MBart50TokenizerFast.from_pretrained(
            str(model_path), src_lang=SRC_LANG, tgt_lang=TGT_LANG
        )
        self.model = MBartForConditionalGeneration.from_pretrained(str(model_path))
        self.model.eval().to(device)
        self._tgt_lang_id = self.tokenizer.lang_code_to_id[TGT_LANG]
        print("Model loaded.")

    def predict(self, input_text: str) -> str:
        self.tokenizer.src_lang = SRC_LANG
        inputs = self.tokenizer(
            input_text,
            return_tensors="pt",
            max_length=MAX_SOURCE_LEN,
            truncation=True,
        ).to(self.device)

        with torch.no_grad():
            out = self.model.generate(
                **inputs,
                forced_bos_token_id=self._tgt_lang_id,
                max_new_tokens=MAX_TARGET_LEN,
                num_beams=4,
                length_penalty=1.2,
                no_repeat_ngram_size=3,
                early_stopping=True,
            )
        return self.tokenizer.decode(out[0], skip_special_tokens=True)

    def evaluate(self, records: list[dict]) -> dict:
        en_hyps, en_refs   = [], []
        kh_hyps, kh_refs   = [], []
        tag_hyps, tag_refs = [], []
        complete_count     = 0
        en_lengths         = []
        kh_lengths         = []

        for rec in tqdm(records, desc="Evaluating"):
            pred_raw = self.predict(rec["input"])
            ref_raw  = rec["output"]

            pred = parse_sections(pred_raw)
            ref  = parse_sections(ref_raw)

            # Track section completeness
            if pred["en"] and pred["kh"] and pred["tags"]:
                complete_count += 1

            en_hyps.append(pred["en"])
            en_refs.append(ref["en"])
            kh_hyps.append(pred["kh"])
            kh_refs.append(ref["kh"])
            tag_hyps.append(pred["tags"])
            tag_refs.append(ref["tags"])

            if pred["en"]:
                en_lengths.append(len(pred["en"].split()))
            if pred["kh"]:
                kh_lengths.append(len(pred["kh"]))

        n = len(records)
        results = {
            "n_samples":          n,
            "bleu_en":            compute_bleu(en_hyps, en_refs),
            "bleu_kh":            compute_bleu(kh_hyps, kh_refs),
            "bleu_tags":          compute_bleu(tag_hyps, tag_refs),
            "section_complete_pct": round(complete_count / n * 100, 1) if n else 0,
            "avg_en_words":       round(sum(en_lengths) / len(en_lengths), 1) if en_lengths else 0,
            "avg_kh_chars":       round(sum(kh_lengths) / len(kh_lengths), 1) if kh_lengths else 0,
        }
        return results


# ──────────────────────────────────────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Evaluate POSTNOW mBART model")
    parser.add_argument("--model_path",  default="model/final",         help="Path to saved model directory")
    parser.add_argument("--test_file",   default="data/raw/batch1.jsonl",help="JSONL file to evaluate on")
    parser.add_argument("--n_samples",   type=int, default=100,          help="Number of samples to evaluate (0 = all)")
    parser.add_argument("--output_file", default=None,                   help="Optional: save results to JSON")
    parser.add_argument("--seed",        type=int, default=42)
    args = parser.parse_args()

    # Load test data
    test_file = Path(args.test_file)
    if not test_file.exists():
        print(f"❌  Test file not found: {test_file}")
        return

    records = load_jsonl(test_file)
    if not records:
        print("❌  No records found in test file.")
        return

    if args.n_samples > 0 and args.n_samples < len(records):
        random.seed(args.seed)
        records = random.sample(records, args.n_samples)

    print(f"📊  Evaluating on {len(records)} samples from {test_file.name}")

    # Run evaluation
    evaluator = Evaluator(args.model_path)
    results   = evaluator.evaluate(records)

    # Print summary
    print("\n─── Evaluation Results ─────────────────────────────────")
    print(f"  Samples evaluated     : {results['n_samples']}")
    print(f"  BLEU-4 (English)      : {results['bleu_en']}")
    print(f"  BLEU-4 (Khmer)        : {results['bleu_kh']}")
    print(f"  BLEU-4 (Hashtags)     : {results['bleu_tags']}")
    print(f"  Complete sections     : {results['section_complete_pct']}%")
    print(f"  Avg EN caption words  : {results['avg_en_words']}")
    print(f"  Avg KH caption chars  : {results['avg_kh_chars']}")
    print("────────────────────────────────────────────────────────\n")

    # Optionally save
    if args.output_file:
        out = Path(args.output_file)
        out.parent.mkdir(parents=True, exist_ok=True)
        with open(out, "w") as f:
            json.dump(results, f, indent=2)
        print(f"💾  Results saved to {out}")


if __name__ == "__main__":
    main()
