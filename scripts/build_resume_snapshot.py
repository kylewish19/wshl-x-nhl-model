from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from build_goalie_features import TEAMS
from run_skater_transition_board import SEASONS, fallback_rate, get_season_stats
from run_skater_transition_slate import current_roster
from wshlx_nhl.bootstrap_models import build_skater_transitions, train_transition_rate_model
from wshlx_nhl.distributions import prob_at_least


def team_form_summary(team_games: pd.DataFrame, target_date: str) -> pd.DataFrame:
    tg = team_games.copy()
    tg["date"] = pd.to_datetime(tg["date"])
    cur = tg[tg["season"].astype(str).eq("20262027")].copy()
    as_of = pd.Timestamp(target_date) - pd.Timedelta(days=1)
    rows = []
    for team in TEAMS:
        g = cur[cur["team"].eq(team)].sort_values(["date", "game_id"])
        if g.empty:
            continue
        def mean_tail(col: str, n: int) -> float:
            return float(g.tail(n)[col].mean())
        last_date = pd.Timestamp(g.iloc[-1]["date"])
        rows.append({
            "team": team,
            "games_played": int(len(g)),
            "last_game_date": last_date.date().isoformat(),
            "days_since_last_game": int((as_of.normalize() - last_date.normalize()).days),
            "gf_pg": float(g["goals_for"].mean()),
            "ga_pg": float(g["goals_against"].mean()),
            "sf_pg": float(g["shots_for"].mean()),
            "sa_pg": float(g["shots_against"].mean()),
            "gf_pg_last5": mean_tail("goals_for", 5),
            "ga_pg_last5": mean_tail("goals_against", 5),
            "sf_pg_last5": mean_tail("shots_for", 5),
            "sa_pg_last5": mean_tail("shots_against", 5),
            "gf_pg_last10": mean_tail("goals_for", 10),
            "ga_pg_last10": mean_tail("goals_against", 10),
            "sf_pg_last10": mean_tail("shots_for", 10),
            "sa_pg_last10": mean_tail("shots_against", 10),
        })
    return pd.DataFrame(rows).sort_values("team").reset_index(drop=True)


def goalie_workload_summary(goalie_features: pd.DataFrame, target_date: str) -> pd.DataFrame:
    gf = goalie_features.copy()
    gf["date"] = pd.to_datetime(gf["date"])
    cur = gf[gf["season"].astype(str).eq("20262027")].copy()
    as_of = pd.Timestamp(target_date) - pd.Timedelta(days=1)
    rows = []
    for goalie_id, g in cur.groupby("goalie_id", dropna=False):
        g = g.sort_values(["date", "game_id"])
        latest = g.iloc[-1]
        shots = float(g["shots_against"].sum())
        saves = float(g["saves"].sum())
        recent = g.tail(5)
        starts_7d = int(((g["date"] >= (as_of - pd.Timedelta(days=6))) & (g["date"] <= as_of)).sum())
        rows.append({
            "goalie_id": goalie_id,
            "goalie_name": latest["goalie_name"],
            "team": latest["team"],
            "starts": int(len(g)),
            "starts_last_7d": starts_7d,
            "last_start_date": pd.Timestamp(latest["date"]).date().isoformat(),
            "days_since_last_start": int((as_of.normalize() - pd.Timestamp(latest["date"]).normalize()).days),
            "saves_per_start": float(g["saves"].mean()),
            "shots_against_per_start": float(g["shots_against"].mean()),
            "save_pct": saves / shots if shots > 0 else np.nan,
            "last5_saves_per_start": float(recent["saves"].mean()),
            "last5_shots_against_per_start": float(recent["shots_against"].mean()),
            "last5_save_pct": float(recent["saves"].sum() / recent["shots_against"].sum()) if float(recent["shots_against"].sum()) > 0 else np.nan,
        })
    return pd.DataFrame(rows).sort_values(["team", "starts"], ascending=[True, False]).reset_index(drop=True)


