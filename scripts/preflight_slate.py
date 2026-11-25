"""Offline preflight for supplied FanDuel boards; no picks or model changes."""
import argparse,json,hashlib
from pathlib import Path
import pandas as pd
import numpy as np
from assemble_core_slate import TEAM_NAMES

def require(flag,message):
    if not flag:raise ValueError(message)

def validate(date,team,core,atg,goalie):
    frames={"team":team,"core":core,"atg":atg,"goalie":goalie}
    for name,d in frames.items():
        require(not d.empty,f"Empty {name} board")
        require(d.date.astype(str).eq(date).all(),f"Wrong date: {name}")
        require(d.game.notna().all(),f"Missing matchup: {name}")
    require(not team.game.duplicated().any(),"Duplicate team matchup")
    require(team.away.isin(TEAM_NAMES).all() and team.home.isin(TEAM_NAMES).all(),"Unknown team")
    require(team.game.eq(team.away+"@"+team.home).all() and team.away.ne(team.home).all(),"Team matchup mismatch")
    require(not pd.concat([team.away,team.home]).duplicated().any(),"Team appears twice")
    require(team.home_spread.eq(-team.away_spread).all(),"Spread lines not complementary")
    require(team.total_line.gt(0).all(),"Invalid totals")
    require(np.isfinite(team[["away_spread","home_spread","total_line","away_context_adjustment","home_context_adjustment"]]).all().all(),"Invalid team numeric value")
    games=set(team.game)
    for name,d in frames.items():
        require(set(d.game)<=games,f"Unexpected game: {name}")
    for name,d,cols in [("core",core,["odds_american"]),("ATG",atg,["odds_american"]),("goalie",goalie,["over_odds","under_odds"])]:
        for col in cols:
            v=pd.to_numeric(d[col],errors="coerce")
            require(np.isfinite(v).all() and v.abs().ge(100).all() and v.mod(1).eq(0).all(),f"Invalid American odds: {name}/{col}")
    def line(v):return None if pd.isna(v) else float(v)
    expected=set()
    for r in team.itertuples():
        for side in ["away","home"]:
            name=TEAM_NAMES[getattr(r,side)]
            expected.add((r.game,"moneyline",name,None))
            expected.add((r.game,"spread",name,float(getattr(r,side+"_spread"))))
        for side in ["Over","Under"]:expected.add((r.game,"total",side,float(r.total_line)))
    actual=[(r.game,r.market,r.selection,line(r.line)) for r in core.itertuples()]
    require(len(actual)==len(set(actual)),"Duplicate core price")
    require(set(actual)==expected,"Core prices missing or unmatched to team board")
    require(atg.market.eq("anytime_goal").all() and atg.line.eq(.5).all(),"Invalid ATG market")
    require(atg.player_name.notna().all() and atg.selection.eq(atg.player_name).all(),"Invalid ATG selection")
    require(not atg.assign(name=atg.player_name.str.casefold().str.strip()).duplicated(["game","name"]).any(),"Duplicate ATG player")
    require(all(t in g.split("@") for g,t in zip(atg.game,atg.team)),"ATG team mismatch")
    require(goalie.goalie_name.notna().all() and goalie.line.gt(0).all(),"Invalid goalie line/name")
    require(not goalie.duplicated(["game","team","goalie_name","line"]).any(),"Duplicate goalie line")
    require(all(t in g.split("@") and o in g.split("@") and t!=o and h==int(t==g.split("@")[1]) for g,t,o,h in zip(goalie.game,goalie.team,goalie.opponent,goalie.is_home)),"Goalie matchup mismatch")
    return {"date":date,"games":len(games),"core_rows":len(core),"atg_rows":len(atg),"goalie_rows":len(goalie),"games_without_atg":sorted(games-set(atg.game)),"games_without_goalie_prices":sorted(games-set(goalie.game)),"status":"INPUT_STRUCTURE_VERIFIED","limitations":["Does not independently verify source sportsbook, real schedule, roster availability or timestamp","Missing market coverage explicitly reported; no prices invented"]}

def main():
    p=argparse.ArgumentParser()
    for k in ["date","team","core","atg","goalie","out"]:p.add_argument("--"+k,required=True)
    a=p.parse_args()
    paths={k:getattr(a,k) for k in ["team","core","atg","goalie"]}
    m=validate(a.date,**{k:pd.read_csv(v) for k,v in paths.items()})
    m["input_hashes"]={k:hashlib.sha256(Path(v).read_bytes()).hexdigest() for k,v in paths.items()}
    out=Path(a.out);out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(m,indent=2))
    print("=== PREFLIGHT ===");print(json.dumps(m,indent=2));print("=== END PREFLIGHT ===")
if __name__=="__main__":main()
