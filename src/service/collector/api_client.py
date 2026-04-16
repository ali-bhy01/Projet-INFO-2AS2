# api_client.py
import requests
from requests.exceptions import Timeout, ConnectionError
from src.service.collector.session_manager import SessionManager

BASE_URL = "https://demo-api-capital.backend-capital.com/api/v1"
TIMEOUT  = 15  # secondes

class CapitalClient:
    def __init__(self, session: SessionManager):
        self.session = session

    def get_instrument(self, search_term: str) -> dict:
        r = requests.get(
            f"{BASE_URL}/markets",
            headers=self.session.get_headers(),
            params={"searchTerm": search_term},
            timeout=TIMEOUT,
        )
        if r.status_code != 200:
            raise ValueError(f"Erreur markets : {r.status_code} - {r.text}")
        return r.json()

    def get_candles(self, epic: str, resolution: str = "MINUTE_5", max: int = 10) -> dict:
        r = requests.get(
            f"{BASE_URL}/prices/{epic}",
            headers=self.session.get_headers(),
            params={"resolution": resolution, "max": max},
            timeout=TIMEOUT,
        )
        if r.status_code != 200:
            raise ValueError(f"Erreur prices : {r.status_code} - {r.text}")
        return r.json()

    def get_candles_paginated(
        self,
        epic: str,
        from_date: str,
        to_date: str,
        resolution: str = "MINUTE_5",
        window_minutes: int = 45,
    ) -> list:
        """
        Récupère TOUTES les candles entre from_date et to_date
        en paginant par fenêtres de window_minutes minutes.

        Args:
            from_date: "2025-01-01" ou "2025-01-01T09:00:00"
            to_date:   "2025-12-31" ou "2025-12-31T17:30:00"

        Returns:
            Liste complète de candles brutes JSON (champ "prices")
        """
        import time as _time
        from datetime import datetime, timedelta

        start = datetime.fromisoformat(from_date)
        end   = datetime.fromisoformat(to_date)
        all_candles: list = []

        window_from = start
        while window_from < end:
            window_to = min(window_from + timedelta(minutes=window_minutes), end)
            from_str  = window_from.strftime("%Y-%m-%dT%H:%M:%S")
            to_str    = window_to.strftime("%Y-%m-%dT%H:%M:%S")

            try:
                result = self.get_candles_range(epic, from_str, to_str, resolution)
                all_candles.extend(result.get("prices", []))
            except ValueError as e:
                err = str(e)
                if "404" not in err and "daterange" not in err:
                    print(f"    Erreur {from_str}: {e}")

            window_from = window_to
            _time.sleep(0.3)

        return all_candles

    def get_candles_range(
        self,
        epic: str,
        from_dt: str,
        to_dt: str,
        resolution: str = "MINUTE_5",
        retries: int = 3,
    ) -> dict:
        """Récupère les candles entre deux dates ISO 8601.
        Réessaie automatiquement en cas de timeout (jusqu'à `retries` fois).
        """
        for attempt in range(1, retries + 1):
            try:
                r = requests.get(
                    f"{BASE_URL}/prices/{epic}",
                    headers=self.session.get_headers(),
                    params={"resolution": resolution, "from": from_dt, "to": to_dt},
                    timeout=TIMEOUT,
                )
                if r.status_code != 200:
                    raise ValueError(f"Erreur prices range : {r.status_code} - {r.text}")
                return r.json()
            except (Timeout, ConnectionError) as e:
                if attempt == retries:
                    raise ValueError(f"Timeout après {retries} tentatives : {e}")
                print(f"    Timeout (tentative {attempt}/{retries}), retry...")

    # ------------------------------------------------------------------ orders

    def place_working_order(
        self,
        epic: str,
        direction: str,   # "BUY" ou "SELL"
        level: float,     # prix de déclenchement
        size: float,
    ) -> dict:
        """Place un ordre stop (working order). Retourne la réponse API."""
        r = requests.post(
            f"{BASE_URL}/workingorders",
            headers={**self.session.get_headers(), "Content-Type": "application/json"},
            json={
                "epic":      epic,
                "direction": direction,
                "size":      size,
                "level":     level,
                "type":      "STOP",
            },
            timeout=TIMEOUT,
        )
        if r.status_code not in (200, 201):
            raise ValueError(f"Erreur place_working_order : {r.status_code} - {r.text}")
        return r.json()

    def get_working_orders(self) -> list:
        """Retourne la liste des ordres stop en attente."""
        r = requests.get(
            f"{BASE_URL}/workingorders",
            headers=self.session.get_headers(),
            timeout=TIMEOUT,
        )
        if r.status_code != 200:
            raise ValueError(f"Erreur get_working_orders : {r.status_code} - {r.text}")
        return r.json().get("workingOrders", [])

    def cancel_working_order(self, deal_id: str) -> dict:
        """Annule un ordre stop par son dealId."""
        r = requests.delete(
            f"{BASE_URL}/workingorders/{deal_id}",
            headers=self.session.get_headers(),
            timeout=TIMEOUT,
        )
        if r.status_code not in (200, 204):
            raise ValueError(f"Erreur cancel_working_order : {r.status_code} - {r.text}")
        return r.json() if r.content else {}

    def get_open_positions(self) -> list:
        """Retourne la liste des positions ouvertes."""
        r = requests.get(
            f"{BASE_URL}/positions",
            headers=self.session.get_headers(),
            timeout=TIMEOUT,
        )
        if r.status_code != 200:
            raise ValueError(f"Erreur get_open_positions : {r.status_code} - {r.text}")
        return r.json().get("positions", [])

    def close_position(self, deal_id: str) -> dict:
        """Ferme une position ouverte par son dealId."""
        r = requests.delete(
            f"{BASE_URL}/positions/{deal_id}",
            headers=self.session.get_headers(),
            timeout=TIMEOUT,
        )
        if r.status_code not in (200, 204):
            raise ValueError(f"Erreur close_position : {r.status_code} - {r.text}")
        return r.json() if r.content else {}