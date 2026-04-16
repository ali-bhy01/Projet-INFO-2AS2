from src.dao.price_candle_dao import insert_candle


def import_candles(candles: list[dict]) -> dict:
    """
    Insère les candles en base SQLite sans doublons.

    Returns:
        {"inserted": 847, "skipped": 153, "total": 1000}
    """
    inserted = 0
    skipped  = 0

    for candle in candles:
        if insert_candle(candle):
            inserted += 1
        else:
            skipped += 1

    return {"inserted": inserted, "skipped": skipped, "total": len(candles)}
