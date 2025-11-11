"""Unit tests for vocabulary extraction.

Tests cover:
- Text preprocessing (cleaning, chunking)
- Vocabulary extraction from sample texts
- Response parsing
- Error handling
- Batch extraction
"""

import json
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from src.ai.cost_tracker import OperationType
from src.ai.openai_client import OpenAIClient
from src.ai.prompts.extraction import (
    build_batch_extraction_prompt,
    build_extraction_prompt,
)
from src.ai.vocabulary_extractor import ExtractedWord, VocabularyExtractor
from src.processing.text_analyzer import (
    chunk_text,
    clean_text,
    estimate_word_count,
    extract_sentences_with_word,
    hash_text,
    normalize_word,
)
from tests.mocks.mock_openai import MockChatCompletion


@pytest.fixture
def sample_transcript():
    """Load sample transcript."""
    transcript_path = Path(__file__).parent.parent / "fixtures" / "sample_transcripts" / "student_001.txt"
    if transcript_path.exists():
        return transcript_path.read_text()
    return "Today we learned about photosynthesis and analyzed data from experiments."


@pytest.fixture
def mock_openai_response():
    """Mock OpenAI API response."""
    return json.dumps({
        "words": [
            {
                "word": "photosynthesis",
                "count": 2,
                "example": "Photosynthesis is the process where plants convert sunlight into energy."
            },
            {
                "word": "analyze",
                "count": 1,
                "example": "We analyzed data from the experiment."
            },
            {
                "word": "experiment",
                "count": 3,
                "example": "During the experiment, we observed plant growth."
            }
        ]
    })


@pytest.fixture
def mock_openai_client():
    """Create mock OpenAI client."""
    client = AsyncMock(spec=OpenAIClient)
    client.complete = AsyncMock()
    return client


@pytest.mark.unit
@pytest.mark.openai
class TestTextAnalyzer:
    """Test text preprocessing utilities."""

    def test_clean_text(self):
        """Test text cleaning."""
        text = "  This   is   a   test  \n\n  with   multiple   spaces  "
        cleaned = clean_text(text)
        assert cleaned == "This is a test with multiple spaces"

    def test_clean_text_empty(self):
        """Test cleaning empty text."""
        assert clean_text("") == ""
        assert clean_text(None) == ""
        assert clean_text("   ") == ""

    def test_estimate_word_count(self):
        """Test word count estimation."""
        text = "This is a test with five words"
        assert estimate_word_count(text) == 7

    def test_estimate_word_count_empty(self):
        """Test word count for empty text."""
        assert estimate_word_count("") == 0
        assert estimate_word_count("   ") == 0

    def test_chunk_text_short(self):
        """Test chunking short text."""
        text = "This is a short text."
        chunks = chunk_text(text, max_words=10)
        assert len(chunks) == 1
        assert chunks[0] == text.strip()

    def test_chunk_text_long(self):
        """Test chunking long text."""
        # Create long text (3000 words)
        words = ["word"] * 3000
        long_text = " ".join(words)

        chunks = chunk_text(long_text, max_words=1000)
        assert len(chunks) == 3
        assert all(len(chunk.split()) <= 1000 for chunk in chunks)

    def test_normalize_word(self):
        """Test word normalization."""
        assert normalize_word("Analyze") == "analyze"
        assert normalize_word("  PHOTOSYNTHESIS  ") == "photosynthesis"
        assert normalize_word("the") is None  # Stopword
        assert normalize_word("123") is None  # Number
        assert normalize_word("") is None  # Empty

    def test_hash_text(self):
        """Test text hashing."""
        text1 = "This is a test"
        text2 = "This is a test"
        text3 = "This is different"

        hash1 = hash_text(text1)
        hash2 = hash_text(text2)
        hash3 = hash_text(text3)

        assert hash1 == hash2
        assert hash1 != hash3
        assert len(hash1) == 32  # MD5 hash length

    def test_extract_sentences_with_word(self):
        """Test sentence extraction."""
        text = "Photosynthesis is important. We learned about it. Plants use photosynthesis."
        sentences = extract_sentences_with_word(text, "photosynthesis")
        assert len(sentences) > 0
        assert all("photosynthesis" in s.lower() for s in sentences)


@pytest.mark.unit
@pytest.mark.openai
class TestExtractionPrompts:
    """Test prompt building."""

    def test_build_extraction_prompt(self):
        """Test building extraction prompt."""
        text = "This is a test."
        messages = build_extraction_prompt(text)

        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        assert messages[1]["role"] == "user"
        assert text in messages[1]["content"]

    def test_build_batch_extraction_prompt(self):
        """Test building batch extraction prompt."""
        texts = ["Text one.", "Text two.", "Text three."]
        messages = build_batch_extraction_prompt(texts)

        assert len(messages) == 2
        assert "3" in messages[1]["content"]  # Number of texts
        assert all(text in messages[1]["content"] for text in texts)


