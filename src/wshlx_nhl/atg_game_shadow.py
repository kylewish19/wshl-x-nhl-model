"""ATG game-level research. No sportsbook prices or same-game inputs in features."""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss, log_loss, roc_auc_score

FEATURES = [
    "is_home", "is_defense", "prior_gp", "rest_days",
    "shots_r5", "shots_r20", "toi_r5", "toi_r20",
    "goals_r20", "pp_goals_r20", "career_shooting_shrunk",
    "opponent_sa_r20", "opponent_ga_r20", "team_sf_r20",
    "baseline_probability", "shot_probability",
]


def build_features(raw: pd.DataFrame) -> pd.DataFrame:
    d = raw.copy()
    required = {"date","game_id","player_id","team","opponent","position","is_home","goals","shots","toi_seconds","pp_goals"}
    if not required.issubset(d.columns):
        raise ValueError(f"Missing {sorted(required-set(d.columns))}")
    d["date"] = pd.to_datetime(d["date"]).dt.normalize()
    if d.duplicated(["game_id","player_id"]).any() or d.duplicated(["date","player_id"]).any():
        raise ValueError("Duplicate player-game or same-day player rows")
    if (d[["goals","shots","toi_seconds","pp_goals"]]<0).any().any() or (d.goals>d.shots).any():
        raise ValueError("Invalid skater counts")
    d = d.sort_values(["date","game_id","player_id"]).reset_index(drop=True)
    d["is_defense"] = d.position.eq("D").astype(int)
    # Opponent and own team histories are derived from earlier completed games.
    t = d.groupby(["date","game_id","team","opponent"],as_index=False).agg(sf=("shots","sum"),gf=("goals","sum"))
    opp = t[["game_id","team","sf","gf"]].rename(columns={"team":"opponent","sf":"sa","gf":"ga"})
    t = t.merge(opp,on=["game_id","opponent"],validate="one_to_one")
    if t.duplicated(["date","team"]).any():
        raise ValueError("Same-day team duplicates")
    t = t.sort_values(["date","game_id"])
    for col in ["sf","sa","ga"]:
        t[col+"_r20"] = t.groupby("team")[col].transform(lambda x:x.shift().rolling(20,min_periods=1).mean())
    d = d.merge(t[["game_id","team","sf_r20"]],on=["game_id","team"],validate="many_to_one")
    d = d.merge(t[["game_id","team","sa_r20","ga_r20"]].rename(columns={"team":"opponent","sa_r20":"opponent_sa_r20","ga_r20":"opponent_ga_r20"}),on=["game_id","opponent"],validate="many_to_one")
    d = d.rename(columns={"sf_r20":"team_sf_r20"}).sort_values(["date","game_id","player_id"]).reset_index(drop=True)
    g = d.groupby("player_id",sort=False)
    d["prior_gp"] = g.cumcount()
    d["rest_days"] = (d.date-g.date.shift()).dt.days.clip(1,30).fillna(7)
    for c, windows in [("shots",[5,20]),("toi_seconds",[5,20]),("goals",[20]),("pp_goals",[20])]:
        for n in windows:
            out = "toi" if c=="toi_seconds" else c
            d[out+f"_r{n}"] = g[c].transform(lambda x:x.shift().rolling(n,min_periods=1).mean())
    prev_goals = g.goals.cumsum()-d.goals
    prev_shots = g.shots.cumsum()-d.shots
    # Fixed, explicit shrinkage priors, not estimated on test outcomes.
    prior_shots = np.where(d.is_defense.eq(1),1.5,2.0)
    prior_finish = np.where(d.is_defense.eq(1),0.05,0.11)
    d["career_shooting_shrunk"] = (prev_goals+50*prior_finish)/(prev_shots+50)
    prior_rate = prior_shots*prior_finish
    n = d.prior_gp.clip(upper=20)
    recent_goals = d.goals_r20.fillna(0)*n
    d["baseline_probability"] = -np.expm1(-(recent_goals+12*prior_rate)/(n+12))
    shot_rate = (d.shots_r20.fillna(0)*n+8*prior_shots)/(n+8)
    matchup = (d.opponent_sa_r20.fillna(30)/30).clip(.75,1.25)
    d["shot_probability"] = -np.expm1(-shot_rate*d.career_shooting_shrunk*matchup)
    d["target"] = d.goals.gt(0).astype(int)
    return d


def score(y, p):
    y = np.asarray(y,dtype=int)
    p = np.clip(np.asarray(p,dtype=float),1e-6,1-1e-6)
    return {"rows":len(y),"goalscorer_rate":float(y.mean()),"mean_probability":float(p.mean()),
            "brier":float(brier_score_loss(y,p)), "log_loss":float(log_loss(y,p,labels=[0,1])),
            "auc":float(roc_auc_score(y,p)) if len(np.unique(y))==2 else None}


def benchmark(features: pd.DataFrame):
    d = features.copy()
    date = pd.to_datetime(d.date)
    # First season provides warm-up; train through 2023-24, calibrate on
    # 2024-25, evaluate 2025-26 and 2026-27 separately, never tune on them.
    train = d[(date>="2022-07-01") & (date<"2024-07-01")]
    cal = d[(date>="2024-07-01") & (date<"2025-07-01")]
    tests = {"2025-26":d[(date>="2025-07-01") & (date<"2026-07-01")],
             "2026-27":d[date>="2026-07-01"]}
    if min(len(train),len(cal),*(len(x) for x in tests.values()))==0:
        raise ValueError("Missing chronological cohort")
    model = HistGradientBoostingClassifier(max_iter=150,max_leaf_nodes=15,learning_rate=.06,
                                             min_samples_leaf=100,l2_regularization=2,early_stopping=False,random_state=42)
    model.fit(train[FEATURES],train.target)
    def logits(p):
        p=np.clip(p,1e-6,1-1e-6)
        return np.log(p/(1-p)).reshape(-1,1)
    calibrator = LogisticRegression(C=1e3)
    calibrator.fit(logits(model.predict_proba(cal[FEATURES])[:,1]),cal.target)
    report = {"status":"SHADOW_ONLY","train_rows":len(train),"calibration_rows":len(cal),"tests":{}}
    predictions=[]
    for season, x in tests.items():
        raw = model.predict_proba(x[FEATURES])[:,1]
        calibrated = calibrator.predict_proba(logits(raw))[:,1]
        ps={"goal_rate_baseline":x.baseline_probability,"shot_finish_baseline":x.shot_probability,
            "boosting":raw,"boosting_calibrated":calibrated}
        report["tests"][season]={name:score(x.target,p) for name,p in ps.items()}
        out=x[["date","game_id","player_id","team","target","prior_gp"]].copy()
        for name,p in ps.items():
            out[name]=p
        out["season"]=season
        predictions.append(out)
    return report,pd.concat(predictions,ignore_index=True),model,calibrator
