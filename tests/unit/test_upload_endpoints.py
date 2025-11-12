"""Tests for upload endpoints.

This module tests the transcript and writing sample upload endpoints.
"""

import pytest
from datetime import date
from unittest.mock import AsyncMock, Mock, patch
from fastapi.testclient import TestClient

from src.api.dependencies import (
    get_s3_client,
    get_student_repository,
    get_text_processing_pipeline,
)
from src.api.main import app
from src.api.models.requests import TranscriptUploadRequest, WritingUploadRequest
from src.api.models.responses import TranscriptUploadResponse, WritingUploadResponse
from src.data.models.recommendation import VocabularyRecommendation, RecommendationStatus
from src.data.models.student_profile import StudentProfile, VocabularyEntry


# Mock dependencies
def mock_get_text_processing_pipeline():
    """Mock text processing pipeline dependency."""
    mock_pipeline = Mock()
    mock_pipeline.process_text = AsyncMock(
        return_value=VocabularyRecommendation(
            student_id="STU-001",
            recommendation_date="2025-11-10",
            words=[],
            status=RecommendationStatus.PENDING,
        )
    )
    yield mock_pipeline


def mock_get_s3_client():
    """Mock S3 client dependency."""
    mock_s3 = Mock()
    mock_s3.upload = Mock()
    yield mock_s3


def mock_get_student_repository():
    """Mock student repository dependency."""
    mock_repo = Mock()
    mock_repo.get = Mock(  # Sync method, not async
        return_value=StudentProfile(
            student_id="STU-001",
            grade_level=7,
            vocabulary_list=[
                VocabularyEntry(
                    word="photosynthesis",
                    first_seen=date(2025, 11, 10),
                    usage_count=1,
                    contexts=["science"],
                )
            ],
        )
    )
    yield mock_repo


class TestTranscriptUploadEndpoint:
    """Test POST /api/v1/transcripts/upload endpoint."""

    def test_upload_transcript_success(self):
        """Test successful transcript upload."""
        app.dependency_overrides[get_text_processing_pipeline] = mock_get_text_processing_pipeline
        app.dependency_overrides[get_s3_client] = mock_get_s3_client
        app.dependency_overrides[get_student_repository] = mock_get_student_repository
        
        try:
            client = TestClient(app)
            response = client.post(
                "/api/v1/transcripts/upload",
                json={
                    "student_id": "STU-001",
                    "text": "Today we learned about photosynthesis and how plants convert sunlight into energy.",
                    "session_date": "2025-11-10",
                    "grade_level": 7,
                },
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["student_id"] == "STU-001"
            assert "words_extracted" in data
        finally:
            app.dependency_overrides.clear()

    def test_upload_transcript_invalid_request(self):
        """Test upload with invalid request data."""
        # Override dependencies to avoid AWS connection attempts
        app.dependency_overrides[get_text_processing_pipeline] = mock_get_text_processing_pipeline
        app.dependency_overrides[get_s3_client] = mock_get_s3_client
        app.dependency_overrides[get_student_repository] = mock_get_student_repository
        
        try:
            client = TestClient(app)
            response = client.post(
                "/api/v1/transcripts/upload",
                json={
                    "student_id": "INVALID",
                    "text": "Short",
                    "session_date": "2025-11-10",
                    "grade_level": 7,
                },
            )

            assert response.status_code == 422  # Validation error
        finally:
            app.dependency_overrides.clear()


class TestWritingUploadEndpoint:
    """Test POST /api/v1/writing/upload endpoint."""

    def test_upload_writing_success(self):
        """Test successful writing sample upload."""
        app.dependency_overrides[get_text_processing_pipeline] = mock_get_text_processing_pipeline
        app.dependency_overrides[get_s3_client] = mock_get_s3_client
        app.dependency_overrides[get_student_repository] = mock_get_student_repository
        
        try:
            client = TestClient(app)
            response = client.post(
                "/api/v1/writing/upload",
                json={
                    "student_id": "STU-001",
                    "text": "In my essay, I will discuss the importance of vocabulary in academic success.",
                    "assignment_id": "ASSIGN-001",
                    "grade_level": 7,
                },
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["student_id"] == "STU-001"
            assert data["assignment_id"] == "ASSIGN-001"
        finally:
            app.dependency_overrides.clear()

    def test_upload_writing_invalid_request(self):
        """Test upload with invalid request data."""
        # Override dependencies to avoid AWS connection attempts
        app.dependency_overrides[get_text_processing_pipeline] = mock_get_text_processing_pipeline
        app.dependency_overrides[get_s3_client] = mock_get_s3_client
        app.dependency_overrides[get_student_repository] = mock_get_student_repository
        
        try:
            client = TestClient(app)
            response = client.post(
                "/api/v1/writing/upload",
                json={
                    "student_id": "INVALID",
                    "text": "Short",
                    "grade_level": 7,
                },
            )

            assert response.status_code == 422  # Validation error
        finally:
            app.dependency_overrides.clear()

    def test_upload_writing_optional_assignment_id(self):
        """Test upload without assignment_id (optional field)."""
        app.dependency_overrides[get_text_processing_pipeline] = mock_get_text_processing_pipeline
        app.dependency_overrides[get_s3_client] = mock_get_s3_client
        app.dependency_overrides[get_student_repository] = mock_get_student_repository
        
        try:
            client = TestClient(app)
            response = client.post(
                "/api/v1/writing/upload",
                json={
                    "student_id": "STU-001",
                    "text": "In my essay, I will discuss the importance of vocabulary.",
                    "grade_level": 7,
                },
            )

            # Should pass validation and processing with mocks
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
        finally:
            app.dependency_overrides.clear()
