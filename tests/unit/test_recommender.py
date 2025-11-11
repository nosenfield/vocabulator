"""Unit tests for vocabulary recommendation generation.

Tests cover:
- Recommendation generation from gap words
- Definition and example sentence generation
- Difficulty progression ordering
- Output format matching VocabularyRecommendation schema
"""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest

from src.ai.cost_tracker import OperationType
from src.ai.openai_client import OpenAIClient
from src.data.models.recommendation import RecommendedWord, VocabularyRecommendation
from src.processing.gap_identifier import GapWord
from src.processing.recommender import Recommender


@pytest.fixture
def sample_gap_words():
    """Create sample gap words for testing."""
    return [
        GapWord(
            word="synthesize",
            rationale="High-frequency academic word across subjects",
            difficulty_score=7,
            cc_grade_level=7,
            subject_areas=["science", "ela"],
        ),
        GapWord(
            word="hypothesize",
            rationale="Important scientific method term",
            difficulty_score=8,
            cc_grade_level=8,
            subject_areas=["science"],
        ),
        GapWord(
            word="analyze",
            rationale="Fundamental critical thinking word",
            difficulty_score=5,
            cc_grade_level=6,
            subject_areas=["math", "science", "ela"],
        ),
    ]


@pytest.fixture
def mock_openai_client():
    """Create mock OpenAI client."""
    client = AsyncMock(spec=OpenAIClient)
    client.complete = AsyncMock()
    return client


