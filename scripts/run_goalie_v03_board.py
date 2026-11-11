from __future__ import annotations

import argparse
import json
from pathlib import Path

import joblib
import pandas as pd
import yaml

from scripts.run_goalie_board import current_feature_rows, choose_side
from wshlx_nhl.goalie_shadow import train_goalie_simulation_shadow


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--features", required=True)
    ap.add_argument("--team-games", required=True)
    ap.add_argument("--odds", required=True)
    ap.add_argument("--target-date", required=True)
    ap.add_argument("--config", default="config/goalie_shadow_v0.3.yaml")
    ap.add_argument("--predictions", required=True)
    ap.add_argument("--metrics", required=True)
    ap.add_argument("--model", default="models/goalie_saves_shadow_v0.3.joblib")
    args = ap.parse_args()

    starts = pd.read_parquet(args.features)
    team_games = pd.read_parquet(args.team_games)
    board = pd.read_csv(args.odds)
    cfg = yaml.safe_load(Path(args.config).read_text())

    target = pd.Timestamp(args.target_date)
    training = starts[pd.to_datetime(starts["date"]) < target].copy()

    workload_features = cfg["workload"]["numeric"] + cfg["workload"]["categorical"]
    save_features = cfg["save_rate"]["numeric"] + cfg["save_rate"]["categorical"]
    tcfg = cfg["training"]

    model = train_goalie_simulation_shadow(
        training,
        workload_features,
        cfg["workload"]["categorical"],
        save_features,
        cfg["save_rate"]["categorical"],
        validation_fraction=float(tcfg.get("validation_fraction", 0.20)),
        half_life_days=float(tcfg.get("half_life_days", 730)),
        random_state=int(tcfg.get("random_state", 42)),
        n_sims=int(tcfg.get("simulation_draws", 20000)),
    )
    Path(args.model).parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, args.model)

    current = current_feature_rows(board, starts, team_games, args.target_date).reset_index(drop=True)
    exp_shots, exp_sv, exp_saves = model.predict_components(current)
    p_over, p_under, p_push = model.simulate_probabilities(current, current["line"].to_numpy())

    rows = []
    for i, row in current.iterrows():
        side = choose_side(
            float(p_over[i]), int(row["over_odds"]),
            float(p_under[i]), int(row["under_odds"]),
        )
        rows.append({
            "date": row["date"],
            "game": row["game"],
            "goalie_name": row["goalie_name"],
            "team": row["team"],
            "opponent": row["opponent"],
            "goalie_id": row["goalie_id"],
            "line": float(row["line"]),
            "over_odds": int(row["over_odds"]),
            "under_odds": int(row["under_odds"]),
            "history_starts": int(row["history_starts"]),
            "v0_3_expected_shots": float(exp_shots[i]),
            "v0_3_expected_save_pct": float(exp_sv[i]),
            "v0_3_expected_saves": float(exp_saves[i]),
            "v0_3_over_probability": float(p_over[i]),
            "v0_3_under_probability": float(p_under[i]),
            "v0_3_push_probability": float(p_push[i]),
            "v0_3_pick": side["pick"],
            "v0_3_pick_probability": float(side["pick_probability"]),
            "v0_3_pick_odds": int(side["pick_odds"]),
            "v0_3_edge": float(side["edge"]),
            "v0_3_expected_roi": float(side["expected_roi"]),
            "v0_3_status": "SHADOW_ONLY",
        })

    pred = pd.DataFrame(rows)
    Path(args.predictions).parent.mkdir(parents=True, exist_ok=True)
    pred.to_csv(args.predictions, index=False)

    payload = {
        "target_date": args.target_date,
        "shadow_version": "v0.3",
        "status": "SHADOW_ONLY",
        "training_includes_current_season": True,
        "training_rows": int(len(training)),
        "training_end": str(pd.to_datetime(training["date"]).max().date()),
        "simulation_draws": int(model.n_sims),
        "validation_metrics": model.validation_metrics,
        "rows": int(len(pred)),
    }
    Path(args.metrics).write_text(json.dumps(payload, indent=2))
    print(pred.to_string(index=False))
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
