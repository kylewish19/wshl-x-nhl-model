import pandas as pd

from wshlx_nhl.selection_shadow import (
    add_shadow_risk_flags,
    apply_market_reliability,
    playable_price_shadow_v0_2,
    playable_price_shadow_v0_3,
)


def candidates():
    return pd.DataFrame([
        {"date":"2026-10-08","game":"AAA@BBB","market":"point_1plus","selection":"Veteran","model_probability":0.62,"odds_american":-105,"model_basis":"transition_ml_anchor","active":1},
        {"date":"2026-10-08","game":"AAA@BBB","market":"point_1plus","selection":"Rookie","model_probability":0.65,"odds_american":110,"model_basis":"limited_history_fallback","active":1},
        {"date":"2026-10-08","game":"CCC@DDD","market":"anytime_assist","selection":"Projected rookie","model_probability":0.42,"odds_american":220,"model_basis":"rookie_projection_fallback","active":1},
        {"date":"2026-10-08","game":"EEE@FFF","market":"anytime_goal","selection":"Longshot","model_probability":0.20,"odds_american":600,"model_basis":"transition_ml_anchor","active":1},
        {"date":"2026-10-08","game":"GGG@HHH","market":"anytime_goal","selection":"Established scorer","model_probability":0.42,"odds_american":180,"model_basis":"transition_ml_anchor","active":1},
    ])


def test_shadow_flags_targeted_cohorts():
    out = add_shadow_risk_flags(candidates()).set_index("selection")
    assert not bool(out.loc["Rookie", "shadow_eligible"])
    assert out.loc["Rookie", "shadow_risk_flag"] == "LIMITED_HISTORY_QUARANTINE"
    assert not bool(out.loc["Projected rookie", "shadow_eligible"])
    assert out.loc["Projected rookie", "shadow_risk_flag"] == "LIMITED_HISTORY_QUARANTINE"
    assert not bool(out.loc["Longshot", "shadow_eligible"])
    assert out.loc["Longshot", "shadow_risk_flag"] == "LOW_PROB_ATG_REVIEW"
    assert bool(out.loc["Veteran", "shadow_eligible"])
    assert bool(out.loc["Established scorer", "shadow_eligible"])


def test_shadow_card_does_not_change_official_probabilities():
    out = playable_price_shadow_v0_2(candidates()).set_index("selection")
    assert "Rookie" not in out.index
    assert "Projected rookie" not in out.index
    assert "Longshot" not in out.index
    assert out.loc["Veteran", "model_probability"] == 0.62
    assert out.loc["Established scorer", "model_probability"] == 0.42


def test_v03_reliability_is_one_sided_and_uses_only_prior_dates():
    history = pd.DataFrame([
        {"date":"2026-10-01","market":"point_1plus","model_probability":0.60,"result":"LOSS"},
        {"date":"2026-10-02","market":"point_1plus","model_probability":0.60,"result":"LOSS"},
        {"date":"2026-10-03","market":"point_1plus","model_probability":0.60,"result":"LOSS"},
        {"date":"2026-10-04","market":"point_1plus","model_probability":0.60,"result":"LOSS"},
        {"date":"2026-10-05","market":"point_1plus","model_probability":0.60,"result":"LOSS"},
        # Same-day information must not leak into the selection haircut.
        {"date":"2026-10-08","market":"point_1plus","model_probability":0.99,"result":"WIN"},
    ])
    row = pd.DataFrame([
        {"market":"point_1plus","model_probability":0.70}
    ])
    out = apply_market_reliability(row, history, target_date="2026-10-08")
    factor = float(out.iloc[0]["market_reliability_factor"])
    assert 0.65 <= factor < 1.0
    assert float(out.iloc[0]["calibrated_probability"]) < 0.70


def test_v03_quarantines_anytime_goal_and_limited_history():
    df = pd.DataFrame([
        {"date":"2026-10-08","game":"AAA@BBB","market":"anytime_goal","selection":"Veteran scorer","model_probability":0.55,"odds_american":150,"model_basis":"transition_ml_anchor","active":1},
        {"date":"2026-10-08","game":"CCC@DDD","market":"point_1plus","selection":"Rookie","model_probability":0.70,"odds_american":100,"model_basis":"limited_history_fallback_reconstruction","active":1},
        {"date":"2026-10-08","game":"EEE@FFF","market":"point_1plus","selection":"Veteran","model_probability":0.65,"odds_american":-105,"model_basis":"transition_ml_anchor","active":1},
    ])
    out = playable_price_shadow_v0_3(df, history=pd.DataFrame(), target_date="2026-10-08")
    assert list(out["selection"]) == ["Veteran"]


def test_v03_same_player_cluster_prefers_safer_hit_probability():
    df = pd.DataFrame([
        {"date":"2026-10-08","game":"AAA@BBB","market":"point_1plus","selection":"Same Player","model_probability":0.66,"odds_american":-105,"model_basis":"transition_ml_anchor","active":1},
        {"date":"2026-10-08","game":"AAA@BBB","market":"point_2plus","selection":"Same Player","model_probability":0.48,"odds_american":180,"model_basis":"transition_ml_anchor","active":1},
    ])
    out = playable_price_shadow_v0_3(df, history=pd.DataFrame(), target_date="2026-10-08")
    assert len(out) == 1
    assert out.iloc[0]["market"] == "point_1plus"
    assert float(out.iloc[0]["model_probability"]) == 0.66
