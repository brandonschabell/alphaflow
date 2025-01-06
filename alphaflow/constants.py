from enum import Enum, auto


class Topic(Enum):
    MARKET_DATA = auto()
    EARNINGS = auto()
    NEWS = auto()
    ORDER = auto()
    FILL = auto()
    PORTFOLIO_UPDATE = auto()
