"""Tests for the EventQueue."""

from datetime import datetime

from alphaflow.enums import OrderType, Side, Topic
from alphaflow.event_bus.event_queue import EventQueue
from alphaflow.events import FillEvent, MarketDataEvent, OrderEvent


def test_event_queue_initialization() -> None:
    """Test event queue initializes empty."""
    queue = EventQueue()

    assert queue.is_empty()
    assert queue.size() == 0
    assert queue.peek() is None


def test_event_queue_push_pop() -> None:
    """Test pushing and popping events."""
    queue = EventQueue()

    event1 = MarketDataEvent(
        timestamp=datetime(2020, 1, 1),
        symbol="AAPL",
        open=100.0,
        high=101.0,
        low=99.0,
        close=100.5,
        volume=1000.0,
    )

    queue.push(Topic.MARKET_DATA, event1, priority=0)

    assert not queue.is_empty()
    assert queue.size() == 1
    peek_result = queue.peek()
    assert peek_result is not None
    assert peek_result[0] == Topic.MARKET_DATA
    assert peek_result[1] == event1

    topic, popped = queue.pop()
    assert topic == Topic.MARKET_DATA
    assert popped == event1
    assert queue.is_empty()


def test_event_queue_chronological_order() -> None:
    """Test events are ordered by timestamp."""
    queue = EventQueue()

    event1 = MarketDataEvent(
        timestamp=datetime(2020, 1, 3),
        symbol="AAPL",
        open=100.0,
        high=101.0,
        low=99.0,
        close=100.5,
        volume=1000.0,
    )

    event2 = MarketDataEvent(
        timestamp=datetime(2020, 1, 1),
        symbol="GOOGL",
        open=200.0,
        high=201.0,
        low=199.0,
        close=200.5,
        volume=2000.0,
    )

    event3 = MarketDataEvent(
        timestamp=datetime(2020, 1, 2),
        symbol="MSFT",
        open=150.0,
        high=151.0,
        low=149.0,
        close=150.5,
        volume=1500.0,
    )

    # Add events out of order
    queue.push(Topic.MARKET_DATA, event1, priority=0)
    queue.push(Topic.MARKET_DATA, event2, priority=0)
    queue.push(Topic.MARKET_DATA, event3, priority=0)

    # Should come out in chronological order
    _, evt2 = queue.pop()
    assert evt2 == event2  # 2020-01-01
    _, evt3 = queue.pop()
    assert evt3 == event3  # 2020-01-02
    _, evt1 = queue.pop()
    assert evt1 == event1  # 2020-01-03


def test_event_queue_priority_order() -> None:
    """Test events at same timestamp are ordered by priority."""
    queue = EventQueue()

    timestamp = datetime(2020, 1, 1)

    market_event = MarketDataEvent(
        timestamp=timestamp,
        symbol="AAPL",
        open=100.0,
        high=101.0,
        low=99.0,
        close=100.5,
        volume=1000.0,
    )

    order_event = OrderEvent(
        timestamp=timestamp,
        symbol="AAPL",
        side=Side.BUY,
        qty=10.0,
        order_type=OrderType.MARKET,
    )

    fill_event = FillEvent(
        timestamp=timestamp,
        symbol="AAPL",
        fill_price=100.5,
        fill_qty=10.0,
        commission=1.0,
    )

    # Add events in wrong order (fill, order, market)
    queue.push(Topic.FILL, fill_event, priority=2)
    queue.push(Topic.ORDER, order_event, priority=1)
    queue.push(Topic.MARKET_DATA, market_event, priority=0)

    # Should come out in priority order (market, order, fill)
    _, evt1 = queue.pop()
    assert isinstance(evt1, MarketDataEvent)
    _, evt2 = queue.pop()
    assert isinstance(evt2, OrderEvent)
    _, evt3 = queue.pop()
    assert isinstance(evt3, FillEvent)


