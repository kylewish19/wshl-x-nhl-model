from __future__ import annotations


def american_to_decimal(odds: float) -> float:
    odds = float(odds)
    if odds == 0:
        raise ValueError("American odds cannot be 0")
    return 1.0 + (odds / 100.0 if odds > 0 else 100.0 / abs(odds))


def american_to_implied(odds: float) -> float:
    odds = float(odds)
    if odds > 0:
        return 100.0 / (odds + 100.0)
    if odds < 0:
        return abs(odds) / (abs(odds) + 100.0)
    raise ValueError("American odds cannot be 0")


def expected_roi(probability: float, american_odds: float) -> float:
    dec = american_to_decimal(american_odds)
    return probability * dec - 1.0


def no_vig_two_way(odds_a: float, odds_b: float) -> tuple[float, float]:
    a = american_to_implied(odds_a)
    b = american_to_implied(odds_b)
    s = a + b
    return a / s, b / s
