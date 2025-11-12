"""Tests for report generation service.

This module tests the report generation service that creates HTML reports
and uploads them to S3.
"""

from datetime import datetime, timezone
from unittest.mock import Mock, patch, MagicMock

import pytest

from src.frontend.report_generator import ReportGenerator, ReportGenerationError
from src.data.models.student_profile import StudentProfile, VocabularyEntry
from src.data.models.recommendation import VocabularyRecommendation, RecommendedWord, RecommendationStatus


@pytest.fixture
def mock_s3_client():
    """Create a mock S3 client."""
    client = Mock()
    client.upload = Mock()
    client.generate_presigned_url = Mock(return_value="https://example.com/report.html")
    return client


@pytest.fixture
def sample_student_profile():
    """Create a sample student profile."""
    profile = StudentProfile(
        student_id="STU-001",
        grade_level=7,
        proficiency_score=75.5,
    )
    profile.vocabulary_list = [
        VocabularyEntry(
            word="analyze",
            first_seen=datetime(2025, 10, 1, tzinfo=timezone.utc),
            usage_count=5,
            contexts=["science"],
        ),
    ]
    return profile


@pytest.fixture
def sample_recommendation():
    """Create a sample recommendation."""
    return VocabularyRecommendation(
        student_id="STU-001",
        recommendation_date="2025-11-11",
        words=[
            RecommendedWord(
                word="hypothesis",
                definition="A proposed explanation",
                grade_level=7,
                difficulty_score=0.4,
            ),
        ],
    )


class TestReportGenerator:
    """Test ReportGenerator class."""
    
    def test_init_with_s3_client(self, mock_s3_client):
        """Test ReportGenerator initialization with S3 client."""
        generator = ReportGenerator(s3_client=mock_s3_client)
        
        assert generator.s3_client == mock_s3_client
    
    def test_generate_profile_report_success(self, mock_s3_client, sample_student_profile):
        """Test successful profile report generation."""
        generator = ReportGenerator(s3_client=mock_s3_client)
        
        url = generator.generate_profile_report(
            profile=sample_student_profile,
            bucket_name="test-bucket",
        )
        
        assert url == "https://example.com/report.html"
        mock_s3_client.upload.assert_called_once()
        call_args = mock_s3_client.upload.call_args
        assert call_args[1]["key"].startswith("reports/STU-001/profile")
        assert call_args[1]["key"].endswith(".html")
        assert call_args[1]["content_type"] == "text/html"
        assert len(call_args[1]["content"]) > 0
    
    def test_generate_recommendations_report_success(self, mock_s3_client, sample_recommendation):
        """Test successful recommendations report generation."""
        generator = ReportGenerator(s3_client=mock_s3_client)
        
        url = generator.generate_recommendations_report(
            recommendation=sample_recommendation,
            bucket_name="test-bucket",
        )
        
        assert url == "https://example.com/report.html"
        mock_s3_client.upload.assert_called_once()
        call_args = mock_s3_client.upload.call_args
        assert call_args[1]["key"].startswith("reports/STU-001/recommendations")
        assert call_args[1]["key"].endswith(".html")
        assert call_args[1]["content_type"] == "text/html"
        assert len(call_args[1]["content"]) > 0
    
    def test_generate_profile_report_s3_upload_failure(self, mock_s3_client, sample_student_profile):
        """Test profile report generation with S3 upload failure."""
        from src.data.s3_client import S3Error
        
        mock_s3_client.upload.side_effect = S3Error("Upload failed")
        generator = ReportGenerator(s3_client=mock_s3_client)
        
        with pytest.raises(ReportGenerationError) as exc_info:
            generator.generate_profile_report(
                profile=sample_student_profile,
                bucket_name="test-bucket",
            )
        
        assert "Failed to upload profile report to S3" in str(exc_info.value)
    
    def test_generate_recommendations_report_s3_upload_failure(self, mock_s3_client, sample_recommendation):
        """Test recommendations report generation with S3 upload failure."""
        from src.data.s3_client import S3Error
        
        mock_s3_client.upload.side_effect = S3Error("Upload failed")
        generator = ReportGenerator(s3_client=mock_s3_client)
        
        with pytest.raises(ReportGenerationError) as exc_info:
            generator.generate_recommendations_report(
                recommendation=sample_recommendation,
                bucket_name="test-bucket",
            )
        
        assert "Failed to upload recommendations report to S3" in str(exc_info.value)
    
    def test_generate_profile_report_presigned_url_failure(self, mock_s3_client, sample_student_profile):
        """Test profile report generation with presigned URL generation failure."""
        from src.data.s3_client import S3Error
        
        mock_s3_client.generate_presigned_url.side_effect = S3Error("URL generation failed")
        generator = ReportGenerator(s3_client=mock_s3_client)
        
        with pytest.raises(ReportGenerationError) as exc_info:
            generator.generate_profile_report(
                profile=sample_student_profile,
                bucket_name="test-bucket",
            )
        
        assert "Failed to upload profile report to S3" in str(exc_info.value)
    
    def test_generate_profile_report_custom_key(self, mock_s3_client, sample_student_profile):
        """Test profile report generation with custom S3 key."""
        generator = ReportGenerator(s3_client=mock_s3_client)
        
        url = generator.generate_profile_report(
            profile=sample_student_profile,
            bucket_name="test-bucket",
            s3_key="custom/path/report.html",
        )
        
        assert url == "https://example.com/report.html"
        call_args = mock_s3_client.upload.call_args
        assert call_args[1]["key"] == "custom/path/report.html"
    
    def test_generate_recommendations_report_custom_key(self, mock_s3_client, sample_recommendation):
        """Test recommendations report generation with custom S3 key."""
        generator = ReportGenerator(s3_client=mock_s3_client)
        
        url = generator.generate_recommendations_report(
            recommendation=sample_recommendation,
            bucket_name="test-bucket",
            s3_key="custom/path/recommendations.html",
        )
        
        assert url == "https://example.com/report.html"
        call_args = mock_s3_client.upload.call_args
        assert call_args[1]["key"] == "custom/path/recommendations.html"
    
    def test_generate_profile_report_default_bucket(self, mock_s3_client, sample_student_profile):
        """Test profile report generation uses default bucket from S3 client."""
        generator = ReportGenerator(s3_client=mock_s3_client)
        
        # Don't specify bucket_name, should use S3 client's default
        url = generator.generate_profile_report(
            profile=sample_student_profile,
        )
        
        assert url == "https://example.com/report.html"
        mock_s3_client.upload.assert_called_once()
    
    def test_generate_both_reports_same_student(self, mock_s3_client, sample_student_profile, sample_recommendation):
        """Test generating both reports for the same student."""
        generator = ReportGenerator(s3_client=mock_s3_client)
        
        profile_url = generator.generate_profile_report(
            profile=sample_student_profile,
            bucket_name="test-bucket",
        )
        
        rec_url = generator.generate_recommendations_report(
            recommendation=sample_recommendation,
            bucket_name="test-bucket",
        )
        
        assert profile_url == "https://example.com/report.html"
        assert rec_url == "https://example.com/report.html"
        assert mock_s3_client.upload.call_count == 2
        
        # Check that keys are different
        profile_key = mock_s3_client.upload.call_args_list[0][1]["key"]
        rec_key = mock_s3_client.upload.call_args_list[1][1]["key"]
        assert profile_key != rec_key
        assert "profile" in profile_key
        assert "recommendations" in rec_key