def test_event_queue_fifo_for_same_priority() -> None:
    """Test FIFO order for events with same timestamp and priority."""
    queue = EventQueue()

    timestamp = datetime(2020, 1, 1)

    event1 = MarketDataEvent(
        timestamp=timestamp,
        symbol="AAPL",
        open=100.0,
        high=101.0,
        low=99.0,
        close=100.5,
        volume=1000.0,
    )

    event2 = MarketDataEvent(
        timestamp=timestamp,
        symbol="GOOGL",
        open=200.0,
        high=201.0,
        low=199.0,
        close=200.5,
        volume=2000.0,
    )

    event3 = MarketDataEvent(
        timestamp=timestamp,
        symbol="MSFT",
        open=150.0,
        high=151.0,
        low=149.0,
        close=150.5,
        volume=1500.0,
    )

    # Add events with same timestamp and priority
    queue.push(Topic.MARKET_DATA, event1, priority=0)
    queue.push(Topic.MARKET_DATA, event2, priority=0)
    queue.push(Topic.MARKET_DATA, event3, priority=0)

    # Should come out in FIFO order
    _, popped1 = queue.pop()
    assert isinstance(popped1, MarketDataEvent)
    assert popped1.symbol == "AAPL"

    _, popped2 = queue.pop()
    assert isinstance(popped2, MarketDataEvent)
    assert popped2.symbol == "GOOGL"

    _, popped3 = queue.pop()
    assert isinstance(popped3, MarketDataEvent)
    assert popped3.symbol == "MSFT"


def test_event_queue_peek_does_not_remove() -> None:
    """Test peek doesn't remove the event."""
    queue = EventQueue()

    event = MarketDataEvent(
        timestamp=datetime(2020, 1, 1),
        symbol="AAPL",
        open=100.0,
        high=101.0,
        low=99.0,
        close=100.5,
        volume=1000.0,
    )

    queue.push(Topic.MARKET_DATA, event, priority=0)

    # Peek multiple times
    peek_result = queue.peek()
    assert peek_result is not None
    assert peek_result[1] == event
    peek_result2 = queue.peek()
    assert peek_result2 is not None
    assert peek_result2[1] == event
    assert queue.size() == 1

    # Pop removes it
    _, popped = queue.pop()
    assert popped == event
    assert queue.is_empty()


def test_event_queue_clear() -> None:
    """Test clearing the queue."""
    queue = EventQueue()

    for i in range(5):
        event = MarketDataEvent(
            timestamp=datetime(2020, 1, i + 1),
            symbol="AAPL",
            open=100.0,
            high=101.0,
            low=99.0,
            close=100.5,
            volume=1000.0,
        )
        queue.push(Topic.MARKET_DATA, event, priority=0)

    assert queue.size() == 5

    queue.clear()

    assert queue.is_empty()
    assert queue.size() == 0
    assert queue.peek() is None


def test_event_queue_mixed_event_types() -> None:
    """Test queue handles multiple event types correctly."""
    queue = EventQueue()

    # Create events at different times with different priorities
    market_event_t1 = MarketDataEvent(
        timestamp=datetime(2020, 1, 1, 9, 30),
        symbol="AAPL",
        open=100.0,
        high=101.0,
        low=99.0,
        close=100.5,
        volume=1000.0,
    )

    order_event_t1 = OrderEvent(
        timestamp=datetime(2020, 1, 1, 9, 30),
        symbol="AAPL",
        side=Side.BUY,
        qty=10.0,
        order_type=OrderType.MARKET,
    )

    market_event_t2 = MarketDataEvent(
        timestamp=datetime(2020, 1, 1, 9, 31),
        symbol="AAPL",
        open=101.0,
        high=102.0,
        low=100.0,
        close=101.5,
        volume=1100.0,
    )

    fill_event_t1 = FillEvent(
        timestamp=datetime(2020, 1, 1, 9, 30),
        symbol="AAPL",
        fill_price=100.5,
        fill_qty=10.0,
        commission=1.0,
    )

    # Add in random order
    queue.push(Topic.MARKET_DATA, market_event_t2, priority=0)
    queue.push(Topic.FILL, fill_event_t1, priority=2)
    queue.push(Topic.ORDER, order_event_t1, priority=1)
    queue.push(Topic.MARKET_DATA, market_event_t1, priority=0)

    # Should get: market@9:30, order@9:30, fill@9:30, market@9:31
    _, event1 = queue.pop()
    assert isinstance(event1, MarketDataEvent)
    assert event1.timestamp == datetime(2020, 1, 1, 9, 30)

    _, event2 = queue.pop()
    assert isinstance(event2, OrderEvent)
    assert event2.timestamp == datetime(2020, 1, 1, 9, 30)

    _, event3 = queue.pop()
    assert isinstance(event3, FillEvent)
    assert event3.timestamp == datetime(2020, 1, 1, 9, 30)

    _, event4 = queue.pop()
    assert isinstance(event4, MarketDataEvent)
    assert event4.timestamp == datetime(2020, 1, 1, 9, 31)
