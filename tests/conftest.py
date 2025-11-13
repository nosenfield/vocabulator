"""Pytest configuration and shared fixtures for Vocabulator tests.

This module provides common fixtures and test configuration used across
all test modules in the Vocabulator project.
"""

import os
from pathlib import Path
from typing import Generator

import pytest

# Set environment variables before any imports that need config
# This must happen at module load time, before pytest collects tests
os.environ.setdefault("AWS_REGION", "us-east-1")
os.environ.setdefault("AWS_ACCESS_KEY_ID", "test")
os.environ.setdefault("AWS_SECRET_ACCESS_KEY", "test")
os.environ.setdefault("DYNAMODB_TABLE_PREFIX", "test")
os.environ.setdefault("S3_BUCKET_NAME", "test-bucket")
os.environ.setdefault("OPENAI_API_KEY", "test-key")
os.environ.setdefault("LOCALSTACK_ENDPOINT_URL", "http://localhost:4566")
os.environ.setdefault("ENVIRONMENT", "development")


# Pytest markers configuration
pytest_plugins = []


@pytest.fixture
def project_root() -> Path:
    """Return the project root directory."""
    return Path(__file__).parent.parent


@pytest.fixture
def test_data_dir(project_root: Path) -> Path:
    """Return the test fixtures directory."""
    return project_root / "tests" / "fixtures"


@pytest.fixture
def sample_transcripts_dir(test_data_dir: Path) -> Path:
    """Return the sample transcripts directory."""
    return test_data_dir / "sample_transcripts"


@pytest.fixture
def temp_env_vars(monkeypatch):
    """Fixture to temporarily set environment variables for testing."""
    env_vars = {}

    def set_env(**kwargs):
        """Set environment variables."""
        for key, value in kwargs.items():
            monkeypatch.setenv(key, value)
            env_vars[key] = value

    def cleanup():
        """Clean up environment variables."""
        for key in env_vars:
            monkeypatch.delenv(key, raising=False)

    yield set_env
    cleanup()


@pytest.fixture
def mock_aws_credentials(temp_env_vars):
    """Set mock AWS credentials for LocalStack testing."""
    temp_env_vars(
        AWS_REGION="us-east-1",
        AWS_ACCESS_KEY_ID="test",
        AWS_SECRET_ACCESS_KEY="test",
        LOCALSTACK_ENDPOINT_URL="http://localhost:4566",
    )


@pytest.fixture(autouse=True)
def reset_logging():
    """Reset logging configuration before each test."""
    import logging

    # Clear all handlers
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
    logging.root.setLevel(logging.WARNING)


# Markers for test categorization
def pytest_configure(config):
    """Register custom pytest markers."""
    config.addinivalue_line("markers", "unit: Unit tests (fast, isolated)")
    config.addinivalue_line("markers", "integration: Integration tests (require external services)")
    config.addinivalue_line("markers", "slow: Slow running tests")
    config.addinivalue_line("markers", "aws: Tests that require AWS services (LocalStack or real)")
    config.addinivalue_line("markers", "openai: Tests that require OpenAI API (mocked or real)")

