from typing import Optional, TypedDict


class Ticker(TypedDict):
    symbol: str
    average: Optional[float]
