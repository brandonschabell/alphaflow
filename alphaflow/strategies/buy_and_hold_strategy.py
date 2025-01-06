import logging

from alphaflow import Strategy
from alphaflow.enums import OrderType, Side, Topic
from alphaflow.events import MarketDataEvent, OrderEvent

logger = logging.getLogger(__name__)


class BuyAndHoldStrategy(Strategy):
    def __init__(self, symbol: str, target_weight: float) -> None:
        self.symbol = symbol
        self.target_weight = target_weight

    def topic_subscriptions(self):
        return [Topic.MARKET_DATA]

    def read_event(self, event: MarketDataEvent):
        logger.debug(f"Strategy received event: {event}")
        if (
            self._alpha_flow.backtest_start_timestamp
            and event.timestamp < self._alpha_flow.backtest_start_timestamp
        ):
            return
        if (
            self._alpha_flow.backtest_end_timestamp
            and event.timestamp > self._alpha_flow.backtest_end_timestamp
        ):
            return

        portfolio_value = self._alpha_flow.portfolio.get_portfolio_value(
            event.timestamp
        )
        position_value = self._alpha_flow.portfolio.get_position_value(
            self.symbol, event.timestamp
        )
        target_value = portfolio_value * self.target_weight
        purchase_value = target_value - position_value
        logger.debug("PURCHASE VALUE: %s", purchase_value)
        if abs(purchase_value) < 0.01:
            return
        shares_needed = purchase_value / event.close
        if shares_needed > 0:
            logger.info(
                f"Buying {shares_needed} shares of {self.symbol} at {event.close} on {event.timestamp}"
            )
            self._alpha_flow.event_bus.publish(
                Topic.ORDER,
                OrderEvent(
                    timestamp=event.timestamp,
                    symbol=self.symbol,
                    side=Side.BUY,
                    qty=shares_needed,
                    order_type=OrderType.MARKET,
                ),
            )
        else:
            logger.info(
                f"Selling {abs(shares_needed)} shares of {self.symbol} at {event.close} on {event.timestamp}"
            )
            self._alpha_flow.event_bus.publish(
                Topic.ORDER,
                OrderEvent(
                    timestamp=event.timestamp,
                    symbol=self.symbol,
                    side=Side.SELL,
                    qty=-shares_needed,
                    order_type=OrderType.MARKET,
                ),
            )
