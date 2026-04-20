import pytest
from src.service.collector.db_importer import import_candles

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


def _make(n: int) -> dict:
    ts = f"2025-01-01T09:{n:02d}:00"
    return {**SAMPLE, "id": f"DE40_{ts}", "timestamp": ts}


def test_import_empty_list():
    assert import_candles([]) == {"inserted": 0, "skipped": 0, "total": 0}


def test_import_single():
    result = import_candles([SAMPLE])
    assert result["inserted"] == 1
    assert result["skipped"] == 0
    assert result["total"] == 1


def test_import_duplicate_skipped():
    import_candles([SAMPLE])
    result = import_candles([SAMPLE])
    assert result["inserted"] == 0
    assert result["skipped"] == 1
    assert result["total"] == 1


def test_import_multiple_unique():
    candles = [_make(i) for i in range(5)]
    result = import_candles(candles)
    assert result["inserted"] == 5
    assert result["skipped"] == 0
    assert result["total"] == 5


def test_import_mixed_new_and_duplicate():
    import_candles([_make(0)])
    result = import_candles([_make(0), _make(1)])
    assert result["inserted"] == 1
    assert result["skipped"] == 1
    assert result["total"] == 2


def test_total_equals_inserted_plus_skipped():
    candles = [_make(i) for i in range(3)]
    import_candles(candles[:2])
    result = import_candles(candles)
    assert result["total"] == result["inserted"] + result["skipped"]
