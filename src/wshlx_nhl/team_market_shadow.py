"""Team-market research using the already archived completed regular-season games."""
import numpy as np
import pandas as pd
from scipy.stats import poisson, skellam
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
from sklearn.linear_model import LogisticRegression
from .atg_game_shadow import score

COLS=["goals_for","goals_against","shots_for","shots_against"]
FEATURES=[f"{side}_{c}" for side in ["home","away"] for c in
          ["gf","ga","rest","gp"]+[f"{x}_r{n}" for x in COLS for n in [5,20]]]
TARGETS=["home_ml","home_minus15","away_minus15","over55","over65"]

def build_team_features(raw):
    d=raw.copy()
    d["date"]=pd.to_datetime(d.date).dt.normalize()
    d["season"]=d.season.astype(str)
    if d.duplicated(["game_id","team"]).any() or d.duplicated(["date","team"]).any():
        raise ValueError("Duplicate team-game or same-day rows")
    if d[COLS].isna().any().any() or d[COLS].lt(0).any().any():
        raise ValueError("Invalid team counts")
    if not d.groupby("game_id").size().eq(2).all():
        raise ValueError("Incomplete games")
    if not d.groupby("game_id").is_home.sum().eq(1).all():
        raise ValueError("Invalid home away assignment")
    d=d.sort_values(["date","game_id","team"]).reset_index(drop=True)
    h=d.groupby("team",sort=False)
    for c in COLS:
        for n in [5,20]:
            d[f"{c}_r{n}"]=h[c].transform(lambda x:x.shift().rolling(n,min_periods=1).mean())
    d["rest"]=(d.date-h.date.shift()).dt.days.clip(1,14).fillna(7)
    s=d.groupby(["season","team"],sort=False)
    d["gp"]=s.cumcount()
    for c,name in [("goals_for","gf"),("goals_against","ga")]:
        prior=d.groupby(["season","team"])[c].mean()
        league=d.groupby("season")[c].mean()
        prev=d.season.map(lambda x:str(int(x)-10001))
        p=pd.Series([prior.get((a,b),league.get(a,3.0)) for a,b in zip(prev,d.team)],index=d.index)
        # Only previous season means, plus shifted current-season cumulative totals.
        d[name]=(10*p+s[c].cumsum()-d[c])/(10+d.gp)
    keys=["date","game_id","season"]
    cols=["gf","ga","rest","gp"]+[f"{x}_r{n}" for x in COLS for n in [5,20]]
    home=d[d.is_home.eq(1)][keys+["team","opponent","goals_for","goals_against"]+cols]
    away=d[d.is_home.eq(0)][keys+["team","opponent","goals_for","goals_against"]+cols]
    z=home.merge(away,on=keys,suffixes=("_h","_a"),validate="one_to_one")
    if not (z.team_h.eq(z.opponent_a)&z.team_a.eq(z.opponent_h)&z.goals_for_h.eq(z.goals_against_a)&z.goals_for_a.eq(z.goals_against_h)).all():
        raise ValueError("Inconsistent paired games")
    for c in cols:
        z["home_"+c]=z[c+"_h"];z["away_"+c]=z[c+"_a"]
    margin=z.goals_for_h-z.goals_for_a
    total=z.goals_for_h+z.goals_for_a
    if margin.eq(0).any():
        raise ValueError("Final-score ties")
    z["margin_class"]=np.select([margin.le(-2),margin.eq(-1),margin.eq(1)],[0,1,2],default=3)
    z["total_class"]=np.select([total.le(5),total.eq(6)],[0,1],default=2)
    for k,v in zip(TARGETS,[margin.gt(0),margin.ge(2),margin.le(-2),total.gt(5.5),total.gt(6.5)]):
        z[k]=v.astype(int)
    return z.sort_values(keys).reset_index(drop=True)

def baseline(z):
    # Infinite-sample equivalent of current v0.1 simulation, zero context.
    h=np.maximum(1.5,np.sqrt(z.home_gf*z.away_ga)*1.02)
    a=np.maximum(1.5,np.sqrt(z.away_gf*z.home_ga)*.98)
    return pd.DataFrame({"home_ml":skellam.sf(0,h,a)+.5*skellam.pmf(0,h,a),
        "home_minus15":skellam.sf(1,h,a),"away_minus15":skellam.cdf(-2,h,a),
        "over55":poisson.sf(5,h+a),"over65":poisson.sf(6,h+a)},index=z.index)

def fit_models(train):
    models={}
    for name in ["margin_class","total_class"]:
        m=make_pipeline(SimpleImputer(strategy="median"),StandardScaler(),LogisticRegression(C=.1,max_iter=2000))
        m.fit(train[FEATURES],train[name])
        models[name]=m
    return models

def predict_models(models,z):
    m,t=(models[k].predict_proba(z[FEATURES]) for k in ["margin_class","total_class"])
    if list(models["margin_class"].classes_)!=[0,1,2,3] or list(models["total_class"].classes_)!=[0,1,2]:
        raise ValueError("Incomplete classes")
    return pd.DataFrame({"home_ml":m[:,2]+m[:,3],"home_minus15":m[:,3],"away_minus15":m[:,0],
                         "over55":t[:,1]+t[:,2],"over65":t[:,2]},index=z.index)

def benchmark(z):
    # Historical diagnostics only: prior holdouts already observed elsewhere.
    train=z[z.season.isin(["20222023","20232024","20242025"])]
    models=fit_models(train)
    rows=[];preds=[]
    for season in ["20252026","20262027"]:
        x=z[z.season.eq(season)]
        p={"v01_analytic_zero_context":baseline(x),"direct_final_score_classes":predict_models(models,x)}
        out=x[["date","game_id","season","team_h","team_a"]+TARGETS].copy()
        for model,prob in p.items():
            for k in TARGETS:
                rows.append({"season":season,"model":model,"market":k,**score(x[k],prob[k])})
                out[model+"_"+k]=prob[k]
        preds.append(out)
    return pd.DataFrame(rows),pd.concat(preds),models
