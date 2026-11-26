"""Offline research-only shot quality and usage features.
Inputs must be synthetic or appropriately authorized, normalized completed-game tables.
No network calls, no official model changes.
"""
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder,StandardScaler
from sklearn.pipeline import make_pipeline
from sklearn.linear_model import LogisticRegression

SHOT_FEATURES=["distance","angle","skater_advantage","shot_type"]
KEYS=["game_id","player_id"]
def require(ok,msg):
    if not ok:raise ValueError(msg)

def validate_shots(shots):
    d=shots.copy()
    fields={"date","game_id","event_id","player_id","team","goal","distance","angle","skater_advantage","shot_type","opponent_goalie_present","penalty_shot"}
    require(fields<=set(d),"Missing normalized shot fields")
    d["date"]=pd.to_datetime(d.date).dt.normalize()
    require(d.date.notna().all() and not d.duplicated(["game_id","event_id"]).any(),"Missing date or duplicate shot")
    require(d[["game_id","player_id","team"]].notna().all().all(),"Missing shot identity")
    require(d.goal.isin([0,1]).all() and d.opponent_goalie_present.isin([0,1]).all() and d.penalty_shot.isin([0,1]).all(),"Invalid shot flags")
    require(d.distance.between(0,200).all() and d.angle.between(0,180).all() and d.skater_advantage.between(-5,5).all(),"Invalid shot geometry or strength")
    require(d.shot_type.notna().all(),"Missing shot type")
    return d

def chronological_xg(shots,cutoffs):
    """Each held-out interval is scored by a model fit strictly before its start.
    Earliest warm-up rows and empty-net/penalty-shot attempts receive no xG.
    Input excludes shootouts and blocked shots. No post-shot inputs.
    """
    d=validate_shots(shots)
    d["xg"]=np.nan;d["xg_train_end"]=pd.NaT
    defended=d.opponent_goalie_present.eq(1)&d.penalty_shot.eq(0)
    boundaries=[pd.Timestamp(x) for x in cutoffs]
    require(len(boundaries)>=2 and boundaries==sorted(set(boundaries)),"Invalid chronological cutoffs")
    for start,end in zip(boundaries[:-1],boundaries[1:]):
        train=d[defended&d.date.lt(start)]
        test=d[defended&d.date.ge(start)&d.date.lt(end)]
        if test.empty:continue
        require(train.goal.nunique()==2,"Insufficient earlier shot labels")
        pre=ColumnTransformer([("numeric",StandardScaler(),SHOT_FEATURES[:3]),("type",OneHotEncoder(handle_unknown="ignore"),["shot_type"])])
        model=make_pipeline(pre,LogisticRegression(max_iter=1000,random_state=42))
        model.fit(train[SHOT_FEATURES],train.goal)
        d.loc[test.index,"xg"]=model.predict_proba(test[SHOT_FEATURES])[:,1]
        d.loc[test.index,"xg_train_end"]=train.date.max()
    return d

def aggregate_usage(shots,participants,pp,complete_games):
    """Only complete, independently reconciled games can imply zero attempts.
    PP report must cover all participants, including explicit zero rows.
    xG is null if any defended attempt lacks a chronological estimate.
    """
    s=validate_shots(shots)
    p=participants.copy();u=pp.copy()
    require({"date","game_id","player_id","team","toi_seconds"}<=set(p),"Missing participant fields")
    require({"game_id","player_id","pp_toi_seconds"}<=set(u),"Missing PP fields")
    p["date"]=pd.to_datetime(p.date).dt.normalize()
    require(not p.duplicated(KEYS).any() and not p.duplicated(["date","player_id"]).any() and not u.duplicated(KEYS).any(),"Duplicate participant or PP row")
    require(p.date.notna().all() and p.toi_seconds.gt(0).all(),"Invalid participation")
    p=p[p.game_id.isin(complete_games)].copy();u=u[u.game_id.isin(complete_games)]
    require(set(map(tuple,p[KEYS].to_numpy()))==set(map(tuple,u[KEYS].to_numpy())),"Incomplete or extra PP identities")
    p=p.merge(u[KEYS+["pp_toi_seconds"]],on=KEYS,validate="one_to_one")
    require(p.pp_toi_seconds.ge(0).all() and p.pp_toi_seconds.le(p.toi_seconds).all(),"Invalid PP time")
    s=s[s.game_id.isin(complete_games)].copy()
    j=s.merge(p[KEYS+["team","date"]],on=KEYS,how="left",suffixes=("","_participant"),validate="many_to_one")
    require(j.team.eq(j.team_participant).all() and j.date.eq(j.date_participant).all(),"Shot/participant identity mismatch")
    require("xg" in s and "xg_train_end" in s,"Missing cross-fit provenance")
    valid=s.xg.notna()
    require(s.loc[valid,"xg"].between(0,1).all() and pd.to_datetime(s.loc[valid,"xg_train_end"]).lt(s.loc[valid,"date"]).all(),"Invalid or future xG provenance")
    defended=s.opponent_goalie_present.eq(1)&s.penalty_shot.eq(0)
    s=s[defended].copy()
    s["pp_attempt"]=s.skater_advantage.gt(0).astype(int)
    s["high_danger_proxy"]=np.where(s.xg.notna(),s.xg.ge(.20).astype(float),np.nan)
    z=s.groupby(KEYS).agg(attempts=("goal","size"),xg_count=("xg","count"),ixg=("xg","sum"),pp_attempts=("pp_attempt","sum"),danger_attempts=("high_danger_proxy","sum")).reset_index()
    z.loc[z.xg_count.ne(z.attempts),["ixg","danger_attempts"]]=np.nan
    p=p.merge(z,on=KEYS,how="left",validate="one_to_one")
    no_attempt=p.attempts.isna()
    p.loc[no_attempt,["attempts","xg_count","ixg","pp_attempts","danger_attempts"]]=0
    return p

def lagged_usage(games,windows=(5,20)):
    """All rolling features strictly lag actual usage; no same-day results."""
    d=games.copy()
    d["date"]=pd.to_datetime(d.date).dt.normalize()
    require(d.date.notna().all() and not d.duplicated(["date","player_id"]).any(),"Duplicate dated player rows")
    d=d.sort_values(["date","game_id","player_id"])
    g=d.groupby("player_id",sort=False)
    for n in windows:
        require(isinstance(n,int) and n>0,"Invalid rolling window")
        for col in ["attempts","ixg","pp_attempts","danger_attempts","pp_toi_seconds"]:
            d[col+f"_r{n}"]=g[col].transform(lambda x:x.shift().rolling(n,min_periods=1).mean())
            d[col+f"_valid_r{n}"]=g[col].transform(lambda x:x.shift().rolling(n,min_periods=1).count())
    return d
