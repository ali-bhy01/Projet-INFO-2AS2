def parse_candles(prices: list, epic: str, resolution: str = "MINUTE_5") -> list[dict]:
    rows = []
    for p in prices:
        ts = p.get("snapshotTimeUTC") or p.get("snapshotTime", "")
        rows.append({
            "id":         f"{epic}_{ts}",
            "epic":       epic,
            "timestamp":  ts,
            "open":       (p["openPrice"]["bid"]  + p["openPrice"]["ask"])  / 2,
            "high":       (p["highPrice"]["bid"]  + p["highPrice"]["ask"])  / 2,
            "low":        (p["lowPrice"]["bid"]   + p["lowPrice"]["ask"])   / 2,
            "close":      (p["closePrice"]["bid"] + p["closePrice"]["ask"]) / 2,
            "volume":     p.get("lastTradedVolume", 0),
            "resolution": resolution,
        })
    return rows
