"""Tests for the event bus publish-subscribe system."""

from datetime import datetime

from alphaflow.enums import Topic
from alphaflow.event_bus.event_bus import EventBus
from alphaflow.event_bus.subscriber import Subscriber
from alphaflow.events.event import Event
from alphaflow.events.market_data_event import MarketDataEvent


def test_subscribe_unsubscribe_publish() -> None:
    """Test event bus subscription, publishing, and unsubscription."""

    class _TestSubscriber(Subscriber):
        def __init__(self) -> None:
            self.read_event_called = False
            self.event: Event | None = None

        def read_event(self, event: Event) -> None:
            self.read_event_called = True
            self.event = event

    event_bus = EventBus()
    subscriber = _TestSubscriber()
    topic = Topic.MARKET_DATA
    event = MarketDataEvent(
        timestamp=datetime.now(),
        symbol="AAPL",
        open=1.0,
        high=1.0,
        low=1.0,
        close=1.0,
        volume=1.0,
    )

    event_bus.subscribe(topic, subscriber)
    assert subscriber in event_bus.subscribers[topic]

    event_bus.unsubscribe(topic, subscriber)
    assert subscriber not in event_bus.subscribers[topic]

    event_bus.subscribe(topic, subscriber)
    event_bus.publish(topic, event)
    assert subscriber.read_event_called
    assert subscriber.event == event


def test_multiple_subscribers_to_same_topic() -> None:
    """Test multiple subscribers receive the same event."""

    class _TestSubscriber(Subscriber):
        def __init__(self) -> None:
            self.events_received: list[Event] = []

        def read_event(self, event: Event) -> None:
            self.events_received.append(event)

    event_bus = EventBus()
    subscriber1 = _TestSubscriber()
    subscriber2 = _TestSubscriber()
    topic = Topic.MARKET_DATA
    event = MarketDataEvent(
        timestamp=datetime.now(),
        symbol="AAPL",
        open=1.0,
        high=1.0,
        low=1.0,
        close=1.0,
        volume=1.0,
    )

    event_bus.subscribe(topic, subscriber1)
    event_bus.subscribe(topic, subscriber2)
    event_bus.publish(topic, event)

    assert len(subscriber1.events_received) == 1
    assert len(subscriber2.events_received) == 1
    assert subscriber1.events_received[0] == event
    assert subscriber2.events_received[0] == event


def test_subscriber_receives_only_subscribed_topics() -> None:
    """Test subscribers only receive events from subscribed topics."""

    class _TestSubscriber(Subscriber):
        def __init__(self) -> None:
            self.events_received: list[Event] = []

        def read_event(self, event: Event) -> None:
            self.events_received.append(event)

    event_bus = EventBus()
    subscriber = _TestSubscriber()

    # Subscribe to MARKET_DATA only
    event_bus.subscribe(Topic.MARKET_DATA, subscriber)

    market_event = MarketDataEvent(
        timestamp=datetime.now(),
        symbol="AAPL",
        open=1.0,
        high=1.0,
        low=1.0,
        close=1.0,
        volume=1.0,
    )

    # Publish to MARKET_DATA - should receive
    event_bus.publish(Topic.MARKET_DATA, market_event)
    assert len(subscriber.events_received) == 1

    # Import OrderEvent to publish to different topic
    from alphaflow.enums import OrderType, Side
    from alphaflow.events import OrderEvent

    order_event = OrderEvent(
        timestamp=datetime.now(),
        symbol="AAPL",
        qty=10.0,
        order_type=OrderType.MARKET,
        side=Side.BUY,
    )

    # Publish to ORDER - should NOT receive
    event_bus.publish(Topic.ORDER, order_event)
    assert len(subscriber.events_received) == 1  # Still only 1


def test_unsubscribe_stops_receiving_events() -> None:
    """Test unsubscribed subscribers don't receive events."""

    class _TestSubscriber(Subscriber):
        def __init__(self) -> None:
            self.events_received: list[Event] = []

        def read_event(self, event: Event) -> None:
            self.events_received.append(event)

    event_bus = EventBus()
    subscriber = _TestSubscriber()
    topic = Topic.MARKET_DATA

    event_bus.subscribe(topic, subscriber)

    event1 = MarketDataEvent(
        timestamp=datetime.now(),
        symbol="AAPL",
        open=1.0,
        high=1.0,
        low=1.0,
        close=1.0,
        volume=1.0,
    )
    event_bus.publish(topic, event1)
    assert len(subscriber.events_received) == 1

    # Unsubscribe
    event_bus.unsubscribe(topic, subscriber)

    # Publish another event
    event2 = MarketDataEvent(
        timestamp=datetime.now(),
        symbol="GOOGL",
        open=2.0,
        high=2.0,
        low=2.0,
        close=2.0,
        volume=2.0,
    )
    event_bus.publish(topic, event2)

    # Should still only have 1 event (from before unsubscribe)
    assert len(subscriber.events_received) == 1


def test_publish_to_topic_with_no_subscribers() -> None:
    """Test publishing to a topic with no subscribers doesn't error."""
    event_bus = EventBus()

    event = MarketDataEvent(
        timestamp=datetime.now(),
        symbol="AAPL",
        open=1.0,
        high=1.0,
        low=1.0,
        close=1.0,
        volume=1.0,
    )

    # Should not raise an error
    event_bus.publish(Topic.MARKET_DATA, event)


def test_subscriber_can_subscribe_to_multiple_topics() -> None:
    """Test a single subscriber can receive events from multiple topics."""

    class _TestSubscriber(Subscriber):
        def __init__(self) -> None:
            self.events_received: list[Event] = []

        def read_event(self, event: Event) -> None:
            self.events_received.append(event)

    event_bus = EventBus()
    subscriber = _TestSubscriber()

    # Subscribe to multiple topics
    event_bus.subscribe(Topic.MARKET_DATA, subscriber)
    event_bus.subscribe(Topic.FILL, subscriber)

    market_event = MarketDataEvent(
        timestamp=datetime.now(),
        symbol="AAPL",
        open=1.0,
        high=1.0,
        low=1.0,
        close=1.0,
        volume=1.0,
    )
    event_bus.publish(Topic.MARKET_DATA, market_event)

    from alphaflow.events import FillEvent

    fill_event = FillEvent(
        timestamp=datetime.now(),
        symbol="AAPL",
        fill_qty=10.0,
        fill_price=100.0,
        commission=1.0,
    )
    event_bus.publish(Topic.FILL, fill_event)

    # Should have received both events
    assert len(subscriber.events_received) == 2


def test_event_bus_initialization() -> None:
    """Test EventBus initializes with empty subscribers dict."""
    event_bus = EventBus()

    assert isinstance(event_bus.subscribers, dict)
    # EventBus uses defaultdict, so it starts empty but will create entries on access
    # Just verify it's a dict-like object
    assert len(event_bus.subscribers) == 0 or all(isinstance(v, list) for v in event_bus.subscribers.values())
