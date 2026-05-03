"""
agents/image_agent.py — Gemini promotional poster generator

3-step pipeline:
  1. Gemini Analyzer  → picks best visual style + describes the drink in detail
  2. Python builder   → injects drink + shop + promo into a tight style-specific prompt
  3. Gemini image     → generates the poster
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

# Mock poster returned when MOCK_IMAGE_GENERATION=true
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


# ── Analyzer system prompt ────────────────────────────────────────────────────

ANALYZER_SYSTEM = """
You are an expert coffee shop creative director based in Southeast Asia.

If a drink photo is provided, describe it in precise photographic detail:
cup type (plastic/ceramic/glass), cup size, lid style, straw color,
drink color and opacity (be specific: "dusty lavender-purple" not "purple"),
visible layers and their colors, toppings (pearls, jelly, foam, cream, powder),
ice, condensation, any logo or branding printed on the cup.

If no photo, write a vivid photogenic drink description from the promo text keywords.

Then pick the most suitable visual style from these 8 options:
- sky_float       → sale, discount, off, promo, free, buy one, grand opening, celebrate
- dark_moody      → premium, special, exclusive, luxury, high-end, craft, signature
- clean_minimal   → new menu, new arrival, launching, introducing, now available
- flat_lay        → collection, variety, menu, selection, combo, all drinks
- outdoor_lifestyle → weekend, chill, relax, cozy, picnic, afternoon, sunny
- close_up_macro  → detail, texture, quality, craftsmanship, fresh, ingredients
- rustic_vintage  → artisan, handcrafted, single origin, pour over, brewing, heritage
- neon_night      → late night, after dark, night, midnight, party, urban, nightlife

