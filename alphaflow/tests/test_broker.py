"""Tests for the SimpleBroker."""

from datetime import datetime

import pytest

from alphaflow import AlphaFlow
from alphaflow.brokers import SimpleBroker
from alphaflow.commission_models import FixedCommissionModel, PerShareCommissionModel
from alphaflow.data_feeds import PolarsDataFeed
from alphaflow.enums import OrderType, Side, Topic
from alphaflow.events import OrderEvent
from alphaflow.events.market_data_event import MarketDataEvent
from alphaflow.slippage_models import FixedSlippageModel


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
    af = AlphaFlow()
    af.set_data_feed(PolarsDataFeed("alphaflow/tests/data/AAPL.csv"))
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
    af = AlphaFlow()
    af.set_data_feed(PolarsDataFeed("alphaflow/tests/data/AAPL.csv"))
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
    af = AlphaFlow()
    af.set_data_feed(PolarsDataFeed("alphaflow/tests/data/AAPL.csv"))
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
    af = AlphaFlow()
    af.set_data_feed(PolarsDataFeed("alphaflow/tests/data/AAPL.csv"))
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
    af = AlphaFlow()
    af.set_data_feed(PolarsDataFeed("alphaflow/tests/data/AAPL.csv"))
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
    af = AlphaFlow()
    af.set_data_feed(PolarsDataFeed("alphaflow/tests/data/AAPL.csv"))
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


def test_broker_with_slippage_and_commission() -> None:
    """Test broker with both slippage and commission models."""
    af = AlphaFlow()
    af.set_data_feed(PolarsDataFeed("alphaflow/tests/data/AAPL.csv"))
    af.add_equity("AAPL")
    af.set_cash(10000)
    af.set_data_start_timestamp(datetime(1980, 12, 25))
    af.run()

    # Create broker with slippage and commission
    broker = SimpleBroker(
        margin=2.0,
        slippage_model=FixedSlippageModel(slippage_bps=5.0),  # 5 bps slippage
        commission_model=PerShareCommissionModel(commission_per_share=0.01, min_commission=1.0),
    )
    broker.set_alpha_flow(af)
    af.event_bus.subscribe(Topic.ORDER, broker)

    # Buy order
    order = OrderEvent(
        timestamp=datetime(1980, 12, 29),
        symbol="AAPL",
        order_type=OrderType.MARKET,
        side=Side.BUY,
        qty=100.0,
    )

    fill_published = []

    class FillCapture:
        def read_event(self, event):  # type: ignore[no-untyped-def]
            fill_published.append(event)

    af.event_bus.subscribe(Topic.FILL, FillCapture())

    # Get market price for verification
    market_price = af.get_price("AAPL", datetime(1980, 12, 29))

    # Execute order
    broker.read_event(order)

    # Verify fill was published
    assert len(fill_published) == 1
    fill = fill_published[0]

    # Verify slippage was applied (buy price should be higher)
    expected_fill_price = market_price * (1 + 5.0 / 10000)  # 5 bps
    assert fill.fill_price == pytest.approx(expected_fill_price, abs=1e-6)
    assert fill.fill_price > market_price

    # Verify commission was applied
    expected_commission = max(100.0 * 0.01, 1.0)  # 100 shares * $0.01, min $1
    assert fill.commission == pytest.approx(expected_commission)

    # Verify portfolio was updated correctly
    # Cost = fill_price * qty + commission
    expected_cost = expected_fill_price * 100.0 + expected_commission
    expected_cash = 10000 - expected_cost
    assert af.portfolio.get_cash() == pytest.approx(expected_cash, abs=1e-2)
    assert af.portfolio.get_position("AAPL") == 100.0


def test_broker_slippage_affects_buying_power_validation() -> None:
    """Test that slippage is considered when validating buying power."""
    af = AlphaFlow()
    af.set_data_feed(PolarsDataFeed("alphaflow/tests/data/AAPL.csv"))
    af.add_equity("AAPL")
    af.set_data_start_timestamp(datetime(1980, 12, 25))
    af.run()

    # Set cash such that order passes without slippage but fails with slippage
    market_price = af.get_price("AAPL", datetime(1980, 12, 29))
    qty = 100.0
    # Set cash to exactly cover market price purchase
    af.set_cash(market_price * qty)

    # Create broker with slippage (no margin)
    broker = SimpleBroker(
        margin=1.0,
        slippage_model=FixedSlippageModel(slippage_bps=50.0),  # 50 bps = 0.5%
    )
    broker.set_alpha_flow(af)
    af.event_bus.subscribe(Topic.ORDER, broker)

    order = OrderEvent(
        timestamp=datetime(1980, 12, 29),
        symbol="AAPL",
        order_type=OrderType.MARKET,
        side=Side.BUY,
        qty=qty,
    )

    fill_published = []

    class FillCapture:
        def read_event(self, event):  # type: ignore[no-untyped-def]
            fill_published.append(event)

    af.event_bus.subscribe(Topic.FILL, FillCapture())

    # Execute order - should be rejected due to slippage
    broker.read_event(order)

    # No fill should be published (insufficient funds with slippage)
    assert len(fill_published) == 0


def test_broker_commission_affects_buying_power_validation() -> None:
    """Test that commission is considered when validating buying power."""
    af = AlphaFlow()
    af.set_data_feed(PolarsDataFeed("alphaflow/tests/data/AAPL.csv"))
    af.add_equity("AAPL")
    af.set_data_start_timestamp(datetime(1980, 12, 25))
    af.run()

    # Set cash such that order passes without commission but fails with commission
    market_price = af.get_price("AAPL", datetime(1980, 12, 29))
    qty = 100.0
    commission = 5.0

    # Set cash to exactly cover market price purchase (but not commission)
    af.set_cash(market_price * qty)

    # Create broker with commission (no margin)
    broker = SimpleBroker(
        margin=1.0,
        commission_model=FixedCommissionModel(commission_per_trade=commission),
    )
    broker.set_alpha_flow(af)
    af.event_bus.subscribe(Topic.ORDER, broker)

    order = OrderEvent(
        timestamp=datetime(1980, 12, 29),
        symbol="AAPL",
        order_type=OrderType.MARKET,
        side=Side.BUY,
        qty=qty,
    )

    fill_published = []

    class FillCapture:
        def read_event(self, event):  # type: ignore[no-untyped-def]
            fill_published.append(event)

    af.event_bus.subscribe(Topic.FILL, FillCapture())

    # Execute order - should be rejected due to commission
    broker.read_event(order)

    # No fill should be published (insufficient funds with commission)
    assert len(fill_published) == 0
