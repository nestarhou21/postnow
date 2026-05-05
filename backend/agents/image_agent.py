"""
agents/image_agent.py — Gemini promotional poster generator

Single-step pipeline:
  1. Python builds a punchy 60-90 word prompt (keyword-based concept selection, no API call)
  2. Gemini image → generates the poster from that prompt
"""
import os
import base64
import httpx

GEMINI_IMAGE_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "gemini-3.1-flash-image-preview:generateContent"
)
IMAGEN_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "imagen-3.0-fast-generate-001:predict"
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


# ── Concept selection ─────────────────────────────────────────────────────────

_CONCEPTS = [
    ("explosion",  ["sale", "discount", "free", "promo", "deal", "off", "buy 1", "bogo", "celebrate", "%"]),
    ("spotlight",  ["premium", "exclusive", "luxury", "signature", "special", "limited"]),
    ("minimal",    ["new", "launching", "introducing", "launch", "arrive", "menu"]),
    ("flat_lay",   ["variety", "combo", "collection", "set", "bundle", "assorted"]),
    ("lifestyle",  ["weekend", "chill", "cozy", "relax", "morning", "afternoon", "enjoy"]),
    ("macro",      ["fresh", "quality", "ingredient", "detail", "pure", "natural", "real"]),
    ("rustic",     ["artisan", "handcraft", "heritage", "traditional", "homemade"]),
    ("night",      ["night", "midnight", "late", "party", "urban", "evening"]),
]

_CONCEPT_PROMPTS = {
    "explosion": (
        "Award-winning explosion commercial photograph, Tiger Sugar campaign poster style, "
        "{drink} hero centered on vivid gradient background, ingredients and coffee beans "
        "flying dynamically around it, dramatic studio lighting from above, "
        "vibrant, energetic, appetising, bold Southeast Asian café marketing. "
        "Shot on Hasselblad H6D, 85mm f/1.8, ultra sharp, 4K, beverage commercial quality. "
        "'{shop}' small elegant text top-right. '{promo}' bold bottom-center."
    ),
    "spotlight": (
        "Award-winning spotlight commercial photograph, KOI Café advertisement style, "
        "{drink} hero on deep dark background, single dramatic overhead spotlight, "
        "rich reflections on the cup surface, moody luxury atmosphere, "
        "premium, exclusive, sophisticated Southeast Asian café marketing. "
        "Shot on Hasselblad H6D, 85mm f/1.8, ultra sharp, 4K, beverage commercial quality. "
        "'{shop}' small elegant text top-right. '{promo}' bold bottom-center."
    ),
    "minimal": (
        "Award-winning minimal commercial photograph, Gong Cha promotional style, "
        "{drink} hero on pure white studio background, generous breathing room, "
        "soft diffused natural lighting, clean and modern, "
        "fresh, simple, refined Southeast Asian café marketing. "
        "Shot on Hasselblad H6D, 85mm f/1.8, ultra sharp, 4K, beverage commercial quality. "
        "'{shop}' small elegant text top-right. '{promo}' bold bottom-center."
    ),
    "flat_lay": (
        "Award-winning flat lay commercial photograph, KOI Café advertisement style, "
        "{drink} and props arranged on pastel surface overhead view, "
        "soft natural side lighting, styled with flowers and coffee beans, "
        "charming, curated, Instagram-worthy Southeast Asian café marketing. "
        "Shot on Hasselblad H6D, 85mm f/1.8, ultra sharp, 4K, beverage commercial quality. "
        "'{shop}' small elegant text top-right. '{promo}' bold bottom-center."
    ),
    "lifestyle": (
        "Award-winning lifestyle commercial photograph, Tiger Sugar campaign poster style, "
        "{drink} held by hand in golden hour outdoor café setting, "
        "warm bokeh background, soft sunlight, inviting relaxed atmosphere, "
        "warm, joyful, authentic Southeast Asian café marketing. "
        "Shot on Hasselblad H6D, 85mm f/1.8, ultra sharp, 4K, beverage commercial quality. "
        "'{shop}' small elegant text top-right. '{promo}' bold bottom-center."
    ),
    "macro": (
        "Award-winning macro commercial photograph, Gong Cha promotional style, "
        "{drink} extreme close-up showing condensation drops on the cup, "
        "ice cubes and drink layers in sharp detail, dramatic side lighting, "
        "fresh, pure, mouthwatering Southeast Asian café marketing. "
        "Shot on Hasselblad H6D, 100mm macro f/2.8, ultra sharp, 4K, beverage commercial quality. "
        "'{shop}' small elegant text top-right. '{promo}' bold bottom-center."
    ),
    "rustic": (
        "Award-winning rustic commercial photograph, artisan café advertisement style, "
        "{drink} on warm wooden table with afternoon natural light, "
        "coffee beans and cinnamon sticks as props, cozy heritage atmosphere, "
        "warm, handcrafted, authentic Southeast Asian café marketing. "
        "Shot on Hasselblad H6D, 85mm f/1.8, ultra sharp, 4K, beverage commercial quality. "
        "'{shop}' small elegant text top-right. '{promo}' bold bottom-center."
    ),
    "night": (
        "Award-winning night commercial photograph, urban café advertisement style, "
        "{drink} glowing on dark background with dramatic neon-accent spotlight, "
        "city night atmosphere, moody and energetic, "
        "bold, modern, vibrant Southeast Asian café marketing. "
        "Shot on Hasselblad H6D, 85mm f/1.8, ultra sharp, 4K, beverage commercial quality. "
        "'{shop}' small elegant text top-right. '{promo}' bold bottom-center."
    ),
}


