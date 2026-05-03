"""
agents/image_agent.py — Gemini promotional poster generator

4-step pipeline:
  1. Claude Analyzer   → examines the reference photo (if any) + promo text,
                         picks the best visual style, writes a detailed drink description.
  2. Claude Engineer   → reads the style guide + drink description, then writes a
                         fully custom, hyper-specific Gemini image prompt from scratch.
  3. Gemini            → generates a clean product photo (zero text in image).
  4. Pillow            → burns shop name + promo text onto the final image.
"""
import os
import base64
import json
import io
import textwrap
import httpx
from PIL import Image, ImageDraw, ImageFont

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
    '<text x="540" y="680" font-family="sans-serif" font-size="26" '
    'text-anchor="middle" fill="#7A5E3E">Set MOCK_IMAGE_GENERATION=false</text>'
    '<text x="540" y="720" font-family="sans-serif" font-size="26" '
    'text-anchor="middle" fill="#7A5E3E">in backend/.env to generate real posters</text>'
    '</svg>'
)
_MOCK_B64 = base64.b64encode(_MOCK_SVG.encode()).decode()


# ── Style guides (passed to the Engineer as composition rules) ─────────────────

STYLE_GUIDES = {
    "sky_float": textwrap.dedent("""
        COMPOSITION: The drink is the absolute hero, centered, filling 50% of the frame,
        resting on an oversized coffee bean as its pedestal. Identifiable at thumbnail size.
        CAMERA: Eye-level, slight low angle looking up. 50mm feel, drink razor sharp.
        LIGHTING: Bright cheerful daylight, single light source from upper left.
        Condensation glistens, ice catches light naturally. All shadows obey one direction.
        SCENE: Bright blue sky with white fluffy clouds as background.
        Scattered coffee beans and green leaves floating weightlessly around the drink.
        No surface — drink floats in open sky on its coffee bean pedestal.
        MOOD: Vibrant, energetic, celebratory Southeast Asian café marketing.
        Sky blue, cream and warm brown palette. Fun, fresh, commercial.
    """).strip(),

    "dark_moody": textwrap.dedent("""
        COMPOSITION: The drink is the only well-lit element, filling 50% of the frame.
        Placed on a dark wooden coaster on a dark wooden surface.
        CAMERA: Eye-level, slight dutch angle for drama. 85mm portrait feel, drink razor sharp.
        Background falls into soft darkness.
        LIGHTING: Single warm dramatic light from upper left. Strong deep shadows everywhere.
        Only the drink catches the light. Rim light on the cup edge. One light source only.
        SCENE: Very dark warm brown background, almost black. Soft blurred ethnic textile
        in far corner. Artisan props nearby — wooden spoon, ceramic bowl with coffee powder,
        folded linen cloth. Everything handcrafted and intentional.
        MOOD: Premium, intimate, slow coffee culture. Deep brown, mocha, dark chocolate palette.
        Zero cold colors. High-end café luxury.
    """).strip(),

    "clean_minimal": textwrap.dedent("""
        COMPOSITION: Drink perfectly centered, filling 40% of the frame maximum.
        Generous empty space on all sides. The emptiness IS the design.
        CAMERA: Eye-level, perfectly straight on, no tilt. 50mm feel. Drink perfectly sharp.
        LIGHTING: Soft even studio light from slightly above. Clean soft shadow to one side.
        No drama, no harsh shadows. One light source only.
        SCENE: Pure off-white or very light warm beige background, completely uncluttered.
        Light grey or white smooth surface underneath. At most one single minimal prop —
        one coffee bean or one clean straw. Zero clutter.
        MOOD: Elegant, modern, confident, simple. Premium brand lookbook aesthetic.
        Off-white, cream, soft beige — drink's own color is the only accent.
    """).strip(),

    "flat_lay": textwrap.dedent("""
        COMPOSITION: Drink viewed from directly overhead, placed slightly off-center.
        All top details clearly visible — lid, straw, toppings identifiable from above.
        CAMERA: Perfectly top-down at 90 degrees. Wide enough to show the full styled scene.
        LIGHTING: Bright soft even daylight from above. No harsh shadows.
        Soft gentle shadows directly under each object only.
        SCENE: Warm peach or soft yellow pastel surface. Props neatly arranged around
        the drink — wooden tray, small ceramic bowl of toppings, wooden spoon, scattered
        coffee beans, small fresh green leaves. A hand reaching in from the frame edge
        adds life and human connection.
        MOOD: Instagram-able, fresh, curated café lifestyle. Warm peach, yellow, cream, brown.
    """).strip(),

    "outdoor_lifestyle": textwrap.dedent("""
        COMPOSITION: Drink sitting naturally in outdoor setting, filling 45% of the frame.
        Sharp and detailed against a beautifully blurred natural background.
        CAMERA: Eye-level from slight 45-degree angle. Natural handheld feel, 50mm.
        Drink sharp, outdoor background in beautiful soft bokeh.
        LIGHTING: Warm natural golden sunlight from the side. Perfect sunny afternoon glow.
        Gentle lens flare from the light source. All shadows follow the sun direction.
        Condensation catches golden sunlight and glistens.
        SCENE: Lush green grass field or garden in soft focus behind the drink.
        Drink on a woven rattan tray on a soft picnic blanket.
        Fresh fruits or wildflowers arranged naturally on the tray.
        MOOD: Relaxed, lifestyle, warm, outdoor freedom. Fresh green, sky blue, warm cream.
    """).strip(),

    "close_up_macro": textwrap.dedent("""
        COMPOSITION: Extreme close-up — drink fills almost the entire frame.
        Every detail visible: condensation droplets, individual ice cubes, liquid layers,
        foam texture on top. The detail IS the story.
        CAMERA: Extreme close-up, 45 degrees from slightly above. Macro feel.
        Very shallow depth of field — only the drink sharp, everything beyond smooth bokeh.
        LIGHTING: Soft dramatic side lighting catches every water droplet and surface texture.
        Makes condensation glisten and sparkle like jewels. Single light source plus rim light.
        SCENE: Completely blurred smooth cream or off-white bokeh background.
        Nothing recognizable behind the drink. Zero props, zero distractions.
        MOOD: Satisfying, premium, deeply sensory. High-end food and beverage magazine cover.
    """).strip(),

    "rustic_vintage": textwrap.dedent("""
        COMPOSITION: Drink sitting within a rich artisan scene, filling 40% of the frame.
        Placed on a wooden serving board on a rustic linen surface.
        CAMERA: Slight high angle, 45 degrees looking down at the full scene.
        50mm feel. Drink sharp, surrounding scene in soft warm focus.
        LIGHTING: Warm golden natural light from one side, like late afternoon sun
        through a window. Long warm amber shadows across the table. Single light source.
        Wood grain, linen weave, ceramic glaze all catch the warm light naturally.
        SCENE: Rustic warm table scene. Terracotta background wall. Props arranged naturally —
        vintage copper gooseneck kettle, ceramic mug on saucer, open book,
        scattered coffee beans, dried pampas grass in background.
        MOOD: Artisan, handcrafted, heritage. Warm brown, terracotta, caramel, copper, cream.
        Specialty single-origin coffee roaster editorial.
    """).strip(),

    "neon_night": textwrap.dedent("""
        COMPOSITION: Drink is the only fully illuminated element, filling 50% of the frame.
        Sitting on a dark dramatic surface, glowing powerfully under a single spotlight.
        CAMERA: Low angle looking slightly up at the drink. Conveys power and drama.
        85mm feel. Drink perfectly sharp, dark background falls away.
        LIGHTING: Single strong warm golden spotlight from directly above, hitting only the drink.
        Everything else in deep shadow. Rim lighting catches cup edges with golden glow.
        Scattered crystals on surface sparkle brilliantly in the spotlight.
        SCENE: Very dark background — deep black with barely visible dark tropical foliage.
        Dark textured stone or slate surface under the drink.
        Scattered sugar crystals or crushed ice around the base sparkle like jewels.
        MOOD: Bold, dramatic, nightlife, urban, trendy. Deep dark green, black, rich gold, warm amber.
        High energy late-night café atmosphere.
    """).strip(),
}


