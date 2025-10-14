"""AlphaFlow - Event-driven backtesting framework for trading strategies."""

from __future__ import annotations

import logging
from collections import defaultdict
from collections.abc import Generator
from datetime import datetime

from alphaflow.enums import Topic
from alphaflow.event_bus.event_bus import EventBus
from alphaflow.event_bus.subscriber import Subscriber
from alphaflow.events.event import Event
from alphaflow.events.fill_event import FillEvent
from alphaflow.events.market_data_event import MarketDataEvent

logger = logging.getLogger(__name__)


class Analyzer(Subscriber):
    """Defines the interface for analyzers."""

    def topic_subscriptions(self) -> list[Topic]:
        """Return the topics to subscribe to."""
        raise NotImplementedError

    def set_alpha_flow(self, alpha_flow: AlphaFlow) -> None:
        """Set the AlphaFlow instance for this analyzer.

        Args:
            alpha_flow: The AlphaFlow backtest engine instance.

        """
        self._alpha_flow = alpha_flow

    def read_event(self, event: Event) -> None:
        """Read and process the event."""
        raise NotImplementedError

    def run(self) -> None:
        """Run the analyzer."""
        raise NotImplementedError


class Broker(Subscriber):
    """Defines the interface for brokers."""

    def topic_subscriptions(self) -> list[Topic]:
        """Return the topics to subscribe to."""
        return [Topic.ORDER]

    def set_alpha_flow(self, alpha_flow: AlphaFlow) -> None:
        """Set the AlphaFlow instance for this broker.

        Args:
            alpha_flow: The AlphaFlow backtest engine instance.

        """
        self._alpha_flow = alpha_flow

    def read_event(self, event: Event) -> None:
        """Read and process the event."""
        raise NotImplementedError


class DataFeed:
    """Defines the interface for data feeds."""

    def set_alpha_flow(self, alpha_flow: AlphaFlow) -> None:
        """Set the AlphaFlow instance for this data feed.

        Args:
            alpha_flow: The AlphaFlow backtest engine instance.

        """
        self._alpha_flow = alpha_flow

    def run(
        self,
        symbol: str,
        start_timestamp: datetime | None,
        end_timestamp: datetime | None,
    ) -> Generator[MarketDataEvent, None, None]:
        """Run the data feed."""
        raise NotImplementedError


