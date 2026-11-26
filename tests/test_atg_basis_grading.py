import pandas as pd
import pytest
from wshlx_nhl.atg_pregame import price_comparison,MODELS
from wshlx_nhl.atg_grading import grade_matched
from wshlx_nhl.atg_basis_grading import basis_summary,update_basis_ledger,cumulative_basis

def fixture():
    p=pd.DataFrame([dict(date="2026-11-26",game="A@B",player_id=i,team="A",
                         official_probability=.45,shot_probability=.2,boosting_calibrated=.5,model_basis=b)
                     for i,b in enumerate(["limited_history_fallback_reconstruction","transition_ml_anchor",None,"limited_history_fallback_reconstruction"],1)])
    p=price_comparison(p,p[["date","game","player_id"]].assign(odds_american=200))
    o=p[["date","game","player_id","team"]].iloc[:3].assign(goals=[1,0,0])
    d,s=grade_matched(p,o,[("2026-11-26","A@B")])
    return d,s

def test_basis_partition_and_frozen_selection_metrics():
    d,s=fixture()
    z,t=basis_summary(d)
    a=t[t.model.eq("official_probability")].set_index("basis_group")
    assert a.loc["limited_history","matched_rows"]==2
    assert a.loc["limited_history","paper_voids"]==1
    assert a.loc["limited_history","paper_profit_units"]==2
    assert a.loc["other_or_unknown","settled_rows"]==1
    for m,g in t.groupby("model"):
        old=s.set_index("model").loc[m]
        for k in ["matched_rows","settled_rows","void_rows","paper_count","paper_wins","paper_losses","paper_voids","paper_profit_units"]:
            assert g[k].sum()==pytest.approx(old[k])
    assert z.basis_group.notna().all()

def test_empty_group_and_bad_flags():
    d,_=fixture()
    _,s=basis_summary(d[d.model_basis.eq("transition_ml_anchor")])
    assert s[s.basis_group.eq("limited_history")].settled_rows.eq(0).all()
    d.loc[0,"official_probability_qualifies"]="invalid"
    with pytest.raises(ValueError,match="Invalid frozen flag"):
        basis_summary(d)

def test_separate_cohorts_and_duplicate_rejection():
    d,_=fixture()
    _,s=basis_summary(d)
    s=s.assign(date="2026-11-26",cohort="CLEAN_SHADOW_PREGAME",source_run_id=1)
    prior=s.assign(date="2026-11-25",cohort="FROZEN_SOURCE_SUBGROUP_REVIEW")
    ledger=update_basis_ledger(prior,s)
    assert len(ledger)==18
    assert len(cumulative_basis(ledger))==18
    pd.testing.assert_frame_equal(update_basis_ledger(prior,s,replay=True),prior)
    with pytest.raises(ValueError,match="Duplicate"):
        update_basis_ledger(ledger,s)
    with pytest.raises(ValueError,match="Not a clean"):
        update_basis_ledger(prior,s.assign(cohort="RETROSPECTIVE_SMOKE_ONLY"))

def test_weighted_cumulative():
    d,_=fixture()
    _,s=basis_summary(d)
    s=s.assign(date="2026-11-26",cohort="CLEAN_SHADOW_PREGAME",source_run_id=1)
    t=s.assign(date="2026-11-27",source_run_id=2)
    q=cumulative_basis(update_basis_ledger(s,t))
    a=q[(q.model=="official_probability")&(q.basis_group=="limited_history")].iloc[0]
    assert a.slates==2 and a.settled_rows==2 and a.paper_profit_units==4
    assert a.brier==pytest.approx(.55**2)
