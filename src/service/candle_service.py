import pandas as pd
from src.dao import candle_dao

EPIC = "DE40"


def get_candles_dataframe(
    epic: str = EPIC, from_date=None, to_date=None,
    start_time: str = "09:00", end_time: str = "17:35",
) -> pd.DataFrame:
    if from_date and to_date:
        candles = candle_dao.get_by_date_range(epic, from_date, to_date)
    else:
        candles = candle_dao.get_all(epic)

    if not candles:
        df = pd.DataFrame(columns=["open", "high", "low", "close", "volume"])
        df.index = pd.DatetimeIndex([])
        return df

    rows = [
        {
            "datetime": c.timestamp,
            "open": c.open,
            "high": c.high,
            "low": c.low,
            "close": c.close,
            "volume": c.volume,
        }
        for c in candles
    ]
    df = pd.DataFrame(rows)
    df["datetime"] = (
        pd.to_datetime(df["datetime"], utc=True)
        .dt.tz_convert("Europe/Berlin")
        .dt.tz_localize(None)
    )
    df = df.set_index("datetime").sort_index()
    df = df[~df.index.duplicated(keep="first")]
    return df.between_time(start_time, end_time)
