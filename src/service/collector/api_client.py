# api_client.py
import requests
from src.service.collector.session_manager import SessionManager

BASE_URL = "https://demo-api-capital.backend-capital.com/api/v1"

class CapitalClient:
    def __init__(self, session: SessionManager):
        self.session = session

    def get_instrument(self, search_term: str) -> dict:
        r = requests.get(
            f"{BASE_URL}/markets",
            headers=self.session.get_headers(),
            params={"searchTerm": search_term}
        )
        if r.status_code != 200:
            raise ValueError(f"Erreur markets : {r.status_code} - {r.text}")
        return r.json()

    def get_candles(self, epic: str, resolution: str = "MINUTE_5", max: int = 10) -> dict:
        r = requests.get(
            f"{BASE_URL}/prices/{epic}",
            headers=self.session.get_headers(),
            params={"resolution": resolution, "max": max}
        )
        if r.status_code != 200:
            raise ValueError(f"Erreur prices : {r.status_code} - {r.text}")
        return r.json()