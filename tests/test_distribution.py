from wshlx_nhl.distributions import prob_at_least, prob_over_line


def test_probability_monotonic():
    assert prob_at_least(1, 1.0, 0.2) > prob_at_least(2, 1.0, 0.2)


def test_over_line():
    p = prob_over_line(2.5, 3.0, 0.1)
    assert 0 < p < 1
