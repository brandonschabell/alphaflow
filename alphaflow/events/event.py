from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class Event:
    """Base class for events."""

    #: The timestamp of the fill.
    timestamp: datetime
