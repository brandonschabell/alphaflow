"""Order event representing a trading order."""

from dataclasses import dataclass
from datetime import datetime

from alphaflow.enums import OrderType, Side
from alphaflow.events.event import Event


@dataclass(frozen=True)
class OrderEvent(Event):
    """Represents an order event."""

    #: The timestamp of the order.
    timestamp: datetime

    #: The symbol of the order.
    symbol: str

    #: The side of the order.
    side: Side

    #: The quantity of the order.
    qty: float

    #: The order type of the order.
    order_type: OrderType

    #: The limit price of the order, if applicable.
    limit_price: float | None = None
