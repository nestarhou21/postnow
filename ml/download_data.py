"""
ml/download_data.py
───────────────────
Downloads publicly available English–Khmer parallel corpora from HuggingFace
and converts them to POSTNOW JSONL format for supplementary mBART training.

These datasets provide real Khmer text so the model generates authentic
language — beyond what the synthetic coffee-shop data alone can teach.

Datasets (all confirmed available on HuggingFace)
─────────────────────────────────────────────────
1. ParaCrawl v2           KrorngAI/ParaCrawl-English-Khmer-v2   1.5M pairs  CC0
2. SeyhaLite All-Domains  SeyhaLite/Translate-English-Khmer-All  366K pairs  Apache 2.0
3. SeyhaLite Travel       SeyhaLite/Translate-Khmer-English-Travel-and-Tourism  89K  Apache 2.0
4. NLLB-Seed              allenai/nllb (khm_Khmr-eng_Latn)      ~6K pairs   ODC-BY
5. OPUS-100               Helsinki-NLP/opus-100 (en-km)          varies      permissive
6. FLORES-200             facebook/flores (eng_Latn-khm_Khmr)   ~2K pairs   CC-BY-SA 4.0

Recommended combination for POSTNOW:
  ParaCrawl + SeyhaLite-All + SeyhaLite-Travel  →  ~2M pairs, general + domain

Usage
─────
    pip install datasets
    python download_data.py --output data/raw/parallel_en_kh.jsonl --limit 5000
    python download_data.py --sources paracrawl seyhalite --limit 10000 --output data/raw/kh_large.jsonl

Output format (JSONL)
─────────────────────
Each record teaches Khmer generation in isolation:

    {"input": "en: {english_sentence}", "output": "[KH]\\n{khmer_sentence}"}

This is kept separate from the coffee-shop synthetic data. The train.py
script combines both when loading data/raw/*.jsonl.
"""

import json
import argparse
from pathlib import Path

try:
    from datasets import load_dataset
except ImportError:
    print("❌  'datasets' library not installed. Run: pip install datasets")
    raise


# ──────────────────────────────────────────────────────────────────────────────
# Dataset loaders
# ──────────────────────────────────────────────────────────────────────────────

def _make_record(en: str, km: str, source: str) -> dict | None:
    """Validate and format a single translation pair."""
    en = en.strip()
    km = km.strip()
    if not en or not km or len(en) < 8 or len(km) < 4:
        return None
    return {"input": f"en: {en}", "output": f"[KH]\n{km}", "_source": source}


def load_paracrawl(limit: int) -> list[dict]:
    """
    ParaCrawl English-Khmer v2
    HF: KrorngAI/ParaCrawl-English-Khmer-v2
    1.5M pairs — CC0 (no restrictions)
    Fields: english, khmer
    BEST source: largest, cleanest, free to use.
    """
    print("📥  Loading ParaCrawl EN-KH v2 (1.5M pairs, CC0) ...")
    try:
        ds = load_dataset("KrorngAI/ParaCrawl-English-Khmer-v2", split="train", trust_remote_code=True)
        records = []
        for i, ex in enumerate(ds):
            if limit and i >= limit:
                break
            r = _make_record(ex.get("english", ""), ex.get("khmer", ""), "paracrawl-v2")
            if r:
                records.append(r)
        print(f"  ✅  {len(records)} pairs from ParaCrawl v2")
        return records
    except Exception as e:
        print(f"  ⚠  ParaCrawl failed: {e}")
        return []


