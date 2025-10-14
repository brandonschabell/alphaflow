"""Financial Modeling Prep API data feed implementation."""

import logging
import os
from collections.abc import Generator
from datetime import datetime

import httpx

from alphaflow import DataFeed
from alphaflow.events.market_data_event import MarketDataEvent

logger = logging.getLogger(__name__)


class FMPDataFeed(DataFeed):
    """Data feed that loads market data from Financial Modeling Prep API."""

    def __init__(
        self,
        use_cache: bool = False,
        api_key: str | None = None,
    ) -> None:
        """Initialize the FMP data feed.

        Args:
            use_cache: Whether to cache API responses (not yet implemented).
            api_key: FMP API key. Falls back to FMP_API_KEY env var.

        """
        self._use_cache = use_cache
        self.__api_key = api_key or os.getenv("FMP_API_KEY")

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
            url = f"https://financialmodelingprep.com/api/v3/historical-price-full/{symbol}?apikey={self.__api_key}"
            if start_timestamp:
                url += f"&from={start_timestamp.date()}"
            if end_timestamp:
                url += f"&to={end_timestamp.date()}"
            logger.debug(f"Fetching data for symbol '{symbol}' from FMP historical-price-full endpoint")
            try:
                response = httpx.get(url, timeout=httpx.Timeout(30.0))
                response.raise_for_status()
                data = response.json()
            except httpx.HTTPError as e:
                logger.error(f"HTTP error while fetching data from FMP: {e}")
                raise ValueError(f"Failed to fetch data from FMP: {e}") from e
            for row in data["historical"]:
                event = MarketDataEvent(
                    timestamp=datetime.strptime(row["date"], "%Y-%m-%d"),
                    symbol=symbol,
                    open=row["open"],
                    high=row["high"],
                    low=row["low"],
                    close=row["adjClose"],
                    volume=row["volume"],
                )
                yield event
