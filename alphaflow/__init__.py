from __future__ import annotations
from collections import defaultdict
from collections.abc import Generator
from datetime import datetime
import logging

from alphaflow.enums import Topic
from alphaflow.event_bus.event_bus import EventBus
from alphaflow.event_bus.subscriber import Subscriber
from alphaflow.events.event import Event
from alphaflow.events.market_data_event import MarketDataEvent

logger = logging.getLogger(__name__)


class Analyzer(Subscriber):
    """Defines the interface for analyzers."""

    def topic_subscriptions(self) -> list[Topic]:
        """Returns the topics to subscribe to."""
        raise NotImplementedError

    def set_alpha_flow(self, alpha_flow: AlphaFlow) -> None:
        self._alpha_flow = alpha_flow

    def read_event(self, event: Event) -> None:
        """Reads the event."""
        raise NotImplementedError

    def run(self) -> None:
        """Runs the analyzer."""
        raise NotImplementedError


class Broker(Subscriber):
    """Defines the interface for brokers."""

    def topic_subscriptions(self) -> list[Topic]:
        """Returns the topics to subscribe to."""
        return [Topic.ORDER]

    def set_alpha_flow(self, alpha_flow: AlphaFlow) -> None:
        self._alpha_flow = alpha_flow

    def read_event(self, event: Event) -> None:
        """Reads the event."""
        raise NotImplementedError


class DataFeed:
    """Defines the interface for data feeds."""

    def set_alpha_flow(self, alpha_flow: AlphaFlow) -> None:
        self._alpha_flow = alpha_flow

    def run(
        self,
        symbol: str,
        start_timestamp: datetime | None,
        end_timestamp: datetime | None,
    ) -> Generator[MarketDataEvent, None, None]:
        """Runs the data feed."""
        raise NotImplementedError


class Portfolio(Subscriber):
    def __init__(self, alpha_flow: AlphaFlow):
        self._alpha_flow = alpha_flow
        self._cash = 0
        self.positions = {}

    def topic_subscriptions(self) -> list[Topic]:
        """Returns the topics to subscribe to."""
        return [Topic.FILL]

    def set_cash(self, cash: float):
        self._cash = cash

    def get_cash(self) -> float:
        return self._cash

    def get_position(self, symbol: str) -> float:
        return self.positions.get(symbol, 0)

    def update_cash(self, amount: float) -> None:
        self._cash += amount

    def update_position(self, symbol: str, qty: float) -> None:
        self.positions[symbol] = self.get_position(symbol) + qty

    def get_position_value(self, symbol: str, timestamp: datetime) -> float:
        return self.get_position(symbol) * self._alpha_flow.get_price(symbol, timestamp)

    def get_positions_value(self, timestamp: datetime) -> float:
        return sum(
            self.get_position_value(symbol, timestamp) for symbol in self.positions
        )

    def get_portfolio_value(self, timestamp: datetime) -> float:
        return self._cash + self.get_positions_value(timestamp)

    def get_buying_power(self, margin: float, timestamp: datetime) -> float:
        return self.get_portfolio_value(timestamp) * margin - self.get_positions_value(
            timestamp
        )

    def get_benchmark_values(self) -> dict[datetime, float]:
        if self._alpha_flow.benchmark is None:
            return {}
        return {
            timestamp: self._alpha_flow.get_price(self._alpha_flow.benchmark, timestamp)
            for timestamp in self._alpha_flow.get_timestamps()
        }

    def read_event(self, event: Event) -> None:
        """Reads the event."""

        cost = event.fill_price * event.fill_qty  # Can be positive or negative
        self.update_cash(-cost)
        self.update_position(event.symbol, event.fill_qty)


class Strategy(Subscriber):
    """Defines the interface for strategies."""

    def topic_subscriptions(self) -> list[Topic]:
        """Returns the topics to subscribe to."""
        raise NotImplementedError

    def set_alpha_flow(self, alpha_flow: AlphaFlow) -> None:
        self._alpha_flow = alpha_flow

    def read_event(self, event: Event) -> None:
        """Reads the event."""
        raise NotImplementedError


class AlphaFlow:
    def __init__(self):
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

    def set_benchmark(self, symbol: str):
        self.universe.add(symbol)
        self.benchmark = symbol

    def add_equity(self, symbol: str):
        self.universe.add(symbol)

    def set_data_feed(self, data_feed: DataFeed):
        data_feed.set_alpha_flow(self)
        self.data_feed = data_feed

    def add_strategy(self, strategy: Strategy):
        strategy.set_alpha_flow(self)
        for topic in strategy.topic_subscriptions():
            self.event_bus.subscribe(topic, strategy)
        self.strategies.append(strategy)

    def add_analyzer(self, analyzer: Analyzer):
        analyzer.set_alpha_flow(self)
        for topic in analyzer.topic_subscriptions():
            self.event_bus.subscribe(topic, analyzer)
        self.analyzers.append(analyzer)

    def set_broker(self, broker: Broker):
        broker.set_alpha_flow(self)
        for topic in broker.topic_subscriptions():
            self.event_bus.subscribe(topic, broker)
        self.broker = broker

    def set_cash(self, cash: float):
        self.portfolio.set_cash(cash)

    def set_data_start_timestamp(self, timestamp: datetime | str):
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)
        self.data_start_timestamp = timestamp

    def set_backtest_start_timestamp(self, timestamp: datetime | str):
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)
        self.backtest_start_timestamp = timestamp

    def set_backtest_end_timestamp(self, timestamp: datetime | str):
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)
        self.backtest_end_timestamp = timestamp

    def get_timestamps(self) -> list[datetime]:
        timestamps = set()
        for events in self._data.values():
            timestamps.update(event.timestamp for event in events)
        return sorted(timestamps)

    def run(self, is_backtest: bool = True):
        if is_backtest:
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
        for event in self._data[symbol]:
            if event.timestamp >= timestamp:
                return event.close
        raise ValueError(
            f"No price data for symbol {symbol} after timestamp {timestamp}"
        )
