import asyncio
import logging
import random
from typing import Callable, TypeVar, Any

logger = logging.getLogger("car-deals-hunter")

T = TypeVar("T")


class APIError(Exception):
    """Base exception for API-related errors."""

    pass


class MCPServerError(APIError):
    """Raised when MCP server is unreachable or fails."""

    pass


class LLMAPIError(APIError):
    """Raised when LLM API call fails."""

    pass


class TimeoutError(APIError):
    """Raised when an API call times out."""

    pass


class RetryableError(APIError):
    """Raised when an error might succeed if retried."""

    pass


async def retry_with_exponential_backoff(
    func: Callable[..., Any],
    max_retries: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 30.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
    *args,
    **kwargs,
) -> Any:
    """
    Retry an async function with exponential backoff.

    Args:
        func: Async function to retry
        max_retries: Maximum number of retries
        initial_delay: Initial delay in seconds
        max_delay: Maximum delay in seconds
        exponential_base: Base for exponential backoff
        jitter: Add random jitter to delay
        *args: Positional arguments for func
        **kwargs: Keyword arguments for func

    Returns:
        Result of func call

    Raises:
        APIError: If all retries fail
    """
    last_exception = None
    delay = initial_delay

    for attempt in range(max_retries + 1):
        try:
            return await func(*args, **kwargs)
        except asyncio.TimeoutError as e:
            last_exception = TimeoutError(f"API call timed out: {str(e)}")
            logger.warning(
                f"Timeout on attempt {attempt + 1}/{max_retries + 1}: {str(e)}"
            )
        except Exception as e:
            # Check if error is retryable
            if _is_retryable_error(e):
                last_exception = RetryableError(
                    f"Retryable error occurred: {type(e).__name__}: {str(e)}"
                )
                logger.warning(
                    f"Retryable error on attempt {attempt + 1}/{max_retries + 1}: {str(e)}"
                )
            else:
                logger.error(f"Non-retryable error: {type(e).__name__}: {str(e)}")
                raise APIError(f"API call failed: {type(e).__name__}: {str(e)}") from e

        # Don't retry if we've exhausted attempts
        if attempt >= max_retries:
            break

        # Calculate delay with optional jitter
        actual_delay = min(delay, max_delay)
        if jitter:
            actual_delay += random.uniform(0, actual_delay * 0.1)

        logger.info(
            f"Retrying after {actual_delay:.2f}s (attempt {attempt + 1}/{max_retries})"
        )
        await asyncio.sleep(actual_delay)
        delay *= exponential_base

    raise last_exception or APIError("All retries exhausted")


def _is_retryable_error(error: Exception) -> bool:
    """Determine if an error is retryable."""
    retryable_types = (
        TimeoutError,
        asyncio.TimeoutError,
        ConnectionError,
        BrokenPipeError,
    )

    if isinstance(error, retryable_types):
        return True

    # Check for common HTTP error codes that warrant retries
    error_str = str(error).lower()
    retryable_patterns = [
        "502",  # Bad Gateway
        "503",  # Service Unavailable
        "504",  # Gateway Timeout
        "connection refused",
        "connection reset",
        "broken pipe",
        "timeout",
    ]

    return any(pattern in error_str for pattern in retryable_patterns)
