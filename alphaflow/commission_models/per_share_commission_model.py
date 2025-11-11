"""Per-share commission model for AlphaFlow."""

from alphaflow import CommissionModel
from alphaflow.events import OrderEvent


class PerShareCommissionModel(CommissionModel):
    """Per-share commission model.

    Charges a fixed amount per share traded, with an optional minimum commission.
    This is common for US equities brokers and professional trading platforms.

    Example:
        With commission_per_share=0.005 and min_commission=1.0:
        - Trading 100 shares: 100 * $0.005 = $0.50, but minimum is $1.00, so charge $1.00
        - Trading 500 shares: 500 * $0.005 = $2.50, which exceeds minimum, so charge $2.50

    """

    def __init__(self, commission_per_share: float, min_commission: float = 0.0) -> None:
        """Initialize the per-share commission model.

        Args:
            commission_per_share: Commission charged per share (e.g., 0.005 for $0.005/share).
                                 Must be non-negative.
            min_commission: Minimum commission per trade (e.g., 1.0 for $1 minimum).
                           Must be non-negative. Defaults to 0.0.

        Raises:
            ValueError: If commission_per_share or min_commission is negative.

        """
        if commission_per_share < 0:
            raise ValueError(f"commission_per_share must be non-negative, got {commission_per_share}")
        if min_commission < 0:
            raise ValueError(f"min_commission must be non-negative, got {min_commission}")
        self.commission_per_share = commission_per_share
        self.min_commission = min_commission

    def calculate_commission(
        self,
        order_event: OrderEvent,
        fill_price: float,
        fill_qty: float,
    ) -> float:
        """Calculate the per-share commission.

        Args:
            order_event: The order being executed (unused).
            fill_price: The price at which the order was filled (unused).
            fill_qty: The quantity filled (signed).

        Returns:
            The commission amount, which is the greater of the per-share cost
            or the minimum commission.

        """
        commission = abs(fill_qty) * self.commission_per_share
        return max(commission, self.min_commission)