# ── Claude system prompts ──────────────────────────────────────────────────────

ANALYZER_SYSTEM = """
You are an expert coffee shop creative director based in Southeast Asia.
Your job is to analyze a promotional context and make two decisions.

If a drink photo is provided, examine it carefully and describe the drink in extreme detail:
exact cup type (plastic/ceramic/glass), cup size, lid type, straw color and style,
drink color (be specific — "dusty purple" not just "purple"), visible layers and their colors,
toppings (pearls, jelly, foam, cream, powder), ice visibility, condensation level,
any branding or logo printed on the cup, garnish. Every detail matters for photographic reproduction.

If no photo is provided, write a beautiful vivid coffee drink description based on
keywords in the promo text. Make it specific and photogenic.

Then pick the best visual style from these 8 options based on the promo text keywords:
- sky_float: discount, off, sale, grand opening, celebrate, promo, free, buy one
- dark_moody: premium, special, exclusive, luxury, high-end, craft, signature
- clean_minimal: new arrival, new menu, launching, introducing, now available
- flat_lay: collection, variety, selection, menu, all drinks, combo
- outdoor_lifestyle: weekend, chill, relax, cozy, picnic, afternoon, sunny
- close_up_macro: detail, texture, quality, craftsmanship, fresh, ingredients
- rustic_vintage: artisan, handcrafted, brewing, single origin, pour over, heritage
- neon_night: late night, after dark, night, midnight, party, urban, nightlife

Respond in this exact JSON format only — no markdown, no backticks, raw JSON:
{"drink_description": "...", "style": "...", "reason": "..."}
""".strip()

