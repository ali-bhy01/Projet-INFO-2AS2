from dataclasses import dataclass


@dataclass
class Signal:
    date:      str
    epic:      str
    strategy:  str
    direction: str
    level:     float
    stop:      float
