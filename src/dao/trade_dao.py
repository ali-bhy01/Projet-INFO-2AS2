from src.dao.db_connection import get_connection
from src.models.trade import Trade


def _ensure_table() -> None:
    conn = get_connection()
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


_ensure_table()


def insert_trade(trade: Trade) -> None:
    conn = get_connection()
    conn.execute(
        "INSERT INTO trade (date, strategy, direction, entry, exit, stop, pnl) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (trade.date, trade.strategy, trade.direction, trade.entry, trade.exit, trade.stop, trade.pnl),
    )
    conn.commit()


def get_by_strategy(strategy: str) -> list[Trade]:
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM trade WHERE strategy = ? ORDER BY date",
        (strategy,),
    ).fetchall()
    return [
        Trade(
            id=r["id"],
            date=r["date"],
            strategy=r["strategy"],
            direction=r["direction"],
            entry=r["entry"],
            exit=r["exit"],
            stop=r["stop"],
            pnl=r["pnl"],
        )
        for r in rows
    ]


def delete_by_strategy(strategy: str) -> int:
    conn = get_connection()
    cursor = conn.execute("DELETE FROM trade WHERE strategy = ?", (strategy,))
    conn.commit()
    return cursor.rowcount
