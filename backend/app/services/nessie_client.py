import os
import httpx
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv("NESSIE_BASE_URL", "http://api.nessieisreal.com")
API_KEY = os.getenv("NESSIE_API_KEY")


class NessieClient:
    def __init__(self):
        self.client = httpx.Client(timeout=10.0)

    def _url(self, path: str) -> str:
        separator = "&" if "?" in path else "?"
        return f"{BASE_URL}{path}{separator}key={API_KEY}"

    def get(self, path: str):
        r = self.client.get(self._url(path))
        r.raise_for_status()
        return r.json()

    def post(self, path: str, body: dict):
        r = self.client.post(self._url(path), json=body)
        r.raise_for_status()
        return r.json()

    def put(self, path: str, body: dict):
        r = self.client.put(self._url(path), json=body)
        r.raise_for_status()
        return r.json()

    def delete(self, path: str):
        r = self.client.delete(self._url(path))
        r.raise_for_status()
        return r.json()


nessie = NessieClient()
