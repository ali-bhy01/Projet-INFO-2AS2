#!/usr/bin/env python3
"""
ASRS Monitor — détecte les positions DE40 sans TP et les ajoute (1:1 R:R).

Déclenché par GitHub Actions toutes les 10 minutes pendant les heures de marché.
"""
import sys
import os
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv
load_dotenv(ROOT / ".env")

from src.service.collector.session_manager import SessionManager
from src.service.collector.api_client import CapitalClient

EPIC   = "DE40"
BERLIN = ZoneInfo("Europe/Berlin")


def main() -> None:
    now = datetime.now(BERLIN)
    print(f"[ASRS MONITOR]  {now.strftime('%Y-%m-%d %H:%M')} CET")

    # Fenêtre d'action : 09:20 → 17:20 CET
    if not (9 <= now.hour <= 17):
        print(f"Hors fenêtre monitor ({now.strftime('%H:%M')} CET) — exit")
        return

    session = SessionManager(
        os.environ["CAPITAL_API_KEY"],
        os.environ["CAPITAL_IDENTIFIER"],
        os.environ["CAPITAL_PASSWORD"],
    )
    client = CapitalClient(session)

    positions = client.get_open_positions()
    de40 = [
        p for p in positions
        if (p.get("position", {}).get("epic") == EPIC or
            p.get("market",   {}).get("epic") == EPIC)
    ]

    if not de40:
        print("  Aucune position DE40 ouverte.")
        session.close()
        return

    updated = 0
    for pos in de40:
        p         = pos["position"]
        deal_id   = p["dealId"]
        direction = p.get("direction")
        entry     = p.get("level")
        stop      = p.get("stopLevel")
        tp        = p.get("limitLevel")

        if tp is not None:
            print(f"  {direction} @ {entry} — TP déjà set @ {tp}")
            continue

        if entry is None or stop is None:
            print(f"  {direction} @ {entry} — données manquantes, skip")
            continue

        stop_dist = abs(entry - stop)
        if direction == "BUY":
            limit_level = round(entry + stop_dist, 1)
        else:
            limit_level = round(entry - stop_dist, 1)

        try:
            client.update_position(deal_id, limit_level)
            print(f"  {direction} @ {entry}  stop {stop}  → TP ajouté @ {limit_level}")
            updated += 1
        except ValueError as e:
            print(f"  Erreur update TP ({deal_id}): {e}")

    if updated == 0 and de40:
        print("  Tous les TP sont déjà en place.")

    session.close()
    print("Done.")


if __name__ == "__main__":
    main()
