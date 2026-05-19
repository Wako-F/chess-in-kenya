import os
from typing import Iterable

import requests


def warm(paths: Iterable[str], api_base: str) -> None:
    for path in paths:
        url = f"{api_base.rstrip('/')}{path}"
        response = requests.get(url, timeout=45)
        response.raise_for_status()
        print(f"Warmed {path}: {response.status_code}")


def main() -> None:
    api_base = os.getenv("CHESSKE_API_BASE", "http://127.0.0.1:8000")
    warm(
        (
            "/home",
            "/overview",
            "/meta/quality",
            "/trends/joins?months=36",
            "/trends/discovery?days=60",
            "/leaderboards/rapid?limit=12&min_games=20",
            "/leaderboards/blitz?limit=12&min_games=20",
            "/stats/analytics-pack",
        ),
        api_base,
    )


if __name__ == "__main__":
    main()
