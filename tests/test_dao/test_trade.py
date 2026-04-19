import pytest
from src.dao import trade_dao
from src.models.trade import Trade

SAMPLE = Trade(
    date="2025-06-10",
    strategy="PDHL",
    direction="long",
    entry=19500.0,
    exit=19600.0,
    stop=19400.0,
    pnl=100.0,
)


def test_insert_and_retrieve():
    trade_dao.delete_by_strategy("PDHL")
    trade_dao.insert_trade(SAMPLE)
    results = trade_dao.get_by_strategy("PDHL")
    assert len(results) == 1
    assert results[0].pnl == 100.0


def test_delete_by_strategy():
    trade_dao.insert_trade(SAMPLE)
    deleted = trade_dao.delete_by_strategy("PDHL")
    assert deleted >= 1
    assert trade_dao.get_by_strategy("PDHL") == []


def test_get_by_strategy_returns_trade_objects():
    trade_dao.delete_by_strategy("PDHL")
    trade_dao.insert_trade(SAMPLE)
    results = trade_dao.get_by_strategy("PDHL")
    assert isinstance(results[0], Trade)