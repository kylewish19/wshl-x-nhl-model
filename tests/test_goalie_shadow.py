import numpy as np
import pandas as pd

from wshlx_nhl.goalie_shadow import GoalieTwoStageShadowBundle, GoalieSimulationShadowBundle


class DummyWorkload:
    alpha = 0.0

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


def test_v03_simulation_is_deterministic_and_structured():
    bundle = GoalieSimulationShadowBundle(
        workload_model=DummyWorkload(),
        save_rate_model=DummySaveRate(),
        beta_concentration=100.0,
        validation_metrics={},
        n_sims=20000,
        random_state=42,
    )
    X = pd.DataFrame({"dummy": [1, 2]})
    lines = np.array([24.5, 29.5])

    over1, under1, push1 = bundle.simulate_probabilities(X, lines)
    over2, under2, push2 = bundle.simulate_probabilities(X, lines)

    assert np.allclose(over1, over2)
    assert np.allclose(under1, under2)
    assert np.allclose(push1, 0.0)
    assert np.allclose(over1 + under1, 1.0)
    assert over1[0] > 0.5
    assert over1[1] < 0.5
