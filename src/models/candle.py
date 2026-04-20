from dataclasses import dataclass


@dataclass
class Candle:
    id: str
    epic: str
    timestamp: str
    open: float
    high: float
    low: float
    close: float
    volume: int
    resolution: str
