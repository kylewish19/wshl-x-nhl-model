from __future__ import annotations

import numpy as np
from scipy.stats import nbinom, poisson


def estimate_nb_alpha(y_true: np.ndarray, mu_pred: np.ndarray, floor: float = 1e-4) -> float:
    """Method-of-moments overdispersion alpha where Var(Y)=mu+alpha*mu^2."""
    y = np.asarray(y_true, dtype=float)
    mu = np.clip(np.asarray(mu_pred, dtype=float), 1e-6, None)
    numer = np.mean((y - mu) ** 2 - mu)
    denom = np.mean(mu ** 2)
    if denom <= 0:
        return floor
    return float(max(numer / denom, floor))


def nb_params_from_mu_alpha(mu: np.ndarray | float, alpha: float):
    mu = np.clip(np.asarray(mu, dtype=float), 1e-9, None)
    alpha = max(float(alpha), 1e-9)
    n = 1.0 / alpha
    p = n / (n + mu)
    return n, p


def prob_at_least(k: int, mu: np.ndarray | float, alpha: float | None = None):
    if k <= 0:
        return np.ones_like(np.asarray(mu, dtype=float))
    if alpha is None or alpha <= 1e-4:
        return 1.0 - poisson.cdf(k - 1, mu)
    n, p = nb_params_from_mu_alpha(mu, alpha)
    return 1.0 - nbinom.cdf(k - 1, n, p)


def prob_over_line(line: float, mu: np.ndarray | float, alpha: float | None = None):
    # For x.5 markets, OVER means count >= floor(line)+1.
    threshold = int(np.floor(line)) + 1
    return prob_at_least(threshold, mu, alpha)


def prob_under_line(line: float, mu: np.ndarray | float, alpha: float | None = None):
    return 1.0 - prob_over_line(line, mu, alpha)
