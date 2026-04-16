from src.dao.db_connection import get_connection


def insert_candle(candle: dict) -> bool:
    """
    Insère une candle. Retourne True si insérée, False si doublon.
    Utilise INSERT OR IGNORE pour ignorer silencieusement les doublons.
    """
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
    """Vérifie si une candle existe déjà en base."""
    conn = get_connection()
    row = conn.execute(
        "SELECT 1 FROM price_candle WHERE epic = ? AND timestamp = ?",
        (epic, timestamp),
    ).fetchone()
    return row is not None


def get_all(epic: str) -> list[dict]:
    """Retourne toutes les candles d'un epic, triées par timestamp."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM price_candle WHERE epic = ? ORDER BY timestamp",
        (epic,),
    ).fetchall()
    return [dict(r) for r in rows]


def get_by_date_range(epic: str, from_date: str, to_date: str) -> list[dict]:
    """
    Retourne les candles entre deux dates ISO 8601 (inclusif).
    Exemple : from_date="2025-01-01", to_date="2025-12-31"
    """
    conn = get_connection()
    rows = conn.execute(
        """
        SELECT * FROM price_candle
        WHERE epic = ? AND timestamp >= ? AND timestamp <= ?
        ORDER BY timestamp
        """,
        (epic, from_date, to_date),
    ).fetchall()
    return [dict(r) for r in rows]
