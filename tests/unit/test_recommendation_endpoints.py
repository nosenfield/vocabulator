"""Tests for recommendation endpoints.

This module tests the recommendation retrieval and status update endpoints.
"""

import pytest
from datetime import date, datetime, timezone
from unittest.mock import Mock
from fastapi.testclient import TestClient

from src.api.dependencies import get_recommendation_repository, get_student_repository
from src.api.main import app
from src.api.models.requests import UpdateRecommendationStatusRequest
from src.api.models.responses import (
    RecommendationsResponse,
    RecommendationsListResponse,
    RecommendationStatusResponse,
)
from src.data.models.recommendation import (
    RecommendationStatus,
    RecommendedWord,
    VocabularyRecommendation,
)
from src.data.models.student_profile import StudentProfile


# Mock dependencies
def mock_get_recommendation_repository():
    """Mock recommendation repository dependency."""
    mock_repo = Mock()
    
    # Mock get_by_student method (sync)
    mock_repo.get_by_student = Mock(
        return_value=[
            VocabularyRecommendation(
                student_id="STU-001",
                recommendation_date="2025-11-10",
                words=[
                    RecommendedWord(
                        word="analyze",
                        definition="To examine in detail",
                        grade_level=7,
                        difficulty_score=0.5,
                        rationale="High-frequency academic word",
                        example_sentences=["Let's analyze the data."],
                    )
                ],
                status=RecommendationStatus.PENDING,
            ),
            VocabularyRecommendation(
                student_id="STU-001",
                recommendation_date="2025-11-09",
                words=[
                    RecommendedWord(
                        word="synthesize",
                        definition="To combine into a whole",
                        grade_level=7,
                        difficulty_score=0.6,
                        rationale="Important academic word",
                        example_sentences=["We need to synthesize the information."],
                    )
                ],
                status=RecommendationStatus.ASSIGNED,
            ),
        ]
    )
    
    # Mock get method (sync)
    mock_repo.get = Mock(
        return_value=VocabularyRecommendation(
            student_id="STU-001",
            recommendation_date="2025-11-10",
            words=[
                RecommendedWord(
                    word="analyze",
                    definition="To examine in detail",
                    grade_level=7,
                    difficulty_score=0.5,
                    rationale="High-frequency academic word",
                    example_sentences=["Let's analyze the data."],
                )
            ],
            status=RecommendationStatus.PENDING,
        )
    )
    
    # Mock update_status method (sync)
    mock_repo.update_status = Mock(
        return_value=VocabularyRecommendation(
            student_id="STU-001",
            recommendation_date="2025-11-10",
            words=[
                RecommendedWord(
                    word="analyze",
                    definition="To examine in detail",
                    grade_level=7,
                    difficulty_score=0.5,
                    rationale="High-frequency academic word",
                    example_sentences=["Let's analyze the data."],
                )
            ],
            status=RecommendationStatus.ASSIGNED,
        )
    )
    
    yield mock_repo


def mock_get_student_repository():
    """Mock student repository dependency."""
    mock_repo = Mock()
    mock_repo.get = Mock(
        return_value=StudentProfile(
            student_id="STU-001",
            grade_level=7,
            vocabulary_list=[],
            proficiency_score=75.5,
        )
    )
    yield mock_repo


class TestGetStudentRecommendations:
    """Test GET /api/v1/students/{student_id}/recommendations endpoint."""

    def test_get_recommendations_success(self):
        """Test successful retrieval of student recommendations."""
        app.dependency_overrides[get_recommendation_repository] = mock_get_recommendation_repository
        app.dependency_overrides[get_student_repository] = mock_get_student_repository
        
        try:
            client = TestClient(app)
            response = client.get("/api/v1/students/STU-001/recommendations")
            
            assert response.status_code == 200
            data = response.json()
            assert "recommendations" in data
            assert "total" in data
            assert len(data["recommendations"]) == 2
            assert data["total"] == 2
            assert data["recommendations"][0]["student_id"] == "STU-001"
        finally:
            app.dependency_overrides.clear()

    def test_get_recommendations_student_not_found(self):
        """Test retrieval when student doesn't exist."""
        mock_repo = Mock()
        mock_repo.get = Mock(return_value=None)
        
        def mock_repo_gen():
            yield mock_repo
        
        app.dependency_overrides[get_student_repository] = mock_repo_gen
        app.dependency_overrides[get_recommendation_repository] = mock_get_recommendation_repository
        
        try:
            client = TestClient(app)
            response = client.get("/api/v1/students/STU-999/recommendations")
            
            assert response.status_code == 404
        finally:
            app.dependency_overrides.clear()

    def test_get_recommendations_empty_list(self):
        """Test retrieval when student has no recommendations."""
        mock_repo = Mock()
        mock_repo.get_by_student = Mock(return_value=[])
        
        def mock_repo_gen():
            yield mock_repo
        
        app.dependency_overrides[get_recommendation_repository] = mock_repo_gen
        app.dependency_overrides[get_student_repository] = mock_get_student_repository
        
        try:
            client = TestClient(app)
            response = client.get("/api/v1/students/STU-001/recommendations")
            
            assert response.status_code == 200
            data = response.json()
            assert len(data["recommendations"]) == 0
            assert data["total"] == 0
        finally:
            app.dependency_overrides.clear()


class TestUpdateRecommendationStatus:
    """Test PATCH /api/v1/recommendations/{id}/status endpoint."""

    def test_update_status_success(self):
        """Test successful status update."""
        app.dependency_overrides[get_recommendation_repository] = mock_get_recommendation_repository
        
        try:
            client = TestClient(app)
            # ID format: student_id:recommendation_date
            response = client.patch(
                "/api/v1/recommendations/STU-001:2025-11-10/status",
                json={"status": "assigned"},
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["status"] == "assigned"
            assert data["recommendation_id"] == "STU-001:2025-11-10"
        finally:
            app.dependency_overrides.clear()

    def test_update_status_invalid_id_format(self):
        """Test update with invalid ID format."""
        app.dependency_overrides[get_recommendation_repository] = mock_get_recommendation_repository
        
        try:
            client = TestClient(app)
            response = client.patch(
                "/api/v1/recommendations/INVALID/status",
                json={"status": "assigned"},
            )
            
            assert response.status_code == 400
        finally:
            app.dependency_overrides.clear()

    def test_update_status_recommendation_not_found(self):
        """Test update when recommendation doesn't exist."""
        mock_repo = Mock()
        mock_repo.get = Mock(return_value=None)
        mock_repo.update_status = Mock(return_value=None)
        
        def mock_repo_gen():
            yield mock_repo
        
        app.dependency_overrides[get_recommendation_repository] = mock_repo_gen
        
        try:
            client = TestClient(app)
            response = client.patch(
                "/api/v1/recommendations/STU-001:2025-11-10/status",
                json={"status": "assigned"},
            )
            
            assert response.status_code == 404
        finally:
            app.dependency_overrides.clear()

    def test_update_status_invalid_status(self):
        """Test update with invalid status value."""
        app.dependency_overrides[get_recommendation_repository] = mock_get_recommendation_repository
        
        try:
            client = TestClient(app)
            response = client.patch(
                "/api/v1/recommendations/STU-001:2025-11-10/status",
                json={"status": "invalid"},
            )
            
            assert response.status_code == 422  # Validation error
        finally:
            app.dependency_overrides.clear()

