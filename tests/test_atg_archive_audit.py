import sys
from pathlib import Path
import pandas as pd
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from audit_atg_archive import audit_counts


def fixture(n=2000):
    return pd.DataFrame({"game_id":range(n),"season":"20252026","goals":0,
                         "shots":1,"toi_seconds":600,"pp_goals":0})


def test_rare_discrepancy_audited_without_changing_input(tmp_path):
    a=fixture()
    a.loc[0,["goals","shots"]]=[1,0]
    b,r=audit_counts(a,tmp_path)
    assert a.loc[0,"shots"]==0 and b.loc[0,"shots"]==1
    assert b.loc[0,"count_anomaly"] and r["goals_gt_shots"]==1
    assert (tmp_path/"count_anomalies.csv").exists()


def test_invalid_or_widespread_discrepancy_fails_closed(tmp_path):
    a=fixture()
    a.loc[:9,["goals","shots"]]=[1,0]
    with pytest.raises(ValueError,match="Data audit failed"):
        audit_counts(a,tmp_path)
    a=fixture()
    a.loc[0,"shots"]=-1
    with pytest.raises(ValueError,match="Data audit failed"):
        audit_counts(a,tmp_path)