Return raw JSON only, no markdown:
{"drink_description": "...", "style": "...", "reason": "..."}
""".strip()


# ── Step 1: Gemini text API helper ────────────────────────────────────────────

def _call_gemini_text(
    system: str,
    user_text: str,
    image_b64: str | None = None,
    image_mime: str = "image/jpeg",
    json_mode: bool = False,
) -> str:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY not set")

    parts: list = []
    if image_b64:
        parts.append({"inlineData": {"mimeType": image_mime, "data": image_b64}})
    parts.append({"text": user_text})

    payload: dict = {
        "system_instruction": {"parts": [{"text": system}]},
        "contents": [{"parts": parts}],
    }
    if json_mode:
        payload["generationConfig"] = {"responseMimeType": "application/json"}

    url = f"{GEMINI_TEXT_URL}?key={api_key}"
    with httpx.Client(timeout=45.0) as client:
        response = client.post(url, json=payload)

    if response.status_code != 200:
        raise RuntimeError(f"Gemini text error {response.status_code}: {response.text}")

    return response.json()["candidates"][0]["content"]["parts"][0]["text"].strip()


# ── Step 2: Analyzer ──────────────────────────────────────────────────────────

def _analyze(
    promotion_prompt: str,
    reference_image_b64: str | None,
    reference_image_mime: str,
) -> dict:
    try:
        raw    = _call_gemini_text(
            system=ANALYZER_SYSTEM,
            user_text=f"Promo text: {promotion_prompt}",
            image_b64=reference_image_b64,
            image_mime=reference_image_mime,
            json_mode=True,
        )
        result = json.loads(raw)
        print(f"[image_agent] style={result.get('style')} | {result.get('reason', '')}")
        return result
    except Exception as e:
        print(f"[image_agent] Analyzer error: {e} — using defaults.")
        return {
            "drink_description": (
                "a clear plastic cup with dome lid and wide black straw, "
                "filled with a layered iced coffee drink, caramel-brown color, "
                "lots of ice, condensation on the outside"
            ),
            "style": "sky_float",
            "reason": "Default fallback.",
        }


# ── Step 3: Style prompt builders ─────────────────────────────────────────────

def _build_prompt(
    style: str,
    drink: str,
    shop: str,
    promo: str,
    colors: list[str],
) -> str:
    _ = colors  # reserved for future per-style color theming
    fns = {
        "sky_float":         _sky_float,
        "dark_moody":        _dark_moody,
        "clean_minimal":     _clean_minimal,
        "flat_lay":          _flat_lay,
        "outdoor_lifestyle": _outdoor_lifestyle,
        "close_up_macro":    _close_up_macro,
        "rustic_vintage":    _rustic_vintage,
        "neon_night":        _neon_night,
    }
    fn = fns.get(style, _sky_float)
    return fn(drink, shop, promo)


def _sky_float(drink: str, shop: str, promo: str) -> str:
    return (
        f"Professional Southeast Asian café advertisement poster, 1080x1080px square format. "
        f"{drink.capitalize()} floating weightlessly in a bright vivid blue sky filled with white fluffy clouds. "
        f"Coffee beans and fresh green leaves flying outward in all directions around the drink. "
        f"The drink is dead-center, filling 60% of the frame, razor sharp. "
        f"Vibrant saturated colors, cheerful commercial energy. "
        f"Shop name '{shop}' in small clean white sans-serif text, top-right corner. "
        f"Main promotional text '{promo}' in large bold white font, bottom-center of the poster. "
        f"Photorealistic, ultra high quality, professional advertising campaign standard."
    )


def _dark_moody(drink: str, shop: str, promo: str) -> str:
    return (
        f"Premium café advertisement poster, 1080x1080px square format. "
        f"{drink.capitalize()} on a dark wooden coaster, single dramatic warm spotlight from above "
        f"illuminating only the drink, everything else in deep rich shadow. "
        f"Dark brown and black background, barely visible ethnic textile texture in far corner. "
        f"Rim lighting catches the cup edges in warm gold. Condensation glistens in the spotlight. "
        f"Shop name '{shop}' in small elegant gold or cream text, top-left corner. "
        f"Promotional text '{promo}' in large refined white serif font, lower-center of poster. "
        f"Photorealistic, cinematic, high-end luxury café quality."
    )


def _clean_minimal(drink: str, shop: str, promo: str) -> str:
    return (
        f"Ultra-minimal luxury café product poster, 1080x1080px square format. "
        f"{drink.capitalize()} perfectly centered on a pure white background with generous empty space on all sides. "
        f"Soft even studio lighting, one clean shadow underneath. Absolutely nothing else in frame. "
        f"Shop name '{shop}' in thin light-weight uppercase grey letters, top-center. "
        f"Promotional text '{promo}' in a single refined accent color centered below the drink. "
        f"Simple, breathable, premium product photography. "
        f"Photorealistic, high quality, Apple-product-launch aesthetic."
    )


def _flat_lay(drink: str, shop: str, promo: str) -> str:
    return (
        f"Instagram flat lay café advertisement poster, 1080x1080px square format. "
        f"Top-down overhead view of {drink} placed slightly off-center on a warm peach pastel surface. "
        f"Coffee beans, wooden spoon, small ceramic bowl, fresh green leaves neatly arranged around the drink. "
        f"A human hand reaching in from one edge holding or arranging a prop adds life. "
        f"Bright soft daylight from above, gentle shadows under each item. "
        f"Shop name '{shop}' and promotional text '{promo}' as a small styled card or label prop within the scene. "
        f"Photorealistic, fresh, curated lifestyle photography."
    )


def _outdoor_lifestyle(drink: str, shop: str, promo: str) -> str:
    return (
        f"Outdoor lifestyle café advertisement poster, 1080x1080px square format. "
        f"{drink.capitalize()} sitting on a woven rattan tray on a soft picnic blanket outdoors. "
        f"Lush green grass and garden in beautiful soft bokeh behind the drink. "
        f"Warm golden afternoon sunlight from the side, gentle lens flare, condensation glistens. "
        f"Small wildflowers or fresh fruits arranged naturally on the tray. "
        f"Shop name '{shop}' in small white text, bottom-left. "
        f"Promotional text '{promo}' in a clean light font at the bottom of the poster. "
        f"Photorealistic, relaxed, warm lifestyle photography."
    )


def _close_up_macro(drink: str, shop: str, promo: str) -> str:
    return (
        f"Extreme close-up macro café advertisement poster, 1080x1080px square format. "
        f"{drink.capitalize()} fills almost the entire frame at 45 degrees from slightly above. "
        f"Every condensation water droplet, individual ice cube, liquid layer and foam texture is razor sharp. "
        f"Soft cream bokeh background, nothing else visible. "
        f"Dramatic side lighting makes every droplet sparkle like jewels. Rim light on cup edges. "
        f"Shop name '{shop}' in very small text, top corner. "
        f"Promotional text '{promo}' in minimal refined font at the bottom edge. "
        f"Photorealistic, sensory, high-end food magazine cover quality."
    )


def _rustic_vintage(drink: str, shop: str, promo: str) -> str:
    return (
        f"Rustic artisan café advertisement poster, 1080x1080px square format. "
        f"{drink.capitalize()} on a wooden serving board on rough linen cloth. "
        f"Warm late-afternoon golden sunlight streaming from one side across the scene. "
        f"Vintage copper gooseneck kettle, ceramic mug on saucer, scattered coffee beans, "
        f"dried pampas grass in background. Terracotta wall behind the scene. "
        f"Shop name '{shop}' in warm vintage serif font at the top of the poster. "
        f"Promotional text '{promo}' in earthy toned lettering, lower section of poster. "
        f"Photorealistic, artisan heritage, handcrafted specialty coffee aesthetic."
    )


def _neon_night(drink: str, shop: str, promo: str) -> str:
    return (
        f"Dramatic night café advertisement poster, 1080x1080px square format. "
        f"{drink.capitalize()} on dark slate surface under a single powerful golden spotlight, "
        f"everything else in deep shadow. Dark background with barely visible tropical foliage. "
        f"Scattered sugar crystals and crushed ice around the base sparkle brilliantly in the spotlight. "
        f"Rim lighting catches cup edges in warm gold. "
        f"Shop name '{shop}' in bold glowing text, top of poster. "
        f"Promotional text '{promo}' large and luminous, bottom-center, with subtle glow. "
        f"Photorealistic, dramatic, high-energy nightlife café atmosphere."
    )


# ── Step 4: Gemini image generation ──────────────────────────────────────────

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

    Returns:
        {"image_base64", "image_data_url", "prompt_used", "style_used"}
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

    # Step 1 — Analyze: pick style + describe drink
    analysis   = _analyze(promotion_prompt, reference_image_base64, reference_image_mime)
    style      = analysis.get("style", "sky_float")
    drink_desc = analysis.get("drink_description", "an iced coffee drink in a clear cup")

    # Step 2 — Build: direct Python prompt (no LLM rewriting)
    prompt = _build_prompt(style, drink_desc, shop_name, promotion_prompt, colors)
    print(f"[image_agent] Prompt ({len(prompt)} chars):\n{prompt[:200]}...")

    # Step 3 — Generate image
    image_bytes, mime = _call_gemini_image(
        prompt, api_key, reference_image_base64, reference_image_mime,
    )

    b64 = base64.b64encode(image_bytes).decode()
    return {
        "image_base64":   b64,
        "image_data_url": f"data:{mime};base64,{b64}",
        "prompt_used":    prompt,
        "style_used":     style,
    }
