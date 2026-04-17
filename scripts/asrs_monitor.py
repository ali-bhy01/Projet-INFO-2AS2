#!/usr/bin/env python3
"""
ASRS Monitor — vérifie si le prix a atteint le TP (1:1 R:R) et ferme la position.

Capital.com demo ne supporte pas limitLevel sur les positions ouvertes.
Le TP est donc géré manuellement : ce script tourne toutes les 10 min,
calcule le TP 1:1 et appelle close_position() quand le prix l'atteint.
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


def main(test: bool = False) -> None:
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

    for pos in de40:
        p         = pos["position"]
        m         = pos.get("market", {})
        deal_id   = p["dealId"]
        direction = p.get("direction")
        entry     = p.get("level")
        stop      = p.get("stopLevel")

        bid = m.get("bid")
        ask = m.get("offer") or m.get("ask")
        if bid and ask:
            current_price = (bid + ask) / 2
        elif bid:
            current_price = bid
        else:
            print(f"  {direction} @ {entry} — prix actuel indisponible, skip")
            continue

        if entry is None or stop is None:
            print(f"  {direction} @ {entry} — données manquantes, skip")
            continue

        stop_dist = abs(entry - stop)
        if test:
            tp = round(entry + 1.0, 1) if direction == "BUY" else round(entry - 1.0, 1)
        else:
            tp = round(entry + stop_dist, 1) if direction == "BUY" else round(entry - stop_dist, 1)
        tp_hit = (current_price >= tp) if direction == "BUY" else (current_price <= tp)

        print(f"  {direction} @ {entry}  stop {stop}  TP {tp}  actuel {current_price:.1f}  {'→ TP ATTEINT' if tp_hit else 'en cours'}")

        if tp_hit:
            try:
                client.close_position(deal_id)
                print(f"  Position fermée @ {current_price:.1f}  (TP {tp})")
            except ValueError as e:
                print(f"  Erreur close_position ({deal_id}): {e}")

    session.close()
    print("Done.")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--test", action="store_true", help="TP fixe à 1 pt (test uniquement)")
    args = parser.parse_args()
    main(test=args.test)
