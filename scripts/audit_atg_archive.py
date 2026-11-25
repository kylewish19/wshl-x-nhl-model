"""Audit the immutable first-run ATG artifact before any model fit.

A goals>shots discrepancy is not automatically a bad goal label. For the
research-only sensitivity run, use goals as a lower bound on shot count on
rare anomalous rows, retain an audit trail, and exclude those rows from
supervised training/evaluation. Never change the original artifact.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import joblib
import pandas as pd
from wshlx_nhl.atg_game_shadow import build_features, benchmark, score


def audit_counts(raw, out):
    cols = ["goals","shots","toi_seconds","pp_goals"]
    missing = raw[cols].isna().any(axis=1)
    negative = raw[cols].lt(0).any(axis=1)
    pp = raw.pp_goals.gt(raw.goals)
    bad = raw.goals.gt(raw.shots)
    issues = missing | negative | pp | bad
    out.mkdir(parents=True,exist_ok=True)
    raw.loc[issues].to_csv(out/"count_anomalies.csv",index=False)
    report = {"rows":len(raw),"games":int(raw.game_id.nunique()),
              "by_season":raw.groupby("season").game_id.nunique().to_dict(),
              "missing_counts":int(missing.sum()),"negative_counts":int(negative.sum()),
              "pp_goals_gt_goals":int(pp.sum()),"goals_gt_shots":int(bad.sum()),
              "goals_gt_shots_rate":float(bad.mean()),
              "anomalies_by_season":raw.loc[issues].groupby("season").size().to_dict(),
              "policy":"Only rare goals>shots discrepancies get a lower-bound shot proxy; all such rows excluded from fit and held-out scoring."}
    (out/"audit.json").write_text(json.dumps(report,indent=2))
    print("=== DATA AUDIT ===",flush=True)
    print(json.dumps(report,indent=2),flush=True)
    print(raw.loc[issues].head(25).to_string(index=False),flush=True)
    # Predeclared fail-closed limit, not selected using benchmark outcomes.
    if missing.any() or negative.any() or pp.any() or bad.mean()>.001:
        raise ValueError("Data audit failed: inspect count_anomalies.csv before training")
    repaired=raw.copy()
    repaired["count_anomaly"]=bad
    repaired.loc[bad,"shots"]=repaired.loc[bad,"goals"]
    return repaired, report


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--raw",required=True)
    ap.add_argument("--out-dir",required=True)
    args=ap.parse_args()
    out=Path(args.out_dir)
    raw=pd.read_parquet(args.raw)
    assert pd.to_datetime(raw.date).max()<pd.Timestamp("2026-11-25")
    assert raw.game_id.nunique()==6945
    repaired,audit=audit_counts(raw,out)
    features=build_features(repaired)
    valid=features.loc[~features.count_anomaly].copy()
    report,preds,model,calibrator=benchmark(valid)
    report["data_audit"]=audit
    report["excluded_supervised_rows"]=int(features.count_anomaly.sum())
    report["status"]="SHADOW_ONLY"
    report["scope"]="Actual participants; no historical prices or pregame roster reconstruction"
    preds=preds.merge(valid[["game_id","player_id","is_defense","toi_r20"]],on=["game_id","player_id"],validate="one_to_one")
    bands=[]
    models=["goal_rate_baseline","shot_finish_baseline","boosting","boosting_calibrated"]
    for season,x in preds.groupby("season"):
        cohorts={"all":x,"prior_gp_0_9":x[x.prior_gp<10],
                 "prior_gp_10_39":x[x.prior_gp.between(10,39)],
                 "prior_gp_40_plus":x[x.prior_gp>=40],
                 "defense":x[x.is_defense==1],"forward":x[x.is_defense==0]}
        for label,cohort in cohorts.items():
            if len(cohort):
                for name in models:
                    bands.append({"season":season,"band":label,"model":name,**score(cohort.target,cohort[name])})
        for name in models:
            for lo,hi in [(0,.1),(.1,.2),(.2,.3),(.3,.4),(.4,.5),(.5,1.01)]:
                z=x[x[name].ge(lo)&x[name].lt(hi)]
                if len(z):
                    bands.append({"season":season,"band":f"prob_{lo}_{hi}","model":name,**score(z.target,z[name])})
    pd.DataFrame(bands).to_csv(out/"bands.csv",index=False)
    preds.to_parquet(out/"heldout_predictions.parquet",index=False)
    joblib.dump({"model":model,"calibrator":calibrator},out/"atg_game_shadow.joblib")
    (out/"metrics.json").write_text(json.dumps(report,indent=2))
    print("=== BENCHMARK ===")
    print(json.dumps(report,indent=2))
    print("=== SUBGROUPS ===")
    print(pd.DataFrame(bands).to_csv(index=False))


if __name__=="__main__":
    main()
