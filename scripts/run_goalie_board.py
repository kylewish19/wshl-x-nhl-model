from __future__ import annotations

import argparse
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import yaml

from wshlx_nhl.bootstrap_models import build_goalie_transitions, train_goalie_transition_model
from wshlx_nhl.distributions import prob_over_line, prob_under_line
from wshlx_nhl.goalie_shadow import train_goalie_two_stage_shadow
from wshlx_nhl.odds import american_to_implied, expected_roi

SEASONS_OFFICIAL = ["20212022", "20222023", "20232024", "20242025", "20252026"]


def season_goalie_frame(starts: pd.DataFrame, season: str) -> pd.DataFrame:
    df = starts[starts["season"].astype(str).eq(season)].copy()
    if df.empty:
        return pd.DataFrame(columns=["playerId","goalie_name","gamesStarted","gamesPlayed","saves","shotsAgainst","savePct","goalsAgainstAverage","wins","timeOnIce"])
    g = df.groupby(["goalie_id", "goalie_name"], dropna=False).agg(
        gamesStarted=("game_id", "count"), saves=("saves", "sum"), shotsAgainst=("shots_against", "sum"),
        goalsAgainst=("goals_against", "sum"), wins=("win", "sum"), timeOnIce=("toi_seconds", "sum"),
    ).reset_index()
    g["gamesPlayed"] = g["gamesStarted"]
    g["savePct"] = g["saves"] / g["shotsAgainst"].replace(0, np.nan)
    g["goalsAgainstAverage"] = g["goalsAgainst"] * 3600.0 / g["timeOnIce"].replace(0, np.nan)
    g = g.rename(columns={"goalie_id":"playerId"})
    return g[["playerId","goalie_name","gamesStarted","gamesPlayed","saves","shotsAgainst","savePct","goalsAgainstAverage","wins","timeOnIce"]]


def recent_team(team_games: pd.DataFrame, team: str, target: pd.Timestamp) -> dict:
    g = team_games[(team_games["team"] == team) & (pd.to_datetime(team_games["date"]) < target)].sort_values("date")
    def mean_tail(col, n, default):
        x = g[col].tail(n)
        return float(x.mean()) if len(x) else default
    return {
        "team_shots_against_r5": mean_tail("shots_against", 5, 30.0),
        "team_shots_against_r10": mean_tail("shots_against", 10, 30.0),
        "team_goals_against_r5": mean_tail("goals_against", 5, 3.0),
        "shots_for_r5": mean_tail("shots_for", 5, 30.0),
        "shots_for_r10": mean_tail("shots_for", 10, 30.0),
        "goals_for_r5": mean_tail("goals_for", 5, 3.0),
    }


def recent_goalie(starts: pd.DataFrame, goalie_id: str | None, goalie_name: str, target: pd.Timestamp) -> dict:
    if goalie_id:
        g = starts[(starts["goalie_id"].astype(str) == str(goalie_id)) & (pd.to_datetime(starts["date"]) < target)].sort_values("date")
    else:
        g = starts[(starts["goalie_name"].str.casefold() == goalie_name.casefold()) & (pd.to_datetime(starts["date"]) < target)].sort_values("date")
    def mean_tail(col, n, default=np.nan):
        x = g[col].tail(n)
        return float(x.mean()) if len(x) else default
    def pct_tail(n):
        x = g.tail(n)
        if x.empty or float(x["shots_against"].sum()) <= 0:
            return np.nan
        return float(x["saves"].sum() / x["shots_against"].sum())
    if g.empty:
        return {"goalie_shots_against_r5":np.nan,"goalie_shots_against_r10":np.nan,"save_pct_r5":np.nan,
                "save_pct_r10":np.nan,"days_rest":7.0,"starts_last_7d":0.0,"history_starts":0}
    last = pd.Timestamp(g.iloc[-1]["date"])
    starts_7 = int(((target - pd.to_datetime(g["date"])).dt.days.between(1, 7)).sum())
    return {
        "goalie_shots_against_r5": mean_tail("shots_against", 5),
        "goalie_shots_against_r10": mean_tail("shots_against", 10),
        "save_pct_r5": pct_tail(5), "save_pct_r10": pct_tail(10),
        "days_rest": float(max(0, min(30, (target - last).days))), "starts_last_7d": float(starts_7),
        "history_starts": int(len(g)),
    }


