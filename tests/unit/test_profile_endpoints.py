"""Tests for student profile endpoints.

This module tests the student profile CRUD endpoints.
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, Mock
from fastapi.testclient import TestClient

from src.api.dependencies import get_student_repository
from src.api.main import app
from src.api.models.requests import CreateStudentRequest, UpdateStudentRequest
from src.api.models.responses import StudentProfileResponse, StudentsListResponse
from src.data.models.student_profile import StudentProfile, VocabularyEntry


# Mock dependencies
def mock_get_student_repository():
    """Mock student repository dependency."""
    mock_repo = Mock()
    
    # Mock get method (sync)
    mock_repo.get = Mock(
        return_value=StudentProfile(
            student_id="STU-001",
            grade_level=7,
            vocabulary_list=[
                VocabularyEntry(
                    word="photosynthesis",
                    first_seen=datetime(2025, 11, 10, tzinfo=timezone.utc),
                    usage_count=3,
                    contexts=["science"],
                )
            ],
            proficiency_score=75.5,
        )
    )
    
    # Mock create method (sync)
    mock_repo.create = Mock(
        return_value=StudentProfile(
            student_id="STU-002",
            grade_level=8,
            vocabulary_list=[],
            proficiency_score=0.0,
        )
    )
    
    # Mock update method (sync)
    mock_repo.update = Mock(
        return_value=StudentProfile(
            student_id="STU-001",
            grade_level=8,
            vocabulary_list=[
                VocabularyEntry(
                    word="photosynthesis",
                    first_seen=datetime(2025, 11, 10, tzinfo=timezone.utc),
                    usage_count=3,
                    contexts=["science"],
                )
            ],
            proficiency_score=75.5,
        )
    )
    
    # Mock list_by_grade_level method (sync)
    mock_repo.list_by_grade_level = Mock(
        return_value=[
            StudentProfile(
                student_id="STU-001",
                grade_level=7,
                vocabulary_list=[],
                proficiency_score=75.5,
            ),
            StudentProfile(
                student_id="STU-002",
                grade_level=7,
                vocabulary_list=[],
                proficiency_score=80.0,
            ),
        ]
    )
    
    yield mock_repo


class TestGetStudentProfile:
    """Test GET /api/v1/students/{student_id}/profile endpoint."""

    def test_get_profile_success(self):
        """Test successful profile retrieval."""
        app.dependency_overrides[get_student_repository] = mock_get_student_repository
        
        try:
            client = TestClient(app)
            response = client.get("/api/v1/students/STU-001/profile")
            
            assert response.status_code == 200
            data = response.json()
            assert data["student_id"] == "STU-001"
            assert data["grade_level"] == 7
            assert data["vocabulary_size"] == 1
            assert data["proficiency_score"] == 75.5
        finally:
            app.dependency_overrides.clear()

    def test_get_profile_not_found(self):
        """Test profile retrieval when student doesn't exist."""
        mock_repo = Mock()
        mock_repo.get = Mock(return_value=None)
        
        def mock_repo_gen():
            yield mock_repo
        
        app.dependency_overrides[get_student_repository] = mock_repo_gen
        
        try:
            client = TestClient(app)
            response = client.get("/api/v1/students/STU-999/profile")
            
            assert response.status_code == 404
            data = response.json()
            assert "detail" in data
            detail = data["detail"]
            assert "error" in detail
            assert "not_found" in detail["error"] or "student" in detail["error"].lower()
        finally:
            app.dependency_overrides.clear()

    def test_get_profile_invalid_id_format(self):
        """Test profile retrieval with invalid student ID format."""
        app.dependency_overrides[get_student_repository] = mock_get_student_repository
        
        try:
            client = TestClient(app)
            response = client.get("/api/v1/students/INVALID/profile")
            
            # Should return 400 for invalid format
            assert response.status_code == 400
        finally:
            app.dependency_overrides.clear()


