"""Unit tests for text processing pipeline.

Tests cover:
- End-to-end pipeline: Extract → Update Profile → Identify Gaps → Generate Recommendations
- Error handling at each stage
- Student profile updates
- Recommendation persistence
"""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.ai.vocabulary_extractor import ExtractedWord, VocabularyExtractor
from src.data.models.recommendation import VocabularyRecommendation
from src.data.models.student_profile import StudentProfile, VocabularyEntry
from src.data.repositories.recommendation_repository import RecommendationRepository
from src.data.repositories.student_repository import StudentRepository
from src.processing.gap_identifier import GapIdentifier, GapWord
from src.processing.recommender import Recommender
from src.processing.text_processing_pipeline import TextProcessingPipeline


@pytest.fixture
def sample_text():
    """Sample student text for processing."""
    return "Today we learned about photosynthesis and analyzed data from experiments. The process involves converting sunlight into energy."


@pytest.fixture
def sample_student_profile():
    """Create a sample student profile."""
    return StudentProfile(
        student_id="STU-001",
        grade_level=7,
        vocabulary_list=[
            VocabularyEntry(
                word="learned",
                first_seen=datetime.now(timezone.utc),
                usage_count=5,
                contexts=["ela"],
            ),
        ],
        proficiency_score=45.0,
    )


@pytest.fixture
def sample_extracted_words():
    """Create sample extracted words."""
    return [
        ExtractedWord(
            word="photosynthesis",
            count=2,
            example="Photosynthesis is the process where plants convert sunlight into energy.",
        ),
        ExtractedWord(
            word="analyzed",
            count=1,
            example="We analyzed data from experiments.",
        ),
        ExtractedWord(
            word="converting",
            count=1,
            example="Converting sunlight into energy.",
        ),
    ]


