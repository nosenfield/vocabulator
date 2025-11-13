"""Tests for API request/response models.

This module tests all Pydantic models used for API request/response validation.
"""

import pytest
from datetime import date, datetime, timezone
from pydantic import ValidationError

from src.api.models.requests import (
    TranscriptUploadRequest,
    WritingUploadRequest,
    CreateStudentRequest,
    UpdateStudentRequest,
    UpdateRecommendationStatusRequest,
    BatchProcessRequest,
)
from src.api.models.responses import (
    TranscriptUploadResponse,
    WritingUploadResponse,
    StudentProfileResponse,
    StudentListItem,
    StudentsListResponse,
    RecommendationWordResponse,
    RecommendationsResponse,
    RecommendationStatusResponse,
    BatchProcessResponse,
    BatchStatusResponse,
    ErrorResponse,
)


class TestTranscriptUploadRequest:
    """Test TranscriptUploadRequest model."""

    def test_valid_request(self):
        """Test valid transcript upload request."""
        request = TranscriptUploadRequest(
            student_id="STU-001",
            text="Today we learned about photosynthesis and how plants convert sunlight into energy.",
            session_date=date(2025, 11, 10),
            grade_level=7,
        )
        assert request.student_id == "STU-001"
        assert len(request.text) > 0
        assert request.grade_level == 7

    def test_invalid_student_id_format(self):
        """Test invalid student ID format."""
        with pytest.raises(ValidationError) as exc_info:
            TranscriptUploadRequest(
                student_id="INVALID",
                text="Sample text",
                session_date=date(2025, 11, 10),
                grade_level=7,
            )
        assert "student_id" in str(exc_info.value)

    def test_text_too_short(self):
        """Test text that is too short."""
        with pytest.raises(ValidationError):
            TranscriptUploadRequest(
                student_id="STU-001",
                text="Short",
                session_date=date(2025, 11, 10),
                grade_level=7,
            )

    def test_invalid_grade_level(self):
        """Test invalid grade level."""
        with pytest.raises(ValidationError):
            TranscriptUploadRequest(
                student_id="STU-001",
                text="Sample text for testing",
                session_date=date(2025, 11, 10),
                grade_level=5,  # Invalid: must be 6-8
            )


class TestWritingUploadRequest:
    """Test WritingUploadRequest model."""

    def test_valid_request(self):
        """Test valid writing upload request."""
        request = WritingUploadRequest(
            student_id="STU-001",
            text="In my essay, I will discuss the importance of vocabulary in academic success.",
            assignment_id="ASSIGN-001",
            grade_level=7,
        )
        assert request.student_id == "STU-001"
        assert request.assignment_id == "ASSIGN-001"

    def test_optional_assignment_id(self):
        """Test that assignment_id is optional."""
        request = WritingUploadRequest(
            student_id="STU-001",
            text="Sample writing sample text",
            grade_level=7,
        )
        assert request.assignment_id is None


class TestCreateStudentRequest:
    """Test CreateStudentRequest model."""

    def test_valid_request(self):
        """Test valid create student request."""
        request = CreateStudentRequest(
            student_id="STU-001",
            grade_level=7,
        )
        assert request.student_id == "STU-001"
        assert request.grade_level == 7


class TestUpdateStudentRequest:
    """Test UpdateStudentRequest model."""

    def test_partial_update(self):
        """Test partial update with only grade_level."""
        request = UpdateStudentRequest(grade_level=8)
        assert request.grade_level == 8

    def test_all_fields_optional(self):
        """Test that all fields are optional."""
        request = UpdateStudentRequest()
        assert request.grade_level is None


class TestUpdateRecommendationStatusRequest:
    """Test UpdateRecommendationStatusRequest model."""

    def test_valid_request(self):
        """Test valid status update request."""
        request = UpdateRecommendationStatusRequest(status="assigned")
        assert request.status == "assigned"

    def test_invalid_status(self):
        """Test invalid status value."""
        with pytest.raises(ValidationError):
            UpdateRecommendationStatusRequest(status="invalid")


class TestBatchProcessRequest:
    """Test BatchProcessRequest model."""

    def test_valid_request(self):
        """Test valid batch process request."""
        request = BatchProcessRequest(
            student_ids=["STU-001", "STU-002"],
            s3_paths=["s3://bucket/transcripts/STU-001.txt", "s3://bucket/transcripts/STU-002.txt"],
            grade_level=7,
        )
        assert len(request.student_ids) == 2
        assert len(request.s3_paths) == 2

    def test_empty_student_ids(self):
        """Test that student_ids cannot be empty."""
        with pytest.raises(ValidationError):
            BatchProcessRequest(
                student_ids=[],
                s3_paths=["s3://bucket/transcript.txt"],
                grade_level=7,
            )


class TestResponseModels:
    """Test response models."""

    def test_transcript_upload_response(self):
        """Test TranscriptUploadResponse."""
        response = TranscriptUploadResponse(
            success=True,
            student_id="STU-001",
            words_extracted=15,
            profile_url="https://example.com/profile/STU-001",
        )
        assert response.success is True
        assert response.words_extracted == 15

    def test_student_profile_response(self):
        """Test StudentProfileResponse."""
        response = StudentProfileResponse(
            student_id="STU-001",
            grade_level=7,
            vocabulary_size=150,
            proficiency_score=75.5,
            created_at=datetime.now(timezone.utc),
            last_updated=datetime.now(timezone.utc),
        )
        assert response.student_id == "STU-001"
        assert response.vocabulary_size == 150

    def test_students_list_response(self):
        """Test StudentsListResponse."""
        items = [
            StudentListItem(
                student_id="STU-001",
                grade_level=7,
                vocabulary_size=150,
                proficiency_score=75.5,
            ),
            StudentListItem(
                student_id="STU-002",
                grade_level=8,
                vocabulary_size=200,
                proficiency_score=80.0,
            ),
        ]
        response = StudentsListResponse(students=items, total=2)
        assert len(response.students) == 2
        assert response.total == 2

    def test_recommendations_response(self):
        """Test RecommendationsResponse."""
        words = [
            RecommendationWordResponse(
                word="photosynthesis",
                definition="The process by which plants convert light into energy",
                grade_level=7,
                difficulty_score=0.6,
                rationale="Important for science curriculum",
                example_sentences=["Plants use photosynthesis to make food."],
            )
        ]
        response = RecommendationsResponse(
            student_id="STU-001",
            recommendation_date="2025-11-10",
            words=words,
            status="pending",
        )
        assert len(response.words) == 1
        assert response.status == "pending"

    def test_batch_process_response(self):
        """Test BatchProcessResponse."""
        response = BatchProcessResponse(
            success=True,
            job_id="job-123",
            message="Batch job submitted successfully",
        )
        assert response.success is True
        assert response.job_id == "job-123"

    def test_batch_status_response(self):
        """Test BatchStatusResponse."""
        response = BatchStatusResponse(
            job_id="job-123",
            status="RUNNING",
            created_at=datetime.now(timezone.utc),
            progress=50,
        )
        assert response.status == "RUNNING"
        assert response.progress == 50

    def test_error_response(self):
        """Test ErrorResponse."""
        response = ErrorResponse(
            error="validation_error",
            message="Invalid student ID format",
            details={"field": "student_id"},
        )
        assert response.error == "validation_error"
        assert "student_id" in response.details["field"]

