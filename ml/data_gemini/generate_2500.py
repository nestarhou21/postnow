"""
ml/data_gemini/generate_2500.py
────────────────────────────────
Generates 2,500 bilingual (EN + Khmer) coffee-shop marketing captions
for POSTNOW mBART fine-tuning using the Claude API.

Distribution:
  product_launch : 600  (24%)
  daily_moment   : 700  (28%)
  promotion      : 500  (20%)
  engagement     : 400  (16%)
  brand_story    : 300  (12%)

Usage:
  export ANTHROPIC_API_KEY=...
  python generate_2500.py

The script saves incrementally to postnow_training_data_2500.json so it
can be safely interrupted and resumed.
"""

import os
import sys
import json
import random
import time
import re
from pathlib import Path
import anthropic

# ──────────────────────────────────────────────────────────────────────────────
# Target distribution
# ──────────────────────────────────────────────────────────────────────────────

TARGET = {
    "product_launch": 600,
    "daily_moment":   700,
    "promotion":      500,
    "engagement":     400,
    "brand_story":    300,
}
TOTAL = 2500
OUTPUT_FILE = Path(__file__).parent / "postnow_training_data_2500.json"
BATCH_SIZE = 10   # captions per API call

# ──────────────────────────────────────────────────────────────────────────────
# Seed variety pools
# ──────────────────────────────────────────────────────────────────────────────

PRODUCTS_COFFEE = [
    "Iced Latte", "Iced Americano", "Iced Cappuccino", "Espresso", "Americano",
    "Cappuccino", "Flat White", "Cortado", "Macchiato", "Affogato",
    "Cold Brew", "Nitro Cold Brew", "Dirty Coffee", "Vietnamese Coffee",
    "Caramel Latte", "Vanilla Latte", "Hazelnut Latte", "Mocha",
    "Caramel Macchiato", "Rose Latte", "Honey Lavender Latte",
    "Coconut Cold Brew", "Brown Sugar Latte", "Taro Latte",
    "Matcha Latte", "Pandan Latte", "Butterfly Pea Latte",
    "Mango Frappe", "Strawberry Frappe", "Chocolate Frappe",
    "Pumpkin Spice Latte", "Peppermint Mocha", "Thai Tea Latte",
    "Uji Matcha Latte", "Avocado Coffee", "Dalgona Coffee",
    "Salted Caramel Cold Brew", "Passion Fruit Cold Brew",
    "Kampot Pepper Cold Brew", "Single-Origin Mondulkiri Espresso",
]

PRODUCTS_NONCOFFEE = [
    "Hot Chocolate", "Chai Latte", "Strawberry Smoothie",
    "Mango Smoothie", "Avocado Smoothie", "Fresh Lemonade",
    "Iced Tea", "Hibiscus Iced Tea", "Fruit Tea",
    "Croissant", "Banana Bread", "Avocado Toast", "Cheese Cake",
    "Chocolate Lava Cake", "Almond Croissant",
]

PRODUCTS_SEASONAL = [
    "Khmer New Year Special Latte", "Water Festival Cold Brew",
    "Pchum Ben Special", "Christmas Peppermint Mocha",
    "Valentine's Rose Latte", "Chinese New Year Taro Latte",
    "Rainy Season Brown Sugar Latte", "Summer Coconut Frappe",
    "Mid-Year Mango Cold Brew",
]

ALL_PRODUCTS = PRODUCTS_COFFEE + PRODUCTS_NONCOFFEE + PRODUCTS_SEASONAL

LOCATIONS = [
    "BKK1", "Toul Tom Poung", "Russian Market", "Riverside",
    "Santhormok", "Daun Penh", "Sen Sok", "Toul Kork",
    "Siem Reap", "all branches", "our shop",
]

