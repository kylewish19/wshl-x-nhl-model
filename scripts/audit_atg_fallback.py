"""Historical fallback proxy and frozen Nov25 ATG diagnostics; no fitting."""
import argparse,json,hashlib
from pathlib import Path
import numpy as np
import pandas as pd
from wshlx_nhl.atg_game_shadow import score

MODELS=["fallback_proxy","shot_finish_baseline","boosting_calibrated","goal_rate_baseline"]

def fallback_proxy(raw):
    d=raw.copy()
    d["season"]=d.season.astype(str)
    d["date"]=pd.to_datetime(d.date)
    if d.duplicated(["game_id","player_id"]).any() or d.duplicated(["date","player_id"]).any():
        raise ValueError("Duplicate player games")
    if not d.position.isin(["F","D"]).all():raise ValueError("Unknown position")
    d=d.sort_values(["date","game_id","player_id"])
    season=d.groupby(["season","player_id"],as_index=False).agg(gp=("goals","size"),goals=("goals","sum"),pos=("position","last"))
    season["rate"]=season.goals/season.gp
    season["prior_season"]=season.season
    season["season"]=(season.season.astype(int)+10001).astype(str)
    med=season.groupby(["season","pos"]).rate.median()
    counts=season.groupby(["season","pos"]).rate.size()
    league=season.groupby("season").rate.median()
    d=d.merge(season[["season","player_id","gp","pos"]].rename(columns={"gp":"previous_season_gp","pos":"previous_position"}),on=["season","player_id"],how="left",validate="many_to_one")
    d["previous_season_gp"]=d.previous_season_gp.fillna(0)
    pos=d.previous_position.fillna(d.position)
    prior=[med.get((s,p),np.nan) if counts.get((s,p),0)>=20 else league.get(s,np.nan) for s,p in zip(d.season,pos)]
    d["position_prior"]=prior
    d=d.sort_values(["date","game_id","player_id"])
    g=d.groupby(["season","player_id"],sort=False)
    d["current_prior_gp"]=g.cumcount()
    d["current_prior_goals"]=g.goals.cumsum()-d.goals
    d["fallback_proxy"]=-np.expm1(-(d.current_prior_goals+5*d.position_prior)/(d.current_prior_gp+5))
    d["target"]=d.goals.gt(0).astype(int)
    return d

def history_audit(raw,pred):
    d=fallback_proxy(raw)
    d=d[d.previous_season_gp.lt(10)&d.season.isin(["20252026","20262027"])]
    x=d.merge(pred[["game_id","player_id","target","shot_finish_baseline","boosting_calibrated","goal_rate_baseline"]],on=["game_id","player_id"],suffixes=("","_frozen"),how="inner",validate="one_to_one")
    if not x.target.eq(x.target_frozen).all():raise ValueError("Outcome mismatch")
    if not x[MODELS].apply(lambda c:c.between(0,1)).all().all():raise ValueError("Invalid probability")
    rows=[]
    for season,z in x.groupby("season"):
        groups={"all_fallback":z,"prev_season_0":z[z.previous_season_gp.eq(0)],
            "prev_season_1_9":z[z.previous_season_gp.between(1,9)],
            "current_0_4":z[z.current_prior_gp.lt(5)],"current_5_14":z[z.current_prior_gp.between(5,14)],
            "current_15_plus":z[z.current_prior_gp.ge(15)],"defense":z[z.position.eq("D")],"forward":z[z.position.eq("F")],
            "proxy_20pct_plus":z[z.fallback_proxy.ge(.20)]}
        for label,b in groups.items():
            if not len(b):continue
            for model in MODELS:
                rows.append(dict(season=season,group=label,model=model,**score(b.target,b[model])))
    return pd.DataFrame(rows),x

