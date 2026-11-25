import pandas as pd
import numpy as np
from wshlx_nhl.goalie_short_shadow import prepare,over

def test_rest_and_prior_short_rate_are_lagged():
    raw=pd.DataFrame({"date":["2025-10-01","2025-10-02","2025-10-08","2025-10-09"],"season":"20252026","goalie_id":"1","game_id":[1,2,3,4],"team":"A","toi_seconds":[3600,1200,3600,3600],"saves":[25,8,24,23],"shots_against":[28,12,27,27]})
    d=prepare(raw)
    assert d.rest_rebuilt.tolist()==[7,1,6,1]
    assert d.starts7_rebuilt.tolist()==[0,1,2,2]
    assert np.isclose(d.short_rate_prior.iloc[1],1/21)
    assert np.isclose(d.short_rate_prior.iloc[2],2/22)
    raw.loc[1,"toi_seconds"]=3600
    e=prepare(raw)
    assert d.short_rate_prior.iloc[1]==e.short_rate_prior.iloc[1]
    assert d.short_rate_prior.iloc[2]>e.short_rate_prior.iloc[2]

def test_over_probabilities_nested():
    p=over(np.array([10.,25.]),.03,20.5)
    q=over(np.array([10.,25.]),.03,28.5)
    assert (p>=q).all() and (p<=1).all() and (q>=0).all()
