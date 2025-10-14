"""Buy-and-hold rebalancing strategy implementation."""

import logging
import math

from alphaflow import Strategy
from alphaflow.enums import OrderType, Side, Topic
from alphaflow.events import MarketDataEvent, OrderEvent

logger = logging.getLogger(__name__)


class BuyAndHoldStrategy(Strategy):
    """A buy-and-hold rebalancing strategy that maintains a target portfolio weight.

    This strategy monitors portfolio value and rebalances positions to maintain
    the target weight, with optional thresholds to avoid excessive trading.
    """

    def __init__(
        self,
        symbol: str,
        target_weight: float,
        min_dollar_delta: float = 0,
        min_share_delta: float = 0,
        share_quantization: float | None = None,
    ) -> None:
        """Initialize the buy-and-hold strategy.

        Args:
            symbol: The ticker symbol to trade.
            target_weight: Target portfolio weight (0.0 to 1.0).
            min_dollar_delta: Minimum dollar difference to trigger rebalancing.
            min_share_delta: Minimum share difference to trigger rebalancing.
            share_quantization: Round shares to multiples of this value (e.g., 1 for whole shares).

        """
        self.symbol = symbol
        self.target_weight = target_weight
        self.min_dollar_delta = min_dollar_delta
        self.min_share_delta = min_share_delta
        self.share_quantization = share_quantization

    def topic_subscriptions(self):
        """Return the topics this strategy subscribes to.

        Returns:
            List of topics this strategy listens to.

        """
        return [Topic.MARKET_DATA]

    def read_event(self, event: MarketDataEvent):
        """Process market data events and generate rebalancing orders.

        Args:
            event: The market data event containing price information.

        """
        if event.symbol != self.symbol:
            return
        if self._alpha_flow.backtest_start_timestamp and event.timestamp < self._alpha_flow.backtest_start_timestamp:
            return
        if self._alpha_flow.backtest_end_timestamp and event.timestamp > self._alpha_flow.backtest_end_timestamp:
            return

        portfolio_value = self._alpha_flow.portfolio.get_portfolio_value(event.timestamp)
        position_value = self._alpha_flow.portfolio.get_position_value(self.symbol, event.timestamp)
        target_value = portfolio_value * self.target_weight
        purchase_value = target_value - position_value
        if abs(purchase_value) < self.min_dollar_delta:
            # Too small of a value difference
            return
        shares_needed = purchase_value / event.close

        if self.share_quantization:
            shares_needed = math.floor(shares_needed / self.share_quantization) * self.share_quantization

        if abs(shares_needed) < self.min_share_delta:
            # Too small of a share purchase
            return
        side = Side.BUY if shares_needed > 0 else Side.SELL
        self._alpha_flow.event_bus.publish(
            Topic.ORDER,
            OrderEvent(
                timestamp=event.timestamp,
                symbol=self.symbol,
                side=side,
                qty=abs(shares_needed),
                order_type=OrderType.MARKET,
            ),
        )
