from __future__ import annotations

import argparse
import json
from pathlib import Path

import joblib
import pandas as pd
import yaml

from wshlx_nhl.goalie_shadow import train_goalie_two_stage_shadow


def main():
    ap = argparse.ArgumentParser(description="Train the shadow v0.2 two-stage goalie saves model.")
    ap.add_argument("--data", default="data/processed/goalie_features.parquet")
    ap.add_argument("--config", default="config/goalie_shadow_v0.2.yaml")
    ap.add_argument("--output", default="models/goalie_saves_shadow_v0.2.joblib")
    ap.add_argument("--metrics", default="data/model_runs/goalie_shadow_v0.2_validation.json")
    ap.add_argument("--date-col", default="date")
    args = ap.parse_args()

    data_path = Path(args.data)
    if not data_path.exists():
        raise FileNotFoundError(
            f"{data_path} does not exist. Build the goalie start-level feature table before training."
        )

    cfg = yaml.safe_load(Path(args.config).read_text())
    df = pd.read_parquet(data_path)

    workload_features = cfg["workload"]["numeric"] + cfg["workload"]["categorical"]
    skill_features = cfg["save_rate"]["numeric"] + cfg["save_rate"]["categorical"]
    shots_target = cfg["workload"].get("target", "shots_against")
    saves_target = cfg["save_rate"].get("target", "saves")

    bundle = train_goalie_two_stage_shadow(
        df=df,
        workload_features=workload_features,
        workload_categorical=cfg["workload"]["categorical"],
        skill_features=skill_features,
        skill_categorical=cfg["save_rate"]["categorical"],
        shots_target=shots_target,
        saves_target=saves_target,
        date_col=args.date_col,
    )

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(bundle, out)

    metrics_path = Path(args.metrics)
    metrics_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "model": "goalie_saves_shadow_v0.2",
        "status": "SHADOW_ONLY",
        "official_model_unchanged": "v0.1.0",
        "validation_metrics": bundle.validation_metrics,
        "promotion_rules": cfg.get("promotion", {}),
    }
    metrics_path.write_text(json.dumps(payload, indent=2))

    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
