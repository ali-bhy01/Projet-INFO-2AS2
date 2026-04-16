#!/usr/bin/env python3
"""
ASRS Signal — vérifie les filtres, lit le signal bar 09:15 CET, place les ordres OCO.

Déclenché par GitHub Actions à 07:20 UTC (été) et 08:20 UTC (hiver).
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

EPIC         = "DE40"
TRADE_SIZE   = 1        # nb de contrats — à ajuster
RANGE_MIN    = 10       # filtre F2 : range minimum du signal bar (pts)
RANGE_MAX    = 55       # filtre F2 : range maximum du signal bar (pts)
BUFFER       = 2        # pts au-dessus/en-dessous du signal bar pour l'entrée
SKIP_MONTHS  = {1, 7, 8}  # filtre C4 : janvier, juillet, août
BERLIN       = ZoneInfo("Europe/Berlin")


def main(force: bool = False) -> None:
    now = datetime.now(BERLIN)
    print(f"[ASRS SIGNAL]  {now.strftime('%Y-%m-%d %H:%M')} CET")

    # Fenêtre d'action : 09:15 → 09:35 CET (marge pour latence GitHub Actions)
    if not force and not (now.hour == 9 and 15 <= now.minute <= 35):
        print(f"Hors fenêtre signal ({now.strftime('%H:%M')} CET) — exit")
        return

    # F1 — skip vendredi
    if now.weekday() == 4:
        print("Vendredi — skip (F1)")
        return

    # C4 — skip janvier, juillet, août
    if now.month in SKIP_MONTHS:
        print(f"Mois {now.month} — skip (C4)")
        return

    # Connexion API
    session = SessionManager(
        os.environ["CAPITAL_API_KEY"],
        os.environ["CAPITAL_IDENTIFIER"],
        os.environ["CAPITAL_PASSWORD"],
    )
    client = CapitalClient(session)

    # Récupérer les 2 dernières bougies :
    # prices[-1] = bougie en cours (09:20), prices[-2] = signal bar (09:15, fermée)
    data   = client.get_candles(EPIC, resolution="MINUTE_5", max=2)
    prices = data.get("prices", [])

    if len(prices) < 2:
        print("Pas assez de candles — exit")
        session.close()
        return

    bar      = prices[-2]  # signal bar 09:15 (dernière fermée)
    sig_high = (bar["highPrice"]["bid"]  + bar["highPrice"]["ask"])  / 2
    sig_low  = (bar["lowPrice"]["bid"]   + bar["lowPrice"]["ask"])   / 2
    sig_range = sig_high - sig_low
    sig_ts    = bar.get("snapshotTimeUTC") or bar.get("snapshotTime", "?")

    print(f"Signal bar @ {sig_ts}  |  high {sig_high:.1f}  low {sig_low:.1f}  range {sig_range:.1f} pts")

    # F2 — filtre range
    if not (RANGE_MIN <= sig_range <= RANGE_MAX):
        print(f"Range {sig_range:.1f} hors [{RANGE_MIN}–{RANGE_MAX}] — skip (F2)")
        session.close()
        return

    long_entry  = round(sig_high + BUFFER, 1)
    short_entry = round(sig_low  - BUFFER, 1)
    long_stop   = short_entry   # stop du long = prix d'entrée short
    short_stop  = long_entry    # stop du short = prix d'entrée long

    print(f"OCO  BUY  STOP @ {long_entry}  stop @ {long_stop}")
    print(f"OCO  SELL STOP @ {short_entry}  stop @ {short_stop}")

    buy = client.place_working_order(
        epic=EPIC, direction="BUY",
        level=long_entry, size=TRADE_SIZE,
    )
    print(f"BUY order placé  → {buy}")

    sell = client.place_working_order(
        epic=EPIC, direction="SELL",
        level=short_entry, size=TRADE_SIZE,
    )
    print(f"SELL order placé → {sell}")

    session.close()
    print("Done.")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true", help="Bypass time window check")
    args = parser.parse_args()
    main(force=args.force)
