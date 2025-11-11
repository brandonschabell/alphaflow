"""Fixed commission model for AlphaFlow."""

from alphaflow import CommissionModel
from alphaflow.events import OrderEvent


class FixedCommissionModel(CommissionModel):
    """Fixed commission per trade.

    Charges a flat fee per trade regardless of trade size, symbol, or direction.
    This is common for retail brokers with flat-fee pricing structures.

    Example:
        With commission_per_trade=4.95:
        - Trading 10 shares costs $4.95
        - Trading 1000 shares also costs $4.95

    """

    def __init__(self, commission_per_trade: float) -> None:
        """Initialize the fixed commission model.

        Args:
            commission_per_trade: Fixed commission per trade (e.g., 4.95 for $4.95).
                                 Must be non-negative.

        Raises:
            ValueError: If commission_per_trade is negative.

        """
        if commission_per_trade < 0:
            raise ValueError(f"commission_per_trade must be non-negative, got {commission_per_trade}")
        self.commission_per_trade = commission_per_trade

    def calculate_commission(
        self,
        order_event: OrderEvent,
        fill_price: float,
        fill_qty: float,
    ) -> float:
        """Calculate the fixed commission.

        Args:
            order_event: The order being executed (unused).
            fill_price: The price at which the order was filled (unused).
            fill_qty: The quantity filled (unused).

        Returns:
            The fixed commission amount.

        """
        return self.commission_per_trade
