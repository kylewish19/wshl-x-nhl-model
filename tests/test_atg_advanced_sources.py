import sys
from pathlib import Path
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from probe_atg_advanced_sources import shot_event

def event(owner=1,x=79,side="left",kind="goal",situation="1451",period="REG"):
    return {"typeDescKey":kind,"eventId":2,"periodDescriptor":{"periodType":period,"number":1},
        "homeTeamDefendingSide":side,"situationCode":situation,
        "details":{"eventOwnerTeamId":owner,"xCoord":x,"yCoord":0,"scoringPlayerId":5,"shootingPlayerId":6}}

def test_geometry_and_strength():
    a=shot_event(event(),1,2)
    assert a["distance"]==10 and a["angle"]==0 and a["goal"]==1 and a["skater_advantage"]==1
    b=shot_event(event(owner=2,x=-79,kind="shot-on-goal"),1,2)
    assert b["distance"]==10 and b["player_id"]==6 and b["skater_advantage"]==-1

def test_shootouts_blocks_and_unknown_geometry():
    assert shot_event(event(period="SO"),1,2) is None
    assert shot_event(event(kind="blocked-shot"),1,2) is None
    assert shot_event(event(side=None),1,2)["distance"] is None

def test_empty_net_flag():
    assert shot_event(event(situation="0651"),1,2)["opponent_goalie_present"]==0
