import threading
import requests

BASE_URL = "https://demo-api-capital.backend-capital.com/api/v1"


class SessionManager:
    def __init__(self, api_key: str, identifier: str, password: str, ping: bool = False):
        self._api_key = api_key
        self._stop_event = threading.Event()

        resp = requests.post(
            f"{BASE_URL}/session",
            headers={"X-CAP-API-KEY": api_key, "Content-Type": "application/json"},
            json={"identifier": identifier, "password": password},
        )
        if resp.status_code != 200:
            raise ValueError(f"{resp.status_code}: {resp.text}")

        self.cst = resp.headers["CST"]
        self.security_token = resp.headers["X-SECURITY-TOKEN"]

        if ping:
            self._start_ping()

    def get_headers(self) -> dict:
        return {"CST": self.cst, "X-SECURITY-TOKEN": self.security_token}

    def close(self) -> None:
        self._stop_event.set()

    def _start_ping(self) -> None:
        def _loop():
            while not self._stop_event.wait(timeout=60):
                try:
                    requests.get(
                        f"{BASE_URL}/ping",
                        headers={"X-CAP-API-KEY": self._api_key, **self.get_headers()},
                        timeout=10,
                    )
                except Exception:
                    pass

        threading.Thread(target=_loop, daemon=True).start()
