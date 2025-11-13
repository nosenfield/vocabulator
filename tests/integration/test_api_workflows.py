"""API workflow integration tests.

This module tests complete API workflows:
- Create student → Upload samples → Retrieve reports
"""

import json
from datetime import datetime, timezone
from unittest.mock import AsyncMock

import boto3
import pytest
from fastapi.testclient import TestClient
from moto import mock_aws

from src.api.main import app
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
            {"word": "photosynthesis", "count": 3, "context": "We learned about photosynthesis."},
            {"word": "chloroplast", "count": 1, "context": "The chloroplast contains chlorophyll."},
        ]
    })
    
    # Mock gap analysis response
    gap_analysis_response = json.dumps({
        "gaps": [
            {"word": "mitochondria", "difficulty": 7, "reason": "Related to cellular respiration"},
        ]
    })
    
    # Mock recommendation generation response
    recommendation_response = json.dumps({
        "recommendations": [
            {
                "word": "mitochondria",
                "definition": "Organelles in cells that produce energy.",
                "example_sentence": "The mitochondria are the powerhouse of the cell.",
                "usage_tips": "Use when discussing cellular energy.",
                "difficulty_score": 0.7,
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
            mock_client.set_success_response(content=extraction_response)
        elif "gpt-4o" in model:
            messages = kwargs.get("messages", [])
            if any("gap" in str(msg).lower() for msg in messages):
                mock_client.set_success_response(content=gap_analysis_response)
            else:
                mock_client.set_success_response(content=recommendation_response)
        
        return mock_client.chat.completions.create.return_value
    
    mock_client.chat.completions.create = AsyncMock(side_effect=mock_create)
    return mock_client


@pytest.fixture
def api_client(mock_aws_services, mock_openai_responses, temp_env_vars):
    """Create FastAPI test client with mocked dependencies."""
    temp_env_vars(
        DYNAMODB_TABLE_PREFIX="test",
        S3_BUCKET_NAME="test-bucket",
        AWS_REGION="us-east-1",
        OPENAI_API_KEY="test-key",
    )
    
    # Override pipeline dependency to inject mocked OpenAI client
    from src.api.dependencies import get_text_processing_pipeline
    from src.ai.vocabulary_extractor import VocabularyExtractor
    from src.processing.gap_identifier import GapIdentifier
    from src.processing.recommender import Recommender
    from src.processing.text_processing_pipeline import TextProcessingPipeline
    
    def get_mocked_pipeline():
        """Provide text processing pipeline with mocked OpenAI client."""
        mock_extractor = VocabularyExtractor(openai_client=mock_openai_responses)
        mock_gap_identifier = GapIdentifier(openai_client=mock_openai_responses)
        mock_recommender = Recommender(openai_client=mock_openai_responses)
        
        pipeline = TextProcessingPipeline(
            extractor=mock_extractor,
            gap_identifier=mock_gap_identifier,
            recommender=mock_recommender,
        )
        yield pipeline
    
    app.dependency_overrides[get_text_processing_pipeline] = get_mocked_pipeline
    
    yield TestClient(app)
    
    # Cleanup: remove overrides
    app.dependency_overrides.clear()


@pytest.mark.integration
def test_create_student_and_upload_transcript_workflow(
    api_client, temp_env_vars
):
    """Test complete workflow: create student → upload transcript → retrieve profile."""
    temp_env_vars(
        DYNAMODB_TABLE_PREFIX="test",
        S3_BUCKET_NAME="test-bucket",
        AWS_REGION="us-east-1",
    )
    
    student_id = "STU-001"
    
    # Step 1: Create student profile
    create_response = api_client.post(
        "/api/v1/students",
        json={
            "student_id": student_id,
            "grade_level": 7,
        },
    )
    assert create_response.status_code == 200
    assert create_response.json()["student_id"] == student_id
    
    # Step 2: Upload transcript (OpenAI already mocked via dependency override)
    transcript_text = "Today we learned about photosynthesis and chloroplasts."
    upload_response = api_client.post(
        "/api/v1/transcripts/upload",
        json={
            "student_id": student_id,
            "text": transcript_text,
            "session_date": "2024-01-15",
            "grade_level": 7,
        },
    )
    
    assert upload_response.status_code == 200
    assert upload_response.json()["success"] is True
    assert upload_response.json()["words_extracted"] > 0
    
    # Step 3: Retrieve student profile
    profile_response = api_client.get(f"/api/v1/students/{student_id}/profile")
    assert profile_response.status_code == 200
    profile_data = profile_response.json()
    assert profile_data["student_id"] == student_id
    assert len(profile_data["vocabulary_list"]) > 0


@pytest.mark.integration
def test_upload_writing_sample_and_get_recommendations_workflow(
    api_client, temp_env_vars
):
    """Test workflow: create student → upload writing → get recommendations."""
    temp_env_vars(
        DYNAMODB_TABLE_PREFIX="test",
        S3_BUCKET_NAME="test-bucket",
        AWS_REGION="us-east-1",
    )
    
    student_id = "STU-002"
    
    # Step 1: Create student profile
    create_response = api_client.post(
        "/api/v1/students",
        json={
            "student_id": student_id,
            "grade_level": 7,
        },
    )
    assert create_response.status_code == 200
    
    # Step 2: Upload writing sample (OpenAI already mocked via dependency override)
    writing_text = "I wrote an essay about cellular processes and energy production."
    upload_response = api_client.post(
        "/api/v1/writing/upload",
        json={
            "student_id": student_id,
            "text": writing_text,
            "assignment_id": "essay-001",
            "grade_level": 7,
        },
    )
    
    assert upload_response.status_code == 200
    assert upload_response.json()["success"] is True
    
    # Step 3: Get recommendations
    recommendations_response = api_client.get(
        f"/api/v1/students/{student_id}/recommendations"
    )
    assert recommendations_response.status_code == 200
    recommendations_data = recommendations_response.json()
    assert len(recommendations_data["recommendations"]) > 0


@pytest.mark.integration
def test_list_students_and_filter_by_grade(
    api_client, temp_env_vars
):
    """Test listing students with grade level filter."""
    temp_env_vars(
        DYNAMODB_TABLE_PREFIX="test",
        S3_BUCKET_NAME="test-bucket",
        AWS_REGION="us-east-1",
    )
    
    # Create multiple students with different grade levels
    students = [
        {"student_id": "STU-003", "grade_level": 6},
        {"student_id": "STU-004", "grade_level": 7},
        {"student_id": "STU-005", "grade_level": 7},
        {"student_id": "STU-006", "grade_level": 8},
    ]
    
    for student_data in students:
        api_client.post("/api/v1/students", json=student_data)
    
    # List all students
    all_response = api_client.get("/api/v1/students")
    assert all_response.status_code == 200
    all_students = all_response.json()["students"]
    assert len(all_students) >= len(students)
    
    # Filter by grade level 7
    grade7_response = api_client.get("/api/v1/students?grade_level=7")
    assert grade7_response.status_code == 200
    grade7_students = grade7_response.json()["students"]
    assert len(grade7_students) >= 2
    assert all(s["grade_level"] == 7 for s in grade7_students)


@pytest.mark.integration
def test_update_recommendation_status_workflow(
    api_client, temp_env_vars
):
    """Test workflow: create student → upload → get recommendations → update status."""
    temp_env_vars(
        DYNAMODB_TABLE_PREFIX="test",
        S3_BUCKET_NAME="test-bucket",
        AWS_REGION="us-east-1",
    )
    
    student_id = "STU-007"
    
    # Step 1: Create student
    api_client.post(
        "/api/v1/students",
        json={"student_id": student_id, "grade_level": 7},
    )
    
    # Step 2: Upload transcript (OpenAI already mocked via dependency override)
    api_client.post(
        "/api/v1/transcripts/upload",
        json={
            "student_id": student_id,
            "text": "Sample text about science.",
            "session_date": "2024-01-15",
            "grade_level": 7,
        },
    )
    
    # Step 3: Get recommendations
    recommendations_response = api_client.get(
        f"/api/v1/students/{student_id}/recommendations"
    )
    assert recommendations_response.status_code == 200
    recommendations = recommendations_response.json()["recommendations"]
    assert len(recommendations) > 0
    
    # Step 4: Update recommendation status
    # Recommendation ID format: {student_id}:{recommendation_date}
    first_rec = recommendations[0]
    recommendation_id = f"{first_rec['student_id']}:{first_rec['recommendation_date']}"
    update_response = api_client.patch(
        f"/api/v1/recommendations/{recommendation_id}/status",
        json={"status": "assigned"},
    )
    assert update_response.status_code == 200
    assert update_response.json()["status"] == "assigned"
    
    # Step 5: Verify status update
    updated_recommendations = api_client.get(
        f"/api/v1/students/{student_id}/recommendations"
    ).json()["recommendations"]
    updated_rec = next(
        (r for r in updated_recommendations 
         if r["student_id"] == first_rec["student_id"] 
         and r["recommendation_date"] == first_rec["recommendation_date"]), 
        None
    )
    assert updated_rec is not None
    assert updated_rec["status"] == "assigned"

