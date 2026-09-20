"""Metrics, including the operational ones that accuracy hides.

Two families are kept apart on purpose:

*Detection* metrics (F1, PR-AUC, recall) describe the classifier. *Operational*
metrics (alerts per hour, PPV at a deployment base rate) describe what a SOC
sees. A detector can be excellent on the first and useless on the second, which
is the paper's Criterion 2 and is Axelsson's 2000 result restated for a specific
artefact.

Note on the positive class: this corpus is 94.6% attack, so "accuracy" and even
F1 on the attack class are close to meaningless. ``balanced_accuracy``,
``pr_auc_benign`` and the explicit FPR are the honest summaries, and the
majority-class baseline must be printed beside them.
"""
from __future__ import annotations

import numpy as np
from sklearn.metrics import (
    average_precision_score,
    balanced_accuracy_score,
    brier_score_loss,
    confusion_matrix,
    f1_score,
    matthews_corrcoef,
    precision_score,
    recall_score,
    roc_auc_score,
)


def detection_metrics(y_true: np.ndarray, y_score: np.ndarray,
                      threshold: float = 0.5) -> dict:
    y_pred = (y_score >= threshold).astype(int)
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()
    out = {
        "threshold": float(threshold),
        "tp": int(tp), "fp": int(fp), "tn": int(tn), "fn": int(fn),
        "accuracy": float((tp + tn) / max(tp + tn + fp + fn, 1)),
        "balanced_accuracy": float(balanced_accuracy_score(y_true, y_pred)),
        "precision": float(precision_score(y_true, y_pred, zero_division=0)),
        "recall": float(recall_score(y_true, y_pred, zero_division=0)),
        "f1": float(f1_score(y_true, y_pred, zero_division=0)),
        "f1_macro": float(f1_score(y_true, y_pred, average="macro", zero_division=0)),
        "mcc": float(matthews_corrcoef(y_true, y_pred)) if len(np.unique(y_true)) > 1 else 0.0,
        # FPR is the quantity Criterion 2 multiplies by the benign flow rate.
        "fpr": float(fp / max(fp + tn, 1)),
        "fnr": float(fn / max(fn + tp, 1)),
        "tnr": float(tn / max(fp + tn, 1)),
    }
    if len(np.unique(y_true)) > 1:
        out["roc_auc"] = float(roc_auc_score(y_true, y_score))
        out["pr_auc"] = float(average_precision_score(y_true, y_score))
        # PR-AUC with benign as the positive class. On a corpus this imbalanced
        # it is the more informative of the two and is almost never reported.
        out["pr_auc_benign"] = float(average_precision_score(1 - y_true, 1 - y_score))
        out["brier"] = float(brier_score_loss(y_true, np.clip(y_score, 0, 1)))
    else:
        out.update(roc_auc=float("nan"), pr_auc=float("nan"),
                   pr_auc_benign=float("nan"), brier=float("nan"))
    return out


def operational_metrics(fpr: float, tpr: float, *, pi: float,
                        lambda_b: float) -> dict:
    """Translate a (FPR, TPR) operating point into what an operator experiences.

    ``pi``        assumed attack base rate in deployment (a DECLARED parameter)
    ``lambda_b``  benign flows per hour (a DECLARED parameter)

    Neither is measurable from these corpora, which is precisely why both are
    swept rather than asserted (plan A6). ``alerts_per_100k_benign`` is included
    so the figure ports to a deployment with a different flow rate.
    """
    lam_attack = lambda_b * pi / max(1 - pi, 1e-12)
    tp_h = tpr * lam_attack
    fp_h = fpr * lambda_b
    alerts_h = tp_h + fp_h
    ppv = tp_h / alerts_h if alerts_h > 0 else float("nan")
    fn_h = (1 - tpr) * lam_attack
    tn_h = (1 - fpr) * lambda_b
    npv = tn_h / (tn_h + fn_h) if (tn_h + fn_h) > 0 else float("nan")
    return {
        "pi": float(pi), "lambda_b": float(lambda_b),
        "alerts_per_hour": float(alerts_h),
        "true_alerts_per_hour": float(tp_h),
        "false_alerts_per_hour": float(fp_h),
        "alerts_per_day": float(alerts_h * 24),
        "alerts_per_100k_benign": float(fpr * 1e5 + tpr * 1e5 * pi / max(1 - pi, 1e-12)),
        "ppv": float(ppv),
        "npv": float(npv),
        "fdr": float(1 - ppv) if ppv == ppv else float("nan"),
        "missed_attacks_per_hour": float(fn_h),
    }


def threshold_sweep(y_true: np.ndarray, y_score: np.ndarray,
                    thresholds: np.ndarray) -> list[dict]:
    return [detection_metrics(y_true, y_score, float(t)) for t in thresholds]


def bootstrap_ci(values: np.ndarray, *, n_boot: int = 10_000, alpha: float = 0.05,
                 seed: int = 0) -> tuple[float, float, float]:
    """Percentile bootstrap over split means. Returns (mean, lo, hi).

    Bootstrapping over SPLIT means, not over individual runs, is the point of
    the two-level seed design (plan A5): the dominant uncertainty is which
    groups landed in which fold, not which random state the model used.

    WARNING (D-012): do NOT use this below about n=30. A percentile bootstrap
    resampling a handful of points with replacement can only produce intervals
    spanning the observed values, so it understates uncertainty. At n=5 it
    reported four significant leakage effects that a paired t-test does not
    support. Use a t-interval at small n; this function warns if asked.
    """
    import warnings as _w
    values = np.asarray(values, dtype=float)
    values = values[~np.isnan(values)]
    if len(values) == 0:
        return float("nan"), float("nan"), float("nan")
    if len(values) == 1:
        return float(values[0]), float("nan"), float("nan")
    if len(values) < 30:
        _w.warn(f"bootstrap_ci called with n={len(values)} (<30): percentile "
                f"intervals are anti-conservative at this size. Use a "
                f"t-interval. See D-012.", stacklevel=2)
    rng = np.random.default_rng(seed)
    boots = rng.choice(values, size=(n_boot, len(values)), replace=True).mean(axis=1)
    return (float(values.mean()),
            float(np.percentile(boots, 100 * alpha / 2)),
            float(np.percentile(boots, 100 * (1 - alpha / 2))))


__all__ = ["detection_metrics", "operational_metrics", "threshold_sweep", "bootstrap_ci"]
