from datetime import datetime
from typing import Any, Dict, List, Optional

import diskcache
import httpx
from pydantic import BaseModel, Field, validator
from tenacity import retry, stop_after_attempt, wait_exponential

from fx_trader.config import settings
from fx_trader.utils.http_client import get_async_http_client, make_request_with_retry
from fx_trader.utils.logging import get_logger

logger = get_logger(__name__)

# Cache for News API responses
news_cache = diskcache.Cache(
    "cache/news_cache", size_limit=1024 * 1024 * 50)  # 50MB


class NewsArticleSentiment(BaseModel):
    ticker: str
    relevance_score: float
    sentiment_score: float = Field(alias="ticker_sentiment_score")
    sentiment_label: str = Field(alias="ticker_sentiment_label")


class NewsArticle(BaseModel):
    title: str
    url: str
    time_published: datetime
    authors: List[str]
    summary: str
    banner_image: Optional[str] = None
    source: str
    category_within_source: str
    source_domain: str
    # List of {"topic": "...", "relevance_score": "..."}
    topics: List[Dict[str, Any]]
    overall_sentiment_score: float
    overall_sentiment_label: str
    ticker_sentiment: List[NewsArticleSentiment]

    @validator("time_published", pre=True)
    def parse_time_published(cls, value: str) -> datetime:
        # AlphaVantage format: "20231026T023151"
        return datetime.strptime(value, "%Y%m%dT%H%M%S")


class AlphaVantageNewsResponse(BaseModel):
    items: str  # Seems to be a count as string
    sentiment_score_definition: str
    relevance_score_definition: str
    feed: List[NewsArticle]


class NewsClient:
    BASE_URL = "https://www.alphavantage.co"

    def __init__(self, api_key: Optional[str] = settings.ALPHAVANTAGE_API_KEY):
        if not api_key:
            logger.warning(
                "ALPHAVANTAGE_API_KEY not set. NewsClient will not be functional.")
        self.api_key = api_key

    @news_cache.memoize(expire=60 * 60 * 1)  # Cache for 1 hour
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def get_news_sentiment(
        self,
        # e.g., ["AAPL", "MSFT"] for stocks, or "FOREX:EURUSD"
        tickers: Optional[List[str]] = None,
        topics: Optional[List[str]] = None,  # e.g., ["technology", "earnings"]
        limit: int = 50,  # Max 1000, default 50
    ) -> Optional[AlphaVantageNewsResponse]:
        if not self.api_key:
            logger.error(
                "Cannot fetch news data: AlphaVantage API key not configured.")
            return None

        endpoint = "/query"
        params: Dict[str, Any] = {
            "function": "NEWS_SENTIMENT",
            "apikey": self.api_key,
            "limit": str(limit),
        }
        if tickers:
            params["tickers"] = ",".join(tickers)
        if topics:
            # e.g. "blockchain", "earnings", "ipo", "mergers_and_acquisitions", "financial_markets", "economy_fiscal", "economy_monetary", "economy_macro", "energy_transportation", "finance", "life_sciences", "manufacturing", "real_estate", "retail_wholesale", "technology"
            params["topics"] = ",".join(topics)

        async with await get_async_http_client(base_url=self.BASE_URL) as client:
            try:
                response = await make_request_with_retry(client, "GET", endpoint, params=params)
                data = response.json()
                if "Error Message" in data or "Information" in data:  # AlphaVantage error/limit messages
                    logger.error(f"AlphaVantage API error/info: {data}")
                    return None  # Or raise a custom error
                return AlphaVantageNewsResponse(**data)
            except httpx.HTTPStatusError as e:
                logger.error(f"AlphaVantage API error: {e.response.text}")
                raise
            except Exception as e:
                logger.error(
                    f"Unexpected error fetching AlphaVantage news: {e}")
                raise
        return None
