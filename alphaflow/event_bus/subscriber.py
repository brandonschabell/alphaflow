"""Subscriber protocol for event bus subscribers."""

from typing import Protocol

from alphaflow.events.event import Event


class Subscriber(Protocol):
    """Defines the interface for event subscribers."""

    def read_event(self, event: Event) -> None:
        """Read and process the event."""
        ...
