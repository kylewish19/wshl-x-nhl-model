from __future__ import annotations

import pandas as pd


def add_rolling_features(
    df: pd.DataFrame,
    group_col: str,
    date_col: str,
    stat_cols: list[str],
    windows: tuple[int, ...] = (5, 10, 20),
) -> pd.DataFrame:
    """Leakage-safe rolling means: every row uses only prior games."""
    out = df.sort_values([group_col, date_col]).copy()
    g = out.groupby(group_col, group_keys=False)
    for col in stat_cols:
        shifted = g[col].shift(1)
        for w in windows:
            out[f"{col}_r{w}"] = shifted.groupby(out[group_col]).transform(lambda s: s.rolling(w, min_periods=1).mean())
    return out


def add_rest_features(df: pd.DataFrame, team_col: str, date_col: str) -> pd.DataFrame:
    out = df.sort_values([team_col, date_col]).copy()
    d = pd.to_datetime(out[date_col])
    prev = d.groupby(out[team_col]).shift(1)
    out["days_rest"] = (d - prev).dt.days.clip(lower=0, upper=10)
    out["back_to_back"] = (out["days_rest"] <= 1).astype(int)
    return out
