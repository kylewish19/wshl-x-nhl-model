import pandas as pd
import pytest
from wshlx_nhl.daily_shadow_grading import grade_totals,grade_goalies,cumulative

def test_totals_grade_only_one_probability_per_game():
    d=pd.DataFrame([{"date":"2026-11-12","game":"A@B","line":6.5,"model":"tie_only","selection":s,"probability":p,"odds_american":100,"qualifies":s=="Over"} for s,p in [("Over",.6),("Under",.4)]])
    finals=pd.DataFrame([{"date":"2026-11-12","game":"A@B","total_goals":7}])
    x,s=grade_totals(d,finals)
    assert x.result.tolist()==["WIN","LOSS"]
    assert s.settled_rows.iloc[0]==1 and s.paper_profit_units.iloc[0]==1

def test_nonstarter_void():
    d=pd.DataFrame([{"date":"2026-11-12","game":"A@B","goalie_id":i,"team":"A","line":24.5,"model":"v0_2","selection":"Over","over_probability":.6,"expected_saves":26,"odds_american":100,"qualifies":True} for i in ["1","2"]])
    starts=d.iloc[:1][["date","game","goalie_id","team"]].assign(saves=28)
    x,s=grade_goalies(d,starts,d[["date","game"]].drop_duplicates())
    assert x.result.tolist()==["WIN","VOID"]
    assert s.paper_voids.iloc[0]==1 and s.saves_mae.iloc[0]==2

def test_ledger_rejects_duplicate_clean_and_excludes_replay():
    d=pd.DataFrame([{"date":"2026-11-12","market":"total","model":"tie_only","cohort":"CLEAN_SHADOW_PREGAME","settled_rows":2,"brier":.2,"log_loss":.5,"paper_wins":1,"paper_losses":0,"paper_voids":0,"paper_profit_units":1}])
    assert cumulative(pd.concat([d,d.assign(cohort="RETROSPECTIVE_SMOKE_ONLY")])).slates.iloc[0]==1
    with pytest.raises(ValueError,match="Duplicate"):
        cumulative(pd.concat([d,d]))
