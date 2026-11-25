import sys
from pathlib import Path
import pandas as pd
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from preflight_slate import validate

def fixture():
    root=Path(__file__).resolve().parents[1]
    date="2026-11-12"
    return date,*[pd.read_csv(root/x) for x in [f"data/inputs/{date}_team_board.csv",f"data/odds/{date}_core_FanDuel.csv",f"data/inputs/{date}_atg_board.csv",f"data/odds/{date}_goalie_saves_FanDuel.csv"]]

def test_original_board_passes():
    date,t,c,a,g=fixture()
    assert validate(date,t,c,a,g)["core_rows"]==6*len(t)

def test_missing_core_price_and_bad_date_fail():
    date,t,c,a,g=fixture()
    with pytest.raises(ValueError,match="missing or unmatched"):
        validate(date,t,c.iloc[1:],a,g)
    with pytest.raises(ValueError,match="Wrong date"):
        validate("2026-11-13",t,c,a,g)

def test_goalie_identity_context_and_price_rejected():
    date,t,c,a,g=fixture()
    x=g.copy();x.loc[x.index[0],"team"]="ANA"
    with pytest.raises(ValueError,match="Goalie matchup"):
        validate(date,t,c,a,x)
    y=a.copy();y.loc[y.index[0],"odds_american"]=0
    with pytest.raises(ValueError,match="Invalid American odds"):
        validate(date,t,c,y,g)
