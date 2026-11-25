"""Frozen ATG research scoring. Never modifies official cards."""
from __future__ import annotations
import numpy as np
import pandas as pd
from .atg_game_shadow import FEATURES
from .odds import american_to_implied, expected_roi

MODELS = ["official_probability", "shot_probability", "boosting_calibrated"]

def pregame_features(history: pd.DataFrame, board: pd.DataFrame, target_date: str) -> pd.DataFrame:
    h = history.copy()
    h["date"] = pd.to_datetime(h.date).dt.normalize()
    target = pd.Timestamp(target_date)
    if h.empty or h.date.ge(target).any():
        raise ValueError("History must be strictly before target")
    if h.duplicated(["game_id","player_id"]).any() or h.duplicated(["date","player_id"]).any():
        raise ValueError("Duplicate history")
    if board.duplicated(["game","player_id"]).any() or board.player_id.duplicated().any():
        raise ValueError("Duplicate board identity")
    h = h.sort_values(["date","game_id"])
    t = h.groupby(["date","game_id","team","opponent"],as_index=False).agg(sf=("shots","sum"),gf=("goals","sum"))
    t = t.merge(t[["game_id","team","sf","gf"]].rename(columns={"team":"opponent","sf":"sa","gf":"ga"}),on=["game_id","opponent"],validate="one_to_one")
    if t.duplicated(["date","team"]).any():
        raise ValueError("Duplicate team history")
    tg = {team:g.sort_values(["date","game_id"]).tail(20) for team,g in t.groupby("team")}
    pg = {int(pid):g for pid,g in h.groupby("player_id")}
    rows=[]
    for r in board.itertuples(index=False):
        g=pg.get(int(r.player_id),h.iloc[:0])
        gp=len(g)
        pos=getattr(r,"position",None)
        if pos not in ("F","D"):
            pos=g.iloc[-1].position if gp else None
        if pos not in ("F","D"):
            raise ValueError(f"Unverified position: {r.player_id}")
        defense=int(pos=="D")
        prior_shots=1.5 if defense else 2.
        prior_finish=.05 if defense else .11
        own=tg.get(r.team,t.iloc[:0])
        opp=tg.get(r.opponent,t.iloc[:0])
        def mean(frame,col,n=20):
            return float(frame[col].tail(n).mean()) if len(frame) else np.nan
        n=min(gp,20)
        goals20=mean(g,"goals")
        shots20=mean(g,"shots")
        finish=(g.goals.sum()+50*prior_finish)/(g.shots.sum()+50)
        opp_sa=mean(opp,"sa")
        matchup=float(np.clip((opp_sa if np.isfinite(opp_sa) else 30)/30,.75,1.25))
        rate=((goals20 if gp else 0)*n+12*prior_shots*prior_finish)/(n+12)
        shots=((shots20 if gp else 0)*n+8*prior_shots)/(n+8)
        rows.append({"is_home":int(r.is_home),"is_defense":defense,"prior_gp":gp,
            "rest_days":float(np.clip((target-g.date.iloc[-1]).days,1,30)) if gp else 7.,
            "shots_r5":mean(g,"shots",5),"shots_r20":shots20,
            "toi_r5":mean(g,"toi_seconds",5),"toi_r20":mean(g,"toi_seconds"),
            "goals_r20":goals20,"pp_goals_r20":mean(g,"pp_goals"),
            "career_shooting_shrunk":float(finish),
            "opponent_sa_r20":opp_sa,"opponent_ga_r20":mean(opp,"ga"),"team_sf_r20":mean(own,"sf"),
            "baseline_probability":float(-np.expm1(-rate)),
            "shot_probability":float(-np.expm1(-shots*finish*matchup))})
    return pd.DataFrame(rows,columns=FEATURES,index=board.index)

def predict(history, board, target_date, bundle):
    features=pregame_features(history,board,target_date)
    raw=bundle["model"].predict_proba(features[FEATURES])[:,1]
    p=np.clip(raw,1e-6,1-1e-6)
    cal=bundle["calibrator"].predict_proba(np.log(p/(1-p)).reshape(-1,1))[:,1]
    return features.assign(boosting_probability=raw,boosting_calibrated=cal)

def price_comparison(predictions, prices, edge_floor=.05, ev_floor=.05):
    keys=["date","game","player_id"]
    if predictions.duplicated(keys).any() or prices.duplicated(keys).any():
        raise ValueError("Duplicate price join")
    d=predictions.merge(prices[keys+["odds_american"]],on=keys,how="left",validate="one_to_one")
    d["odds_american"]=pd.to_numeric(d.odds_american,errors="coerce")
    if d.odds_american.isna().any() or (~np.isfinite(d.odds_american)).any() or d.odds_american.abs().lt(100).any():
        raise ValueError("Missing or invalid FanDuel price")
    d["implied_probability"]=d.odds_american.map(american_to_implied)
    for m in MODELS:
        d[m+"_edge"]=d[m]-d.implied_probability
        d[m+"_ev"]=[expected_roi(p,o) for p,o in zip(d[m],d.odds_american)]
        d[m+"_qualifies"]=d[m+"_edge"].ge(edge_floor)&d[m+"_ev"].ge(ev_floor)
    return d