def build_skater_snapshot() -> tuple[pd.DataFrame, dict]:
    frames = {s: get_season_stats(s) for s in SEASONS}
    transitions = build_skater_transitions([frames[s] for s in SEASONS[:-1]], min_games=10)
    models = {
        "goals": train_transition_rate_model(transitions, "next_goals_pg", alpha_grid=(10.0,)),
        "assists": train_transition_rate_model(transitions, "next_assists_pg", alpha_grid=(0.3,)),
        "points": train_transition_rate_model(transitions, "next_points_pg", alpha_grid=(0.3,)),
    }
    prior = frames[20252026].copy()
    prior["playerId"] = prior["playerId"].astype(int)
    current = frames[20262027].copy()
    current["playerId"] = current["playerId"].astype(int)

    roster = []
    for team in TEAMS:
        roster.extend(current_roster(team))

    rows = []
    for p in roster:
        pid = int(p["player_id"])
        name = p["player_name"]
        team = p["team"]
        pprev = prior[prior["playerId"].eq(pid)]
        pcur = current[current["playerId"].eq(pid)]
        pos = str(pprev.iloc[0]["positionCode"]) if not pprev.empty else (
            str(pcur.iloc[0]["positionCode"]) if not pcur.empty else p.get("positionCode")
        )

        official_rates = {}
        bases = {}
        for key, target, model_key in [
            ("goal", "next_goals_pg", "goals"),
            ("assist", "next_assists_pg", "assists"),
            ("point", "next_points_pg", "points"),
        ]:
            if not pprev.empty and float(pprev.iloc[0]["gamesPlayed"]) >= 10:
                mu = float(models[model_key].predict(pprev.iloc[[0]])[0])
                basis = "transition_ml_anchor"
            else:
                mu = fallback_rate(pcur, prior, target, pos)
                basis = "limited_history_fallback_reconstruction"
            official_rates[key] = max(0.0, mu)
            bases[key] = basis

        gp = int(float(pcur.iloc[0]["gamesPlayed"])) if not pcur.empty else 0
        goals = float(pcur.iloc[0]["goals"]) if not pcur.empty else 0.0
        assists = float(pcur.iloc[0]["assists"]) if not pcur.empty else 0.0
        points = float(pcur.iloc[0]["points"]) if not pcur.empty else 0.0
        shots = float(pcur.iloc[0]["shots"]) if not pcur.empty else 0.0

        current_counts = {"goal": goals, "assist": assists, "point": points}
        shadow_prior_games = {"goal": 12.0, "assist": 10.0, "point": 10.0}
        shadow_rates = {}
        for key in ["goal", "assist", "point"]:
            k = shadow_prior_games[key]
            shadow_rates[key] = (k * official_rates[key] + current_counts[key]) / max(k + gp, 1.0)

        rows.append({
            "player_id": pid,
            "player_name": name,
            "team": team,
            "position": pos,
            "current_gp": gp,
            "current_goals": goals,
            "current_assists": assists,
            "current_points": points,
            "current_shots": shots,
            "current_goals_pg": goals / gp if gp else 0.0,
            "current_assists_pg": assists / gp if gp else 0.0,
            "current_points_pg": points / gp if gp else 0.0,
            "official_goal_mu": official_rates["goal"],
            "official_assist_mu": official_rates["assist"],
            "official_point_mu": official_rates["point"],
            "official_goal_prob": float(prob_at_least(1, official_rates["goal"], None)),
            "official_assist_prob": float(prob_at_least(1, official_rates["assist"], None)),
            "official_point_1plus_prob": float(prob_at_least(1, official_rates["point"], None)),
            "official_point_2plus_prob": float(prob_at_least(2, official_rates["point"], None)),
            "official_goal_basis": bases["goal"],
            "official_assist_basis": bases["assist"],
            "official_point_basis": bases["point"],
            "shadow_goal_mu": shadow_rates["goal"],
            "shadow_assist_mu": shadow_rates["assist"],
            "shadow_point_mu": shadow_rates["point"],
            "shadow_goal_prob": float(prob_at_least(1, shadow_rates["goal"], None)),
            "shadow_assist_prob": float(prob_at_least(1, shadow_rates["assist"], None)),
            "shadow_point_1plus_prob": float(prob_at_least(1, shadow_rates["point"], None)),
            "shadow_point_2plus_prob": float(prob_at_least(2, shadow_rates["point"], None)),
        })

    out = pd.DataFrame(rows).drop_duplicates(["player_id", "team"]).reset_index(drop=True)
    metrics = {
        "roster_players": int(len(out)),
        "current_season_stat_rows": int(len(current)),
        "transition_rows": int(len(transitions)),
        "validation_mae": {k: float(v.validation_mae) for k, v in models.items()},
        "alpha": {k: float(v.alpha) for k, v in models.items()},
        "shadow": {
            "name": "SKATER_CURRENT_SEASON_BLEND_SHADOW_V0_2",
            "status": "SHADOW_ONLY",
            "goal_prior_games": 12.0,
            "assist_prior_games": 10.0,
            "point_prior_games": 10.0,
            "description": "Empirical-Bayes blend of official v0.1 rate and 2026-27 observed counts. Does not alter official picks until validated prospectively."
        },
    }
    return out, metrics


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--goalie-features", required=True)
    ap.add_argument("--team-games", required=True)
    ap.add_argument("--target-date", required=True)
    ap.add_argument("--out-dir", required=True)
    args = ap.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    goalie_features = pd.read_parquet(args.goalie_features)
    team_games = pd.read_parquet(args.team_games)

    teams = team_form_summary(team_games, args.target_date)
    goalies = goalie_workload_summary(goalie_features, args.target_date)
    skaters, skater_metrics = build_skater_snapshot()

    teams.to_csv(out_dir / "team_form_2026-11-08.csv", index=False)
    goalies.to_csv(out_dir / "goalie_workload_2026-11-08.csv", index=False)
    skaters.to_csv(out_dir / "skater_snapshot_2026-11-08.csv", index=False)

    summary = {
        "snapshot_date": "2026-11-08",
        "data_cutoff_target_date": args.target_date,
        "current_season_team_games": int((team_games["season"].astype(str).eq("20262027")).sum()),
        "current_season_completed_games": int((team_games["season"].astype(str).eq("20262027")).sum() / 2),
        "team_count": int(len(teams)),
        "goalies_with_2026_27_starts": int(len(goalies)),
        "skater_metrics": skater_metrics,
        "official_model_changed": False,
        "notes": [
            "Team and goalie summaries include only completed regular-season games discovered before target date.",
            "Official v0.1 skater probabilities remain unchanged in architecture.",
            "Current-season skater blend is shadow-only and exists because established-player v0.1 anchors to 2025-26.",
            "Injuries, line combinations, PP units, scratches, and projected starters remain live context and must be refreshed again on each betting slate."
        ],
    }
    (out_dir / "resume_refresh_summary.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))
    print("\nTop team GF/game:")
    print(teams.sort_values("gf_pg", ascending=False).head(10).to_string(index=False))
    print("\nTop current goalie starts:")
    print(goalies.sort_values("starts", ascending=False).head(15).to_string(index=False))
    print("\nTop shadow 1+ point probabilities:")
    print(skaters.sort_values("shadow_point_1plus_prob", ascending=False).head(20)[[
        "player_name","team","current_gp","current_points","official_point_1plus_prob","shadow_point_1plus_prob"
    ]].to_string(index=False))


if __name__ == "__main__":
    main()
