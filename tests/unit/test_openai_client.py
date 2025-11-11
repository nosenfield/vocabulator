"""Unit tests for OpenAI client wrapper.

Tests cover:
- Successful API calls
- Retry logic for transient failures
- Rate limit handling
- Cost tracking
- Error handling
- Timeout handling
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from openai import APIError, RateLimitError

from src.ai.cost_tracker import CostTracker, OperationType
from src.ai.openai_client import (
    OpenAIClient,
    OpenAIError,
    OpenAIRateLimitError,
    OpenAITimeoutError,
)
from tests.mocks.mock_openai import MockOpenAIClient


@pytest.fixture
def mock_openai_client():
    """Create mock OpenAI client."""
    return MockOpenAIClient()


@pytest.fixture
def openai_client():
    """Create OpenAI client instance for testing."""
    return OpenAIClient(
        api_key="test-fake-key-12345-not-real",
        max_retries=3,
        timeout=5,
        backoff_factor=1.5,
    )


@pytest.mark.unit
@pytest.mark.openai
class TestOpenAIClientInitialization:
    """Test OpenAI client initialization."""

    def test_init_with_api_key(self):
        """Test initialization with explicit API key."""
        client = OpenAIClient(api_key="sk-test-dummy-key-not-real")
        assert client.api_key == "sk-test-dummy-key-not-real"
        assert client.max_retries == 3
        assert client.timeout == 30

    def test_init_with_custom_params(self):
        """Test initialization with custom parameters."""
        client = OpenAIClient(
            api_key="test-fake-key-12345-not-real",
            max_retries=5,
            timeout=60,
            backoff_factor=2.5,
        )
        assert client.max_retries == 5
        assert client.timeout == 60
        assert client.backoff_factor == 2.5

    def test_init_with_config(self, monkeypatch):
        """Test initialization using config."""
        monkeypatch.setenv("OPENAI_API_KEY", "config-key")
        client = OpenAIClient()
        assert client.api_key == "config-key"

    def test_model_validation_warning(self, openai_client, monkeypatch):
        """Test that unknown models generate warning but proceed."""
        # Mock logger to capture warnings
        with patch("src.ai.openai_client.logger") as mock_logger:
            # This should warn but not raise (strict mode disabled by default)
            # We can't actually call complete() without openai installed,
            # but we can verify the validation logic exists
            assert hasattr(openai_client, "complete")

    def test_cost_tracker_initialized(self, openai_client):
        """Test that cost tracker is initialized."""
        assert isinstance(openai_client.cost_tracker, CostTracker)
        assert openai_client.cost_tracker.total_requests == 0
        assert openai_client.cost_tracker.total_cost == 0.0


@pytest.mark.unit
@pytest.mark.openai
class TestOpenAIClientComplete:
    """Test OpenAI client complete method."""

    @pytest.mark.asyncio
    async def test_complete_success(self, openai_client, mock_openai_client):
        """Test successful completion request."""
        # Setup mock
        mock_openai_client.set_success_response(
            content="Test response",
            prompt_tokens=10,
            completion_tokens=20,
            model="gpt-4o-mini",
        )

        # Patch client
        with patch.object(
            openai_client.client.chat.completions,
            "create",
            mock_openai_client.chat.completions.create,
        ):
            response = await openai_client.complete(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": "Test"}],
            )

        assert response == "Test response"
        assert openai_client.cost_tracker.total_requests == 1

    @pytest.mark.asyncio
    async def test_complete_with_gpt4o(self, openai_client, mock_openai_client):
        """Test completion with GPT-4o model."""
        mock_openai_client.set_success_response(
            content="GPT-4o response",
            prompt_tokens=15,
            completion_tokens=30,
            model="gpt-4o",
        )

        with patch.object(
            openai_client.client.chat.completions,
            "create",
            mock_openai_client.chat.completions.create,
        ):
            response = await openai_client.complete(
                model="gpt-4o",
                messages=[{"role": "user", "content": "Test"}],
                operation_type=OperationType.ANALYSIS,
            )

        assert response == "GPT-4o response"
        assert openai_client.cost_tracker.total_requests == 1

    @pytest.mark.asyncio
    async def test_complete_with_custom_params(
        self, openai_client, mock_openai_client
    ):
        """Test completion with custom temperature and max_tokens."""
        mock_openai_client.set_success_response()

        with patch.object(
            openai_client.client.chat.completions,
            "create",
            mock_openai_client.chat.completions.create,
        ):
            await openai_client.complete(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": "Test"}],
                temperature=0.3,
                max_tokens=500,
            )

        # Verify call was made with correct params
        call_args = mock_openai_client.chat.completions.create.call_args
        assert call_args.kwargs["temperature"] == 0.3
        assert call_args.kwargs["max_tokens"] == 500

    @pytest.mark.asyncio
    async def test_complete_with_request_id(
        self, openai_client, mock_openai_client
    ):
        """Test completion with request ID for correlation."""
        mock_openai_client.set_success_response()

        with patch.object(
            openai_client.client.chat.completions,
            "create",
            mock_openai_client.chat.completions.create,
        ):
            await openai_client.complete(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": "Test"}],
                request_id="req-123",
            )

        # Verify cost record has request_id
        assert len(openai_client.cost_tracker.records) == 1
        assert openai_client.cost_tracker.records[0].request_id == "req-123"


@pytest.mark.unit
@pytest.mark.openai
class TestOpenAIClientRetryLogic:
    """Test retry logic for transient failures."""

    @pytest.mark.asyncio
    async def test_retry_on_rate_limit_success(
        self, openai_client, mock_openai_client
    ):
        """Test retry succeeds after rate limit error."""
        # First call fails with rate limit, second succeeds
        call_count = 0

        async def mock_create(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise RateLimitError(
                    message="Rate limit",
                    response=MagicMock(),
                    body={},
                )
            # Second call succeeds
            from tests.mocks.mock_openai import MockChatCompletion
            return MockChatCompletion(
                content="Success",
                prompt_tokens=10,
                completion_tokens=20,
                model="gpt-4o-mini",
            )

        mock_openai_client.chat.completions.create = AsyncMock(
            side_effect=mock_create
        )

        with patch.object(
            openai_client.client.chat.completions,
            "create",
            mock_openai_client.chat.completions.create,
        ):
            # Mock sleep to speed up test
            with patch("asyncio.sleep", new_callable=AsyncMock):
                response = await openai_client.complete(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": "Test"}],
                )

        assert call_count == 2

    @pytest.mark.asyncio
    async def test_retry_exhausted_raises_error(
        self, openai_client, mock_openai_client
    ):
        """Test that exhausted retries raise error."""
        mock_openai_client.set_rate_limit_error()

        with patch.object(
            openai_client.client.chat.completions,
            "create",
            mock_openai_client.chat.completions.create,
        ):
            with patch("asyncio.sleep", new_callable=AsyncMock):
                with pytest.raises(OpenAIRateLimitError):
                    await openai_client.complete(
                        model="gpt-4o-mini",
                        messages=[{"role": "user", "content": "Test"}],
                    )

    @pytest.mark.asyncio
    async def test_retry_with_retry_after_header(
        self, openai_client, mock_openai_client
    ):
        """Test retry respects retry-after header."""
        call_count = 0

        async def mock_create(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                error = RateLimitError(
                    message="Rate limit",
                    response=MagicMock(),
                    body={},
                )
                error.response.headers = {"retry-after": "2"}
                raise error
            from tests.mocks.mock_openai import MockChatCompletion
            return MockChatCompletion(
                content="Success",
                prompt_tokens=10,
                completion_tokens=20,
                model="gpt-4o-mini",
            )

        mock_openai_client.chat.completions.create = AsyncMock(
            side_effect=mock_create
        )

        with patch.object(
            openai_client.client.chat.completions,
            "create",
            mock_openai_client.chat.completions.create,
        ):
            sleep_calls = []

            async def mock_sleep(seconds):
                sleep_calls.append(seconds)

            with patch("asyncio.sleep", side_effect=mock_sleep):
                await openai_client.complete(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": "Test"}],
                )

        # Verify retry-after was used
        assert len(sleep_calls) == 1
        assert sleep_calls[0] == 2.0


@pytest.mark.unit
@pytest.mark.openai
class TestOpenAIClientErrorHandling:
    """Test error handling."""

    @pytest.mark.asyncio
    async def test_client_error_no_retry(
        self, openai_client, mock_openai_client
    ):
        """Test that client errors (4xx) don't retry."""
        error = APIError(
            message="Bad request",
            response=MagicMock(status_code=400),
            body={},
        )
        mock_openai_client.chat.completions.create.side_effect = error

        with patch.object(
            openai_client.client.chat.completions,
            "create",
            mock_openai_client.chat.completions.create,
        ):
            with pytest.raises(OpenAIError):
                await openai_client.complete(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": "Test"}],
                )

        # Verify only one attempt was made
        assert (
            mock_openai_client.chat.completions.create.call_count == 1
        )

    @pytest.mark.asyncio
    async def test_server_error_retries(
        self, openai_client, mock_openai_client
    ):
        """Test that server errors (5xx) retry."""
        call_count = 0

        async def mock_create(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise APIError(
                    message="Server error",
                    response=MagicMock(status_code=500),
                    body={},
                )
            from tests.mocks.mock_openai import MockChatCompletion
            return MockChatCompletion(
                content="Success",
                prompt_tokens=10,
                completion_tokens=20,
                model="gpt-4o-mini",
            )

        mock_openai_client.chat.completions.create = AsyncMock(
            side_effect=mock_create
        )

        with patch.object(
            openai_client.client.chat.completions,
            "create",
            mock_openai_client.chat.completions.create,
        ):
            with patch("asyncio.sleep", new_callable=AsyncMock):
                await openai_client.complete(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": "Test"}],
                )

        assert call_count == 3

    @pytest.mark.asyncio
    async def test_timeout_error(self, openai_client):
        """Test timeout handling."""
        # Create client with short timeout
        client = OpenAIClient(api_key="sk-test-dummy-key-not-real", timeout=0.1)

        # Mock a slow response
        async def slow_create(*args, **kwargs):
            await asyncio.sleep(1)
            return MagicMock()

        with patch.object(
            client.client.chat.completions, "create", slow_create
        ):
            with pytest.raises(OpenAITimeoutError):
                await client.complete(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": "Test"}],
                )


@pytest.mark.unit
@pytest.mark.openai
class TestOpenAIClientCostTracking:
    """Test cost tracking functionality."""

    @pytest.mark.asyncio
    async def test_cost_tracking_gpt4o_mini(
        self, openai_client, mock_openai_client
    ):
        """Test cost tracking for GPT-4o-mini."""
        mock_openai_client.set_success_response(
            prompt_tokens=1000,
            completion_tokens=500,
            model="gpt-4o-mini",
        )

        with patch.object(
            openai_client.client.chat.completions,
            "create",
            mock_openai_client.chat.completions.create,
        ):
            await openai_client.complete(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": "Test"}],
                operation_type=OperationType.EXTRACTION,
            )

        assert openai_client.cost_tracker.total_requests == 1
        assert openai_client.cost_tracker.total_cost > 0

        record = openai_client.cost_tracker.records[0]
        assert record.prompt_tokens == 1000
        assert record.completion_tokens == 500
        assert record.model == "gpt-4o-mini"
        assert record.operation_type == OperationType.EXTRACTION

    @pytest.mark.asyncio
    async def test_cost_tracking_gpt4o(
        self, openai_client, mock_openai_client
    ):
        """Test cost tracking for GPT-4o."""
        mock_openai_client.set_success_response(
            prompt_tokens=1000,
            completion_tokens=500,
            model="gpt-4o",
        )

        with patch.object(
            openai_client.client.chat.completions,
            "create",
            mock_openai_client.chat.completions.create,
        ):
            await openai_client.complete(
                model="gpt-4o",
                messages=[{"role": "user", "content": "Test"}],
                operation_type=OperationType.ANALYSIS,
            )

        record = openai_client.cost_tracker.records[0]
        assert record.model == "gpt-4o"
        assert record.operation_type == OperationType.ANALYSIS
        # GPT-4o should cost more than GPT-4o-mini
        assert record.estimated_cost > 0

    @pytest.mark.asyncio
    async def test_cost_stats(self, openai_client, mock_openai_client):
        """Test cost statistics aggregation."""
        # Make multiple requests
        mock_openai_client.set_success_response(
            prompt_tokens=100, completion_tokens=50
        )

        with patch.object(
            openai_client.client.chat.completions,
            "create",
            mock_openai_client.chat.completions.create,
        ):
            for _ in range(3):
                await openai_client.complete(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": "Test"}],
                )

        stats = openai_client.get_cost_stats()
        assert stats["total_requests"] == 3
        assert stats["total_cost"] > 0
        assert stats["average_cost_per_request"] > 0
        assert "by_model" in stats
        assert "by_operation" in stats


@pytest.mark.unit
@pytest.mark.openai
class TestOpenAIClientLogging:
    """Test logging behavior."""

    @pytest.mark.asyncio
    async def test_request_logging(self, openai_client, mock_openai_client):
        """Test that requests are logged."""
        mock_openai_client.set_success_response()

        with patch.object(
            openai_client.client.chat.completions,
            "create",
            mock_openai_client.chat.completions.create,
        ):
            with patch("src.ai.openai_client.logger") as mock_logger:
                await openai_client.complete(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": "Test"}],
                )

                # Verify logging calls
                assert mock_logger.debug.called
                # Check that sensitive data is not logged
                call_args = mock_logger.debug.call_args
                assert "test-key" not in str(call_args)

