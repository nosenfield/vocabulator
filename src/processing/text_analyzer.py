"""Text preprocessing and analysis utilities.

This module provides utilities for preprocessing student text before
vocabulary extraction, including chunking, cleaning, and normalization.
"""

import hashlib
import re
from typing import List, Optional

from src.utils.logger import get_logger

logger = get_logger("processing.text_analyzer")

# Common stopwords to filter (basic set - OpenAI will also filter)
COMMON_STOPWORDS = {
    "the",
    "a",
    "an",
    "and",
    "or",
    "but",
    "in",
    "on",
    "at",
    "to",
    "for",
    "of",
    "with",
    "by",
    "from",
    "as",
    "is",
    "are",
    "was",
    "were",
    "be",
    "been",
    "being",
    "have",
    "has",
    "had",
    "do",
    "does",
    "did",
    "will",
    "would",
    "could",
    "should",
    "may",
    "might",
    "can",
    "must",
    "this",
    "that",
    "these",
    "those",
    "i",
    "you",
    "he",
    "she",
    "it",
    "we",
    "they",
    "what",
    "which",
    "who",
    "when",
    "where",
    "why",
    "how",
}

# Maximum words per chunk (for long texts)
MAX_WORDS_PER_CHUNK = 2000


def clean_text(text: str) -> str:
    """Clean and normalize text for processing.

    Args:
        text: Raw text input

    Returns:
        Cleaned text with normalized whitespace
    """
    if not text or not isinstance(text, str):
        return ""

    # Normalize whitespace
    text = re.sub(r"\s+", " ", text)

    # Remove leading/trailing whitespace
    text = text.strip()

    return text


def estimate_word_count(text: str) -> int:
    """Estimate word count in text.

    Args:
        text: Text to count words in

    Returns:
        Estimated word count
    """
    if not text:
        return 0

    # Simple word count (split on whitespace)
    words = text.split()
    return len(words)


def chunk_text(text: str, max_words: int = MAX_WORDS_PER_CHUNK) -> List[str]:
    """Split long text into chunks for processing.

    Args:
        text: Text to chunk
        max_words: Maximum words per chunk

    Returns:
        List of text chunks
    """
    if not text:
        return []

    cleaned = clean_text(text)
    word_count = estimate_word_count(cleaned)

    # If text is short enough, return as single chunk
    if word_count <= max_words:
        return [cleaned]

    # Split into chunks
    words = cleaned.split()
    chunks = []

    for i in range(0, len(words), max_words):
        chunk = " ".join(words[i : i + max_words])
        chunks.append(chunk)

    logger.debug(
        f"Chunked text into {len(chunks)} chunks",
        extra={"word_count": word_count, "chunks": len(chunks)},
    )

    return chunks


def normalize_word(word: str) -> Optional[str]:
    """Normalize a word for comparison.

    Args:
        word: Word to normalize

    Returns:
        Normalized word (lowercase, stripped), or None if invalid
    """
    if not word or not isinstance(word, str):
        return None

    # Convert to lowercase and strip
    normalized = word.lower().strip()

    # Remove punctuation at start/end (keep internal punctuation like "don't")
    normalized = re.sub(r"^[^\w]+|[^\w]+$", "", normalized)

    # Skip if empty after normalization
    if not normalized:
        return None

    # Skip if it's a stopword
    if normalized in COMMON_STOPWORDS:
        return None

    # Skip if it's a number
    if normalized.isdigit():
        return None

    return normalized


def hash_text(text: str) -> str:
    """Generate hash of text for caching.

    Args:
        text: Text to hash

    Returns:
        MD5 hash of text
    """
    return hashlib.md5(text.encode("utf-8")).hexdigest()


def extract_sentences_with_word(text: str, word: str) -> List[str]:
    """Extract sentences containing a specific word.

    Args:
        text: Text to search in
        word: Word to find sentences for

    Returns:
        List of sentences containing the word
    """
    if not text or not word:
        return []

    # Split into sentences (simple approach - split on . ! ?)
    sentences = re.split(r"[.!?]+", text)

    # Find sentences containing the word (case-insensitive)
    matching_sentences = []
    word_lower = word.lower()

    for sentence in sentences:
        sentence = sentence.strip()
        if sentence and word_lower in sentence.lower():
            matching_sentences.append(sentence)

    return matching_sentences[:3]  # Return up to 3 sentences

