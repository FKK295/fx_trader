from datetime import date, datetime
from typing import Any, Dict, List, Optional

import diskcache
import httpx
import pandas as pd
from pydantic import BaseModel, Field, validator
from tenacity import retry, stop_after_attempt, wait_exponential

from config import settings
from utils.http_client import get_async_http_client, make_request_with_retry
from utils.logging import get_logger

logger = get_logger(__name__)

# Cache for FRED API responses
fred_cache = diskcache.Cache(
    "cache/fred_cache", size_limit=1024 * 1024 * 100)  # 100MB


class FredObservation(BaseModel):
    realtime_start: date
    realtime_end: date
    date: date
    value: float

    @validator("value", pre=True)
    def parse_value(cls, v: Any) -> float:
        if isinstance(v, str) and v == ".":  # FRED uses "." for missing values
            return float("nan")
        return float(v)


class FredSeriesObservations(BaseModel):
    realtime_start: date
    realtime_end: date
    observation_start: date
    observation_end: date
    units: str
    output_type: int
    file_type: str
    order_by: str
    sort_order: str
    count: int
    offset: int
    limit: int
    observations: List[FredObservation]


class FredClient:
    BASE_URL = "https://api.stlouisfed.org/fred"

    def __init__(self, api_key: Optional[str] = settings.FRED_API_KEY):
        if not api_key:
            logger.warning(
                "FRED_API_KEY not set. FREDClient will not be functional.")
            # raise ValueError("FRED_API_KEY is required for FredClient")
        self.api_key = api_key

    @fred_cache.memoize(expire=60 * 60 * 24)  # Cache for 24 hours
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def get_series_observations(
        self,
        series_id: str,
        observation_start: Optional[date] = None,
        observation_end: Optional[date] = None,
    ) -> Optional[FredSeriesObservations]:
        if not self.api_key:
            logger.error("Cannot fetch FRED data: API key not configured.")
            return None

        endpoint = "/series/observations"
        params: Dict[str, Any] = {
            "series_id": series_id,
            "api_key": self.api_key,
            "file_type": "json",
        }
        if observation_start:
            params["observation_start"] = observation_start.strftime(
                "%Y-%m-%d")
        if observation_end:
            params["observation_end"] = observation_end.strftime("%Y-%m-%d")

        async with await get_async_http_client(base_url=self.BASE_URL) as client:
            try:
                response = await make_request_with_retry(client, "GET", endpoint, params=params)
                data = response.json()
                return FredSeriesObservations(**data)
            except httpx.HTTPStatusError as e:
                logger.error(
                    f"FRED API error for series {series_id}: {e.response.text}")
                raise
            except Exception as e:
                logger.error(
                    f"Unexpected error fetching FRED series {series_id}: {e}")
                raise
        return None
