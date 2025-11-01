"""Utility functions for AlphaFlow."""

import logging
import time
from collections.abc import Callable
from typing import Any

import httpx

logger = logging.getLogger(__name__)


def http_request_with_backoff(
    request_func: Callable[[], httpx.Response],
    retries: int = 3,
    backoff: float = 60.0,
    backoff_multiplier: float = 1.0,
    error_message: str = "HTTP request failed",
) -> Any:
    """Execute HTTP request with exponential backoff for rate limit errors.

    Args:
        request_func: Function that makes the HTTP request and returns httpx.Response.
        retries: Number of retry attempts for 429 rate limit errors (default: 3).
        backoff: Initial backoff delay in seconds for rate limit errors (default: 60).
        backoff_multiplier: Multiplier for exponential backoff (default: 1.0 for constant backoff).
        error_message: Custom error message prefix for exceptions.

    Returns:
        Parsed JSON response from the successful request.

    Raises:
        ValueError: If rate limit is exceeded after all retries.
        httpx.HTTPError: For other HTTP errors (network issues, non-2xx status codes, etc.).

    Example:
        >>> def make_request():
        ...     return httpx.get("https://api.example.com/data", timeout=30.0)
        >>> data = http_request_with_backoff(make_request, retries=5, backoff=12.0)

    """
    for attempt in range(retries + 1):
        response = request_func()

        # Handle rate limiting with backoff
        if response.status_code == 429:
            if attempt < retries:
                delay = backoff * (backoff_multiplier**attempt)
                logger.warning(
                    f"Rate limit hit (429) on attempt {attempt + 1}/{retries + 1}. Retrying in {delay:.1f} seconds..."
                )
                time.sleep(delay)
                continue
            else:
                raise ValueError(
                    f"Rate limit exceeded after {retries + 1} attempts. Consider increasing backoff or retries."
                )

        # Raise for other HTTP errors
        response.raise_for_status()
        return response.json()
