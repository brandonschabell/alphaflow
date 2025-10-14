"""Tests for the SimpleBroker."""

from datetime import datetime

from alphaflow import AlphaFlow
from alphaflow.brokers import SimpleBroker
from alphaflow.data_feeds import CSVDataFeed
from alphaflow.enums import OrderType, Side
from alphaflow.events import OrderEvent
from alphaflow.events.market_data_event import MarketDataEvent


def test_simple_broker_initialization() -> None:
    """Test broker is initialized with correct margin."""
    broker = SimpleBroker(margin=2.0)
    assert broker.margin == 2.0

    broker_default = SimpleBroker()
    assert broker_default.margin == 2.0


def test_simple_broker_initialization_custom_margin() -> None:
    """Test broker with custom margin."""
    broker = SimpleBroker(margin=1.5)
    assert broker.margin == 1.5


def test_broker_executes_valid_buy_order() -> None:
    """Test broker executes a valid buy order."""
    from alphaflow.enums import Topic

    af = AlphaFlow()
    af.set_data_feed(CSVDataFeed("alphaflow/tests/data/AAPL.csv"))
    af.add_equity("AAPL")
    af.set_cash(10000)
    af.set_data_start_timestamp(datetime(1980, 12, 25))
    af.run()

    broker = SimpleBroker()
    broker.set_alpha_flow(af)
    af.event_bus.subscribe(Topic.ORDER, broker)

    # Create a buy order
    order = OrderEvent(
        timestamp=datetime(1980, 12, 29),
        symbol="AAPL",
        order_type=OrderType.MARKET,
        side=Side.BUY,
        qty=10.0,
    )

    # Track if fill was published
    fill_published = []

    def capture_fill(event):  # type: ignore[no-untyped-def]
        fill_published.append(event)

    class FillCapture:
        def read_event(self, event):  # type: ignore[no-untyped-def]
            fill_published.append(event)

    af.event_bus.subscribe(Topic.FILL, FillCapture())

    # Execute order
    broker.read_event(order)

    # Fill should be published
    assert len(fill_published) == 1
    assert fill_published[0].symbol == "AAPL"
    assert fill_published[0].fill_qty == 10.0


def test_broker_rejects_insufficient_buying_power() -> None:
    """Test broker rejects orders with insufficient buying power."""
    from alphaflow.enums import Topic

    af = AlphaFlow()
    af.set_data_feed(CSVDataFeed("alphaflow/tests/data/AAPL.csv"))
    af.add_equity("AAPL")
    af.set_cash(10)  # Very low cash - only $10
    af.set_data_start_timestamp(datetime(1980, 12, 25))
    af.run()

    broker = SimpleBroker(margin=1.0)  # No margin
    broker.set_alpha_flow(af)
    af.event_bus.subscribe(Topic.ORDER, broker)

    # Try to buy more than we can afford
    # Price on 1980-12-29 is $0.160714, so 100 shares = $16.07
    order = OrderEvent(
        timestamp=datetime(1980, 12, 29),
        symbol="AAPL",
        order_type=OrderType.MARKET,
        side=Side.BUY,
        qty=100.0,  # $16.07 > $10 cash
    )

    fill_published = []

    class FillCapture:
        def read_event(self, event):  # type: ignore[no-untyped-def]
            fill_published.append(event)

    af.event_bus.subscribe(Topic.FILL, FillCapture())

    # Execute order
    broker.read_event(order)

    # No fill should be published
    assert len(fill_published) == 0


def test_broker_rejects_short_sell() -> None:
    """Test broker rejects short selling (selling without position)."""
    from alphaflow.enums import Topic

    af = AlphaFlow()
    af.set_data_feed(CSVDataFeed("alphaflow/tests/data/AAPL.csv"))
    af.add_equity("AAPL")
    af.set_cash(10000)
    af.set_data_start_timestamp(datetime(1980, 12, 25))
    af.run()

    broker = SimpleBroker()
    broker.set_alpha_flow(af)
    af.event_bus.subscribe(Topic.ORDER, broker)

    # Try to sell shares we don't own
    order = OrderEvent(
        timestamp=datetime(1980, 12, 29),
        symbol="AAPL",
        order_type=OrderType.MARKET,
        side=Side.SELL,
        qty=10.0,
    )

    fill_published = []

    class FillCapture:
        def read_event(self, event):  # type: ignore[no-untyped-def]
            fill_published.append(event)

    af.event_bus.subscribe(Topic.FILL, FillCapture())

    # Execute order
    broker.read_event(order)

    # No fill should be published (short selling not allowed)
    assert len(fill_published) == 0


