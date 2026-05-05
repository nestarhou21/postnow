"""
agents/image_agent.py — Gemini promotional poster generator

2-step pipeline:
  1. Gemini text   → reads the promo + optional photo, invents a creative concept,
                     writes the full image generation prompt from scratch
  2. Gemini image  → generates the poster from that prompt
"""
import os
import base64
import json
import httpx

GEMINI_IMAGE_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "gemini-3.1-flash-image-preview:generateContent"
)
GEMINI_TEXT_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "gemini-2.0-flash:generateContent"
)

_MOCK_SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" width="1080" height="1080">'
    '<rect width="1080" height="1080" fill="#C8A27C"/>'
    '<rect x="60" y="60" width="960" height="960" fill="none" stroke="#5A3E2B" stroke-width="6"/>'
    '<text x="540" y="420" font-family="Georgia,serif" font-size="96" font-weight="bold" '
    'text-anchor="middle" fill="#5A3E2B">POSTNOW</text>'
    '<text x="540" y="530" font-family="Georgia,serif" font-size="48" '
    'text-anchor="middle" fill="#5A3E2B">Mock Poster Preview</text>'
    '<text x="540" y="620" font-family="sans-serif" font-size="30" '
    'text-anchor="middle" fill="#7A5E3E">Mock mode active</text>'
    '</svg>'
)
_MOCK_B64 = base64.b64encode(_MOCK_SVG.encode()).decode()


# ── Master prompt ─────────────────────────────────────────────────────────────

MASTER_SYSTEM = """
You are an expert AI image prompt engineer for Southeast Asian café advertising.
You write prompts that make Google Gemini produce results that look like
real paid campaigns for KOI, Tiger Sugar, and Gong Cha.

STEP 1 — DRINK DESCRIPTION:
If a photo is provided: describe it precisely — cup type, lid, straw color,
drink color and layers, toppings, ice level, condensation, any logo on the cup.
If no photo: invent a specific beautiful drink from the promo text keywords.

STEP 2 — PICK A VISUAL CONCEPT based on the promotion energy:
• EXPLOSION   → sale, discount, free, promo, celebrate (ingredients flying in vivid sky)
• SPOTLIGHT   → premium, exclusive, luxury, signature (dramatic dark studio light)
• MINIMAL     → new menu, launching, introducing (pure white studio, breathing room)
• FLAT LAY    → variety, combo, collection, menu (overhead pastel surface, props)
• LIFESTYLE   → weekend, chill, cozy, relax (golden hour outdoor, soft bokeh)
• MACRO       → fresh, quality, ingredients, detail (extreme close-up, condensation drops)
• RUSTIC      → artisan, handcrafted, heritage (warm wooden table, afternoon light)
• NIGHT       → late night, midnight, party, urban (dark background, glowing spotlight)

STEP 3 — WRITE THE IMAGE PROMPT (60–90 words, punchy and keyword-dense):

Follow this structure exactly:
1. Style anchor: "Award-winning [style] commercial photograph, [brand reference] advertisement style,"
2. Drink: exact description, 2–3 specific visual details
3. Scene: 2–3 specific scene details separated by commas
4. Lighting: one specific lighting description
5. Mood keywords: 3–5 comma-separated words
6. Technical: "Shot on Hasselblad H6D, 85mm f/1.8, ultra sharp, 4K, beverage commercial quality."
7. Text: "[shop_name] small elegant text top-right. [short punchy promo] bold bottom-center."

Rules:
- 60–90 words MAX. Short and punchy always beats long and detailed.
- Use real brand references: "KOI Café advertisement", "Tiger Sugar campaign poster", "Gong Cha promotional style"
- Use specific camera specs — they dramatically improve output quality
- Keep text instruction to ONE short sentence at the end
- If reference photo provided, START the prompt with: "Reproduce the EXACT drink from the reference photo — same cup, colors, branding —"

Return raw JSON only, no markdown:
{"drink_description": "...", "concept": "one line", "image_prompt": "60-90 word prompt"}
""".strip()


# ── Gemini text API ───────────────────────────────────────────────────────────

def _call_gemini_text(
    system: str,
    user_text: str,
    image_b64: str | None = None,
    image_mime: str = "image/jpeg",
) -> str:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY not set")

    parts: list = []
    if image_b64:
        parts.append({"inlineData": {"mimeType": image_mime, "data": image_b64}})
    parts.append({"text": user_text})

    payload = {
        "system_instruction": {"parts": [{"text": system}]},
        "contents": [{"parts": parts}],
        "generationConfig": {"responseMimeType": "application/json"},
    }

    url = f"{GEMINI_TEXT_URL}?key={api_key}"
    with httpx.Client(timeout=45.0) as client:
        response = client.post(url, json=payload)

    if response.status_code != 200:
        raise RuntimeError(f"Gemini text error {response.status_code}: {response.text}")

    return response.json()["candidates"][0]["content"]["parts"][0]["text"].strip()


# ── Step 1: Build the image prompt ───────────────────────────────────────────

