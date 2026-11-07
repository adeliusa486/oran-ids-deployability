"""Domain-adversarial neural network (DANN), in NumPy (revision 1, R1.12/R2.6).

Ganin et al., "Domain-adversarial training of neural networks", JMLR 17(59),
2016. A feature extractor G_f is trained so that a label predictor G_y can
classify labelled source flows while a domain classifier G_d cannot tell source
features from (unlabelled) target features. The gradient of the domain loss is
reversed, with coefficient lambda, on its way into G_f.

Written in NumPy because the CPU PyTorch environment of EXP-050 no longer loads
on this host (DLL initialisation failure). The network is small enough that
hand-written backpropagation is short and checkable; ``tests/unit/test_dann.py``
compares every gradient with finite differences.

Architecture and schedule are fixed before any result (D-036):
  G_f: d -> 64 -> 32 (ReLU)   G_y: 32 -> 1 (sigmoid)   G_d: 32 -> 32 -> 1
  Adam (lr 1e-3), 256 source + 256 target rows per step, 5 passes over the
  source training set, lambda_p = 2 / (1 + exp(-10 p)) - 1 (Ganin et al.),
  class-balanced weights on the label loss, inputs standardised with source
  training statistics. No early stopping: there are no target labels to stop on.
"""
from __future__ import annotations

import numpy as np


def _relu(x):
    return np.maximum(x, 0.0)


def _sigmoid(x):
    return 0.5 * (1.0 + np.tanh(0.5 * x))


def _bce_grad(logit, y, w):
    """d/dlogit of the weighted mean binary cross-entropy."""
    return w * (_sigmoid(logit) - y) / w.sum()


def _bce(logit, y, w):
    p = np.clip(_sigmoid(logit), 1e-12, 1 - 1e-12)
    return float(-(w * (y * np.log(p) + (1 - y) * np.log(1 - p))).sum() / w.sum())