class Portfolio(Subscriber):
    """Manages portfolio state including cash, positions, and performance calculations."""

    def __init__(self, alpha_flow: AlphaFlow):
        """Initialize the portfolio.

        Args:
            alpha_flow: The AlphaFlow backtest engine instance.

        """
        self._alpha_flow = alpha_flow
        self._cash: float = 0.0
        self.positions: dict[str, float] = {}

    def topic_subscriptions(self) -> list[Topic]:
        """Return the topics to subscribe to."""
        return [Topic.FILL]

    def set_cash(self, cash: float) -> None:
        """Set the cash balance.

        Args:
            cash: The cash amount to set.

        """
        self._cash = cash

    def get_cash(self) -> float:
        """Get the current cash balance.

        Returns:
            The current cash balance.

        """
        return self._cash

    def get_position(self, symbol: str) -> float:
        """Get the current position quantity for a symbol.

        Args:
            symbol: The ticker symbol.

        Returns:
            The number of shares held (0 if no position).

        """
        return self.positions.get(symbol, 0.0)

    def update_cash(self, amount: float) -> None:
        """Update the cash balance by adding an amount.

        Args:
            amount: The amount to add (can be negative).

        """
        self._cash += amount

    def update_position(self, symbol: str, qty: float) -> None:
        """Update the position quantity for a symbol.

        Args:
            symbol: The ticker symbol.
            qty: The quantity to add (can be negative for sells).

        """
        self.positions[symbol] = self.get_position(symbol) + qty

    def get_position_value(self, symbol: str, timestamp: datetime) -> float:
        """Get the market value of a position at a specific timestamp.

        Args:
            symbol: The ticker symbol.
            timestamp: The timestamp for price lookup.

        Returns:
            The position value (shares * price).

        """
        return self.get_position(symbol) * self._alpha_flow.get_price(symbol, timestamp)

    def get_positions_value(self, timestamp: datetime) -> float:
        """Get the total market value of all positions at a specific timestamp.

        Args:
            timestamp: The timestamp for price lookup.

        Returns:
            The total value of all positions.

        """
        return sum(self.get_position_value(symbol, timestamp) for symbol in self.positions)

    def get_portfolio_value(self, timestamp: datetime) -> float:
        """Get the total portfolio value (cash + positions) at a specific timestamp.

        Args:
            timestamp: The timestamp for price lookup.

        Returns:
            The total portfolio value.

        """
        return self._cash + self.get_positions_value(timestamp)

    def get_buying_power(self, margin: float, timestamp: datetime) -> float:
        """Calculate available buying power with margin.

        Args:
            margin: The margin multiplier (e.g., 2.0 for 2x margin).
            timestamp: The timestamp for price lookup.

        Returns:
            The available buying power.

        """
        return self.get_portfolio_value(timestamp) * margin - self.get_positions_value(timestamp)

    def get_benchmark_values(self) -> dict[datetime, float]:
        """Get benchmark prices for all timestamps in the backtest.

        Returns:
            Dictionary mapping timestamps to benchmark prices.

        """
        if self._alpha_flow.benchmark is None:
            return {}
        return {
            timestamp: self._alpha_flow.get_price(self._alpha_flow.benchmark, timestamp)
            for timestamp in self._alpha_flow.get_timestamps()
        }

    def read_event(self, event: Event) -> None:
        """Read and process the event."""
        if not isinstance(event, FillEvent):
            return

        cost = event.fill_price * event.fill_qty  # Can be positive or negative
        self.update_cash(-cost - event.commission)  # Deduct commission on all trades
        self.update_position(event.symbol, event.fill_qty)


class Strategy(Subscriber):
    """Defines the interface for strategies."""

    def topic_subscriptions(self) -> list[Topic]:
        """Return the topics to subscribe to."""
        raise NotImplementedError

    def set_alpha_flow(self, alpha_flow: AlphaFlow) -> None:
        """Set the AlphaFlow instance for this strategy.

        Args:
            alpha_flow: The AlphaFlow backtest engine instance.

        """
        self._alpha_flow = alpha_flow

    def read_event(self, event: Event) -> None:
        """Read and process the event."""
        raise NotImplementedError