def resolve_goalie(starts: pd.DataFrame, name: str) -> str | None:
    g = starts[starts["goalie_name"].str.casefold() == name.casefold()]
    return None if g.empty else str(g.sort_values("date").iloc[-1]["goalie_id"])


def current_feature_rows(board: pd.DataFrame, starts: pd.DataFrame, team_games: pd.DataFrame, target_date: str) -> pd.DataFrame:
    target = pd.Timestamp(target_date)
    rows = []
    for _, r in board.iterrows():
        name = str(r["goalie_name"])
        gid = resolve_goalie(starts, name)
        own = recent_team(team_games, str(r["team"]), target)
        opp = recent_team(team_games, str(r["opponent"]), target)
        gr = recent_goalie(starts, gid, name, target)
        rows.append({**r.to_dict(), "goalie_id": gid or f"UNKNOWN::{name}", "is_home": float(r["is_home"]),
            "days_rest": gr["days_rest"], "starts_last_7d": gr["starts_last_7d"],
            "team_shots_against_r5": own["team_shots_against_r5"], "team_shots_against_r10": own["team_shots_against_r10"],
            "opponent_shots_for_r5": opp["shots_for_r5"], "opponent_shots_for_r10": opp["shots_for_r10"],
            "opponent_goals_for_r5": opp["goals_for_r5"], "team_goals_against_r5": own["team_goals_against_r5"],
            "save_pct_r5": gr["save_pct_r5"], "save_pct_r10": gr["save_pct_r10"],
            "goalie_shots_against_r5": gr["goalie_shots_against_r5"], "goalie_shots_against_r10": gr["goalie_shots_against_r10"],
            "history_starts": gr["history_starts"]})
    return pd.DataFrame(rows)


