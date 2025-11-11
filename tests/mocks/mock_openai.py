"""Mock OpenAI API responses for testing.

This module provides mock responses that simulate OpenAI API behavior
for unit testing without making actual API calls.
"""

from typing import Any, Dict, Optional
from unittest.mock import AsyncMock, MagicMock

from openai import APIError, RateLimitError


class MockChatCompletion:
    """Mock OpenAI chat completion response."""

    def __init__(
        self,
        content: str = "Test response",
        prompt_tokens: int = 10,
        completion_tokens: int = 20,
        model: str = "gpt-4o-mini",
    ):
        """Initialize mock completion response.

        Args:
            content: Response content text
            prompt_tokens: Number of prompt tokens used
            completion_tokens: Number of completion tokens used
            model: Model name used
        """
        self.choices = [MagicMock()]
        self.choices[0].message = MagicMock()
        self.choices[0].message.content = content
        self.usage = MagicMock()
        self.usage.prompt_tokens = prompt_tokens
        self.usage.completion_tokens = completion_tokens
        self.model = model


class MockOpenAIClient:
    """Mock OpenAI client for testing."""

    def __init__(self):
        """Initialize mock client."""
        self.chat = MagicMock()
        self.chat.completions = MagicMock()
        self.chat.completions.create = AsyncMock()

    def set_success_response(
        self,
        content: str = "Test response",
        prompt_tokens: int = 10,
        completion_tokens: int = 20,
        model: str = "gpt-4o-mini",
    ):
        """Configure mock to return successful response.

        Args:
            content: Response content text
            prompt_tokens: Number of prompt tokens used
            completion_tokens: Number of completion tokens used
            model: Model name used
        """
        mock_response = MockChatCompletion(
            content=content,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            model=model,
        )
        self.chat.completions.create.return_value = mock_response

    def set_rate_limit_error(self, retry_after: Optional[int] = None):
        """Configure mock to raise rate limit error.

        Args:
            retry_after: Optional retry-after seconds
        """
        error = RateLimitError(
            message="Rate limit exceeded",
            response=MagicMock(),
            body={"error": {"message": "Rate limit exceeded"}},
        )
        if retry_after:
            error.response.headers = {"retry-after": str(retry_after)}
        self.chat.completions.create.side_effect = error

    def set_api_error(self, message: str = "API error"):
        """Configure mock to raise API error.

        Args:
            message: Error message
        """
        error = APIError(
            message=message,
            response=MagicMock(),
            body={"error": {"message": message}},
        )
        self.chat.completions.create.side_effect = error

    def set_timeout_error(self):
        """Configure mock to raise timeout error."""
        import asyncio

        async def timeout_func(*args, **kwargs):
            await asyncio.sleep(100)  # Simulate timeout

        self.chat.completions.create.side_effect = timeout_func

    def reset(self):
        """Reset mock to default state."""
        self.chat.completions.create.reset_mock()
        self.chat.completions.create.side_effect = None
        self.set_success_response()

