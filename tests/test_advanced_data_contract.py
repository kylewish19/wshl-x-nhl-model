import json
import pandas as pd
import pytest
from wshlx_nhl.advanced_data_contract import reconcile,build_research,load_bundle,sha

def fixture():
    games=pd.DataFrame([dict(date=f"2024-10-0{i}",game_id=i,home="A",away="B",final=1) for i in range(1,5)])
    participants=pd.DataFrame([dict(date=g.date,game_id=g.game_id,team=t,player_id=p,toi_seconds=900) for g in games.itertuples() for t,p in [("A",1),("B",2)]])
    pp=participants[["game_id","player_id"]].assign(pp_toi_seconds=lambda x:x.player_id.map({1:120,2:0}))
    shots=pd.DataFrame([dict(date=g.date,game_id=g.game_id,event_id=i,player_id=1,team="A",kind=k,goal=int(k=="goal"),distance=20+i*5,angle=15,skater_advantage=1,shot_type="wrist",opponent_goalie_present=1,penalty_shot=0) for g in games.itertuples() for i,k in enumerate(["goal","shot-on-goal","missed-shot"],1)])
    ref=participants[["game_id","player_id"]].assign(goals=lambda x:x.player_id.map({1:1,2:0}),shots_on_goal=lambda x:x.player_id.map({1:2,2:0}),unblocked_attempts=lambda x:x.player_id.map({1:3,2:0}))
    return dict(games=games,participants=participants,pp=pp,shots=shots,reference=ref)

def test_reconciles_and_builds_lagged_features():
    d=fixture()
    r,f=build_research(d,["2024-10-02","2024-10-05"])
    assert r["games"]==4 and r["participants"]==8 and r["attempts"]==12 and r["pp_zero_rows"]==4
    assert r["scored_attempts"]==9
    assert f[f.game_id.eq(1)].pp_toi_seconds_r5.isna().all()
    assert f[(f.game_id.eq(2))&f.player_id.eq(1)].pp_toi_seconds_r5.iloc[0]==120

@pytest.mark.parametrize("table,column,value,match",[("reference","unblocked_attempts",4,"Independent count mismatch"),("pp","pp_toi_seconds",901,"Invalid PP seconds"),("games","final",0,"Invalid expected"),("shots","kind","blocked-shot","Unsupported attempt"),("shots","team","B","Shot identity")])
def test_invalid_data_fails(table,column,value,match):
    d=fixture();d[table].loc[0,column]=value
    with pytest.raises(ValueError,match=match):reconcile(d)

def test_missing_zero_row_and_game_rejected():
    d=fixture();d["pp"]=d["pp"].iloc[:-1]
    with pytest.raises(ValueError,match="participant coverage"):reconcile(d)
    d=fixture();d["shots"]=d["shots"][d["shots"].game_id.ne(4)]
    with pytest.raises(ValueError,match="game coverage"):reconcile(d)

def test_bundle_hash_and_rights(tmp_path):
    d=fixture();m=dict(schema_version=1,scope="SYNTHETIC",time_unit="seconds",distance_unit="feet",angle_unit="degrees",tables={})
    for n,x in d.items():
        p=tmp_path/(n+".csv");x.to_csv(p,index=False);m["tables"][n]=dict(sha256=sha(p),rows=len(x))
    p=tmp_path/"manifest.json";p.write_text(json.dumps(m))
    _,b=load_bundle(tmp_path);assert reconcile(b)["games"]==4
    m.update(scope="AUTHORIZED_RESEARCH",rights_reference="fixture only",provider="test");p.write_text(json.dumps(m))
    with pytest.raises(ValueError,match="Explicit authorization"):load_bundle(tmp_path)
    load_bundle(tmp_path,allow_authorized=True)
    (tmp_path/"pp.csv").write_text("changed")
    with pytest.raises(ValueError,match="Input hash mismatch"):load_bundle(tmp_path,allow_authorized=True)
