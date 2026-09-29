from __future__ import annotations

from dataclasses import dataclass
from typing import Callable
import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


SKATER_FEATURES = [
    "log_games",
    "goals_pg",
    "assists_pg",
    "points_pg",
    "shots_pg",
    "pp_goals_pg",
    "pp_points_pg",
    "toi20",
    "shooting_pct",
    "is_defense",
    "is_center",
    "is_wing",
]


def skater_feature_frame(df: pd.DataFrame) -> pd.DataFrame:
    gp = df["gamesPlayed"].clip(lower=1).astype(float)
    out = pd.DataFrame(index=df.index)
    out["log_games"] = np.log1p(gp)
    out["goals_pg"] = df["goals"].fillna(0) / gp
    out["assists_pg"] = df["assists"].fillna(0) / gp
    out["points_pg"] = df["points"].fillna(0) / gp
    out["shots_pg"] = df["shots"].fillna(0) / gp
    out["pp_goals_pg"] = df["ppGoals"].fillna(0) / gp
    out["pp_points_pg"] = df["ppPoints"].fillna(0) / gp
    out["toi20"] = (df["timeOnIcePerGame"].fillna(0) / 60.0) / 20.0
    out["shooting_pct"] = df["shootingPct"].fillna(0)
    pos = df["positionCode"].fillna("")
    out["is_defense"] = pos.eq("D").astype(float)
    out["is_center"] = pos.eq("C").astype(float)
    out["is_wing"] = pos.isin(["L", "R"]).astype(float)
    return out


def build_skater_transitions(seasons: list[pd.DataFrame], min_games: int = 10) -> pd.DataFrame:
    rows: list[pd.DataFrame] = []
    for idx in range(len(seasons) - 1):
        prev = seasons[idx].copy()
        nxt = seasons[idx + 1].copy()
        keep = ["playerId", "gamesPlayed", "goals", "assists", "points", "shots",
                "ppGoals", "ppPoints", "timeOnIcePerGame", "shootingPct", "positionCode"]
        prev = prev[keep]
        nxt = nxt[["playerId", "gamesPlayed", "goals", "assists", "points"]]
        merged = prev.merge(nxt, on="playerId", suffixes=("_prev", "_next"))
        merged = merged[
            (merged["gamesPlayed_prev"] >= min_games)
            & (merged["gamesPlayed_next"] >= min_games)
        ].copy()
        renamed = pd.DataFrame({
            "playerId": merged["playerId"],
            "gamesPlayed": merged["gamesPlayed_prev"],
            "goals": merged["goals_prev"],
            "assists": merged["assists_prev"],
            "points": merged["points_prev"],
            "shots": merged["shots"],
            "ppGoals": merged["ppGoals"],
            "ppPoints": merged["ppPoints"],
            "timeOnIcePerGame": merged["timeOnIcePerGame"],
            "shootingPct": merged["shootingPct"],
            "positionCode": merged["positionCode"],
            "next_goals_pg": merged["goals_next"] / merged["gamesPlayed_next"],
            "next_assists_pg": merged["assists_next"] / merged["gamesPlayed_next"],
            "next_points_pg": merged["points_next"] / merged["gamesPlayed_next"],
            "transition": idx,
        })
        rows.append(renamed)
    return pd.concat(rows, ignore_index=True)


@dataclass
class TransitionRateModel:
    target: str
    alpha: float
    pipeline: Pipeline
    validation_mae: float

    def predict(self, previous_season: pd.DataFrame) -> np.ndarray:
        X = skater_feature_frame(previous_season)
        pred = np.exp(self.pipeline.predict(X)) - 0.02
        return np.clip(pred, 0, None)


