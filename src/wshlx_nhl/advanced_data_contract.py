"""Offline import contract for synthetic or explicitly authorized advanced data.
No provider credentials, network access, or production predictions.
"""
from pathlib import Path
import hashlib,json
import numpy as np
import pandas as pd
from .advanced_shot_research import validate_shots,aggregate_usage,chronological_xg,lagged_usage,require,KEYS

TABLES=("shots","participants","pp","reference","games")
def sha(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""):h.update(chunk)
    return h.hexdigest()

def load_bundle(root,allow_authorized=False):
    root=Path(root).resolve()
    m=json.loads((root/"manifest.json").read_text())
    require(m.get("schema_version")==1,"Unknown schema")
    require(m.get("scope") in ("SYNTHETIC","AUTHORIZED_RESEARCH"),"Missing data-use scope")
    if m["scope"]=="AUTHORIZED_RESEARCH":
        require(allow_authorized and bool(m.get("rights_reference")) and bool(m.get("provider")),"Explicit authorization and rights record required")
    require(m.get("time_unit")=="seconds" and m.get("distance_unit")=="feet" and m.get("angle_unit")=="degrees","Unsupported units")
    require(set(m["tables"])==set(TABLES),"Missing or unexpected table")
    data={}
    for n in TABLES:
        e=m["tables"][n];p=root/(n+".csv")
        require(p.resolve().parent==root,"Input outside bundle")
        require(sha(p)==e["sha256"],"Input hash mismatch: "+n)
        d=pd.read_csv(p)
        require(len(d)==e["rows"],"Input row count mismatch: "+n)
        data[n]=d
    return m,data

def reconcile(data):
    """Reference table must be independently sourced, including zero rows.
    Reject entire incomplete bundle rather than silently dropping games.
    """
    s=validate_shots(data["shots"])
    p=data["participants"].copy();u=data["pp"].copy();r=data["reference"].copy();g=data["games"].copy()
    require({"date","game_id","home","away","final"}<=set(g),"Missing expected schedule fields")
    require({"date","game_id","player_id","team","toi_seconds"}<=set(p),"Missing participant fields")
    require({"game_id","player_id","pp_toi_seconds"}<=set(u),"Missing PP fields")
    require({"game_id","player_id","goals","shots_on_goal","unblocked_attempts"}<=set(r),"Missing independent reference counts")
    require("kind" in s and s.kind.isin(["goal","shot-on-goal","missed-shot"]).all(),"Unsupported attempt type")
    require(s.goal.eq(s.kind.eq("goal").astype(int)).all(),"Goal event mismatch")
    for d in (g,p):
        d["date"]=pd.to_datetime(d.date).dt.normalize()
        require(d.date.notna().all(),"Missing date")
    require(not g.empty and not g.game_id.duplicated().any() and g.final.eq(1).all() and g.home.ne(g.away).all(),"Invalid expected completed schedule")
    require(g[["game_id","home","away"]].notna().all().all(),"Missing game identity")
    require(not p.duplicated(KEYS).any() and not p.duplicated(["date","player_id"]).any(),"Duplicate participants")
    require(p[KEYS+["team"]].notna().all().all() and np.isfinite(p.toi_seconds).all() and p.toi_seconds.gt(0).all(),"Invalid participant identity/time")
    for d in (p,u,r,s):
        require(set(d.game_id)==set(g.game_id),"Incomplete or extra game coverage")
    for d in (u,r):
        require(not d.duplicated(KEYS).any() and set(map(tuple,d[KEYS].to_numpy()))==set(map(tuple,p[KEYS].to_numpy())),"Incomplete or extra participant coverage")
    j=p.merge(g[["game_id","date","home","away"]],on="game_id",suffixes=("","_expected"),validate="many_to_one")
    require(j.date.eq(j.date_expected).all() and (j.team.eq(j.home)|j.team.eq(j.away)).all(),"Participant schedule mismatch")
    require(j.groupby("game_id").team.nunique().eq(2).all(),"Missing team participants")
    # Both clubs must have independently documented skater rows; no guessed zeros.
    z=s.merge(p[KEYS+["date","team"]],on=KEYS,how="left",suffixes=("","_participant"),validate="many_to_one")
    require(z.team.eq(z.team_participant).all() and z.date.eq(z.date_participant).all(),"Shot identity mismatch")
    p=p.merge(u[KEYS+["pp_toi_seconds"]],on=KEYS,validate="one_to_one")
    require(np.isfinite(p.pp_toi_seconds).all() and p.pp_toi_seconds.ge(0).all() and p.pp_toi_seconds.le(p.toi_seconds).all(),"Invalid PP seconds")
    counts=["goals","shots_on_goal","unblocked_attempts"]
    for n in counts:require(np.isfinite(r[n]).all() and r[n].ge(0).all() and r[n].mod(1).eq(0).all(),"Invalid independent count")
    require(r.goals.le(r.shots_on_goal).all() and r.shots_on_goal.le(r.unblocked_attempts).all(),"Invalid reference hierarchy")
    s["on_goal"]=s.kind.ne("missed-shot").astype(int)
    observed=s.groupby(KEYS).agg(goals=("goal","sum"),shots_on_goal=("on_goal","sum"),unblocked_attempts=("goal","size")).reset_index()
    q=r.merge(observed,on=KEYS,how="left",suffixes=("_reference","_observed"),validate="one_to_one")
    for n in counts:require(q[n+"_reference"].eq(q[n+"_observed"].fillna(0)).all(),"Independent count mismatch: "+n)
    return {"games":len(g),"participants":len(p),"attempts":len(s),"goals":int(s.goal.sum()),"pp_zero_rows":int(p.pp_toi_seconds.eq(0).sum()),"status":"COUNTS_RECONCILED"}

def build_research(data,cutoffs):
    report=reconcile(data)
    x=chronological_xg(data["shots"],cutoffs)
    usage=aggregate_usage(x,data["participants"],data["pp"],data["games"].game_id)
    features=lagged_usage(usage)
    report.update(scored_attempts=int(x.xg.notna().sum()),unscored_attempts=int(x.xg.isna().sum()),feature_rows=len(features))
    return report,features
