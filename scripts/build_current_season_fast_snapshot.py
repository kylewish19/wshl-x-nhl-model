from __future__ import annotations

import argparse
import concurrent.futures as cf
from pathlib import Path

import pandas as pd

from build_goalie_features import TEAMS, add_goalie_features, parse_boxscore, session

BASE = "https://api-web.nhle.com/v1"
SEASON = "20262027"


def current_season_games(target_date: str) -> dict[int, str]:
    target = pd.Timestamp(target_date)
    found: dict[int, str] = {}
    s = session()
    try:
        for team in TEAMS:
            url = f"{BASE}/club-schedule-season/{team}/{SEASON}"
            try:
                payload = s.get(url, timeout=30).json()
            except Exception:
                continue
            for g in payload.get("games", []):
                try:
                    gid = int(g["id"])
                except Exception:
                    continue
                if int(g.get("gameType", 0) or 0) != 2:
                    continue
                gd = pd.Timestamp(g.get("gameDate"))
                if pd.isna(gd) or gd >= target:
                    continue
                state = str(g.get("gameState", "")).upper()
                if state not in {"OFF", "FINAL"}:
                    continue
                found[gid] = SEASON
    finally:
        s.close()
    return found


def build(target_date: str, max_workers: int = 16):
    games = current_season_games(target_date)
    print(f"Discovered {len(games)} completed 2026-27 regular-season games before {target_date}")
    starts = []
    team_rows = []
    items = list(games.items())
    with cf.ThreadPoolExecutor(max_workers=max_workers) as ex:
        futs = {ex.submit(parse_boxscore, gid, season): gid for gid, season in items}
        for idx, fut in enumerate(cf.as_completed(futs), 1):
            gid = futs[fut]
            try:
                srows, trows = fut.result()
                starts.extend(srows)
                team_rows.extend(trows)
            except Exception as e:
                print(f"WARN boxscore {gid}: {e}")
            if idx % 100 == 0:
                print(f"Fetched {idx}/{len(items)} boxscores")
    starts_df = pd.DataFrame(starts).drop_duplicates(["game_id", "team"]).copy()
    team_df = pd.DataFrame(team_rows).drop_duplicates(["game_id", "team"]).copy()
    if starts_df.empty or team_df.empty:
        raise RuntimeError("No current-season NHL data parsed")
    starts_df["date"] = pd.to_datetime(starts_df["date"])
    team_df["date"] = pd.to_datetime(team_df["date"])
    return add_goalie_features(starts_df, team_df), team_df


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--target-date", required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--team-games", required=True)
    ap.add_argument("--max-workers", type=int, default=16)
    args = ap.parse_args()
    features, team_games = build(args.target_date, args.max_workers)
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    features.to_parquet(args.output, index=False)
    team_games.to_parquet(args.team_games, index=False)
    print(f"Wrote {len(features)} current-season goalie starts -> {args.output}")
    print(f"Wrote {len(team_games)} current-season team-games -> {args.team_games}")


if __name__ == "__main__":
    main()

# Trigger fast refresh 2026-11-08
