"""Percentage-based commission model for AlphaFlow."""

from alphaflow import CommissionModel
from alphaflow.events import OrderEvent


class PercentageCommissionModel(CommissionModel):
    """Percentage-based commission model.

    Charges a percentage of the trade's notional value (price * quantity),
    with an optional minimum commission. This is common for forex brokers
    and some international equity brokers.

    Example:
        With commission_pct=0.1 and min_commission=2.0:
        - Trading 100 shares at $50: notional = $5,000
          Commission = $5,000 * 0.1% = $5.00
        - Trading 10 shares at $10: notional = $100
          Commission = $100 * 0.1% = $0.10, but minimum is $2.00, so charge $2.00

    """

    def __init__(self, commission_pct: float, min_commission: float = 0.0) -> None:
        """Initialize the percentage commission model.

        Args:
            commission_pct: Commission as a percentage (e.g., 0.1 for 0.1%).
                           Must be non-negative.
            min_commission: Minimum commission per trade (e.g., 1.0 for $1 minimum).
                           Must be non-negative. Defaults to 0.0.

        Raises:
            ValueError: If commission_pct or min_commission is negative.

        """
        if commission_pct < 0:
            raise ValueError(f"commission_pct must be non-negative, got {commission_pct}")
        if min_commission < 0:
            raise ValueError(f"min_commission must be non-negative, got {min_commission}")
        self.commission_pct = commission_pct
        self.min_commission = min_commission

    def calculate_commission(
        self,
        order_event: OrderEvent,
        fill_price: float,
        fill_qty: float,
    ) -> float:
        """Calculate the percentage-based commission.

        Args:
            order_event: The order being executed (unused).
            fill_price: The price at which the order was filled.
            fill_qty: The quantity filled (signed).

        Returns:
            The commission amount, which is the greater of the percentage-based cost
            or the minimum commission.

        """
        notional_value = abs(fill_price * fill_qty)
        commission = notional_value * (self.commission_pct / 100)
        return max(commission, self.min_commission)
