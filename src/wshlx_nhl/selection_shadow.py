from __future__ import annotations

import re

import pandas as pd

from .odds import american_to_implied, expected_roi
from .selection import DEFAULT_MIN_EDGE, eligible_candidates, playable_price_card


FALLBACK_BASIS_TAGS = (
    "limited_history_fallback",
    "rookie_projection_fallback",
)

V0_3_PROBABILITY_FLOORS = {
    "moneyline": 0.00,
    "spread": 0.55,
    "total": 0.55,
    "anytime_goal": 1.01,  # temporary full quarantine while ATG is recalibrated
    "anytime_assist": 0.50,
    "goalie_saves": 0.58,
    "point_1plus": 0.55,
    "point_2plus": 0.45,
}


def add_shadow_risk_flags(df: pd.DataFrame) -> pd.DataFrame:
    """Tag known high-uncertainty cohorts without changing official v0.1 selection.

    This function remains the v0.2 risk layer. It does not mutate probabilities.
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
    """First Playable challenger: official gate plus targeted quarantines."""
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


def _settled_clean_history(history: pd.DataFrame | None, target_date: str | None) -> pd.DataFrame:
    """Return only clean, settled rows strictly before the slate being selected.

    v0.3 is prospective. Same-day outcomes and LATE_LOCK evidence are never allowed
    into the reliability haircut used to select a card.
    """
    if history is None or history.empty:
        return pd.DataFrame()

    out = history.copy()
    if "result" not in out.columns or "market" not in out.columns or "model_probability" not in out.columns:
        return pd.DataFrame()

    if "lock_type" in out.columns:
        late = out["lock_type"].fillna("").astype(str).str.contains("LATE_LOCK", case=False, regex=False)
        out = out[~late]
    if "source_file" in out.columns:
        late = out["source_file"].fillna("").astype(str).str.contains("LATE_LOCK", case=False, regex=False)
        out = out[~late]

    out = out[out["result"].astype(str).str.upper().isin(["WIN", "LOSS"])].copy()
    if "date" in out.columns:
        out["date"] = pd.to_datetime(out["date"], errors="coerce")
        out = out[out["date"].notna()]
        if target_date:
            out = out[out["date"] < pd.Timestamp(target_date)]
    elif target_date:
        # If chronology cannot be proved, do not use the rows for calibration.
        return pd.DataFrame()

    out["model_probability"] = pd.to_numeric(out["model_probability"], errors="coerce")
    return out[out["model_probability"].notna()].copy()


def market_reliability_table(
    history: pd.DataFrame | None,
    target_date: str | None,
    prior_weight: float = 20.0,
    min_history: int = 5,
    min_factor: float = 0.65,
) -> pd.DataFrame:
    """Build a conservative one-sided market reliability haircut.

    Historical graded Playable rows are a selected sample, not a full calibration
    universe, so v0.3 never uses them to *increase* a probability. They can only
    shrink a market that has prospectively hit below its own average raw forecast.
    The prior is centered on that market's average raw probability to avoid a tiny
    sample producing an extreme haircut.
    """
    clean = _settled_clean_history(history, target_date)
    cols = [
        "market",
        "history_n",
        "history_wins",
        "history_avg_raw_probability",
        "posterior_hit_probability",
        "reliability_factor",
    ]
    if clean.empty:
        return pd.DataFrame(columns=cols)

    rows: list[dict] = []
    for market, group in clean.groupby("market", dropna=False):
        n = int(len(group))
        avg_raw = float(group["model_probability"].mean())
        wins = int(group["result"].astype(str).str.upper().eq("WIN").sum())
        posterior = (prior_weight * avg_raw + wins) / max(prior_weight + n, 1.0)
        if n < min_history or avg_raw <= 0:
            factor = 1.0
        else:
            factor = posterior / avg_raw
            factor = max(float(min_factor), min(1.0, float(factor)))
        rows.append(
            {
                "market": market,
                "history_n": n,
                "history_wins": wins,
                "history_avg_raw_probability": avg_raw,
                "posterior_hit_probability": posterior,
                "reliability_factor": factor,
            }
        )
    return pd.DataFrame(rows, columns=cols)


def apply_market_reliability(
    df: pd.DataFrame,
    history: pd.DataFrame | None,
    target_date: str | None,
    prior_weight: float = 20.0,
    min_history: int = 5,
    min_factor: float = 0.65,
) -> pd.DataFrame:
    out = df.copy()
    table = market_reliability_table(
        history,
        target_date,
        prior_weight=prior_weight,
        min_history=min_history,
        min_factor=min_factor,
    )
    factors = table.set_index("market")["reliability_factor"].to_dict() if not table.empty else {}
    out["market_reliability_factor"] = out["market"].map(factors).fillna(1.0).astype(float)
    out["calibrated_probability"] = (
        out["model_probability"].astype(float) * out["market_reliability_factor"]
    ).clip(0.001, 0.999)
    return out


def _limited_history_mask(df: pd.DataFrame) -> pd.Series:
    if "model_basis" not in df.columns:
        return pd.Series(False, index=df.index)
    basis = df["model_basis"].fillna("").astype(str).str.casefold()
    mask = pd.Series(False, index=df.index)
    for tag in FALLBACK_BASIS_TAGS:
        mask |= basis.str.contains(tag.casefold(), regex=False)
    return mask


def _selection_subject(row: pd.Series) -> str:
    for col in ("player_name", "goalie_name", "selection"):
        if col in row.index and pd.notna(row[col]) and str(row[col]).strip():
            value = str(row[col]).strip()
            value = re.sub(r"\s+(Over|Under)$", "", value, flags=re.IGNORECASE)
            return value.casefold()
    return "unknown"


def _cluster_key(row: pd.Series) -> str:
    """Group bets whose result exposure is substantially the same underlying event."""
    game = str(row.get("game", "")).casefold()
    market = str(row.get("market", ""))
    subject = _selection_subject(row)

    if market in {"anytime_goal", "anytime_assist", "point_1plus", "point_2plus"}:
        return f"skater|{game}|{subject}"
    if market == "goalie_saves":
        return f"goalie|{game}|{subject}"
    if market in {"moneyline", "spread"}:
        return f"team_side|{game}|{subject}"
    if market == "total":
        return f"total|{game}|{subject}|{row.get('line', '')}"
    return f"other|{game}|{market}|{subject}|{row.get('line', '')}"


def playable_price_shadow_v0_3(
    df: pd.DataFrame,
    history: pd.DataFrame | None = None,
    target_date: str | None = None,
    min_expected_roi: float = 0.05,
    min_edge: dict[str, float] | None = None,
    probability_floors: dict[str, float] | None = None,
    prior_weight: float = 20.0,
    min_history: int = 5,
    min_reliability_factor: float = 0.65,
) -> pd.DataFrame:
    """Second Playable challenger: reliability, floors, quarantine, and exposure gate.

    This remains SHADOW_ONLY. Raw v0.1 model probabilities are preserved. Edge and
    EV for the challenger are calculated from a one-sided market reliability-adjusted
    probability that is based only on earlier clean settled Playable observations.
    """
    min_edge = {**DEFAULT_MIN_EDGE, **(min_edge or {})}
    floors = {**V0_3_PROBABILITY_FLOORS, **(probability_floors or {})}

    out = eligible_candidates(df)
    out = out.dropna(subset=["odds_american"]).copy()
    out = apply_market_reliability(
        out,
        history,
        target_date,
        prior_weight=prior_weight,
        min_history=min_history,
        min_factor=min_reliability_factor,
    )

    out["shadow_v0_3_risk_flag"] = ""
    out["shadow_v0_3_eligible"] = True

    limited = _limited_history_mask(out)
    out.loc[limited, "shadow_v0_3_risk_flag"] = "LIMITED_HISTORY_QUARANTINE"
    out.loc[limited, "shadow_v0_3_eligible"] = False

    atg = out["market"].eq("anytime_goal")
    out.loc[atg & out["shadow_v0_3_eligible"], "shadow_v0_3_risk_flag"] = "ATG_RECALIBRATION_QUARANTINE"
    out.loc[atg, "shadow_v0_3_eligible"] = False

    out["required_probability_floor"] = out["market"].map(floors).fillna(0.50)
    below_floor = out["calibrated_probability"] < out["required_probability_floor"]
    mark_floor = below_floor & out["shadow_v0_3_eligible"]
    out.loc[mark_floor, "shadow_v0_3_risk_flag"] = "MARKET_PROBABILITY_FLOOR"
    out.loc[below_floor, "shadow_v0_3_eligible"] = False

    out["implied_probability"] = out["odds_american"].map(american_to_implied)
    out["calibrated_edge"] = out["calibrated_probability"] - out["implied_probability"]
    out["calibrated_expected_roi"] = [
        expected_roi(p, o) for p, o in zip(out["calibrated_probability"], out["odds_american"])
    ]
    out["required_edge"] = out["market"].map(min_edge).fillna(0.05)

    price_ok = (
        out["calibrated_edge"].ge(out["required_edge"])
        & out["calibrated_expected_roi"].ge(min_expected_roi)
    )
    mark_price = ~price_ok & out["shadow_v0_3_eligible"]
    out.loc[mark_price, "shadow_v0_3_risk_flag"] = "CALIBRATED_PRICE_GATE"
    out.loc[~price_ok, "shadow_v0_3_eligible"] = False

    selected = out[out["shadow_v0_3_eligible"]].copy()
    if selected.empty:
        selected["cohort"] = pd.Series(dtype=str)
        selected["rank"] = pd.Series(dtype=int)
        return selected

    selected["exposure_cluster"] = selected.apply(_cluster_key, axis=1)
    # Within a correlated cluster, prioritize the safer calibrated hit probability;
    # expected ROI is only a tie-break. This prevents a volatile 2+ prop from beating
    # the same player's stronger 1+ prop solely because its plus-money payout is larger.
    selected = selected.sort_values(
        ["exposure_cluster", "calibrated_probability", "calibrated_expected_roi"],
        ascending=[True, False, False],
    )
    selected = selected.drop_duplicates("exposure_cluster", keep="first")
    selected = selected.sort_values(
        ["calibrated_expected_roi", "calibrated_probability"], ascending=[False, False]
    ).copy()
    selected["cohort"] = "PLAYABLE_PRICE_SHADOW_V0_3"
    selected["rank"] = range(1, len(selected) + 1)
    return selected
