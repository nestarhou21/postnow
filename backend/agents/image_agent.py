"""
agents/image_agent.py — Gemini promotional poster generator

Flow:
  1. Claude meta-prompt  → picks best visual style + describes the drink
  2. Style function      → builds a detailed Gemini image prompt (no text in image)
  3. Gemini API          → generates clean product photo
  4. Pillow              → burns promo text + shop name onto the final image
"""
import os
import base64
import json
import io
import textwrap
import httpx
from PIL import Image, ImageDraw, ImageFont

GEMINI_API_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "gemini-3.1-flash-image-preview:generateContent"
)
CLAUDE_API_URL = "https://api.anthropic.com/v1/messages"

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
    '<text x="540" y="680" font-family="sans-serif" font-size="26" '
    'text-anchor="middle" fill="#7A5E3E">Set MOCK_IMAGE_GENERATION=false</text>'
    '<text x="540" y="720" font-family="sans-serif" font-size="26" '
    'text-anchor="middle" fill="#7A5E3E">in backend/.env to generate real posters</text>'
    '</svg>'
)
_MOCK_B64 = base64.b64encode(_MOCK_SVG.encode()).decode()


# ── 8 Specialized style templates ─────────────────────────────────────────────

def sky_float(drink_description: str) -> str:
    return textwrap.dedent(f"""
        [SUBJECT]: {drink_description}
        The drink is the absolute hero, centered and dominant,
        filling 50% of the frame. Placed resting on top of
        a large oversized coffee bean as its pedestal.
        Passes the 3-second zoom-out test — identifiable
        even at thumbnail size.

        [CAMERA]: Eye-level shot, slight low angle looking
        up at the drink to convey energy and excitement.
        50mm feel, drink sharp and in crisp focus.
        Natural bokeh background.

        [LIGHTING]: Bright cheerful daylight. Single light
        source from upper left. All shadows, highlights and
        reflections obey this one direction only.
        Real-world light — condensation on cup glistens,
        ice catches the light naturally.

        [SCENE]: Bright blue sky with white fluffy clouds
        as the background, clean and airy. Scattered coffee
        beans and green leaves floating in air at various
        angles around the drink — some in foreground,
        some behind. Everything feels suspended and
        weightless. No surface — drink floats on its
        coffee bean pedestal in open sky.

        [STYLE]: Vibrant, energetic, commercial Southeast
        Asian café marketing. Sky blue, cream and warm
        brown color palette. Fun, fresh, celebratory mood.
        Real-world textures throughout — every surface,
        every prop feels physically present and tangible.

        [TECHNICAL]: Photorealistic, ultra high quality, 4K.
        Square 1:1 format.
        --no text, no words, no letters, no watermarks,
        no floating overlays, no UI elements, no digital effects.
    """).strip()


def dark_moody(drink_description: str) -> str:
    return textwrap.dedent(f"""
        [SUBJECT]: {drink_description}
        The drink is the absolute hero and the only
        well-lit element in the entire scene, filling
        50% of the frame. Placed on a dark wooden coaster
        on a dark wooden surface. Every detail of the drink
        is crisp and sharp — condensation, layers, texture.

        [CAMERA]: Eye-level shot, slight dutch angle for
        drama and intimacy. 85mm portrait feel, drink
        razor sharp. Background falls into soft darkness.
        Composition passes the 3-second zoom-out test.

        [LIGHTING]: Single warm dramatic light from upper
        left. Strong deep shadows everywhere. Only the
        drink catches the light — everything else fades
        into darkness. Rim light catches the very edge
        of the cup. All shadows obey one single direction.

        [SCENE]: Very dark warm brown background, almost
        black. Soft blurred ethnic textile visible in far
        corner. Dark wooden surface. Artisan props placed
        naturally nearby — wooden spoon, small ceramic bowl
        with coffee powder, folded linen cloth underneath.

        [STYLE]: Premium, intimate, slow coffee culture.
        Deep brown, mocha, dark chocolate color palette.
        Zero cold colors anywhere. High-end café luxury.

        [TECHNICAL]: Photorealistic, ultra high quality, 4K.
        Square 1:1 format.
        --no text, no words, no letters, no watermarks,
        no floating overlays, no UI elements, no digital effects.
    """).strip()


