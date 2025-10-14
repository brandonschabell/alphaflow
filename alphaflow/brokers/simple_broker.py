"""Simple broker implementation with margin support."""

import logging
from datetime import datetime

from alphaflow import Broker
from alphaflow.enums import Side, Topic
from alphaflow.events import FillEvent, OrderEvent
from alphaflow.events.event import Event

logger = logging.getLogger(__name__)


class SimpleBroker(Broker):
    """A simple broker that executes orders.

    Note: This broker does not allow for short selling.
    """

    def __init__(self, margin: float = 2.0) -> None:
        """Initialize the broker.

        Args:
            margin: The allowed margin for trading. If the margin is 1.0, then the broker does not allow for margin trading.

        """
        self.margin = margin

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
        price = self._get_price(event.symbol, event.timestamp)

        if event.side is Side.BUY:
            return self._alpha_flow.portfolio.get_buying_power(self.margin, event.timestamp) >= event.qty * price
        else:
            return self._alpha_flow.portfolio.get_position(event.symbol) >= event.qty

    def _execute_order(self, event: OrderEvent) -> FillEvent:
        price = self._get_price(event.symbol, event.timestamp)

        quantity = event.qty if event.side is Side.BUY else -event.qty

        return FillEvent(
            timestamp=event.timestamp,
            symbol=event.symbol,
            fill_price=price,
            fill_qty=quantity,
            commission=0,
        )
