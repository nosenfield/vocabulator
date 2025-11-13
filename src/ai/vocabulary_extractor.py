"""Vocabulary extraction from student text using OpenAI.

This module provides functionality to extract vocabulary from student
transcripts and writing samples using OpenAI GPT models.
"""

import json
import re
from typing import Dict, List, Optional

from src.ai.cost_tracker import OperationType
from src.ai.openai_client import OpenAIClient, OpenAIError
from src.ai.prompts.extraction import (
    build_batch_extraction_prompt,
    build_extraction_prompt,
)
from src.processing.text_analyzer import (
    chunk_text,
    clean_text,
    estimate_word_count,
    hash_text,
)
from src.utils.logger import get_logger

logger = get_logger("ai.vocabulary_extractor")


class ExtractedWord:
    """Represents a single extracted vocabulary word."""

    def __init__(
        self,
        word: str,
        count: int,
        example: str,
        context_sentences: Optional[List[str]] = None,
    ):
        """Initialize extracted word.

        Args:
            word: Word in lemmatized form
            count: Number of times word appears
            example: Example sentence showing usage
            context_sentences: Additional context sentences
        """
        self.word = word.lower().strip()
        self.count = count
        self.example = example
        self.context_sentences = context_sentences or []

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "word": self.word,
            "count": self.count,
            "example": self.example,
            "context_sentences": self.context_sentences,
        }

    def __eq__(self, other):
        """Equality comparison (by word)."""
        if not isinstance(other, ExtractedWord):
            return False
        return self.word == other.word

    def __hash__(self):
        """Hash by word."""
        return hash(self.word)