class DANN:
    def __init__(self, h1: int = 64, h2: int = 32, hd: int = 32, lr: float = 1e-3,
                 batch: int = 256, epochs: int = 5, gamma: float = 10.0,
                 lambda_max: float = 1.0, seed: int = 0):
        self.h1, self.h2, self.hd = h1, h2, hd
        self.lr, self.batch, self.epochs = lr, batch, epochs
        self.gamma, self.lambda_max, self.seed = gamma, lambda_max, seed

    # ---------------------------------------------------------------- params
    def _init(self, d: int, rng):
        def he(n_in, n_out):
            return rng.normal(0.0, np.sqrt(2.0 / n_in), size=(n_in, n_out))
        self.P = {
            "W1": he(d, self.h1), "b1": np.zeros(self.h1),
            "W2": he(self.h1, self.h2), "b2": np.zeros(self.h2),
            "Wy": he(self.h2, 1) * 0.5, "by": np.zeros(1),
            "Wd1": he(self.h2, self.hd), "bd1": np.zeros(self.hd),
            "Wd2": he(self.hd, 1) * 0.5, "bd2": np.zeros(1),
        }
        self.m = {k: np.zeros_like(v) for k, v in self.P.items()}
        self.v = {k: np.zeros_like(v) for k, v in self.P.items()}
        self.t = 0

    # --------------------------------------------------------------- forward
    def _features(self, X):
        P = self.P
        a1 = X @ P["W1"] + P["b1"]
        h1 = _relu(a1)
        a2 = h1 @ P["W2"] + P["b2"]
        f = _relu(a2)
        return a1, h1, a2, f

    def _domain(self, f):
        P = self.P
        ad = f @ P["Wd1"] + P["bd1"]
        hd = _relu(ad)
        return ad, hd, (hd @ P["Wd2"] + P["bd2"]).ravel()

    def loss_and_grads(self, Xs, ys, ws, Xt, lam):
        """Label loss on source, domain loss on both, and reversed gradients.

        Returns (label_loss, domain_loss, grads). For G_f the gradient is
        dL_y/dθ_f - lam * dL_d/dθ_f; G_d descends L_d; G_y descends L_y.
        """
        P = self.P
        X = np.vstack([Xs, Xt])
        ns = len(Xs)
        a1, h1, a2, f = self._features(X)
        # label head on the source rows only
        ly = (f[:ns] @ P["Wy"] + P["by"]).ravel()
        Ly = _bce(ly, ys, ws)
        gly = _bce_grad(ly, ys, ws)                       # (ns,)
        # domain head on all rows: source 0, target 1, equal weight
        d = np.r_[np.zeros(ns), np.ones(len(Xt))]
        wd = np.ones(len(X))
        ad, hd, ld = self._domain(f)
        Ld = _bce(ld, d, wd)
        gld = _bce_grad(ld, d, wd)                        # (n,)

        G = {}
        G["Wy"] = f[:ns].T @ gly[:, None]
        G["by"] = np.array([gly.sum()])
        G["Wd2"] = hd.T @ gld[:, None]
        G["bd2"] = np.array([gld.sum()])
        ghd = gld[:, None] @ P["Wd2"].T * (ad > 0)
        G["Wd1"] = f.T @ ghd
        G["bd1"] = ghd.sum(0)
        # into the features: label part (source rows) minus lam * domain part
        gf = -lam * (ghd @ P["Wd1"].T)
        gf[:ns] += gly[:, None] @ P["Wy"].T
        ga2 = gf * (a2 > 0)
        G["W2"] = h1.T @ ga2
        G["b2"] = ga2.sum(0)
        ga1 = ga2 @ P["W2"].T * (a1 > 0)
        G["W1"] = X.T @ ga1
        G["b1"] = ga1.sum(0)
        return Ly, Ld, G

    def _adam(self, G, b1=0.9, b2=0.999, eps=1e-8):
        self.t += 1
        for k, g in G.items():
            self.m[k] = b1 * self.m[k] + (1 - b1) * g
            self.v[k] = b2 * self.v[k] + (1 - b2) * g * g
            mh = self.m[k] / (1 - b1 ** self.t)
            vh = self.v[k] / (1 - b2 ** self.t)
            self.P[k] -= self.lr * mh / (np.sqrt(vh) + eps)

    # ------------------------------------------------------------------- api
    def fit(self, Xs, ys, Xt):
        rng = np.random.default_rng(self.seed)
        Xs = np.asarray(Xs, np.float64)
        Xt = np.asarray(Xt, np.float64)
        ys = np.asarray(ys, np.float64)
        self.mu = Xs.mean(0)
        self.sd = Xs.std(0) + 1e-9
        Zs = (Xs - self.mu) / self.sd
        Zt = (Xt - self.mu) / self.sd
        self._init(Zs.shape[1], rng)
        # class-balanced weights, as for every other model (n / (2 n_c))
        n1 = max(ys.sum(), 1.0)
        n0 = max(len(ys) - ys.sum(), 1.0)
        wcls = np.where(ys == 1, len(ys) / (2 * n1), len(ys) / (2 * n0))
        steps_per_epoch = int(np.ceil(len(Zs) / self.batch))
        total = steps_per_epoch * self.epochs
        self.history = []
        step = 0
        for ep in range(self.epochs):
            order = rng.permutation(len(Zs))
            for i in range(steps_per_epoch):
                idx = order[i * self.batch:(i + 1) * self.batch]
                jdx = rng.integers(0, len(Zt), size=len(idx))
                p = step / max(total - 1, 1)
                lam = self.lambda_max * (2.0 / (1.0 + np.exp(-self.gamma * p)) - 1.0)
                Ly, Ld, G = self.loss_and_grads(Zs[idx], ys[idx], wcls[idx], Zt[jdx], lam)
                self._adam(G)
                step += 1
            self.history.append(dict(epoch=ep, label_loss=Ly, domain_loss=Ld, lam=lam))
        return self

    def predict_proba(self, X):
        Z = (np.asarray(X, np.float64) - self.mu) / self.sd
        out = []
        for i in range(0, len(Z), 200_000):        # bounded memory on 1.6M rows
            _, _, _, f = self._features(Z[i:i + 200_000])
            out.append(_sigmoid((f @ self.P["Wy"] + self.P["by"]).ravel()))
        p = np.concatenate(out) if out else np.zeros(0)
        return np.c_[1 - p, p]


__all__ = ["DANN"]