OCCASIONS = {
    "product_launch": [
        "new menu launch", "seasonal launch", "limited edition drop",
        "summer launch", "Khmer New Year launch", "anniversary special",
        "collab launch", "weekend exclusive", "holiday edition",
        "premium range debut", "new branch opening", "rebranding launch",
    ],
    "daily_moment": [
        "Monday morning", "early morning fuel", "afternoon slump",
        "work from cafe", "study session", "weekend brunch",
        "rainy day comfort", "Friday feeling", "late night study",
        "morning ritual", "post-gym refuel", "Sunday slow morning",
        "meeting fuel", "afternoon break", "evening unwind",
    ],
    "promotion": [
        "happy hour", "flash sale", "student discount day",
        "birthday promo", "loyalty reward", "Khmer New Year deal",
        "Water Festival special", "weekday offer", "app-exclusive deal",
        "BOGO weekend", "early bird offer", "reusable cup discount",
        "referral reward", "members only", "clearance promo",
    ],
    "engagement": [
        "weekend poll", "taste test vote", "tag a friend challenge",
        "community question", "this or that", "user-generated content",
        "giveaway announcement", "caption contest", "monthly favorite vote",
        "coffee personality quiz", "feedback request", "staff pick reveal",
    ],
    "brand_story": [
        "farm-to-cup story", "Cambodian coffee heritage", "ethical sourcing",
        "brewing method spotlight", "local farmer partnership",
        "sustainability commitment", "team behind the cup",
        "origin story", "roasting process", "community roots",
        "Mondulkiri highlands journey", "women farmers feature",
    ],
}

MOODS = {
    "product_launch": [
        "exciting, exclusive", "fresh, innovative", "premium, indulgent",
        "tropical, refreshing", "cozy, warm", "bold, vibrant",
        "limited, exclusive", "seasonal, festive",
    ],
    "daily_moment": [
        "energizing, motivational", "comforting, cozy", "relaxing, calm",
        "productive, focused", "cheerful, uplifting", "nostalgic, warm",
        "refreshing, revitalizing",
    ],
    "promotion": [
        "urgent, exciting", "value-focused, cheerful", "limited-time, urgent",
        "festive, generous", "playful, energetic",
    ],
    "engagement": [
        "playful, interactive", "fun, community-focused",
        "curious, conversational", "lighthearted, relatable",
    ],
    "brand_story": [
        "authentic, inspiring", "educational, heartfelt",
        "values-driven, sincere", "local, proud", "sustainable, hopeful",
    ],
}

PROMOTIONS_MAP = {
    "product_launch": ["new menu item", "limited edition", "seasonal special"],
    "daily_moment":   [None, None, "loyalty points", None],
    "promotion": [
        "20% off", "Buy 1 Get 1 Free", "flash sale 30% off",
        "student discount 15%", "birthday free drink",
        "happy hour 2-for-1", "free size upgrade", "app discount 25%",
        "loyalty reward free drink", "referral discount",
    ],
    "engagement":   [None],
    "brand_story":  [None],
}

AUDIENCES = [
    "young professionals, 18-35",
    "students, 18-25",
    "coffee enthusiasts",
    "families",
    "remote workers",
    "expats and tourists",
    "locals, all ages",
    "working adults, 25-40",
]

CULTURAL_HOOKS = [
    "Khmer New Year (មហាសង្រ្កាន្ត)",
    "Pchum Ben (បុណ្យភ្ជុំបិណ្ឌ)",
    "Water Festival (បុណ្យអុំទូក)",
    "King's Birthday",
    "Cambodian Independence Day",
    "Chinese New Year",
    "rainy season",
    "dry season heat",
    "Phnom Penh café culture",
    "Cambodian coffee heritage",
]

# ──────────────────────────────────────────────────────────────────────────────
# Prompt builder
# ──────────────────────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are an expert bilingual social media copywriter for Cambodian coffee shops.
Write captions that sound like real Cambodian coffee shop Instagram posts — natural, engaging, and culturally authentic.

RULES:
1. English captions: conversational, engaging, 2-5 sentences, strong hook, clear CTA, emojis appropriate to mood
2. Khmer captions: MUST be natural marketing language — how real Cambodian coffee shops write on social media
   - Use English coffee terms naturally (Latte, Cold Brew, Espresso, Frappuccino, etc.)
   - Mixed Khmer-English is CORRECT and authentic (e.g., "Iced Latte ត្រជាក់ ផ្អែម ឈ្ងុយ!")
   - DO NOT do word-for-word translation — adapt culturally
   - Keep the same energy and emojis as English version