def load_seyhalite_all(limit: int) -> list[dict]:
    """
    SeyhaLite Translate-English-Khmer-All
    HF: SeyhaLite/Translate-English-Khmer-All
    366K pairs — Apache 2.0
    Multi-domain: business, technology, medical, legal, daily conversation.
    Fields: eng, kh
    """
    print("📥  Loading SeyhaLite All-Domains EN-KH (366K, Apache 2.0) ...")
    try:
        ds = load_dataset("SeyhaLite/Translate-English-Khmer-All", split="train", trust_remote_code=True)
        records = []
        for i, ex in enumerate(ds):
            if limit and i >= limit:
                break
            r = _make_record(ex.get("eng", ""), ex.get("kh", ""), "seyhalite-all")
            if r:
                records.append(r)
        print(f"  ✅  {len(records)} pairs from SeyhaLite All-Domains")
        return records
    except Exception as e:
        print(f"  ⚠  SeyhaLite All failed: {e}")
        return []


def load_seyhalite_travel(limit: int) -> list[dict]:
    """
    SeyhaLite Translate-Khmer-English-Travel-and-Tourism
    HF: SeyhaLite/Translate-Khmer-English-Travel-and-Tourism
    89K pairs — Apache 2.0
    Tourism/hospitality domain — closest to coffee-shop/service context.
    Fields: eng, kh
    """
    print("📥  Loading SeyhaLite Travel & Tourism EN-KH (89K, Apache 2.0) ...")
    try:
        ds = load_dataset(
            "SeyhaLite/Translate-Khmer-English-Travel-and-Tourism",
            split="train",
            trust_remote_code=True,
        )
        records = []
        for i, ex in enumerate(ds):
            if limit and i >= limit:
                break
            r = _make_record(ex.get("eng", ""), ex.get("kh", ""), "seyhalite-travel")
            if r:
                records.append(r)
        print(f"  ✅  {len(records)} pairs from SeyhaLite Travel")
        return records
    except Exception as e:
        print(f"  ⚠  SeyhaLite Travel failed: {e}")
        return []


def load_nllb(limit: int) -> list[dict]:
    """
    NLLB-Seed (Meta AI No Language Left Behind)
    HF: allenai/nllb  config: khm_Khmr-eng_Latn
    ~6K quality-scored professional translations — ODC-BY
    Fields: translation (dict with eng_Latn, khm_Khmr), laser_score
    """
    print("📥  Loading NLLB-Seed EN-KH (~6K, ODC-BY) ...")
    try:
        ds = load_dataset("allenai/nllb", "khm_Khmr-eng_Latn", split="train", trust_remote_code=True)
        records = []
        for i, ex in enumerate(ds):
            if limit and i >= limit:
                break
            tr = ex.get("translation", {})
            r = _make_record(tr.get("eng_Latn", ""), tr.get("khm_Khmr", ""), "nllb-seed")
            if r:
                records.append(r)
        print(f"  ✅  {len(records)} pairs from NLLB-Seed")
        return records
    except Exception as e:
        print(f"  ⚠  NLLB-Seed failed: {e}")
        return []


def load_opus100(limit: int) -> list[dict]:
    """
    OPUS-100 en-km
    HF: Helsinki-NLP/opus-100  config: en-km
    Aggregated from OpenSubtitles, Bible, news, web — permissive
    Fields: translation (dict with en, km)
    """
    print("📥  Loading OPUS-100 EN-KH (permissive) ...")
    try:
        ds = load_dataset("Helsinki-NLP/opus-100", "en-km", split="train", trust_remote_code=True)
        records = []
        for i, ex in enumerate(ds):
            if limit and i >= limit:
                break
            tr = ex.get("translation", {})
            r = _make_record(tr.get("en", ""), tr.get("km", ""), "opus-100")
            if r:
                records.append(r)
        print(f"  ✅  {len(records)} pairs from OPUS-100")
        return records
    except Exception as e:
        print(f"  ⚠  OPUS-100 failed: {e}")
        return []


