from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import unicodedata

import numpy as np
import pandas as pd
import requests

from wshlx_nhl.bootstrap_models import build_skater_transitions, train_transition_rate_model
from wshlx_nhl.distributions import prob_at_least

STATS_BASE = "https://api.nhle.com/stats/rest/en"
WEB_BASE = "https://api-web.nhle.com/v1"
SEASONS = [20212022, 20222023, 20232024, 20242025, 20252026, 20262027]


def norm_name(value: str) -> str:
    s = unicodedata.normalize("NFKD", str(value)).encode("ascii", "ignore").decode("ascii").casefold()
    return re.sub(r"[^a-z0-9]+", " ", s).strip()


def get_season_stats(season: int) -> pd.DataFrame:
    url=f"{STATS_BASE}/skater/summary"; rows=[]; start=0
    while True:
        params={"isAggregate":"false","isGame":"false","sort":'[{"property":"points","direction":"DESC"}]',"start":start,"limit":100,"cayenneExp":f"gameTypeId=2 and seasonId={season}"}
        r=requests.get(url,params=params,timeout=60,headers={"User-Agent":"wshlx-nhl-model/skater-transition"}); r.raise_for_status(); payload=r.json(); page=payload.get("data",[])
        if not page: break
        rows.extend(page); start+=len(page); total=payload.get("total")
        if total is not None and start>=int(total): break
        if len(page)<100: break
        if start>5000: raise RuntimeError(f"Unexpected pagination runaway for season {season}")
    df=pd.DataFrame(rows).drop_duplicates(subset=["playerId"],keep="first")
    if df.empty: raise RuntimeError(f"No skater data returned for {season}")
    for src,dst in {"powerPlayGoals":"ppGoals","powerPlayPoints":"ppPoints"}.items():
        if src in df.columns and dst not in df.columns: df[dst]=df[src]
    required=["playerId","gamesPlayed","goals","assists","points","shots","ppGoals","ppPoints","timeOnIcePerGame","shootingPct","positionCode"]
    missing=[c for c in required if c not in df.columns]
    if missing: raise RuntimeError(f"Season {season} missing fields {missing}")
    return df[required+[c for c in ["skaterFullName","teamAbbrevs"] if c in df.columns]].copy()


def roster_map(team: str) -> dict[str,int]:
    out={}
    for url in [f"{WEB_BASE}/roster-current/{team}",f"{WEB_BASE}/roster/{team}/20262027"]:
        r=requests.get(url,timeout=30,headers={"User-Agent":"wshlx-nhl-model/skater-transition"})
        if not r.ok: continue
        for group in ["forwards","defensemen"]:
            for p in r.json().get(group,[]):
                first=p.get("firstName",{}); last=p.get("lastName",{})
                if isinstance(first,dict): first=first.get("default") or first.get("en") or ""
                if isinstance(last,dict): last=last.get("default") or last.get("en") or ""
                pid=p.get("id") or p.get("playerId"); key=norm_name(f"{first} {last}")
                if key and pid: out[key]=int(pid)
        if out: break
    return out


def fallback_rate(current_row: pd.DataFrame, prior: pd.DataFrame, target: str, pos: str|None) -> float:
    rate_col={"next_goals_pg":"goals","next_assists_pg":"assists","next_points_pg":"points"}[target]; med=prior.copy()
    if pos and "positionCode" in med.columns:
        same=med[med["positionCode"].eq(pos)]
        if len(same)>=20: med=same
    league_rate=float((med[rate_col]/med["gamesPlayed"].clip(lower=1)).median())
    if current_row.empty: return max(0.0,league_rate)
    gp=float(current_row.iloc[0]["gamesPlayed"] or 0); cnt=float(current_row.iloc[0][rate_col] or 0)
    return max(0.0,(cnt+5.0*league_rate)/max(gp+5.0,1.0))


