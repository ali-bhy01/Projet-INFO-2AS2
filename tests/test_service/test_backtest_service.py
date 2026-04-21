import pytest
import pandas as pd
from unittest.mock import patch
from src.utils.enumeration import Strategy
from src.service.backtest_service import run_backtest
from src.dto.backtest_dto import BacktestDTO
from src.dto.trade_dto import TradeDTO


def _make_df() -> pd.DataFrame:
    """DataFrame 5min minimal pour déclencher un trade PDH/PDL."""
    rows = []
    # Jour 1 (veille) : PDH=20100, PDL=19800 → range=300, dans [50,300]
    for h in range(9, 18):
        for m in [0, 5, 10, 15, 20, 25, 30, 35]:
            rows.append({
                "datetime": pd.Timestamp(f"2025-06-09 {h:02d}:{m:02d}"),
                "open":  20000.0, "high": 20100.0,
                "low":   19800.0, "close": 20000.0, "volume": 100,
            })
    # Jour 2 (lundi, mois ok) : le prix monte au-dessus du PDH+5=20105
    for h in range(9, 18):
        for m in [0, 5, 10, 15, 20, 25, 30, 35]:
            rows.append({
                "datetime": pd.Timestamp(f"2025-06-10 {h:02d}:{m:02d}"),
                "open":  20050.0, "high": 20200.0,
                "low":   20040.0, "close": 20180.0, "volume": 100,
            })
    df = pd.DataFrame(rows).set_index("datetime")
    df.index = pd.DatetimeIndex(df.index)
    return df


@pytest.fixture(autouse=True)
def mock_candles(monkeypatch):
    monkeypatch.setattr(
        "src.service.backtest_service.get_candles_dataframe",
        lambda **_: _make_df(),
    )


def test_run_backtest_returns_backtest_dto():
    assert isinstance(run_backtest(Strategy.PDHL), BacktestDTO)


def test_run_backtest_pdhl_has_trades():
    result = run_backtest(Strategy.PDHL)
    assert result.n_trades > 0


def test_run_backtest_trades_are_trade_dto():
    result = run_backtest(Strategy.PDHL)
    assert all(isinstance(t, TradeDTO) for t in result.trades)


def test_run_backtest_win_rate_between_0_and_1():
    result = run_backtest(Strategy.PDHL)
    assert 0 <= result.win_rate <= 1


def test_run_backtest_unknown_strategy_raises():
    with pytest.raises(NotImplementedError):
        run_backtest("UNKNOWN")