class TestListStudents:
    """Test GET /api/v1/students endpoint."""

    def test_list_students_all(self):
        """Test listing all students (requires grade_level filter)."""
        app.dependency_overrides[get_student_repository] = mock_get_student_repository
        
        try:
            client = TestClient(app)
            # Without grade_level filter, returns empty list (MVP limitation)
            response = client.get("/api/v1/students")
            
            assert response.status_code == 200
            data = response.json()
            assert "students" in data
            assert "total" in data
            # Currently returns empty list when no grade_level filter
            assert len(data["students"]) == 0
            assert data["total"] == 0
        finally:
            app.dependency_overrides.clear()

    def test_list_students_by_grade(self):
        """Test listing students filtered by grade level."""
        app.dependency_overrides[get_student_repository] = mock_get_student_repository
        
        try:
            client = TestClient(app)
            response = client.get("/api/v1/students?grade_level=7")
            
            assert response.status_code == 200
            data = response.json()
            assert len(data["students"]) == 2
            assert all(s["grade_level"] == 7 for s in data["students"])
        finally:
            app.dependency_overrides.clear()


class TestCreateStudent:
    """Test POST /api/v1/students endpoint."""

    def test_create_student_success(self):
        """Test successful student creation."""
        # Create a mock that returns None for get (student doesn't exist)
        mock_repo = Mock()
        mock_repo.get = Mock(return_value=None)  # Student doesn't exist
        mock_repo.create = Mock(
            return_value=StudentProfile(
                student_id="STU-002",
                grade_level=8,
                vocabulary_list=[],
                proficiency_score=0.0,
            )
        )
        
        def mock_repo_gen():
            yield mock_repo
        
        app.dependency_overrides[get_student_repository] = mock_repo_gen
        
        try:
            client = TestClient(app)
            response = client.post(
                "/api/v1/students",
                json={
                    "student_id": "STU-002",
                    "grade_level": 8,
                },
            )
            
            assert response.status_code == 201
            data = response.json()
            assert data["student_id"] == "STU-002"
            assert data["grade_level"] == 8
        finally:
            app.dependency_overrides.clear()

    def test_create_student_invalid_request(self):
        """Test student creation with invalid request."""
        app.dependency_overrides[get_student_repository] = mock_get_student_repository
        
        try:
            client = TestClient(app)
            response = client.post(
                "/api/v1/students",
                json={
                    "student_id": "INVALID",
                    "grade_level": 5,  # Invalid grade level
                },
            )
            
            assert response.status_code == 422  # Validation error
        finally:
            app.dependency_overrides.clear()


class TestUpdateStudent:
    """Test PUT /api/v1/students/{student_id} endpoint."""

    def test_update_student_success(self):
        """Test successful student update."""
        app.dependency_overrides[get_student_repository] = mock_get_student_repository
        
        try:
            client = TestClient(app)
            response = client.put(
                "/api/v1/students/STU-001",
                json={
                    "grade_level": 8,
                },
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["student_id"] == "STU-001"
            assert data["grade_level"] == 8
        finally:
            app.dependency_overrides.clear()

    def test_update_student_not_found(self):
        """Test update when student doesn't exist."""
        mock_repo = Mock()
        mock_repo.get = Mock(return_value=None)
        mock_repo.update = Mock(return_value=None)
        
        def mock_repo_gen():
            yield mock_repo
        
        app.dependency_overrides[get_student_repository] = mock_repo_gen
        
        try:
            client = TestClient(app)
            response = client.put(
                "/api/v1/students/STU-999",
                json={
                    "grade_level": 8,
                },
            )
            
            assert response.status_code == 404
        finally:
            app.dependency_overrides.clear()

    def test_update_student_invalid_request(self):
        """Test update with invalid request data."""
        app.dependency_overrides[get_student_repository] = mock_get_student_repository
        
        try:
            client = TestClient(app)
            response = client.put(
                "/api/v1/students/STU-001",
                json={
                    "grade_level": 5,  # Invalid grade level
                },
            )
            
            assert response.status_code == 422  # Validation error
        finally:
            app.dependency_overrides.clear()