_DRINKS = [
    "iced latte", "latte", "cold brew", "iced coffee", "espresso",
    "americano", "cappuccino", "mocha", "flat white", "macchiato",
    "matcha latte", "matcha", "bubble tea", "boba", "milk tea",
    "thai tea", "taro", "strawberry smoothie", "smoothie",
    "frappe", "frappuccino", "hot chocolate", "chocolate",
    "caramel macchiato", "vanilla latte", "brown sugar latte",
    "passion fruit", "lemonade", "iced tea", "green tea",
]

def _extract_drink(promotion_prompt: str) -> str:
    t = promotion_prompt.lower()
    for drink in _DRINKS:
        if drink in t:
            # capitalise nicely
            return drink.title()
    return "iced café drink"


def _pick_concept(promotion_prompt: str) -> str:
    t = promotion_prompt.lower()
    for concept, keywords in _CONCEPTS:
        if any(k in t for k in keywords):
            return concept
    return "explosion"  # default


def _build_prompt(
    promotion_prompt: str,
    shop_name: str,
    reference_image_b64: str | None,
) -> tuple[str, str]:
    concept = _pick_concept(promotion_prompt)
    drink = _extract_drink(promotion_prompt)

    template = _CONCEPT_PROMPTS[concept]
    prompt = template.format(drink=drink, shop=shop_name, promo=promotion_prompt)

    if reference_image_b64:
        prompt = (
            "Reproduce the EXACT drink from the reference photo — "
            "same cup shape, same colors, same branding on the cup — "
            + prompt
        )

    print(f"[image_agent] Concept: {concept} | Prompt ({len(prompt.split())} words)")
    return prompt, concept


# ── Image generation ──────────────────────────────────────────────────────────

_TIMEOUT = httpx.Timeout(connect=10.0, read=120.0, write=30.0, pool=5.0)


def _call_imagen(prompt: str, api_key: str) -> tuple[bytes, str]:
    """Imagen 3 fast — $0.02/image, text-to-image only."""
    payload = {
        "instances": [{"prompt": prompt}],
        "parameters": {"sampleCount": 1, "aspectRatio": "1:1"},
    }
    url = f"{IMAGEN_URL}?key={api_key}"
    with httpx.Client(timeout=_TIMEOUT) as client:
        response = client.post(url, json=payload)

    if response.status_code != 200:
        raise RuntimeError(f"Imagen error {response.status_code}: {response.text}")

    pred = response.json()["predictions"][0]
    return base64.b64decode(pred["bytesBase64Encoded"]), pred.get("mimeType", "image/png")


def _call_gemini_image(
    prompt: str,
    api_key: str,
    reference_image_b64: str,
    reference_image_mime: str = "image/jpeg",
) -> tuple[bytes, str]:
    """Gemini multimodal — only used when a reference photo is provided."""
    payload = {
        "contents": [{"parts": [
            {"inlineData": {"mimeType": reference_image_mime, "data": reference_image_b64}},
            {"text": prompt},
        ]}],
        "generationConfig": {"responseModalities": ["IMAGE"]},
    }
    url = f"{GEMINI_IMAGE_URL}?key={api_key}"
    with httpx.Client(timeout=_TIMEOUT) as client:
        response = client.post(url, json=payload)

    if response.status_code != 200:
        raise RuntimeError(f"Gemini image error {response.status_code}: {response.text}")

    data = response.json()
    try:
        for part in data["candidates"][0]["content"]["parts"]:
            if "inlineData" in part:
                mime = part["inlineData"].get("mimeType", "image/png")
                return base64.b64decode(part["inlineData"]["data"]), mime
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
    _ = aesthetic, template_id, colors  # kept for caller compatibility

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

    prompt, concept = _build_prompt(promotion_prompt, shop_name, reference_image_base64)

    if reference_image_base64:
        # Multimodal Gemini — needed to see the reference drink photo
        image_bytes, mime = _call_gemini_image(
            prompt, api_key, reference_image_base64, reference_image_mime,
        )
    else:
        # Imagen 3 fast — $0.02/image, no reference photo needed
        image_bytes, mime = _call_imagen(prompt, api_key)

    b64 = base64.b64encode(image_bytes).decode()
    return {
        "image_base64":   b64,
        "image_data_url": f"data:{mime};base64,{b64}",
        "prompt_used":    prompt,
        "style_used":     concept,
    }
