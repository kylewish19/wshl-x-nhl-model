"""Isolate final-score tie treatment from team-strength model changes."""
import numpy as np
import pandas as pd
from scipy.stats import poisson, skellam
from scipy.optimize import brentq
from .team_market_shadow import baseline, TARGETS
from .atg_game_shadow import score

def means(z):
    return (np.maximum(1.5,np.sqrt(z.home_gf*z.away_ga)*1.02),
            np.maximum(1.5,np.sqrt(z.away_gf*z.home_ga)*.98))

def regulation_scale(h,a):
    # Original rates estimate final credited goals, so do not add an extra
    # goal blindly: reduce regulation means until E(final total) is preserved.
    return brentq(lambda s:s*(h+a)+skellam.pmf(0,s*h,s*a)-(h+a),.01,1.)

def resolved(h,a,index, preserve=False, factor=1.):
    h=np.asarray(h,dtype=float)*factor
    a=np.asarray(a,dtype=float)*factor
    if preserve:
        scales=np.array([regulation_scale(x,y) for x,y in zip(h,a)])
        h=h*scales;a=a*scales
    # On a regulation tie a single credited goal goes to either side.
    # At +/-1.5, both tied paths still fail the favorite's -1.5.
    # A half-goal total changes only when a tie was exactly on the lower integer.
    return pd.DataFrame({"home_ml":skellam.sf(0,h,a)+.5*skellam.pmf(0,h,a),
        "home_minus15":skellam.sf(1,h,a),"away_minus15":skellam.cdf(-2,h,a),
        "over55":poisson.sf(5,h+a),
        "over65":poisson.sf(6,h+a)+poisson.pmf(3,h)*poisson.pmf(3,a)},index=index)

def benchmark(z):
    cal=z[z.season.eq("20242025")]
    h,a=means(cal)
    # Single predetermined era scale estimated on earlier calibration games.
    factor=float((cal.goals_for_h+cal.goals_for_a).mean()/(h+a).mean())
    rows=[];preds=[]
    for season in ["20242025","20252026","20262027"]:
        x=z[z.season.eq(season)]
        h,a=means(x)
        models={"baseline":baseline(x),"tie_only":resolved(h,a,x.index),
                "tie_mean_preserved":resolved(h,a,x.index,preserve=True),
                "tie_mean_calibrated":resolved(h,a,x.index,preserve=True,factor=factor)}
        out=x[["date","game_id","season"]+TARGETS].copy()
        for name,p in models.items():
            for k in TARGETS:
                rows.append({"season":season,"model":name,"market":k,**score(x[k],p[k])})
                out[name+"_"+k]=p[k]
        preds.append(out)
    return pd.DataFrame(rows),pd.concat(preds),factor
