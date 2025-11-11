"""Configuration management system for Vocabulator.

This module provides type-safe configuration loading from environment variables
with validation and support for multiple environments (development, staging, production).
"""

import os
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator, model_validator


class Environment(str, Enum):
    """Supported deployment environments."""

    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class LogLevel(str, Enum):
    """Supported log levels."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class MissingConfigError(Exception):
    """Raised when required configuration is missing."""

    def __init__(self, missing_keys: list[str]):
        """Initialize error with list of missing configuration keys."""
        self.missing_keys = missing_keys
        keys_str = ", ".join(missing_keys)
        super().__init__(
            f"Missing required configuration: {keys_str}. "
            "Please set these environment variables."
        )


class Config(BaseModel):
    """Application configuration loaded from environment variables.

    All configuration values are loaded from environment variables with
    validation and type safety provided by Pydantic.
    """

    model_config = {
        "extra": "ignore",
        "case_sensitive": False,
    }

    # Environment
    environment: Environment = Field(
        default=Environment.DEVELOPMENT,
        description="Deployment environment (development, staging, production)",
    )

    # AWS Configuration
    aws_region: str = Field(
        default="us-east-1",
        description="AWS region for all services",
    )
    aws_access_key_id: str = Field(
        ...,
        description="AWS access key ID (required)",
    )
    aws_secret_access_key: str = Field(
        ...,
        description="AWS secret access key (required)",
    )

    # AWS Resources
    s3_bucket_name: str = Field(
        ...,
        description="S3 bucket name for storing data (required)",
    )
    dynamodb_table_prefix: str = Field(
        ...,
        description="DynamoDB table name prefix (required)",
    )

    # OpenAI Configuration
    openai_api_key: str = Field(
        ...,
        description="OpenAI API key (required)",
    )

    # Logging
    log_level: LogLevel = Field(
        default=LogLevel.INFO,
        description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
    )

    # LocalStack (optional, for local development)
    localstack_endpoint_url: Optional[str] = Field(
        default=None,
        description="LocalStack endpoint URL for local AWS emulation (optional)",
    )

    # CORS Configuration
    cors_allowed_origins: Optional[str] = Field(
        default=None,
        description="Comma-separated list of allowed CORS origins (optional, defaults to localhost:3000 in dev)",
    )

    @field_validator("environment", mode="before")
    @classmethod
    def validate_environment(cls, v: Any) -> str:
        """Validate environment value."""
        if isinstance(v, str):
            v = v.lower()
        return v

    @field_validator("log_level", mode="before")
    @classmethod
    def validate_log_level(cls, v: Any) -> str:
        """Validate log level value."""
        if isinstance(v, str):
            v = v.upper()
        return v

    @model_validator(mode="after")
    def validate_required_fields(self) -> "Config":
        """Validate that all required fields are present."""
        missing_keys = []

        # Check required string fields
        required_fields = [
            ("aws_access_key_id", "AWS_ACCESS_KEY_ID"),
            ("aws_secret_access_key", "AWS_SECRET_ACCESS_KEY"),
            ("s3_bucket_name", "S3_BUCKET_NAME"),
            ("dynamodb_table_prefix", "DYNAMODB_TABLE_PREFIX"),
            ("openai_api_key", "OPENAI_API_KEY"),
        ]

        for field_name, env_key in required_fields:
            value = getattr(self, field_name, None)
            if not value or (isinstance(value, str) and not value.strip()):
                missing_keys.append(env_key)

        if missing_keys:
            raise MissingConfigError(missing_keys)

        return self

    def get_dynamodb_table_name(self, table_suffix: str) -> str:
        """Get full DynamoDB table name with prefix.

        Args:
            table_suffix: Table name suffix (e.g., 'students', 'vocabulary')

        Returns:
            Full table name: {prefix}-{suffix}
        """
        return f"{self.dynamodb_table_prefix}-{table_suffix}"

    def get_aws_endpoint_url(self) -> Optional[str]:
        """Get AWS endpoint URL (LocalStack for dev, None for production).

        Returns:
            LocalStack endpoint URL if in development, None otherwise
        """
        if self.environment == Environment.DEVELOPMENT and self.localstack_endpoint_url:
            return self.localstack_endpoint_url
        return None

    def get_cors_origins(self) -> list[str]:
        """Get CORS allowed origins.

        Returns:
            List of allowed origins, defaults to localhost:3000 in development
        """
        if self.cors_allowed_origins:
            return [origin.strip() for origin in self.cors_allowed_origins.split(",")]
        
        # Default: allow localhost in development, empty list in production
        if self.environment == Environment.DEVELOPMENT:
            return ["http://localhost:3000", "http://localhost:8000"]
        
        return []


# Global config instance (lazy-loaded)
_config: Optional[Config] = None


def load_config() -> Config:
    """Load configuration from environment variables.

    Configuration is loaded from:
    1. Environment variables (highest priority)
    2. .env file in project root (if exists, via python-dotenv)
    3. Default values (lowest priority)

    Returns:
        Config instance with all configuration values

    Raises:
        MissingConfigError: If required configuration is missing
        ValidationError: If configuration values are invalid
    """
    global _config

    if _config is None:
        # Load .env file if it exists
        try:
            from dotenv import load_dotenv

            load_dotenv()
        except ImportError:
            # python-dotenv not installed, skip .env loading
            pass

        # Build config dict from environment variables
        config_dict: dict[str, Any] = {}

        # Map environment variables to config fields
        env_mapping = {
            "ENVIRONMENT": "environment",
            "AWS_REGION": "aws_region",
            "AWS_ACCESS_KEY_ID": "aws_access_key_id",
            "AWS_SECRET_ACCESS_KEY": "aws_secret_access_key",
            "S3_BUCKET_NAME": "s3_bucket_name",
            "DYNAMODB_TABLE_PREFIX": "dynamodb_table_prefix",
            "OPENAI_API_KEY": "openai_api_key",
            "LOG_LEVEL": "log_level",
            "LOCALSTACK_ENDPOINT_URL": "localstack_endpoint_url",
            "CORS_ALLOWED_ORIGINS": "cors_allowed_origins",
        }

        for env_key, config_key in env_mapping.items():
            env_value = os.getenv(env_key)
            if env_value is not None:
                config_dict[config_key] = env_value

        try:
            _config = Config(**config_dict)
        except Exception as e:
            # Check if it's a missing field error from Pydantic
            if "Field required" in str(e) or "missing" in str(e).lower():
                # Extract missing fields from error or check manually
                missing_keys = []
                required_fields = [
                    "AWS_ACCESS_KEY_ID",
                    "AWS_SECRET_ACCESS_KEY",
                    "S3_BUCKET_NAME",
                    "DYNAMODB_TABLE_PREFIX",
                    "OPENAI_API_KEY",
                ]
                for env_key in required_fields:
                    if env_key not in os.environ or not os.getenv(env_key):
                        missing_keys.append(env_key)
                if missing_keys:
                    raise MissingConfigError(missing_keys) from e
            raise

    return _config


def get_config() -> Config:
    """Get the current configuration instance.

    Returns:
        Config instance (loads if not already loaded)

    Raises:
        MissingConfigError: If required configuration is missing
    """
    return load_config()


def reset_config() -> None:
    """Reset the global config instance (useful for testing)."""
    global _config
    _config = None