def clean_minimal(drink_description: str) -> str:
    return textwrap.dedent(f"""
        [SUBJECT]: {drink_description}
        The drink is the absolute hero, perfectly centered
        with generous empty space around it. Filling 40%
        of the frame maximum. Clean and confident.

        [CAMERA]: Eye-level shot, perfectly straight on,
        no tilt whatsoever. 50mm feel. Drink perfectly
        sharp. Lots of negative space above and below.
        The emptiness IS the design.

        [LIGHTING]: Soft even studio light from slightly
        above. Clean soft shadow cast naturally to one
        side on the surface below. No drama, no harsh
        shadows. One light source only.

        [SCENE]: Pure off-white or very light warm beige
        background, completely clean and uncluttered.
        Light grey or white smooth surface underneath.
        Zero clutter. At most one single minimal prop —
        one coffee bean or one clean straw. Nothing more.

        [STYLE]: Elegant, modern, confident, simple.
        Off-white, cream, soft beige palette. Premium
        brand lookbook or high-end product photography.

        [TECHNICAL]: Photorealistic, ultra high quality, 4K.
        Square 1:1 format.
        --no text, no words, no letters, no watermarks,
        no floating overlays, no UI elements, no digital effects.
    """).strip()


def flat_lay(drink_description: str) -> str:
    return textwrap.dedent(f"""
        [SUBJECT]: {drink_description}
        The drink is the absolute hero viewed from directly
        above. Placed slightly off-center in the composition.
        All details visible from overhead — top of the drink,
        lid, straw, toppings all clearly identifiable.

        [CAMERA]: Directly overhead, perfectly top-down
        flat lay. Camera pointing straight down at 90 degrees.

        [LIGHTING]: Bright soft even daylight from above.
        No harsh shadows. One consistent light source.
        Soft gentle shadows directly under each object only.

        [SCENE]: Warm peach or soft yellow pastel surface.
        Props neatly arranged around the drink — wooden tray,
        small ceramic bowl of toppings, wooden spoon,
        scattered coffee beans, small fresh green leaves.
        A hand reaching in from the frame edge adds life.

        [STYLE]: Instagram-able, fresh, curated café lifestyle.
        Warm peach, soft yellow, cream, brown palette.

        [TECHNICAL]: Photorealistic, ultra high quality, 4K.
        Square 1:1 format.
        --no text, no words, no letters, no watermarks,
        no floating overlays, no UI elements, no digital effects.
    """).strip()


def outdoor_lifestyle(drink_description: str) -> str:
    return textwrap.dedent(f"""
        [SUBJECT]: {drink_description}
        The drink is the absolute hero, sitting naturally
        in an outdoor lifestyle setting. Filling 45% of
        the frame. Sharp and detailed against the beautifully
        blurred natural background behind it.

        [CAMERA]: Eye-level shot from slight 45 degree angle.
        Natural handheld feel, 50mm. Drink sharp. Lush
        outdoor background in beautiful soft bokeh.

        [LIGHTING]: Warm natural golden sunlight from the
        side. Soft and glowing, feels like a perfect sunny
        afternoon. Gentle lens flare from the light source.

        [SCENE]: Outdoor natural setting. Lush green grass
        or garden in soft focus background. Drink sitting
        on a woven rattan tray on a soft picnic blanket.
        Fresh fruits or wildflowers arranged naturally nearby.
        Feels like a perfect sunny picnic afternoon.

        [STYLE]: Relaxed, lifestyle, warm, outdoor freedom.
        Fresh green, sky blue, warm cream, natural organic tones.

        [TECHNICAL]: Photorealistic, ultra high quality, 4K.
        Square 1:1 format.
        --no text, no words, no letters, no watermarks,
        no floating overlays, no UI elements, no digital effects.
    """).strip()


def close_up_macro(drink_description: str) -> str:
    return textwrap.dedent(f"""
        [SUBJECT]: {drink_description}
        The drink fills almost the entire frame — extreme
        close-up hero shot. Every detail is visible and
        razor sharp — condensation water droplets, individual
        ice cubes, liquid color layers, foam texture on top.

        [CAMERA]: Extreme close-up, 45 degree angle from
        slightly above. Macro feel. Very shallow depth of
        field — only the drink is sharp, everything beyond
        is smooth creamy bokeh.

        [LIGHTING]: Soft dramatic side lighting that catches
        every water droplet and surface texture. Makes
        condensation glisten and sparkle like jewels.
        Single light source, rim light on opposite edge.

        [SCENE]: Completely blurred smooth cream or off-white
        bokeh background. Nothing recognizable behind the
        drink. Zero props, zero distractions.

        [STYLE]: Satisfying, premium, quality-focused, deeply
        sensory. Feels like a cover shot from a high-end
        food and beverage magazine.

        [TECHNICAL]: Photorealistic, ultra high quality, 4K.
        Square 1:1 format.
        --no text, no words, no letters, no watermarks,
        no floating overlays, no UI elements, no digital effects.
    """).strip()


