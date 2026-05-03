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
You are a world-class commercial poster designer and creative director
specialized in Southeast Asian café advertising (Cambodia, Vietnam, Thailand).
You have designed viral café posters for KOI, Tiger Sugar, and Gong Cha.

Your job: given a café promotion and optional drink photo, write a stunning
image generation prompt that produces a professional advertisement poster.

STEP 1 — DESCRIBE THE DRINK:
If a photo is provided, describe the drink in precise detail:
cup material, size, lid style, straw, drink color and layers, toppings,
ice, condensation, any branding/logo on the cup.
If no photo, invent a beautiful specific drink that fits the promo keywords.

STEP 2 — INVENT A CREATIVE CONCEPT:
Choose any visual direction that best fits the promotion's mood and energy.
Examples (don't limit yourself to these):
  • Floating in vivid blue sky with flying ingredients
  • Single dramatic spotlight on dark background
  • Ultra-clean white minimal luxury
  • Overhead flat lay on pastel surface
  • Golden hour outdoor picnic lifestyle
  • Extreme close-up macro condensation
  • Rustic wooden table artisan scene
  • Neon night dramatic glow
  • Colorful gradient explosion
  • Split-layout bold typography
  • Underwater or fantasy dreamscape
  • Illustrated mixed-media collage
Be bold. Match the concept to the energy of the promotion.

STEP 3 — WRITE THE IMAGE PROMPT (150–250 words):
A complete, vivid, specific image generation prompt that:
  - Describes the scene, composition, camera angle, lighting, mood in detail
  - Names the drink precisely using the description from Step 1
  - Specifies where the shop name and promo text appear on the poster
  - Produces a commercially polished result, not a generic AI image
  - Ends with: "Photorealistic, ultra high quality, 1080x1080px square Instagram poster."

Return raw JSON only — no markdown, no backticks:
{"drink_description": "...", "concept": "one short line", "image_prompt": "full prompt here"}
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

    # Fallback: simple direct prompt
    fallback = (
        f"Professional Southeast Asian café advertisement poster for '{shop_name}'. "
        f"A beautifully presented iced coffee drink as the hero, centered and vibrant. "
        f"Promotion text '{promotion_prompt}' displayed prominently on the poster. "
        f"Shop name '{shop_name}' in the corner. "
        f"Commercial quality, eye-catching, Instagram-ready. "
        f"Photorealistic, ultra high quality, 1080x1080px square Instagram poster."
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
