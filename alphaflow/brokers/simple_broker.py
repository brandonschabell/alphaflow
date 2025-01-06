from datetime import datetime
import logging

from alphaflow import Broker
from alphaflow.enums import Side
from alphaflow.events.order_event import OrderEvent

logger = logging.getLogger(__name__)


class SimpleBroker(Broker):
    """A simple broker that executes orders.

    Note: This broker does not allow for short selling or margin trading.
    """

    def read_event(self, event: OrderEvent) -> None:
        """Reads the event."""
        logger.info(f"Broker received event: {event}")
        if self._can_execute_order(event):
            self._execute_order(event)
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

    def _execute_order(self, event: OrderEvent) -> None:
        price = self._get_price(event.symbol, event.timestamp)
        cost = event.qty * price

        if event.side is Side.BUY:
            self._alpha_flow.portfolio.update_cash(-cost)
            self._alpha_flow.portfolio.update_position(event.symbol, event.qty)
        else:
            self._alpha_flow.portfolio.update_cash(cost)
            self._alpha_flow.portfolio.update_position(event.symbol, -event.qty)

        logger.info(f"Order executed: {event}")
        logger.info(f"Portfolio cash: {self._get_cash()}")
        logger.info(f"Portfolio positions: {self._alpha_flow.portfolio.positions}")