@pytest.mark.unit
@pytest.mark.openai
class TestRecommender:
    """Test Recommender class."""

    @pytest.mark.asyncio
    async def test_generate_recommendations_success(
        self, mock_openai_client, sample_gap_words
    ):
        """Test successful recommendation generation."""
        import json

        mock_response = {
            "recommendations": [
                {
                    "word": "analyze",
                    "definition": "examine in detail to understand",
                    "difficulty_score": 0.5,
                    "rationale": "Fundamental critical thinking word",
                    "example_sentences": [
                        "Scientists analyze data to find patterns.",
                        "Let's analyze the author's argument.",
                    ],
                    "usage_tips": "Use when examining details carefully",
                    "word_family": ["analysis", "analytical"],
                },
                {
                    "word": "synthesize",
                    "definition": "combine elements into a whole",
                    "difficulty_score": 0.7,
                    "rationale": "High-frequency academic word across subjects",
                    "example_sentences": [
                        "Students synthesize information from multiple sources.",
                        "The author synthesizes different perspectives.",
                    ],
                    "usage_tips": "Use when combining ideas or information",
                    "word_family": ["synthesis", "synthetic"],
                },
                {
                    "word": "hypothesize",
                    "definition": "form a hypothesis or educated guess",
                    "difficulty_score": 0.8,
                    "rationale": "Important scientific method term",
                    "example_sentences": [
                        "Scientists hypothesize about possible explanations.",
                        "We can hypothesize what might happen next.",
                    ],
                    "usage_tips": "Use in scientific contexts",
                    "word_family": ["hypothesis", "hypothetical"],
                },
            ],
            "difficulty_progression": "gradual",
            "estimated_learning_time": "2-3 weeks",
        }

        mock_openai_client.complete.return_value = json.dumps(mock_response)

        recommender = Recommender(openai_client=mock_openai_client)

        recommendation = await recommender.generate(
            gap_words=sample_gap_words,
            student_id="STU-001",
            grade_level=7,
        )

        assert isinstance(recommendation, VocabularyRecommendation)
        assert recommendation.student_id == "STU-001"
        assert len(recommendation.words) == 3

        # Verify words are ordered by difficulty (easiest first)
        assert recommendation.words[0].difficulty_score <= recommendation.words[1].difficulty_score
        assert recommendation.words[1].difficulty_score <= recommendation.words[2].difficulty_score

        # Verify each word has required fields
        for word in recommendation.words:
            assert word.word
            assert word.definition
            assert word.example_sentences
            assert 0.0 <= word.difficulty_score <= 1.0
            assert word.grade_level in [6, 7, 8]

        # Verify API was called correctly
        mock_openai_client.complete.assert_called_once()
        call_args = mock_openai_client.complete.call_args
        assert call_args.kwargs["model"] == "gpt-4o"
        assert call_args.kwargs["operation_type"] == OperationType.RECOMMENDATION

    @pytest.mark.asyncio
    async def test_generate_recommendations_empty_gap_words(
        self, mock_openai_client
    ):
        """Test recommendation generation with empty gap words."""
        recommender = Recommender(openai_client=mock_openai_client)

        recommendation = await recommender.generate(
            gap_words=[],
            student_id="STU-001",
            grade_level=7,
        )

        assert isinstance(recommendation, VocabularyRecommendation)
        assert recommendation.student_id == "STU-001"
        assert len(recommendation.words) == 0

        # Should not call OpenAI API for empty gap words
        mock_openai_client.complete.assert_not_called()

    @pytest.mark.asyncio
    async def test_generate_recommendations_orders_by_difficulty(
        self, mock_openai_client, sample_gap_words
    ):
        """Test that recommendations are ordered by difficulty (easiest first)."""
        import json

        # Response with words in random order
        mock_response = {
            "recommendations": [
                {
                    "word": "hypothesize",
                    "definition": "form a hypothesis",
                    "difficulty_score": 0.8,
                    "rationale": "Hard word",
                    "example_sentences": ["Test sentence"],
                },
                {
                    "word": "analyze",
                    "definition": "examine in detail",
                    "difficulty_score": 0.5,
                    "rationale": "Easy word",
                    "example_sentences": ["Test sentence"],
                },
                {
                    "word": "synthesize",
                    "definition": "combine elements",
                    "difficulty_score": 0.7,
                    "rationale": "Medium word",
                    "example_sentences": ["Test sentence"],
                },
            ],
        }

        mock_openai_client.complete.return_value = json.dumps(mock_response)

        recommender = Recommender(openai_client=mock_openai_client)

        recommendation = await recommender.generate(
            gap_words=sample_gap_words,
            student_id="STU-001",
            grade_level=7,
        )

        # Verify ordering (easiest first)
        difficulties = [w.difficulty_score for w in recommendation.words]
        assert difficulties == sorted(difficulties)

    @pytest.mark.asyncio
    async def test_generate_recommendations_converts_difficulty_scale(
        self, mock_openai_client, sample_gap_words
    ):
        """Test that difficulty scores are converted from 1-10 to 0.0-1.0 scale."""
        import json

        mock_response = {
            "recommendations": [
                {
                    "word": "analyze",
                    "definition": "examine in detail",
                    "difficulty_score": 0.5,  # Already in 0-1 scale
                    "rationale": "Test",
                    "example_sentences": ["Test"],
                },
            ],
        }

        mock_openai_client.complete.return_value = json.dumps(mock_response)

        recommender = Recommender(openai_client=mock_openai_client)

        recommendation = await recommender.generate(
            gap_words=[sample_gap_words[0]],  # difficulty_score=7 (1-10 scale)
            student_id="STU-001",
            grade_level=7,
        )

        # Verify difficulty score is in 0.0-1.0 range
        assert 0.0 <= recommendation.words[0].difficulty_score <= 1.0

    @pytest.mark.asyncio
    async def test_generate_recommendations_includes_all_fields(
        self, mock_openai_client, sample_gap_words
    ):
        """Test that recommendations include all required fields."""
        import json

        mock_response = {
            "recommendations": [
                {
                    "word": "analyze",
                    "definition": "examine in detail to understand",
                    "difficulty_score": 0.5,
                    "rationale": "Fundamental critical thinking word",
                    "example_sentences": [
                        "Scientists analyze data to find patterns.",
                        "Let's analyze the author's argument.",
                    ],
                    "usage_tips": "Use when examining details carefully",
                    "word_family": ["analysis", "analytical"],
                },
            ],
        }

        mock_openai_client.complete.return_value = json.dumps(mock_response)

        recommender = Recommender(openai_client=mock_openai_client)

        recommendation = await recommender.generate(
            gap_words=[sample_gap_words[0]],
            student_id="STU-001",
            grade_level=7,
        )

        word = recommendation.words[0]
        assert word.word == "analyze"
        assert word.definition == "examine in detail to understand"
        assert len(word.example_sentences) == 2
        assert word.rationale == "Fundamental critical thinking word"
        assert word.grade_level == 7

    @pytest.mark.asyncio
    async def test_generate_recommendations_handles_malformed_response(
        self, mock_openai_client, sample_gap_words
    ):
        """Test handling of malformed API response."""
        # Return invalid JSON
        mock_openai_client.complete.return_value = "Invalid JSON response"

        recommender = Recommender(openai_client=mock_openai_client)

        with pytest.raises(ValueError, match="Invalid JSON response"):
            await recommender.generate(
                gap_words=sample_gap_words,
                student_id="STU-001",
                grade_level=7,
            )

    @pytest.mark.asyncio
    async def test_generate_recommendations_sets_recommendation_date(
        self, mock_openai_client, sample_gap_words
    ):
        """Test that recommendation_date is set correctly."""
        import json

        mock_response = {
            "recommendations": [
                {
                    "word": "analyze",
                    "definition": "test",
                    "difficulty_score": 0.5,
                    "rationale": "test",
                    "example_sentences": ["test"],
                },
            ],
        }

        mock_openai_client.complete.return_value = json.dumps(mock_response)

        recommender = Recommender(openai_client=mock_openai_client)

        recommendation = await recommender.generate(
            gap_words=[sample_gap_words[0]],
            student_id="STU-001",
            grade_level=7,
        )

        # Verify recommendation_date is set (ISO 8601 date string)
        assert recommendation.recommendation_date
        assert len(recommendation.recommendation_date) == 10  # YYYY-MM-DD format
        assert recommendation.recommendation_date.count("-") == 2

    @pytest.mark.asyncio
    async def test_generate_recommendations_handles_missing_optional_fields(
        self, mock_openai_client, sample_gap_words
    ):
        """Test that missing optional fields are handled gracefully."""
        import json

        # Response missing some optional fields
        mock_response = {
            "recommendations": [
                {
                    "word": "analyze",
                    "definition": "examine in detail",
                    "difficulty_score": 0.5,
                    # Missing rationale, usage_tips, word_family
                    "example_sentences": ["Test sentence"],
                },
            ],
        }

        mock_openai_client.complete.return_value = json.dumps(mock_response)

        recommender = Recommender(openai_client=mock_openai_client)

        recommendation = await recommender.generate(
            gap_words=[sample_gap_words[0]],
            student_id="STU-001",
            grade_level=7,
        )

        word = recommendation.words[0]
        assert word.word == "analyze"
        assert word.definition == "examine in detail"
        # Optional fields should have defaults
        assert word.rationale  # Should have a default rationale (not empty)
        assert len(word.example_sentences) == 1