def choose_side(p_over: float, over_odds: int, p_under: float, under_odds: int) -> dict:
    oi, ui = american_to_implied(int(over_odds)), american_to_implied(int(under_odds))
    oroi, uroi = expected_roi(p_over, int(over_odds)), expected_roi(p_under, int(under_odds))
    if oroi >= uroi:
        return {"pick":"Over","pick_probability":p_over,"pick_odds":int(over_odds),"edge":p_over-oi,"expected_roi":oroi}
    return {"pick":"Under","pick_probability":p_under,"pick_odds":int(under_odds),"edge":p_under-ui,"expected_roi":uroi}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--features", required=True)
    ap.add_argument("--team-games", required=True)
    ap.add_argument("--odds", required=True)
    ap.add_argument("--config", default="config/goalie_shadow_v0.2.yaml")
    ap.add_argument("--target-date", required=True)
    ap.add_argument("--predictions", required=True)
    ap.add_argument("--metrics", required=True)
    ap.add_argument("--shadow-model", default="models/goalie_saves_shadow_v0.2.joblib")
    ap.add_argument("--official-model", default="models/goalie_saves_v0.1_reconstructed.joblib")
    args = ap.parse_args()

    starts = pd.read_parquet(args.features)
    team_games = pd.read_parquet(args.team_games)
    board = pd.read_csv(args.odds)
    cfg = yaml.safe_load(Path(args.config).read_text())
    historical = starts[pd.to_datetime(starts["date"]) < pd.Timestamp("2026-07-01")].copy()

    workload_features = cfg["workload"]["numeric"] + cfg["workload"]["categorical"]
    skill_features = cfg["save_rate"]["numeric"] + cfg["save_rate"]["categorical"]
    shadow = train_goalie_two_stage_shadow(historical, workload_features, cfg["workload"]["categorical"],
                                           skill_features, cfg["save_rate"]["categorical"])
    Path(args.shadow_model).parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(shadow, args.shadow_model)

    season_frames = [season_goalie_frame(starts, s) for s in SEASONS_OFFICIAL]
    transitions = build_goalie_transitions(season_frames, min_starts=5)
    official = train_goalie_transition_model(transitions)
    joblib.dump(official, args.official_model)

    current = current_feature_rows(board, starts, team_games, args.target_date)
    exp_shots, exp_sv, exp_saves = shadow.predict_components(current)
    prior = season_frames[-1].copy(); prior["playerId"] = prior["playerId"].astype(str)
    league_fallback = float((prior["saves"] / prior["gamesStarted"].clip(lower=1)).median())

    records = []
    for i, row in current.reset_index(drop=True).iterrows():
        gid = str(row["goalie_id"]); pprev = prior[prior["playerId"] == gid]
        if len(pprev):
            mu01 = float(official.predict_saves_per_start(pprev.iloc[[0]])[0]); basis01 = "goalie_transition_ml_reconstructed"
        else:
            mu01 = league_fallback; basis01 = "goalie_transition_fallback_no_2025_26"
        line = float(row["line"])
        p01o, p01u = float(prob_over_line(line, mu01, None)), float(prob_under_line(line, mu01, None))
        p02o, p02u = float(shadow.prob_over(current.iloc[[i]], line)[0]), float(shadow.prob_under(current.iloc[[i]], line)[0])
        pick01 = choose_side(p01o, int(row["over_odds"]), p01u, int(row["under_odds"]))
        pick02 = choose_side(p02o, int(row["over_odds"]), p02u, int(row["under_odds"]))
        records.append({"date":row["date"],"game":row["game"],"goalie_name":row["goalie_name"],"team":row["team"],
            "opponent":row["opponent"],"line":line,"over_odds":int(row["over_odds"]),"under_odds":int(row["under_odds"]),
            "history_starts":int(row["history_starts"]),"v0_1_expected_saves":mu01,"v0_1_over_probability":p01o,
            "v0_1_under_probability":p01u,"v0_1_pick":pick01["pick"],"v0_1_pick_probability":pick01["pick_probability"],
            "v0_1_pick_odds":pick01["pick_odds"],"v0_1_edge":pick01["edge"],"v0_1_expected_roi":pick01["expected_roi"],
            "v0_1_basis":basis01,"v0_2_expected_shots":float(exp_shots[i]),"v0_2_expected_save_pct":float(exp_sv[i]),
            "v0_2_expected_saves":float(exp_saves[i]),"v0_2_over_probability":p02o,"v0_2_under_probability":p02u,
            "v0_2_pick":pick02["pick"],"v0_2_pick_probability":pick02["pick_probability"],"v0_2_pick_odds":pick02["pick_odds"],
            "v0_2_edge":pick02["edge"],"v0_2_expected_roi":pick02["expected_roi"],"v0_2_status":"SHADOW_ONLY"})

    pred = pd.DataFrame(records)
    Path(args.predictions).parent.mkdir(parents=True, exist_ok=True)
    pred.to_csv(args.predictions, index=False)
    payload = {"target_date":args.target_date,
        "official_v0_1_reconstruction":{"transition_rows":int(len(transitions)),"alpha":official.alpha,
            "validation_mae_saves_per_start":official.validation_mae,"distribution":"Poisson",
            "notes":"Reconstructed from NHL regular-season starter boxscores, 2021-22 through 2025-26."},
        "shadow_v0_2":{"status":"SHADOW_ONLY","validation_metrics":shadow.validation_metrics},"rows":int(len(pred))}
    Path(args.metrics).write_text(json.dumps(payload, indent=2))
    print(pred.to_string(index=False)); print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
