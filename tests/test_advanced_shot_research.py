import pandas as pd
import numpy as np
import pytest
from wshlx_nhl.advanced_shot_research import chronological_xg,aggregate_usage,lagged_usage

def shots():
    return pd.DataFrame([dict(date=f"2024-10-0{day}",game_id=day,event_id=i,player_id=1,team="A",
        goal=int(i%2==0),distance=10+i*5,angle=20,skater_advantage=i%2,shot_type="wrist",
        opponent_goalie_present=1,penalty_shot=0)
        for day in range(1,5) for i in range(4)])

def test_crossfit_uses_only_prior_labels():
    d=shots()
    x=chronological_xg(d,["2024-10-02","2024-10-03","2024-10-05"])
    assert x[x.game_id.eq(1)].xg.isna().all()
    assert x[x.game_id.gt(1)].xg.between(0,1).all()
    assert x.loc[x.xg.notna(),"xg_train_end"].lt(x.loc[x.xg.notna(),"date"]).all()
    d.loc[d.game_id.eq(2),"goal"]=1-d.loc[d.game_id.eq(2),"goal"]
    y=chronological_xg(d,["2024-10-02","2024-10-03","2024-10-05"])
    np.testing.assert_allclose(x[x.game_id.eq(2)].xg,y[y.game_id.eq(2)].xg)

def test_usage_zeros_missing_pp_and_lag():
    x=chronological_xg(shots(),["2024-10-02","2024-10-03","2024-10-05"])
    p=pd.DataFrame([dict(date=f"2024-10-0{day}",game_id=day,player_id=i,team="A",toi_seconds=900)
        for day in range(1,5) for i in (1,2)])
    u=p[["game_id","player_id"]].assign(pp_toi_seconds=lambda q:np.where(q.player_id.eq(1),120,0))
    d=aggregate_usage(x,p,u,[1,2,3,4])
    assert d[d.player_id.eq(2)].ixg.eq(0).all()
    assert d[(d.player_id.eq(1))&d.game_id.eq(1)].ixg.isna().all()
    with pytest.raises(ValueError,match="Incomplete or extra PP"):
        aggregate_usage(x,p,u.iloc[:-1],[1,2,3,4])
    z=lagged_usage(d)
    assert z[z.game_id.eq(1)].pp_toi_seconds_r5.isna().all()
    assert z[(z.game_id.eq(2))&z.player_id.eq(1)].pp_toi_seconds_r5.iloc[0]==120
    d.loc[d.game_id.eq(4),"pp_toi_seconds"]=500
    v=lagged_usage(d)
    np.testing.assert_allclose(z.pp_toi_seconds_r5,v.pp_toi_seconds_r5,equal_nan=True)

def test_empty_net_and_penalty_shot_excluded():
    d=shots()
    d.loc[(d.game_id.eq(2))&d.event_id.eq(0),"opponent_goalie_present"]=0
    d.loc[(d.game_id.eq(2))&d.event_id.eq(1),"penalty_shot"]=1
    x=chronological_xg(d,["2024-10-02","2024-10-05"])
    assert x[(x.game_id.eq(2))&x.event_id.isin([0,1])].xg.isna().all()
