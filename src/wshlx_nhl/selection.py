from __future__ import annotations

import pandas as pd
from .odds import american_to_implied, expected_roi

DEFAULT_MIN_EDGE = {
    "moneyline": 0.03,
    "spread": 0.03,
    "total": 0.03,
    "anytime_goal": 0.05,
    "anytime_assist": 0.04,
    "goalie_saves": 0.04,
    "point_1plus": 0.04,
    "point_2plus": 0.05,
}


def eligible_candidates(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    if "active" in out.columns:
        out = out[out["active"].fillna(1).astype(bool)]
    if "market" in out.columns and "starter_confirmed" in out.columns:
        goalie = out["market"].eq("goalie_saves")
        confirmed = out["starter_confirmed"].fillna(0).astype(bool)
        out = out[~goalie | confirmed]
    return out.dropna(subset=["model_probability"]).copy()


def top_probability_card(df: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    out = eligible_candidates(df)
    out = out.sort_values(["model_probability", "market"], ascending=[False, True]).head(n).copy()
    out["cohort"] = "TOP10_PROBABILITY"
    out["rank"] = range(1, len(out) + 1)
    return out


def playable_price_card(
    df: pd.DataFrame,
    min_expected_roi: float = 0.05,
    min_edge: dict[str, float] | None = None,
) -> pd.DataFrame:
    min_edge = {**DEFAULT_MIN_EDGE, **(min_edge or {})}
    out = eligible_candidates(df)
    out = out.dropna(subset=["odds_american"]).copy()
    out["implied_probability"] = out["odds_american"].map(american_to_implied)
    out["edge"] = out["model_probability"] - out["implied_probability"]
    out["expected_roi"] = [expected_roi(p, o) for p, o in zip(out["model_probability"], out["odds_american"])]
    out["required_edge"] = out["market"].map(min_edge).fillna(0.05)
    out = out[(out["edge"] >= out["required_edge"]) & (out["expected_roi"] >= min_expected_roi)]
    out = out.sort_values(["expected_roi", "model_probability"], ascending=False).copy()
    out["cohort"] = "PLAYABLE_PRICE"
    out["rank"] = range(1, len(out) + 1)
    return out
