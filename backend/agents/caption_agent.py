"""
agents/caption_agent.py — Claude-powered bilingual caption generator

Uses Anthropic Claude (claude-sonnet-4-6) to produce:
  • English caption (≤150 words, Facebook/Instagram ready)
  • Khmer caption (culturally adapted, NOT a literal translation)
  • 5 relevant hashtags
"""
import os
import re
import anthropic

_client = None


def _get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    return _client


SYSTEM_PROMPT_TEMPLATE = """You are a social media manager for {shop_name}, a {aesthetic} coffee shop in Phnom Penh, Cambodia.

Your job is to write promotional content for Facebook and Instagram that feels authentic, warm, and on-brand.

Brand personality:
- Shop name: {shop_name}
- Aesthetic: {aesthetic}
- Brand colors (for reference/mood): {colors}

Rules you MUST follow:
1. Write an English caption first — max 150 words, conversational, ends with a call-to-action.
2. Write a Khmer caption second — culturally adapted for a Cambodian audience (NOT a word-for-word translation). Natural, friendly tone.
3. Write exactly 5 hashtags on one line, mixing English and Khmer hashtags relevant to the promotion.
4. Do NOT use emojis unless the aesthetic is "Bold".
5. Do NOT include pricing unless the user's prompt mentions it.
6. Return your answer in EXACTLY this format with these section markers:

[EN]
<english caption here>

[KH]
<khmer caption here>

[TAGS]
<5 hashtags here>

Do not add any extra text, explanation, or commentary outside these three sections."""


def generate_caption(
    promotion_prompt: str,
    shop_name: str,
    aesthetic: str,
    colors: list[str],
) -> dict:
    """
    Call Claude to generate bilingual caption + hashtags.

    Returns:
        {
            "en_caption": str,
            "kh_caption": str,
            "hashtags": str,
        }
    """
    system = SYSTEM_PROMPT_TEMPLATE.format(
        shop_name=shop_name,
        aesthetic=aesthetic,
        colors=", ".join(colors),
    )

    user_message = f"Write a promotional post for this campaign:\n\n{promotion_prompt}"

    response = _get_client().messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        system=system,
        messages=[{"role": "user", "content": user_message}],
    )

    raw = response.content[0].text
    return _parse_caption_response(raw)


def _parse_caption_response(raw: str) -> dict:
    """Parse Claude's structured [EN] / [KH] / [TAGS] response."""
    en_match  = re.search(r"\[EN\]\s*(.*?)\s*(?=\[KH\]|\[TAGS\]|$)", raw, re.DOTALL)
    kh_match  = re.search(r"\[KH\]\s*(.*?)\s*(?=\[EN\]|\[TAGS\]|$)", raw, re.DOTALL)
    tag_match = re.search(r"\[TAGS\]\s*(.*?)$", raw, re.DOTALL)

    return {
        "en_caption": en_match.group(1).strip() if en_match else "",
        "kh_caption": kh_match.group(1).strip() if kh_match else "",
        "hashtags":   tag_match.group(1).strip() if tag_match else "",
    }