def train_transition_rate_model(
    transitions: pd.DataFrame,
    target: str,
    alpha_grid: tuple[float, ...] = (0.3, 1.0, 3.0, 10.0, 30.0),
) -> TransitionRateModel:
    latest = int(transitions["transition"].max())
    train = transitions[transitions["transition"] < latest].copy()
    valid = transitions[transitions["transition"] == latest].copy()

    def target_values(frame: pd.DataFrame) -> np.ndarray:
        return np.log(frame[target].clip(lower=0).to_numpy(dtype=float) + 0.02)

    best_alpha = None
    best_mae = float("inf")
    for alpha in alpha_grid:
        model = Pipeline([
            ("scale", StandardScaler()),
            ("ridge", Ridge(alpha=alpha)),
        ])
        model.fit(skater_feature_frame(train), target_values(train))
        pred = np.exp(model.predict(skater_feature_frame(valid))) - 0.02
        mae = float(np.mean(np.abs(np.clip(pred, 0, None) - valid[target].to_numpy())))
        if mae < best_mae:
            best_mae = mae
            best_alpha = alpha

    final = Pipeline([
        ("scale", StandardScaler()),
        ("ridge", Ridge(alpha=float(best_alpha))),
    ])
    final.fit(skater_feature_frame(transitions), target_values(transitions))
    return TransitionRateModel(target, float(best_alpha), final, best_mae)


GOALIE_FEATURES = [
    "log_starts", "save_pct", "saves_per_start", "shots_per_start",
    "gaa", "wins_per_start", "hours_per_start", "log_games",
]


def goalie_feature_frame(df: pd.DataFrame) -> pd.DataFrame:
    gs = df["gamesStarted"].clip(lower=1).astype(float)
    gp = df["gamesPlayed"].clip(lower=1).astype(float)
    return pd.DataFrame({
        "log_starts": np.log1p(gs),
        "save_pct": df["savePct"].fillna(0.9),
        "saves_per_start": df["saves"].fillna(0) / gs,
        "shots_per_start": df["shotsAgainst"].fillna(0) / gs,
        "gaa": df["goalsAgainstAverage"].fillna(3.0),
        "wins_per_start": df["wins"].fillna(0) / gs,
        "hours_per_start": (df["timeOnIce"].fillna(0) / 3600.0) / gs,
        "log_games": np.log1p(gp),
    }, index=df.index)


def build_goalie_transitions(seasons: list[pd.DataFrame], min_starts: int = 5) -> pd.DataFrame:
    rows = []
    for idx in range(len(seasons) - 1):
        p = seasons[idx].copy()
        n = seasons[idx + 1][["playerId", "gamesStarted", "saves"]].copy()
        m = p.merge(n, on="playerId", suffixes=("_prev", "_next"))
        m = m[(m["gamesStarted_prev"] >= min_starts) & (m["gamesStarted_next"] >= min_starts)].copy()
        m["next_saves_per_start"] = m["saves_next"] / m["gamesStarted_next"]
        m["transition"] = idx
        rows.append(m)
    return pd.concat(rows, ignore_index=True)


@dataclass
class GoalieTransitionModel:
    alpha: float
    pipeline: Pipeline
    validation_mae: float

    def predict_saves_per_start(self, previous_season: pd.DataFrame) -> np.ndarray:
        pred = np.exp(self.pipeline.predict(goalie_feature_frame(previous_season))) - 0.5
        return np.clip(pred, 5, None)


def train_goalie_transition_model(
    transitions: pd.DataFrame,
    alpha_grid: tuple[float, ...] = (0.3, 1.0, 3.0, 10.0, 30.0),
) -> GoalieTransitionModel:
    latest = int(transitions["transition"].max())
    train = transitions[transitions["transition"] < latest]
    valid = transitions[transitions["transition"] == latest]

    best_alpha = None
    best_mae = float("inf")
    for alpha in alpha_grid:
        model = Pipeline([("scale", StandardScaler()), ("ridge", Ridge(alpha=alpha))])
        model.fit(goalie_feature_frame(train), np.log(train["next_saves_per_start"] + 0.5))
        pred = np.exp(model.predict(goalie_feature_frame(valid))) - 0.5
        mae = float(np.mean(np.abs(pred - valid["next_saves_per_start"].to_numpy())))
        if mae < best_mae:
            best_mae = mae
            best_alpha = alpha

    final = Pipeline([("scale", StandardScaler()), ("ridge", Ridge(alpha=float(best_alpha)))])
    final.fit(goalie_feature_frame(transitions), np.log(transitions["next_saves_per_start"] + 0.5))
    return GoalieTransitionModel(float(best_alpha), final, best_mae)
