"""Tests for commission models."""

from datetime import datetime

import pytest

from alphaflow.commission_models import (
    FixedCommissionModel,
    PercentageCommissionModel,
    PerShareCommissionModel,
)
from alphaflow.enums import OrderType, Side
from alphaflow.events import OrderEvent

# ===== FixedCommissionModel Tests =====


def test_fixed_commission_model_initialization() -> None:
    """Test FixedCommissionModel initializes correctly."""
    model = FixedCommissionModel(commission_per_trade=4.95)
    assert model.commission_per_trade == 4.95


def test_fixed_commission_model_returns_fixed_amount() -> None:
    """Test FixedCommissionModel returns the same amount regardless of trade size."""
    model = FixedCommissionModel(commission_per_trade=5.0)

    order = OrderEvent(
        timestamp=datetime(2024, 1, 1),
        symbol="AAPL",
        side=Side.BUY,
        order_type=OrderType.MARKET,
        qty=100.0,
    )

    # Small trade
    commission_small = model.calculate_commission(order, fill_price=100.0, fill_qty=10.0)
    assert commission_small == 5.0

    # Large trade
    commission_large = model.calculate_commission(order, fill_price=100.0, fill_qty=1000.0)
    assert commission_large == 5.0


def test_fixed_commission_model_works_for_sells() -> None:
    """Test FixedCommissionModel works for sell orders."""
    model = FixedCommissionModel(commission_per_trade=3.99)

    order = OrderEvent(
        timestamp=datetime(2024, 1, 1),
        symbol="AAPL",
        side=Side.SELL,
        order_type=OrderType.MARKET,
        qty=100.0,
    )

    commission = model.calculate_commission(order, fill_price=100.0, fill_qty=-100.0)
    assert commission == 3.99


def test_fixed_commission_model_negative_commission_raises_error() -> None:
    """Test FixedCommissionModel raises ValueError for negative commission."""
    with pytest.raises(ValueError, match="commission_per_trade must be non-negative"):
        FixedCommissionModel(commission_per_trade=-1.0)


def test_fixed_commission_model_zero_commission() -> None:
    """Test FixedCommissionModel with zero commission."""
    model = FixedCommissionModel(commission_per_trade=0.0)

    order = OrderEvent(
        timestamp=datetime(2024, 1, 1),
        symbol="AAPL",
        side=Side.BUY,
        order_type=OrderType.MARKET,
        qty=100.0,
    )

    commission = model.calculate_commission(order, fill_price=100.0, fill_qty=100.0)
    assert commission == 0.0


# ===== PerShareCommissionModel Tests =====


def test_per_share_commission_model_initialization() -> None:
    """Test PerShareCommissionModel initializes correctly."""
    model = PerShareCommissionModel(commission_per_share=0.005, min_commission=1.0)
    assert model.commission_per_share == 0.005
    assert model.min_commission == 1.0


def test_per_share_commission_model_calculates_correctly() -> None:
    """Test PerShareCommissionModel calculates per-share commission."""
    model = PerShareCommissionModel(commission_per_share=0.01, min_commission=0.0)

    order = OrderEvent(
        timestamp=datetime(2024, 1, 1),
        symbol="AAPL",
        side=Side.BUY,
        order_type=OrderType.MARKET,
        qty=100.0,
    )

    # 100 shares * $0.01 = $1.00
    commission = model.calculate_commission(order, fill_price=100.0, fill_qty=100.0)
    assert commission == pytest.approx(1.0)


def test_per_share_commission_model_minimum_commission() -> None:
    """Test PerShareCommissionModel enforces minimum commission."""
    model = PerShareCommissionModel(commission_per_share=0.005, min_commission=1.0)

    order = OrderEvent(
        timestamp=datetime(2024, 1, 1),
        symbol="AAPL",
        side=Side.BUY,
        order_type=OrderType.MARKET,
        qty=10.0,
    )

    # 10 shares * $0.005 = $0.05, but minimum is $1.00
    commission = model.calculate_commission(order, fill_price=100.0, fill_qty=10.0)
    assert commission == 1.0


def test_per_share_commission_model_above_minimum() -> None:
    """Test PerShareCommissionModel when calculated commission exceeds minimum."""
    model = PerShareCommissionModel(commission_per_share=0.005, min_commission=1.0)

    order = OrderEvent(
        timestamp=datetime(2024, 1, 1),
        symbol="AAPL",
        side=Side.BUY,
        order_type=OrderType.MARKET,
        qty=500.0,
    )

    # 500 shares * $0.005 = $2.50, which exceeds $1.00 minimum
    commission = model.calculate_commission(order, fill_price=100.0, fill_qty=500.0)
    assert commission == pytest.approx(2.5)


def test_per_share_commission_model_sell_orders() -> None:
    """Test PerShareCommissionModel uses absolute quantity for sells."""
    model = PerShareCommissionModel(commission_per_share=0.01, min_commission=0.0)

    order = OrderEvent(
        timestamp=datetime(2024, 1, 1),
        symbol="AAPL",
        side=Side.SELL,
        order_type=OrderType.MARKET,
        qty=100.0,
    )

    # Sell orders have negative fill_qty, but commission should be positive
    commission = model.calculate_commission(order, fill_price=100.0, fill_qty=-100.0)
    assert commission == pytest.approx(1.0)
    assert commission > 0


