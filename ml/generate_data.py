"""
ml/generate_data.py
───────────────────
Generates synthetic bilingual (EN + KH) coffee-shop marketing training data
using the Claude API, for fine-tuning mBART-large-50.

Each record follows the POSTNOW two-layer caption format:

    Input : "{shop_name} | {aesthetic} | {colors} | {promotion_prompt}"
    Output: "[EN]\n{english_caption}\n\n[KH]\n{khmer_caption}\n\n[TAGS]\n{hashtags}"

Usage
-----
    # Generate 500 examples → data/raw/batch1.jsonl
    python generate_data.py --count 500 --output data/raw/batch1.jsonl

    # Append another 300 for a second batch
    python generate_data.py --count 300 --output data/raw/batch2.jsonl

Requirements
------------
    pip install anthropic tqdm
    export ANTHROPIC_API_KEY=...
"""

import os
import sys
import json
import random
import argparse
import time
from pathlib import Path
import anthropic
from tqdm import tqdm

# ──────────────────────────────────────────────────────────────────────────────
# Seed data: shop names, aesthetics, palettes, promotion templates
# ──────────────────────────────────────────────────────────────────────────────

SHOP_NAMES = [
    "Slow Drip Café", "Bean & Bloom", "The Roast House", "Phnompenh Brew",
    "Sunrise Sip", "Golden Cup Café", "River Bend Coffee", "Mekong Roasters",
    "Bayon Brew", "Lotus Coffee House", "The Daily Grind PH", "Khmer Kafe",
    "Bamboo & Beans", "Siem Reap Sips", "Cloud Nine Coffee", "Brown Sugar Café",
    "Drip Society", "The Coffee Monk", "Angkor Espresso", "Cozy Corner Café",
    "Midnight Brew", "The Winding Cup", "Pepper & Bean", "Basil Coffee Co.",
    "Humble Sip", "The Quarter Cup", "Sakura Coffee", "Tangerine Roasters",
    "Urban Grind PH", "Latte Love Café",
]

AESTHETICS = ["Cozy", "Bold", "Minimalist"]

COLOR_PALETTES = [
    ["#C8A27C", "#5A3E2B", "#FFF8F0"],
    ["#E83F6F", "#2274A5", "#FFFFFF"],
    ["#F5F5F5", "#1A1A1A", "#C8A97E"],
    ["#7FA39C", "#2C4B44", "#F0F5F4"],
    ["#D4A017", "#6B3A2A", "#FEF9EC"],
    ["#3D5A80", "#98C1D9", "#E0EBF5"],
    ["#6B4226", "#D2955A", "#FFF4E6"],
    ["#1B4332", "#52B788", "#D8F3DC"],
    ["#E07A5F", "#3D405B", "#F4F1DE"],
    ["#C77DFF", "#7B2D8B", "#EDE7F6"],
    ["#FF6B6B", "#4ECDC4", "#F7FFF7"],
    ["#264653", "#2A9D8F", "#E9C46A"],
    ["#8B5E3C", "#F0C27F", "#FFF8EE"],
    ["#4A4E69", "#9A8C98", "#F2E9E4"],
    ["#B5838D", "#E5989B", "#FFB4A2"],
]

PROMOTIONS = [
    "Buy 1 Get 1 Free on all lattes this weekend",
    "50% off every Iced Americano on Mondays",
    "Free slice of cake with any large coffee",
    "New seasonal menu: Pandan Latte and Taro Frappé",
    "Morning special: Espresso + croissant for $3 before 9am",
    "Loyalty card: collect 10 stamps, get 1 free drink",
    "Happy hour 3–5pm: 30% off all cold drinks",
    "Grand reopening this Saturday — free tastings all day",
    "New Khmer-style iced coffee now available",
    "Student discount: 15% off with valid student ID",
    "Valentine's Day special: couples buy 2 drinks, get a free dessert",
    "Weekend brunch combo: coffee + eggs + toast for $5",
    "Introducing our single-origin Kampot beans",
    "Flash sale: 40% off all frappes today only",
    "Free upgrade to large size every Friday",
    "New Nitro Cold Brew just landed — try it free with any purchase",
    "Anniversary offer: 2nd year — 2nd drink at half price",
    "Signature drink launch: The Mekong Sunset cocktail coffee",
    "Monthly subscription box: get 250g of our beans delivered",
    "Kids' special: free hot chocolate for children under 12",
    "Back-to-school: extra shot free in September",
    "New: Matcha Latte and Brown Sugar Milk Tea added to menu",
    "Win a month of free coffee — follow us and tag a friend",
    "Takeaway Tuesday: 20% off all to-go orders",
    "New single-origin Ethiopia Yirgacheffe — limited stock",
    "Late night special: open till midnight on weekends",
    "Rainy day deal: free hot drink upgrade when it rains",
    "Referral reward: bring a new customer, both get 25% off",
    "Try our new oat milk range — plant-based alternatives now available",
    "Weekly special: Signature latte + free Wi-Fi upgrade",
    "Seasonal special: Pumpkin Spice Latte is back",
    "Premium beans from Ratanakiri — taste the highlands",
    "Weekend special: bottomless drip coffee $4",
    "Pre-order your Christmas gift sets — coffee hampers available",
    "Reusable cup discount: bring your own, save $0.50",
    "New collab with a local bakery — exclusive pastries now in store",
    "Birthday month offer: free drink on your birthday",
    "Staff picks: our top 3 seasonal recommendations this week",
    "Community table: free co-working space with any purchase",
    "Same-day delivery available now in Phnom Penh",
]