def _build_image_prompt(
    promotion_prompt: str,
    shop_name: str,
    colors: list[str],
    reference_image_b64: str | None,
    reference_image_mime: str,
) -> tuple[str, str]:
    """
    Ask Gemini to invent a creative concept and write the full image prompt.
    Returns (image_prompt, concept).
    """
    color_str = ", ".join(colors) if colors else "#C8A27C, #5A3E2B"
    user_text = (
        f"Shop name: {shop_name}\n"
        f"Brand colors: {color_str}\n"
        f"Promotion: {promotion_prompt}"
    )

    try:
        raw    = _call_gemini_text(
            system=MASTER_SYSTEM,
            user_text=user_text,
            image_b64=reference_image_b64,
            image_mime=reference_image_mime,
        )
        result = json.loads(raw)
        prompt  = result.get("image_prompt", "")
        concept = result.get("concept", "")
        if prompt:
            print(f"[image_agent] Concept: {concept}")
            print(f"[image_agent] Prompt ({len(prompt)} chars): {prompt[:120]}...")
            return prompt, concept
    except Exception as e:
        print(f"[image_agent] Prompt builder error: {e} — using fallback prompt.")

    # Fallback: short punchy direct prompt
    prefix = "Reproduce the EXACT drink from the reference photo — same cup, colors, branding — " if reference_image_b64 else ""
    fallback = (
        f"{prefix}Award-winning beverage commercial photograph, KOI Café advertisement style, "
        f"iced coffee drink hero centered, vivid and appetising, floating ingredients and coffee beans, "
        f"bright vivid background, dramatic lighting, "
        f"commercial, vibrant, Southeast Asian café marketing. "
        f"Shot on Hasselblad H6D, 85mm f/1.8, ultra sharp, 4K, beverage commercial quality. "
        f"'{shop_name}' small white text top-right. '{promotion_prompt}' bold bottom-center."
    )
    return fallback, "fallback"


# ── Step 2: Gemini image generation ──────────────────────────────────────────

def _call_gemini_image(
    prompt: str,
    api_key: str,
    reference_image_b64: str | None = None,
    reference_image_mime: str = "image/jpeg",
) -> tuple[bytes, str]:
    parts = []
    if reference_image_b64:
        parts.append({
            "inlineData": {"mimeType": reference_image_mime, "data": reference_image_b64}
        })
    parts.append({"text": prompt})

    payload = {
        "contents": [{"parts": parts}],
        "generationConfig": {"responseModalities": ["IMAGE", "TEXT"]},
    }

    url = f"{GEMINI_IMAGE_URL}?key={api_key}"
    with httpx.Client(timeout=90.0) as client:
        response = client.post(url, json=payload)

    if response.status_code != 200:
        raise RuntimeError(f"Gemini image error {response.status_code}: {response.text}")

    data = response.json()
    try:
        for part in data["candidates"][0]["content"]["parts"]:
            if "inlineData" in part:
                mime = part["inlineData"].get("mimeType", "image/png")
                raw  = base64.b64decode(part["inlineData"]["data"])
                return raw, mime
    except (KeyError, IndexError) as e:
        raise RuntimeError(f"Could not parse Gemini response: {e}\nRaw: {data}")

    raise RuntimeError("No image returned from Gemini API")


# ── Public entry point ────────────────────────────────────────────────────────

def generate_poster(
    promotion_prompt: str,
    shop_name: str,
    aesthetic: str,
    colors: list[str],
    template_id: str = "centered",
    reference_image_base64: str | None = None,
    reference_image_mime: str = "image/jpeg",
) -> dict:
    """
    Generate a promotional poster.
    Returns: {"image_base64", "image_data_url", "prompt_used", "style_used"}
    """
    _ = aesthetic, template_id  # kept for caller compatibility

    if os.getenv("MOCK_IMAGE_GENERATION", "false").lower() == "true":
        return {
            "image_base64":   _MOCK_B64,
            "image_data_url": f"data:image/svg+xml;base64,{_MOCK_B64}",
            "prompt_used":    "(mock mode)",
            "style_used":     "mock",
        }

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not set. Add it to backend/.env.")

    # Step 1 — Gemini text: invent concept + write image prompt
    prompt, concept = _build_image_prompt(
        promotion_prompt, shop_name, colors,
        reference_image_base64, reference_image_mime,
    )

    # When a reference photo is provided, prepend a strong cup-consistency instruction
    if reference_image_base64 and not prompt.startswith("Reproduce"):
        prompt = (
            "Reproduce the EXACT drink from the reference photo — "
            "same cup shape, same colors, same branding on the cup — "
            + prompt
        )

    # Step 2 — Gemini image: generate the poster
    image_bytes, mime = _call_gemini_image(
        prompt, api_key, reference_image_base64, reference_image_mime,
    )

    b64 = base64.b64encode(image_bytes).decode()
    return {
        "image_base64":   b64,
        "image_data_url": f"data:{mime};base64,{b64}",
        "prompt_used":    prompt,
        "style_used":     concept,
    }
