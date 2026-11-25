"""Probe advanced NHL sources; no official forecasts or training."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import math
import pandas as pd
import requests
from build_goalie_features import BASE,get_json

STATS="https://api.nhle.com/stats/rest/en/skater"

def shot_event(play,home,away):
    kind=play.get("typeDescKey")
    if kind not in ("goal","shot-on-goal","missed-shot"):
        return None
    period=play.get("periodDescriptor",{})
    if period.get("periodType")=="SO":
        return None
    d=play.get("details",{})
    owner=d.get("eventOwnerTeamId")
    shooter=d.get("scoringPlayerId") if kind=="goal" else d.get("shootingPlayerId")
    side=play.get("homeTeamDefendingSide")
    x,y=d.get("xCoord"),d.get("yCoord")
    situation=str(play.get("situationCode",""))
    valid_situation=len(situation)==4 and situation.isdigit()
    known_owner=owner in (home,away)
    valid_coords=isinstance(x,(int,float)) and isinstance(y,(int,float)) and abs(x)<=100 and abs(y)<=42.5
    oriented=valid_coords and known_owner and side in ("left","right")
    # Home defending left -> home attacks right; away attacks left.
    attack_right=(owner==home)==(side=="left") if oriented else None
    nx=(x if attack_right else -x) if oriented else None
    distance=math.hypot(89-nx,y) if oriented else None
    angle=math.degrees(math.atan2(abs(y),89-nx)) if oriented else None
    opp_goalie=(situation[0] if owner==home else situation[3]) if valid_situation and known_owner else None
    own_skaters=int(situation[2] if owner==home else situation[1]) if valid_situation and known_owner else None
    opp_skaters=int(situation[1] if owner==home else situation[2]) if valid_situation and known_owner else None
    return {"event_id":play.get("eventId"),"player_id":shooter,"team_id":owner,
            "goal":int(kind=="goal"),"kind":kind,"distance":distance,"angle":angle,
            "shot_type":d.get("shotType"),"opponent_goalie_present":int(opp_goalie) if opp_goalie in ("0","1") else None,
            "skater_advantage":own_skaters-opp_skaters if own_skaters is not None else None,
            "period":period.get("number"),"time_in_period":play.get("timeInPeriod")}

def probe_stats(gid):
    result={}
    for report in ["timeonice","powerplay"]:
        try:
            r=requests.get(f"{STATS}/{report}",params={"isAggregate":"false","isGame":"true",
                "start":0,"limit":100,"cayenneExp":f"gameId={gid} and gameTypeId=2"},timeout=40)
            r.raise_for_status()
            data=r.json().get("data",[])
            result[report]={"rows":len(data),"keys":sorted(set().union(*(x.keys() for x in data))),
                "example":data[0] if data else None,"total":r.json().get("total")}
        except Exception as e:
            result[report]={"error":str(e)}
    return result

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--history",required=True)
    ap.add_argument("--out-dir",required=True)
    args=ap.parse_args()
    out=Path(args.out_dir);out.mkdir(parents=True,exist_ok=True)
    raw=pd.read_parquet(args.history)
    assert pd.to_datetime(raw.date).max()<pd.Timestamp("2026-11-25")
    games=raw[["season","date","game_id"]].drop_duplicates().sort_values(["season","date","game_id"])
    samples=[]
    for season,g in games.groupby("season"):
        for i in sorted({0,len(g)//2,len(g)-1}):
            samples.append(g.iloc[i])
    rows=[];schemas=[];shots=[]
    for g in samples:
        gid=int(g.game_id)
        entry={"game_id":gid,"season":str(g.season),"date":str(g.date)}
        try:
            p=get_json(f"{BASE}/gamecenter/{gid}/play-by-play")
            assert str(p.get("gameState","")).upper() in ("OFF","FINAL")
            assert p["gameDate"]==str(g.date)[:10]
            events=[shot_event(e,p["homeTeam"]["id"],p["awayTeam"]["id"]) for e in p["plays"]]
            events=[e for e in events if e is not None]
            z=pd.DataFrame(events)
            assert len(z)>0 and not z.event_id.duplicated().any()
            known=set(raw.loc[raw.game_id.eq(gid),"player_id"])
            z["game_id"]=gid
            shots.extend(z.to_dict("records"))
            entry.update({"shot_events":len(z),"goal_events":int(z.goal.sum()),
                "missing_shooter":int(z.player_id.isna().sum()),
                "unmatched_shooter":int((~z.player_id.isin(known)).sum()),
                "missing_geometry":int(z.distance.isna().sum()),
                "missing_strength":int(z.skater_advantage.isna().sum()),
                "missing_shot_type":int(z.shot_type.isna().sum()),
                "missing_goalie_state":int(z.opponent_goalie_present.isna().sum())})
        except Exception as e:
            entry["pbp_error"]=str(e)
        stats=probe_stats(gid)
        schemas.append({"game_id":gid,"season":str(g.season),"reports":stats})
        for name,d in stats.items():
            entry[name+"_rows"]=d.get("rows",0)
            entry[name+"_pp_keys"]="|".join(k for k in d.get("keys",[]) if "pp" in k.lower() or "powerplay" in k.lower())
        rows.append(entry)
    pd.DataFrame(rows).to_csv(out/"coverage.csv",index=False)
    pd.DataFrame(shots).to_parquet(out/"sample_shots.parquet",index=False)
    (out/"schemas.json").write_text(json.dumps(schemas,indent=2))
    print("=== SOURCE COVERAGE ===")
    print(pd.DataFrame(rows).to_csv(index=False))
    print("=== STATS SCHEMAS ===")
    print(json.dumps(schemas[:2],indent=2))
    print("=== END SOURCE AUDIT ===")
if __name__=="__main__":
    main()