def rustic_vintage(drink_description: str) -> str:
    return textwrap.dedent(f"""
        [SUBJECT]: {drink_description}
        The drink is the absolute hero sitting within a
        rich artisan scene, filling 40% of the frame.
        Placed on a wooden serving board on a rustic
        linen surface.

        [CAMERA]: Slight high angle, 45 degrees looking
        down at the full scene. 50mm feel. Drink sharp,
        surrounding scene in soft warm focus.

        [LIGHTING]: Warm golden natural light from one side,
        like late afternoon sun streaming through a window.
        Long warm amber shadows across the table surface.
        Everything glows with warmth. Single light source.

        [SCENE]: Rustic warm table scene. Wooden surface
        with linen cloth underneath. Terracotta background
        wall. Props arranged naturally — vintage copper
        gooseneck kettle, ceramic mug on saucer, open book,
        scattered coffee beans, dried pampas grass in background.

        [STYLE]: Artisan, handcrafted, heritage storytelling.
        Warm brown, terracotta, caramel, copper, cream.
        Specialty single-origin coffee roaster editorial.

        [TECHNICAL]: Photorealistic, ultra high quality, 4K.
        Square 1:1 format.
        --no text, no words, no letters, no watermarks,
        no floating overlays, no UI elements, no digital effects.
    """).strip()


def neon_night(drink_description: str) -> str:
    return textwrap.dedent(f"""
        [SUBJECT]: {drink_description}
        The drink is the absolute hero, the only element
        fully illuminated. Filling 50% of the frame.
        Sitting on a dark dramatic surface, glowing
        powerfully under a single spotlight.

        [CAMERA]: Low angle looking slightly up at the drink.
        Conveys power, premium energy and drama. 85mm feel.
        Drink perfectly sharp, dark background falls away.

        [LIGHTING]: Single strong warm golden spotlight
        from directly above hitting only the drink.
        Everything else in deep shadow. Rim lighting
        catches the very edges of the cup with golden glow.
        Scattered crystals on surface sparkle in the spotlight.

        [SCENE]: Dark dramatic setting. Very dark background —
        deep black with barely visible dark tropical foliage.
        Dark textured stone or slate surface under the drink.
        Scattered sugar crystals or crushed ice around the
        base catch the spotlight and sparkle brilliantly.

        [STYLE]: Bold, dramatic, nightlife, urban, trendy.
        Deep dark green, black, rich gold, warm amber.
        High energy night café atmosphere.

        [TECHNICAL]: Photorealistic, ultra high quality, 4K.
        Square 1:1 format.
        --no text, no words, no letters, no watermarks,
        no floating overlays, no UI elements, no digital effects.
    """).strip()


STYLE_FUNCTIONS = {
    "sky_float":        sky_float,
    "dark_moody":       dark_moody,
    "clean_minimal":    clean_minimal,
    "flat_lay":         flat_lay,
    "outdoor_lifestyle": outdoor_lifestyle,
    "close_up_macro":   close_up_macro,
    "rustic_vintage":   rustic_vintage,
    "neon_night":       neon_night,
}

# ── Meta prompt ───────────────────────────────────────────────────────────────

META_PROMPT = """
You are an expert coffee shop creative director and
poster designer specialized in Southeast Asian café
marketing. You have 10 years of experience designing
viral coffee shop promotional posters for cafés across
Cambodia, Vietnam, and Thailand. You understand what
makes a coffee poster sell — composition, light, mood,
and the culture of the market.

Your job is to do two things:

1. DESCRIBE THE DRINK: If an image is provided, look
at it carefully and write a detailed vivid description
of the drink exactly as it looks. Include: cup type
and material, drink color and layers, toppings, ice,
foam, condensation, garnish, and any other visible
details. Be specific — this description will be used
to recreate the drink visually so every detail matters.
If no image is provided, write a beautiful generic
coffee drink description based on keywords found in
the promo text.

2. PICK THE STYLE: Read the promo text carefully and
as an experienced coffee poster designer pick the most
suitable visual style from these 8 options:
- sky_float: discount, promotion, off, sale,
  grand opening, celebrate, energetic
- dark_moody: premium, special, exclusive, luxury,
  high-end, craft
- clean_minimal: new arrival, new menu, launching,
  introducing, fresh, simple
- flat_lay: overhead, layout, collection, menu,
  variety, selection
- outdoor_lifestyle: weekend, chill, relax, cozy,
  picnic, afternoon, nature
- close_up_macro: detail, texture, quality, close,
  craftsmanship, ingredients
- rustic_vintage: artisan, handcrafted, brewing,
  single origin, pour over, heritage
- neon_night: late night, after dark, night,
  midnight, party, urban, trendy

Always return your response in this exact JSON format:
{"drink_description": "your detailed drink description here", "style": "the chosen style name here", "reason": "one sentence why you chose this style"}

Never return anything outside of this JSON.
Never add markdown, never add backticks.
Just clean raw JSON only.
""".strip()


