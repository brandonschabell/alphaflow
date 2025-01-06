from dataclasses import dataclass
from datetime import datetime

from alphaflow.events.event import Event


@dataclass(frozen=True)
class FillEvent(Event):
    """Represents a fill event."""

    #: The timestamp of the fill.
    timestamp: datetime

    #: The symbol of the fill.
    symbol: str

    #: The side of the fill.
    fill_price: float

    #: The quantity of the fill.
    fill_qty: float

    #: The commission of the fill.
    commission: float
