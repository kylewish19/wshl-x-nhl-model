"""Paper-only matched totals and goalie board preparation."""
import numpy as np
import pandas as pd
from scipy.stats import poisson
from .odds import american_to_implied,expected_roi

def price_fields(p,odds,edge_floor):
    if not np.isfinite(p) or not 0<=p<=1 or not np.isfinite(odds) or abs(odds)<100:
        raise ValueError("Invalid probability or price")
    e=p-american_to_implied(odds);v=expected_roi(p,odds)
    return {"probability":p,"odds_american":odds,"edge":e,"expected_roi":v,"qualifies":e>=edge_floor and v>=.05}

def totals_board(candidates,means):
    c=candidates[candidates.market.eq("total") & candidates.active.eq(1) & candidates.line.isin([5.5,6.5])]
    if c.duplicated(["date","game","line","selection"]).any():
        raise ValueError("Duplicate total side")
    rows=[]
    for (date,game,line),g in c.groupby(["date","game","line"]):
        if set(g.selection)!={"Over","Under"}:
            raise ValueError("Incomplete total pair")
        h=float(means[game]["home"]);a=float(means[game]["away"])
        if not np.isfinite([h,a]).all() or min(h,a)<=0:raise ValueError("Invalid means")
        delta=float(poisson.pmf(3,h)*poisson.pmf(3,a)) if line==6.5 else 0.
        base=float(poisson.sf(int(line),h+a))
        for r in g.itertuples():
            p=base if r.selection=="Over" else 1-base
            q=p+delta if r.selection=="Over" else p-delta
            for model,prob in [("official_locked",r.model_probability),("analytic_control",p),("tie_only",q)]:
                rows.append({"date":date,"game":game,"line":line,"selection":r.selection,"model":model,
                             **price_fields(prob,r.odds_american,.03)})
    return pd.DataFrame(rows,columns=["date","game","line","selection","model","probability","odds_american","edge","expected_roi","qualifies"])

def goalie_board(official,research):
    keys=["date","game","goalie_name","team","line"]
    if official.duplicated(keys).any() or research.duplicated(keys).any():raise ValueError("Duplicate goalie row")
    z=official.merge(research,on=keys,how="outer",suffixes=("_official","_research"),indicator=True,validate="one_to_one")
    valid=z["_merge"].eq("both") & z.goalie_id_official.astype(str).str.fullmatch(r"\d+") & z.goalie_id_official.astype(str).eq(z.goalie_id_research.astype(str))
    valid &= z.line.mod(1).eq(.5)
    excluded=z.loc[~valid,keys+["goalie_id_official","goalie_id_research","_merge"]].copy()
    rows=[]
    for r in z[valid].to_dict("records"):
        for side in ["over","under"]:
            if r[side+"_odds_official"]!=r[side+"_odds_research"]:raise ValueError("Goalie price mismatch")
        for model in ["v0_1","v0_2","v0_3"]:
            p,q=r[model+"_over_probability"],r[model+"_under_probability"]
            if abs(p+q-1)>1e-6:raise ValueError("Noncomplementary goalie probabilities")
            sides=[(s,price_fields(r[model+"_"+s+"_probability"],r[s+"_odds_official"],.04)) for s in ["over","under"]]
            side,fields=max(sides,key=lambda x:x[1]["expected_roi"])
            rows.append({**{k:r[k] for k in keys},"goalie_id":r["goalie_id_official"],"model":model,
                         "over_probability":p,"expected_saves":r[model+"_expected_saves"],"selection":side.title(),**fields})
    return pd.DataFrame(rows,columns=keys+["goalie_id","model","over_probability","expected_saves","selection","probability","odds_american","edge","expected_roi","qualifies"]),excluded
