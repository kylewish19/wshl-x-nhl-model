import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from assemble_core_slate import TEAM_NAMES
from build_goalie_features import TEAMS


def test_active_team_market_mapping_complete():
    assert set(TEAM_NAMES)==set(TEAMS)-{"ARI"}
    assert len(TEAM_NAMES)==32
    assert len(set(TEAM_NAMES.values()))==32
