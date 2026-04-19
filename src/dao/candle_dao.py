from src.dao.db_connection import get_connection
from src.models.candle import Candle


def _row_to_candle(row: dict) -> Candle:
    return Candle(**row)


def insert_candle(candle: dict) -> bool:
    conn = get_connection()
    cursor = conn.execute(
        """
        INSERT OR IGNORE INTO price_candle
            (id, epic, timestamp, open, high, low, close, volume, resolution)
        VALUES
            (:id, :epic, :timestamp, :open, :high, :low, :close, :volume, :resolution)
        """,
        candle,
    )
    conn.commit()
    return cursor.rowcount == 1


def exists(epic: str, timestamp: str) -> bool:
    conn = get_connection()
    row = conn.execute(
        "SELECT 1 FROM price_candle WHERE epic = ? AND timestamp = ?",
        (epic, timestamp),
    ).fetchone()
    return row is not None


def get_all(epic: str) -> list[Candle]:
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM price_candle WHERE epic = ? ORDER BY timestamp",
        (epic,),
    ).fetchall()
    return [_row_to_candle(dict(r)) for r in rows]


def get_by_date_range(epic: str, from_date: str, to_date: str) -> list[Candle]:
    conn = get_connection()
    rows = conn.execute(
        """
        SELECT * FROM price_candle
        WHERE epic = ? AND timestamp >= ? AND timestamp <= ?
        ORDER BY timestamp
        """,
        (epic, from_date, to_date),
    ).fetchall()
    return [_row_to_candle(dict(r)) for r in rows]