def test_per_share_commission_model_negative_parameters_raise_error() -> None:
    """Test PerShareCommissionModel raises ValueError for negative parameters."""
    with pytest.raises(ValueError, match="commission_per_share must be non-negative"):
        PerShareCommissionModel(commission_per_share=-0.01, min_commission=1.0)

    with pytest.raises(ValueError, match="min_commission must be non-negative"):
        PerShareCommissionModel(commission_per_share=0.01, min_commission=-1.0)


# ===== PercentageCommissionModel Tests =====


def test_percentage_commission_model_initialization() -> None:
    """Test PercentageCommissionModel initializes correctly."""
    model = PercentageCommissionModel(commission_pct=0.1, min_commission=2.0)
    assert model.commission_pct == 0.1
    assert model.min_commission == 2.0


def test_percentage_commission_model_calculates_correctly() -> None:
    """Test PercentageCommissionModel calculates percentage-based commission."""
    model = PercentageCommissionModel(commission_pct=0.1, min_commission=0.0)

    order = OrderEvent(
        timestamp=datetime(2024, 1, 1),
        symbol="AAPL",
        side=Side.BUY,
        order_type=OrderType.MARKET,
        qty=100.0,
    )

    # Notional value = 100 shares * $100 = $10,000
    # Commission = $10,000 * 0.1% = $10.00
    commission = model.calculate_commission(order, fill_price=100.0, fill_qty=100.0)
    assert commission == pytest.approx(10.0)


def test_percentage_commission_model_minimum_commission() -> None:
    """Test PercentageCommissionModel enforces minimum commission."""
    model = PercentageCommissionModel(commission_pct=0.1, min_commission=5.0)

    order = OrderEvent(
        timestamp=datetime(2024, 1, 1),
        symbol="AAPL",
        side=Side.BUY,
        order_type=OrderType.MARKET,
        qty=10.0,
    )

    # Notional value = 10 shares * $10 = $100
    # Commission = $100 * 0.1% = $0.10, but minimum is $5.00
    commission = model.calculate_commission(order, fill_price=10.0, fill_qty=10.0)
    assert commission == 5.0


def test_percentage_commission_model_above_minimum() -> None:
    """Test PercentageCommissionModel when calculated commission exceeds minimum."""
    model = PercentageCommissionModel(commission_pct=0.5, min_commission=1.0)

    order = OrderEvent(
        timestamp=datetime(2024, 1, 1),
        symbol="AAPL",
        side=Side.BUY,
        order_type=OrderType.MARKET,
        qty=1000.0,
    )

    # Notional value = 1000 shares * $100 = $100,000
    # Commission = $100,000 * 0.5% = $500, which exceeds $1.00 minimum
    commission = model.calculate_commission(order, fill_price=100.0, fill_qty=1000.0)
    assert commission == pytest.approx(500.0)


def test_percentage_commission_model_sell_orders() -> None:
    """Test PercentageCommissionModel uses absolute notional value for sells."""
    model = PercentageCommissionModel(commission_pct=0.2, min_commission=0.0)

    order = OrderEvent(
        timestamp=datetime(2024, 1, 1),
        symbol="AAPL",
        side=Side.SELL,
        order_type=OrderType.MARKET,
        qty=100.0,
    )

    # Notional value = |100 * -$100| = $10,000
    # Commission = $10,000 * 0.2% = $20.00
    commission = model.calculate_commission(order, fill_price=100.0, fill_qty=-100.0)
    assert commission == pytest.approx(20.0)
    assert commission > 0


@pytest.mark.parametrize(
    ("fill_price", "expected_commission"),
    [
        (10.0, 1.0),  # $1,000 notional * 0.1% = $1.00
        (50.0, 5.0),  # $5,000 notional * 0.1% = $5.00
        (100.0, 10.0),  # $10,000 notional * 0.1% = $10.00
        (500.0, 50.0),  # $50,000 notional * 0.1% = $50.00
    ],
)
def test_percentage_commission_model_different_prices(fill_price: float, expected_commission: float) -> None:
    """Test PercentageCommissionModel scales with different fill prices."""
    model = PercentageCommissionModel(commission_pct=0.1, min_commission=0.0)

    order = OrderEvent(
        timestamp=datetime(2024, 1, 1),
        symbol="AAPL",
        side=Side.BUY,
        order_type=OrderType.MARKET,
        qty=100.0,
    )

    commission = model.calculate_commission(order, fill_price=fill_price, fill_qty=100.0)
    assert commission == pytest.approx(expected_commission)


def test_percentage_commission_model_negative_parameters_raise_error() -> None:
    """Test PercentageCommissionModel raises ValueError for negative parameters."""
    with pytest.raises(ValueError, match="commission_pct must be non-negative"):
        PercentageCommissionModel(commission_pct=-0.1, min_commission=1.0)

    with pytest.raises(ValueError, match="min_commission must be non-negative"):
        PercentageCommissionModel(commission_pct=0.1, min_commission=-1.0)
