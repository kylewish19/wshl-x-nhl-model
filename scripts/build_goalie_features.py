from __future__ import annotations

import argparse
import concurrent.futures as cf
from pathlib import Path

import numpy as np
import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

BASE = "https://api-web.nhle.com/v1"
SEASONS = ["20212022", "20222023", "20232024", "20242025", "20252026", "20262027"]
TEAMS = [
    "ANA","ARI","BOS","BUF","CAR","CBJ","CGY","CHI","COL","DAL","DET","EDM",
    "FLA","LAK","MIN","MTL","NJD","NSH","NYI","NYR","OTT","PHI","PIT","SEA",
    "SJS","STL","TBL","TOR","UTA","VAN","VGK","WPG","WSH",
]


def session() -> requests.Session:
    s = requests.Session()
    retry = Retry(total=5, backoff_factor=0.35, status_forcelist=[429, 500, 502, 503, 504])
    s.mount("https://", HTTPAdapter(max_retries=retry, pool_connections=20, pool_maxsize=20))
    s.headers.update({"User-Agent": "wshlx-nhl-model/goalie-builder"})
    return s


def get_json(url: str, timeout: int = 30) -> dict:
    with session() as s:
        r = s.get(url, timeout=timeout)
        r.raise_for_status()
        return r.json()


def localized(v):
    if isinstance(v, dict):
        return v.get("default") or v.get("en") or next(iter(v.values()), "")
    return v or ""


def toi_seconds(v) -> int:
    if v is None:
        return 0
    if isinstance(v, (int, float)):
        return int(v)
    text = str(v)
    if ":" in text:
        try:
            mm, ss = text.split(":", 1)
            return int(mm) * 60 + int(float(ss))
        except Exception:
            return 0
    try:
        return int(float(text))
    except Exception:
        return 0


def list_games(target_date: str) -> dict[int, str]:
    target = pd.Timestamp(target_date)
    found: dict[int, str] = {}
    s = session()
    try:
        for season in SEASONS:
            for team in TEAMS:
                url = f"{BASE}/club-schedule-season/{team}/{season}"
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
                    if season == "20262027" and state not in {"OFF", "FINAL"}:
                        continue
                    found[gid] = season
    finally:
        s.close()
    return found


def parse_goalie(g: dict) -> dict:
    first = localized(g.get("firstName"))
    last = localized(g.get("lastName"))
    name = localized(g.get("name")) or (f"{first} {last}".strip())
    return {
        "goalie_id": str(g.get("playerId", "")),
        "goalie_name": name,
        "saves": float(g.get("saves", 0) or 0),
        "shots_against": float(g.get("shotsAgainst", 0) or 0),
        "goals_against": float(g.get("goalsAgainst", 0) or 0),
        "toi_seconds": toi_seconds(g.get("toi") or g.get("timeOnIce")),
        "starter_flag": bool(g.get("starter", False)),
    }


def parse_boxscore(game_id: int, season: str) -> tuple[list[dict], list[dict]]:
    payload = get_json(f"{BASE}/gamecenter/{game_id}/boxscore")
    game_date = str(payload.get("gameDate", ""))[:10]
    away_team = payload.get("awayTeam", {})
    home_team = payload.get("homeTeam", {})
    away = localized(away_team.get("abbrev")) or away_team.get("abbrev", "")
    home = localized(home_team.get("abbrev")) or home_team.get("abbrev", "")
    away_score = float(away_team.get("score", 0) or 0)
    home_score = float(home_team.get("score", 0) or 0)
    pstats = payload.get("playerByGameStats", {})
    away_goalies = [parse_goalie(x) for x in pstats.get("awayTeam", {}).get("goalies", [])]
    home_goalies = [parse_goalie(x) for x in pstats.get("homeTeam", {}).get("goalies", [])]
    if not away_goalies or not home_goalies:
        return [], []

    away_sog = sum(x["shots_against"] for x in home_goalies)
    home_sog = sum(x["shots_against"] for x in away_goalies)
    team_rows = [
        {"date": game_date, "season": season, "game_id": game_id, "team": away, "opponent": home,
         "is_home": 0, "shots_for": away_sog, "shots_against": home_sog,
         "goals_for": away_score, "goals_against": home_score},
        {"date": game_date, "season": season, "game_id": game_id, "team": home, "opponent": away,
         "is_home": 1, "shots_for": home_sog, "shots_against": away_sog,
         "goals_for": home_score, "goals_against": away_score},
    ]

    starter_rows = []
    for team, opp, is_home, gl, won in [
        (away, home, 0, away_goalies, away_score > home_score),
        (home, away, 1, home_goalies, home_score > away_score),
    ]:
        starters = [x for x in gl if x["starter_flag"]]
        starter = max(starters or gl, key=lambda x: x["toi_seconds"])
        row = {"date": game_date, "season": season, "game_id": game_id, "team": team,
               "opponent": opp, "is_home": is_home, "win": int(won), **starter}
        starter_rows.append(row)
    return starter_rows, team_rows