# ── Step 1: Analyze promo → pick style + describe drink ──────────────────────

def _analyze_promo(
    promotion_prompt: str,
    reference_image_base64: str | None = None,
    reference_image_mime: str = "image/jpeg",
) -> dict:
    """
    Call Claude to pick the best visual style and describe the drink.
    Falls back to sky_float if Claude is unavailable.
    """
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        return {
            "drink_description": (
                f"A beautifully presented iced coffee drink in a clear plastic cup "
                f"with a dome lid and black straw. Related to: {promotion_prompt}"
            ),
            "style": "sky_float",
            "reason": "Default style — no Claude API key configured.",
        }

    content = []
    if reference_image_base64:
        content.append({
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": reference_image_mime,
                "data": reference_image_base64,
            },
        })
    content.append({"type": "text", "text": f"Promo text: {promotion_prompt}"})

    payload = {
        "model": "claude-sonnet-4-6",
        "max_tokens": 512,
        "system": META_PROMPT,
        "messages": [{"role": "user", "content": content}],
    }

    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.post(
                CLAUDE_API_URL,
                headers={
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json=payload,
            )
        if response.status_code == 200:
            raw = response.json()["content"][0]["text"].strip()
            return json.loads(raw)
    except Exception as e:
        print(f"[image_agent] Meta-prompt error: {e} — using default style.")

    return {
        "drink_description": (
            f"A beautifully presented iced coffee drink in a clear plastic cup "
            f"with a dome lid and black straw. Related to: {promotion_prompt}"
        ),
        "style": "sky_float",
        "reason": "Fallback style due to analysis error.",
    }


# ── Step 2: Pillow text overlay ───────────────────────────────────────────────

_FONT_CANDIDATES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "/usr/share/fonts/truetype/ubuntu/Ubuntu-B.ttf",
    "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
    "/System/Library/Fonts/Helvetica.ttc",
    "/Library/Fonts/Arial Bold.ttf",
    "/System/Library/Fonts/Arial.ttf",
]


def _load_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for path in _FONT_CANDIDATES:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue
    return ImageFont.load_default()


def _split_lines(text: str, max_chars: int = 18) -> list[str]:
    """Break promo text into short punchy uppercase lines."""
    words = text.split()
    lines, current = [], []
    for word in words:
        if sum(len(w) + 1 for w in current) + len(word) > max_chars and current:
            lines.append(" ".join(current).upper())
            current = [word]
        else:
            current.append(word)
    if current:
        lines.append(" ".join(current).upper())
    return lines[:3]


def _hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    h = hex_color.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return r, g, b


