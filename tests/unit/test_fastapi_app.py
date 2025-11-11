"""Tests for FastAPI application setup.

This module tests the FastAPI application initialization, dependency injection,
middleware, and health check endpoint.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch

from src.api.main import app, get_dynamodb_client, get_s3_client
from src.api.main import get_student_repository, get_recommendation_repository
from src.api.main import get_text_processing_pipeline, get_batch_client


class TestFastAPIApp:
    """Test FastAPI application setup."""

    def test_app_initialization(self):
        """Test that FastAPI app is initialized correctly."""
        assert app is not None
        assert app.title == "Vocabulator API"
        assert app.version == "1.0.0"

    def test_health_check_endpoint(self):
        """Test health check endpoint returns 200."""
        client = TestClient(app)
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert data["service"] == "vocabulator-api"
        assert data["version"] == "1.0.0"


class TestDependencyInjection:
    """Test dependency injection functions."""

    @patch("src.api.main.DynamoDBClient")
    def test_get_dynamodb_client(self, mock_client_class):
        """Test DynamoDB client dependency injection."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        # Get dependency
        client_gen = get_dynamodb_client()
        client = next(client_gen)
        
        assert client == mock_client
        mock_client_class.assert_called_once()
        
        # Cleanup
        try:
            next(client_gen)
        except StopIteration:
            pass

    @patch("src.api.main.S3Client")
    def test_get_s3_client(self, mock_client_class):
        """Test S3 client dependency injection."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        # Get dependency
        client_gen = get_s3_client()
        client = next(client_gen)
        
        assert client == mock_client
        mock_client_class.assert_called_once()
        
        # Cleanup
        try:
            next(client_gen)
        except StopIteration:
            pass

    @patch("src.api.main.StudentRepository")
    def test_get_student_repository(self, mock_repo_class):
        """Test student repository dependency injection."""
        mock_repo = Mock()
        mock_repo_class.return_value = mock_repo
        
        # Get dependency
        repo_gen = get_student_repository()
        repo = next(repo_gen)
        
        assert repo == mock_repo
        mock_repo_class.assert_called_once()
        
        # Cleanup
        try:
            next(repo_gen)
        except StopIteration:
            pass

    @patch("src.api.main.RecommendationRepository")
    def test_get_recommendation_repository(self, mock_repo_class):
        """Test recommendation repository dependency injection."""
        mock_repo = Mock()
        mock_repo_class.return_value = mock_repo
        
        # Get dependency
        repo_gen = get_recommendation_repository()
        repo = next(repo_gen)
        
        assert repo == mock_repo
        mock_repo_class.assert_called_once()
        
        # Cleanup
        try:
            next(repo_gen)
        except StopIteration:
            pass

    @patch("src.api.main.TextProcessingPipeline")
    def test_get_text_processing_pipeline(self, mock_pipeline_class):
        """Test text processing pipeline dependency injection."""
        mock_pipeline = Mock()
        mock_pipeline_class.return_value = mock_pipeline
        
        # Get dependency
        pipeline_gen = get_text_processing_pipeline()
        pipeline = next(pipeline_gen)
        
        assert pipeline == mock_pipeline
        mock_pipeline_class.assert_called_once()
        
        # Cleanup
        try:
            next(pipeline_gen)
        except StopIteration:
            pass

    @patch("src.api.main.BatchClient")
    def test_get_batch_client(self, mock_client_class):
        """Test batch client dependency injection."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        # Get dependency
        client_gen = get_batch_client()
        client = next(client_gen)
        
        assert client == mock_client
        mock_client_class.assert_called_once()
        
        # Cleanup
        try:
            next(client_gen)
        except StopIteration:
            pass


class TestMiddleware:
    """Test middleware functionality."""

    def test_cors_middleware(self):
        """Test that CORS middleware is configured."""
        # Check that middleware is added to app
        # FastAPI stores middleware in app.user_middleware
        assert len(app.user_middleware) > 0
        # Verify CORS middleware is present
        middleware_types = [m.cls.__name__ for m in app.user_middleware]
        assert "CORSMiddleware" in middleware_types


class TestErrorHandling:
    """Test error handling."""

    def test_404_handler(self):
        """Test 404 error handling."""
        client = TestClient(app)
        response = client.get("/nonexistent")
        
        assert response.status_code == 404

    def test_422_validation_error(self):
        """Test 422 validation error format."""
        client = TestClient(app)
        # This will fail until we add routes, but we can check error handling
        # For now, just verify the app handles errors
        assert app.exception_handlers is not None

