# session_manager.py
import requests
import threading
import time

BASE_URL = "https://demo-api-capital.backend-capital.com/api/v1"

class SessionManager:
    def __init__(self, api_key, identifier, password):
        self.api_key = api_key
        self.identifier = identifier
        self.password = password
        self.cst = None
        self.security_token = None
        self._start_session()
        self._start_ping()

    def _start_session(self):
        r = requests.post(
            f"{BASE_URL}/session",
            headers={"X-CAP-API-KEY": self.api_key},
            json={"identifier": self.identifier, "password": self.password, "encryptedPassword": False}
        )
        if r.status_code != 200:
            raise ValueError(f"Session failed : {r.status_code} - {r.text}")
        self.cst = r.headers["CST"]
        self.security_token = r.headers["X-SECURITY-TOKEN"]
        print("Session ouverte avec succès")

    def _ping(self):
        while True:
            time.sleep(9 * 60)
            r = requests.get(f"{BASE_URL}/ping", headers=self.get_headers())
            if r.status_code != 200:
                print("Ping failed, reconnexion...")
                self._start_session()

    def _start_ping(self):
        t = threading.Thread(target=self._ping, daemon=True)
        t.start()

    def get_headers(self):
        return {"CST": self.cst, "X-SECURITY-TOKEN": self.security_token}