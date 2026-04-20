import pytest
from src.dao import trade_dao
from src.models.trade import Trade


def make_sample(**kwargs) -> Trade:
    defaults = dict(
        date="2025-06-10",
        strategy="PDHL",
        direction="long",
        entry=19500.0,
        exit=19600.0,
        stop=19400.0,
        pnl=100.0,
    )
    return Trade(**{**defaults, **kwargs})


def test_insert_and_retrieve():
    trade_dao.insert_trade(make_sample())
    results = trade_dao.get_by_strategy("PDHL")
    assert len(results) == 1
    assert results[0].pnl == 100.0


def test_delete_by_strategy():
    trade_dao.insert_trade(make_sample())
    deleted = trade_dao.delete_by_strategy("PDHL")
    assert deleted == 1
    assert trade_dao.get_by_strategy("PDHL") == []


def test_get_by_strategy_returns_trade_objects():
    trade_dao.insert_trade(make_sample())
    results = trade_dao.get_by_strategy("PDHL")
    assert isinstance(results[0], Trade)


def test_get_by_strategy_empty():
    assert trade_dao.get_by_strategy("UNKNOWN") == []


def test_multiple_inserts():
    trade_dao.insert_trade(make_sample())
    trade_dao.insert_trade(make_sample())
    results = trade_dao.get_by_strategy("PDHL")
    assert len(results) == 2


def test_delete_only_target_strategy():
    trade_dao.insert_trade(make_sample(strategy="PDHL"))
    trade_dao.insert_trade(make_sample(strategy="ASRS"))
    trade_dao.delete_by_strategy("PDHL")
    assert trade_dao.get_by_strategy("PDHL") == []
    assert len(trade_dao.get_by_strategy("ASRS")) == 1


def test_trade_fields_preserved():
    trade_dao.insert_trade(make_sample())
    t = trade_dao.get_by_strategy("PDHL")[0]
    assert t.date == "2025-06-10"
    assert t.direction == "long"
    assert t.entry == 19500.0
    assert t.stop == 19400.0


def test_delete_returns_zero_when_empty():
    assert trade_dao.delete_by_strategy("MISSING") == 0
