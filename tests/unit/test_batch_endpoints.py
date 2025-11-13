"""Tests for batch processing endpoints.

This module tests the batch job submission and status endpoints.
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import Mock
from fastapi.testclient import TestClient

from src.api.dependencies import get_batch_client
from src.api.main import app
from src.api.models.requests import BatchProcessRequest
from src.api.models.responses import BatchProcessResponse, BatchStatusResponse
from src.processing.batch_client import BatchClient, BatchJobInfo, BatchJobStatus


# Mock dependencies
def mock_get_batch_client():
    """Mock batch client dependency."""
    mock_client = Mock(spec=BatchClient)
    
    # Mock submit_job method
    mock_client.submit_job = Mock(return_value="job-12345")
    
    # Mock get_job_status method
    mock_client.get_job_status = Mock(
        return_value=BatchJobInfo(
            job_id="job-12345",
            job_name="batch-process-20251111-120000",
            status=BatchJobStatus.RUNNING,
            created_at=datetime(2025, 11, 11, 12, 0, 0, tzinfo=timezone.utc),
            started_at=datetime(2025, 11, 11, 12, 1, 0, tzinfo=timezone.utc),
            stopped_at=None,
            exit_code=None,
            status_reason=None,
        )
    )
    
    yield mock_client


class TestBatchProcessEndpoint:
    """Test POST /api/v1/batch/process endpoint."""

    def test_submit_batch_job_success(self):
        """Test successful batch job submission."""
        app.dependency_overrides[get_batch_client] = mock_get_batch_client
        
        try:
            client = TestClient(app)
            response = client.post(
                "/api/v1/batch/process",
                json={
                    "student_ids": ["STU-001", "STU-002"],
                    "s3_paths": [
                        "s3://bucket/transcripts/STU-001.txt",
                        "s3://bucket/transcripts/STU-002.txt",
                    ],
                    "grade_level": 7,
                },
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["job_id"] == "job-12345"
            assert "message" in data
        finally:
            app.dependency_overrides.clear()

    def test_submit_batch_job_invalid_request(self):
        """Test submission with invalid request."""
        app.dependency_overrides[get_batch_client] = mock_get_batch_client
        
        try:
            client = TestClient(app)
            response = client.post(
                "/api/v1/batch/process",
                json={
                    "student_ids": [],  # Empty list
                    "s3_paths": ["s3://bucket/file.txt"],
                    "grade_level": 7,
                },
            )
            
            assert response.status_code == 422  # Validation error
        finally:
            app.dependency_overrides.clear()

    def test_submit_batch_job_mismatched_lengths(self):
        """Test submission with mismatched student_ids and s3_paths lengths."""
        app.dependency_overrides[get_batch_client] = mock_get_batch_client
        
        try:
            client = TestClient(app)
            response = client.post(
                "/api/v1/batch/process",
                json={
                    "student_ids": ["STU-001", "STU-002"],
                    "s3_paths": ["s3://bucket/file.txt"],  # Only 1 path for 2 students
                    "grade_level": 7,
                },
            )
            
            assert response.status_code == 422  # Validation error (Pydantic validates this)
        finally:
            app.dependency_overrides.clear()

    def test_submit_batch_job_invalid_grade_level(self):
        """Test submission with invalid grade level."""
        app.dependency_overrides[get_batch_client] = mock_get_batch_client
        
        try:
            client = TestClient(app)
            response = client.post(
                "/api/v1/batch/process",
                json={
                    "student_ids": ["STU-001"],
                    "s3_paths": ["s3://bucket/file.txt"],
                    "grade_level": 5,  # Invalid (must be 6-8)
                },
            )
            
            assert response.status_code == 422  # Validation error
        finally:
            app.dependency_overrides.clear()


class TestBatchStatusEndpoint:
    """Test GET /api/v1/batch/{job_id}/status endpoint."""

    def test_get_batch_status_success(self):
        """Test successful batch status retrieval."""
        app.dependency_overrides[get_batch_client] = mock_get_batch_client
        
        try:
            client = TestClient(app)
            response = client.get("/api/v1/batch/job-12345/status")
            
            assert response.status_code == 200
            data = response.json()
            assert data["job_id"] == "job-12345"
            assert data["status"] == "RUNNING"
            assert "created_at" in data
            assert "started_at" in data
        finally:
            app.dependency_overrides.clear()

    def test_get_batch_status_not_found(self):
        """Test status retrieval when job doesn't exist."""
        mock_client = Mock(spec=BatchClient)
        mock_client.get_job_status = Mock(return_value=None)
        
        def mock_client_gen():
            yield mock_client
        
        app.dependency_overrides[get_batch_client] = mock_client_gen
        
        try:
            client = TestClient(app)
            response = client.get("/api/v1/batch/nonexistent-job/status")
            
            assert response.status_code == 404
        finally:
            app.dependency_overrides.clear()

    def test_get_batch_status_completed(self):
        """Test status retrieval for completed job."""
        mock_client = Mock(spec=BatchClient)
        mock_client.get_job_status = Mock(
            return_value=BatchJobInfo(
                job_id="job-12345",
                job_name="batch-process-20251111-120000",
                status=BatchJobStatus.SUCCEEDED,
                created_at=datetime(2025, 11, 11, 12, 0, 0, tzinfo=timezone.utc),
                started_at=datetime(2025, 11, 11, 12, 1, 0, tzinfo=timezone.utc),
                stopped_at=datetime(2025, 11, 11, 12, 15, 0, tzinfo=timezone.utc),
                exit_code=0,
                status_reason=None,
            )
        )
        
        def mock_client_gen():
            yield mock_client
        
        app.dependency_overrides[get_batch_client] = mock_client_gen
        
        try:
            client = TestClient(app)
            response = client.get("/api/v1/batch/job-12345/status")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "SUCCEEDED"
            assert data["stopped_at"] is not None
            assert data["progress"] == 100  # Completed jobs have 100% progress
        finally:
            app.dependency_overrides.clear()

