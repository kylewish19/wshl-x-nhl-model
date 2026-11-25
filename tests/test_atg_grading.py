import sys
from pathlib import Path
import pandas as pd
import pytest
from wshlx_nhl.atg_grading import grade_matched
from wshlx_nhl.atg_pregame import MODELS,price_comparison
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from grade_atg_pregame import lock_status

def fixtures():
    p=pd.DataFrame([{"date":"2026-11-26","game":"A@B","player_id":i,"team":"A",
        "official_probability":.45,"shot_probability":.2,"boosting_calibrated":.5} for i in [1,2,3]])
    p=price_comparison(p,p[["date","game","player_id"]].assign(odds_american=200))
    o=p[["date","game","player_id","team"]].iloc[:2].assign(goals=[1,0])
    return p,o,[("2026-11-26","A@B")]

def test_win_loss_void_and_frozen_price_flags():
    p,o,g=fixtures()
    d,s=grade_matched(p,o,g)
    assert d.result.tolist()==["WIN","LOSS","VOID"]
    x=s.set_index("model")
    assert x.loc["official_probability","paper_profit_units"]==1
    assert x.loc["shot_probability","paper_count"]==0
    assert pd.isna(x.loc["shot_probability","paper_roi"])
    assert x.loc["boosting_calibrated","paper_voids"]==1

def test_reject_incomplete_or_mismatched_games():
    p,o,g=fixtures()
    with pytest.raises(ValueError,match="Incomplete"):
        grade_matched(p,o,[])
    with pytest.raises(ValueError,match="team mismatch"):
        grade_matched(p,o.assign(team="B"),g)

def test_artifact_timestamp_gate():
    m={"status":"PREGAME_PENDING_ARTIFACT_VERIFICATION","created_at_utc":"2026-11-26T22:00:00Z",
       "first_puck_utc":"2026-11-27T00:00:00Z","history_last_date":"2026-11-25","target_date":"2026-11-26"}
    a={"name":"atg-pregame-shadow-output","workflow_run":{"id":123},"created_at":"2026-11-26T22:01:00Z","expired":False}
    assert lock_status(m,a,False)=="CLEAN_SHADOW_PREGAME"
    with pytest.raises(ValueError,match="before puck"):
        lock_status(m,{**a,"created_at":"2026-11-27T00:01:00Z"},False)
    m["status"]="RETROSPECTIVE_SMOKE_ONLY"
    assert lock_status(m,a,True)=="RETROSPECTIVE_SMOKE_ONLY"
    with pytest.raises(ValueError,match="Expected pregame"):
        lock_status(m,a,False)