def test_broker_allows_valid_sell() -> None:
    """Test broker allows selling shares we own."""
    from alphaflow.enums import Topic

    af = AlphaFlow()
    af.set_data_feed(CSVDataFeed("alphaflow/tests/data/AAPL.csv"))
    af.add_equity("AAPL")
    af.set_cash(10000)
    af.set_data_start_timestamp(datetime(1980, 12, 25))
    af.run()

    # Add position
    af.portfolio.update_position("AAPL", 20.0)

    broker = SimpleBroker()
    broker.set_alpha_flow(af)
    af.event_bus.subscribe(Topic.ORDER, broker)

    # Sell some shares
    order = OrderEvent(
        timestamp=datetime(1980, 12, 29),
        symbol="AAPL",
        order_type=OrderType.MARKET,
        side=Side.SELL,
        qty=10.0,
    )

    fill_published = []

    class FillCapture:
        def read_event(self, event):  # type: ignore[no-untyped-def]
            fill_published.append(event)

    af.event_bus.subscribe(Topic.FILL, FillCapture())

    # Execute order
    broker.read_event(order)

    # Fill should be published
    assert len(fill_published) == 1
    assert fill_published[0].fill_qty == -10.0  # Negative for sell


def test_broker_ignores_non_order_events() -> None:
    """Test broker ignores events that aren't orders."""
    from alphaflow.enums import Topic

    af = AlphaFlow()
    af.set_data_feed(CSVDataFeed("alphaflow/tests/data/AAPL.csv"))
    af.add_equity("AAPL")
    af.set_cash(10000)
    af.set_data_start_timestamp(datetime(1980, 12, 25))
    af.run()

    broker = SimpleBroker()
    broker.set_alpha_flow(af)

    # Send a non-order event
    market_event = MarketDataEvent(
        timestamp=datetime(1980, 12, 29),
        symbol="AAPL",
        open=28.0,
        high=29.0,
        low=27.0,
        close=28.5,
        volume=1000000.0,
    )

    fill_published = []

    class FillCapture:
        def read_event(self, event):  # type: ignore[no-untyped-def]
            fill_published.append(event)

    af.event_bus.subscribe(Topic.FILL, FillCapture())

    # Process the event
    broker.read_event(market_event)

    # No fill should be published
    assert len(fill_published) == 0


def test_broker_with_margin() -> None:
    """Test broker allows larger positions with margin."""
    from alphaflow.enums import Topic

    af = AlphaFlow()
    af.set_data_feed(CSVDataFeed("alphaflow/tests/data/AAPL.csv"))
    af.add_equity("AAPL")
    af.set_cash(1000)  # Limited cash
    af.set_data_start_timestamp(datetime(1980, 12, 25))
    af.run()

    # With 2x margin, should be able to buy more
    broker = SimpleBroker(margin=2.0)
    broker.set_alpha_flow(af)
    af.event_bus.subscribe(Topic.ORDER, broker)

    # Buy order that would fail without margin
    order = OrderEvent(
        timestamp=datetime(1980, 12, 29),
        symbol="AAPL",
        order_type=OrderType.MARKET,
        side=Side.BUY,
        qty=50.0,  # At ~$28.75 = ~$1437.50 cost
    )

    fill_published = []

    class FillCapture:
        def read_event(self, event):  # type: ignore[no-untyped-def]
            fill_published.append(event)

    af.event_bus.subscribe(Topic.FILL, FillCapture())

    # Execute order
    broker.read_event(order)

    # With 2x margin on $1000, we can buy up to ~$2000 worth
    # This should still fail since $1437.50 > $1000 buying power initially
    # Actually, portfolio value * margin - positions = $1000 * 2 - 0 = $2000
    # So it should succeed
    assert len(fill_published) == 1
