"""Fixed slippage model for AlphaFlow."""

from alphaflow import AlphaFlow, SlippageModel
from alphaflow.enums import Side
from alphaflow.events import OrderEvent


class FixedSlippageModel(SlippageModel):
    """Fixed slippage model using basis points.

    Applies a constant percentage slippage to all orders based on the order side.
    This simulates a basic bid-ask spread where:
    - Buy orders pay a higher price (the "ask")
    - Sell orders receive a lower price (the "bid")

    Example:
        With slippage_bps=5.0 (5 basis points = 0.05%):
        - If market price is $100.00:
          - Buy order fills at $100.05 (pays 0.05% more)
          - Sell order fills at $99.95 (receives 0.05% less)

    """

    def __init__(self, slippage_bps: float) -> None:
        """Initialize the fixed slippage model.

        Args:
            slippage_bps: Slippage in basis points (e.g., 5.0 for 0.05% slippage).
                         Must be non-negative.

        Raises:
            ValueError: If slippage_bps is negative.

        """
        if slippage_bps < 0:
            raise ValueError(f"slippage_bps must be non-negative, got {slippage_bps}")
        self.slippage_bps = slippage_bps

    def calculate_slippage(
        self,
        order_event: OrderEvent,
        market_price: float,
        alpha_flow: AlphaFlow,
    ) -> float:
        """Calculate the slipped fill price.

        Args:
            order_event: The order being executed.
            market_price: The market price at execution time.
            alpha_flow: The AlphaFlow instance (unused in this model).

        Returns:
            The fill price after applying slippage.

        """
        slippage_multiplier = 1 + (self.slippage_bps / 10000)

        if order_event.side is Side.BUY:
            # Buys pay more (slippage is adverse)
            return market_price * slippage_multiplier
        else:
            # Sells receive less (slippage is adverse)
            return market_price / slippage_multiplier
