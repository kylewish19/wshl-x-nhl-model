from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_poisson_deviance
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from .distributions import estimate_nb_alpha, prob_over_line, prob_under_line
from .modeling import (
    CountModelBundle,
    chronological_split,
    exponential_recency_weights,
    train_count_model,
)


def _preprocessor(feature_columns: Iterable[str], categorical_columns: Iterable[str]):
    feature_columns = list(feature_columns)
    categorical_columns = list(categorical_columns)
    numeric = [c for c in feature_columns if c not in categorical_columns]
    return ColumnTransformer(
        transformers=[
            ("num", Pipeline([("imputer", SimpleImputer(strategy="median"))]), numeric),
            (
                "cat",
                Pipeline([
                    ("imputer", SimpleImputer(strategy="most_frequent")),
                    ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
                ]),
                categorical_columns,
            ),
        ],
        remainder="drop",
    )


def _logit(p: np.ndarray) -> np.ndarray:
    p = np.clip(np.asarray(p, dtype=float), 1e-6, 1.0 - 1e-6)
    return np.log(p / (1.0 - p))


def _sigmoid(x: np.ndarray) -> np.ndarray:
    x = np.asarray(x, dtype=float)
    return 1.0 / (1.0 + np.exp(-x))


@dataclass
class SaveRateModelBundle:
    primary: Pipeline
    baseline: Pipeline
    feature_columns: list[str]
    categorical_columns: list[str]
    validation_metrics: dict
    primary_weight: float = 0.80

    def predict_save_pct(self, X: pd.DataFrame) -> np.ndarray:
        cols = self.feature_columns
        p1 = _sigmoid(self.primary.predict(X[cols]))
        p2 = _sigmoid(self.baseline.predict(X[cols]))
        pred = self.primary_weight * p1 + (1.0 - self.primary_weight) * p2
        # Guardrails are deliberately broad; the model still determines movement inside them.
        return np.clip(pred, 0.80, 0.97)


def train_save_rate_model(
    df: pd.DataFrame,
    feature_columns: list[str],
    categorical_columns: list[str] | None = None,
    saves_col: str = "saves",
    shots_col: str = "shots_against",
    date_col: str = "date",
    validation_fraction: float = 0.20,
    half_life_days: float = 730.0,
    random_state: int = 42,
) -> SaveRateModelBundle:
    categorical_columns = categorical_columns or []
    clean = df.dropna(subset=[saves_col, shots_col, date_col]).copy()
    clean = clean[clean[shots_col] > 0].copy()
    train, valid = chronological_split(clean, date_col, validation_fraction)
    if len(train) < 100:
        raise ValueError(f"Not enough goalie-start rows to train save rate: {len(train)}")

    # Jeffreys-style smoothing avoids infinite logits for perfect/zero outcomes.
    smoothed = (train[saves_col].to_numpy(dtype=float) + 0.5) / (
        train[shots_col].to_numpy(dtype=float) + 1.0
    )
    y_train = _logit(np.clip(smoothed, 0.80, 0.97))

    pre = _preprocessor(feature_columns, categorical_columns)
    primary = Pipeline([
        ("pre", pre),
        (
            "model",
            HistGradientBoostingRegressor(
                loss="squared_error",
                learning_rate=0.04,
                max_iter=300,
                max_leaf_nodes=15,
                min_samples_leaf=25,
                l2_regularization=2.0,
                random_state=random_state,
            ),
        ),
    ])

    pre2 = _preprocessor(feature_columns, categorical_columns)
    baseline = Pipeline([
        ("pre", pre2),
        ("scale", StandardScaler()),
        ("model", Ridge(alpha=3.0)),
    ])

    recency = exponential_recency_weights(train[date_col], half_life_days)
    shot_weight = np.sqrt(np.clip(train[shots_col].to_numpy(dtype=float), 1.0, None))
    weights = recency * shot_weight
    primary.fit(train[feature_columns], y_train, model__sample_weight=weights)
    baseline.fit(train[feature_columns], y_train, model__sample_weight=weights)

    bundle = SaveRateModelBundle(
        primary=primary,
        baseline=baseline,
        feature_columns=list(feature_columns),
        categorical_columns=list(categorical_columns),
        validation_metrics={},
    )

    if len(valid):
        pred = bundle.predict_save_pct(valid)
        actual = valid[saves_col].to_numpy(dtype=float) / np.clip(
            valid[shots_col].to_numpy(dtype=float), 1.0, None
        )
        bundle.validation_metrics = {
            "validation_rows": int(len(valid)),
            "save_pct_mae": float(mean_absolute_error(actual, pred)),
        }
    else:
        bundle.validation_metrics = {"validation_rows": 0}
    return bundle


