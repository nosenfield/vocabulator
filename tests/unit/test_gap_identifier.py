"""Unit tests for vocabulary gap identification.

Tests cover:
- ZPD (Zone of Proximal Development) calculation
- Gap identification against Common Core standards
- Difficulty scoring
- Word filtering and selection
"""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.ai.cost_tracker import OperationType
from src.ai.openai_client import OpenAIClient, OpenAIError
from src.ai.vocabulary_extractor import ExtractedWord
from src.data.models.student_profile import StudentProfile, VocabularyEntry
from src.processing.gap_identifier import GapIdentifier, GapWord
from src.vocabulary.common_core_loader import CommonCoreLoader, VocabularyWord
from tests.mocks.mock_openai import MockChatCompletion


@pytest.fixture
def sample_common_core_words():
    """Create sample Common Core vocabulary words."""
    return [
        VocabularyWord(
            word="analyze",
            grade_level=6,
            definition="examine in detail",
            subject_areas=["math", "science", "ela"],
            complexity_tier=2,
            word_family=["analysis", "analytical"],
        ),
        VocabularyWord(
            word="synthesize",
            grade_level=7,
            definition="combine elements into a whole",
            subject_areas=["science", "ela"],
            complexity_tier=3,
            word_family=["synthesis", "synthetic"],
        ),
        VocabularyWord(
            word="evaluate",
            grade_level=6,
            definition="assess or judge",
            subject_areas=["math", "ela"],
            complexity_tier=2,
            word_family=["evaluation", "evaluative"],
        ),
        VocabularyWord(
            word="hypothesize",
            grade_level=8,
            definition="form a hypothesis",
            subject_areas=["science"],
            complexity_tier=3,
            word_family=["hypothesis", "hypothetical"],
        ),
    ]


@pytest.fixture
def sample_student_profile():
    """Create sample student profile."""
    return StudentProfile(
        student_id="STU-001",
        grade_level=7,
        vocabulary_list=[
            VocabularyEntry(
                word="analyze",
                first_seen=datetime.fromisoformat("2025-01-01T00:00:00+00:00"),
                usage_count=5,
                contexts=["science", "math"],
            ),
            VocabularyEntry(
                word="evaluate",
                first_seen=datetime.fromisoformat("2025-01-01T00:00:00+00:00"),
                usage_count=3,
                contexts=["ela"],
            ),
        ],
        proficiency_score=65.0,
    )


@pytest.fixture
def sample_extracted_words():
    """Create sample extracted vocabulary words."""
    return [
        ExtractedWord(word="analyze", count=5, example="We need to analyze the data."),
        ExtractedWord(word="evaluate", count=3, example="Let's evaluate the results."),
        ExtractedWord(word="compare", count=2, example="Compare these two options."),
    ]


@pytest.fixture
def mock_openai_client():
    """Create mock OpenAI client."""
    client = AsyncMock(spec=OpenAIClient)
    client.complete = AsyncMock()
    return client


@pytest.mark.unit
@pytest.mark.openai
class TestGapWord:
    """Test GapWord dataclass."""

    def test_create_gap_word(self):
        """Test creating a gap word."""
        gap = GapWord(
            word="synthesize",
            rationale="High-frequency academic word",
            difficulty_score=7,
            cc_grade_level=7,
            subject_areas=["science", "ela"],
        )

        assert gap.word == "synthesize"
        assert gap.rationale == "High-frequency academic word"
        assert gap.difficulty_score == 7
        assert gap.cc_grade_level == 7
        assert gap.subject_areas == ["science", "ela"]

    def test_to_dict(self):
        """Test converting to dictionary."""
        gap = GapWord(
            word="analyze",
            rationale="Test rationale",
            difficulty_score=5,
            cc_grade_level=6,
            subject_areas=["math"],
        )

        gap_dict = gap.to_dict()
        assert gap_dict["word"] == "analyze"
        assert gap_dict["rationale"] == "Test rationale"
        assert gap_dict["difficulty_score"] == 5
        assert gap_dict["cc_grade_level"] == 6
        assert gap_dict["subject_areas"] == ["math"]


