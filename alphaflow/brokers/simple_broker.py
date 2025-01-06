from datetime import datetime
import logging

from alphaflow import Broker
from alphaflow.enums import Side, Topic
from alphaflow.events import FillEvent, OrderEvent

logger = logging.getLogger(__name__)


class SimpleBroker(Broker):
    """A simple broker that executes orders.

    Note: This broker does not allow for short selling or margin trading.
    """

    def read_event(self, event: OrderEvent) -> None:
        """Reads the event."""
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
        cash = self._get_cash()
        price = self._get_price(event.symbol, event.timestamp)

        if event.side is Side.BUY:
            return cash >= event.qty * price
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
