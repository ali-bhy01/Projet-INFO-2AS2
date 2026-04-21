import sqlite3
from pathlib import Path

_DB_PATH = Path(__file__).resolve().parents[2] / "src" / "database" / "trading.db"
_connection: sqlite3.Connection | None = None


def get_connection() -> sqlite3.Connection:
    """Retourne la connexion SQLite (Singleton). La crée si elle n'existe pas."""
    global _connection
    if _connection is None:
        _DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        _connection = sqlite3.connect(_DB_PATH, check_same_thread=False)
        _connection.row_factory = sqlite3.Row
        _init_schema(_connection)
    return _connection


def _init_schema(conn: sqlite3.Connection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS price_candle (
            id         TEXT PRIMARY KEY,
            epic       TEXT NOT NULL,
            timestamp  TEXT NOT NULL,
            open       REAL NOT NULL,
            high       REAL NOT NULL,
            low        REAL NOT NULL,
            close      REAL NOT NULL,
            volume     INTEGER NOT NULL,
            resolution TEXT NOT NULL,
            UNIQUE(epic, timestamp)
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_epic_ts ON price_candle(epic, timestamp)")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS trade (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            date      TEXT NOT NULL,
            strategy  TEXT NOT NULL,
            direction TEXT NOT NULL,
            entry     REAL NOT NULL,
            exit      REAL NOT NULL,
            stop      REAL NOT NULL,
            pnl       REAL NOT NULL
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_trade_strategy ON trade(strategy)")
    conn.commit()
