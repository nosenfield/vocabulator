"""Tests for configuration management system.

This module tests the configuration loading, validation, and environment
switching functionality.
"""

import os
from typing import Any

import pytest

from src.utils.config import (
    Config,
    Environment,
    load_config,
    MissingConfigError,
    reset_config,
)


@pytest.mark.unit
class TestConfigLoading:
    """Test configuration loading from environment variables."""

    def setup_method(self):
        """Reset config before each test."""
        reset_config()

    def test_load_config_with_all_required_vars(self, temp_env_vars):
        """Test loading config with all required environment variables."""
        temp_env_vars(
            ENVIRONMENT="development",
            AWS_REGION="us-east-1",
            AWS_ACCESS_KEY_ID="test-key",
            AWS_SECRET_ACCESS_KEY="test-secret",
            OPENAI_API_KEY="sk-test123",
            S3_BUCKET_NAME="vocabulator-data-dev",
            DYNAMODB_TABLE_PREFIX="vocabulator-dev",
            LOG_LEVEL="INFO",
        )

        config = load_config()

        assert config.environment == Environment.DEVELOPMENT
        assert config.aws_region == "us-east-1"
        assert config.aws_access_key_id == "test-key"
        assert config.aws_secret_access_key == "test-secret"
        assert config.openai_api_key == "sk-test123"
        assert config.s3_bucket_name == "vocabulator-data-dev"
        assert config.dynamodb_table_prefix == "vocabulator-dev"
        assert config.log_level == "INFO"

    def test_load_config_missing_required_var(self, temp_env_vars):
        """Test that missing required config raises clear error."""
        # Set only some variables, missing OPENAI_API_KEY
        temp_env_vars(
            ENVIRONMENT="development",
            AWS_REGION="us-east-1",
            AWS_ACCESS_KEY_ID="test-key",
            AWS_SECRET_ACCESS_KEY="test-secret",
            S3_BUCKET_NAME="vocabulator-data-dev",
            DYNAMODB_TABLE_PREFIX="vocabulator-dev",
            LOG_LEVEL="INFO",
        )

        with pytest.raises(MissingConfigError) as exc_info:
            load_config()

        assert "OPENAI_API_KEY" in str(exc_info.value)
        assert "required" in str(exc_info.value).lower()

    def test_load_config_with_optional_localstack(self, temp_env_vars):
        """Test loading config with optional LocalStack endpoint."""
        temp_env_vars(
            ENVIRONMENT="development",
            AWS_REGION="us-east-1",
            AWS_ACCESS_KEY_ID="test-key",
            AWS_SECRET_ACCESS_KEY="test-secret",
            OPENAI_API_KEY="sk-test123",
            S3_BUCKET_NAME="vocabulator-data-dev",
            DYNAMODB_TABLE_PREFIX="vocabulator-dev",
            LOG_LEVEL="INFO",
            LOCALSTACK_ENDPOINT_URL="http://localhost:4566",
        )

        config = load_config()

        assert config.localstack_endpoint_url == "http://localhost:4566"

    def test_load_config_without_localstack(self, temp_env_vars):
        """Test loading config without LocalStack endpoint (production)."""
        temp_env_vars(
            ENVIRONMENT="production",
            AWS_REGION="us-east-1",
            AWS_ACCESS_KEY_ID="prod-key",
            AWS_SECRET_ACCESS_KEY="prod-secret",
            OPENAI_API_KEY="sk-prod123",
            S3_BUCKET_NAME="vocabulator-data-prod",
            DYNAMODB_TABLE_PREFIX="vocabulator-prod",
            LOG_LEVEL="WARNING",
        )

        config = load_config()

        assert config.localstack_endpoint_url is None


