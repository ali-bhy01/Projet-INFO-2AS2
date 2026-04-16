#!/usr/bin/env python3
"""
ASRS EOD — annule les ordres pending et ferme toute position DE40 ouverte à 17:30 CET.

Déclenché par GitHub Actions à 15:35 UTC (été) et 16:35 UTC (hiver).
Le script vérifie lui-même l'heure de Berlin avant d'agir.
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
    print(f"[ASRS EOD]  {now.strftime('%Y-%m-%d %H:%M')} CET")

    # Fenêtre d'action : 17:28 → 17:50 CET
    if not (now.hour == 17 and 28 <= now.minute <= 50):
        print(f"Hors fenêtre EOD ({now.strftime('%H:%M')} CET) — exit")
        return

    session = SessionManager(
        os.environ["CAPITAL_API_KEY"],
        os.environ["CAPITAL_IDENTIFIER"],
        os.environ["CAPITAL_PASSWORD"],
    )
    client = CapitalClient(session)

    # 1. Annuler les ordres stop en attente pour DE40
    orders     = client.get_working_orders()
    de40_orders = [
        o for o in orders
        if o.get("workingOrderData", {}).get("epic") == EPIC
    ]

    if de40_orders:
        for order in de40_orders:
            deal_id = order["workingOrderData"]["dealId"]
            client.cancel_working_order(deal_id)
            print(f"  Ordre annulé : {deal_id}")
    else:
        print("  Aucun ordre pending.")

    # 2. Fermer toute position ouverte sur DE40
    positions  = client.get_open_positions()
    de40_pos   = [
        p for p in positions
        if (p.get("position", {}).get("epic") == EPIC or
            p.get("market",   {}).get("epic") == EPIC)
    ]

    if de40_pos:
        for pos in de40_pos:
            deal_id = pos["position"]["dealId"]
            result  = client.close_position(deal_id)
            direction = pos["position"].get("direction", "?")
            size      = pos["position"].get("size", "?")
            print(f"  Position fermée : {direction} {size} lot(s) — dealId {deal_id}")
    else:
        print("  Aucune position ouverte.")

    session.close()
    print("Done.")


if __name__ == "__main__":
    main()
