from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.linear_model import PoissonRegressor
from sklearn.metrics import mean_absolute_error, mean_poisson_deviance

from .distributions import estimate_nb_alpha


@dataclass
class CountModelBundle:
    primary: Pipeline
    baseline: Pipeline
    alpha: float
    feature_columns: list[str]
    categorical_columns: list[str]
    validation_metrics: dict

    def predict_mu(self, X: pd.DataFrame) -> np.ndarray:
        p1 = np.clip(self.primary.predict(X[self.feature_columns]), 1e-5, None)
        p2 = np.clip(self.baseline.predict(X[self.feature_columns]), 1e-5, None)
        # Mild ensemble stabilizes opening-season extrapolation.
        return 0.80 * p1 + 0.20 * p2


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


def exponential_recency_weights(dates: pd.Series, half_life_days: float = 730.0) -> np.ndarray:
    d = pd.to_datetime(dates)
    newest = d.max()
    age = (newest - d).dt.days.clip(lower=0).to_numpy(dtype=float)
    return np.power(0.5, age / float(half_life_days))


def chronological_split(df: pd.DataFrame, date_col: str, validation_fraction: float = 0.20):
    ordered = df.sort_values(date_col).reset_index(drop=True)
    cut = max(1, int(len(ordered) * (1.0 - validation_fraction)))
    return ordered.iloc[:cut].copy(), ordered.iloc[cut:].copy()


def train_count_model(
    df: pd.DataFrame,
    target: str,
    feature_columns: list[str],
    categorical_columns: list[str] | None = None,
    date_col: str = "date",
    validation_fraction: float = 0.20,
    half_life_days: float = 730.0,
    random_state: int = 42,
) -> CountModelBundle:
    categorical_columns = categorical_columns or []
    clean = df.dropna(subset=[target, date_col]).copy()
    train, valid = chronological_split(clean, date_col, validation_fraction)
    if len(train) < 100:
        raise ValueError(f"Not enough rows to train {target}: {len(train)}")

    pre = _preprocessor(feature_columns, categorical_columns)
    primary = Pipeline([
        ("pre", pre),
        (
            "model",
            HistGradientBoostingRegressor(
                loss="poisson",
                learning_rate=0.045,
                max_iter=350,
                max_leaf_nodes=31,
                min_samples_leaf=25,
                l2_regularization=1.0,
                random_state=random_state,
            ),
        ),
    ])

    # A simple Poisson GLM baseline provides shrinkage/stability.
    pre2 = _preprocessor(feature_columns, categorical_columns)
    baseline = Pipeline([
        ("pre", pre2),
        ("scale", StandardScaler(with_mean=False)),
        ("model", PoissonRegressor(alpha=0.25, max_iter=500)),
    ])

    w = exponential_recency_weights(train[date_col], half_life_days)
    primary.fit(train[feature_columns], train[target], model__sample_weight=w)
    baseline.fit(train[feature_columns], train[target], model__sample_weight=w)

    if len(valid):
        v1 = np.clip(primary.predict(valid[feature_columns]), 1e-5, None)
        v2 = np.clip(baseline.predict(valid[feature_columns]), 1e-5, None)
        mu = 0.80 * v1 + 0.20 * v2
        alpha = estimate_nb_alpha(valid[target].to_numpy(), mu)
        metrics = {
            "validation_rows": int(len(valid)),
            "mae": float(mean_absolute_error(valid[target], mu)),
            "poisson_deviance": float(mean_poisson_deviance(valid[target], np.clip(mu, 1e-5, None))),
            "nb_alpha": float(alpha),
        }
    else:
        alpha = 0.10
        metrics = {"validation_rows": 0, "nb_alpha": alpha}

    return CountModelBundle(
        primary=primary,
        baseline=baseline,
        alpha=float(alpha),
        feature_columns=list(feature_columns),
        categorical_columns=list(categorical_columns),
        validation_metrics=metrics,
    )