@pytest.mark.unit
class TestEnvironmentSwitching:
    """Test environment switching functionality."""

    def setup_method(self):
        """Reset config before each test."""
        reset_config()

    def test_development_environment(self, temp_env_vars):
        """Test development environment configuration."""
        temp_env_vars(
            ENVIRONMENT="development",
            AWS_REGION="us-east-1",
            AWS_ACCESS_KEY_ID="test",
            AWS_SECRET_ACCESS_KEY="test",
            OPENAI_API_KEY="sk-test",
            S3_BUCKET_NAME="vocabulator-data-dev",
            DYNAMODB_TABLE_PREFIX="vocabulator-dev",
            LOG_LEVEL="DEBUG",
        )

        config = load_config()

        assert config.environment == Environment.DEVELOPMENT
        assert config.log_level == "DEBUG"

    def test_staging_environment(self, temp_env_vars):
        """Test staging environment configuration."""
        temp_env_vars(
            ENVIRONMENT="staging",
            AWS_REGION="us-east-1",
            AWS_ACCESS_KEY_ID="staging-key",
            AWS_SECRET_ACCESS_KEY="staging-secret",
            OPENAI_API_KEY="sk-staging",
            S3_BUCKET_NAME="vocabulator-data-staging",
            DYNAMODB_TABLE_PREFIX="vocabulator-staging",
            LOG_LEVEL="INFO",
        )

        config = load_config()

        assert config.environment == Environment.STAGING
        assert config.log_level == "INFO"

    def test_production_environment(self, temp_env_vars):
        """Test production environment configuration."""
        temp_env_vars(
            ENVIRONMENT="production",
            AWS_REGION="us-east-1",
            AWS_ACCESS_KEY_ID="prod-key",
            AWS_SECRET_ACCESS_KEY="prod-secret",
            OPENAI_API_KEY="sk-prod",
            S3_BUCKET_NAME="vocabulator-data-prod",
            DYNAMODB_TABLE_PREFIX="vocabulator-prod",
            LOG_LEVEL="WARNING",
        )

        config = load_config()

        assert config.environment == Environment.PRODUCTION
        assert config.log_level == "WARNING"

    def test_invalid_environment(self, temp_env_vars):
        """Test that invalid environment raises validation error."""
        temp_env_vars(
            ENVIRONMENT="invalid",
            AWS_REGION="us-east-1",
            AWS_ACCESS_KEY_ID="test",
            AWS_SECRET_ACCESS_KEY="test",
            OPENAI_API_KEY="sk-test",
            S3_BUCKET_NAME="vocabulator-data-dev",
            DYNAMODB_TABLE_PREFIX="vocabulator-dev",
            LOG_LEVEL="INFO",
        )

        with pytest.raises(ValueError):
            load_config()


@pytest.mark.unit
class TestConfigValidation:
    """Test configuration validation."""

    def setup_method(self):
        """Reset config before each test."""
        reset_config()

    def test_log_level_validation(self, temp_env_vars):
        """Test that log level is validated."""
        temp_env_vars(
            ENVIRONMENT="development",
            AWS_REGION="us-east-1",
            AWS_ACCESS_KEY_ID="test",
            AWS_SECRET_ACCESS_KEY="test",
            OPENAI_API_KEY="sk-test",
            S3_BUCKET_NAME="vocabulator-data-dev",
            DYNAMODB_TABLE_PREFIX="vocabulator-dev",
            LOG_LEVEL="INVALID",
        )

        with pytest.raises(ValueError):
            load_config()

    def test_openai_api_key_format(self, temp_env_vars):
        """Test that OpenAI API key has correct format."""
        temp_env_vars(
            ENVIRONMENT="development",
            AWS_REGION="us-east-1",
            AWS_ACCESS_KEY_ID="test",
            AWS_SECRET_ACCESS_KEY="test",
            OPENAI_API_KEY="invalid-key-format",
            S3_BUCKET_NAME="vocabulator-data-dev",
            DYNAMODB_TABLE_PREFIX="vocabulator-dev",
            LOG_LEVEL="INFO",
        )

        # Should still load (format validation can be added later)
        config = load_config()
        assert config.openai_api_key == "invalid-key-format"


@pytest.mark.unit
class TestConfigTypeSafety:
    """Test that config provides type-safe access."""

    def setup_method(self):
        """Reset config before each test."""
        reset_config()

    def test_config_is_pydantic_model(self, temp_env_vars):
        """Test that config is a Pydantic model."""
        temp_env_vars(
            ENVIRONMENT="development",
            AWS_REGION="us-east-1",
            AWS_ACCESS_KEY_ID="test",
            AWS_SECRET_ACCESS_KEY="test",
            OPENAI_API_KEY="sk-test",
            S3_BUCKET_NAME="vocabulator-data-dev",
            DYNAMODB_TABLE_PREFIX="vocabulator-dev",
            LOG_LEVEL="INFO",
        )

        config = load_config()

        assert isinstance(config, Config)
        # Test that we can access attributes
        assert hasattr(config, "environment")
        assert hasattr(config, "aws_region")
        assert hasattr(config, "openai_api_key")

    def test_config_serialization(self, temp_env_vars):
        """Test that config can be serialized to dict."""
        temp_env_vars(
            ENVIRONMENT="development",
            AWS_REGION="us-east-1",
            AWS_ACCESS_KEY_ID="test",
            AWS_SECRET_ACCESS_KEY="test",
            OPENAI_API_KEY="sk-test",
            S3_BUCKET_NAME="vocabulator-data-dev",
            DYNAMODB_TABLE_PREFIX="vocabulator-dev",
            LOG_LEVEL="INFO",
        )

        config = load_config()
        config_dict = config.model_dump()

        assert isinstance(config_dict, dict)
        assert config_dict["environment"] == "development"
        assert config_dict["aws_region"] == "us-east-1"

