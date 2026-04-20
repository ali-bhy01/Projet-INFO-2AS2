from dataclasses import dataclass


@dataclass
class Trade:
    date: str
    strategy: str
    direction: str
    entry: float
    exit: float
    stop: float
    pnl: float
    id: int | None = None
