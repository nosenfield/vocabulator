"""Tests for logging utility system.

This module tests structured JSON logging, correlation IDs, log levels,
and sensitive data masking.
"""

import json
import logging
import sys
from contextvars import ContextVar
from io import StringIO
from unittest.mock import patch

import pytest

from src.utils.config import Environment, LogLevel
from src.utils.logger import (
    JSONFormatter,
    get_logger,
    mask_sensitive_data,
    set_correlation_id,
    get_correlation_id,
    configure_logging,
)


@pytest.mark.unit
class TestJSONFormatter:
    """Test JSON log formatter."""

    def test_json_formatter_outputs_valid_json(self):
        """Test that JSON formatter outputs valid JSON."""
        formatter = JSONFormatter()
        handler = logging.StreamHandler(StringIO())
        handler.setFormatter(formatter)

        logger = logging.getLogger("test")
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

        logger.info("Test message")

        # Get output
        output = handler.stream.getvalue()
        log_data = json.loads(output)

        assert isinstance(log_data, dict)
        assert log_data["level"] == "INFO"
        assert log_data["message"] == "Test message"
        assert "timestamp" in log_data
        assert "module" in log_data

    def test_json_formatter_includes_extra_fields(self):
        """Test that JSON formatter includes extra fields."""
        formatter = JSONFormatter()
        handler = logging.StreamHandler(StringIO())
        handler.setFormatter(formatter)

        logger = logging.getLogger("test")
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

        logger.info("Test message", extra={"student_id": "STU-001", "custom_field": "value"})

        output = handler.stream.getvalue()
        log_data = json.loads(output)

        # Student ID should be masked
        assert log_data["student_id"] == "STU-***"
        assert log_data["custom_field"] == "value"

    def test_json_formatter_includes_exception_info(self):
        """Test that JSON formatter includes exception information."""
        formatter = JSONFormatter()
        handler = logging.StreamHandler(StringIO())
        handler.setFormatter(formatter)

        logger = logging.getLogger("test")
        logger.addHandler(handler)
        logger.setLevel(logging.ERROR)

        try:
            raise ValueError("Test error")
        except ValueError:
            logger.exception("Exception occurred")

        output = handler.stream.getvalue()
        log_data = json.loads(output)

        assert "exception" in log_data
        assert "ValueError" in log_data["exception"]
        assert "Test error" in log_data["exception"]


@pytest.mark.unit
class TestCorrelationID:
    """Test correlation ID functionality."""

    def test_set_correlation_id(self):
        """Test setting correlation ID."""
        cid = set_correlation_id("test-correlation-id")
        assert cid == "test-correlation-id"

    def test_get_correlation_id_returns_set_value(self):
        """Test getting correlation ID returns set value."""
        cid = set_correlation_id("test-123")
        assert get_correlation_id() == "test-123"

    def test_get_correlation_id_generates_new_if_not_set(self):
        """Test that get_correlation_id generates new ID if not set."""
        # Reset context
        correlation_id: ContextVar[str] = ContextVar("correlation_id", default=None)
        correlation_id.set(None)

        cid = get_correlation_id()
        assert cid is not None
        assert len(cid) > 0

    def test_correlation_id_in_logs(self):
        """Test that correlation ID appears in logs."""
        set_correlation_id("test-cid-123")

        formatter = JSONFormatter()
        handler = logging.StreamHandler(StringIO())
        handler.setFormatter(formatter)

        logger = logging.getLogger("test")
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

        logger.info("Test message")

        output = handler.stream.getvalue()
        log_data = json.loads(output)

        assert log_data["correlation_id"] == "test-cid-123"


@pytest.mark.unit
class TestSensitiveDataMasking:
    """Test sensitive data masking."""

    def test_mask_api_key(self):
        """Test that API keys are masked."""
        from src.utils.logger import mask_sensitive_data
        
        masked = mask_sensitive_data("sk-1234567890abcdef")
        assert masked == "sk-***"
        assert "1234567890abcdef" not in masked

    def test_mask_student_id(self):
        """Test that student IDs are masked."""
        masked = mask_sensitive_data("STU-001")
        assert masked == "STU-***"
        assert "001" not in masked

    def test_mask_aws_secret_key(self):
        """Test that AWS secret keys are masked."""
        masked = mask_sensitive_data("wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY")
        assert "***" in masked
        assert "wJalrXUtnFEMI" not in masked

    def test_non_sensitive_data_not_masked(self):
        """Test that non-sensitive data is not masked."""
        assert mask_sensitive_data("normal-text") == "normal-text"
        assert mask_sensitive_data("12345") == "12345"

    def test_mask_in_logs(self):
        """Test that sensitive data is masked in log output."""
        formatter = JSONFormatter()
        handler = logging.StreamHandler(StringIO())
        handler.setFormatter(formatter)

        logger = logging.getLogger("test")
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

        logger.info("API key is sk-1234567890abcdef", extra={"api_key": "sk-1234567890abcdef"})

        output = handler.stream.getvalue()
        log_data = json.loads(output)

        # Message should be masked
        assert "sk-***" in log_data["message"]
        # Extra field should be masked
        assert log_data.get("api_key") == "sk-***"


