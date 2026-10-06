from __future__ import annotations

import pandas as pd

from .selection import playable_price_card


FALLBACK_BASIS_TAGS = (
    "limited_history_fallback",
    "rookie_projection_fallback",
)


def add_shadow_risk_flags(df: pd.DataFrame) -> pd.DataFrame:
    """Tag known high-uncertainty cohorts without changing official v0.1 selection.

    This is deliberately conservative and shadow-only. It does not mutate model
    probabilities. It simply identifies cohorts that have repeated prospective
    calibration concerns and withholds them from the shadow challenger until more
    independent observations accumulate.
    """
    out = df.copy()
    out["shadow_risk_flag"] = ""
    out["shadow_eligible"] = True

    if "model_basis" in out.columns:
        basis = out["model_basis"].fillna("").astype(str).str.casefold()
        limited = pd.Series(False, index=out.index)
        for tag in FALLBACK_BASIS_TAGS:
            limited |= basis.str.contains(tag.casefold(), regex=False)
        out.loc[limited, "shadow_risk_flag"] = "LIMITED_HISTORY_QUARANTINE"
        out.loc[limited, "shadow_eligible"] = False

    if {"market", "model_probability"}.issubset(out.columns):
        rare_atg = (
            out["market"].eq("anytime_goal")
            & out["model_probability"].lt(0.25)
            & out["shadow_eligible"]
        )
        out.loc[rare_atg, "shadow_risk_flag"] = "LOW_PROB_ATG_REVIEW"
        out.loc[rare_atg, "shadow_eligible"] = False

    return out


def playable_price_shadow_v0_2(
    df: pd.DataFrame,
    min_expected_roi: float = 0.05,
    min_edge: dict[str, float] | None = None,
) -> pd.DataFrame:
    """Shadow challenger for Playable Price selection.

    First applies the exact official price gate, then withholds two cohorts under
    targeted review: tagged limited-history/rookie fallback and sub-25% anytime-goal
    candidates. This challenger must be tracked prospectively before any promotion.
    """
    official = playable_price_card(
        df,
        min_expected_roi=min_expected_roi,
        min_edge=min_edge,
    )
    flagged = add_shadow_risk_flags(official)
    out = flagged[flagged["shadow_eligible"]].copy()
    out["cohort"] = "PLAYABLE_PRICE_SHADOW_V0_2"
    out["rank"] = range(1, len(out) + 1)
    return out
