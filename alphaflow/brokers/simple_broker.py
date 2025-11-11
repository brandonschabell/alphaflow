"""Simple broker implementation with margin support."""

import logging
from datetime import datetime

from alphaflow import Broker, CommissionModel, SlippageModel
from alphaflow.enums import Side, Topic
from alphaflow.events import FillEvent, OrderEvent
from alphaflow.events.event import Event

logger = logging.getLogger(__name__)


class SimpleBroker(Broker):
    """A simple broker that executes orders with configurable slippage and commissions.

    This broker simulates order execution with realistic transaction costs. Both slippage
    and commission models are optional - if not provided, orders fill at exact market prices
    with zero commission (backward compatible behavior).

    Note: This broker does not allow for short selling.

    Example:
        # Zero-cost trading (backward compatible)
        broker = SimpleBroker(margin=2.0)

        # With slippage and commissions
        from alphaflow.slippage_models import FixedSlippageModel
        from alphaflow.commission_models import PerShareCommissionModel

        broker = SimpleBroker(
            margin=2.0,
            slippage_model=FixedSlippageModel(slippage_bps=5.0),
            commission_model=PerShareCommissionModel(
                commission_per_share=0.005,
                min_commission=1.0
            ),
        )

    """

    def __init__(
        self,
        margin: float = 2.0,
        slippage_model: SlippageModel | None = None,
        commission_model: CommissionModel | None = None,
    ) -> None:
        """Initialize the broker.

        Args:
            margin: The allowed margin for trading. If 1.0, no margin trading is allowed.
            slippage_model: Optional slippage model for realistic fill prices.
                          If None, orders fill at exact market price.
            commission_model: Optional commission model for trading costs.
                            If None, no commission is charged.

        """
        self.margin = margin
        self.slippage_model = slippage_model
        self.commission_model = commission_model

    def read_event(self, event: Event) -> None:
        """Read and process the event."""
        # Type narrowing - we only get OrderEvent from Topic.ORDER
        if not isinstance(event, OrderEvent):
            return

        if self._can_execute_order(event):
            fill_event = self._execute_order(event)
            self._alpha_flow.event_bus.publish(Topic.FILL, fill_event)
        else:
            logger.warning("Order cannot be executed.")

    def _get_cash(self) -> float:
        return self._alpha_flow.portfolio.get_cash()

    def _get_price(self, symbol: str, timestamp: datetime) -> float:
        return self._alpha_flow.get_price(symbol, timestamp)

    def _can_execute_order(self, event: OrderEvent) -> bool:
        """Check if order can be executed given available buying power or position.

        For buy orders, validates against the post-slippage fill price and expected
        commission to ensure realistic execution simulation.

        """
        if event.side is Side.SELL:
            # For sells, only check position size
            return self._alpha_flow.portfolio.get_position(event.symbol) >= event.qty

        # For buys, calculate total cost including slippage and commission
        market_price = self._get_price(event.symbol, event.timestamp)

        # Calculate expected fill price (with slippage if model provided)
        if self.slippage_model is not None:
            fill_price = self.slippage_model.calculate_slippage(event, market_price, self._alpha_flow)
        else:
            fill_price = market_price

        # Calculate expected commission
        fill_qty = event.qty  # Positive for buys
        if self.commission_model is not None:
            expected_commission = self.commission_model.calculate_commission(event, fill_price, fill_qty)
        else:
            expected_commission = 0.0

        # Total cost = fill_price * qty + commission
        total_cost = event.qty * fill_price + expected_commission

        return self._alpha_flow.portfolio.get_buying_power(self.margin, event.timestamp) >= total_cost

    def _execute_order(self, event: OrderEvent) -> FillEvent:
        """Execute the order and return a fill event with slippage and commission applied."""
        market_price = self._get_price(event.symbol, event.timestamp)

        # Apply slippage if model provided
        if self.slippage_model is not None:
            fill_price = self.slippage_model.calculate_slippage(event, market_price, self._alpha_flow)
        else:
            fill_price = market_price

        # Determine fill quantity (signed: positive for buys, negative for sells)
        fill_qty = event.qty if event.side is Side.BUY else -event.qty

        # Calculate commission if model provided
        if self.commission_model is not None:
            commission = self.commission_model.calculate_commission(event, fill_price, fill_qty)
        else:
            commission = 0.0

        return FillEvent(
            timestamp=event.timestamp,
            symbol=event.symbol,
            fill_price=fill_price,
            fill_qty=fill_qty,
            commission=commission,
        )