class VocabularyExtractor:
    """Extract vocabulary from student text using OpenAI."""

    def __init__(
        self,
        openai_client: Optional[OpenAIClient] = None,
        model: str = "gpt-4o-mini",
        temperature: float = 0.3,
    ):
        """Initialize vocabulary extractor.

        Args:
            openai_client: OpenAI client instance (creates new if None)
            model: Model to use for extraction (default: gpt-4o-mini)
            temperature: Sampling temperature (default: 0.3 for consistency)
        """
        self.client = openai_client or OpenAIClient()
        self.model = model
        self.temperature = temperature
        self._cache: Dict[str, List[ExtractedWord]] = {}

    async def extract(
        self,
        text: str,
        use_cache: bool = True,
        request_id: Optional[str] = None,
    ) -> List[ExtractedWord]:
        """Extract vocabulary from text.

        Args:
            text: Student text to extract vocabulary from
            use_cache: Whether to use cached results for identical text
            request_id: Optional request ID for correlation

        Returns:
            List of extracted vocabulary words

        Raises:
            OpenAIError: If extraction fails
        """
        if not text or not text.strip():
            logger.warning("Empty text provided for extraction")
            return []

        # Clean text
        cleaned_text = clean_text(text)
        word_count = estimate_word_count(cleaned_text)

        logger.info(
            f"Extracting vocabulary from text",
            extra={
                "word_count": word_count,
                "request_id": request_id,
            },
        )

        # Check cache
        if use_cache:
            text_hash = hash_text(cleaned_text)
            if text_hash in self._cache:
                logger.debug(
                    f"Using cached extraction result",
                    extra={"request_id": request_id},
                )
                return self._cache[text_hash]

        # Chunk text if too long
        chunks = chunk_text(cleaned_text)
        all_words: Dict[str, ExtractedWord] = {}

        # Process each chunk
        for i, chunk in enumerate(chunks):
            try:
                words = await self._extract_from_chunk(
                    chunk, request_id=f"{request_id}-chunk{i}" if request_id else None
                )

                # Merge words (combine counts for duplicates)
                for word in words:
                    if word.word in all_words:
                        # Combine counts and examples
                        existing = all_words[word.word]
                        existing.count += word.count
                        if word.example and word.example not in existing.context_sentences:
                            existing.context_sentences.append(word.example)
                    else:
                        all_words[word.word] = word

            except OpenAIError as e:
                logger.error(
                    f"Failed to extract vocabulary from chunk {i+1}",
                    extra={
                        "chunk": i + 1,
                        "total_chunks": len(chunks),
                        "error": str(e),
                        "request_id": request_id,
                    },
                )
                # Continue with other chunks
                continue

        result = list(all_words.values())

        # Cache result
        if use_cache:
            text_hash = hash_text(cleaned_text)
            self._cache[text_hash] = result

        logger.info(
            f"Extracted {len(result)} unique vocabulary words",
            extra={
                "word_count": word_count,
                "unique_words": len(result),
                "request_id": request_id,
            },
        )

        return result

    async def _extract_from_chunk(
        self, chunk: str, request_id: Optional[str] = None
    ) -> List[ExtractedWord]:
        """Extract vocabulary from a single chunk.

        Args:
            chunk: Text chunk to process
            request_id: Optional request ID

        Returns:
            List of extracted words

        Raises:
            OpenAIError: If extraction fails
        """
        # Build prompt
        messages = build_extraction_prompt(chunk)

        # Call OpenAI API
        response = await self.client.complete(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
            max_tokens=2000,  # Sufficient for vocabulary list
            operation_type=OperationType.EXTRACTION,
            request_id=request_id,
        )

        # Parse JSON response
        words = self._parse_response(response)

        return words

    def _parse_response(self, response: str) -> List[ExtractedWord]:
        """Parse OpenAI API response into ExtractedWord objects.

        Args:
            response: JSON response string from OpenAI

        Returns:
            List of ExtractedWord objects

        Raises:
            ValueError: If response cannot be parsed
        """
        if not response or not response.strip():
            logger.warning("Empty response from OpenAI API")
            return []

        # Try to extract JSON from response (handle markdown code blocks)
        json_match = re.search(r"\{[\s\S]*\}", response)
        if json_match:
            json_str = json_match.group(0)
        else:
            json_str = response

        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as e:
            logger.error(
                f"Failed to parse OpenAI response as JSON",
                extra={"response_preview": response[:200], "error": str(e)},
            )
            raise ValueError(f"Invalid JSON response from OpenAI: {e}") from e

        # Extract words
        if not isinstance(data, dict) or "words" not in data:
            logger.warning("Response missing 'words' key")
            return []

        words_list = data.get("words", [])
        if not isinstance(words_list, list):
            logger.warning("'words' is not a list")
            return []

        extracted_words = []

        for word_data in words_list:
            if not isinstance(word_data, dict):
                continue

            word = word_data.get("word", "").strip()
            if not word:
                continue

            count = word_data.get("count", 1)
            if not isinstance(count, int) or count < 1:
                count = 1

            example = word_data.get("example", "").strip()
            if not example:
                example = f"Example usage of '{word}'"

            extracted_words.append(
                ExtractedWord(
                    word=word,
                    count=count,
                    example=example,
                )
            )

        return extracted_words

    async def extract_batch(
        self,
        texts: List[str],
        request_id: Optional[str] = None,
    ) -> List[ExtractedWord]:
        """Extract vocabulary from multiple texts in a single API call.

        Args:
            texts: List of texts to extract vocabulary from
            request_id: Optional request ID

        Returns:
            Combined list of extracted words (deduplicated)
        """
        if not texts:
            return []

        # Filter empty texts
        valid_texts = [clean_text(t) for t in texts if t and t.strip()]
        if not valid_texts:
            return []

        # Build batch prompt
        messages = build_batch_extraction_prompt(valid_texts)

        # Call OpenAI API
        response = await self.client.complete(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
            max_tokens=4000,  # More tokens for batch processing
            operation_type=OperationType.EXTRACTION,
            request_id=request_id,
        )

        # Parse response
        words = self._parse_response(response)

        logger.info(
            f"Extracted vocabulary from {len(valid_texts)} texts",
            extra={
                "texts_processed": len(valid_texts),
                "unique_words": len(words),
                "request_id": request_id,
            },
        )

        return words

    def clear_cache(self):
        """Clear extraction cache."""
        self._cache.clear()
        logger.debug("Extraction cache cleared")

