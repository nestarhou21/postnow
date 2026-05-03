"""
agents/image_agent.py — Gemini promotional poster generator
"""
import os
import base64
import httpx

GEMINI_API_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "gemini-2.0-flash-preview-image-generation:generateContent"
)

# Mock poster returned when MOCK_IMAGE_GENERATION=true (no API key needed)
_MOCK_SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" width="1080" height="1080">'
    '<rect width="1080" height="1080" fill="#C8A27C"/>'
    '<rect x="60" y="60" width="960" height="960" fill="none" stroke="#5A3E2B" stroke-width="6"/>'
    '<text x="540" y="420" font-family="Georgia,serif" font-size="96" font-weight="bold" '
    'text-anchor="middle" fill="#5A3E2B">POSTNOW</text>'
    '<text x="540" y="530" font-family="Georgia,serif" font-size="48" '
    'text-anchor="middle" fill="#5A3E2B">Mock Poster Preview</text>'
    '<text x="540" y="620" font-family="sans-serif" font-size="30" '
    'text-anchor="middle" fill="#7A5E3E">☕  Mock mode active</text>'
    '<text x="540" y="680" font-family="sans-serif" font-size="26" '
    'text-anchor="middle" fill="#7A5E3E">Set MOCK_IMAGE_GENERATION=false</text>'
    '<text x="540" y="720" font-family="sans-serif" font-size="26" '
    'text-anchor="middle" fill="#7A5E3E">in backend/.env to generate real posters</text>'
    '</svg>'
)
_MOCK_B64 = base64.b64encode(_MOCK_SVG.encode()).decode()

# ── Template art direction ────────────────────────────────────────────────────

TEMPLATE_STYLES = {
    "centered": (
        "centered product-hero composition. "
        "The drink or product is the focal point dead-center. "
        "Shop name as a large headline above the product. "
        "Promotion text as a bold call-to-action below the product. "
        "Symmetrical layout with balanced margins on all sides."
    ),
    "text_banner": (
        "typography-first banner layout. "
        "A bold oversized headline fills the top half of the poster. "
        "Promotion details in medium weight text below. "
        "Small product image or icon in the bottom corner. "
        "High contrast between text color and background. "
        "Thick decorative border framing the entire poster."
    ),
    "lifestyle": (
        "warm lifestyle scene. "
        "A candid top-down or side-angle shot of coffee drinks on a cafe table. "
        "Soft natural window light, warm ambient atmosphere. "
        "Shop name and promotion text as an elegant semi-transparent overlay "
        "in the bottom third of the image. "
        "Authentic, inviting, and aspirational feel."
    ),
    "minimal": (
        "clean minimalist layout with maximum white or cream negative space. "
        "A single small product illustration or icon centered slightly above middle. "
        "Shop name in a light-weight elegant font below the icon. "
        "Promotion text in small refined type at the bottom. "
        "No decorative elements — only essential information. "
        "Swiss design influence, calm and sophisticated."
    ),
}

AESTHETIC_MOODS = {
    "Cozy": (
        "warm and cozy cafe atmosphere. "
        "Terracotta, latte brown, and cream tones dominate. "
        "Soft bokeh background, natural wood textures. "
        "Handwritten-style or serif fonts. "
        "Intimate, inviting, and comfortable feeling. "
        "Warm golden hour lighting."
    ),
    "Bold": (
        "bold and energetic design. "
        "Saturated, high-contrast colors. "
        "Strong geometric shapes and color blocks. "
        "Thick modern sans-serif fonts with heavy weight. "
        "Dynamic and eye-catching composition. "
        "Vibrant, youthful, urban energy."
    ),
    "Minimalist": (
        "clean minimalist aesthetic. "
        "Predominantly white or off-white background. "
        "One or two accent colors used sparingly. "
        "Thin elegant fonts, generous negative space. "
        "No gradients or textures — flat, refined, modern. "
        "Calm, premium, and sophisticated feel."
    ),
}

