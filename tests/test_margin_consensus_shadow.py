import numpy as np
import pandas as pd
import pytest
from wshlx_nhl.margin_consensus_shadow import (
    pregame_margin_features,spread_board,grade_spreads,goalie_consensus,grade_consensus)

def history():
    rows=[]
    for i,(day,season) in enumerate([("2026-04-01","20252026"),("2026-10-01","20262027")],1):
        for t,o,home,gf,ga in [("A","B",0,1,3),("B","A",1,3,1)]:
            rows.append(dict(date=day,season=season,game_id=i,team=t,opponent=o,is_home=home,
                             goals_for=gf,goals_against=ga,shots_for=25+gf,shots_against=25+ga))
    return pd.DataFrame(rows)

class Model:
    classes_=[0,1,2,3]
    def predict_proba(self,x):
        return np.array([[.15,.25,.20,.40]]*len(x))

def test_features_strict_prior_and_lagged():
    h=history()
    z=pregame_margin_features(h,["A@B"],"2026-10-02")
    assert z.loc["A@B","home_gp"]==1
    assert z.loc["A@B","home_goals_for_r5"]==3
    assert z.loc["A@B","away_goals_for_r5"]==1
    with pytest.raises(ValueError,match="strictly prior"):
        pregame_margin_features(h,["A@B"],"2026-10-01")

@pytest.mark.parametrize("favorite_home",[True,False])
def test_spread_complements_and_settlement(favorite_home):
    z=pregame_margin_features(history(),["A@B"],"2026-10-02")
    c=pd.DataFrame([dict(date="2026-10-02",game="A@B",market="spread",active=1,
                         selection=name,line=line,model_probability=p,odds_american=100)
                    for name,line,p in [("Alpha",1.5 if favorite_home else -1.5,.65 if favorite_home else .35),
                                        ("Beta",-1.5 if favorite_home else 1.5,.35 if favorite_home else .65)]])
    d=spread_board(c,{"A@B":{"home":3.2,"away":2.8}},z,Model(),{"A":"Alpha","B":"Beta"})
    np.testing.assert_allclose(d.groupby("model").probability.sum(),1)
    p=d[(d.model=="direct_final_score_classes")&(d.line==-1.5)].probability.iloc[0]
    assert p==(.4 if favorite_home else .15)
    g,s=grade_spreads(d,pd.DataFrame([dict(date="2026-10-02",game="A@B",home_margin=2)]))
    assert s.settled_rows.eq(1).all()
    assert g[g.team.eq("B")].result.eq("WIN").all()
    assert g[g.team.eq("A")].result.eq("LOSS").all()

def test_goalie_consensus_uses_direction_and_exact_gate():
    rows=[]
    for id,ps,sides,flags in [("1",[.7,.6,.62],["Over"]*3,[True]*3),
            ("2",[.7,.6,.62],["Over","Over","Under"],[True]*3),
            ("3",[.7,.4,.62],["Over"]*3,[True]*3),
            ("4",[.7,.5,.62],["Over"]*3,[True]*3),
            ("5",[.3,.4,.38],["Under"]*3,[False,True,True])]:
        for m,p,side,q in zip(["v0_1","v0_2","v0_3"],ps,sides,flags):
            rows.append(dict(date="2026-10-02",game="A@B",goalie_id=id,goalie_name=id,
                team="A",line=20.5,model=m,over_probability=p,selection=side,qualifies=q,odds_american=100))
    d=goalie_consensus(pd.DataFrame(rows))
    assert set(d.goalie_id)=={"1","2","5"}
    assert d.unanimous_all_gates.sum()==1 and d.unanimous_v03_gate.sum()==2
    starts=d[d.goalie_id.ne("5")][["date","game","goalie_id","team"]].assign(saves=25)
    g,s=grade_consensus(d,starts,d[["date","game"]].drop_duplicates())
    assert s.direction_wins.tolist()==[2,1,1]
    assert s.direction_voids.tolist()==[1,1,0]
    assert s.paper_count.tolist()==[0,2,1]
    assert s.paper_profit_units.tolist()==[0,1,1]
    with pytest.raises(ValueError,match="Missing or duplicate"):
        goalie_consensus(pd.DataFrame(rows[:-1]))