@pytest.mark.unit
class TestLoggerFactory:
    """Test logger factory function."""

    @patch("src.utils.logger.get_config")
    def test_get_logger_returns_logger(self, mock_config):
        """Test that get_logger returns a logger instance."""
        from src.utils.config import Config, Environment, LogLevel
        
        mock_config.return_value = Config(
            environment=Environment.DEVELOPMENT,
            aws_region="us-east-1",
            aws_access_key_id="test",
            aws_secret_access_key="test",
            s3_bucket_name="test-bucket",
            dynamodb_table_prefix="test",
            openai_api_key="sk-test",
            log_level=LogLevel.INFO,
        )
        
        logger = get_logger("test_module")
        assert isinstance(logger, logging.Logger)
        assert logger.name == "vocabulator.test_module"

    @patch("src.utils.logger.get_config")
    def test_get_logger_uses_correct_name_prefix(self, mock_config):
        """Test that logger names use vocabulator prefix."""
        from src.utils.config import Config, Environment, LogLevel
        
        mock_config.return_value = Config(
            environment=Environment.DEVELOPMENT,
            aws_region="us-east-1",
            aws_access_key_id="test",
            aws_secret_access_key="test",
            s3_bucket_name="test-bucket",
            dynamodb_table_prefix="test",
            openai_api_key="sk-test",
            log_level=LogLevel.INFO,
        )
        
        logger1 = get_logger("api")
        logger2 = get_logger("processing")

        assert logger1.name == "vocabulator.api"
        assert logger2.name == "vocabulator.processing"

    @patch("src.utils.logger.get_config")
    def test_get_logger_includes_correlation_id(self, mock_config):
        """Test that logger includes correlation ID in logs."""
        from src.utils.config import Config, Environment, LogLevel
        
        mock_config.return_value = Config(
            environment=Environment.DEVELOPMENT,
            aws_region="us-east-1",
            aws_access_key_id="test",
            aws_secret_access_key="test",
            s3_bucket_name="test-bucket",
            dynamodb_table_prefix="test",
            openai_api_key="sk-test",
            log_level=LogLevel.INFO,
        )
        
        set_correlation_id("test-cid")

        logger = get_logger("test")
        handler = logging.StreamHandler(StringIO())
        handler.setFormatter(JSONFormatter())
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

        logger.info("Test message")

        output = handler.stream.getvalue()
        log_data = json.loads(output)

        assert log_data["correlation_id"] == "test-cid"


@pytest.mark.unit
class TestLogLevelConfiguration:
    """Test log level configuration per environment."""

    def test_development_log_level(self):
        """Test that development uses DEBUG level."""
        with patch("src.utils.logger.get_config") as mock_config:
            mock_config.return_value.environment = Environment.DEVELOPMENT
            mock_config.return_value.log_level = LogLevel.DEBUG

            configure_logging()
            logger = logging.getLogger("vocabulator")
            assert logger.level == logging.DEBUG

    def test_production_log_level(self):
        """Test that production uses INFO level."""
        with patch("src.utils.logger.get_config") as mock_config:
            mock_config.return_value.environment = Environment.PRODUCTION
            mock_config.return_value.log_level = LogLevel.INFO

            configure_logging()
            logger = logging.getLogger("vocabulator")
            assert logger.level == logging.INFO

    def test_staging_log_level(self):
        """Test that staging uses INFO level."""
        with patch("src.utils.logger.get_config") as mock_config:
            mock_config.return_value.environment = Environment.STAGING
            mock_config.return_value.log_level = LogLevel.INFO

            configure_logging()
            logger = logging.getLogger("vocabulator")
            assert logger.level == logging.INFO


@pytest.mark.unit
class TestCloudWatchIntegration:
    """Test CloudWatch Logs integration (stub for local)."""

    def test_cloudwatch_handler_not_added_in_development(self):
        """Test that CloudWatch handler is not added in development."""
        with patch("src.utils.logger.get_config") as mock_config:
            mock_config.return_value.environment = Environment.DEVELOPMENT

            configure_logging()
            logger = logging.getLogger("vocabulator")

            # Should not have CloudWatch handler in dev
            cloudwatch_handlers = [
                h for h in logger.handlers if "cloudwatch" in str(type(h)).lower()
            ]
            assert len(cloudwatch_handlers) == 0

    @patch("src.utils.logger.get_config")
    def test_cloudwatch_handler_stub_exists(self, mock_config):
        """Test that CloudWatch handler stub exists (for future implementation)."""
        from src.utils.config import Config, Environment, LogLevel
        
        mock_config.return_value = Config(
            environment=Environment.DEVELOPMENT,
            aws_region="us-east-1",
            aws_access_key_id="test",
            aws_secret_access_key="test",
            s3_bucket_name="test-bucket",
            dynamodb_table_prefix="test",
            openai_api_key="sk-test",
            log_level=LogLevel.INFO,
        )
        
        # This test verifies the structure is in place
        # Actual CloudWatch integration will be implemented in infrastructure phase
        from src.utils.logger import _create_cloudwatch_handler

        # Should not raise error (stub implementation)
        handler = _create_cloudwatch_handler()
        assert handler is None or isinstance(handler, logging.Handler)