QUALITY_SUFFIX = (
    "Square 1:1 format, optimised for Instagram. "
    "Professional marketing quality. "
    "All text must be spelled correctly and be clearly legible. "
    "No watermarks, no extra logos. "
    "Photorealistic or high-quality graphic design style."
)


# ── Prompt builder ────────────────────────────────────────────────────────────

def build_image_prompt(
    promotion_prompt: str,
    shop_name: str,
    aesthetic: str,
    colors: list[str],
    template_id: str = "centered",
    has_reference_photo: bool = False,
) -> str:
    style     = TEMPLATE_STYLES.get(template_id, TEMPLATE_STYLES["centered"])
    mood      = AESTHETIC_MOODS.get(aesthetic, AESTHETIC_MOODS["Cozy"])
    color_str = " and ".join(colors) if colors else "#C8A27C and #5A3E2B"

    base = (
        f"Design a professional promotional poster for a Cambodian coffee shop named '{shop_name}'.\n\n"
        f"PROMOTION: {promotion_prompt}\n\n"
        f"LAYOUT: {style}\n\n"
        f"MOOD & ATMOSPHERE: {mood}\n\n"
        f"BRAND COLORS: Use {color_str} as the primary color palette throughout the design — "
        f"for backgrounds, text, accents, and decorative elements.\n\n"
        f"REQUIRED TEXT ON POSTER:\n"
        f"- Shop name: '{shop_name}'\n"
        f"- Promotion: '{promotion_prompt}'\n\n"
        f"QUALITY: {QUALITY_SUFFIX}"
    )

    if has_reference_photo:
        base += (
            "\n\nREFERENCE PHOTO: A real coffee shop photo is provided. "
            "Use it as the visual foundation — keep the authentic atmosphere and real elements "
            "from the photo while overlaying the brand colors, layout template, shop name, "
            "and promotion text to transform it into a polished promotional poster."
        )

    return base


# ── API call ──────────────────────────────────────────────────────────────────

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
    Generate a promotional poster via Gemini image generation.

    If reference_image_base64 is provided, Gemini uses it as a visual reference.
    If MOCK_IMAGE_GENERATION=true, returns an SVG placeholder (no API call).

    Returns:
        {
            "image_base64": str,
            "image_data_url": str,  # ready for <img src="...">
            "prompt_used": str,
        }
    """
    mock_mode = os.getenv("MOCK_IMAGE_GENERATION", "false").lower() == "true"
    prompt    = build_image_prompt(
        promotion_prompt, shop_name, aesthetic, colors, template_id,
        has_reference_photo=bool(reference_image_base64),
    )

    if mock_mode:
        return {
            "image_base64":   _MOCK_B64,
            "image_data_url": f"data:image/svg+xml;base64,{_MOCK_B64}",
            "prompt_used":    prompt,
        }

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not set. Add it to backend/.env or set MOCK_IMAGE_GENERATION=true.")

    # Build the content parts — photo first (if provided), then text prompt
    parts = []
    if reference_image_base64:
        parts.append({
            "inlineData": {
                "mimeType": reference_image_mime,
                "data":     reference_image_base64,
            }
        })
    parts.append({"text": prompt})

    payload = {
        "contents": [{"parts": parts}],
        "generationConfig": {
            "responseModalities": ["IMAGE", "TEXT"],
        },
    }

    url = f"{GEMINI_API_URL}?key={api_key}"

    with httpx.Client(timeout=90.0) as client:
        response = client.post(url, json=payload)

    if response.status_code != 200:
        raise RuntimeError(f"Gemini API error {response.status_code}: {response.text}")

    data = response.json()

    try:
        parts_out = data["candidates"][0]["content"]["parts"]
        for part in parts_out:
            if "inlineData" in part:
                b64  = part["inlineData"]["data"]
                mime = part["inlineData"].get("mimeType", "image/png")
                return {
                    "image_base64":   b64,
                    "image_data_url": f"data:{mime};base64,{b64}",
                    "prompt_used":    prompt,
                }
    except (KeyError, IndexError) as e:
        raise RuntimeError(f"Could not parse Gemini response: {e}\nRaw: {data}")

    raise RuntimeError("No image returned from Gemini API")
