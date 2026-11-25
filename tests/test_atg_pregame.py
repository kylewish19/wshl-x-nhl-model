import sys
from pathlib import Path
import numpy as np
import pandas as pd
import pytest
from wshlx_nhl.atg_game_shadow import build_features, FEATURES
from wshlx_nhl.atg_pregame import pregame_features, price_comparison
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from run_atg_pregame import matched_board

def fixture():
    return pd.DataFrame([
        {"date":f"2025-01-0{day}","game_id":day,"player_id":pid,"team":team,"opponent":opp,
         "position":pos,"is_home":int(team=="B"),"goals":int(day==2 and pid==1),
         "shots":day+pid,"toi_seconds":600+day*60,"pp_goals":0}
        for day in (1,2,3) for pid,team,opp,pos in [(1,"A","B","F"),(2,"B","A","D")]
    ])

def test_exact_historical_feature_parity():
    raw=fixture()
    past=raw[raw.game_id.lt(3)]
    board=raw[raw.game_id.eq(3)].assign(game="A@B").reset_index(drop=True)
    actual=pregame_features(past,board,"2025-01-03")
    expected=build_features(raw).query("game_id==3")[FEATURES].reset_index(drop=True)
    np.testing.assert_allclose(actual,expected,equal_nan=True,rtol=1e-12,atol=1e-12)

def test_future_rows_rejected():
    raw=fixture()
    with pytest.raises(ValueError,match="strictly before"):
        pregame_features(raw,raw.query("game_id==3").assign(game="A@B"),"2025-01-03")

def test_price_changes_do_not_change_features():
    raw=fixture()
    board=raw.query("game_id==3").assign(game="A@B",odds_american=150)
    a=pregame_features(raw.query("game_id<3"),board,"2025-01-03")
    b=pregame_features(raw.query("game_id<3"),board.assign(odds_american=900),"2025-01-03")
    pd.testing.assert_frame_equal(a,b)

def test_matched_price_gate():
    p=pd.DataFrame([{"date":"2025-01-03","game":"A@B","player_id":1,"official_probability":.40,"shot_probability":.30,"boosting_calibrated":.5}])
    o=p[["date","game","player_id"]].assign(odds_american=200)
    x=price_comparison(p,o)
    assert x.official_probability_qualifies.iloc[0]
    assert not x.shot_probability_qualifies.iloc[0]
    assert x.boosting_calibrated_qualifies.iloc[0]
    with pytest.raises(ValueError,match="Missing or invalid"):
        price_comparison(p,o.assign(odds_american=0))

def test_unknown_and_mismatched_players_are_audited():
    raw=fixture()
    d=pd.DataFrame([{"date":"2025-01-03","game":"A@B","market":"anytime_goal","active":1,
        "team":"A","resolved_team":"A","listed_team":"A","player_id":pid,"model_probability":.2}
        for pid in [1,2,3,None]])
    d.loc[1,"resolved_team"]="B"
    good,excluded=matched_board(d,raw.query("game_id<3"),"2025-01-03")
    assert good.player_id.tolist()==[1]
    assert set(excluded.exclusion_reason)=={"TEAM_MISMATCH","UNKNOWN_POSITION","UNRESOLVED_ID"}
