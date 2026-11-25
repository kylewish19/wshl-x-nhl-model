import pandas as pd
import numpy as np
from wshlx_nhl.daily_shadow import totals_board,goalie_board

def test_total_tie_only_and_complementarity():
    c=pd.DataFrame([{"date":"2026-11-12","game":"A@B","market":"total","active":1,"line":line,"selection":side,"model_probability":.5,"odds_american":-110} for line in [5.5,6.5,7.5] for side in ["Over","Under"]])
    x=totals_board(c,{"A@B":{"home":3.,"away":3.}})
    assert len(x)==12
    assert np.allclose(x.groupby(["line","model"]).probability.sum(),1)
    p=x[x.selection.eq("Over")].pivot(index="line",columns="model",values="probability")
    assert p.loc[5.5,"analytic_control"]==p.loc[5.5,"tie_only"]
    assert p.loc[6.5,"tie_only"]>p.loc[6.5,"analytic_control"]

def test_goalie_mismatch_is_excluded():
    common={"date":"2026-11-12","game":"A@B","goalie_name":"Example","team":"A","line":24.5,"over_odds":-110,"under_odds":-110}
    a=pd.DataFrame([{**common,"goalie_id":"1",**{f"{m}_{k}":v for m in ["v0_1","v0_2"] for k,v in [("over_probability",.6),("under_probability",.4),("expected_saves",26)]}}])
    b=pd.DataFrame([{**common,"goalie_id":"1","v0_3_over_probability":.4,"v0_3_under_probability":.6,"v0_3_expected_saves":23}])
    x,e=goalie_board(a,b)
    assert len(x)==3 and e.empty and x.qualifies.all()
    x,e=goalie_board(a,b.assign(goalie_id="UNKNOWN"))
    assert x.empty and len(e)==1
