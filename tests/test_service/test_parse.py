import pytest
from src.service.collector.parse import parse_candles

RAW = {
    "snapshotTimeUTC": "2025-01-02T09:15:00",
    "openPrice":  {"bid": 19998.0, "ask": 20002.0},
    "highPrice":  {"bid": 20048.0, "ask": 20052.0},
    "lowPrice":   {"bid": 19978.0, "ask": 19982.0},
    "closePrice": {"bid": 20028.0, "ask": 20032.0},
    "lastTradedVolume": 150,
}


def test_parse_returns_list():
    assert isinstance(parse_candles([RAW], "DE40"), list)


def test_parse_length():
    assert len(parse_candles([RAW], "DE40")) == 1


def test_parse_empty_list():
    assert parse_candles([], "DE40") == []


def test_parse_multiple():
    assert len(parse_candles([RAW, RAW], "DE40")) == 2


def test_parse_mid_open():
    c = parse_candles([RAW], "DE40")[0]
    assert c["open"] == (19998.0 + 20002.0) / 2


def test_parse_mid_high():
    c = parse_candles([RAW], "DE40")[0]
    assert c["high"] == (20048.0 + 20052.0) / 2


def test_parse_mid_low():
    c = parse_candles([RAW], "DE40")[0]
    assert c["low"] == (19978.0 + 19982.0) / 2


def test_parse_mid_close():
    c = parse_candles([RAW], "DE40")[0]
    assert c["close"] == (20028.0 + 20032.0) / 2


def test_parse_id_format():
    c = parse_candles([RAW], "DE40")[0]
    assert c["id"] == "DE40_2025-01-02T09:15:00"


def test_parse_epic():
    c = parse_candles([RAW], "UK100")[0]
    assert c["epic"] == "UK100"


def test_parse_resolution_default():
    c = parse_candles([RAW], "DE40")[0]
    assert c["resolution"] == "MINUTE_5"


def test_parse_resolution_custom():
    c = parse_candles([RAW], "DE40", "HOUR")[0]
    assert c["resolution"] == "HOUR"


def test_parse_volume():
    c = parse_candles([RAW], "DE40")[0]
    assert c["volume"] == 150


def test_parse_volume_missing_defaults_to_zero():
    raw = {k: v for k, v in RAW.items() if k != "lastTradedVolume"}
    c = parse_candles([raw], "DE40")[0]
    assert c["volume"] == 0


def test_parse_snapshot_time_fallback():
    raw = {k: v for k, v in RAW.items() if k != "snapshotTimeUTC"}
    raw["snapshotTime"] = "2025-01-02T09:15:00"
    c = parse_candles([raw], "DE40")[0]
    assert c["timestamp"] == "2025-01-02T09:15:00"


def test_parse_required_keys():
    c = parse_candles([RAW], "DE40")[0]
    for key in ("id", "epic", "timestamp", "open", "high", "low", "close", "volume", "resolution"):
        assert key in c
