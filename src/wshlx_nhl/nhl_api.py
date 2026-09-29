from __future__ import annotations

from dataclasses import dataclass
import requests

BASE = "https://api-web.nhle.com/v1"


@dataclass
class NHLApi:
    timeout: int = 20

    def _get(self, path: str):
        r = requests.get(f"{BASE}{path}", timeout=self.timeout)
        r.raise_for_status()
        return r.json()

    def schedule(self, date: str):
        return self._get(f"/schedule/{date}")

    def scores(self, date: str):
        return self._get(f"/score/{date}")

    def roster(self, team_abbrev: str, season: str = "current"):
        return self._get(f"/roster/{team_abbrev}/{season}")

    def player_game_log(self, player_id: int, season: int, game_type: int = 2):
        return self._get(f"/player/{player_id}/game-log/{season}/{game_type}")

    def boxscore(self, game_id: int):
        return self._get(f"/gamecenter/{game_id}/boxscore")

    def play_by_play(self, game_id: int):
        return self._get(f"/gamecenter/{game_id}/play-by-play")
