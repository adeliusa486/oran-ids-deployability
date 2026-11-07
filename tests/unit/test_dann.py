"""The hand-written DANN gradients against finite differences (D-036).

A sign error in a reversed gradient does not raise; it trains a network that
quietly does something else. Every parameter block is checked.
"""
from __future__ import annotations

import numpy as np
import pytest

from oran_ids.models.dann import DANN


def _setup(seed=0):
    rng = np.random.default_rng(seed)
    net = DANN(h1=7, h2=5, hd=4, seed=seed)
    net._init(6, rng)
    Xs = rng.normal(size=(9, 6))
    ys = (rng.random(9) > 0.5).astype(float)
    ws = rng.uniform(0.5, 2.0, size=9)
    Xt = rng.normal(loc=0.7, size=(8, 6))
    return net, Xs, ys, ws, Xt


@pytest.mark.parametrize("lam", [0.0, 0.37, 1.0])
def test_gradients_match_finite_differences(lam):
    net, Xs, ys, ws, Xt = _setup()
    _, _, G = net.loss_and_grads(Xs, ys, ws, Xt, lam)

    def objective(key):
        Ly, Ld, _ = net.loss_and_grads(Xs, ys, ws, Xt, lam)
        if key in ("Wy", "by"):
            return Ly
        if key in ("Wd1", "bd1", "Wd2", "bd2"):
            return Ld
        return Ly - lam * Ld                      # feature extractor: reversed

    eps = 1e-6
    for key, P in net.P.items():
        num = np.zeros_like(P)
        it = np.nditer(P, flags=["multi_index"])
        for _ in it:
            i = it.multi_index
            old = P[i]
            P[i] = old + eps
            up = objective(key)
            P[i] = old - eps
            dn = objective(key)
            P[i] = old
            num[i] = (up - dn) / (2 * eps)
        np.testing.assert_allclose(G[key], num, rtol=1e-4, atol=1e-7,
                                   err_msg=f"gradient mismatch in {key} at lam={lam}")


def test_fit_learns_a_separable_source_task():
    rng = np.random.default_rng(1)
    Xs = rng.normal(size=(2000, 4))
    ys = (Xs[:, 0] + 0.5 * Xs[:, 1] > 0).astype(int)
    Xt = rng.normal(size=(2000, 4)) + np.array([0.3, 0.0, 0.0, 0.0])
    net = DANN(epochs=3, seed=3).fit(Xs, ys, Xt)
    acc = ((net.predict_proba(Xs)[:, 1] >= 0.5) == ys).mean()
    assert acc > 0.9
