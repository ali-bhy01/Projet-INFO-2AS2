def parse_candles(raw_candles: list, epic: str, resolution: str = "MINUTE_5") -> list[dict]:
    """
    Transforme le JSON brut de Capital.com en dicts normalisés.

    Input  : liste de candles brutes (champ "prices" de la réponse API)
    Output : liste de dicts prêts à être insérés en base
    """
    result = []
    for c in raw_candles:
        ts = c.get("snapshotTimeUTC") or c.get("snapshotTime", "")
        open_  = (c["openPrice"]["bid"]  + c["openPrice"]["ask"])  / 2
        high   = (c["highPrice"]["bid"]  + c["highPrice"]["ask"])  / 2
        low    = (c["lowPrice"]["bid"]   + c["lowPrice"]["ask"])   / 2
        close  = (c["closePrice"]["bid"] + c["closePrice"]["ask"]) / 2
        volume = c.get("lastTradedVolume", 0)

        result.append({
            "id":         f"{epic}_{ts}",
            "epic":       epic,
            "timestamp":  ts,
            "open":       open_,
            "high":       high,
            "low":        low,
            "close":      close,
            "volume":     volume,
            "resolution": resolution,
        })
    return result