ENGINEER_SYSTEM = """
You are a world-class commercial photography director who writes image generation prompts
for Southeast Asian café advertising. Your prompts produce photorealistic, commercially
polished results that look like professional paid campaigns.

You will receive:
- STYLE GUIDE: Exact composition, camera, lighting and scene rules to follow
- DRINK DESCRIPTION: The specific drink that must appear — follow every detail precisely
- SHOP NAME and PROMOTION CONTEXT

Your task: Write ONE complete, optimized, highly specific image generation prompt.

Critical rules:
1. Follow the STYLE GUIDE's composition, camera, lighting, and scene rules exactly.
2. Replace every generic drink reference with the exact DRINK DESCRIPTION details.
   The cup's material, color, lid, straw, layers, toppings must all be described explicitly.
3. If a reference photo is attached, the drink in the generated image must match it exactly —
   same cup shape, same colors, same branding, same visual identity.
4. The scene must feel physically real — every surface, liquid, ice cube, droplet
   responds to light naturally. No CGI look, no digital art feel.
5. The image must contain ABSOLUTELY ZERO text, words, letters, numbers, watermarks,
   overlays, UI elements, or digital effects of any kind.
6. End the prompt with: --no text, no words, no letters, no watermarks, no overlays

Write in vivid present-tense descriptive language. Be specific. Be cinematic.
Output ONLY the raw prompt text. No explanation, no labels, no JSON. Just the prompt.
""".strip()


# ── Gemini text API helper (used for Analyzer + Engineer) ─────────────────────

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
        raise RuntimeError(f"Gemini text API error {response.status_code}: {response.text}")

    return response.json()["candidates"][0]["content"]["parts"][0]["text"].strip()


# ── Step 1: Analyzer ──────────────────────────────────────────────────────────

def _analyze(
    promotion_prompt: str,
    reference_image_b64: str | None,
    reference_image_mime: str,
) -> dict:
    """
    Claude Analyzer: picks best style + describes the drink in detail.
    Falls back to sky_float with a generic description if Claude is unavailable.
    """
    try:
        raw = _call_gemini_text(
            system=ANALYZER_SYSTEM,
            user_text=f"Promo text: {promotion_prompt}",
            image_b64=reference_image_b64,
            image_mime=reference_image_mime,
            json_mode=True,
        )
        result = json.loads(raw)
        print(f"[image_agent] Analyzer → style={result.get('style')} | {result.get('reason', '')}")
        return result
    except Exception as e:
        print(f"[image_agent] Analyzer error: {e} — using defaults.")
        return {
            "drink_description": (
                "A beautifully presented iced coffee drink in a clear plastic cup "
                f"with a dome lid, wide black straw, caramel-brown layered drink, "
                f"condensation on the outside, lots of ice. Related to: {promotion_prompt}"
            ),
            "style": "sky_float",
            "reason": "Default fallback.",
        }


# ── Step 2: Engineer ──────────────────────────────────────────────────────────

def _engineer_prompt(
    style: str,
    drink_description: str,
    shop_name: str,
    promotion_prompt: str,
    reference_image_b64: str | None,
    reference_image_mime: str,
) -> str:
    """
    Claude Engineer: writes the final hyper-specific Gemini image prompt from scratch.
    Falls back to a basic style template if Claude is unavailable.
    """
    style_guide = STYLE_GUIDES.get(style, STYLE_GUIDES["sky_float"])
    user_text = (
        f"STYLE GUIDE:\n{style_guide}\n\n"
        f"DRINK DESCRIPTION:\n{drink_description}\n\n"
        f"SHOP NAME: {shop_name}\n"
        f"PROMOTION: {promotion_prompt}\n\n"
        "Write the complete Gemini image generation prompt now."
    )

    try:
        prompt = _call_gemini_text(
            system=ENGINEER_SYSTEM,
            user_text=user_text,
            image_b64=reference_image_b64,
            image_mime=reference_image_mime,
        )
        print(f"[image_agent] Engineer → wrote {len(prompt)} char prompt.")
        return prompt
    except Exception as e:
        print(f"[image_agent] Engineer error: {e} — using style template directly.")
        # Fallback: fill the style guide template directly with the drink description
        guide = STYLE_GUIDES.get(style, STYLE_GUIDES["sky_float"])
        return (
            f"Photorealistic commercial café advertisement photograph.\n\n"
            f"HERO PRODUCT: {drink_description}\n\n"
            f"{guide}\n\n"
            f"Ultra high quality, 4K, square 1:1 format.\n"
            f"--no text, no words, no letters, no watermarks, no overlays"
        )


