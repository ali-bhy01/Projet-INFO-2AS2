from pydantic import BaseModel
from src.dto.trade_dto import TradeDTO


class BacktestDTO(BaseModel):
    strategy:    str
    n_trades:    int
    win_rate:    float
    profit_factor: float
    total_pnl:   float
    trades:      list[TradeDTO]
