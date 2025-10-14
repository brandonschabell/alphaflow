"""Alpha Vantage API data feed implementation."""

import logging
import os
from collections.abc import Generator
from datetime import datetime

import httpx

from alphaflow import DataFeed
from alphaflow.events.market_data_event import MarketDataEvent

logger = logging.getLogger(__name__)


class AlphaVantageFeed(DataFeed):
    """Data feed that loads market data from Alpha Vantage API."""

    def __init__(
        self,
        use_cache: bool = False,
        api_key: str | None = None,
    ) -> None:
        """Initialize the Alpha Vantage data feed.

        Args:
            use_cache: Whether to cache API responses (not yet implemented).
            api_key: Alpha Vantage API key. Falls back to ALPHA_VANTAGE_API_KEY env var.

        """
        self._use_cache = use_cache
        self.__api_key = api_key or os.getenv("ALPHA_VANTAGE_API_KEY")

    def run(
        self,
        symbol: str,
        start_timestamp: datetime | None,
        end_timestamp: datetime | None,
    ) -> Generator[MarketDataEvent, None, None]:
        """Load and yield market data events from Alpha Vantage API.

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
            url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY_ADJUSTED&symbol={symbol}&apikey={self.__api_key}&outputsize=full"
            logger.debug(f"Fetching data from {url}")
            response = httpx.get(url)
            if response.status_code != 200:
                raise ValueError(f"Failed to fetch data: {response.text}")
            data = response.json()
            for date, datum in data["Time Series (Daily)"].items():
                event = MarketDataEvent(
                    timestamp=datetime.strptime(date, "%Y-%m-%d"),
                    symbol=symbol,
                    open=float(datum["1. open"]),
                    high=float(datum["2. high"]),
                    low=float(datum["3. low"]),
                    close=float(datum["5. adjusted close"]),
                    volume=float(datum["6. volume"]),
                )
                if start_timestamp is not None and event.timestamp < start_timestamp:
                    continue
                if end_timestamp is not None and event.timestamp > end_timestamp:
                    continue
                yield event
