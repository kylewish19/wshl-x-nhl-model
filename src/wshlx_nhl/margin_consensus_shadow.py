"""Paper-only prospective margin and goalie agreement comparisons.
No fitting, odds substitution, or modification of official selections.
"""
import numpy as np
import pandas as pd
from scipy.stats import skellam
from .team_market_shadow import build_team_features, FEATURES
from .daily_shadow import price_fields
from .daily_shadow_grading import settle, summary
from .atg_game_shadow import score

SPREAD_MODELS=("official_locked","analytic_control","direct_final_score_classes")
GOALIE_MODELS=("v0_1","v0_2","v0_3")
GROUPS=("unanimous_direction","unanimous_v03_gate","unanimous_all_gates")

def pregame_margin_features(history,games,date):
    """Append placeholders solely to invoke the existing lagged feature builder.
    Placeholder labels are discarded; their values cannot enter target-day features.
    """
    raw=history.copy()
    raw["date"]=pd.to_datetime(raw.date).dt.normalize()
    day=pd.Timestamp(date).normalize()
    if raw.empty or raw.date.ge(day).any():raise ValueError("History must be strictly prior")
    season=str(day.year if day.month>=7 else day.year-1)
    season+=str(int(season)+1)
    if season not in set(raw.season.astype(str)):raise ValueError("Missing current season")
    teams=set();rows=[]
    for i,game in enumerate(sorted(set(games)),1):
        a,h=game.split("@")
        if a==h or a in teams or h in teams:raise ValueError("Duplicate slate team")
        teams.update([a,h])
        if not {a,h}.issubset(set(raw.team)):raise ValueError("Unknown team")
        for t,o,home,gf,ga in [(a,h,0,0,1),(h,a,1,1,0)]:
            rows.append(dict(date=day,season=season,game_id=-i,team=t,opponent=o,is_home=home,
                             goals_for=gf,goals_against=ga,shots_for=0,shots_against=0))
    z=build_team_features(pd.concat([raw,pd.DataFrame(rows)],ignore_index=True))
    z=z[z.date.eq(day)].copy()
    z["game"]=z.team_a+"@"+z.team_h
    if set(z.game)!=set(games):raise ValueError("Incomplete target features")
    return z.set_index("game")[FEATURES]

def spread_board(candidates,means,features,model,team_names):
    c=candidates[candidates.market.eq("spread") & candidates.active.eq(1)].copy()
    if c.duplicated(["date","game","selection","line"]).any():raise ValueError("Duplicate spread")
    if not c.line.abs().eq(1.5).all():raise ValueError("Unsupported spread line")
    if set(c.game)!=set(features.index):raise ValueError("Missing spread game features")
    if list(model.classes_)!=[0,1,2,3]:raise ValueError("Incomplete margin classes")
    probs=pd.DataFrame(model.predict_proba(features[FEATURES]),index=features.index,columns=[0,1,2,3])
    if not np.isfinite(probs).all().all() or not np.allclose(probs.sum(axis=1),1):raise ValueError("Invalid margin probabilities")
    rows=[]
    for (date,game),g in c.groupby(["date","game"]):
        a,h=game.split("@")
        if len(g)!=2 or set(g.selection)!={team_names[a],team_names[h]} or set(g.line)!={-1.5,1.5}:
            raise ValueError("Incomplete spread pair")
        if not np.isclose(g.model_probability.sum(),1):raise ValueError("Noncomplementary official spread")
        ah=float(means[game]["away"]);hh=float(means[game]["home"])
        if min(ah,hh)<=0 or not np.isfinite([ah,hh]).all():raise ValueError("Invalid goal means")
        neg=g[g.line.eq(-1.5)].iloc[0]
        fav_home=neg.selection==team_names[h]
        analytic=float(skellam.sf(1,hh,ah) if fav_home else skellam.cdf(-2,hh,ah))
        direct=float(probs.loc[game,3 if fav_home else 0])
        for r in g.itertuples():
            for name,p in zip(SPREAD_MODELS,[r.model_probability,analytic if r.line<0 else 1-analytic,direct if r.line<0 else 1-direct]):
                rows.append(dict(date=date,game=game,team=h if r.selection==team_names[h] else a,
                    selection=r.selection,line=r.line,model=name,**price_fields(p,r.odds_american,.03)))
    return pd.DataFrame(rows)

