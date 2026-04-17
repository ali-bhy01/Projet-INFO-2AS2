#!/usr/bin/env python3
"""
Test : place un trade marché sur DE40 avec TP et SL natifs via POST /positions.
Objectif : vérifier si Capital.com supporte limitLevel sur les positions demo.
"""
import sys, os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv
load_dotenv(ROOT / ".env")

import requests
from src.service.collector.session_manager import SessionManager
from src.service.collector.api_client import CapitalClient

BASE_URL = "https://demo-api-capital.backend-capital.com/api/v1"
EPIC     = "DE40"
SIZE     = 1
TP_DIST  = 30   # pts de TP au-dessus/en-dessous du prix courant
SL_DIST  = 30   # pts de SL

session = SessionManager(
    os.environ["CAPITAL_API_KEY"],
    os.environ["CAPITAL_IDENTIFIER"],
    os.environ["CAPITAL_PASSWORD"],
)
client = CapitalClient(session)

# Prix courant
candles = client.get_candles(EPIC, resolution="MINUTE", max=1)
last    = candles["prices"][-1]
bid     = last["closePrice"]["bid"]
ask     = last["closePrice"]["ask"]
mid     = round((bid + ask) / 2, 1)
print(f"Prix courant : {mid}  (bid {bid} / ask {ask})")

# BUY marché avec TP et SL
direction  = "BUY"
tp         = round(ask + TP_DIST, 1)
sl         = round(ask - SL_DIST, 1)

print(f"Placement BUY marché  TP={tp}  SL={sl}")

r = requests.post(
    f"{BASE_URL}/positions",
    headers={**session.get_headers(), "Content-Type": "application/json"},
    json={
        "epic":           EPIC,
        "direction":      direction,
        "size":           SIZE,
        "limitLevel":     tp,
        "stopLevel":      sl,
        "guaranteedStop": True,
    },
    timeout=15,
)

print(f"Status : {r.status_code}")
print(f"Réponse : {r.text}")
session.close()
