import pandas as pd

from wshlx_nhl.atg_consensus_shadow import atg_consensus_shadow


def test_atg_consensus_uses_lower_probability_and_price_gate():
    df = pd.DataFrame([
        {
            "player_name": "A",
            "odds_american": 250,
            "official_probability": 0.40,
            "current_season_probability": 0.36,
            "model_basis": "transition_ml_anchor",
            "current_gp": 15,
        },
        {
            "player_name": "B",
            "odds_american": 250,
            "official_probability": 0.45,
            "current_season_probability": 0.20,
            "model_basis": "transition_ml_anchor",
            "current_gp": 15,
        },
    ])
    out = atg_consensus_shadow(df)
    assert list(out["player_name"]) == ["A"]
    assert out.iloc[0]["consensus_probability"] == 0.36


def test_atg_consensus_quarantines_fallback():
    df = pd.DataFrame([
        {
            "player_name": "Fallback",
            "odds_american": 500,
            "official_probability": 0.35,
            "current_season_probability": 0.34,
            "model_basis": "limited_history_fallback_reconstruction",
            "current_gp": 12,
        }
    ])
    out = atg_consensus_shadow(df)
    assert out.empty
