"""Financial Modeling Prep API data feed implementation."""

import logging
import os
from collections.abc import Generator
from datetime import datetime

import httpx

from alphaflow import DataFeed
from alphaflow.events.market_data_event import MarketDataEvent
from alphaflow.utils import http_request_with_backoff

logger = logging.getLogger(__name__)


class FMPDataFeed(DataFeed):
    """Data feed that loads market data from Financial Modeling Prep API."""

    def __init__(
        self,
        use_cache: bool = False,
        api_key: str | None = None,
        rate_limit_retries: int = 3,
        rate_limit_backoff: float = 60.0,
        rate_limit_backoff_multiplier: float = 1.0,
    ) -> None:
        """Initialize the FMP data feed.

        Args:
            use_cache: Whether to cache API responses (not yet implemented).
            api_key: FMP API key. Falls back to FMP_API_KEY env var.
            rate_limit_retries: Number of retry attempts for 429 rate limit errors (default: 3).
            rate_limit_backoff: Initial backoff delay in seconds for rate limit errors (default: 60).
            rate_limit_backoff_multiplier: Multiplier for exponential backoff (default: 1.0).

        """
        self._use_cache = use_cache
        self.__api_key = api_key or os.getenv("FMP_API_KEY")
        self.rate_limit_retries = rate_limit_retries
        self.rate_limit_backoff = rate_limit_backoff
        self.rate_limit_backoff_multiplier = rate_limit_backoff_multiplier

    def run(
        self,
        symbol: str,
        start_timestamp: datetime | None,
        end_timestamp: datetime | None,
    ) -> Generator[MarketDataEvent, None, None]:
        """Load and yield market data events from FMP API.

        Args:
            symbol: The ticker symbol to load data for.
            start_timestamp: Optional start time for filtering data.
            end_timestamp: Optional end time for filtering data.

        Yields:
            MarketDataEvent objects containing OHLCV data.

        """
        if self._use_cache:
            raise NotImplementedError("Cache not implemented yet")
        else:
            url = f"https://financialmodelingprep.com/stable/historical-price-eod/dividend-adjusted?symbol={symbol}&apikey={self.__api_key}"
            if start_timestamp:
                url += f"&from={start_timestamp.date()}"
            if end_timestamp:
                url += f"&to={end_timestamp.date()}"
            logger.debug(f"Fetching data for symbol '{symbol}' from FMP stable historical-price-eod endpoint")
            data = http_request_with_backoff(
                request_func=lambda: httpx.get(url, timeout=httpx.Timeout(30.0)),
                retries=self.rate_limit_retries,
                backoff=self.rate_limit_backoff,
                backoff_multiplier=self.rate_limit_backoff_multiplier,
                error_message="Failed to fetch data from FMP",
            )

            # Sort data by date to ensure chronological order (oldest first)
            sorted_data = sorted(data, key=lambda x: x["date"])

            for row in sorted_data:
                event = MarketDataEvent(
                    timestamp=datetime.strptime(row["date"], "%Y-%m-%d"),
                    symbol=symbol,
                    open=row["adjOpen"],
                    high=row["adjHigh"],
                    low=row["adjLow"],
                    close=row["adjClose"],
                    volume=row["volume"],
                )
                yield event
