import pandas as pd

from wshlx_nhl.selection_shadow import add_shadow_risk_flags, playable_price_shadow_v0_2


def candidates():
    return pd.DataFrame([
        {"market":"point_1plus","selection":"Veteran","model_probability":0.62,"odds_american":-105,"model_basis":"transition_ml_anchor","active":1},
        {"market":"point_1plus","selection":"Rookie","model_probability":0.65,"odds_american":110,"model_basis":"limited_history_fallback","active":1},
        {"market":"anytime_goal","selection":"Longshot","model_probability":0.20,"odds_american":600,"model_basis":"transition_ml_anchor","active":1},
        {"market":"anytime_goal","selection":"Established scorer","model_probability":0.40,"odds_american":180,"model_basis":"transition_ml_anchor","active":1},
    ])


def test_shadow_flags_targeted_cohorts():
    out = add_shadow_risk_flags(candidates()).set_index("selection")
    assert not bool(out.loc["Rookie", "shadow_eligible"])
    assert out.loc["Rookie", "shadow_risk_flag"] == "LIMITED_HISTORY_QUARANTINE"
    assert not bool(out.loc["Longshot", "shadow_eligible"])
    assert out.loc["Longshot", "shadow_risk_flag"] == "LOW_PROB_ATG_REVIEW"
    assert bool(out.loc["Veteran", "shadow_eligible"])
    assert bool(out.loc["Established scorer", "shadow_eligible"])


def test_shadow_card_does_not_change_official_probabilities():
    out = playable_price_shadow_v0_2(candidates()).set_index("selection")
    assert "Rookie" not in out.index
    assert "Longshot" not in out.index
    assert out.loc["Veteran", "model_probability"] == 0.62
    assert out.loc["Established scorer", "model_probability"] == 0.40