@pytest.mark.unit
@pytest.mark.openai
class TestGapIdentifierZPD:
    """Test ZPD (Zone of Proximal Development) logic."""

    def test_calculate_zpd_difficulty_grade_6(self):
        """Test ZPD calculation for grade 6 student."""
        identifier = GapIdentifier()

        # Student at expected level for grade 6
        min_difficulty, max_difficulty = identifier._calculate_zpd_difficulty(
            student_vocab_size=100, grade_level=6
        )

        assert min_difficulty >= 0
        assert max_difficulty >= min_difficulty
        assert max_difficulty <= 10  # Difficulty scale is 1-10

    def test_calculate_zpd_difficulty_grade_7(self):
        """Test ZPD calculation for grade 7 student."""
        identifier = GapIdentifier()

        min_difficulty, max_difficulty = identifier._calculate_zpd_difficulty(
            student_vocab_size=150, grade_level=7
        )

        assert min_difficulty >= 0
        assert max_difficulty >= min_difficulty
        assert max_difficulty <= 10

    def test_calculate_zpd_difficulty_above_average(self):
        """Test ZPD for student above average vocabulary."""
        identifier = GapIdentifier()

        # Student with large vocabulary (above average)
        min_difficulty, max_difficulty = identifier._calculate_zpd_difficulty(
            student_vocab_size=300, grade_level=7
        )

        # Should target higher difficulty
        assert min_difficulty > 0
        assert max_difficulty > min_difficulty

    def test_calculate_zpd_difficulty_below_average(self):
        """Test ZPD for student below average vocabulary."""
        identifier = GapIdentifier()

        # Student with small vocabulary (below average)
        min_difficulty, max_difficulty = identifier._calculate_zpd_difficulty(
            student_vocab_size=50, grade_level=7
        )

        # Should target lower difficulty but still challenging
        assert min_difficulty >= 0
        assert max_difficulty >= min_difficulty


@pytest.mark.unit
@pytest.mark.openai
class TestGapIdentifierFiltering:
    """Test gap identification filtering logic."""

    def test_filter_missing_words(
        self, sample_student_profile, sample_common_core_words
    ):
        """Test filtering words missing from student vocabulary."""
        identifier = GapIdentifier()

        # Student knows "analyze" and "evaluate"
        # Missing: "synthesize" and "hypothesize"
        missing = identifier._filter_missing_words(
            student_profile=sample_student_profile,
            common_core_words=sample_common_core_words,
        )

        assert len(missing) == 2
        assert any(w.word == "synthesize" for w in missing)
        assert any(w.word == "hypothesize" for w in missing)
        assert not any(w.word == "analyze" for w in missing)
        assert not any(w.word == "evaluate" for w in missing)

    def test_filter_by_difficulty_range(
        self, sample_common_core_words, sample_student_profile
    ):
        """Test filtering words by difficulty range."""
        identifier = GapIdentifier()

        # Get missing words first
        missing = identifier._filter_missing_words(
            sample_student_profile, sample_common_core_words
        )

        # Filter by difficulty range (5-8)
        filtered = identifier._filter_by_difficulty_range(missing, min_difficulty=5, max_difficulty=8)

        # Should include words within difficulty range
        assert all(
            5 <= identifier._calculate_word_difficulty(w, sample_student_profile.grade_level) <= 8
            for w in filtered
        )

    def test_calculate_word_difficulty(self, sample_student_profile):
        """Test word difficulty calculation."""
        identifier = GapIdentifier()

        # Grade 6 word for grade 7 student (easier)
        word1 = VocabularyWord(
            word="analyze",
            grade_level=6,
            definition="test",
            complexity_tier=2,
        )
        difficulty1 = identifier._calculate_word_difficulty(word1, 7)

        # Grade 8 word for grade 7 student (harder)
        word2 = VocabularyWord(
            word="hypothesize",
            grade_level=8,
            definition="test",
            complexity_tier=3,
        )
        difficulty2 = identifier._calculate_word_difficulty(word2, 7)

        # Grade 8 word should be more difficult
        assert difficulty2 > difficulty1
        assert 1 <= difficulty1 <= 10
        assert 1 <= difficulty2 <= 10


