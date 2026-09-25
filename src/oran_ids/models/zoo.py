"""The baseline ladder.

These architectures are **subjects, not competitors**. None of them is "ours",
and the paper's claim is about what happens to all of them, not about one
beating the others. Two consequences for how this module is written:

* Every model gets the same treatment: the same preprocessing, the same
  class-weighting policy, the same tuning budget. Under-tuning the deep models
  would inflate the headline transfer gap and is the first thing a reviewer
  attacks (plan risk R7).
* The trivial baselines are not decoration. On a corpus that is 94.6% attack, a
  majority-class classifier scores 94.6% accuracy and an F1 of 0.97 by
  construction. Without that number on the page, no other number can be read
  (plan I5, risk R8).

Model seeds perturb only model fitting. Split seeds, which dominate the
variance, live in ``splits/`` (plan A5).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

import numpy as np
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.neural_network import MLPClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.tree import DecisionTreeClassifier
from sklearn.utils.class_weight import compute_sample_weight


@dataclass(frozen=True)
class ModelSpec:
    key: str
    label: str
    level: int          # 1 trivial, 2 conventional, 3 deep, 4 deployment
    build: Callable[[int], Any]
    needs_scaling: bool = False
    notes: str = ""
    tags: tuple[str, ...] = field(default_factory=tuple)


def _lr(seed: int):
    return LogisticRegression(max_iter=2000, class_weight="balanced",
                              random_state=seed)


def _tree(seed: int):
    return DecisionTreeClassifier(max_depth=12, class_weight="balanced",
                                  random_state=seed)


def _rf(seed: int):
    return RandomForestClassifier(n_estimators=200, max_depth=None,
                                  min_samples_leaf=2, class_weight="balanced_subsample",
                                  random_state=seed, n_jobs=-1)


def _xgb(seed: int):
    from xgboost import XGBClassifier
    return XGBClassifier(
        n_estimators=300, max_depth=6, learning_rate=0.1,
        subsample=0.8, colsample_bytree=0.8, tree_method="hist",
        eval_metric="logloss", random_state=seed, n_jobs=-1,
        # scale_pos_weight is set per-fit from the training prior; see fit_model
    )


def _hgb(seed: int):
    return HistGradientBoostingClassifier(
        max_iter=300, learning_rate=0.1, max_depth=6,
        class_weight="balanced", random_state=seed)


def _mlp(seed: int):
    return MLPClassifier(hidden_layer_sizes=(128, 64), max_iter=300,
                         early_stopping=True, n_iter_no_change=10,
                         random_state=seed)


LADDER: tuple[ModelSpec, ...] = (
    ModelSpec("majority", "Majority class", 1,
              lambda s: DummyClassifier(strategy="most_frequent"),
              notes="The floor. On a 94.6%-attack corpus this scores ~0.97 F1 "
                    "by construction. Quote it next to every other F1.",
              tags=("trivial",)),
    ModelSpec("stratified", "Stratified random", 1,
              lambda s: DummyClassifier(strategy="stratified", random_state=s),
              notes="Chance under the training prior.", tags=("trivial",)),
    ModelSpec("logreg", "Logistic regression", 2, _lr, needs_scaling=True,
              notes="Linear reference. Also the deployment candidate: a linear "
                    "model exports to C and runs in microseconds (cf. P04).",
              tags=("conventional", "deployment")),
    ModelSpec("tree", "Decision tree (d=12)", 2, _tree,
              notes="Single tree: shows how much of the task is a few thresholds.",
              tags=("conventional",)),
    ModelSpec("rf", "Random forest", 2, _rf,
              notes="Strong conventional baseline.", tags=("conventional",)),
    ModelSpec("xgboost", "XGBoost", 2, _xgb,
              notes="The architecture the draft claims meets the latency budget.",
              tags=("conventional", "deployment")),
    ModelSpec("hgb", "Hist gradient boosting", 2, _hgb,
              notes="Second boosted implementation; guards against a result that "
                    "is really about one library's defaults.",
              tags=("conventional",)),
    ModelSpec("mlp", "MLP (128, 64)", 3, _mlp, needs_scaling=True,
              notes="Shallow neural reference.", tags=("deep",)),
)

BY_KEY = {m.key: m for m in LADDER}


def build(key: str, seed: int):
    """Instantiate a model, wrapping in a scaler where the family needs one.

    Scaling is fitted inside the pipeline, so it is fitted on training data
    only. That is not a convenience -- fitting any transform on data that
    includes the evaluation set is the A2 leak.
    """
    spec = BY_KEY[key]
    est = spec.build(seed)
    if spec.needs_scaling:
        return Pipeline([("scale", StandardScaler()), ("clf", est)])
    return est


def fit_model(key: str, X, y, seed: int):
    """Fit with the same class-imbalance policy for every family.

    XGBoost has no ``class_weight``, so its equivalent (``scale_pos_weight``) is
    set from the *training* prior here. Leaving it unset would hand every other
    model a balancing advantage and make the comparison unfair in exactly the
    way plan risk R7 describes.

    The MLP has no ``class_weight`` either. Until D-021 it was trained with no
    weighting at all, while the paper stated an identical policy for every
    family. It now receives the same balanced weights as ``class_weight=
    "balanced"`` would give, passed as ``sample_weight`` (scikit-learn >= 1.7).
    """
    model = build(key, seed)
    if key == "xgboost":
        n_pos = float((y == 1).sum())
        n_neg = float((y == 0).sum())
        if n_pos > 0:
            model.set_params(scale_pos_weight=max(n_neg / n_pos, 1e-6))
    if key == "mlp":
        w = compute_sample_weight("balanced", np.asarray(y))
        model.fit(X, y, clf__sample_weight=w)
        return model
    model.fit(X, y)
    return model


def predict_scores(model, X) -> np.ndarray:
    """Probability of the positive class, for threshold sweeps and calibration."""
    if hasattr(model, "predict_proba"):
        p = model.predict_proba(X)
        return p[:, 1] if p.ndim == 2 and p.shape[1] > 1 else p.ravel()
    if hasattr(model, "decision_function"):
        d = model.decision_function(X)
        return 1.0 / (1.0 + np.exp(-d))
    return model.predict(X).astype(float)


__all__ = ["LADDER", "BY_KEY", "ModelSpec", "build", "fit_model", "predict_scores"]
