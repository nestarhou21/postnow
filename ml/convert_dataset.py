"""
ml/convert_dataset.py
─────────────────────
Converts data_gemini/postnow_training_data_2500.json
     → data/raw/postnow_2500.jsonl

Each JSONL line: {"input": "ShopName | Aesthetic | Colors | Prompt", "output": "[EN]...[KH]...[TAGS]..."}

Run:
    cd ml
    python convert_dataset.py
"""

import json
import random
from pathlib import Path

INPUT_FILE  = Path("data_gemini/postnow_training_data_2500.json")
OUTPUT_FILE = Path("data/raw/postnow_2500.jsonl")
SEED = 42

# ── Shop variety (model must generalise across different shops) ────────────────

SHOP_NAMES = [
    "Slow Drip Café",     "Phnom Penh Brew",    "Khmer Coffee House",
    "Morning Sip",        "Aroma Café",          "Riverside Roasters",
    "Bean & Beyond",      "Café Angkor",         "Golden Cup",
    "Brew Society",       "The Daily Grind",     "Sip & Stay",
    "Cloud Nine Café",    "Heritage Brew",       "The Coffee Loft",
    "Mekong Roasters",    "Café Kampot",         "Lotus Brew",
    "Bayon Coffee",       "Silk Road Café",
]

COLOR_PALETTES = {
    "Cozy": [
        "#C8A27C,#5A3E2B,#FFF8F0",
        "#D4A96A,#6B3D2E,#F5E6D3",
        "#C9956C,#4A3728,#FFF3E8",
        "#BF8A5E,#3D2B1A,#FAF0E6",
    ],
    "Bold": [
        "#FF6B35,#1A1A2E,#E8C547",
        "#E63946,#1D3557,#F4D35E",
        "#F72585,#3A0CA3,#4CC9F0",
        "#FF4500,#2D2D2D,#FFD700",
    ],
    "Minimalist": [
        "#F5F5F5,#3A3A3A,#C8A27C",
        "#FAFAFA,#2D2D2D,#A8A8A8",
        "#F8F8F8,#404040,#D4C4B0",
        "#FFFFFF,#1A1A1A,#E0D5C5",
    ],
}

MOOD_KEYWORDS = {
    "Cozy":       ["warm", "cozy", "soft", "gentle", "inviting", "nostalgic",
                   "sincere", "homey", "comfort", "intimate", "laid-back"],
    "Bold":       ["vibrant", "energetic", "playful", "exciting", "bold",
                   "dynamic", "fun", "upbeat", "expressive", "driven"],
    "Minimalist": ["clean", "minimal", "calm", "professional", "elegant",
                   "refined", "sleek", "modern", "quiet", "simple"],
}


def infer_aesthetic(mood: str) -> str:
    if mood:
        mood_lower = mood.lower()
        for aesthetic, keywords in MOOD_KEYWORDS.items():
            if any(k in mood_lower for k in keywords):
                return aesthetic
    return random.choice(["Cozy", "Bold", "Minimalist"])


PROMPT_TEMPLATES = {
    "product_launch": [
        "Introducing our new {product}",
        "New arrival: {product} is here!",
        "Try our brand-new {product} today",
        "Meet our newest menu item: {product}",
    ],
    "daily_moment": [
        "Start your {occasion} with great coffee",
        "Your daily {occasion} deserves the best cup",
        "Perfect {product} for your {occasion}",
        "Fuel your {occasion} with {product}",
    ],
    "engagement": [
        "Join us for {occasion}",
        "Come celebrate {occasion} with us",
        "Share your {occasion} at our café",
        "We love seeing you on {occasion}",
    ],
    "brand_story": [
        "Our story: {occasion}",
        "Why we care about {occasion}",
        "What makes us different: {occasion}",
        "The heart of our café: {occasion}",
    ],
    "promotion": [
        "Special {occasion} deal on {product}",
        "Limited time: {product} promotion",
        "Don't miss our {product} offer this {occasion}",
    ],
}


def build_prompt(record: dict) -> str:
    meta     = record["metadata"]
    category = record["category"]

    if meta.get("promotion"):
        return meta["promotion"]

    occasion = (meta.get("occasion") or "").strip()
    product  = (meta.get("product")  or "").strip()

    templates = PROMPT_TEMPLATES.get(category, ["{occasion} — {product}"])
    tpl = random.choice(templates)
    return tpl.format(occasion=occasion or "special moment", product=product or "our signature coffee")


def build_output(record: dict) -> str:
    en = record["caption"]["en"].strip()
    km = record["caption"]["km"].strip()

    en_tags  = record["hashtags"].get("en", [])
    km_tags  = record["hashtags"].get("km", [])
    all_tags = " ".join(en_tags + km_tags)

    return f"[EN]\n{en}\n\n[KH]\n{km}\n\n[TAGS]\n{all_tags}"


def main():
    random.seed(SEED)

    print(f"Reading {INPUT_FILE} ...")
    with open(INPUT_FILE, encoding="utf-8") as f:
        data = json.load(f)

    captions = data["captions"]
    print(f"  {len(captions)} records loaded")

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    written = skipped = 0
    category_counts: dict[str, int] = {}

    with open(OUTPUT_FILE, "w", encoding="utf-8") as out:
        for record in captions:
            en = record["caption"].get("en", "").strip()
            km = record["caption"].get("km", "").strip()
            if not en or not km:
                skipped += 1
                continue

            shop      = random.choice(SHOP_NAMES)
            mood      = record["metadata"].get("mood", "")
            aesthetic = infer_aesthetic(mood)
            colors    = random.choice(COLOR_PALETTES[aesthetic])

            prompt      = build_prompt(record)
            input_text  = f"{shop} | {aesthetic} | {colors} | {prompt}"
            output_text = build_output(record)

            out.write(json.dumps({"input": input_text, "output": output_text}, ensure_ascii=False) + "\n")
            written += 1
            category_counts[record["category"]] = category_counts.get(record["category"], 0) + 1

    print(f"\n  Written : {written}")
    print(f"  Skipped : {skipped}")
    print(f"\n  Category breakdown:")
    for cat, count in sorted(category_counts.items()):
        print(f"    {cat:<20} {count}")

    print(f"\n  Output  : {OUTPUT_FILE}")

    print("\nSample record (first line):")
    with open(OUTPUT_FILE, encoding="utf-8") as f:
        sample = json.loads(f.readline())
    print(f"  INPUT : {sample['input']}")
    out_preview = sample["output"].replace("\n", " | ")
    print(f"  OUTPUT: {out_preview[:130]}...")

    print("\nReady to train.")


if __name__ == "__main__":
    main()
