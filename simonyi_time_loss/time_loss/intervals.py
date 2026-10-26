"""Interval-set arithmetic on ``(n, 2)`` arrays of UTC MJD.

All sets are sorted, non-overlapping, half-open ``[start, end)``. Used by the
ROSP-24 ordered classifier (``classify.py``) so that every category is an exact
interval set and the categories partition the night to the second.
"""

from __future__ import annotations

import numpy as np

__all__ = ["empty", "normalize", "union", "intersect", "subtract", "hours", "clip"]


def empty() -> np.ndarray:
    return np.empty((0, 2))


def normalize(w: np.ndarray) -> np.ndarray:
    """Sort and merge touching/overlapping intervals; drop empty ones."""
    w = np.asarray(w, dtype=float).reshape(-1, 2)
    w = w[w[:, 1] > w[:, 0]]
    if len(w) == 0:
        return empty()
    w = w[np.argsort(w[:, 0])]
    out = [list(w[0])]
    for a, b in w[1:]:
        if a <= out[-1][1]:
            out[-1][1] = max(out[-1][1], b)
        else:
            out.append([a, b])
    return np.array(out)


def union(*sets: np.ndarray) -> np.ndarray:
    parts = [np.asarray(s, dtype=float).reshape(-1, 2) for s in sets if len(s)]
    return normalize(np.vstack(parts)) if parts else empty()


def intersect(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    a, b = normalize(a), normalize(b)
    out = []
    i = j = 0
    while i < len(a) and j < len(b):
        lo = max(a[i, 0], b[j, 0])
        hi = min(a[i, 1], b[j, 1])
        if hi > lo:
            out.append([lo, hi])
        if a[i, 1] < b[j, 1]:
            i += 1
        else:
            j += 1
    return np.array(out) if out else empty()


def subtract(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """``a`` minus ``b``."""
    a, b = normalize(a), normalize(b)
    if len(a) == 0 or len(b) == 0:
        return a
    out = []
    for s, e in a:
        cur = s
        for bs, be in b:
            if be <= cur or bs >= e:
                continue
            if bs > cur:
                out.append([cur, bs])
            cur = max(cur, be)
            if cur >= e:
                break
        if cur < e:
            out.append([cur, e])
    return np.array(out) if out else empty()


def clip(w: np.ndarray, t0: float, t1: float) -> np.ndarray:
    return intersect(w, np.array([[t0, t1]]))


def hours(w: np.ndarray) -> float:
    w = np.asarray(w, dtype=float).reshape(-1, 2)
    return float((w[:, 1] - w[:, 0]).sum() * 24.0) if len(w) else 0.0
