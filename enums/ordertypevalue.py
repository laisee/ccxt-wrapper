from enum import Enum


class OrderTypeValues(str, Enum):
    LIMIT = "limit"
    MARKET = "market"


class OrderSideValues(str, Enum):
    BUY = "Buy"
    SELL = "Sell"
