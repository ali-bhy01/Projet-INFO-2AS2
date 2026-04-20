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
    assert candle_dao.insert_candle(SAMPLE) is True


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
    assert len(results) == 1
    assert isinstance(results[0], Candle)


def test_get_all_empty_for_unknown_epic():
    assert candle_dao.get_all("UNKNOWN") == []


def test_candle_fields():
    candle_dao.insert_candle(SAMPLE)
    c = candle_dao.get_all("DE40")[0]
    assert c.epic == "DE40"
    assert c.open == 20000.0
    assert c.high == 20050.0
    assert c.low == 19980.0
    assert c.close == 20030.0
    assert c.volume == 100
    assert c.resolution == "MINUTE_5"


def test_get_by_date_range_returns_candle_objects():
    candle_dao.insert_candle(SAMPLE)
    results = candle_dao.get_by_date_range("DE40", "2025-01-01", "2025-01-02")
    assert len(results) == 1
    assert isinstance(results[0], Candle)
    assert results[0].timestamp == "2025-01-01T09:00:00"


def test_get_by_date_range_out_of_range():
    candle_dao.insert_candle(SAMPLE)
    results = candle_dao.get_by_date_range("DE40", "2024-01-01", "2024-12-31")
    assert results == []


def test_get_all_ordered_by_timestamp():
    earlier = {**SAMPLE, "id": "DE40_A", "timestamp": "2025-01-01T09:00:00"}
    later   = {**SAMPLE, "id": "DE40_B", "timestamp": "2025-01-01T09:05:00"}
    candle_dao.insert_candle(later)
    candle_dao.insert_candle(earlier)
    results = candle_dao.get_all("DE40")
    assert results[0].timestamp < results[1].timestamp
