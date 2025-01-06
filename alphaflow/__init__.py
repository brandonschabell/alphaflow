from __future__ import annotations
from collections import defaultdict
from collections.abc import Generator
from datetime import datetime

from alphaflow.enums import Topic
from alphaflow.event_bus.event_bus import EventBus
from alphaflow.event_bus.subscriber import Subscriber
from alphaflow.events.event import Event
from alphaflow.events.market_data_event import MarketDataEvent


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
        self, start_timestamp: datetime | None, end_timestamp: datetime | None
    ) -> Generator[MarketDataEvent, None, None]:
        """Runs the data feed."""
        raise NotImplementedError


class Portfolio:
    def __init__(self, alpha_flow: AlphaFlow):
        self._alpha_flow = alpha_flow
        self._cash = 0
        self.positions = {}

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

    def get_portfolio_value(self, timestamp: datetime) -> float:
        position_value = sum(
            self.get_position_value(symbol, timestamp) for symbol in self.positions
        )
        return self._cash + position_value


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
        self.data_feeds: list[DataFeed] = []
        self.strategies: list[Strategy] = []
        self.broker: Broker | None = None
        self._data: dict[str, list[MarketDataEvent]] = defaultdict(list)
        self.data_start_timestamp: datetime | None = None
        self.backtest_start_timestamp: datetime | None = None
        self.backtest_end_timestamp: datetime | None = None

    def add_data_feed(self, data_feed: DataFeed):
        data_feed.set_alpha_flow(self)
        self.data_feeds.append(data_feed)

    def add_strategy(self, strategy: Strategy):
        strategy.set_alpha_flow(self)
        for topic in strategy.topic_subscriptions():
            self.event_bus.subscribe(topic, strategy)
        self.strategies.append(strategy)

    def set_broker(self, broker: Broker):
        broker.set_alpha_flow(self)
        for topic in broker.topic_subscriptions():
            self.event_bus.subscribe(topic, broker)
        self.broker = broker

    def set_cash(self, cash: float):
        self.portfolio.set_cash(cash)

    def set_data_start_timestamp(self, timestamp: datetime):
        self.data_start_timestamp = timestamp

    def set_backtest_start_timestamp(self, timestamp: datetime):
        self.backtest_start_timestamp = timestamp

    def set_backtest_end_timestamp(self, timestamp: datetime):
        self.backtest_end_timestamp = timestamp

    def get_timestamps(self) -> list[datetime]:
        timestamps = set()
        for events in self._data.values():
            timestamps.update(event.timestamp for event in events)
        return sorted(timestamps)

    def run(self, is_backtest: bool = True):
        if is_backtest:
            events: list[MarketDataEvent] = []
            for data_feed in self.data_feeds:
                events.extend(
                    list(
                        data_feed.run(
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
        else:
            raise NotImplementedError

    def get_price(self, symbol: str, timestamp: datetime) -> float:
        for event in self._data[symbol]:
            if event.timestamp >= timestamp:
                return event.close
        raise ValueError(
            f"No price data for symbol {symbol} after timestamp {timestamp}"
        )
