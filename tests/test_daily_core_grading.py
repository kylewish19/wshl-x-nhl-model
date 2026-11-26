import sys
from pathlib import Path
from types import SimpleNamespace
import pandas as pd
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from grade_daily_core import settle,grade_card,season_update,CARDS,verify_core

def fixture():
    finals=pd.DataFrame([dict(game="NYR@BUF",total_goals=6,home_margin=2)]).set_index("game")
    starts=pd.DataFrame([dict(game="NYR@BUF",goalie_id="1",team="BUF",saves=24)])
    skaters=pd.DataFrame([dict(game="NYR@BUF",player_id=2,team="NYR",goals=1)])
    ids={("NYR@BUF","Goalie","BUF"):"1",("NYR@BUF","Other","NYR"):"3"}
    def f(**kwargs):return settle(SimpleNamespace(game="NYR@BUF",**kwargs),finals,starts,skaters,ids)
    return f

def test_settlement_wins_push_void_and_team_identity():
    f=fixture()
    assert f(market="moneyline",selection="Buffalo Sabres")[0]=="WIN"
    assert f(market="spread",selection="New York Rangers",line=1.5)[0]=="LOSS"
    assert f(market="total",selection="Over",line=6)[0]=="PUSH"
    assert f(market="anytime_goal",player_id=2,team="NYR")[0]=="WIN"
    assert f(market="anytime_goal",player_id=9,team="NYR")[0]=="VOID"
    assert f(market="goalie_saves",goalie_name="Other",team="NYR",selection="Other Over",line=22.5)[0]=="VOID"
    assert f(market="goalie_saves",goalie_name="Goalie",team="BUF",selection="Goalie Over",line=24)[0]=="PUSH"
    with pytest.raises(ValueError,match="team mismatch"):f(market="anytime_goal",player_id=2,team="BUF")

def test_grade_empty_and_void_card():
    d=pd.DataFrame([dict(date="2026-11-25",game="NYR@BUF",market="total",selection="Over",line=6.5,odds_american=100,model_probability=.6)])
    _,s=grade_card(d,lambda r:("VOID","DNP",""),"model_probability")
    assert s["voids"]==1 and s["roi"] is None and s["brier"] is None
    _,s=grade_card(d.iloc[:0],lambda r:None,"model_probability")
    assert s["wins"]==s["losses"]==s["voids"]==0

def test_season_update_duplicate_and_separate_cohorts():
    p=pd.DataFrame([dict(date="CUMULATIVE",cohort=c,wins=2,losses=2,hit_rate=.5,expected_wins=2.5,brier=.25,profit_units=float("nan") if n=="top10" else -1.,roi=float("nan") if n=="top10" else -.25) for n,c in CARDS.items()])
    stats={n:dict(wins=1,losses=0,hit_rate=1.,expected_wins=.6,brier=.16,profit_units=1.,roi=1.) for n in CARDS}
    q=season_update(p,"2026-11-26",stats)
    assert len(q)==6 and q[q.date.eq("CUMULATIVE")].wins.eq(3).all()
    assert q[q.date.eq("CUMULATIVE")].brier.tolist()==pytest.approx([.232]*3)
    with pytest.raises(ValueError,match="already graded"):season_update(q,"2026-11-26",stats)