@pytest.mark.unit
@pytest.mark.openai
class TestGapIdentifierIntegration:
    """Test gap identification integration."""

    @pytest.mark.asyncio
    async def test_identify_gaps_success(
        self,
        mock_openai_client,
        sample_student_profile,
        sample_common_core_words,
        sample_extracted_words,
    ):
        """Test successful gap identification."""
        # Mock OpenAI response
        mock_response = {
            "gaps": [
                {
                    "word": "synthesize",
                    "rationale": "High-frequency academic word across subjects",
                    "difficulty_score": 7,
                    "cc_grade_level": 7,
                    "subject_areas": ["science", "ela"],
                },
                {
                    "word": "hypothesize",
                    "rationale": "Important scientific method term",
                    "difficulty_score": 8,
                    "cc_grade_level": 8,
                    "subject_areas": ["science"],
                },
            ]
        }

        import json

        mock_openai_client.complete.return_value = json.dumps(mock_response)

        identifier = GapIdentifier(
            openai_client=mock_openai_client,
            common_core_loader=CommonCoreLoader(),
        )

        # Mock loader to return sample words
        with patch.object(
            identifier,
            "_load_common_core_vocabulary",
            return_value=sample_common_core_words,
        ):
            gaps = await identifier.identify_gaps(
                extracted_words=sample_extracted_words,
                student_profile=sample_student_profile,
            )

        assert len(gaps) == 2
        assert any(g.word == "synthesize" for g in gaps)
        assert any(g.word == "hypothesize" for g in gaps)

        # Verify API was called correctly
        mock_openai_client.complete.assert_called_once()
        call_args = mock_openai_client.complete.call_args
        assert call_args.kwargs["model"] == "gpt-4o"
        assert call_args.kwargs["operation_type"] == OperationType.ANALYSIS

    @pytest.mark.asyncio
    async def test_identify_gaps_empty_extracted_words(
        self, mock_openai_client, sample_student_profile
    ):
        """Test gap identification with empty extracted words."""
        identifier = GapIdentifier(openai_client=mock_openai_client)

        gaps = await identifier.identify_gaps(
            extracted_words=[],
            student_profile=sample_student_profile,
        )

        # Should return empty list or handle gracefully
        assert isinstance(gaps, list)

    @pytest.mark.asyncio
    async def test_identify_gaps_filters_existing_words(
        self,
        mock_openai_client,
        sample_student_profile,
        sample_common_core_words,
    ):
        """Test that gaps don't include words student already knows."""
        mock_response = {
            "gaps": [
                {
                    "word": "analyze",  # Student already knows this
                    "rationale": "Test",
                    "difficulty_score": 5,
                    "cc_grade_level": 6,
                    "subject_areas": ["math"],
                },
                {
                    "word": "synthesize",  # Student doesn't know this
                    "rationale": "Test",
                    "difficulty_score": 7,
                    "cc_grade_level": 7,
                    "subject_areas": ["science"],
                },
            ]
        }

        import json

        mock_openai_client.complete.return_value = json.dumps(mock_response)

        identifier = GapIdentifier(openai_client=mock_openai_client)

        with patch.object(
            identifier,
            "_load_common_core_vocabulary",
            return_value=sample_common_core_words,
        ):
            gaps = await identifier.identify_gaps(
                extracted_words=[],
                student_profile=sample_student_profile,
            )

        # Should filter out "analyze" since student already knows it
        assert not any(g.word == "analyze" for g in gaps)

