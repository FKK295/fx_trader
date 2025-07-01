from typing import Any, Dict, Optional

import httpx
from tenacity import (
    AsyncRetrying,
    RetryError,
    stop_after_attempt,
    wait_exponential,
)

from utils.logging import get_logger

logger = get_logger(__name__)


async def get_async_http_client(
    base_url: Optional[str] = None,
    headers: Optional[Dict[str, str]] = None,
    timeout: float = 30.0,
) -> httpx.AsyncClient:
    """
    Creates and returns an asynchronous HTTPX client with default configurations.
    """
    return httpx.AsyncClient(base_url=base_url or "", headers=headers or {}, timeout=timeout)


async def make_request_with_retry(
    client: httpx.AsyncClient,
    method: str,
    url: str,
    max_attempts: int = 3,
    **kwargs: Any,
) -> httpx.Response:
    """
    Makes an HTTP request with retries using tenacity.
    """
    async for attempt in AsyncRetrying(
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
    ):
        with attempt:
            logger.debug(
                f"Attempt {attempt.retry_state.attempt_number}: {method.upper()} {client.base_url}{url}")
            response = await client.request(method, url, **kwargs)
            response.raise_for_status()  # Raise HTTPStatusError for 4xx/5xx responses
            return response
    # Should not be reached if reraise=True
    raise RetryError("Failed to make request after multiple retries")
