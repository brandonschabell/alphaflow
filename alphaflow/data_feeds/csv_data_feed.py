from collections.abc import Generator
from datetime import datetime
import logging
from pathlib import Path

import pandas as pd

from alphaflow import DataFeed
from alphaflow.events.market_data_event import BarTimeWindow, MarketDataEvent

logger = logging.getLogger(__name__)


class CSVDataFeed(DataFeed):
    def __init__(
        self,
        file_path: Path,
        *,
        col_timestamp: str = "Date",
        col_symbol: str = "Symbol",
        col_open: str = "Open",
        col_high: str = "High",
        col_low: str = "Low",
        col_close: str = "Close",
        col_volume: str = "Volume",
        symbol_override: str | None = None,
    ) -> None:
        self.file_path = file_path
        self._col_timestamp = col_timestamp
        self._col_symbol = col_symbol
        self._col_open = col_open
        self._col_high = col_high
        self._col_low = col_low
        self._col_close = col_close
        self._col_volume = col_volume
        self._symbol_override = symbol_override

    def run(
        self, start_timestamp: datetime | None, end_timestamp: datetime | None
    ) -> Generator[MarketDataEvent, None, None]:
        logger.debug("Opening CSV file...")
        df = pd.read_csv(self.file_path, parse_dates=[self._col_timestamp])

        required_cols = {
            self._col_timestamp,
            self._col_close,
            self._col_high,
            self._col_low,
            self._col_open,
            self._col_volume,
        }
        if not self._symbol_override:
            required_cols.add(self._col_symbol)

        missing_cols = required_cols.difference(df.columns)
        if missing_cols:
            raise ValueError(f"Missing columns: {missing_cols}")

        for _, row in df.iterrows():
            if start_timestamp and row[self._col_timestamp] < start_timestamp:
                continue
            if end_timestamp and row[self._col_timestamp] > end_timestamp:
                continue

            event = MarketDataEvent(
                timestamp=row[
                    self._col_timestamp
                ],  # TODO: Timestamp should be AFTER the bar time window
                symbol=self._symbol_override or row[self._col_symbol],
                bar_time_window=BarTimeWindow(
                    start_timestamp=row[self._col_timestamp],
                    end_timestamp=row[
                        self._col_timestamp
                    ],  # TODO: End timestamp should be AFTER the start timestamp
                ),
                open=row[self._col_open],
                high=row[self._col_high],
                low=row[self._col_low],
                close=row[self._col_close],
                volume=row[self._col_volume],
            )
            yield event
