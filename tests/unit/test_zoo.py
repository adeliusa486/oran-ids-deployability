"""The model ladder applies one class-imbalance policy to every family (D-021).

The paper states that every architecture receives the same class-imbalance
policy. Until D-021 the MLP was trained with no weighting at all, and nothing
failed. These tests make the policy a checked property rather than a sentence.
"""
from __future__ import annotations

import numpy as np
import pytest
from sklearn.neural_network import MLPClassifier

from oran_ids.models import LADDER, fit_model, predict_scores


def _imbalanced(n=400, prevalence=0.9, seed=0):
    rng = np.random.default_rng(seed)
    y = (rng.random(n) < prevalence).astype(int)
    X = rng.normal(size=(n, 5)) + y[:, None] * 0.8
    return X.astype(np.float32), y


def test_mlp_receives_balanced_sample_weights(monkeypatch):
    X, y = _imbalanced()
    seen = {}
    orig = MLPClassifier.fit

    def spy(self, X_, y_, sample_weight=None):
        seen["w"] = None if sample_weight is None else np.asarray(sample_weight)
        return orig(self, X_, y_, sample_weight=sample_weight)

    monkeypatch.setattr(MLPClassifier, "fit", spy)
    fit_model("mlp", X, y, seed=11)

    w = seen.get("w")
    assert w is not None, "the MLP was fitted without sample weights"
    n, pos = len(y), int(y.sum())
    expected_pos = n / (2 * pos)
    expected_neg = n / (2 * (n - pos))
    assert np.allclose(w[y == 1], expected_pos)
    assert np.allclose(w[y == 0], expected_neg)
    # balanced weights give each class the same total mass
    assert np.isclose(w[y == 1].sum(), w[y == 0].sum())


def test_xgboost_scale_pos_weight_from_training_prior():
    pytest.importorskip("xgboost")
    X, y = _imbalanced()
    m = fit_model("xgboost", X, y, seed=11)
    n_pos, n_neg = int(y.sum()), int((y == 0).sum())
    assert np.isclose(m.get_params()["scale_pos_weight"], n_neg / n_pos)


@pytest.mark.parametrize("key", [m.key for m in LADDER])
def test_every_family_fits_and_scores_in_unit_interval(key):
    X, y = _imbalanced()
    m = fit_model(key, X, y, seed=11)
    s = predict_scores(m, X)
    assert s.shape == (len(y),)
    assert np.all((s >= 0) & (s <= 1))
