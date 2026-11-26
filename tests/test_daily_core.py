import sys
from pathlib import Path
import pandas as pd
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from run_daily_core import validate_review,resolve_atg

def board():
    return pd.DataFrame([dict(game="A@B",player_name="Player A",team="A",odds_american=400),
                         dict(game="A@B",player_name="Player B",team="B",odds_american=600)])

def snapshot():
    return pd.DataFrame([dict(team="A",player_name="Player A",player_id=1,position="F",official_goal_prob=.2,official_goal_mu=.22,official_goal_basis="transition_ml_anchor"),
                         dict(team="B",player_name="Alternate B",player_id=2,position="D",official_goal_prob=.1,official_goal_mu=.105,official_goal_basis="limited_history_fallback_reconstruction")])

def test_exact_or_explicit_id_resolution():
    b=board();s=snapshot()
    d=resolve_atg(b,s,{})
    assert d.player_id.iloc[0]==1 and pd.isna(d.player_id.iloc[1])
    d=resolve_atg(b,s,{("A@B","Player B"):{"player_id":2,"position":"D"}})
    assert d.player_id.tolist()==[1,2]
    assert d.player_name.tolist()==b.player_name.tolist()
    assert d.odds_american.tolist()==b.odds_american.tolist()

def test_duplicate_identity_fails():
    b=board();b.loc[1,"team"]="A"
    with pytest.raises(ValueError,match="Duplicate resolved"):
        resolve_atg(b,snapshot(),{("A@B","Player B"):{"player_id":1}})

def test_review_requires_correct_date_and_known_rows():
    b=board()
    r=dict(date="2026-11-25",reviewed=True,source_note="review",scratches=["Player A"],corrections=[])
    assert validate_review("2026-11-25",r,b)[1]==["Player A"]
    with pytest.raises(ValueError,match="date-specific"):
        validate_review("2026-11-26",r,b)
    with pytest.raises(ValueError,match="Invalid scratch"):
        validate_review("2026-11-25",{**r,"scratches":["Old scratch"]},b)
    with pytest.raises(ValueError,match="outside matchup"):
        validate_review("2026-11-25",{**r,"corrections":[dict(game="A@B",player_name="Player B",team="C")]},b)
