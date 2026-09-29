from __future__ import annotations

from pathlib import Path
import requests

# MoneyPuck publishes these files for download. Do not scrape non-download pages.
TEAM_GAME_BY_GAME_URL = "https://moneypuck.com/moneypuck/playerData/careers/gameByGame/all_teams.csv"
RECENT_SHOTS_URL = "https://peter-tanner.com/moneypuck/downloads/shots_2021-2025.zip"


def download_file(url: str, destination: str | Path, timeout: int = 120) -> Path:
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with requests.get(url, stream=True, timeout=timeout) as r:
        r.raise_for_status()
        with destination.open("wb") as f:
            for chunk in r.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    f.write(chunk)
    return destination
