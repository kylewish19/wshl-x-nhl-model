from __future__ import annotations

import argparse
import json
from pathlib import Path
import joblib
import pandas as pd
import yaml

from wshlx_nhl.modeling import train_count_model

MARKETS = {
    "game_goals": ("game_team_features.parquet", "goals"),
    "player_goals": ("player_features.parquet", "goals"),
    "player_assists": ("player_features.parquet", "assists"),
    "player_points": ("player_features.parquet", "points"),
    "goalie_saves": ("goalie_features.parquet", "saves"),
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", default="data/processed")
    ap.add_argument("--model-dir", default="models")
    ap.add_argument("--spec", default="config/feature_specs.yaml")
    args = ap.parse_args()

    spec = yaml.safe_load(Path(args.spec).read_text())
    out_dir = Path(args.model_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    metrics = {}

    for model_name, (filename, target) in MARKETS.items():
        path = Path(args.data_dir) / filename
        if not path.exists():
            print(f"SKIP {model_name}: {path} not found")
            continue
        df = pd.read_parquet(path)
        cols = spec[model_name]["numeric"] + spec[model_name]["categorical"]
        missing = [c for c in cols + [target, "date"] if c not in df.columns]
        if missing:
            print(f"SKIP {model_name}: missing columns {missing}")
            continue
        bundle = train_count_model(
            df=df,
            target=target,
            feature_columns=cols,
            categorical_columns=spec[model_name]["categorical"],
        )
        joblib.dump(bundle, out_dir / f"{model_name}.joblib")
        metrics[model_name] = bundle.validation_metrics
        print(f"TRAINED {model_name}: {bundle.validation_metrics}")

    (out_dir / "validation_metrics.json").write_text(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
