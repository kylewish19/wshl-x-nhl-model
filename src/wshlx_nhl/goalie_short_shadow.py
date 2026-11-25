"""Goalie short-start research using only archived, strictly prior inputs."""
import numpy as np
import pandas as pd
from scipy.stats import poisson, nbinom
from sklearn.pipeline import make_pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression, PoissonRegressor
from .atg_game_shadow import score

FEATURES=["is_home","rest_rebuilt","starts7_rebuilt","prior_starts","short_rate_prior",
          "team_shots_against_r5","team_shots_against_r10","opponent_shots_for_r5",
          "opponent_shots_for_r10","opponent_goals_for_r5","team_goals_against_r5",
          "save_pct_r5","save_pct_r10","goalie_shots_against_r5","goalie_shots_against_r10"]
LINES=[20.5,24.5,28.5]

def prepare(raw):
    d=raw.copy()
    d["date"]=pd.to_datetime(d.date).dt.normalize()
    d["season"]=d.season.astype(str)
    d["goalie_id"]=d.goalie_id.astype(str)
    if not d.goalie_id.str.fullmatch(r"\d+").all():
        raise ValueError("Unresolved goalie IDs")
    if d.duplicated(["game_id","team"]).any() or d.duplicated(["date","goalie_id"]).any():
        raise ValueError("Duplicate goalie start")
    if d[["toi_seconds","saves","shots_against"]].isna().any().any() or d.toi_seconds.le(0).any() or d.saves.lt(0).any() or d.saves.gt(d.shots_against).any():
        raise ValueError("Invalid goalie outcomes")
    d=d.sort_values(["goalie_id","date","game_id"]).reset_index(drop=True)
    d["short"]=(d.toi_seconds<3000).astype(int)
    g=d.groupby("goalie_id",sort=False)
    d["prior_starts"]=g.cumcount()
    d["rest_rebuilt"]=(d.date-g.date.shift()).dt.days.clip(0,30).fillna(7)
    d["short_rate_prior"]=(g.short.cumsum()-d.short+1)/(d.prior_starts+20)
    d["starts7_rebuilt"]=0
    for _,idx in g.groups.items():
        dates=d.loc[idx,"date"].to_numpy(dtype="datetime64[D]").astype("int64")
        n=np.arange(len(dates))-np.searchsorted(dates,dates-7,side="left")
        d.loc[idx,"starts7_rebuilt"]=n
    return d

def count_fit(d):
    m=make_pipeline(SimpleImputer(strategy="median"),StandardScaler(),PoissonRegressor(alpha=.3,max_iter=500))
    m.fit(d[FEATURES],d.saves)
    return m

def alpha_est(y,mu):
    return max(0.,float(np.sum((y-mu)**2-y)/max(np.sum(mu**2),1e-8)))

def over(mu,alpha,line):
    if alpha<1e-8:return poisson.sf(np.floor(line),mu)
    return nbinom.sf(np.floor(line),1/alpha,1/(1+alpha*mu))

def benchmark(d):
    train=d[d.season.isin(["20222023","20232024"])]
    cal=d[d.season.eq("20242025")]
    reg=count_fit(train)
    short=count_fit(train[train.short.eq(1)])
    full=count_fit(train[train.short.eq(0)])
    risk=make_pipeline(SimpleImputer(strategy="median"),StandardScaler(),LogisticRegression(C=.1,max_iter=500))
    risk.fit(train[FEATURES],train.short)
    prior=float(cal.short.mean())
    # Calibrate the risk intercept only on 2024-25 via fixed logistic recalibration.
    def logit(p):
        p=np.clip(p,1e-6,1-1e-6);return np.log(p/(1-p)).reshape(-1,1)
    calibrator=LogisticRegression(C=1000)
    calibrator.fit(logit(risk.predict_proba(cal[FEATURES])[:,1]),cal.short)
    models={"single":reg,"short":short,"full":full}
    alphas={}
    for k,m in models.items():
        q=cal if k=="single" else cal[cal.short.eq(int(k=="short"))]
        alphas[k]=alpha_est(q.saves.to_numpy(),m.predict(q[FEATURES]))
    metrics=[];risk_metrics=[];counts=[]
    for season in ["20252026","20262027"]:
        x=d[d.season.eq(season)]
        mu={k:m.predict(x[FEATURES]) for k,m in models.items()}
        p=calibrator.predict_proba(logit(risk.predict_proba(x[FEATURES])[:,1]))[:,1]
        for k,prob in [("constant",np.full(len(x),prior)),("learned",p)]:
            risk_metrics.append({"season":season,"model":k,**score(x.short,prob)})
        for name,weight in [("single",None),("constant_mixture",prior),("learned_mixture",p)]:
            pred=mu["single"] if weight is None else weight*mu["short"]+(1-weight)*mu["full"]
            counts.append({"season":season,"model":name,"rows":len(x),"mean_prediction":float(pred.mean()),"actual_mean":float(x.saves.mean()),"mae":float(np.abs(pred-x.saves).mean()),"rmse":float(np.sqrt(np.mean((pred-x.saves)**2)))})
            for line in LINES:
                prob=over(mu["single"],alphas["single"],line) if weight is None else weight*over(mu["short"],alphas["short"],line)+(1-weight)*over(mu["full"],alphas["full"],line)
                metrics.append({"season":season,"model":name,"line":line,**score(x.saves.gt(line),prob)})
    return pd.DataFrame(metrics),pd.DataFrame(risk_metrics),pd.DataFrame(counts),{"calibration_short_rate":prior,"alphas":alphas,"train_rows":len(train),"calibration_rows":len(cal)}
