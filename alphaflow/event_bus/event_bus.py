from collections import defaultdict

from alphaflow.constants import Topic
from alphaflow.event_bus.subscriber import Subscriber
from alphaflow.events.event import Event


class EventBus:
    """Manages event subscriptions and publish events to subscribers."""

    def __init__(self) -> None:
        """Initializes the event bus."""
        self.subscribers: dict[Topic, list[Subscriber]] = defaultdict(
            list
        )  # topic -> list of subscribers

    def subscribe(self, topic: Topic, subscriber: Subscriber) -> None:
        """Subscribes a subscriber to a topic.

        Args:
            topic: The topic to subscribe to.
            subscriber: The subscriber to subscribe.
        """
        self.subscribers[topic].append(subscriber)

    def unsubscribe(self, topic: Topic, subscriber: Subscriber) -> None:
        """Unsubscribes a subscriber from a topic.

        Args:
            topic: The topic to unsubscribe from.
            subscriber: The subscriber to unsubscribe.
        """
        self.subscribers[topic].remove(subscriber)

    def publish(self, topic: Topic, event: Event) -> None:
        """Publishes an event to all subscribers of a topic.

        Args:
            topic: The topic to publish to.
            event: The event to publish.
        """
        for subscriber in self.subscribers[topic]:
            subscriber.read_event(event)
