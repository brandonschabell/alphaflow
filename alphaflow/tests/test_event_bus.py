from datetime import datetime
from alphaflow.enums import Topic
from alphaflow.event_bus.event_bus import EventBus
from alphaflow.event_bus.subscriber import Subscriber
from alphaflow.events.event import Event
from alphaflow.events.market_data_event import MarketDataEvent


def test_subscribe_unsubscribe_publish():
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
