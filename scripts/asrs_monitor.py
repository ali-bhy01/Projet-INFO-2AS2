#!/usr/bin/env python3
"""
ASRS Monitor — pose le TP (limitLevel) sur les positions ouvertes via update_position().

Le TP est géré côté broker dès qu'il est posé : pas besoin de poller.
Ce script tourne toutes les 10 min pour attraper les positions nouvellement ouvertes.
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

EPIC      = "DE40"
BERLIN    = ZoneInfo("Europe/Berlin")
TP_RR     = 1.0   # ratio R:R — 1.0 = 1:1 (même distance que le stop)
TP_TEST_PTS = 1.0 # pts fixes pour le test (--test)


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
        deal_id   = p["dealId"]
        direction = p.get("direction")
        entry     = p.get("level")
        stop      = p.get("stopLevel")
        limit     = p.get("limitLevel")  # TP déjà posé ?

        if entry is None or stop is None:
            print(f"  {direction} @ {entry} — données manquantes, skip")
            continue

        stop_dist = abs(entry - stop)
        if test:
            tp = round(entry + TP_TEST_PTS, 1) if direction == "BUY" \
                 else round(entry - TP_TEST_PTS, 1)
            print(f"  [TEST] TP fixé à {TP_TEST_PTS} pt(s) de l'entrée")
        else:
            tp = round(entry + stop_dist * TP_RR, 1) if direction == "BUY" \
                 else round(entry - stop_dist * TP_RR, 1)

        if limit is not None:
            print(f"  {direction} @ {entry}  stop {stop}  TP déjà posé @ {limit}  — skip")
            continue

        print(f"  {direction} @ {entry}  stop {stop}  → pose TP @ {tp}")
        try:
            client.update_position(deal_id, limit_level=tp, stop_level=stop)
            print(f"  TP posé @ {tp}  (deal {deal_id})")
        except ValueError as e:
            print(f"  Erreur update_position ({deal_id}): {e}")

    session.close()
    print("Done.")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--test", action="store_true", help="TP fixe à 1 pt pour tester update_position()")
    args = parser.parse_args()
    main(test=args.test)
