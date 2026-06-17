"""Shared helper utilities."""

import re
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def clean_text(text: str) -> str:
    """Normalize whitespace and strip leading/trailing space."""
    text = re.sub(r"\r\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def truncate_for_preview(text: str, max_chars: int = 300) -> str:
    """Return a short preview of text."""
    if len(text) <= max_chars:
        return text
    return text[:max_chars].rstrip() + "…"


def word_count(text: str) -> int:
    """Count words in text."""
    return len(text.split())


def char_count(text: str) -> int:
    """Count characters excluding whitespace."""
    return len(text.replace(" ", "").replace("\n", ""))


def sentence_split(text: str) -> list[str]:
    """Split text into sentences using a simple regex approach."""
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    return [s for s in sentences if s.strip()]


def validate_api_key(api_key: Optional[str]) -> bool:
    """Basic format check for a Gemini API key."""
    if not api_key:
        return False
    return len(api_key.strip()) > 10


def format_score(score: float, decimals: int = 1) -> str:
    """Format a numeric score for display."""
    return f"{score:.{decimals}f}"
