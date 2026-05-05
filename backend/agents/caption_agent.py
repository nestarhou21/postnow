"""
agents/caption_agent.py — Bilingual caption generator

Priority:
  1. Local model (mBART or Gemma) — loaded by generate.py at startup
  2. Gemini API fallback (gemini-2.0-flash) — uses existing GEMINI_API_KEY
  3. Simple template — last resort, no API needed
"""
import os
import re
import json
import httpx

GEMINI_TEXT_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "gemini-2.0-flash:generateContent"
)

_CAPTION_SYSTEM = """You are a bilingual social media manager for Cambodian coffee shops.
Write promotional content for Facebook and Instagram that feels authentic and on-brand.

Rules:
1. English caption — max 120 words, conversational, ends with a call-to-action.
2. Khmer caption — culturally adapted for Cambodian audience (NOT word-for-word translation). Natural, friendly tone. Use mixed Khmer-English for drink names (Latte, Cold Brew, etc.).
3. Exactly 5 hashtags — mix English and Khmer, relevant to the promotion.
4. No emojis unless aesthetic is Bold.
5. Do NOT invent prices unless the prompt mentions them.

Return raw JSON only, no markdown:
{"en_caption": "...", "kh_caption": "...", "hashtags": "#tag1 #tag2 #tag3 #tag4 #tag5"}"""


def generate_gemini_caption(
    promotion_prompt: str,
    shop_name: str,
    aesthetic: str,
    colors: list[str],
) -> dict:
    """Generate caption using Gemini text API."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY not set")

    user_text = (
        f"Shop: {shop_name}\n"
        f"Aesthetic: {aesthetic}\n"
        f"Colors: {', '.join(colors)}\n"
        f"Promotion: {promotion_prompt}\n\n"
        f"Write a promotional social media caption."
    )

    payload = {
        "system_instruction": {"parts": [{"text": _CAPTION_SYSTEM}]},
        "contents": [{"parts": [{"text": user_text}]}],
        "generationConfig": {"responseMimeType": "application/json"},
    }

    url = f"{GEMINI_TEXT_URL}?key={api_key}"
    with httpx.Client(timeout=30.0) as client:
        response = client.post(url, json=payload)

    if response.status_code != 200:
        raise RuntimeError(f"Gemini caption error {response.status_code}: {response.text}")

    raw = response.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
    result = json.loads(raw)
    return {
        "en_caption": result.get("en_caption", ""),
        "kh_caption": result.get("kh_caption", ""),
        "hashtags":   result.get("hashtags", ""),
    }


def _simple_caption(promotion_prompt: str, shop_name: str, aesthetic: str) -> dict:
    """Last-resort template fallback — tries Gemini first, then uses template."""
    try:
        return generate_gemini_caption(promotion_prompt, shop_name, aesthetic, ["#C8A27C", "#5A3E2B"])
    except Exception:
        pass

    emoji = "✨" if aesthetic == "Bold" else ""
    en = (
        f"{emoji} {promotion_prompt} at {shop_name}! "
        f"Come visit us and enjoy this special offer. "
        f"Tag a friend you'd love to share this with. "
        f"See you soon! {emoji}"
    ).strip()
    kh = (
        f"មកទទួលបានការផ្តល់ជូនពិសេសនៅ {shop_name}! "
        f"{promotion_prompt} — កុំខកខានឱកាសនេះ។ "
        f"អញ្ជើញមិត្តភ័ក្តិរបស់អ្នកមកផងដែរ!"
    )
    tags = f"#{shop_name.replace(' ','')} #PhnomPenhCafe #កាហ្វេភ្នំពេញ #CambodianCoffee #SpecialOffer"
    return {"en_caption": en, "kh_caption": kh, "hashtags": tags}


def generate_caption(
    promotion_prompt: str,
    shop_name: str,
    aesthetic: str,
    colors: list[str],
) -> dict:
    """Claude API caption generator (requires ANTHROPIC_API_KEY)."""
    import anthropic

    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    system = (
        f"You are a social media manager for {shop_name}, a {aesthetic} coffee shop in Phnom Penh, Cambodia. "
        f"Write promotional content that feels authentic and on-brand. Brand colors: {', '.join(colors)}.\n\n"
        "Return EXACTLY this format:\n[EN]\n<english caption>\n\n[KH]\n<khmer caption>\n\n[TAGS]\n<5 hashtags>"
    )
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        system=system,
        messages=[{"role": "user", "content": f"Write a promotional post for: {promotion_prompt}"}],
    )
    raw = response.content[0].text
    en_match  = re.search(r"\[EN\]\s*(.*?)\s*(?=\[KH\]|\[TAGS\]|$)", raw, re.DOTALL)
    kh_match  = re.search(r"\[KH\]\s*(.*?)\s*(?=\[EN\]|\[TAGS\]|$)", raw, re.DOTALL)
    tag_match = re.search(r"\[TAGS\]\s*(.*?)$", raw, re.DOTALL)
    return {
        "en_caption": en_match.group(1).strip()  if en_match  else "",
        "kh_caption": kh_match.group(1).strip()  if kh_match  else "",
        "hashtags":   tag_match.group(1).strip() if tag_match else "",
    }
