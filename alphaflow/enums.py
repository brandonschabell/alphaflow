from enum import Enum, auto


class OrderType(Enum):
    """Represents the type of order."""

    #: A market order.
    MARKET = auto()

    #: A limit order.
    LIMIT = auto()


class Side(Enum):
    """Represents the side of an order."""

    #: A buy order.
    BUY = auto()

    #: A sell order.
    SELL = auto()


class Topic(Enum):
    """Represents a topic for an event."""

    #: Market data topic.
    MARKET_DATA = auto()

    #: Order topic.
    ORDER = auto()

    #: Fill topic.
    FILL = auto()
