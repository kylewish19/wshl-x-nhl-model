import math
from wshlx_nhl.odds import american_to_decimal, american_to_implied, expected_roi


def test_negative_odds():
    assert math.isclose(american_to_implied(-200), 2/3, rel_tol=1e-9)
    assert math.isclose(american_to_decimal(-200), 1.5, rel_tol=1e-9)


def test_positive_odds():
    assert math.isclose(american_to_implied(150), 0.4, rel_tol=1e-9)
    assert math.isclose(american_to_decimal(150), 2.5, rel_tol=1e-9)


def test_roi():
    assert expected_roi(0.5, 120) > 0
