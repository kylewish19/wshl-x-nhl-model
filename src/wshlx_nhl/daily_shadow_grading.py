"""Grade frozen daily research comparisons; no prediction or price changes."""
import numpy as np
import pandas as pd
from .atg_game_shadow import score
from .odds import american_to_decimal
from .atg_grading import grade_matched
from .atg_pregame import MODELS

def summary(market,model,d,prob,target):
    settled=d[d.result.ne("VOID")]
    q=d[d.qualifies]
    w=int(q.result.eq("WIN").sum());l=int(q.result.eq("LOSS").sum())
    net=float(q.profit.sum())
    return {"market":market,"model":model,"matched_rows":len(d),"settled_rows":len(settled),
            "void_rows":int(d.result.eq("VOID").sum()),
            **(score(settled[target],settled[prob]) if len(settled) else {"rows":0,"brier":None,"log_loss":None,"auc":None}),
            "paper_count":len(q),"paper_wins":w,"paper_losses":l,"paper_voids":int(q.result.eq("VOID").sum()),
            "paper_profit_units":net,"paper_roi":net/(w+l) if w+l else None}

def settle(d,win,void):
    if not d.qualifies.isin([True,False]).all():raise ValueError("Invalid frozen flag")
    if not d.odds_american.abs().ge(100).all():raise ValueError("Invalid frozen price")
    d["result"]=np.where(void,"VOID",np.where(win,"WIN","LOSS"))
    d["profit"]=np.where(d.result.eq("WIN"),d.odds_american.map(american_to_decimal)-1,np.where(d.result.eq("LOSS"),-1,0))
    return d

def grade_totals(board,finals):
    k=["date","game"];keys=k+["line","model","selection"]
    if board.duplicated(keys).any() or finals.duplicated(k).any():raise ValueError("Duplicate totals")
    d=board.merge(finals[k+["total_goals"]],on=k,how="left",validate="many_to_one")
    if d.total_goals.isna().any():raise ValueError("Incomplete totals finals")
    if not d.line.isin([5.5,6.5]).all() or not d.selection.isin(["Over","Under"]).all():raise ValueError("Invalid total market")
    d["over_target"]=d.total_goals.gt(d.line).astype(int)
    d=settle(d,d.over_target.eq(d.selection.eq("Over").astype(int)),np.zeros(len(d),dtype=bool))
    rows=[]
    for model,x in d.groupby("model"):
        # Probability metrics use only one side per line; price metrics include all frozen qualifying selections.
        o=x[x.selection.eq("Over")]
        if len(o)*2!=len(x):raise ValueError("Incomplete total pair")
        w=int((x.qualifies & x.result.eq("WIN")).sum());l=int((x.qualifies & x.result.eq("LOSS")).sum());net=float(x.loc[x.qualifies,"profit"].sum())
        rows.append({"market":"total","model":model,"matched_rows":len(o),"settled_rows":len(o),"void_rows":0,
                     **score(o.over_target,o.probability),"paper_count":int(x.qualifies.sum()),"paper_wins":w,"paper_losses":l,"paper_voids":0,"paper_profit_units":net,"paper_roi":net/(w+l) if w+l else None})
    return d,pd.DataFrame(rows)

def grade_goalies(board,starts,finals):
    k=["date","game","goalie_id"]
    if board.duplicated(k+["line","model"]).any() or starts.duplicated(k).any():raise ValueError("Duplicate goalie outcome")
    if not set(zip(board.date,board.game)).issubset(set(zip(finals.date,finals.game))):raise ValueError("Incomplete goalie finals")
    d=board.merge(starts[k+["team","saves"]].rename(columns={"team":"actual_team"}),on=k,how="left",validate="many_to_one")
    played=d.saves.notna()
    if (played & d.team.ne(d.actual_team)).any():raise ValueError("Goalie outcome team mismatch")
    d["over_target"]=np.where(played,d.saves.gt(d.line).astype(int),np.nan)
    d=settle(d,d.over_target.eq(d.selection.eq("Over").astype(int)),~played)
    rows=[]
    for model,x in d.groupby("model"):
        s=summary("goalie_saves",model,x,"over_probability","over_target")
        z=x[x.result.ne("VOID")]
        s["saves_mae"]=float((z.saves-z.expected_saves).abs().mean()) if len(z) else None
        rows.append(s)
    return d,pd.DataFrame(rows)

def cumulative(ledger):
    clean=ledger[ledger.cohort.eq("CLEAN_SHADOW_PREGAME")].copy()
    if clean.duplicated(["date","market","model"]).any():raise ValueError("Duplicate prospective slate/model")
    rows=[]
    for (market,model),g in clean.groupby(["market","model"]):
        w=int(g.paper_wins.sum());l=int(g.paper_losses.sum());net=float(g.paper_profit_units.sum());n=int(g.settled_rows.sum())
        rows.append({"market":market,"model":model,"slates":g.date.nunique(),"settled_rows":n,
                     "brier":float((g.brier*g.settled_rows).sum()/n) if n else None,
                     "log_loss":float((g.log_loss*g.settled_rows).sum()/n) if n else None,
                     "paper_wins":w,"paper_losses":l,"paper_voids":int(g.paper_voids.sum()),"paper_profit_units":net,"paper_roi":net/(w+l) if w+l else None})
    return pd.DataFrame(rows,columns=["market","model","slates","settled_rows","brier","log_loss","paper_wins","paper_losses","paper_voids","paper_profit_units","paper_roi"])