SYSTEM_PROMPT = """You are a bilingual social media copywriter for Cambodian coffee shops.

Given a shop name, aesthetic style, brand colors, and a promotion, write promotional content.

Rules:
1. [EN] caption: max 140 words, conversational, ends with a CTA. No emojis unless aesthetic is "Bold".
2. [KH] caption: culturally adapted Khmer (NOT word-for-word translation). Natural, warm tone using everyday Khmer expressions. No emojis unless aesthetic is "Bold".
3. [TAGS]: exactly 5 hashtags on ONE line, mixing English and Khmer (use # prefix).
4. Return ONLY this format — no extra text:

[EN]
<english caption>

[KH]
<khmer caption>

[TAGS]
<5 hashtags>"""


def make_user_message(shop_name: str, aesthetic: str, colors: list, promotion: str) -> str:
    color_str = ", ".join(colors)
    return (
        f"Shop: {shop_name}\n"
        f"Aesthetic: {aesthetic}\n"
        f"Brand colors: {color_str}\n"
        f"Promotion: {promotion}"
    )


def make_input_key(shop_name: str, aesthetic: str, colors: list, promotion: str) -> str:
    color_str = ",".join(colors)
    return f"{shop_name} | {aesthetic} | {color_str} | {promotion}"


def parse_response(raw: str) -> dict | None:
    """Parse [EN] / [KH] / [TAGS] sections from Claude response."""
    import re
    en_match  = re.search(r"\[EN\]\s*(.*?)\s*(?=\[KH\]|\[TAGS\]|$)", raw, re.DOTALL)
    kh_match  = re.search(r"\[KH\]\s*(.*?)\s*(?=\[EN\]|\[TAGS\]|$)", raw, re.DOTALL)
    tag_match = re.search(r"\[TAGS\]\s*(.*?)$", raw, re.DOTALL)

    if not (en_match and kh_match and tag_match):
        return None

    en  = en_match.group(1).strip()
    kh  = kh_match.group(1).strip()
    tags = tag_match.group(1).strip()

    # Validate: must have content in all three sections
    if len(en) < 20 or len(kh) < 10 or len(tags) < 5:
        return None

    return {"en": en, "kh": kh, "tags": tags}


def generate_single(
    client: anthropic.Anthropic,
    shop_name: str,
    aesthetic: str,
    colors: list,
    promotion: str,
    retries: int = 3,
) -> dict | None:
    """Call Claude and return a parsed training record, or None on failure."""
    user_msg = make_user_message(shop_name, aesthetic, colors, promotion)
    input_key = make_input_key(shop_name, aesthetic, colors, promotion)

    for attempt in range(retries):
        try:
            response = client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=1024,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": user_msg}],
            )
            raw = response.content[0].text
            parsed = parse_response(raw)
            if not parsed:
                continue

            output = (
                f"[EN]\n{parsed['en']}\n\n"
                f"[KH]\n{parsed['kh']}\n\n"
                f"[TAGS]\n{parsed['tags']}"
            )
            return {"input": input_key, "output": output}

        except anthropic.RateLimitError:
            wait = 2 ** (attempt + 1)
            time.sleep(wait)
        except Exception as e:
            print(f"\n  ⚠  Error on attempt {attempt+1}: {e}", file=sys.stderr)
            time.sleep(1)

    return None


def sample_record() -> tuple[str, str, list, str]:
    """Return a random (shop_name, aesthetic, colors, promotion) combo."""
    return (
        random.choice(SHOP_NAMES),
        random.choice(AESTHETICS),
        random.choice(COLOR_PALETTES),
        random.choice(PROMOTIONS),
    )


def main():
    parser = argparse.ArgumentParser(
        description="Generate synthetic bilingual coffee-shop marketing data for mBART training"
    )
    parser.add_argument("--count",  type=int, default=500,
                        help="Number of training examples to generate (default: 500)")
    parser.add_argument("--output", type=str, default="data/raw/batch1.jsonl",
                        help="Output JSONL file path (default: data/raw/batch1.jsonl)")
    parser.add_argument("--delay",  type=float, default=0.5,
                        help="Seconds to wait between API calls (default: 0.5)")
    args = parser.parse_args()

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("❌  ANTHROPIC_API_KEY not set. Export it before running.", file=sys.stderr)
        sys.exit(1)

    client = anthropic.Anthropic(api_key=api_key)

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # Resume: count already-written lines
    existing = 0
    if out_path.exists():
        with open(out_path) as f:
            existing = sum(1 for _ in f)
        print(f"ℹ  Resuming — {existing} records already in {out_path}")

    remaining = max(0, args.count - existing)
    if remaining == 0:
        print(f"✅  Already have {existing} records. Nothing to generate.")
        return

    print(f"🚀  Generating {remaining} records → {out_path}")
    success = 0
    failed  = 0

    with open(out_path, "a", encoding="utf-8") as fout:
        with tqdm(total=remaining, unit="rec") as bar:
            while success < remaining:
                shop, aesthetic, colors, promo = sample_record()
                record = generate_single(client, shop, aesthetic, colors, promo)

                if record:
                    fout.write(json.dumps(record, ensure_ascii=False) + "\n")
                    fout.flush()
                    success += 1
                    bar.update(1)
                    bar.set_postfix(ok=success, fail=failed)
                else:
                    failed += 1
                    bar.set_postfix(ok=success, fail=failed)

                time.sleep(args.delay)

    total = existing + success
    print(f"\n✅  Done. {success} new records written ({failed} failed). Total in file: {total}")


if __name__ == "__main__":
    main()
