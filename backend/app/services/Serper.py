import os
import requests

# Environment or fallback URL
SERPER_API_KEY = os.getenv("SERPER_API_KEY")
SERPER_API_URL = "https://google.serper.dev/search"

class SerperClient:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or SERPER_API_KEY
        if not self.api_key:
            raise ValueError("Serper API key not set. Please set SERPER_API_KEY in your environment.")

    def search(self, query: str, gl: str = "in", hl: str = "en") -> dict:
        headers = {
            "X-API-KEY": self.api_key,
            "Content-Type": "application/json"
        }
        payload = {
            "q": query.strip(),
            "gl": gl,
            "hl": hl
        }
        response = requests.post(SERPER_API_URL, headers=headers, json=payload, timeout=10)
        response.raise_for_status()
        return response.json()
