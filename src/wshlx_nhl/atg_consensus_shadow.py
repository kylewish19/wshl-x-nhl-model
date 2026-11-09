from __future__ import annotations

import pandas as pd

from .odds import american_to_implied, expected_roi


FALLBACK_TAGS = (
    "limited_history_fallback",
    "rookie_projection_fallback",
)


def atg_consensus_shadow(
    df: pd.DataFrame,
    *,
    min_probability: float = 0.30,
    max_model_disagreement: float = 0.12,
    min_edge: float = 0.05,
    min_expected_roi: float = 0.05,
    min_current_gp: int = 8,
) -> pd.DataFrame:
    """Conservative anytime-goal research card.

    Required input columns:
      player_name, odds_american, official_probability,
      current_season_probability, model_basis

    Optional:
      current_gp, game, team

    This is SHADOW_ONLY and must never alter Official Top 10 or Official
    Playable results. The consensus probability is the lower of the two
    independent scorer estimates, so the shadow never increases confidence
    beyond either component model.
    """
    out = df.copy()

    required = {
        "player_name",
        "odds_american",
        "official_probability",
        "current_season_probability",
    }
    missing = required.difference(out.columns)
    if missing:
        raise ValueError(f"Missing ATG consensus columns: {sorted(missing)}")

    out["official_probability"] = pd.to_numeric(out["official_probability"], errors="coerce")
    out["current_season_probability"] = pd.to_numeric(
        out["current_season_probability"], errors="coerce"
    )
    out["odds_american"] = pd.to_numeric(out["odds_american"], errors="coerce")
    out = out.dropna(
        subset=["official_probability", "current_season_probability", "odds_american"]
    ).copy()

    if "model_basis" in out.columns:
        basis = out["model_basis"].fillna("").astype(str).str.casefold()
        fallback = pd.Series(False, index=out.index)
        for tag in FALLBACK_TAGS:
            fallback |= basis.str.contains(tag.casefold(), regex=False)
        out = out[~fallback].copy()

    if "current_gp" in out.columns:
        gp = pd.to_numeric(out["current_gp"], errors="coerce").fillna(0)
        out = out[gp >= min_current_gp].copy()

    out["model_disagreement"] = (
        out["official_probability"] - out["current_season_probability"]
    ).abs()
    out["consensus_probability"] = out[
        ["official_probability", "current_season_probability"]
    ].min(axis=1)

    out["implied_probability"] = out["odds_american"].map(american_to_implied)
    out["consensus_edge"] = out["consensus_probability"] - out["implied_probability"]
    out["consensus_expected_roi"] = [
        expected_roi(p, o)
        for p, o in zip(out["consensus_probability"], out["odds_american"])
    ]

    out = out[
        out["consensus_probability"].ge(min_probability)
        & out["model_disagreement"].le(max_model_disagreement)
        & out["consensus_edge"].ge(min_edge)
        & out["consensus_expected_roi"].ge(min_expected_roi)
    ].copy()

    out = out.sort_values(
        ["consensus_probability", "consensus_expected_roi"],
        ascending=[False, False],
    )
    out["cohort"] = "ATG_CONSENSUS_SHADOW_V0_1"
    out["rank"] = range(1, len(out) + 1)
    return out
