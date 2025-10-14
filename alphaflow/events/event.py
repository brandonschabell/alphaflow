"""Base event class for the event-driven architecture."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class Event:
    """Base class for events.

    All events must have a timestamp and are ordered chronologically.
    """

    #: The timestamp of the event.
    timestamp: datetime

    def __lt__(self, other: Event) -> bool:
        """Compare events by timestamp for sorting.

        Args:
            other: Another Event to compare against.

        Returns:
            True if this event's timestamp is less than the other's.

        """
        return self.timestamp < other.timestamp

    def __gt__(self, other: Event) -> bool:
        """Compare events by timestamp for sorting.

        Args:
            other: Another Event to compare against.

        Returns:
            True if this event's timestamp is greater than the other's.

        """
        return self.timestamp > other.timestamp

    def __le__(self, other: Event) -> bool:
        """Compare events by timestamp for sorting.

        Args:
            other: Another Event to compare against.

        Returns:
            True if this event's timestamp is less than or equal to the other's.

        """
        return self.timestamp <= other.timestamp

    def __ge__(self, other: Event) -> bool:
        """Compare events by timestamp for sorting.

        Args:
            other: Another Event to compare against.

        Returns:
            True if this event's timestamp is greater than or equal to the other's.

        """
        return self.timestamp >= other.timestamp

    def __eq__(self, other: object) -> bool:
        """Compare events for equality.

        Args:
            other: Another object to compare against.

        Returns:
            True if the events are equal (all fields match).

        """
        if not isinstance(other, Event):
            return NotImplemented
        # Use dataclass default equality (compares all fields)
        return self.__dict__ == other.__dict__
