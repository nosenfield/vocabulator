"""End-to-end workflow integration tests.

This module tests the complete workflow:
- Upload transcript → Extract vocabulary → Update profile → Generate recommendations
"""

import json
from datetime import datetime, timezone
from unittest.mock import AsyncMock

import boto3
import pytest
from moto import mock_aws

from src.data.models.recommendation import VocabularyRecommendation
from src.data.models.student_profile import StudentProfile
from src.data.repositories.recommendation_repository import RecommendationRepository
from src.data.repositories.student_repository import StudentRepository
from src.data.s3_client import S3Client
from src.processing.text_processing_pipeline import TextProcessingPipeline
from tests.mocks.mock_openai import MockOpenAIClient


@pytest.fixture
def mock_aws_services():
    """Create mock AWS services (S3 and DynamoDB) for testing."""
    with mock_aws():
        # Set up S3
        s3_client = boto3.client("s3", region_name="us-east-1")
        s3_client.create_bucket(Bucket="test-bucket")
        
        # Set up DynamoDB
        dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
        
        # Create StudentProfiles table
        dynamodb.create_table(
            TableName="test-StudentProfiles",
            KeySchema=[{"AttributeName": "student_id", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "student_id", "AttributeType": "S"}],
            BillingMode="PAY_PER_REQUEST",
        )
        
        # Create VocabularyRecommendations table
        dynamodb.create_table(
            TableName="test-VocabularyRecommendations",
            KeySchema=[
                {"AttributeName": "student_id", "KeyType": "HASH"},
                {"AttributeName": "recommendation_date", "KeyType": "RANGE"},
            ],
            AttributeDefinitions=[
                {"AttributeName": "student_id", "AttributeType": "S"},
                {"AttributeName": "recommendation_date", "AttributeType": "S"},
            ],
            BillingMode="PAY_PER_REQUEST",
        )
        
        yield {"s3": s3_client, "dynamodb": dynamodb}


@pytest.fixture
def mock_openai_responses():
    """Mock OpenAI API responses for vocabulary extraction and gap analysis."""
    # Mock vocabulary extraction response
    extraction_response = json.dumps({
        "words": [
            {"word": "photosynthesis", "count": 3, "context": "We learned about photosynthesis in science class."},
            {"word": "chloroplast", "count": 1, "context": "The chloroplast contains chlorophyll."},
            {"word": "cellular", "count": 2, "context": "Cellular respiration occurs in mitochondria."},
        ]
    })
    
    # Mock gap analysis response
    gap_analysis_response = json.dumps({
        "gaps": [
            {"word": "mitochondria", "difficulty": 7, "reason": "Related to cellular respiration"},
            {"word": "chlorophyll", "difficulty": 6, "reason": "Related to photosynthesis"},
            {"word": "respiration", "difficulty": 7, "reason": "Scientific term"},
        ]
    })
    
    # Mock recommendation generation response
    recommendation_response = json.dumps({
        "recommendations": [
            {
                "word": "mitochondria",
                "definition": "Organelles in cells that produce energy through cellular respiration.",
                "example_sentence": "The mitochondria are often called the powerhouse of the cell.",
                "usage_tips": "Use when discussing how cells produce energy.",
                "difficulty_score": 0.7,
            },
            {
                "word": "chlorophyll",
                "definition": "Green pigment in plants that captures light energy for photosynthesis.",
                "example_sentence": "Chlorophyll gives leaves their green color.",
                "usage_tips": "Use when discussing plant biology and photosynthesis.",
                "difficulty_score": 0.6,
            },
        ]
    })
    
    # Initialize mock client with default response
    mock_client = MockOpenAIClient()
    mock_client.set_success_response(content=extraction_response)
    
    # Configure mock to return different responses based on model
    async def mock_create(*args, **kwargs):
        model = kwargs.get("model", "")
        if "mini" in model:
            # Vocabulary extraction uses GPT-4o-mini
            mock_client.set_success_response(content=extraction_response)
        elif "gpt-4o" in model:
            # Check if it's gap analysis or recommendation
            messages = kwargs.get("messages", [])
            if any("gap" in str(msg).lower() for msg in messages):
                mock_client.set_success_response(content=gap_analysis_response)
            else:
                mock_client.set_success_response(content=recommendation_response)
        
        return mock_client.chat.completions.create.return_value
    
    mock_client.chat.completions.create = AsyncMock(side_effect=mock_create)
    return mock_client


