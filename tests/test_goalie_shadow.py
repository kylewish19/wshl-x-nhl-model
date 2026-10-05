import numpy as np
import pandas as pd

from wshlx_nhl.goalie_shadow import GoalieTwoStageShadowBundle


class DummyWorkload:
    def predict_mu(self, X):
        return np.full(len(X), 30.0)


class DummySaveRate:
    def predict_save_pct(self, X):
        return np.full(len(X), 0.90)


def test_two_stage_expected_saves_and_probability():
    bundle = GoalieTwoStageShadowBundle(
        workload_model=DummyWorkload(),
        save_rate_model=DummySaveRate(),
        alpha=0.15,
        validation_metrics={},
    )
    X = pd.DataFrame({"dummy": [1, 2]})
    shots, save_pct, saves = bundle.predict_components(X)

    assert np.allclose(shots, 30.0)
    assert np.allclose(save_pct, 0.90)
    assert np.allclose(saves, 27.0)

    over = bundle.prob_over(X, 24.5)
    under = bundle.prob_under(X, 24.5)
    assert np.all((over > 0) & (over < 1))
    assert np.allclose(over + under, 1.0)