class AlphaFlow:
    """Event-driven backtesting engine for trading strategies."""

    def __init__(self) -> None:
        """Initialize the AlphaFlow backtest engine."""
        self.event_bus = EventBus()
        self.portfolio = Portfolio(self)
        self.strategies: list[Strategy] = []
        self.analyzers: list[Analyzer] = []
        self.universe: set[str] = set()
        self.data_feed: DataFeed | None = None
        self.broker: Broker | None = None
        self.benchmark: str | None = None
        self._data: dict[str, list[MarketDataEvent]] = defaultdict(list)
        self.data_start_timestamp: datetime | None = None
        self.backtest_start_timestamp: datetime | None = None
        self.backtest_end_timestamp: datetime | None = None
        for topic in self.portfolio.topic_subscriptions():
            self.event_bus.subscribe(topic, self.portfolio)

    def set_benchmark(self, symbol: str) -> None:
        """Set the benchmark symbol for performance comparison.

        Args:
            symbol: The ticker symbol to use as a benchmark (e.g., "SPY").

        """
        self.universe.add(symbol)
        self.benchmark = symbol

    def add_equity(self, symbol: str) -> None:
        """Add an equity symbol to the trading universe.

        Args:
            symbol: The ticker symbol to add (e.g., "AAPL").

        """
        self.universe.add(symbol)

    def set_data_feed(self, data_feed: DataFeed) -> None:
        """Set the data feed for retrieving market data.

        Args:
            data_feed: A DataFeed instance that will provide market data.

        """
        data_feed.set_alpha_flow(self)
        self.data_feed = data_feed

    def add_strategy(self, strategy: Strategy) -> None:
        """Add a trading strategy to the backtest.

        Args:
            strategy: A Strategy instance that will generate trading signals.

        """
        strategy.set_alpha_flow(self)
        for topic in strategy.topic_subscriptions():
            self.event_bus.subscribe(topic, strategy)
        self.strategies.append(strategy)

    def add_analyzer(self, analyzer: Analyzer) -> None:
        """Add an analyzer for performance metrics and visualization.

        Args:
            analyzer: An Analyzer instance for computing metrics and generating reports.

        """
        analyzer.set_alpha_flow(self)
        for topic in analyzer.topic_subscriptions():
            self.event_bus.subscribe(topic, analyzer)
        self.analyzers.append(analyzer)

    def set_broker(self, broker: Broker) -> None:
        """Set the broker for order execution simulation.

        Args:
            broker: A Broker instance that will simulate order execution.

        """
        broker.set_alpha_flow(self)
        for topic in broker.topic_subscriptions():
            self.event_bus.subscribe(topic, broker)
        self.broker = broker

    def set_cash(self, cash: float) -> None:
        """Set the initial cash balance for the portfolio.

        Args:
            cash: The initial cash amount in the portfolio currency.

        """
        self.portfolio.set_cash(cash)

    def set_data_start_timestamp(self, timestamp: datetime | str) -> None:
        """Set the start timestamp for loading data.

        Args:
            timestamp: Start datetime or ISO format string. Data will be loaded from this point.

        """
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)
        self.data_start_timestamp = timestamp

    def set_backtest_start_timestamp(self, timestamp: datetime | str) -> None:
        """Set the start timestamp for the backtest period.

        Args:
            timestamp: Start datetime or ISO format string. Strategies will begin trading from this point.

        """
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)
        self.backtest_start_timestamp = timestamp

    def set_backtest_end_timestamp(self, timestamp: datetime | str) -> None:
        """Set the end timestamp for the backtest period.

        Args:
            timestamp: End datetime or ISO format string. Backtest will stop at this point.

        """
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)
        self.backtest_end_timestamp = timestamp

    def get_timestamps(self) -> list[datetime]:
        """Return all unique timestamps from loaded market data, sorted chronologically.

        Returns:
            Sorted list of datetime objects representing all data points in the backtest.

        """
        timestamps: set[datetime] = set()
        for events in self._data.values():
            timestamps.update(event.timestamp for event in events)
        return sorted(timestamps)

    def run(self, is_backtest: bool = True) -> None:
        """Run the backtest simulation.

        Load all market data for symbols in the universe, publishes events chronologically
        through the EventBus, and runs all analyzers after completion.

        Args:
            is_backtest: Whether to run in backtest mode. Live trading not yet implemented.

        Raises:
            NotImplementedError: If is_backtest is False (live trading not supported).

        """
        if is_backtest:
            if self.data_feed is None:
                raise ValueError("Data feed must be set before running backtest")

            events: list[MarketDataEvent] = []
            for symbol in self.universe:
                events.extend(
                    list(
                        self.data_feed.run(
                            symbol,
                            self.data_start_timestamp or self.backtest_start_timestamp,
                            self.backtest_end_timestamp,
                        )
                    )
                )
            events = sorted(events)
            for event in events:
                self._data[event.symbol].append(event)
            for event in events:
                self.event_bus.publish(Topic.MARKET_DATA, event)
            for analyzer in self.analyzers:
                logger.info("Running analyzer %s", analyzer)
                analyzer.run()
        else:
            raise NotImplementedError

    def get_price(self, symbol: str, timestamp: datetime) -> float:
        """Get the closing price for a symbol at or after a specific timestamp.

        Args:
            symbol: The ticker symbol.
            timestamp: The timestamp to look up the price for.

        Returns:
            The closing price at or after the given timestamp.

        Raises:
            ValueError: If no price data exists after the timestamp.

        """
        for event in self._data[symbol]:
            if event.timestamp >= timestamp:
                return event.close
        raise ValueError(f"No price data for symbol {symbol} after timestamp {timestamp}")