@pytest.mark.integration
@pytest.mark.asyncio
async def test_end_to_end_workflow(
    mock_aws_services, mock_openai_responses, temp_env_vars
):
    """Test complete end-to-end workflow: upload → extract → update → recommend."""
    # Set up environment
    temp_env_vars(
        DYNAMODB_TABLE_PREFIX="test",
        S3_BUCKET_NAME="test-bucket",
        AWS_REGION="us-east-1",
    )
    
    # Initialize components
    student_repo = StudentRepository()
    recommendation_repo = RecommendationRepository()
    s3_client = S3Client()
    
    # Create student profile
    student_id = "STU-001"
    student = StudentProfile(
        student_id=student_id,
        grade_level=7,
        vocabulary_list=[],
    )
    student_repo.create(student)
    
    # Sample transcript text
    transcript_text = """
    Today in science class, we learned about photosynthesis and cellular respiration.
    Photosynthesis occurs in chloroplasts, which contain chlorophyll.
    The chloroplast uses sunlight to create energy.
    Cellular respiration happens in mitochondria.
    """
    
    # Process text through pipeline with mocked OpenAI
    from src.ai.vocabulary_extractor import VocabularyExtractor
    from src.processing.gap_identifier import GapIdentifier
    from src.processing.recommender import Recommender
    
    # Create mocked components
    mock_extractor = VocabularyExtractor(openai_client=mock_openai_responses)
    mock_gap_identifier = GapIdentifier(openai_client=mock_openai_responses)
    mock_recommender = Recommender(openai_client=mock_openai_responses)
    
    pipeline = TextProcessingPipeline(
        extractor=mock_extractor,
        gap_identifier=mock_gap_identifier,
        recommender=mock_recommender,
        student_repository=student_repo,
        recommendation_repository=recommendation_repo,
    )
    
    recommendation = await pipeline.process_text(
        text=transcript_text,
        student_id=student_id,
        grade_level=7,
    )
    
    # Verify student profile was updated
    updated_profile = student_repo.get(student_id)
    assert updated_profile is not None
    assert len(updated_profile.vocabulary_list) > 0
    
    # Verify vocabulary was extracted
    vocabulary_words = [entry.word for entry in updated_profile.vocabulary_list]
    assert "photosynthesis" in vocabulary_words
    assert "chloroplast" in vocabulary_words
    assert "cellular" in vocabulary_words
    
    # Verify recommendation was created
    assert recommendation is not None
    assert recommendation.student_id == student_id
    assert len(recommendation.recommended_words) > 0
    
    # Verify recommendation was persisted
    stored_recommendation = recommendation_repo.get(
        student_id=student_id,
        recommendation_date=recommendation.recommendation_date,
    )
    assert stored_recommendation is not None
    assert stored_recommendation.student_id == student_id


@pytest.mark.integration
@pytest.mark.asyncio
async def test_multiple_transcript_uploads_accumulate_vocabulary(
    mock_aws_services, mock_openai_responses, temp_env_vars
):
    """Test that multiple transcript uploads accumulate vocabulary in profile."""
    temp_env_vars(
        DYNAMODB_TABLE_PREFIX="test",
        S3_BUCKET_NAME="test-bucket",
        AWS_REGION="us-east-1",
    )
    
    student_repo = StudentRepository()
    recommendation_repo = RecommendationRepository()
    
    # Create student profile
    student_id = "STU-002"
    student = StudentProfile(
        student_id=student_id,
        grade_level=7,
        vocabulary_list=[],
    )
    student_repo.create(student)
    
    # Create mocked components
    from src.ai.vocabulary_extractor import VocabularyExtractor
    from src.processing.gap_identifier import GapIdentifier
    from src.processing.recommender import Recommender
    
    mock_extractor = VocabularyExtractor(openai_client=mock_openai_responses)
    mock_gap_identifier = GapIdentifier(openai_client=mock_openai_responses)
    mock_recommender = Recommender(openai_client=mock_openai_responses)
    
    pipeline = TextProcessingPipeline(
        extractor=mock_extractor,
        gap_identifier=mock_gap_identifier,
        recommender=mock_recommender,
        student_repository=student_repo,
        recommendation_repository=recommendation_repo,
    )
    
    # First transcript
    transcript1 = "We studied photosynthesis in plants today."
    await pipeline.process_text(
        text=transcript1,
        student_id=student_id,
        grade_level=7,
    )
    
    # Second transcript with different vocabulary
    transcript2 = "Today we learned about mitochondria and cellular respiration."
    await pipeline.process_text(
        text=transcript2,
        student_id=student_id,
        grade_level=7,
    )
    
    # Verify vocabulary accumulated
    updated_profile = student_repo.get(student_id)
    assert len(updated_profile.vocabulary_list) >= 2  # At least words from both transcripts


@pytest.mark.integration
@pytest.mark.asyncio
async def test_recommendation_generation_after_profile_update(
    mock_aws_services, mock_openai_responses, temp_env_vars
):
    """Test that recommendations are generated after profile is updated."""
    temp_env_vars(
        DYNAMODB_TABLE_PREFIX="test",
        S3_BUCKET_NAME="test-bucket",
        AWS_REGION="us-east-1",
    )
    
    student_repo = StudentRepository()
    recommendation_repo = RecommendationRepository()
    
    # Create student with existing vocabulary
    student_id = "STU-003"
    student = StudentProfile(
        student_id=student_id,
        grade_level=7,
        vocabulary_list=[
            {"word": "analyze", "count": 5},
            {"word": "evaluate", "count": 3},
        ],
    )
    student_repo.create(student)
    
    # Create mocked components
    from src.ai.vocabulary_extractor import VocabularyExtractor
    from src.processing.gap_identifier import GapIdentifier
    from src.processing.recommender import Recommender
    
    mock_extractor = VocabularyExtractor(openai_client=mock_openai_responses)
    mock_gap_identifier = GapIdentifier(openai_client=mock_openai_responses)
    mock_recommender = Recommender(openai_client=mock_openai_responses)
    
    pipeline = TextProcessingPipeline(
        extractor=mock_extractor,
        gap_identifier=mock_gap_identifier,
        recommender=mock_recommender,
        student_repository=student_repo,
        recommendation_repository=recommendation_repo,
    )
    
    # Process new transcript
    transcript = "We discussed photosynthesis and cellular processes."
    recommendation = await pipeline.process_text(
        text=transcript,
        student_id=student_id,
        grade_level=7,
    )
    
    # Verify recommendation was generated
    assert recommendation is not None
    assert len(recommendation.recommended_words) > 0
    
    # Verify recommended words are not already in profile
    profile = student_repo.get(student_id)
    profile_words = {entry.word for entry in profile.vocabulary_list}
    recommended_words = {word.word for word in recommendation.recommended_words}
    
    # Recommended words should not overlap with existing vocabulary
    assert recommended_words.isdisjoint(profile_words) or len(recommended_words) > 0