def rolling_mean_shifted(s: pd.Series, n: int) -> pd.Series:
    return s.shift().rolling(n, min_periods=1).mean()


def add_team_features(team_games: pd.DataFrame) -> pd.DataFrame:
    tg = team_games.sort_values(["team", "date", "game_id"]).copy()
    for col in ["shots_for", "shots_against", "goals_for", "goals_against"]:
        for n in [5, 10]:
            tg[f"{col}_r{n}"] = tg.groupby("team")[col].transform(lambda s: rolling_mean_shifted(s, n))
    return tg


def add_goalie_features(starts: pd.DataFrame, team_games: pd.DataFrame) -> pd.DataFrame:
    st = starts.sort_values(["goalie_id", "date", "game_id"]).copy()
    st["date"] = pd.to_datetime(st["date"])
    st["goalie_shots_against_r5"] = st.groupby("goalie_id")["shots_against"].transform(lambda s: rolling_mean_shifted(s, 5))
    st["goalie_shots_against_r10"] = st.groupby("goalie_id")["shots_against"].transform(lambda s: rolling_mean_shifted(s, 10))

    st["save_pct_r5"] = np.nan
    st["save_pct_r10"] = np.nan
    st["starts_last_7d"] = 0.0
    for _, idx in st.groupby("goalie_id").groups.items():
        ids = list(idx)
        g = st.loc[ids]
        for n in [5, 10]:
            saves = g["saves"].shift().rolling(n, min_periods=1).sum()
            shots = g["shots_against"].shift().rolling(n, min_periods=1).sum()
            st.loc[ids, f"save_pct_r{n}"] = (saves / shots.replace(0, np.nan)).to_numpy()
        dates = list(pd.to_datetime(g["date"]))
        counts = [sum(1 for p in dates[:i] if pd.Timedelta(0) < (d - p) <= pd.Timedelta(days=7)) for i, d in enumerate(dates)]
        st.loc[ids, "starts_last_7d"] = counts

    prev_date = st.groupby("goalie_id")["date"].shift()
    st["days_rest"] = (st["date"] - prev_date).dt.days.clip(lower=0, upper=30).fillna(7)

    tg = add_team_features(team_games)
    own = tg[["game_id", "team", "shots_against_r5", "shots_against_r10", "goals_against_r5"]].rename(columns={
        "shots_against_r5": "team_shots_against_r5",
        "shots_against_r10": "team_shots_against_r10",
        "goals_against_r5": "team_goals_against_r5",
    })
    opp = tg[["game_id", "team", "shots_for_r5", "shots_for_r10", "goals_for_r5"]].rename(columns={
        "team": "opponent",
        "shots_for_r5": "opponent_shots_for_r5",
        "shots_for_r10": "opponent_shots_for_r10",
        "goals_for_r5": "opponent_goals_for_r5",
    })
    return st.merge(own, on=["game_id", "team"], how="left").merge(opp, on=["game_id", "opponent"], how="left")


def build(target_date: str, max_workers: int = 12) -> tuple[pd.DataFrame, pd.DataFrame]:
    games = list_games(target_date)
    print(f"Discovered {len(games)} completed regular-season games before {target_date}")
    starts: list[dict] = []
    team_rows: list[dict] = []
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
            if idx % 250 == 0:
                print(f"Fetched {idx}/{len(items)} boxscores")
    starts_df = pd.DataFrame(starts).drop_duplicates(["game_id", "team"]).copy()
    team_df = pd.DataFrame(team_rows).drop_duplicates(["game_id", "team"]).copy()
    if starts_df.empty or team_df.empty:
        raise RuntimeError("No goalie start data were parsed from NHL boxscores")
    starts_df["date"] = pd.to_datetime(starts_df["date"])
    team_df["date"] = pd.to_datetime(team_df["date"])
    return add_goalie_features(starts_df, team_df), team_df


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--target-date", required=True)
    ap.add_argument("--output", default="data/processed/goalie_features.parquet")
    ap.add_argument("--team-games", default="data/processed/team_games.parquet")
    ap.add_argument("--max-workers", type=int, default=12)
    args = ap.parse_args()
    features, team_games = build(args.target_date, args.max_workers)
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    features.to_parquet(args.output, index=False)
    team_games.to_parquet(args.team_games, index=False)
    print(f"Wrote {len(features)} goalie starts -> {args.output}")
    print(f"Wrote {len(team_games)} team-games -> {args.team_games}")


if __name__ == "__main__":
    main()
