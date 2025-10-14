"""Market data event representing a price bar."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from alphaflow.events.event import Event


@dataclass(frozen=True)
class MarketDataEvent(Event):
    """Represents a market data event."""

    #: The timestamp of the event.
    timestamp: datetime

    #: The symbol of the market data.
    symbol: str

    #: The open price of the bar.
    open: float

    #: The high price of the bar.
    high: float

    #: The low price of the bar.
    low: float

    #: The close price of the bar.
    close: float

    #: The volume of the bar.
    volume: float

    def __gt__(self, other: MarketDataEvent) -> bool:
        """Compare events by timestamp for sorting.

        Args:
            other: Another MarketDataEvent to compare against.

        Returns:
            True if this event's timestamp is greater than the other's.

        """
        return self.timestamp > other.timestamp
