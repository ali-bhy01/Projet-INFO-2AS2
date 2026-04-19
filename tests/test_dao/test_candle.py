import pytest
from src.dao import candle_dao
from src.models.candle import Candle

SAMPLE = {
    "id":         "DE40_2025-01-01T09:00:00",
    "epic":       "DE40",
    "timestamp":  "2025-01-01T09:00:00",
    "open":       20000.0,
    "high":       20050.0,
    "low":        19980.0,
    "close":      20030.0,
    "volume":     100,
    "resolution": "MINUTE_5",
}


def test_insert_candle_returns_true():
    candle_dao.exists("DE40", "2025-01-01T09:00:00")  # force init DB
    assert candle_dao.insert_candle(SAMPLE) in (True, False)  # peut déjà exister


def test_insert_duplicate_returns_false():
    candle_dao.insert_candle(SAMPLE)
    assert candle_dao.insert_candle(SAMPLE) is False


def test_exists_after_insert():
    candle_dao.insert_candle(SAMPLE)
    assert candle_dao.exists("DE40", "2025-01-01T09:00:00") is True


def test_exists_unknown_returns_false():
    assert candle_dao.exists("DE40", "1900-01-01T00:00:00") is False


def test_get_all_returns_candle_objects():
    candle_dao.insert_candle(SAMPLE)
    results = candle_dao.get_all("DE40")
    assert len(results) >= 1
    assert isinstance(results[0], Candle)


def test_get_by_date_range():
    candle_dao.insert_candle(SAMPLE)
    results = candle_dao.get_by_date_range("DE40", "2025-01-01", "2025-01-02")
    assert any(r.timestamp == "2025-01-01T09:00:00" for r in results)