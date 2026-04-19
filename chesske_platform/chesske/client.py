import time
from typing import Dict, List, Optional, Tuple

import requests
from requests.exceptions import RequestException

from .config import Settings


class ChessComClient:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.base_url = "https://api.chess.com/pub"
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": settings.user_agent})

    def _request_json(self, url: str) -> Tuple[str, Optional[Dict]]:
        last_error: Optional[Exception] = None
        for attempt in range(self.settings.max_retries):
            try:
                response = self.session.get(
                    url,
                    timeout=(
                        self.settings.request_connect_timeout,
                        self.settings.request_read_timeout,
                    ),
                )
                if response.status_code == 404:
                    return "not_found", None
                response.raise_for_status()
                return "ok", response.json()
            except RequestException as exc:
                last_error = exc
                time.sleep((2**attempt) * 0.25)
        return f"error:{last_error}", None

    def fetch_active_country_players(self, country_code: str) -> List[str]:
        status, payload = self._request_json(f"{self.base_url}/country/{country_code}/players")
        if status != "ok" or not payload:
            return []
        players = payload.get("players", [])
        normalized = [str(p).strip().lower() for p in players if str(p).strip()]
        unique = sorted(set(normalized))
        if self.settings.max_active_players > 0:
            return unique[: self.settings.max_active_players]
        return unique

    def fetch_profile(self, username: str) -> Tuple[str, Optional[Dict]]:
        return self._request_json(f"{self.base_url}/player/{username}")

    def fetch_stats(self, username: str) -> Tuple[str, Optional[Dict]]:
        return self._request_json(f"{self.base_url}/player/{username}/stats")

