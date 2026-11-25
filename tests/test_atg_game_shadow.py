import numpy as np
import pandas as pd
from wshlx_nhl.atg_game_shadow import build_features, FEATURES, score


def rows():
    return pd.DataFrame([
        {"date":f"2025-01-0{day}","game_id":day,"player_id":pid,"team":team,"opponent":opp,
         "position":"F","is_home":int(team=="B"),"goals":int(day==2 and pid==1),
         "shots":day+pid,"toi_seconds":600+day*60,"pp_goals":0}
        for day in (1,2,3) for pid,team,opp in [(1,"A","B"),(2,"B","A")]
    ])


def test_features_do_not_use_current_or_future_outcome():
    a=rows()
    baseline=build_features(a)
    a.loc[a.game_id.eq(2)&a.player_id.eq(1),["goals","shots","toi_seconds","pp_goals"]]=[2,9,1400,1]
    changed=build_features(a)
    before=baseline.game_id.le(2)
    np.testing.assert_allclose(baseline.loc[before,FEATURES],changed.loc[before,FEATURES],equal_nan=True)
    assert changed.loc[changed.game_id.eq(3)&changed.player_id.eq(1),"shots_r5"].iloc[0]>baseline.loc[baseline.game_id.eq(3)&baseline.player_id.eq(1),"shots_r5"].iloc[0]


def test_bounded_probability_and_prior_counts():
    d=build_features(rows())
    assert d.prior_gp.tolist()==[0,0,1,1,2,2]
    for col in ["baseline_probability","shot_probability"]:
        assert d[col].between(0,1).all()
    assert score([0,1],[.1,.9])["brier"]<.02


def test_duplicates_rejected():
    import pytest
    a=rows()
    with pytest.raises(ValueError,match="Duplicate"):
        build_features(pd.concat([a,a.iloc[[0]]]))
