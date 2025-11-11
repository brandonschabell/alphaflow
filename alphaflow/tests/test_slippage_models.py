"""Tests for slippage models."""

from datetime import datetime

import pytest

from alphaflow import AlphaFlow
from alphaflow.enums import OrderType, Side
from alphaflow.events import OrderEvent
from alphaflow.slippage_models import FixedSlippageModel


def test_fixed_slippage_model_initialization() -> None:
    """Test FixedSlippageModel initializes with correct slippage_bps."""
    model = FixedSlippageModel(slippage_bps=5.0)
    assert model.slippage_bps == 5.0


def test_fixed_slippage_model_zero_slippage() -> None:
    """Test FixedSlippageModel with zero slippage returns market price unchanged."""
    model = FixedSlippageModel(slippage_bps=0.0)
    alpha_flow = AlphaFlow()

    order = OrderEvent(
        timestamp=datetime(2024, 1, 1),
        symbol="AAPL",
        side=Side.BUY,
        order_type=OrderType.MARKET,
        qty=100.0,
    )

    market_price = 150.0
    fill_price = model.calculate_slippage(order, market_price, alpha_flow)

    assert fill_price == pytest.approx(150.0)


def test_fixed_slippage_model_buy_increases_price() -> None:
    """Test FixedSlippageModel increases price for buy orders."""
    model = FixedSlippageModel(slippage_bps=5.0)  # 5 bps = 0.05%
    alpha_flow = AlphaFlow()

    order = OrderEvent(
        timestamp=datetime(2024, 1, 1),
        symbol="AAPL",
        side=Side.BUY,
        order_type=OrderType.MARKET,
        qty=100.0,
    )

    market_price = 100.0
    fill_price = model.calculate_slippage(order, market_price, alpha_flow)

    # Expected: 100.0 * (1 + 5/10000) = 100.05
    assert fill_price == pytest.approx(100.05, abs=1e-6)
    assert fill_price > market_price


def test_fixed_slippage_model_sell_decreases_price() -> None:
    """Test FixedSlippageModel decreases price for sell orders."""
    model = FixedSlippageModel(slippage_bps=5.0)  # 5 bps = 0.05%
    alpha_flow = AlphaFlow()

    order = OrderEvent(
        timestamp=datetime(2024, 1, 1),
        symbol="AAPL",
        side=Side.SELL,
        order_type=OrderType.MARKET,
        qty=100.0,
    )

    market_price = 100.0
    fill_price = model.calculate_slippage(order, market_price, alpha_flow)

    # Expected: 100.0 / (1 + 5/10000) = 99.95 (approximately)
    assert fill_price == pytest.approx(99.95002498750625, abs=1e-6)
    assert fill_price < market_price


@pytest.mark.parametrize(
    ("slippage_bps", "expected_buy_price"),
    [
        (1.0, 100.01),  # 1 bps
        (10.0, 100.10),  # 10 bps
        (50.0, 100.50),  # 50 bps
        (100.0, 101.0),  # 100 bps = 1%
    ],
)
def test_fixed_slippage_model_various_bps_values(slippage_bps: float, expected_buy_price: float) -> None:
    """Test FixedSlippageModel with various basis point values."""
    alpha_flow = AlphaFlow()
    market_price = 100.0

    model = FixedSlippageModel(slippage_bps=slippage_bps)

    buy_order = OrderEvent(
        timestamp=datetime(2024, 1, 1),
        symbol="AAPL",
        side=Side.BUY,
        order_type=OrderType.MARKET,
        qty=100.0,
    )

    fill_price = model.calculate_slippage(buy_order, market_price, alpha_flow)
    assert fill_price == pytest.approx(expected_buy_price, abs=1e-6)


def test_fixed_slippage_model_negative_slippage_raises_error() -> None:
    """Test FixedSlippageModel raises ValueError for negative slippage_bps."""
    with pytest.raises(ValueError, match="slippage_bps must be non-negative"):
        FixedSlippageModel(slippage_bps=-5.0)


def test_fixed_slippage_model_large_slippage() -> None:
    """Test FixedSlippageModel handles large slippage values correctly."""
    model = FixedSlippageModel(slippage_bps=500.0)  # 500 bps = 5%
    alpha_flow = AlphaFlow()

    buy_order = OrderEvent(
        timestamp=datetime(2024, 1, 1),
        symbol="AAPL",
        side=Side.BUY,
        order_type=OrderType.MARKET,
        qty=100.0,
    )

    market_price = 100.0
    fill_price = model.calculate_slippage(buy_order, market_price, alpha_flow)

    # Expected: 100.0 * (1 + 500/10000) = 105.0
    assert fill_price == pytest.approx(105.0, abs=1e-6)


@pytest.mark.parametrize("market_price", [10.0, 50.0, 100.0, 500.0, 1000.0])
def test_fixed_slippage_model_different_market_prices(market_price: float) -> None:
    """Test FixedSlippageModel scales correctly with different market prices."""
    model = FixedSlippageModel(slippage_bps=10.0)  # 10 bps = 0.1%
    alpha_flow = AlphaFlow()

    buy_order = OrderEvent(
        timestamp=datetime(2024, 1, 1),
        symbol="AAPL",
        side=Side.BUY,
        order_type=OrderType.MARKET,
        qty=100.0,
    )

    fill_price = model.calculate_slippage(buy_order, market_price, alpha_flow)
    expected_price = market_price * 1.001  # 0.1% increase
    assert fill_price == pytest.approx(expected_price, rel=1e-6)


def test_fixed_slippage_model_adverse_for_both_sides() -> None:
    """Test that slippage is adverse (costs money) for both buy and sell orders."""
    model = FixedSlippageModel(slippage_bps=10.0)
    alpha_flow = AlphaFlow()
    market_price = 100.0

    buy_order = OrderEvent(
        timestamp=datetime(2024, 1, 1),
        symbol="AAPL",
        side=Side.BUY,
        order_type=OrderType.MARKET,
        qty=100.0,
    )

    sell_order = OrderEvent(
        timestamp=datetime(2024, 1, 1),
        symbol="AAPL",
        side=Side.SELL,
        order_type=OrderType.MARKET,
        qty=100.0,
    )

    buy_fill_price = model.calculate_slippage(buy_order, market_price, alpha_flow)
    sell_fill_price = model.calculate_slippage(sell_order, market_price, alpha_flow)

    # Buy orders pay more than market price (adverse)
    assert buy_fill_price > market_price

    # Sell orders receive less than market price (adverse)
    assert sell_fill_price < market_price

    # Both sides experience slippage cost
    buy_slippage_cost = buy_fill_price - market_price
    sell_slippage_cost = market_price - sell_fill_price

    assert buy_slippage_cost > 0
    assert sell_slippage_cost > 0
