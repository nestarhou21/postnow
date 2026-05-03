"""
Quick test for image_agent.py — runs from the backend/ directory.

Usage:
    cd backend
    python test_image.py

Saves the generated poster to test_output.png and opens it.
"""
import os
import sys
import base64

# Load .env manually (no need for python-dotenv)
env_path = os.path.join(os.path.dirname(__file__), ".env")
if os.path.exists(env_path):
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, val = line.partition("=")
                os.environ.setdefault(key.strip(), val.strip())

from agents.image_agent import generate_poster, TEMPLATE_STYLES, AESTHETIC_MOODS

# ── Test parameters — change these to try different combos ───────────────────

SHOP_NAME  = "Slow Drip Café"
AESTHETIC  = "Cozy"                      # Cozy | Bold | Minimalist
COLORS     = ["#C8A27C", "#5A3E2B"]
PROMOTION  = "Buy 1 Get 1 Latte this weekend"
TEMPLATE   = "centered"                  # centered | text_banner | lifestyle | minimal
OUTPUT     = "test_output.png"

# ─────────────────────────────────────────────────────────────────────────────

def main():
    print(f"Generating poster...")
    print(f"  Shop      : {SHOP_NAME}")
    print(f"  Aesthetic : {AESTHETIC}")
    print(f"  Colors    : {COLORS}")
    print(f"  Promotion : {PROMOTION}")
    print(f"  Template  : {TEMPLATE}")
    print()

    try:
        result = generate_poster(PROMOTION, SHOP_NAME, AESTHETIC, COLORS, TEMPLATE)
    except Exception as e:
        print(f"❌ Failed: {e}")
        sys.exit(1)

    # Save to file
    img_bytes = base64.b64decode(result["image_base64"])
    with open(OUTPUT, "wb") as f:
        f.write(img_bytes)

    size_kb = len(img_bytes) / 1024
    print(f"✅ Poster saved → {OUTPUT}  ({size_kb:.0f} KB)")
    print()
    print("── Prompt used ──────────────────────────────────────────")
    print(result["prompt_used"])

    # Open the image (macOS)
    os.system(f"open {OUTPUT}")


if __name__ == "__main__":
    main()