# ── Step 3: Gemini image generation ──────────────────────────────────────────

def _call_gemini(
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
        raise RuntimeError(f"Gemini API error {response.status_code}: {response.text}")

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


# ── Step 4: Pillow text overlay ───────────────────────────────────────────────

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
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def overlay_promo_text(
    image_bytes: bytes,
    promotion_prompt: str,
    shop_name: str,
    brand_color: str = "#C8A27C",
) -> bytes:
    img = Image.open(io.BytesIO(image_bytes)).convert("RGBA")
    w, h = img.size

    # Dark gradient in bottom 38% of image for text readability
    overlay    = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw_ov    = ImageDraw.Draw(overlay)
    grad_start = int(h * 0.62)
    for row in range(grad_start, h):
        progress = (row - grad_start) / (h - grad_start)
        alpha    = int(210 * (progress ** 0.55))
        draw_ov.line([(0, row), (w, row)], fill=(0, 0, 0, alpha))
    img  = Image.alpha_composite(img, overlay)
    draw = ImageDraw.Draw(img)

    font_shop  = _load_font(max(28, w // 36))
    font_promo = _load_font(max(52, w // 16))
    accent_rgb = _hex_to_rgb(brand_color)

    # Shop name (accent color, small)
    shop_text = shop_name.upper()
    bbox      = draw.textbbox((0, 0), shop_text, font=font_shop)
    shop_w    = bbox[2] - bbox[0]
    shop_y    = int(h * 0.67)
    draw.text(((w - shop_w) // 2, shop_y), shop_text, font=font_shop,
              fill=(*accent_rgb, 230))

    # Promo lines (white, bold, large)
    lines  = _split_lines(promotion_prompt)
    line_h = draw.textbbox((0, 0), "A", font=font_promo)[3] + 10
    y      = int(h * 0.73)
    for line in lines:
        bbox   = draw.textbbox((0, 0), line, font=font_promo)
        line_w = bbox[2] - bbox[0]
        x      = (w - line_w) // 2
        draw.text((x + 3, y + 3), line, font=font_promo, fill=(0, 0, 0, 160))  # shadow
        draw.text((x, y),         line, font=font_promo, fill=(255, 255, 255, 255))
        y += line_h

    buf = io.BytesIO()
    img.convert("RGB").save(buf, format="PNG", optimize=True)
    return buf.getvalue()


# ── Public entry point ────────────────────────────────────────────────────────

def generate_poster(
    promotion_prompt: str,
    shop_name: str,
    aesthetic: str,
    colors: list[str],
    template_id: str = "centered",           # kept for caller compatibility; style is auto-selected
    reference_image_base64: str | None = None,
    reference_image_mime: str = "image/jpeg",
) -> dict:
    """
    Generate a promotional poster via the 4-step pipeline.

    Returns:
        {
            "image_base64":   str,
            "image_data_url": str,   # ready for <img src="...">
            "prompt_used":    str,
            "style_used":     str,
        }
    """
    _ = aesthetic, template_id  # kept for caller compatibility

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

    # Step 1 — Analyzer: pick style + describe drink
    analysis     = _analyze(promotion_prompt, reference_image_base64, reference_image_mime)
    style        = analysis.get("style", "sky_float")
    drink_desc   = analysis.get("drink_description", promotion_prompt)

    # Step 2 — Engineer: write the final custom Gemini prompt
    final_prompt = _engineer_prompt(
        style, drink_desc, shop_name, promotion_prompt,
        reference_image_base64, reference_image_mime,
    )

    # Step 3 — Gemini: generate clean product photo
    image_bytes, mime = _call_gemini(
        final_prompt, api_key,
        reference_image_base64, reference_image_mime,
    )

    # Step 4 — Pillow: burn text onto image
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
        "prompt_used":    final_prompt,
        "style_used":     style,
    }
