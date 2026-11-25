"""Matched ATG grading; no model fitting or price re-selection."""
from __future__ import annotations
import numpy as np
import pandas as pd
from .atg_pregame import MODELS
from .atg_game_shadow import score
from .odds import american_to_decimal

KEYS = ["date","game","player_id"]

def grade_matched(prices, outcomes, completed_games):
    p=prices.copy()
    o=outcomes.copy()
    if p.duplicated(KEYS).any() or o.duplicated(KEYS).any():
        raise ValueError("Duplicate player/game key")
    if not set(zip(p.date,p.game)).issubset(set(completed_games)):
        raise ValueError("Incomplete final games")
    if not p[MODELS].apply(lambda x:x.between(0,1)).all().all():
        raise ValueError("Invalid locked probability")
    if not p.odds_american.abs().ge(100).all():
        raise ValueError("Invalid locked price")
    if o.goals.isna().any() or o.goals.lt(0).any() or o.goals.mod(1).ne(0).any():
        raise ValueError("Invalid goal count")
    d=p.merge(o[KEYS+["team","goals"]].rename(columns={"team":"actual_team"}),on=KEYS,how="left",validate="one_to_one")
    # Outcomes contain only skaters with positive ice time. A missing player
    # in a verified complete final game is a paper DNP, not a scoring loss.
    played=d.goals.notna()
    if (played & d.team.ne(d.actual_team)).any():
        raise ValueError("Outcome team mismatch; review identity before grading")
    d["result"]=np.where(~played,"VOID",np.where(d.goals.gt(0),"WIN","LOSS"))
    d["target"]=np.where(played,d.goals.gt(0).astype(int),np.nan)
    profit=np.where(d.result.eq("WIN"),d.odds_american.map(american_to_decimal)-1,np.where(d.result.eq("LOSS"),-1,0))
    summaries=[]
    for m in MODELS:
        flag=d[m+"_qualifies"]
        if not flag.isin([True,False]).all():
            raise ValueError("Invalid frozen selection flag")
        flag=flag.astype(bool)
        d[m+"_paper_profit"]=np.where(flag,profit,0)
        ranked=d.sort_values([m,"game","player_id"],ascending=[False,True,True]).head(10)
        settled=d[d.result.ne("VOID")]
        q=d[flag]
        wins=int(q.result.eq("WIN").sum()); losses=int(q.result.eq("LOSS").sum())
        net=float(q[m+"_paper_profit"].sum())
        summaries.append({"model":m,"matched_rows":len(d),"settled_rows":len(settled),
            "void_rows":int(d.result.eq("VOID").sum()),
            **(score(settled.target,settled[m]) if len(settled) else {"brier":None,"log_loss":None,"auc":None}),
            "top10_wins":int(ranked.result.eq("WIN").sum()),"top10_losses":int(ranked.result.eq("LOSS").sum()),
            "top10_voids":int(ranked.result.eq("VOID").sum()),
            "paper_count":len(q),"paper_wins":wins,"paper_losses":losses,
            "paper_voids":int(q.result.eq("VOID").sum()),"paper_profit_units":net,
            "paper_roi":net/(wins+losses) if wins+losses else None})
    return d,pd.DataFrame(summaries)