@dataclass
class GoalieTwoStageShadowBundle:
    workload_model: CountModelBundle
    save_rate_model: SaveRateModelBundle
    alpha: float
    validation_metrics: dict
    shots_target: str = "shots_against"
    saves_target: str = "saves"

    def predict_components(self, X: pd.DataFrame) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        expected_shots = np.clip(self.workload_model.predict_mu(X), 5.0, 60.0)
        expected_save_pct = self.save_rate_model.predict_save_pct(X)
        expected_saves = np.clip(expected_shots * expected_save_pct, 3.0, 58.0)
        return expected_shots, expected_save_pct, expected_saves

    def predict_mu_saves(self, X: pd.DataFrame) -> np.ndarray:
        return self.predict_components(X)[2]

    def prob_over(self, X: pd.DataFrame, line: float) -> np.ndarray:
        return prob_over_line(line, self.predict_mu_saves(X), self.alpha)

    def prob_under(self, X: pd.DataFrame, line: float) -> np.ndarray:
        return prob_under_line(line, self.predict_mu_saves(X), self.alpha)


def train_goalie_two_stage_shadow(
    df: pd.DataFrame,
    workload_features: list[str],
    workload_categorical: list[str],
    skill_features: list[str],
    skill_categorical: list[str],
    shots_target: str = "shots_against",
    saves_target: str = "saves",
    date_col: str = "date",
    validation_fraction: float = 0.20,
    half_life_days: float = 730.0,
    random_state: int = 42,
) -> GoalieTwoStageShadowBundle:
    required = set(
        workload_features
        + skill_features
        + [shots_target, saves_target, date_col]
    )
    missing = sorted(c for c in required if c not in df.columns)
    if missing:
        raise ValueError(f"Missing goalie-shadow columns: {missing}")

    clean = df.dropna(subset=[shots_target, saves_target, date_col]).copy()
    clean = clean[clean[shots_target] > 0].copy()

    workload = train_count_model(
        df=clean,
        target=shots_target,
        feature_columns=workload_features,
        categorical_columns=workload_categorical,
        date_col=date_col,
        validation_fraction=validation_fraction,
        half_life_days=half_life_days,
        random_state=random_state,
    )
    save_rate = train_save_rate_model(
        df=clean,
        feature_columns=skill_features,
        categorical_columns=skill_categorical,
        saves_col=saves_target,
        shots_col=shots_target,
        date_col=date_col,
        validation_fraction=validation_fraction,
        half_life_days=half_life_days,
        random_state=random_state,
    )

    _, valid = chronological_split(clean, date_col, validation_fraction)
    if len(valid):
        expected_shots = np.clip(workload.predict_mu(valid), 5.0, 60.0)
        expected_save_pct = save_rate.predict_save_pct(valid)
        mu_saves = np.clip(expected_shots * expected_save_pct, 3.0, 58.0)
        actual_saves = valid[saves_target].to_numpy(dtype=float)
        alpha = estimate_nb_alpha(actual_saves, mu_saves)
        metrics = {
            "validation_rows": int(len(valid)),
            "shots_mae": float(mean_absolute_error(valid[shots_target], expected_shots)),
            "save_pct_mae": float(save_rate.validation_metrics.get("save_pct_mae", np.nan)),
            "saves_mae": float(mean_absolute_error(actual_saves, mu_saves)),
            "saves_poisson_deviance": float(
                mean_poisson_deviance(actual_saves, np.clip(mu_saves, 1e-5, None))
            ),
            "nb_alpha": float(alpha),
        }
    else:
        alpha = 0.10
        metrics = {"validation_rows": 0, "nb_alpha": alpha}

    return GoalieTwoStageShadowBundle(
        workload_model=workload,
        save_rate_model=save_rate,
        alpha=float(alpha),
        validation_metrics=metrics,
        shots_target=shots_target,
        saves_target=saves_target,
    )
