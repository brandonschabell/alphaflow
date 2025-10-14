"""Event bus for publish-subscribe messaging between components."""

import logging
from collections import defaultdict

from alphaflow.enums import Topic
from alphaflow.event_bus.event_queue import EventQueue
from alphaflow.event_bus.subscriber import Subscriber
from alphaflow.events.event import Event
from alphaflow.events.fill_event import FillEvent
from alphaflow.events.market_data_event import MarketDataEvent
from alphaflow.events.order_event import OrderEvent

logger = logging.getLogger(__name__)


class EventBus:
    """Manages event subscriptions and publish events to subscribers.

    Supports both immediate publishing (for live trading) and queued publishing
    (for backtests requiring proper chronological event ordering).
    """

    def __init__(self) -> None:
        """Initialize the event bus."""
        self.subscribers: dict[Topic, list[Subscriber]] = defaultdict(list)  # topic -> list of subscribers
        self.event_queue = EventQueue()
        self._use_queue = False  # When True, events are queued instead of immediately published

    def subscribe(self, topic: Topic, subscriber: Subscriber) -> None:
        """Subscribe a subscriber to a topic.

        Args:
            topic: The topic to subscribe to.
            subscriber: The subscriber to subscribe.

        """
        self.subscribers[topic].append(subscriber)

    def unsubscribe(self, topic: Topic, subscriber: Subscriber) -> None:
        """Unsubscribe a subscriber from a topic.

        Args:
            topic: The topic to unsubscribe from.
            subscriber: The subscriber to unsubscribe.

        """
        self.subscribers[topic].remove(subscriber)

    def enable_queue_mode(self) -> None:
        """Enable queue mode where events are queued instead of immediately published."""
        self._use_queue = True

    def disable_queue_mode(self) -> None:
        """Disable queue mode, events are immediately published."""
        self._use_queue = False

    def publish(self, topic: Topic, event: Event) -> None:
        """Publish an event to all subscribers of a topic.

        If queue mode is enabled, the event is added to the queue for later processing.
        Otherwise, it's immediately delivered to all subscribers.

        Args:
            topic: The topic to publish to.
            event: The event to publish.

        """
        if self._use_queue:
            # Determine priority based on event type
            if isinstance(event, MarketDataEvent):
                priority = 0  # Market data arrives first
            elif isinstance(event, OrderEvent):
                priority = 1  # Orders generated from market data
            elif isinstance(event, FillEvent):
                priority = 2  # Fills result from orders
            else:
                priority = 3  # Other events

            self.event_queue.push(topic, event, priority)
            logger.debug("Queued event %s on topic %s with priority %d", event, topic, priority)
        else:
            # Immediate publishing for live trading
            self._deliver_event(topic, event)

    def _deliver_event(self, topic: Topic, event: Event) -> None:
        """Deliver an event to all subscribers of a topic.

        Args:
            topic: The topic to deliver to.
            event: The event to deliver.

        """
        for subscriber in self.subscribers[topic]:
            logger.debug("Publishing event %s to subscriber %s", event, subscriber)
            subscriber.read_event(event)

    def process_queue(self) -> None:
        """Process all events in the queue in chronological order.

        Events are processed one at a time, with each event being delivered
        to all subscribers of its associated topic before the next event is
        processed. This ensures proper ordering even when events generate
        other events.
        """
        while not self.event_queue.is_empty():
            topic, event = self.event_queue.pop()
            self._deliver_event(topic, event)
