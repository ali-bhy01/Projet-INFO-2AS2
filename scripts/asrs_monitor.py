#!/usr/bin/env python3
"""
ASRS Monitor — vérifie le TP toutes les 5s entre 09:20 et 17:20 CET.

Logique :
- Hors fenêtre    → attend sans appel API
- Dans la fenêtre, pas de position connue → vérifie /positions toutes les 30s
- Position connue → vérifie le prix toutes les 5s via candles
"""
import sys
import os
import json
import time
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo

ROOT       = Path(__file__).resolve().parent.parent
STATE_FILE = ROOT / "state.json"


def position_active() -> bool:
    try:
        return json.loads(STATE_FILE.read_text()).get("position_active", False)
    except Exception:
        return False


def clear_state() -> None:
    STATE_FILE.write_text(json.dumps({"position_active": False}))
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv
load_dotenv(ROOT / ".env")

from src.service.collector.session_manager import SessionManager
from src.service.collector.api_client import CapitalClient

EPIC   = "DE40"
BERLIN = ZoneInfo("Europe/Berlin")


def in_window(now: datetime) -> bool:
    return (now.hour == 9 and now.minute >= 20) or (10 <= now.hour <= 16) or \
           (now.hour == 17 and now.minute < 20)


def run(client: CapitalClient, test: bool) -> bool:
    """Vérifie le TP. Retourne True si une position est ouverte."""
    positions = client.get_open_positions()
    de40 = [
        p for p in positions
        if (p.get("position", {}).get("epic") == EPIC or
            p.get("market",   {}).get("epic") == EPIC)
    ]

    if not de40:
        return False

    # Prix live
    try:
        candles       = client.get_candles(EPIC, resolution="MINUTE", max=1)
        last          = candles["prices"][-1]
        bid_live      = last["closePrice"]["bid"]
        ask_live      = last["closePrice"]["ask"]
        current_price = round((bid_live + ask_live) / 2, 1)
    except Exception as e:
        print(f"  Prix indisponible : {e}")
        return True

    for pos in de40:
        p         = pos["position"]
        deal_id   = p["dealId"]
        direction = p.get("direction")
        entry     = p.get("level")
        stop      = p.get("stopLevel")

        if entry is None or stop is None:
            continue

        stop_dist = abs(entry - stop)
        tp     = round(entry + 1.0, 1) if (test and direction == "BUY") \
            else round(entry - 1.0, 1) if test \
            else round(entry + stop_dist, 1) if direction == "BUY" \
            else round(entry - stop_dist, 1)

        tp_hit = (current_price >= tp) if direction == "BUY" else (current_price <= tp)

        now_str = datetime.now(BERLIN).strftime("%H:%M:%S")
        print(f"  [{now_str}] {direction} @ {entry}  TP {tp}  actuel {current_price:.1f}  {'→ TP ATTEINT' if tp_hit else '...'}")

        if tp_hit:
            try:
                client.close_position(deal_id)
                print(f"  Position fermée @ {current_price:.1f}")
                clear_state()
            except ValueError as e:
                print(f"  Erreur close_position : {e}")

    return True


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--test",  action="store_true", help="TP fixe à 1 pt")
    parser.add_argument("--force", action="store_true", help="Bypass fenêtre horaire")
    args = parser.parse_args()

    if args.force:
        session = SessionManager(os.environ["CAPITAL_API_KEY"], os.environ["CAPITAL_IDENTIFIER"], os.environ["CAPITAL_PASSWORD"])
        client  = CapitalClient(session)
        run(client, test=args.test)
        session.close()
        sys.exit(0)

    print("Monitor démarré — en attente d'une position active...")
    session = SessionManager(os.environ["CAPITAL_API_KEY"], os.environ["CAPITAL_IDENTIFIER"], os.environ["CAPITAL_PASSWORD"])
    client  = CapitalClient(session)

    while True:
        now = datetime.now(BERLIN)

        # Arrêt à 17:20
        if now.hour > 17 or (now.hour == 17 and now.minute >= 20):
            print("17:20 CET — monitor arrêté.")
            break

        # Hors fenêtre ou pas de position signalée → dort sans appel API
        if not in_window(now) or not position_active():
            time.sleep(5)
            continue

        # Position active → vérifie le TP toutes les 5s
        has_position = run(client, test=args.test)
        if not has_position:
            clear_state()
        time.sleep(5)

    session.close()
