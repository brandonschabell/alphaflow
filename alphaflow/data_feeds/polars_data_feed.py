"""Polars data feed implementation."""

import logging
from collections.abc import Generator
from datetime import datetime
from pathlib import Path

import polars as pl

from alphaflow import DataFeed
from alphaflow.events.market_data_event import MarketDataEvent

logger = logging.getLogger(__name__)


class PolarsDataFeed(DataFeed):
    """Data feed that loads market data from Polars dataframes."""

    def __init__(
        self,
        df_or_file_path: Path | str | pl.DataFrame | pl.LazyFrame,
        *,
        col_timestamp: str = "Date",
        col_symbol: str = "Symbol",
        col_open: str = "Open",
        col_high: str = "High",
        col_low: str = "Low",
        col_close: str = "Close",
        col_volume: str = "Volume",
    ) -> None:
        """Initialize the Polars data feed.

        Args:
            df_or_file_path: Polars dataframe or path to the Polars dataframe containing market data.
            col_timestamp: Name of the timestamp column.
            col_symbol: Name of the symbol column.
            col_open: Name of the open price column.
            col_high: Name of the high price column.
            col_low: Name of the low price column.
            col_close: Name of the close price column.
            col_volume: Name of the volume column.

        """
        self.df_or_file_path = df_or_file_path
        self._col_timestamp = col_timestamp
        self._col_symbol = col_symbol
        self._col_open = col_open
        self._col_high = col_high
        self._col_low = col_low
        self._col_close = col_close
        self._col_volume = col_volume

    def run(
        self,
        symbol: str,
        start_timestamp: datetime | None,
        end_timestamp: datetime | None,
    ) -> Generator[MarketDataEvent, None, None]:
        """Load and yield market data events from the Polars dataframe.

        Args:
            symbol: The ticker symbol to load data for.
            start_timestamp: Optional start time for filtering data.
            end_timestamp: Optional end time for filtering data.

        Yields:
            MarketDataEvent objects containing OHLCV data.

        Raises:
            ValueError: If required columns are missing from the Polars dataframe.

        """
        if isinstance(self.df_or_file_path, (str, Path)):
            df_path = Path(self.df_or_file_path) if isinstance(self.df_or_file_path, str) else self.df_or_file_path
            if df_path.suffix in {".parquet", ".parq"}:
                df = pl.read_parquet(df_path)
                df = df.with_columns(pl.col(self._col_timestamp).cast(pl.Datetime))
            elif df_path.suffix == ".csv":
                df = pl.read_csv(df_path, try_parse_dates=True)
            else:
                raise ValueError(f"Unsupported file format: {df_path.suffix}")
        elif isinstance(self.df_or_file_path, pl.LazyFrame):
            df = self.df_or_file_path.collect()
        else:
            df = self.df_or_file_path

        required_cols = {
            self._col_timestamp,
            self._col_close,
            self._col_high,
            self._col_low,
            self._col_open,
            self._col_volume,
        }

        missing_cols = required_cols.difference(df.columns)
        if missing_cols:
            raise ValueError(f"Missing columns: {missing_cols}")

        # Convert date column to datetime if needed (polars parses as date by default)
        if df[self._col_timestamp].dtype == pl.Date:
            df = df.with_columns(pl.col(self._col_timestamp).cast(pl.Datetime))

        # Filter by symbol using polars
        if self._col_symbol in df.columns:
            df = df.filter(pl.col(self._col_symbol) == symbol)

        # Filter by timestamp bounds using polars
        if start_timestamp:
            df = df.filter(pl.col(self._col_timestamp) >= start_timestamp)
        if end_timestamp:
            df = df.filter(pl.col(self._col_timestamp) <= end_timestamp)

        # Convert to dicts once after all filtering
        for row in df.sort(by=self._col_timestamp).iter_rows(named=True):
            event = MarketDataEvent(
                timestamp=row[self._col_timestamp],
                symbol=symbol,
                open=row[self._col_open],
                high=row[self._col_high],
                low=row[self._col_low],
                close=row[self._col_close],
                volume=row[self._col_volume],
            )
            yield event