def live_audit(core,graded):
    c=core[core.market.eq("anytime_goal")&core.active.eq(1)][["date","game","player_id","model_basis","model_probability"]].copy()
    k=["date","game","player_id"]
    z=graded.merge(c,on=k,how="left",validate="one_to_one")
    if z.model_basis.isna().any() or not np.allclose(z.official_probability,z.model_probability):raise ValueError("Basis or probability mismatch")
    z["fallback"]=z.model_basis.str.contains("limited_history_fallback",regex=False)
    z["hybrid_shot"]=np.where(z.fallback,z.shot_probability,z.official_probability)
    z["hybrid_boost"]=np.where(z.fallback,z.boosting_calibrated,z.official_probability)
    from wshlx_nhl.odds import american_to_implied,expected_roi,american_to_decimal
    models=["official_probability","shot_probability","boosting_calibrated","hybrid_shot","hybrid_boost"]
    imp=z.odds_american.map(american_to_implied)
    z["profit"]=np.where(z.result.eq("WIN"),z.odds_american.map(american_to_decimal)-1,np.where(z.result.eq("LOSS"),-1.,0.))
    reports=[]
    for label,b in [("all",z),("fallback",z[z.fallback]),("anchor",z[~z.fallback])]:
        for model in models:
            p=b[model];edge=p-imp.loc[b.index];ev=pd.Series([expected_roi(v,o) for v,o in zip(p,b.odds_american)],index=b.index)
            flag=edge.ge(.05)&ev.ge(.05)
            if model+"_qualifies" in b and not flag.eq(b[model+"_qualifies"]).all():raise ValueError("Frozen gate mismatch")
            q=b[flag];s=b[b.result.ne("VOID")]
            w=int(q.result.eq("WIN").sum());l=int(q.result.eq("LOSS").sum());net=float(q.profit.sum())
            reports.append(dict(group=label,model=model,matched=len(b),voids=int(b.result.eq("VOID").sum()),**score(s.target,s[model]),paper_count=len(q),wins=w,losses=l,paper_voids=len(q)-w-l,profit=net,roi=net/(w+l) if w+l else None))
            if label=="all":z[model+"_audit_gate"]=flag
    return pd.DataFrame(reports),z

def main():
    a=argparse.ArgumentParser()
    for n in ["raw","heldout","core","graded","out"]:a.add_argument("--"+n,required=True)
    p=a.parse_args();out=Path(p.out);out.mkdir(parents=True,exist_ok=True)
    assert hashlib.sha256(Path(p.raw).read_bytes()).hexdigest()=="5a782b58ddd7922c7820de4dc20262b348f2547a891e431441dddf5d6734ff2b"
    raw=pd.read_parquet(p.raw);pred=pd.read_parquet(p.heldout)
    hist,rows=history_audit(raw,pred)
    live,z=live_audit(pd.read_csv(p.core),pd.read_csv(p.graded))
    hist.to_csv(out/"historical.csv",index=False);live.to_csv(out/"nov25.csv",index=False)
    cols=["player_name","game","model_basis","odds_american","official_probability","shot_probability","boosting_calibrated","result"]
    cards=z[z.official_probability_audit_gate][cols]
    cards.to_csv(out/"nov25_official_atg_detail.csv",index=False)
    print("=== HISTORICAL FALLBACK PROXY ===");print(hist.to_csv(index=False),end="");print("=== END HISTORICAL ===")
    print("=== NOV25 BASIS AUDIT ===");print(live.to_csv(index=False),end="");print("=== END NOV25 ===")
    print("=== OFFICIAL PRICE DETAILS ===");print(cards.to_csv(index=False),end="");print("=== END DETAILS ===")
    meta=dict(status="RETROSPECTIVE_DIAGNOSTIC_ONLY",historical_rows=len(rows),history_cutoff=str(pd.to_datetime(raw.date).max().date()),nov25_matched_rows=len(z),notes=["Proxy uses F/D medians, not exact NHL C/L/R/D position codes; prior season boxscore totals, not official season endpoint. Actual participant cohort only. No historical odds.","Previous-season GP<10, not career GP<10; current-season counts lagged per player.","Shot and boosting probabilities reused from frozen heldout artifact; no fitting or tuning.","Nov25 hybrids are retrospective what-if comparisons, not newly locked picks. Excluded identities and DNP handled on common matched board."])
    (out/"manifest.json").write_text(json.dumps(meta,indent=2))
    print("=== AUDIT MANIFEST ===");print(json.dumps(meta,indent=2));print("=== END MANIFEST ===")

if __name__=="__main__":main()
