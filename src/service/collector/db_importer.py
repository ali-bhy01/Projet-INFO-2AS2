from src.dao.candle_dao import insert_candle


def import_candles(candles: list[dict]) -> dict:
    inserted = skipped = 0
    for c in candles:
        if insert_candle(c):
            inserted += 1
        else:
            skipped += 1
    return {"inserted": inserted, "skipped": skipped, "total": inserted + skipped}