@pytest.mark.unit
@pytest.mark.openai
class TestExtractedWord:
    """Test ExtractedWord class."""

    def test_create_extracted_word(self):
        """Test creating extracted word."""
        word = ExtractedWord(
            word="analyze",
            count=3,
            example="We need to analyze the data.",
        )

        assert word.word == "analyze"
        assert word.count == 3
        assert word.example == "We need to analyze the data."
        assert word.context_sentences == []

    def test_to_dict(self):
        """Test converting to dictionary."""
        word = ExtractedWord(
            word="photosynthesis",
            count=2,
            example="Plants use photosynthesis.",
            context_sentences=["Sentence 1", "Sentence 2"],
        )

        word_dict = word.to_dict()
        assert word_dict["word"] == "photosynthesis"
        assert word_dict["count"] == 2
        assert word_dict["example"] == "Plants use photosynthesis."
        assert len(word_dict["context_sentences"]) == 2

    def test_equality(self):
        """Test word equality."""
        word1 = ExtractedWord("analyze", 1, "Example 1")
        word2 = ExtractedWord("analyze", 2, "Example 2")
        word3 = ExtractedWord("photosynthesis", 1, "Example 3")

        assert word1 == word2  # Same word
        assert word1 != word3  # Different word


@pytest.mark.unit
@pytest.mark.openai
class TestVocabularyExtractor:
    """Test VocabularyExtractor class."""

    @pytest.mark.asyncio
    async def test_extract_success(self, mock_openai_client, mock_openai_response, sample_transcript):
        """Test successful vocabulary extraction."""
        # Setup mock
        mock_openai_client.complete.return_value = mock_openai_response

        extractor = VocabularyExtractor(openai_client=mock_openai_client)

        words = await extractor.extract(sample_transcript)

        assert len(words) == 3
        assert any(w.word == "photosynthesis" for w in words)
        assert any(w.word == "analyze" for w in words)
        assert any(w.word == "experiment" for w in words)

        # Verify API was called correctly
        mock_openai_client.complete.assert_called_once()
        call_args = mock_openai_client.complete.call_args
        assert call_args.kwargs["model"] == "gpt-4o-mini"
        assert call_args.kwargs["operation_type"] == OperationType.EXTRACTION
        assert call_args.kwargs["temperature"] == 0.3

    @pytest.mark.asyncio
    async def test_extract_empty_text(self, mock_openai_client):
        """Test extraction from empty text."""
        extractor = VocabularyExtractor(openai_client=mock_openai_client)

        words = await extractor.extract("")

        assert words == []
        mock_openai_client.complete.assert_not_called()

    @pytest.mark.asyncio
    async def test_extract_with_cache(self, mock_openai_client, mock_openai_response, sample_transcript):
        """Test extraction caching."""
        mock_openai_client.complete.return_value = mock_openai_response

        extractor = VocabularyExtractor(openai_client=mock_openai_client)

        # First extraction
        words1 = await extractor.extract(sample_transcript, use_cache=True)
        assert len(words1) == 3

        # Second extraction (should use cache)
        words2 = await extractor.extract(sample_transcript, use_cache=True)
        assert len(words2) == 3

        # Should only call API once
        assert mock_openai_client.complete.call_count == 1

    @pytest.mark.asyncio
    async def test_extract_long_text_chunking(self, mock_openai_client, mock_openai_response):
        """Test extraction from long text (chunking)."""
        # Create long text (3000 words)
        long_text = " ".join(["word"] * 3000)

        mock_openai_client.complete.return_value = mock_openai_response

        extractor = VocabularyExtractor(openai_client=mock_openai_client)

        words = await extractor.extract(long_text)

        # Should call API multiple times (one per chunk)
        assert mock_openai_client.complete.call_count >= 2

    @pytest.mark.asyncio
    async def test_extract_batch(self, mock_openai_client, mock_openai_response):
        """Test batch extraction."""
        texts = [
            "We learned about photosynthesis.",
            "We analyzed the data carefully.",
            "The experiment showed interesting results.",
        ]

        mock_openai_client.complete.return_value = mock_openai_response

        extractor = VocabularyExtractor(openai_client=mock_openai_client)

        words = await extractor.extract_batch(texts)

        assert len(words) > 0
        mock_openai_client.complete.assert_called_once()

    @pytest.mark.asyncio
    async def test_parse_response_valid_json(self):
        """Test parsing valid JSON response."""
        extractor = VocabularyExtractor()

        response = json.dumps({
            "words": [
                {"word": "analyze", "count": 3, "example": "Example 1"},
                {"word": "photosynthesis", "count": 2, "example": "Example 2"},
            ]
        })

        words = extractor._parse_response(response)

        assert len(words) == 2
        assert words[0].word == "analyze"
        assert words[0].count == 3
        assert words[1].word == "photosynthesis"
        assert words[1].count == 2

    @pytest.mark.asyncio
    async def test_parse_response_markdown_wrapped(self):
        """Test parsing JSON wrapped in markdown."""
        extractor = VocabularyExtractor()

        response = "```json\n" + json.dumps({
            "words": [{"word": "test", "count": 1, "example": "Example"}]
        }) + "\n```"

        words = extractor._parse_response(response)

        assert len(words) == 1
        assert words[0].word == "test"

    @pytest.mark.asyncio
    async def test_parse_response_empty(self):
        """Test parsing empty response."""
        extractor = VocabularyExtractor()

        words = extractor._parse_response("")

        assert words == []

    @pytest.mark.asyncio
    async def test_parse_response_invalid_json(self):
        """Test parsing invalid JSON."""
        extractor = VocabularyExtractor()

        with pytest.raises(ValueError):
            extractor._parse_response("This is not JSON")

    def test_clear_cache(self, mock_openai_client):
        """Test clearing cache."""
        extractor = VocabularyExtractor(openai_client=mock_openai_client)

        # Add something to cache (by extracting)
        extractor._cache["test"] = [ExtractedWord("test", 1, "Example")]

        assert len(extractor._cache) == 1

        extractor.clear_cache()

        assert len(extractor._cache) == 0