@pytest.fixture
def sample_gap_words():
    """Create sample gap words."""
    return [
        GapWord(
            word="synthesize",
            rationale="High-frequency academic word",
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
    ]


@pytest.fixture
def sample_recommendation():
    """Create sample recommendation."""
    from src.data.models.recommendation import RecommendedWord

    return VocabularyRecommendation(
        student_id="STU-001",
        recommendation_date=datetime.now(timezone.utc).date().isoformat(),
        words=[
            RecommendedWord(
                word="synthesize",
                definition="combine elements into a whole",
                grade_level=7,
                difficulty_score=0.7,
                rationale="High-frequency academic word",
                example_sentences=["Scientists synthesize information from multiple sources."],
            ),
        ],
    )


@pytest.fixture
def mock_extractor():
    """Create mock vocabulary extractor."""
    extractor = MagicMock(spec=VocabularyExtractor)
    extractor.extract = AsyncMock(return_value=[])
    return extractor


@pytest.fixture
def mock_gap_identifier():
    """Create mock gap identifier."""
    identifier = MagicMock(spec=GapIdentifier)
    identifier.identify_gaps = AsyncMock(return_value=[])
    return identifier


@pytest.fixture
def mock_recommender():
    """Create mock recommender."""
    recommender = MagicMock(spec=Recommender)
    recommender.generate = AsyncMock(return_value=None)
    return recommender


@pytest.fixture
def mock_student_repository():
    """Create mock student repository."""
    repo = MagicMock(spec=StudentRepository)
    repo.get = MagicMock(return_value=None)
    repo.create = MagicMock(return_value=None)
    repo.update = MagicMock(return_value=None)
    return repo


@pytest.fixture
def mock_recommendation_repository():
    """Create mock recommendation repository."""
    repo = MagicMock(spec=RecommendationRepository)
    repo.create = MagicMock(return_value=None)
    return repo


@pytest.mark.asyncio
async def test_process_text_full_pipeline(
    sample_text,
    sample_student_profile,
    sample_extracted_words,
    sample_gap_words,
    sample_recommendation,
    mock_extractor,
    mock_gap_identifier,
    mock_recommender,
    mock_student_repository,
    mock_recommendation_repository,
):
    """Test full pipeline execution."""
    # Setup mocks
    mock_extractor.extract.return_value = sample_extracted_words
    mock_student_repository.get.return_value = sample_student_profile
    mock_student_repository.update.return_value = sample_student_profile
    mock_gap_identifier.identify_gaps.return_value = sample_gap_words
    mock_recommender.generate.return_value = sample_recommendation
    mock_recommendation_repository.create.return_value = sample_recommendation

    # Create pipeline
    pipeline = TextProcessingPipeline(
        extractor=mock_extractor,
        gap_identifier=mock_gap_identifier,
        recommender=mock_recommender,
        student_repository=mock_student_repository,
        recommendation_repository=mock_recommendation_repository,
    )

    # Execute pipeline
    result = await pipeline.process_text(
        text=sample_text,
        student_id="STU-001",
        request_id="test-request-001",
    )

    # Verify result
    assert result is not None
    assert result.student_id == "STU-001"
    assert len(result.words) > 0

    # Verify extractor was called
    mock_extractor.extract.assert_called_once_with(
        sample_text,
        use_cache=True,
        request_id="test-request-001",
    )

    # Verify student repository was called
    mock_student_repository.get.assert_called_once_with("STU-001", 1)
    mock_student_repository.update.assert_called_once()

    # Verify gap identifier was called
    mock_gap_identifier.identify_gaps.assert_called_once()
    call_args = mock_gap_identifier.identify_gaps.call_args
    assert len(call_args[0][0]) == len(sample_extracted_words)  # extracted_words
    assert call_args[0][1].student_id == "STU-001"  # student_profile

    # Verify recommender was called
    mock_recommender.generate.assert_called_once()
    rec_call_args = mock_recommender.generate.call_args
    assert len(rec_call_args[0][0]) == len(sample_gap_words)  # gap_words
    assert rec_call_args[0][1] == "STU-001"  # student_id

    # Verify recommendation repository was called
    mock_recommendation_repository.create.assert_called_once_with(sample_recommendation)


@pytest.mark.asyncio
async def test_process_text_creates_new_profile(
    sample_text,
    sample_extracted_words,
    sample_gap_words,
    sample_recommendation,
    mock_extractor,
    mock_gap_identifier,
    mock_recommender,
    mock_student_repository,
    mock_recommendation_repository,
):
    """Test pipeline creates new student profile if none exists."""
    # Setup mocks - no existing profile
    mock_extractor.extract.return_value = sample_extracted_words
    mock_student_repository.get.return_value = None  # No existing profile
    new_profile = StudentProfile(
        student_id="STU-002",
        grade_level=7,
    )
    mock_student_repository.create.return_value = new_profile
    mock_student_repository.update.return_value = new_profile
    mock_gap_identifier.identify_gaps.return_value = sample_gap_words
    mock_recommender.generate.return_value = sample_recommendation
    mock_recommendation_repository.create.return_value = sample_recommendation

    # Create pipeline
    pipeline = TextProcessingPipeline(
        extractor=mock_extractor,
        gap_identifier=mock_gap_identifier,
        recommender=mock_recommender,
        student_repository=mock_student_repository,
        recommendation_repository=mock_recommendation_repository,
        default_grade_level=7,
    )

    # Execute pipeline
    result = await pipeline.process_text(
        text=sample_text,
        student_id="STU-002",
    )

    # Verify new profile was created
    mock_student_repository.get.assert_called_once_with("STU-002", 1)
    mock_student_repository.create.assert_called_once()
    create_call = mock_student_repository.create.call_args[0][0]
    assert create_call.student_id == "STU-002"
    assert create_call.grade_level == 7


@pytest.mark.asyncio
async def test_process_text_handles_empty_extraction(
    sample_text,
    sample_student_profile,
    mock_extractor,
    mock_gap_identifier,
    mock_recommender,
    mock_student_repository,
    mock_recommendation_repository,
):
    """Test pipeline handles empty vocabulary extraction."""
    # Setup mocks - no words extracted
    mock_extractor.extract.return_value = []
    mock_student_repository.get.return_value = sample_student_profile
    mock_student_repository.update.return_value = sample_student_profile
    mock_gap_identifier.identify_gaps.return_value = []
    empty_recommendation = VocabularyRecommendation(
        student_id="STU-001",
        recommendation_date=datetime.now(timezone.utc).date().isoformat(),
        words=[],
    )
    mock_recommender.generate.return_value = empty_recommendation
    mock_recommendation_repository.create.return_value = empty_recommendation

    # Create pipeline
    pipeline = TextProcessingPipeline(
        extractor=mock_extractor,
        gap_identifier=mock_gap_identifier,
        recommender=mock_recommender,
        student_repository=mock_student_repository,
        recommendation_repository=mock_recommendation_repository,
    )

    # Execute pipeline
    result = await pipeline.process_text(
        text=sample_text,
        student_id="STU-001",
    )

    # Verify pipeline completed successfully
    assert result is not None
    assert len(result.words) == 0

    # Verify gap identifier was called with empty list
    mock_gap_identifier.identify_gaps.assert_called_once()
    call_args = mock_gap_identifier.identify_gaps.call_args
    assert len(call_args[0][0]) == 0  # empty extracted_words


@pytest.mark.asyncio
async def test_process_text_handles_extraction_error(
    sample_text,
    sample_student_profile,
    mock_extractor,
    mock_gap_identifier,
    mock_recommender,
    mock_student_repository,
    mock_recommendation_repository,
):
    """Test pipeline handles extraction errors gracefully."""
    from src.ai.openai_client import OpenAIError

    # Setup mocks - extraction fails
    mock_extractor.extract.side_effect = OpenAIError("Extraction failed")
    mock_student_repository.get.return_value = sample_student_profile

    # Create pipeline
    pipeline = TextProcessingPipeline(
        extractor=mock_extractor,
        gap_identifier=mock_gap_identifier,
        recommender=mock_recommender,
        student_repository=mock_student_repository,
        recommendation_repository=mock_recommendation_repository,
    )

    # Execute pipeline - should raise error
    with pytest.raises(OpenAIError):
        await pipeline.process_text(
            text=sample_text,
            student_id="STU-001",
        )


@pytest.mark.asyncio
async def test_process_text_updates_profile_with_new_words(
    sample_text,
    sample_student_profile,
    sample_extracted_words,
    sample_gap_words,
    sample_recommendation,
    mock_extractor,
    mock_gap_identifier,
    mock_recommender,
    mock_student_repository,
    mock_recommendation_repository,
):
    """Test pipeline updates student profile with extracted words."""
    # Setup mocks
    mock_extractor.extract.return_value = sample_extracted_words
    mock_student_repository.get.return_value = sample_student_profile
    updated_profile = StudentProfile(
        student_id="STU-001",
        grade_level=7,
        vocabulary_list=sample_student_profile.vocabulary_list + [
            VocabularyEntry(
                word="photosynthesis",
                first_seen=datetime.now(timezone.utc),
                usage_count=2,
                contexts=["science"],
            ),
        ],
    )
    mock_student_repository.update.return_value = updated_profile
    mock_gap_identifier.identify_gaps.return_value = sample_gap_words
    mock_recommender.generate.return_value = sample_recommendation
    mock_recommendation_repository.create.return_value = sample_recommendation

    # Create pipeline
    pipeline = TextProcessingPipeline(
        extractor=mock_extractor,
        gap_identifier=mock_gap_identifier,
        recommender=mock_recommender,
        student_repository=mock_student_repository,
        recommendation_repository=mock_recommendation_repository,
    )

    # Execute pipeline
    await pipeline.process_text(
        text=sample_text,
        student_id="STU-001",
    )

    # Verify profile was updated
    mock_student_repository.update.assert_called_once()
    update_call = mock_student_repository.update.call_args[0][0]
    assert update_call.student_id == "STU-001"
    # Profile should have new words added
    assert len(update_call.vocabulary_list) >= len(sample_student_profile.vocabulary_list)


@pytest.mark.asyncio
async def test_process_text_with_custom_request_id(
    sample_text,
    sample_student_profile,
    sample_extracted_words,
    sample_gap_words,
    sample_recommendation,
    mock_extractor,
    mock_gap_identifier,
    mock_recommender,
    mock_student_repository,
    mock_recommendation_repository,
):
    """Test pipeline propagates request ID through all components."""
    custom_request_id = "custom-request-123"

    # Setup mocks
    mock_extractor.extract.return_value = sample_extracted_words
    mock_student_repository.get.return_value = sample_student_profile
    mock_student_repository.update.return_value = sample_student_profile
    mock_gap_identifier.identify_gaps.return_value = sample_gap_words
    mock_recommender.generate.return_value = sample_recommendation
    mock_recommendation_repository.create.return_value = sample_recommendation

    # Create pipeline
    pipeline = TextProcessingPipeline(
        extractor=mock_extractor,
        gap_identifier=mock_gap_identifier,
        recommender=mock_recommender,
        student_repository=mock_student_repository,
        recommendation_repository=mock_recommendation_repository,
    )

    # Execute pipeline
    await pipeline.process_text(
        text=sample_text,
        student_id="STU-001",
        request_id=custom_request_id,
    )

    # Verify request ID was propagated
    mock_extractor.extract.assert_called_once_with(
        sample_text,
        use_cache=True,
        request_id=custom_request_id,
    )
    mock_gap_identifier.identify_gaps.assert_called_once()
    gap_call = mock_gap_identifier.identify_gaps.call_args
    assert gap_call[1]["request_id"] == custom_request_id

    mock_recommender.generate.assert_called_once()
    rec_call = mock_recommender.generate.call_args
    assert rec_call[1]["request_id"] == custom_request_id

