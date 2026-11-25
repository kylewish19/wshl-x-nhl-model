import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import run_goalie_board as board


def test_historical_full_name_survives_roster_outage(monkeypatch):
    def unavailable(team):
        raise AssertionError("unique historical match should not query API")
    monkeypatch.setattr(board, "roster_goalie_map", unavailable)
    starts = pd.DataFrame({"goalie_name": ["Darcy Kuemper", "Darcy Kuemper"], "goalie_id": ["8475311", "8475311"]})
    assert board.resolve_goalie(starts, "Darcy Kuemper", "LAK") == "8475311"


def test_accent_and_punctuation_normalization(monkeypatch):
    monkeypatch.setattr(board, "roster_goalie_map", lambda t: {})
    starts = pd.DataFrame({"goalie_name": ["Ukko-Pekka Luukkonen"], "goalie_id": ["8480045"]})
    assert board.resolve_goalie(starts, "Ukko Pekka Luukkonen", "BUF") == "8480045"


def test_ambiguous_identity_is_not_guessed(monkeypatch):
    monkeypatch.setattr(board, "roster_goalie_map", lambda t: {})
    starts = pd.DataFrame({"goalie_name": ["Same Name", "Same Name", "D. Kuemper"], "goalie_id": ["1", "2", "8475311"]})
    assert board.resolve_goalie(starts, "Same Name", "LAK") is None
    assert board.resolve_goalie(starts, "Darcy Kuemper", "LAK") is None
