"""Stratify frozen ATG research grades, never refit or reselect prices."""
import numpy as np
import pandas as pd
from .atg_grading import KEYS
from .atg_pregame import MODELS
from .atg_game_shadow import score

GROUPS=("limited_history","established_anchor","other_or_unknown")
COHORTS=("CLEAN_SHADOW_PREGAME","FROZEN_SOURCE_SUBGROUP_REVIEW")

def classify_basis(basis):
    s=basis.fillna("").astype(str).str.strip().str.casefold()
    return pd.Series(np.select(
        [s.str.startswith("limited_history_fallback"),s.eq("transition_ml_anchor")],
        ["limited_history","established_anchor"],default="other_or_unknown"),index=s.index)

def basis_summary(graded):
    d=graded.copy()
    if d.duplicated(KEYS).any():raise ValueError("Duplicate graded identity")
    if not d.result.isin(["WIN","LOSS","VOID"]).all():raise ValueError("Invalid result")
    d["basis_group"]=classify_basis(d.model_basis)
    settled=d.result.ne("VOID")
    if not d.loc[settled,"target"].eq(d.loc[settled,"result"].eq("WIN").astype(int)).all():
        raise ValueError("Inconsistent outcome")
    if not d[MODELS].apply(lambda c:c.between(0,1)).all().all():raise ValueError("Invalid probability")
    out=[]
    for group in GROUPS:
        g=d[d.basis_group.eq(group)]
        s=g[g.result.ne("VOID")]
        for m in MODELS:
            flag=g[m+"_qualifies"]
            if not flag.isin([True,False]).all():raise ValueError("Invalid frozen flag")
            q=g[flag.astype(bool)]
            w=int(q.result.eq("WIN").sum());l=int(q.result.eq("LOSS").sum())
            net=float(q[m+"_paper_profit"].sum())
            out.append(dict(basis_group=group,model=m,matched_rows=len(g),settled_rows=len(s),
                void_rows=len(g)-len(s),actual_goalscorers=int(s.target.sum()),
                expected_goalscorers=float(s[m].sum()),
                **(score(s.target,s[m]) if len(s) else dict(rows=0,goalscorer_rate=None,mean_probability=None,brier=None,log_loss=None,auc=None)),
                paper_count=len(q),paper_wins=w,paper_losses=l,paper_voids=len(q)-w-l,
                paper_profit_units=net,paper_roi=net/(w+l) if w+l else None))
    return d,pd.DataFrame(out)

def update_basis_ledger(prior,summary,replay=False):
    if not prior.empty and not prior.cohort.isin(COHORTS).all():raise ValueError("Nonprospective or unknown cohort")
    if not replay and not summary.cohort.eq("CLEAN_SHADOW_PREGAME").all():raise ValueError("Not a clean subgroup lock")
    ledger=prior.copy() if replay else pd.concat([prior,summary],ignore_index=True)
    if ledger.duplicated(["date","basis_group","model"]).any():raise ValueError("Duplicate subgroup date/model")
    return ledger

def cumulative_basis(ledger):
    rows=[]
    # Keep prior frozen-source reviews separate from newly locked subgroup labels.
    for (cohort,group,model),g in ledger.groupby(["cohort","basis_group","model"]):
        n=int(g.settled_rows.sum());w=int(g.paper_wins.sum());l=int(g.paper_losses.sum())
        actual=int(g.actual_goalscorers.sum());exp=float(g.expected_goalscorers.sum());net=float(g.paper_profit_units.sum())
        rows.append(dict(cohort=cohort,basis_group=group,model=model,slates=g.date.nunique(),
            matched_rows=int(g.matched_rows.sum()),settled_rows=n,void_rows=int(g.void_rows.sum()),
            actual_goalscorers=actual,expected_goalscorers=exp,actual_rate=actual/n if n else None,
            mean_probability=exp/n if n else None,
            brier=float((g.brier*g.settled_rows).sum()/n) if n else None,
            log_loss=float((g.log_loss*g.settled_rows).sum()/n) if n else None,
            paper_wins=w,paper_losses=l,paper_voids=int(g.paper_voids.sum()),
            paper_profit_units=net,paper_roi=net/(w+l) if w+l else None))
    return pd.DataFrame(rows)
