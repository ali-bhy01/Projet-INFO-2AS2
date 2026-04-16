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