def load_flores200(limit: int) -> list[dict]:
    """
    FLORES-200 benchmark (Meta AI)
    HF: facebook/flores  config: eng_Latn-khm_Khmr
    ~2K high-quality human-translated sentences — CC-BY-SA 4.0
    Primarily used for evaluation, but small enough to include in training too.
    Fields: sentence_eng_Latn, sentence_khm_Khmr
    """
    print("📥  Loading FLORES-200 EN-KH (~2K, CC-BY-SA 4.0) ...")
    try:
        records = []
        for split in ("dev", "devtest"):
            try:
                ds = load_dataset(
                    "facebook/flores", "eng_Latn-khm_Khmr",
                    split=split, trust_remote_code=True,
                )
                for i, ex in enumerate(ds):
                    if limit and len(records) >= limit:
                        break
                    r = _make_record(
                        ex.get("sentence_eng_Latn", ""),
                        ex.get("sentence_khm_Khmr", ""),
                        "flores-200",
                    )
                    if r:
                        records.append(r)
            except Exception:
                pass
        print(f"  ✅  {len(records)} pairs from FLORES-200")
        return records
    except Exception as e:
        print(f"  ⚠  FLORES-200 failed: {e}")
        return []


# ──────────────────────────────────────────────────────────────────────────────
# Source registry
# ──────────────────────────────────────────────────────────────────────────────

SOURCES = {
    "paracrawl":  load_paracrawl,
    "seyhalite":  load_seyhalite_all,
    "travel":     load_seyhalite_travel,
    "nllb":       load_nllb,
    "opus100":    load_opus100,
    "flores200":  load_flores200,
}

# Recommended default: fastest, highest quality, closest to coffee-shop domain
DEFAULT_SOURCES = ["seyhalite", "travel", "nllb", "flores200"]


# ──────────────────────────────────────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Download EN-KH parallel data for mBART training",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Sources available:
  paracrawl   1.5M pairs  CC0        KrorngAI/ParaCrawl-English-Khmer-v2  (LARGEST)
  seyhalite   366K pairs  Apache 2.0 SeyhaLite/Translate-English-Khmer-All
  travel       89K pairs  Apache 2.0 SeyhaLite/Translate-Khmer-English-Travel-and-Tourism
  nllb          ~6K pairs ODC-BY     allenai/nllb (khm_Khmr-eng_Latn)
  opus100     varies      permissive Helsinki-NLP/opus-100 (en-km)
  flores200    ~2K pairs  CC-BY-SA   facebook/flores (eng_Latn-khm_Khmr)  (evaluation)

Examples:
  # Recommended quick start (~5K records from clean domain-relevant sources)
  python download_data.py --limit 5000

  # Large-scale: download ParaCrawl + SeyhaLite (for Google Colab)
  python download_data.py --sources paracrawl seyhalite --limit 50000 --output data/raw/kh_large.jsonl
        """,
    )
    parser.add_argument(
        "--output", default="data/raw/parallel_en_kh.jsonl",
        help="Output JSONL file path",
    )
    parser.add_argument(
        "--limit", type=int, default=5000,
        help="Max records per source (0 = all). Default: 5000",
    )
    parser.add_argument(
        "--sources", nargs="+",
        choices=list(SOURCES.keys()),
        default=DEFAULT_SOURCES,
        help=f"Sources to download. Default: {DEFAULT_SOURCES}",
    )
    args = parser.parse_args()

    per_source = args.limit if args.limit > 0 else 999_999

    print(f"\n🌐  Downloading EN-KH parallel data ({per_source} per source) ...")
    print(f"    Sources: {', '.join(args.sources)}\n")

    all_records = []
    for src_name in args.sources:
        loader = SOURCES[src_name]
        all_records += loader(per_source)

    if not all_records:
        print("\n❌  No records downloaded. Check your internet connection.")
        return

    # Strip internal _source key before saving
    clean = [{k: v for k, v in r.items() if k != "_source"} for r in all_records]

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)

    with open(out, "w", encoding="utf-8") as f:
        for rec in clean:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    print(f"\n✅  Saved {len(clean):,} records → {out}")

    # Source breakdown
    from collections import Counter
    counts = Counter(r["_source"] for r in all_records)
    print("\nBreakdown by source:")
    for src, n in counts.most_common():
        print(f"  {src:35s}  {n:7,}")


if __name__ == "__main__":
    main()