3. Hashtags: 3-5 English tags, 2-4 Khmer tags, relevant and specific
4. Return ONLY valid JSON array — no explanation, no markdown fences

GOOD KHMER EXAMPLE: "ក្តៅៗ ហើយ? 🥵 Coconut Cold Brew ត្រជាក់ ផ្អែម ល្អឥតខ្ចោះ! 🥥☕ មាននៅគ្រប់សាខា!"
BAD KHMER EXAMPLE: "យើងសូមណែនាំភេសជ្ជៈថ្មីមួយ" (too formal, no coffee term, robotic)"""


def build_batch_prompt(category: str, items: list[dict]) -> str:
    specs = json.dumps(items, ensure_ascii=False, indent=2)
    return f"""Generate {len(items)} coffee shop social media captions for the category: {category.upper()}

For each item in this spec list, generate one caption entry following the EXACT JSON structure shown.
Vary the writing style, length (some short 1-2 sentences, some medium 3-4 sentences), hooks, and CTAs.

SPEC LIST:
{specs}

Return a JSON array of {len(items)} objects. Each object MUST have this exact structure:
{{
  "id": <same id from spec>,
  "category": "{category}",
  "metadata": {{
    "product": "<product name>",
    "promotion": <string or null>,
    "mood": "<1-3 adjectives>",
    "occasion": "<specific occasion>",
    "target_audience": "<audience>"
  }},
  "caption": {{
    "en": "<english caption with \\n for line breaks>",
    "km": "<khmer caption with \\n for line breaks>"
  }},
  "hashtags": {{
    "en": ["#tag1", "#tag2", "#tag3"],
    "km": ["#ខ្មែរ១", "#ខ្មែរ២", "#ខ្មែរ៣"]
  }}
}}"""


def make_spec(idx: int, category: str) -> dict:
    """Create a randomized spec for one caption."""
    all_prods = ALL_PRODUCTS.copy()
    if category == "product_launch":
        all_prods = PRODUCTS_COFFEE + PRODUCTS_SEASONAL
    elif category == "brand_story":
        all_prods = ["Kampot Beans", "Mondulkiri Single-Origin", "Local Robusta",
                     "Arabica Blend", "Cold Brew", "Espresso", "Pour Over"]

    product = random.choice(all_prods)
    occasion = random.choice(OCCASIONS[category])
    mood = random.choice(MOODS[category])
    promotion_pool = PROMOTIONS_MAP[category]
    promotion = random.choice(promotion_pool)
    audience = random.choice(AUDIENCES)

    # Occasionally inject a cultural hook into the occasion
    if random.random() < 0.18:
        occasion = random.choice(CULTURAL_HOOKS)

    # Occasionally add a location note
    location_note = ""
    if random.random() < 0.35:
        location_note = f" at {random.choice(LOCATIONS)}"

    spec = {
        "id": idx,
        "product": product,
        "promotion": promotion,
        "mood": mood,
        "occasion": occasion + location_note,
        "target_audience": audience,
    }
    return spec


# ──────────────────────────────────────────────────────────────────────────────
# Generation engine
# ──────────────────────────────────────────────────────────────────────────────

def generate_batch(
    client: anthropic.Anthropic,
    category: str,
    specs: list[dict],
    retries: int = 3,
) -> list[dict] | None:
    prompt = build_batch_prompt(category, specs)
    for attempt in range(retries):
        try:
            response = client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=4096,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}],
            )
            raw = response.content[0].text.strip()

            # Strip markdown code fences if present
            raw = re.sub(r"^```(?:json)?\s*", "", raw)
            raw = re.sub(r"\s*```$", "", raw)

            parsed = json.loads(raw)
            if not isinstance(parsed, list):
                continue

            # Basic validation
            valid = []
            for item in parsed:
                if (
                    isinstance(item, dict)
                    and "caption" in item
                    and "en" in item["caption"]
                    and "km" in item["caption"]
                    and len(item["caption"]["en"]) > 20
                    and len(item["caption"]["km"]) > 10
                    and "hashtags" in item
                ):
                    valid.append(item)

            if len(valid) >= max(1, len(specs) // 2):
                return valid

        except anthropic.RateLimitError:
            wait = 2 ** (attempt + 2)
            print(f"  Rate limited — waiting {wait}s…", flush=True)
            time.sleep(wait)
        except json.JSONDecodeError as e:
            print(f"  JSON parse error (attempt {attempt+1}): {e}", flush=True)
            time.sleep(2)
        except Exception as e:
            print(f"  Error (attempt {attempt+1}): {e}", flush=True)
            time.sleep(2)
    return None


# ──────────────────────────────────────────────────────────────────────────────
# Load / save helpers
# ──────────────────────────────────────────────────────────────────────────────

def load_existing() -> tuple[list[dict], dict[str, int]]:
    """Return (existing_captions, counts_per_category)."""
    counts = {cat: 0 for cat in TARGET}
    if not OUTPUT_FILE.exists():
        return [], counts
    try:
        with open(OUTPUT_FILE, encoding="utf-8") as f:
            data = json.load(f)
        captions = data.get("captions", [])
        for c in captions:
            cat = c.get("category", "")
            if cat in counts:
                counts[cat] += 1
        return captions, counts
    except Exception:
        return [], counts


def save_all(captions: list[dict]) -> None:
    counts = {cat: 0 for cat in TARGET}
    for c in captions:
        cat = c.get("category", "")
        if cat in counts:
            counts[cat] += 1

    data = {
        "dataset_info": {
            "total_captions": len(captions),
            "language_pair": "en-km",
            "created_for": "POSTNOW mBART fine-tuning",
            "categories": counts,
        },
        "captions": captions,
    }
    # Write atomically via temp file
    tmp = OUTPUT_FILE.with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    tmp.replace(OUTPUT_FILE)


# ──────────────────────────────────────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────────────────────────────────────

def main():
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY not set.", file=sys.stderr)
        sys.exit(1)

    client = anthropic.Anthropic(api_key=api_key)

    captions, counts = load_existing()
    next_id = max((c.get("id", 0) for c in captions), default=0) + 1

    print("=" * 60)
    print("POSTNOW — 2500 Caption Dataset Generator")
    print("=" * 60)
    print(f"Already generated: {len(captions)}")
    for cat, target in TARGET.items():
        done = counts[cat]
        print(f"  {cat:<20} {done:>4} / {target}")
    print()

    total_done = len(captions)
    total_failed = 0

    # Build work queue: list of (category, batch_size) to generate
    work_queue = []
    for cat, target in TARGET.items():
        remaining = target - counts[cat]
        while remaining > 0:
            batch = min(BATCH_SIZE, remaining)
            work_queue.append((cat, batch))
            remaining -= batch

    if not work_queue:
        print("✅  Dataset already complete!")
        return

    total_batches = len(work_queue)
    batch_num = 0

    for category, batch_size in work_queue:
        batch_num += 1
        specs = [make_spec(next_id + i, category) for i in range(batch_size)]
        ids_in_batch = [s["id"] for s in specs]

        print(
            f"[{batch_num:>3}/{total_batches}] {category:<20} "
            f"ids {ids_in_batch[0]}-{ids_in_batch[-1]}  "
            f"({total_done}/{TOTAL} done)",
            end="  ",
            flush=True,
        )

        result = generate_batch(client, category, specs)

        if result:
            # Ensure category field is set, fix IDs to be sequential
            for i, item in enumerate(result):
                item["category"] = category
                item["id"] = ids_in_batch[i] if i < len(ids_in_batch) else next_id + i

            captions.extend(result)
            next_id += len(result)
            total_done += len(result)
            counts[category] += len(result)

            # Save after every batch
            save_all(captions)
            print(f"✓  +{len(result)}", flush=True)
        else:
            total_failed += batch_size
            print("✗  FAILED — skipped", flush=True)

        # Polite delay
        time.sleep(0.4)

    print()
    print("=" * 60)
    print(f"DONE. Total captions saved: {len(captions)}")
    print(f"Failed: {total_failed}")
    for cat, target in TARGET.items():
        print(f"  {cat:<20} {counts[cat]:>4} / {target}")
    print(f"\nSaved to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
