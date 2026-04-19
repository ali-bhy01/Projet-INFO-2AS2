import pytest
from src.utils.enumeration import Strategy
from src.service.backtest_service import run_backtest
from src.dto.backtest_dto import BacktestDTO
from src.dto.trade_dto import TradeDTO


def test_run_backtest_returns_backtest_dto():
    result = run_backtest(Strategy.PDHL)
    assert isinstance(result, BacktestDTO)


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