"""Split protocols, including the ones we expect to fail.

Four protocols are implemented rather than one, because the *difference* between
them is itself a result. A random split over flow records is the protocol most
NIDS papers use; a group-disjoint split is the protocol that reflects deployment.
Reporting both quantifies how much of a published accuracy figure is an artefact
of the split, which is the Phase 2 leakage audit.

EXP-001 established what the grouping key can be:
  network layer  ``src_ip``   318 groups, largest 33.8%
  radio layer    ``session``  30 recovered runs, 100% label-pure

Device-disjoint splitting, which the manuscript currently claims, is **not**
supportable: ``ue_id`` has 9 values and one holds 60.8% of records (B-010).
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class Split:
    name: str
    train_idx: np.ndarray
    test_idx: np.ndarray
    seed: int
    fold: int
    n_train_groups: int
    n_test_groups: int
    train_prevalence: float
    test_prevalence: float

    def check_disjoint(self, groups: np.ndarray) -> None:
        """A group-disjoint split that is not disjoint is silent leakage."""
        overlap = set(groups[self.train_idx]) & set(groups[self.test_idx])
        if overlap:
            raise LeakageError(
                f"{self.name} seed={self.seed} fold={self.fold}: "
                f"{len(overlap)} group(s) appear in BOTH train and test, "
                f"e.g. {sorted(overlap)[:5]}"
            )


class LeakageError(AssertionError):
    """Raised when a split that claims to be disjoint is not."""


def random_split(y: np.ndarray, groups: np.ndarray, *, seed: int,
                 n_folds: int = 5, test_frac: float = 0.2) -> list[Split]:
    """Ignore groups entirely. The protocol most NIDS papers use.

    Kept so the leakage audit has something to measure against. It is NEVER the
    primary protocol, and any number produced under it is labelled as the
    optimistic bound, not as a result.
    """
    rng = np.random.default_rng(seed)
    n = len(y)
    out = []
    for fold in range(n_folds):
        perm = rng.permutation(n)
        cut = int(n * (1 - test_frac))
        tr, te = np.sort(perm[:cut]), np.sort(perm[cut:])
        out.append(Split("random", tr, te, seed, fold,
                         len(np.unique(groups[tr])), len(np.unique(groups[te])),
                         float(y[tr].mean()), float(y[te].mean())))
    return out


def group_disjoint_split(y: np.ndarray, groups: np.ndarray, *, seed: int,
                         n_folds: int = 5, test_frac: float = 0.2,
                         min_test_groups: int = 2,
                         balance_prevalence: bool = True) -> list[Split]:
    """Whole groups go to exactly one side. The primary protocol.

    Groups are assigned greedily to the test side in a shuffled order until the
    target size is reached. With ``balance_prevalence`` the greedy pass prefers
    the group that moves test-set attack prevalence closest to the overall
    prevalence, which stops one huge group from producing a test fold that is
    100% attack -- a degenerate fold makes F1 meaningless rather than merely
    noisy.
    """
    rng = np.random.default_rng(seed)
    uniq = np.unique(groups)
    if len(uniq) < min_test_groups + 1:
        raise ValueError(
            f"only {len(uniq)} group(s); cannot build a group-disjoint split "
            f"with at least {min_test_groups} test groups. This is the "
            f"condition that rules out device-disjoint splitting on D_A (B-010)."
        )
    idx_of = {g: np.flatnonzero(groups == g) for g in uniq}
    overall = float(y.mean())
    target = int(len(y) * test_frac)

    out = []
    for fold in range(n_folds):
        order = rng.permutation(uniq)
        test_groups: list = []
        n_test = 0
        for g in order:
            if n_test >= target and len(test_groups) >= min_test_groups:
                break
            if not balance_prevalence:
                test_groups.append(g)
                n_test += len(idx_of[g])
                continue
            # pick, among the next few candidates, the one that keeps the test
            # fold's prevalence nearest the overall prevalence
            remaining = [x for x in order if x not in test_groups][:8]
            best, best_err = None, None
            cur = np.concatenate([idx_of[t] for t in test_groups]) if test_groups \
                else np.array([], dtype=int)
            for cand in remaining:
                trial = np.concatenate([cur, idx_of[cand]])
                err = abs(float(y[trial].mean()) - overall)
                if best_err is None or err < best_err:
                    best, best_err = cand, err
            if best is None:
                break
            test_groups.append(best)
            n_test += len(idx_of[best])

        te = np.sort(np.concatenate([idx_of[g] for g in test_groups]))
        mask = np.ones(len(y), dtype=bool)
        mask[te] = False
        tr = np.flatnonzero(mask)
        if len(tr) == 0 or len(te) == 0:
            raise ValueError(f"degenerate fold {fold} at seed {seed}")
        s = Split("group_disjoint", tr, te, seed, fold,
                  len(np.unique(groups[tr])), len(np.unique(groups[te])),
                  float(y[tr].mean()), float(y[te].mean()))
        s.check_disjoint(groups)
        out.append(s)
    return out


def stratified_group_split(y: np.ndarray, groups: np.ndarray, category: np.ndarray,
                           *, seed: int, n_folds: int = 5,
                           test_frac: float = 0.2) -> list[Split]:
    """Group-disjoint, but every attack category must appear on both sides.

    Without this, a fold can omit a whole attack family from training, and the
    resulting recall collapse is a property of the split rather than of the
    model. Prior work on this corpus (Fard et al.) stratifies runs by attack
    family for the same reason.
    """
    rng = np.random.default_rng(seed)
    uniq = np.unique(groups)
    # dominant category per group -- groups here are label-pure or near it
    gcat = {}
    for g in uniq:
        m = groups == g
        vals, counts = np.unique(category[m], return_counts=True)
        gcat[g] = vals[np.argmax(counts)]

    out = []
    for fold in range(n_folds):
        test_groups = []
        for cat in np.unique(list(gcat.values())):
            members = np.array([g for g in uniq if gcat[g] == cat])
            rng.shuffle(members)
            k = max(1, int(round(len(members) * test_frac)))
            if len(members) <= 1:
                continue  # a single-group category must stay in train
            test_groups.extend(members[:min(k, len(members) - 1)])
        if not test_groups:
            raise ValueError("no category had enough groups to stratify")
        te = np.sort(np.concatenate([np.flatnonzero(groups == g) for g in test_groups]))
        mask = np.ones(len(y), dtype=bool)
        mask[te] = False
        tr = np.flatnonzero(mask)
        s = Split("stratified_group", tr, te, seed, fold,
                  len(np.unique(groups[tr])), len(np.unique(groups[te])),
                  float(y[tr].mean()), float(y[te].mean()))
        s.check_disjoint(groups)
        out.append(s)
    return out


SPLIT_PROTOCOLS = {
    "random": random_split,
    "group_disjoint": group_disjoint_split,
}

__all__ = ["Split", "LeakageError", "random_split", "group_disjoint_split",
           "stratified_group_split", "SPLIT_PROTOCOLS"]
