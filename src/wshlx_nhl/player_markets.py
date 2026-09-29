from __future__ import annotations

from .distributions import prob_at_least, prob_over_line, prob_under_line


def anytime_goal_probability(goal_mu: float, alpha: float) -> float:
    return float(prob_at_least(1, goal_mu, alpha))


def anytime_assist_probability(assist_mu: float, alpha: float) -> float:
    return float(prob_at_least(1, assist_mu, alpha))


def point_1plus_probability(point_mu: float, alpha: float) -> float:
    return float(prob_at_least(1, point_mu, alpha))


def point_2plus_probability(point_mu: float, alpha: float) -> float:
    return float(prob_at_least(2, point_mu, alpha))


def goalie_saves_probabilities(save_mu: float, line: float, alpha: float) -> tuple[float, float]:
    over = float(prob_over_line(line, save_mu, alpha))
    return over, float(prob_under_line(line, save_mu, alpha))
