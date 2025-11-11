"""OpenAI API client wrapper with retry logic and cost tracking.

This module provides a high-level interface for OpenAI API calls with:
- Automatic retry on transient failures
- Rate limit handling with exponential backoff
- Cost tracking per request
- Sanitized logging
- Support for GPT-4o and GPT-4o-mini models
"""

import asyncio
import time
from typing import Any, Dict, List, Optional

from openai import APIError, AsyncOpenAI, RateLimitError
from openai.types.chat import ChatCompletion

from src.ai.cost_tracker import CostTracker, OperationType
from src.utils.config import get_config
from src.utils.logger import get_logger

logger = get_logger("ai.openai_client")


class OpenAIError(Exception):
    """Base exception for OpenAI client errors."""

    pass


class OpenAIRateLimitError(OpenAIError):
    """Raised when rate limit is exceeded."""

    pass


class OpenAITimeoutError(OpenAIError):
    """Raised when request times out."""

    pass


class OpenAIClient:
    """OpenAI API client wrapper with retry logic and cost tracking.

    This client provides a unified interface for OpenAI API calls with
    automatic retry on transient failures, rate limit handling, and
    comprehensive cost tracking.

    Attributes:
        client: AsyncOpenAI client instance
        cost_tracker: CostTracker instance for tracking API usage
        max_retries: Maximum number of retry attempts
        timeout: Request timeout in seconds
        backoff_factor: Exponential backoff multiplier
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        max_retries: int = 3,
        timeout: int = 30,
        backoff_factor: float = 2.0,
    ):
        """Initialize OpenAI client wrapper.

        Args:
            api_key: OpenAI API key (defaults to config)
            max_retries: Maximum retry attempts for transient failures
            timeout: Request timeout in seconds
            backoff_factor: Exponential backoff multiplier
        """
        config = get_config()
        self.api_key = api_key or config.openai_api_key
        self.max_retries = max_retries
        self.timeout = timeout
        self.backoff_factor = backoff_factor

        # Initialize OpenAI client
        self.client = AsyncOpenAI(
            api_key=self.api_key,
            timeout=timeout,
            max_retries=0,  # We handle retries ourselves
        )

        # Initialize cost tracker
        self.cost_tracker = CostTracker()

    async def complete(
        self,
        model: str,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        operation_type: OperationType = OperationType.EXTRACTION,
        request_id: Optional[str] = None,
    ) -> str:
        """Send chat completion request with retry logic.

        Args:
            model: Model to use (gpt-4o-mini or gpt-4o)
            messages: List of message dicts with 'role' and 'content'
            temperature: Sampling temperature (0.0-2.0)
            max_tokens: Maximum tokens in response (None for no limit)
            operation_type: Type of operation for cost tracking
            request_id: Optional request ID for correlation

        Returns:
            Response content text

        Raises:
            OpenAIRateLimitError: If rate limit exceeded after retries
            OpenAITimeoutError: If request times out
            OpenAIError: For other API errors
        """
        # Validate model
        if model not in ["gpt-4o-mini", "gpt-4o"]:
            logger.warning(
                f"Unknown model {model}, proceeding anyway",
                extra={"model": model, "request_id": request_id},
            )

        # Log request (sanitized)
        logger.debug(
            f"OpenAI API request",
            extra={
                "model": model,
                "operation_type": operation_type.value,
                "message_count": len(messages),
                "temperature": temperature,
                "max_tokens": max_tokens,
                "request_id": request_id,
            },
        )

        # Prepare request parameters
        request_params: Dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
        }
        if max_tokens is not None:
            request_params["max_tokens"] = max_tokens

        # Execute with retry logic
        try:
            response = await self._execute_with_retry(
                request_params, operation_type, request_id
            )
        except RateLimitError as e:
            raise OpenAIRateLimitError(
                f"Rate limit exceeded: {e}"
            ) from e
        except asyncio.TimeoutError as e:
            raise OpenAITimeoutError(
                f"Request timed out after {self.timeout}s"
            ) from e
        except APIError as e:
            raise OpenAIError(f"OpenAI API error: {e}") from e

        # Extract content
        content = response.choices[0].message.content or ""
        if not content:
            logger.warning(
                "OpenAI API returned empty content",
                extra={
                    "model": model,
                    "operation_type": operation_type.value,
                    "request_id": request_id,
                },
            )

        # Log response (sanitized)
        logger.debug(
            f"OpenAI API response received",
            extra={
                "model": model,
                "operation_type": operation_type.value,
                "response_length": len(content),
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "request_id": request_id,
            },
        )

        return content

    async def _execute_with_retry(
        self,
        request_params: Dict[str, Any],
        operation_type: OperationType,
        request_id: Optional[str],
    ) -> ChatCompletion:
        """Execute API request with exponential backoff retry.

        Args:
            request_params: Parameters for chat.completions.create
            operation_type: Operation type for cost tracking
            request_id: Optional request ID

        Returns:
            ChatCompletion response

        Raises:
            RateLimitError: If rate limit exceeded after retries
            APIError: For other API errors
        """
        last_error = None

        for attempt in range(self.max_retries):
            try:
                # Execute request with timeout
                response = await asyncio.wait_for(
                    self.client.chat.completions.create(**request_params),
                    timeout=self.timeout,
                )

                # Track cost
                self.cost_tracker.log(
                    model=request_params["model"],
                    prompt_tokens=response.usage.prompt_tokens,
                    completion_tokens=response.usage.completion_tokens,
                    operation_type=operation_type,
                    request_id=request_id,
                )

                return response

            except RateLimitError as e:
                last_error = e
                if attempt < self.max_retries - 1:
                    # Calculate backoff time
                    retry_after = self._get_retry_after(e)
                    wait_time = retry_after or (
                        self.backoff_factor ** attempt
                    )

                    logger.warning(
                        f"Rate limit hit, retrying in {wait_time:.2f}s "
                        f"(attempt {attempt + 1}/{self.max_retries})",
                        extra={
                            "model": request_params["model"],
                            "attempt": attempt + 1,
                            "max_retries": self.max_retries,
                            "wait_time": wait_time,
                            "request_id": request_id,
                        },
                    )

                    await asyncio.sleep(wait_time)
                    continue
                else:
                    # Max retries reached
                    logger.error(
                        f"Rate limit exceeded after {self.max_retries} retries",
                        extra={
                            "model": request_params["model"],
                            "request_id": request_id,
                        },
                    )
                    raise

            except asyncio.TimeoutError:
                logger.error(
                    f"Request timed out (attempt {attempt + 1}/{self.max_retries})",
                    extra={
                        "model": request_params["model"],
                        "timeout": self.timeout,
                        "request_id": request_id,
                    },
                )
                raise

            except APIError as e:
                last_error = e
                # Don't retry on non-transient errors
                if e.status_code and e.status_code >= 400 and e.status_code < 500:
                    # Client errors (4xx) - don't retry
                    logger.error(
                        f"OpenAI API client error: {e}",
                        extra={
                            "model": request_params["model"],
                            "status_code": e.status_code,
                            "request_id": request_id,
                        },
                    )
                    raise

                # Server errors (5xx) - retry
                if attempt < self.max_retries - 1:
                    wait_time = self.backoff_factor ** attempt
                    logger.warning(
                        f"OpenAI API server error, retrying in {wait_time:.2f}s "
                        f"(attempt {attempt + 1}/{self.max_retries})",
                        extra={
                            "model": request_params["model"],
                            "error": str(e),
                            "status_code": e.status_code,
                            "request_id": request_id,
                        },
                    )
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    logger.error(
                        f"OpenAI API error after {self.max_retries} retries: {e}",
                        extra={
                            "model": request_params["model"],
                            "request_id": request_id,
                        },
                    )
                    raise

        # Should not reach here, but handle just in case
        if last_error:
            raise OpenAIError(
                f"Request failed after {self.max_retries} retries"
            ) from last_error

        raise OpenAIError("Request failed unexpectedly")

    def _get_retry_after(self, error: RateLimitError) -> Optional[float]:
        """Extract retry-after value from rate limit error.

        Args:
            error: RateLimitError instance

        Returns:
            Retry-after seconds, or None if not available
        """
        try:
            if hasattr(error, "response") and error.response:
                headers = error.response.headers
                if headers and "retry-after" in headers:
                    return float(headers["retry-after"])
        except (AttributeError, ValueError, TypeError):
            pass

        return None

    def get_cost_stats(self) -> Dict:
        """Get cost tracking statistics.

        Returns:
            Dictionary with cost statistics
        """
        return self.cost_tracker.get_stats()

