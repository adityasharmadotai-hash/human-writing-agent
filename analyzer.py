"""Analyze writing quality and human-likeness of text."""

import logging
import re
import math
from collections import Counter
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class AnalysisResult:
    human_likeness_score: float       # 0–100
    vocabulary_diversity: float        # 0–100 (type-token ratio normalised)
    sentence_variety: float            # 0–100
    readability_score: float           # 0–100 (mapped from Flesch)
    repetition_score: float            # 0–100 (higher = less repetition = better)
    explanation: str                   # Human-readable reason
    word_count: int
    sentence_count: int
    avg_sentence_length: float


def _split_sentences(text: str) -> list[str]:
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    return [s for s in sentences if len(s.split()) >= 3]


def _tokenize_words(text: str) -> list[str]:
    return re.findall(r"\b[a-zA-Z']+\b", text.lower())


def _vocabulary_diversity(words: list[str]) -> float:
    """
    Measure of lexical richness. We use an approximation of MTLD
    via a simple type-token ratio over rolling windows, mapped to 0-100.
    For short texts we use raw TTR.
    """
    if not words:
        return 0.0
    unique = len(set(words))
    total = len(words)
    if total <= 50:
        ttr = unique / total
        return round(min(ttr * 130, 100), 1)  # scale so ~0.75 TTR → ~97
    # For longer text use MATTR (Moving Average TTR) window=50
    window = 50
    ttrs = []
    for i in range(0, total - window + 1, 1):
        chunk = words[i : i + window]
        ttrs.append(len(set(chunk)) / window)
    mattr = sum(ttrs) / len(ttrs) if ttrs else unique / total
    return round(min(mattr * 145, 100), 1)


def _sentence_variety(sentences: list[str]) -> float:
    """
    Score based on variance in sentence length (words).
    High variance → more variety → higher score.
    """
    if len(sentences) < 2:
        return 50.0
    lengths = [len(s.split()) for s in sentences]
    mean = sum(lengths) / len(lengths)
    variance = sum((l - mean) ** 2 for l in lengths) / len(lengths)
    std_dev = math.sqrt(variance)
    # Typical human academic writing: std_dev around 8-15 words
    score = min(std_dev / 0.18, 100)  # 18 std_dev → 100
    return round(score, 1)


def _flesch_readability(text: str, words: list[str], sentences: list[str]) -> float:
    """Return Flesch Reading Ease score, mapped to 0-100 human-likeness proxy."""
    try:
        import textstat
        score = textstat.flesch_reading_ease(text)
        # Academic text typically scores 30-60; we map 0-100 range to 0-100
        # Penalise extremes (very simple OR unreadable)
        if score < 0:
            score = 0.0
        mapped = max(0.0, min(100.0, score))
        return round(mapped, 1)
    except Exception:
        # Fallback: approximate
        if not sentences or not words:
            return 50.0
        avg_sent_len = len(words) / len(sentences)
        syllables = sum(_count_syllables(w) for w in words)
        avg_syllables = syllables / len(words)
        flesch = 206.835 - 1.015 * avg_sent_len - 84.6 * avg_syllables
        return round(max(0.0, min(100.0, flesch)), 1)


def _count_syllables(word: str) -> int:
    """Rough syllable count for a single word."""
    word = word.lower()
    count = len(re.findall(r"[aeiou]+", word))
    if word.endswith("e") and count > 1:
        count -= 1
    return max(1, count)


def _repetition_score(words: list[str]) -> float:
    """
    Score based on how non-repetitive the text is.
    Filters stop words. Returns 0–100 (100 = minimal repetition).
    """
    STOP_WORDS = {
        "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
        "of", "with", "by", "from", "is", "are", "was", "were", "be", "been",
        "being", "have", "has", "had", "do", "does", "did", "will", "would",
        "could", "should", "may", "might", "shall", "can", "this", "that",
        "these", "those", "it", "its", "as", "not", "also", "which", "who",
        "what", "when", "where", "how", "all", "both", "each", "their",
        "they", "we", "i", "you", "he", "she", "our", "your", "my",
    }
    content_words = [w for w in words if w not in STOP_WORDS and len(w) > 3]
    if not content_words:
        return 80.0
    counter = Counter(content_words)
    total = len(content_words)
    # Ratio of words appearing more than twice
    repetitive = sum(count - 1 for count in counter.values() if count > 2)
    repetition_ratio = repetitive / total if total else 0
    score = max(0.0, 100.0 - repetition_ratio * 250)
    return round(min(score, 100.0), 1)


def _build_explanation(
    human_score: float,
    vocab: float,
    variety: float,
    readability: float,
    repetition: float,
) -> str:
    parts = []

    if human_score >= 80:
        parts.append("The text reads naturally and demonstrates strong markers of human academic authorship.")
    elif human_score >= 60:
        parts.append("The text reads reasonably well and shows several human writing characteristics.")
    elif human_score >= 40:
        parts.append("The text has some natural qualities but retains patterns common in AI-generated content.")
    else:
        parts.append("The text shows strong signs of templated or formulaic writing.")

    # Vocabulary note
    if vocab >= 75:
        parts.append("Lexical diversity is high, suggesting a broad and varied vocabulary.")
    elif vocab < 50:
        parts.append("Vocabulary diversity is limited, with repeated word choices across the passage.")

    # Sentence variety note
    if variety >= 70:
        parts.append("Sentence lengths vary considerably, creating a natural reading rhythm.")
    elif variety < 40:
        parts.append("Sentence lengths are notably uniform, which can feel mechanical.")

    # Repetition note
    if repetition < 55:
        parts.append("Several content words recur more often than typical in polished academic prose.")

    return " ".join(parts)


def analyze_text(text: str, gemini_explanation: Optional[str] = None) -> AnalysisResult:
    """
    Run all metrics and return an AnalysisResult.
    If gemini_explanation is provided it replaces the auto-generated one.
    """
    words = _tokenize_words(text)
    sentences = _split_sentences(text)

    vocab = _vocabulary_diversity(words)
    variety = _sentence_variety(sentences)
    readability = _flesch_readability(text, words, sentences)
    repetition = _repetition_score(words)

    # Weighted composite
    human_score = round(
        0.30 * vocab
        + 0.25 * variety
        + 0.25 * repetition
        + 0.20 * min(readability, 100),
        1,
    )
    human_score = max(0.0, min(100.0, human_score))

    avg_sent_len = (len(words) / len(sentences)) if sentences else 0.0

    explanation = gemini_explanation or _build_explanation(
        human_score, vocab, variety, readability, repetition
    )

    return AnalysisResult(
        human_likeness_score=human_score,
        vocabulary_diversity=vocab,
        sentence_variety=variety,
        readability_score=readability,
        repetition_score=repetition,
        explanation=explanation,
        word_count=len(words),
        sentence_count=len(sentences),
        avg_sentence_length=round(avg_sent_len, 1),
    )
