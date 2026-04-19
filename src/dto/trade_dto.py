from pydantic import BaseModel


class TradeDTO(BaseModel):
    date:      str
    strategy:  str
    direction: str
    entry:     float
    exit:      float
    stop:      float
    pnl:       float
