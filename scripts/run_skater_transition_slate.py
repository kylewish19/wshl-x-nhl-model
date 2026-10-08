from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd
import requests

from run_skater_transition_board import (
    SEASONS,
    WEB_BASE,
    fallback_rate,
    get_season_stats,
    norm_name,
)
from wshlx_nhl.bootstrap_models import build_skater_transitions, train_transition_rate_model
from wshlx_nhl.distributions import prob_at_least


def _local(v):
    if isinstance(v, dict):
        return v.get("default") or v.get("en") or next(iter(v.values()), "")
    return v or ""


def current_roster(team: str) -> list[dict]:
    for url in [f"{WEB_BASE}/roster-current/{team}", f"{WEB_BASE}/roster/{team}/20262027"]:
        r = requests.get(url, timeout=30, headers={"User-Agent":"wshlx-nhl-model/skater-slate"})
        if not r.ok:
            continue
        out=[]
        payload=r.json()
        for group in ["forwards","defensemen"]:
            for p in payload.get(group,[]):
                pid=p.get("id") or p.get("playerId")
                name=f"{_local(p.get('firstName'))} {_local(p.get('lastName'))}".strip()
                pos=p.get("positionCode") or p.get("position") or ""
                if pid and name:
                    out.append({"player_id":int(pid),"player_name":name,"team":team,"positionCode":pos})
        if out:
            return out
    return []


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--games", required=True)
    ap.add_argument("--predictions", required=True)
    ap.add_argument("--metrics", required=True)
    args=ap.parse_args()

    games=pd.read_csv(args.games)
    teams=sorted(set(games["away"]).union(set(games["home"])))
    frames={s:get_season_stats(s) for s in SEASONS}
    transitions=build_skater_transitions([frames[s] for s in SEASONS[:-1]], min_games=10)
    models={
        "goals":train_transition_rate_model(transitions,"next_goals_pg",alpha_grid=(10.0,)),
        "assists":train_transition_rate_model(transitions,"next_assists_pg",alpha_grid=(0.3,)),
        "points":train_transition_rate_model(transitions,"next_points_pg",alpha_grid=(0.3,)),
    }
    prior=frames[20252026].copy(); prior["playerId"]=prior["playerId"].astype(int)
    current=frames[20262027].copy(); current["playerId"]=current["playerId"].astype(int)

    roster=[]
    for team in teams:
        roster.extend(current_roster(team))

    rows=[]
    for p in roster:
        pid=int(p["player_id"]); team=p["team"]; name=p["player_name"]
        pprev=prior[prior["playerId"].eq(pid)]
        pcur=current[current["playerId"].eq(pid)]
        pos=str(pprev.iloc[0]["positionCode"]) if not pprev.empty else (str(pcur.iloc[0]["positionCode"]) if not pcur.empty else p.get("positionCode"))
        rates={}; bases={}
        for key,target,model_key in [("goal","next_goals_pg","goals"),("assist","next_assists_pg","assists"),("point","next_points_pg","points")]:
            if not pprev.empty and float(pprev.iloc[0]["gamesPlayed"])>=10:
                mu=float(models[model_key].predict(pprev.iloc[[0]])[0]); basis="transition_ml_anchor"
            else:
                mu=fallback_rate(pcur, prior, target, pos); basis="limited_history_fallback_reconstruction"
            rates[key]=mu; bases[key]=basis
        specs=[
            ("anytime_goal", rates["goal"], 1, bases["goal"]),
            ("anytime_assist", rates["assist"], 1, bases["assist"]),
            ("point_1plus", rates["point"], 1, bases["point"]),
            ("point_2plus", rates["point"], 2, bases["point"]),
        ]
        for market,mu,k,basis in specs:
            rows.append({"player_id":pid,"player_name":name,"team":team,"market":market,"expected_count":mu,"model_probability":float(prob_at_least(k,mu,None)),"model_basis":basis})

    out=pd.DataFrame(rows)
    Path(args.predictions).parent.mkdir(parents=True,exist_ok=True)
    out.to_csv(args.predictions,index=False)
    metrics={"teams":teams,"roster_players":len(roster),"rows_scored":len(out),"transition_rows":len(transitions),"validation_mae":{k:float(v.validation_mae) for k,v in models.items()},"alpha":{k:float(v.alpha) for k,v in models.items()}}
    Path(args.metrics).write_text(json.dumps(metrics,indent=2))
    print(out.sort_values("model_probability",ascending=False).head(60).to_string(index=False))
    print(json.dumps(metrics,indent=2))

if __name__=="__main__":
    main()
