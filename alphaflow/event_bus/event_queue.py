"""Priority queue for event-driven backtesting."""

import heapq
from datetime import datetime

from alphaflow.events.event import Event


class EventQueue:
    """Priority queue that orders events by timestamp and priority.

    Events are ordered first by timestamp (earliest first), then by priority
    (lower number = higher priority). This ensures that events at the same
    timestamp are processed in the correct order:
    1. MarketDataEvent (priority 0) - market data arrives first
    2. OrderEvent (priority 1) - strategies generate orders
    3. FillEvent (priority 2) - broker executes orders
    4. Other events (priority 3+)
    """

    def __init__(self) -> None:
        """Initialize an empty event queue."""
        self._queue: list[tuple[datetime, int, int, Event]] = []
        self._counter = 0  # Used to break ties for events with same timestamp and priority

    def push(self, event: Event, priority: int = 3) -> None:
        """Add an event to the queue.

        Args:
            event: The event to add to the queue.
            priority: Priority level (0 = highest). Default is 3.
                     0: MarketDataEvent
                     1: OrderEvent
                     2: FillEvent
                     3+: Other events

        """
        # Use counter to maintain FIFO order for events with same timestamp and priority
        heapq.heappush(self._queue, (event.timestamp, priority, self._counter, event))
        self._counter += 1

    def pop(self) -> Event:
        """Remove and return the next event from the queue.

        Returns:
            The next event in chronological order.

        Raises:
            IndexError: If the queue is empty.

        """
        _, _, _, event = heapq.heappop(self._queue)
        return event

    def is_empty(self) -> bool:
        """Check if the queue is empty.

        Returns:
            True if the queue has no events, False otherwise.

        """
        return len(self._queue) == 0

    def peek(self) -> Event | None:
        """View the next event without removing it.

        Returns:
            The next event, or None if the queue is empty.

        """
        if self.is_empty():
            return None
        return self._queue[0][3]

    def size(self) -> int:
        """Get the number of events in the queue.

        Returns:
            The number of events currently in the queue.

        """
        return len(self._queue)

    def clear(self) -> None:
        """Remove all events from the queue."""
        self._queue.clear()
        self._counter = 0