def overlay_promo_text(
    image_bytes: bytes,
    promotion_prompt: str,
    shop_name: str,
    brand_color: str = "#C8A27C",
) -> bytes:
    """
    Composite shop name + promo text onto the image using Pillow.
    Returns the final composited image as PNG bytes.
    """
    img = Image.open(io.BytesIO(image_bytes)).convert("RGBA")
    w, h = img.size

    # ── Dark gradient overlay at the bottom third ──────────────────────────
    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw_ov = ImageDraw.Draw(overlay)
    gradient_top = int(h * 0.62)
    for row in range(gradient_top, h):
        progress = (row - gradient_top) / (h - gradient_top)
        alpha = int(200 * (progress ** 0.6))
        draw_ov.line([(0, row), (w, row)], fill=(0, 0, 0, alpha))
    img = Image.alpha_composite(img, overlay)

    draw = ImageDraw.Draw(img)

    # ── Font sizes relative to image width ─────────────────────────────────
    font_shop  = _load_font(max(28, w // 36))
    font_promo = _load_font(max(52, w // 16))

    # ── Shop name ──────────────────────────────────────────────────────────
    accent_rgb = _hex_to_rgb(brand_color)
    shop_text  = shop_name.upper()
    bbox       = draw.textbbox((0, 0), shop_text, font=font_shop)
    shop_w     = bbox[2] - bbox[0]
    shop_y     = int(h * 0.67)
    draw.text(((w - shop_w) // 2, shop_y), shop_text, font=font_shop,
              fill=(*accent_rgb, 220))

    # ── Promo lines ────────────────────────────────────────────────────────
    lines  = _split_lines(promotion_prompt)
    line_h = (draw.textbbox((0, 0), "A", font=font_promo)[3]) + 8
    y      = int(h * 0.73)

    for line in lines:
        bbox   = draw.textbbox((0, 0), line, font=font_promo)
        line_w = bbox[2] - bbox[0]
        x      = (w - line_w) // 2
        # Drop shadow
        draw.text((x + 3, y + 3), line, font=font_promo, fill=(0, 0, 0, 160))
        # Main text
        draw.text((x, y), line, font=font_promo, fill=(255, 255, 255, 255))
        y += line_h

    result = img.convert("RGB")
    buf    = io.BytesIO()
    result.save(buf, format="PNG", optimize=True)
    return buf.getvalue()


# ── Step 3: Gemini image generation ──────────────────────────────────────────

def _call_gemini(
    prompt: str,
    api_key: str,
    reference_image_base64: str | None = None,
    reference_image_mime: str = "image/jpeg",
) -> tuple[bytes, str]:
    """
    Call Gemini and return (raw_image_bytes, mime_type).
    """
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
        "generationConfig": {"responseModalities": ["IMAGE", "TEXT"]},
    }

    url = f"{GEMINI_API_URL}?key={api_key}"
    with httpx.Client(timeout=90.0) as client:
        response = client.post(url, json=payload)

    if response.status_code != 200:
        raise RuntimeError(f"Gemini API error {response.status_code}: {response.text}")

    data = response.json()
    try:
        for part in data["candidates"][0]["content"]["parts"]:
            if "inlineData" in part:
                mime  = part["inlineData"].get("mimeType", "image/png")
                raw   = base64.b64decode(part["inlineData"]["data"])
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
    template_id: str = "centered",          # kept for API compatibility; style is auto-selected
    reference_image_base64: str | None = None,
    reference_image_mime: str = "image/jpeg",
) -> dict:
    """
    Generate a promotional poster.

    Steps:
      1. Claude picks the best visual style and describes the drink.
      2. The matching style function builds a Gemini image prompt.
      3. Gemini generates a clean product photo (no text).
      4. Pillow burns the shop name + promo text onto the image.

    Returns:
        {
            "image_base64":   str,
            "image_data_url": str,   # ready for <img src="...">
            "prompt_used":    str,
            "style_used":     str,
        }
    """
    _ = aesthetic, template_id  # auto-selected by _analyze_promo; kept for caller compatibility
    mock_mode = os.getenv("MOCK_IMAGE_GENERATION", "false").lower() == "true"

    if mock_mode:
        return {
            "image_base64":   _MOCK_B64,
            "image_data_url": f"data:image/svg+xml;base64,{_MOCK_B64}",
            "prompt_used":    "(mock mode)",
            "style_used":     "mock",
        }

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not set. Add it to backend/.env or set MOCK_IMAGE_GENERATION=true.")

    # Step 1 — meta-prompt: pick style + describe drink
    analysis = _analyze_promo(promotion_prompt, reference_image_base64, reference_image_mime)
    style    = analysis.get("style", "sky_float")
    drink_desc = analysis.get("drink_description", promotion_prompt)
    print(f"[image_agent] Style: {style} | {analysis.get('reason', '')}")

    # Step 2 — build image prompt from the chosen style function
    style_fn = STYLE_FUNCTIONS.get(style, sky_float)
    prompt   = style_fn(drink_desc)

    # Step 3 — call Gemini
    image_bytes, mime = _call_gemini(
        prompt, api_key,
        reference_image_base64, reference_image_mime,
    )

    # Step 4 — Pillow text overlay
    brand_color = colors[0] if colors else "#C8A27C"
    try:
        image_bytes = overlay_promo_text(image_bytes, promotion_prompt, shop_name, brand_color)
        mime = "image/png"
    except Exception as e:
        print(f"[image_agent] Text overlay failed: {e} — returning raw image.")

    b64 = base64.b64encode(image_bytes).decode()
    return {
        "image_base64":   b64,
        "image_data_url": f"data:{mime};base64,{b64}",
        "prompt_used":    prompt,
        "style_used":     style,
    }
