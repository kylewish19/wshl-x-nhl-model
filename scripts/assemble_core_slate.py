from __future__ import annotations

import argparse
from pathlib import Path
import pandas as pd

TEAM_NAMES = {
    "VGK":"Vegas Golden Knights","BUF":"Buffalo Sabres","TBL":"Tampa Bay Lightning",
    "WPG":"Winnipeg Jets","NJD":"New Jersey Devils","TOR":"Toronto Maple Leafs",
    "PHI":"Philadelphia Flyers","CGY":"Calgary Flames","PIT":"Pittsburgh Penguins",
    "ANA":"Anaheim Ducks"
}

SCRATCHED_ATG = {"Scott Sabourin"}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--team-pred",required=True)
    ap.add_argument("--core-odds",required=True)
    ap.add_argument("--atg-pred",required=True)
    ap.add_argument("--goalie-pred",required=True)
    ap.add_argument("--skater-snapshot",required=True)
    ap.add_argument("--out",required=True)
    ap.add_argument("--shadow-atg-out",required=True)
    args=ap.parse_args()

    team=pd.read_csv(args.team_pred)
    odds=pd.read_csv(args.core_odds)
    team["selection"]=team["selection"].replace(TEAM_NAMES)
    team["line_key"]=team["line"].fillna("").astype(str)
    odds["line_key"]=odds["line"].fillna("").astype(str)
    team=team.merge(
        odds[["date","game","market","selection","line_key","odds_american"]],
        on=["game","market","selection","line_key"], how="left"
    )
    team["date"]=team["date"].fillna("2026-11-08")
    team["active"]=1

    atg=pd.read_csv(args.atg_pred)
    atg["date"]="2026-11-08"
    atg["selection"]=atg["player_name"]
    atg["active"]=~atg["player_name"].isin(SCRATCHED_ATG)
    atg["active"]=atg["active"].astype(int)

    goal=pd.read_csv(args.goalie_pred)
    grow=[]
    for _,r in goal.iterrows():
        for side in ("Over","Under"):
            low=side.lower()
            grow.append({
                "date":"2026-11-08","game":r["game"],"market":"goalie_saves",
                "selection":f'{r["goalie_name"]} {side}',"goalie_name":r["goalie_name"],
                "team":r["team"],"line":r["line"],
                "odds_american":r[f"{low}_odds"],
                "model_probability":r[f"v0_1_{low}_probability"],
                "model_basis":r["v0_1_basis"],"active":1,
                "v0_2_probability":r[f"v0_2_{low}_probability"],
                "v0_2_expected_saves":r["v0_2_expected_saves"],
                "v0_1_expected_saves":r["v0_1_expected_saves"],
            })
    goalc=pd.DataFrame(grow)

    keep=["date","game","market","selection","line","odds_american","model_probability","model_basis","active"]
    extras=[c for c in ["player_name","player_id","team","resolved_team","listed_team"] if c in atg.columns]
    atg_out=atg[keep+extras].copy()
    team_out=team[keep].copy()
    goal_out=goalc[keep+[c for c in ["goalie_name","team","v0_2_probability","v0_2_expected_saves","v0_1_expected_saves"] if c in goalc.columns]].copy()

    candidates=pd.concat([team_out,atg_out,goal_out],ignore_index=True,sort=False)
    candidates.to_csv(args.out,index=False)

    snap=pd.read_csv(args.skater_snapshot)
    shadow_cols=["player_id","player_name","team","shadow_goal_prob","official_goal_prob","current_gp","current_goals","current_goals_pg"]
    snap=snap[[c for c in shadow_cols if c in snap.columns]].copy()
    shadow=atg.merge(snap,on="player_id",how="left",suffixes=("","_snap"))
    shadow["shadow_probability"]=shadow["shadow_goal_prob"]
    shadow["official_probability"]=shadow["model_probability"]
    shadow["probability_delta"]=shadow["shadow_probability"]-shadow["official_probability"]
    shadow=shadow.sort_values("shadow_probability",ascending=False)
    shadow.to_csv(args.shadow_atg_out,index=False)

    print("Candidate counts by market:")
    print(candidates.groupby("market").size().to_string())
    print("\nTop official probabilities:")
    print(candidates[candidates["active"].eq(1)].sort_values("model_probability",ascending=False).head(25).to_string(index=False))
    print("\nTop ATG current-season shadow:")
    print(shadow[["player_name","team","odds_american","official_probability","shadow_probability","probability_delta"]].head(25).to_string(index=False))

if __name__=="__main__":
    main()
