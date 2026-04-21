import requests
from requests.exceptions import Timeout

BASE_URL = "https://demo-api-capital.backend-capital.com/api/v1"


class CapitalClient:
    def __init__(self, session):
        self._session = session

    def _headers(self) -> dict:
        return self._session.get_headers()

    def _get(self, path: str, params: dict = None) -> dict:
        resp = requests.get(f"{BASE_URL}/{path}", headers=self._headers(), params=params)
        if resp.status_code != 200:
            raise ValueError(f"{resp.status_code}: {resp.text}")
        return resp.json()

    def _delete(self, path: str) -> dict:
        resp = requests.delete(f"{BASE_URL}/{path}", headers=self._headers())
        if resp.status_code not in (200, 204):
            raise ValueError(f"{resp.status_code}: {resp.text}")
        if not resp.content:
            return {}
        return resp.json()

    def get_instrument(self, search_term: str) -> dict:
        return self._get("markets", params={"searchTerm": search_term})

    def get_candles(self, epic: str, resolution: str = "MINUTE_5", max: int = 1000) -> dict:
        return self._get(f"prices/{epic}", params={"resolution": resolution, "max": max})

    def get_candles_range(
        self, epic: str, from_dt: str, to_dt: str,
        resolution: str = "MINUTE_5", retries: int = 3,
    ) -> dict:
        for attempt in range(retries):
            try:
                resp = requests.get(
                    f"{BASE_URL}/prices/{epic}",
                    headers=self._headers(),
                    params={"resolution": resolution, "from": from_dt, "to": to_dt},
                )
                if resp.status_code != 200:
                    raise ValueError(f"{resp.status_code}: {resp.text}")
                return resp.json()
            except Timeout:
                if attempt == retries - 1:
                    raise ValueError(f"Timeout after {retries} retries")

    def get_working_orders(self) -> list:
        return self._get("workingorders").get("workingOrders", [])

    def get_open_positions(self) -> list:
        return self._get("positions").get("positions", [])

    def cancel_working_order(self, deal_id: str) -> dict:
        return self._delete(f"workingorders/{deal_id}")

    def close_position(self, position_id: str) -> dict:
        return self._delete(f"positions/{position_id}")
