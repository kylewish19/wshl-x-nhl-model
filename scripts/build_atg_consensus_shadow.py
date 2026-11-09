from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from wshlx_nhl.atg_consensus_shadow import atg_consensus_shadow


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--official-atg", required=True)
    ap.add_argument("--skater-snapshot", required=True)
    ap.add_argument("--output", required=True)
    args = ap.parse_args()

    official = pd.read_csv(args.official_atg)
    snapshot = pd.read_csv(args.skater_snapshot)

    if "player_id" not in official.columns or "player_id" not in snapshot.columns:
        raise ValueError("ATG consensus builder requires player_id in both inputs")

    snap_cols = [
        c for c in [
            "player_id",
            "shadow_goal_prob",
            "current_gp",
            "current_goals",
            "current_goals_pg",
        ]
        if c in snapshot.columns
    ]

    merged = official.merge(
        snapshot[snap_cols].drop_duplicates("player_id"),
        on="player_id",
        how="left",
    )
    merged["official_probability"] = merged["model_probability"]
    merged["current_season_probability"] = merged["shadow_goal_prob"]

    out = atg_consensus_shadow(merged)
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(args.output, index=False)

    print(f"Selected {len(out)} ATG consensus shadow candidates -> {args.output}")
    if not out.empty:
        cols = [
            c for c in [
                "player_name", "game", "team", "odds_american",
                "official_probability", "current_season_probability",
                "consensus_probability", "model_disagreement",
                "consensus_edge", "consensus_expected_roi",
            ]
            if c in out.columns
        ]
        print(out[cols].to_string(index=False))


if __name__ == "__main__":
    main()
