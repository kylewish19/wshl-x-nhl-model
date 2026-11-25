import numpy as np
import pandas as pd
import pytest
from wshlx_nhl.team_market_shadow import build_team_features,baseline,FEATURES

def fixture():
    out=[]
    for day,h,a in [(1,3,1),(2,2,3),(3,4,3),(4,1,4)]:
        for team,opp,home,gf,ga in [("A","B",1,h,a),("B","A",0,a,h)]:
            out.append({"date":f"2025-10-0{day}","season":"20252026","game_id":day,"team":team,"opponent":opp,"is_home":home,"goals_for":gf,"goals_against":ga,"shots_for":30+gf,"shots_against":30+ga})
    return pd.DataFrame(out)

def test_current_and_future_outcomes_do_not_change_features():
    d=fixture()
    a=build_team_features(d)
    m=d.game_id.eq(3)
    d.loc[m,"goals_for"]=d.loc[m,"goals_for"]+1
    d.loc[m,"goals_against"]=d.loc[m,"goals_against"]+1
    b=build_team_features(d)
    np.testing.assert_allclose(a.loc[a.game_id.le(3),FEATURES],b.loc[b.game_id.le(3),FEATURES],equal_nan=True)
    assert not a.loc[a.game_id.eq(4),"home_gf"].equals(b.loc[b.game_id.eq(4),"home_gf"])

def test_baseline_and_labels():
    z=build_team_features(fixture())
    p=baseline(z)
    assert p.apply(lambda x:x.between(0,1)).all().all()
    assert (p.over55>=p.over65).all()
    assert z.margin_class.tolist()==[3,1,2,0]
    assert z.total_class.tolist()==[0,0,2,0]

def test_incomplete_game_rejected():
    with pytest.raises(ValueError,match="Incomplete"):
        build_team_features(fixture().iloc[:-1])
