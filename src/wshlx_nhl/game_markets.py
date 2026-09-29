from __future__ import annotations

from dataclasses import dataclass
import numpy as np


@dataclass(frozen=True)
class GameProbabilities:
    home_ml: float
    away_ml: float
    home_cover: float | None = None
    away_cover: float | None = None
    over: float | None = None
    under: float | None = None


def simulate_game(
    home_mu: float,
    away_mu: float,
    runs: int = 20_000,
    home_spread: float | None = None,
    total_line: float | None = None,
    rng_seed: int = 42,
) -> GameProbabilities:
    """Monte Carlo from expected regulation+OT credited goals.

    Ties are resolved 50/50 for moneyline as a neutral approximation until a
    dedicated OT/SO module has enough prospective data to replace it.
    """
    rng = np.random.default_rng(rng_seed)
    hg = rng.poisson(max(home_mu, 1e-5), size=runs)
    ag = rng.poisson(max(away_mu, 1e-5), size=runs)
    ties = hg == ag
    home_w = (hg > ag).astype(float)
    home_w[ties] = 0.5
    home_ml = float(home_w.mean())
    away_ml = 1.0 - home_ml

    home_cover = away_cover = None
    if home_spread is not None:
        margin = hg - ag
        # For half-goal/1.5 lines there are no pushes. Pushes on integer lines
        # are excluded from win probability denominator.
        z = margin + float(home_spread)
        wins = z > 0
        pushes = z == 0
        denom = max(1, int((~pushes).sum()))
        home_cover = float(wins.sum() / denom)
        away_cover = 1.0 - home_cover

    over = under = None
    if total_line is not None:
        t = hg + ag
        wins = t > total_line
        losses = t < total_line
        denom = max(1, int((wins | losses).sum()))
        over = float(wins.sum() / denom)
        under = float(losses.sum() / denom)

    return GameProbabilities(home_ml, away_ml, home_cover, away_cover, over, under)
