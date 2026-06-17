"""Humanize academic text using the Google Gemini API (google-genai SDK)."""

import logging
from typing import Optional

from google import genai
from google.genai import types

from utils.prompts import get_humanize_prompt, ANALYSIS_PROMPT

logger = logging.getLogger(__name__)

_GEMINI_MODEL = "gemini-2.0-flash"


def _make_client(api_key: str) -> genai.Client:
    return genai.Client(api_key=api_key)


def humanize_text(
    text: str,
    api_key: str,
    level: str = "moderate",
) -> str:
    """
    Send text to Gemini and return the humanized version.

    Args:
        text: Academic text to rewrite.
        api_key: Gemini API key.
        level: One of 'light', 'moderate', 'aggressive'.

    Returns:
        Rewritten text string.

    Raises:
        ValueError: On API errors or empty response.
    """
    client = _make_client(api_key)
    prompt = get_humanize_prompt(level, text)

    try:
        response = client.models.generate_content(
            model=_GEMINI_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.75,
                top_p=0.95,
                max_output_tokens=8192,
            ),
        )
        result = response.text.strip() if response.text else ""
        if not result:
            raise ValueError("Gemini returned an empty response.")
        return result
    except Exception as e:
        logger.error("Gemini humanization failed: %s", e)
        raise ValueError(f"Gemini API error: {e}") from e


def get_ai_explanation(text: str, api_key: str) -> Optional[str]:
    """
    Ask Gemini to explain why the text reads naturally (or not).
    Returns None on failure so callers can fall back gracefully.
    """
    client = _make_client(api_key)
    prompt = ANALYSIS_PROMPT.format(text=text[:3000])  # Cap to save tokens

    try:
        response = client.models.generate_content(
            model=_GEMINI_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.4,
                max_output_tokens=512,
            ),
        )
        explanation = response.text.strip() if response.text else ""
        return explanation if explanation else None
    except Exception as e:
        logger.warning("Could not get AI explanation: %s", e)
        return None
