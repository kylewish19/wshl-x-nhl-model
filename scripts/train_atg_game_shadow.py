from __future__ import annotations

import argparse
import concurrent.futures as cf
import json
from pathlib import Path

import joblib
import pandas as pd

from build_goalie_features import BASE, get_json, list_games, localized, toi_seconds
from wshlx_nhl.atg_game_shadow import build_features, benchmark


def parse_game(gid, season):
    p = get_json(f"{BASE}/gamecenter/{gid}/boxscore")
    if str(p.get("gameState","")).upper() not in {"OFF","FINAL"}:
        raise ValueError("Game not final")
    day = p["gameDate"]
    away = localized(p["awayTeam"]["abbrev"])
    home = localized(p["homeTeam"]["abbrev"])
    out = []
    for side, team, opp, is_home in [("awayTeam",away,home,0),("homeTeam",home,away,1)]:
        stats = p["playerByGameStats"][side]
        team_rows = []
        for group in ["forwards","defense"]:
            for x in stats.get(group,[]):
                toi = toi_seconds(x.get("toi"))
                if toi<=0:
                    continue
                # These are realized outcomes; feature builder uses only lagged
                # values. Missing core stats are errors, never silently zeroed.
                team_rows.append({"date":day,"game_id":gid,"season":season,
                    "player_id":int(x["playerId"]),"team":team,"opponent":opp,
                    "position":"D" if group=="defense" else "F","is_home":is_home,
                    "goals":int(x["goals"]),"shots":int(x["sog"]),
                    "toi_seconds":toi,"pp_goals":int(x["powerPlayGoals"])})
        if len(team_rows)<10:
            raise ValueError(f"Incomplete skater rows for {team}")
        out.extend(team_rows)
    return out


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--target-date",required=True)
    ap.add_argument("--out-dir",required=True)
    ap.add_argument("--workers",type=int,default=12)
    ap.add_argument("--team-games",help="Optional dated historical team-game parquet")
    args=ap.parse_args()
    out=Path(args.out_dir);out.mkdir(parents=True,exist_ok=True)
    target=pd.Timestamp(args.target_date)
    if args.team_games:
        t=pd.read_parquet(args.team_games)
        t=t[pd.to_datetime(t.date)<target]
        games=dict(zip(t.game_id.astype(int),t.season.astype(str)))
    else:
        games=list_games(args.target_date)
    if not games:
        raise RuntimeError("No games discovered")
    rows=[];errors=[]
    with cf.ThreadPoolExecutor(max_workers=args.workers) as ex:
        futures={ex.submit(parse_game,gid,season):gid for gid,season in games.items()}
        for i,f in enumerate(cf.as_completed(futures),1):
            try: rows.extend(f.result())
            except Exception as e: errors.append({"game_id":futures[f],"error":str(e)})
            if i%250==0: print(f"Fetched {i}/{len(games)}; errors={len(errors)}",flush=True)
    (out/"coverage.json").write_text(json.dumps({"discovered_games":len(games),"errors":errors},indent=2))
    # Incomplete game history would distort rolling histories. Fail closed.
    if errors: raise RuntimeError(f"{len(errors)} boxscores failed; inspect coverage.json")
    raw=pd.DataFrame(rows)
    if raw.game_id.nunique()!=len(games) or pd.to_datetime(raw.date).max()>=target:
        raise RuntimeError("Game coverage or date cutoff failure")
    raw.to_parquet(out/"skater_games.parquet",index=False)
    features=build_features(raw)
    report,preds,model,calibrator=benchmark(features)
    report["target_date"]=args.target_date
    report["game_count"]=len(games)
    report["player_game_rows"]=len(raw)
    report["last_game_date"]=str(pd.to_datetime(raw.date).max().date())
    report["coverage_by_season"]=raw.groupby("season").game_id.nunique().to_dict()
    report["limitations"]=["Conditional on actual participation; no archived pregame odds or lineup forecasts.",
        "PP goals are lagged; PP ice time, xG and projected opponent goalie not yet included.",
        "Baselines are research baselines, not frozen official v0.1 probabilities."]
    preds.to_parquet(out/"heldout_predictions.parquet",index=False)
    joblib.dump({"model":model,"calibrator":calibrator},out/"atg_game_shadow.joblib")
    (out/"metrics.json").write_text(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2))


if __name__=="__main__":
    main()
