from __future__ import annotations

import numpy as np
import pandas as pd
from .odds import american_to_decimal


def grade_binary_picks(picks: pd.DataFrame, results: pd.DataFrame) -> pd.DataFrame:
    keys = ["date", "game_id", "market", "selection"]
    missing = [k for k in keys if k not in picks.columns or k not in results.columns]
    if missing:
        raise ValueError(f"Missing grading keys: {missing}")
    merged = picks.merge(results[keys + ["result"]], on=keys, how="left", suffixes=("", "_actual"))
    merged["hit"] = merged["result"].map({"WIN": 1.0, "LOSS": 0.0, "PUSH": np.nan})
    merged["brier"] = (merged["model_probability"] - merged["hit"]) ** 2

    if "odds_american" in merged.columns:
        def profit(row):
            if row["result"] == "PUSH":
                return 0.0
            if row["result"] == "LOSS":
                return -1.0
            if row["result"] == "WIN" and pd.notna(row["odds_american"]):
                return american_to_decimal(row["odds_american"]) - 1.0
            return np.nan
        merged["profit_units"] = merged.apply(profit, axis=1)
    return merged


def card_summary(graded: pd.DataFrame) -> dict:
    settled = graded[graded["result"].isin(["WIN", "LOSS"])].copy()
    wins = int((settled["result"] == "WIN").sum())
    losses = int((settled["result"] == "LOSS").sum())
    out = {
        "wins": wins,
        "losses": losses,
        "hit_rate": float(wins / max(wins + losses, 1)),
        "mean_brier": float(settled["brier"].mean()) if len(settled) else np.nan,
    }
    if "profit_units" in settled.columns and settled["profit_units"].notna().any():
        out["profit_units"] = float(settled["profit_units"].sum())
        out["roi"] = float(settled["profit_units"].sum() / max(settled["profit_units"].notna().sum(), 1))
    return out
