import os
from datetime import datetime, timezone

from dotenv import load_dotenv

from src.service.collector.session_manager import SessionManager
from src.service.collector.api_client import CapitalClient
from src.service.collector.parse import parse_candles
from src.service.collector.db_importer import import_candles

load_dotenv()


def run_historical_collection(
    epic: str = "DE40",
    from_date: str = "2025-01-01",
    to_date: str | None = None,
    resolution: str = "MINUTE_5",
) -> dict:
    """
    Pipeline complète de collecte historique :
      1. Ouvre la session Capital.com
      2. Récupère les candles par fenêtres paginées
      3. Parse chaque candle (mid bid/ask, id unique)
      4. Insère en base SQLite sans doublons
      5. Retourne un rapport

    Returns:
        {
            "status": "success",
            "epic": "DE40",
            "total_candles": 5234,
            "inserted": 4987,
            "skipped": 247,
            "date_range": {"from": "2025-01-01", "to": "2025-12-31"}
        }
    """
    if to_date is None:
        to_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    api_key    = os.getenv("CAPITAL_API_KEY")
    identifier = os.getenv("CAPITAL_IDENTIFIER")
    password   = os.getenv("CAPITAL_PASSWORD")

    if not all([api_key, identifier, password]):
        raise EnvironmentError(
            "Variables manquantes dans .env : CAPITAL_API_KEY, CAPITAL_IDENTIFIER, CAPITAL_PASSWORD"
        )

    session = SessionManager(api_key, identifier, password, ping=True)
    client  = CapitalClient(session)

    print(f"Collecte {epic}  {from_date} → {to_date} ...")
    raw     = client.get_candles_paginated(epic, from_date, to_date, resolution)
    parsed  = parse_candles(raw, epic, resolution)
    report  = import_candles(parsed)

    session.close()

    return {
        "status":       "success",
        "epic":         epic,
        "total_candles": report["total"],
        "inserted":     report["inserted"],
        "skipped":      report["skipped"],
        "date_range":   {"from": from_date, "to": to_date},
    }