def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--board",required=True); ap.add_argument("--predictions",required=True); ap.add_argument("--metrics",required=True); args=ap.parse_args()
    frames={s:get_season_stats(s) for s in SEASONS}; transitions=build_skater_transitions([frames[s] for s in SEASONS[:-1]],min_games=10)
    models={"goals":train_transition_rate_model(transitions,"next_goals_pg",alpha_grid=(10.0,)),"assists":train_transition_rate_model(transitions,"next_assists_pg",alpha_grid=(0.3,)),"points":train_transition_rate_model(transitions,"next_points_pg",alpha_grid=(0.3,))}
    board=pd.read_csv(args.board); rosters={t:roster_map(t) for t in sorted(board["team"].dropna().unique())}
    prior=frames[20252026].copy(); prior["playerId"]=prior["playerId"].astype(int); current=frames[20262027].copy(); current["playerId"]=current["playerId"].astype(int)
    rows=[]
    for _,r in board.iterrows():
        name=str(r["player_name"]); listed_team=str(r["team"]); key=norm_name(name); pid=rosters.get(listed_team,{}).get(key); resolved_team=listed_team
        if not pid:
            hits=[(t,m[key]) for t,m in rosters.items() if key in m]
            if len(hits)==1: resolved_team,pid=hits[0]
        pprev=prior[prior["playerId"].eq(pid)] if pid else prior.iloc[0:0]; pcur=current[current["playerId"].eq(pid)] if pid else current.iloc[0:0]
        pos=str(pprev.iloc[0]["positionCode"]) if not pprev.empty else (str(pcur.iloc[0]["positionCode"]) if not pcur.empty else None)
        pred_rates={}; bases={}
        for k,target in [("goal","next_goals_pg"),("assist","next_assists_pg"),("point","next_points_pg")]:
            model=models[{"goal":"goals","assist":"assists","point":"points"}[k]]
            if not pprev.empty and float(pprev.iloc[0]["gamesPlayed"])>=10: mu=float(model.predict(pprev.iloc[[0]])[0]); basis="transition_ml_anchor"
            else: mu=fallback_rate(pcur,prior,target,pos); basis="limited_history_fallback_reconstruction"
            pred_rates[k]=mu; bases[k]=basis
        market=str(r["market"])
        if market=="anytime_goal": mu=pred_rates["goal"]; p=float(prob_at_least(1,mu,None)); basis=bases["goal"]
        elif market=="anytime_assist": mu=pred_rates["assist"]; p=float(prob_at_least(1,mu,None)); basis=bases["assist"]
        elif market=="point_1plus": mu=pred_rates["point"]; p=float(prob_at_least(1,mu,None)); basis=bases["point"]
        elif market=="point_2plus": mu=pred_rates["point"]; p=float(prob_at_least(2,mu,None)); basis=bases["point"]
        else: raise ValueError(f"Unsupported market {market}")
        d=r.to_dict(); d["listed_team"]=listed_team; d["resolved_team"]=resolved_team; d["player_id"]=pid; d["expected_count"]=mu; d["model_probability"]=p; d["model_basis"]=basis; rows.append(d)
    out=pd.DataFrame(rows); Path(args.predictions).parent.mkdir(parents=True,exist_ok=True); out.to_csv(args.predictions,index=False)
    metrics={"transition_rows":int(len(transitions)),"season_row_counts":{str(s):int(len(frames[s])) for s in SEASONS},"validation_mae":{k:float(v.validation_mae) for k,v in models.items()},"alpha":{k:float(v.alpha) for k,v in models.items()},"unresolved_player_rows":int(out["player_id"].isna().sum()),"roster_reassigned_rows":int((out["listed_team"]!=out["resolved_team"]).sum()),"rows_scored":int(len(out))}
    Path(args.metrics).write_text(json.dumps(metrics,indent=2)); print(out.to_string(index=False)); print(json.dumps(metrics,indent=2))

if __name__=="__main__": main()