def goalie_consensus(board):
    """Use probability direction, not the price-selected side, for unanimity.
    Gate groups require the qualifying price-selected side to match that direction.
    Exact .5 is not a directional prediction.
    """
    rows=[]
    keys=["date","game","goalie_id","line"]
    for _,g in board.groupby(keys,sort=True):
        if len(g)!=3 or set(g.model)!=set(GOALIE_MODELS):raise ValueError("Missing or duplicate goalie model")
        if g.team.nunique()!=1 or g.goalie_name.nunique()!=1:raise ValueError("Goalie identity mismatch")
        p=g.over_probability.to_numpy()
        if not np.isfinite(p).all() or not ((p>=0)&(p<=1)).all():raise ValueError("Invalid goalie probability")
        if not ((p>.5).all() or (p<.5).all()):continue
        side="Over" if (p>.5).all() else "Under"
        match=g.selection.eq(side)&g.qualifies
        v3=bool(match[g.model.eq("v0_3")].iloc[0])
        # The input board has only each model's selected-side price. If none chose
        # the unanimous direction, no exact price is available here; direction only.
        prices=g.loc[g.selection.eq(side),"odds_american"].unique()
        if len(prices)>1:raise ValueError("Conflicting goalie price")
        r=g.iloc[0];q=float(p.mean())
        rows.append(dict(date=r.date,game=r.game,goalie_id=r.goalie_id,goalie_name=r.goalie_name,
            team=r.team,line=r.line,selection=side,over_probability=q,
            probability=q if side=="Over" else 1-q,
            odds_american=float(prices[0]) if len(prices) else np.nan,
            unanimous_direction=True,unanimous_v03_gate=v3,unanimous_all_gates=bool(match.all())))
    return pd.DataFrame(rows,columns=keys+["goalie_name","team","selection","over_probability","probability",
        "odds_american",*GROUPS])

def grade_spreads(board,finals):
    keys=["date","game"]
    if board.duplicated(keys+["model","team","line"]).any() or finals.duplicated(keys).any():raise ValueError("Duplicate spread outcome")
    d=board.merge(finals[keys+["home_margin"]],on=keys,how="left",validate="many_to_one")
    if d.home_margin.isna().any() or d.home_margin.eq(0).any():raise ValueError("Missing final margin")
    home=d.game.str.split("@").str[1]
    margin=np.where(d.team.eq(home),d.home_margin,-d.home_margin)
    d["target"]=(margin+d.line>0).astype(int)
    d=settle(d,d.target.eq(1),np.zeros(len(d),dtype=bool))
    reports=[]
    for model,g in d.groupby("model"):
        # One complementary pair per game; use +1.5 for calibration.
        z=g[g.line.eq(1.5)]
        if len(z)*2!=len(g):raise ValueError("Incomplete spread pair")
        s=summary("spread",model,g,"probability","target")
        s.update(matched_rows=len(z),settled_rows=len(z),void_rows=0,**score(z.target,z.probability))
        reports.append(s)
    return d,pd.DataFrame(reports)

def grade_consensus(board,starts,finals):
    keys=["date","game","goalie_id"]
    if board.duplicated(keys+["line"]).any() or starts.duplicated(keys).any():raise ValueError("Duplicate goalie agreement outcome")
    if not set(zip(board.date,board.game)).issubset(set(zip(finals.date,finals.game))):raise ValueError("Missing game")
    d=board.merge(starts[keys+["team","saves"]].rename(columns={"team":"actual_team"}),on=keys,how="left",validate="many_to_one")
    played=d.saves.notna()
    if (played & d.team.ne(d.actual_team)).any():raise ValueError("Goalie team mismatch")
    d["target"]=np.where(played,d.saves.gt(d.line).eq(d.selection.eq("Over")).astype(int),np.nan)
    d["result"]=np.where(~played,"VOID",np.where(d.target.eq(1),"WIN","LOSS"))
    from .odds import american_to_decimal
    d["profit"]=np.where(d.result.eq("LOSS"),-1.,0.)
    win=d.result.eq("WIN")
    d.loc[win,"profit"]=d.loc[win,"odds_american"].map(lambda x:american_to_decimal(x)-1 if np.isfinite(x) else np.nan)
    reports=[]
    for name in GROUPS:
        z=d[d[name]].copy()
        settled=z[z.result.ne("VOID")]
        w=int(settled.result.eq("WIN").sum());l=len(settled)-w
        # Agreement alone is a diagnostic, not a priced paper card.
        priced=name!="unanimous_direction"
        if priced and z.odds_american.isna().any():raise ValueError("Missing qualifying price")
        net=float(z.profit.sum()) if priced else 0.
        reports.append(dict(market="goalie_consensus",model=name,matched_rows=len(z),settled_rows=len(settled),
            void_rows=len(z)-len(settled),**(score(settled.target,settled.probability) if len(settled) else dict(rows=0,brier=None,log_loss=None,auc=None)),
            paper_count=len(z) if priced else 0,paper_wins=w if priced else 0,paper_losses=l if priced else 0,
            paper_voids=len(z)-len(settled) if priced else 0,paper_profit_units=net,paper_roi=net/(w+l) if priced and w+l else None,
            direction_wins=w,direction_losses=l,direction_voids=len(z)-len(settled)))
    return d,pd.DataFrame(reports)
