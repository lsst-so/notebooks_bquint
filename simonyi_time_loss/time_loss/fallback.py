"""ROSP-24 §C weather fallback: allskycam cloud index and the C1 weather-tower limits.

Used wherever the Observatory Status WEATHER bit is **absent** (before
``DAY_OBS_WEATHER_BIT_START``) or **masked** (FAULT or DOWNTIME active and the bit
not set). Evidence, per ROSP-24 §C (comments of 2026-10-19 and 2026-10-26):

* ``cloud_idx > 0.5`` — Brian Stalder's completeness-weighted allskycam cloud index
  (``/sdf/data/rubin/user/stalder/allsky/cloud/``), resampled to the 1-min grid by
  ``python/pull_allsky_cloud_1min.py``. NaN (no frame within 3 min) = no evidence.
* C1 weather-tower limits on ESS salIndex 301 (1-min means from
  ``python/pull_efd_weather_1min.py``): RH > 80 %, dew-point depression
  ``t_out − dp_out`` < 2.0 °C, wind > 15 m/s (1-min mean) or gust > 18 m/s
  (max of the ~1.3 s samples in the minute). The 20 / 25 m/s limits of Oct 2026
  are outside the range. Precipitation and snow/ice on the dome have no usable
  EFD source (README §3.5: ``rainRate`` is too sparse) and are not evaluated.

A minute is a fallback-weather minute if any of the above holds. Runs are merged
when separated by less than ``MERGE_MIN`` minutes and runs shorter than
``MIN_DURATION_MIN`` are dropped, so that fallback windows have the same time
resolution as the loss windows (``GAP_MIN_MINUTES`` = 10). Sensitivity of this
choice is reported in the README (≈ 1 h pre-bit, ≈ 2.5 h in the masked periods).
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from . import GAP_MIN_MINUTES
from .intervals import clip, empty, normalize

__all__ = [
    "CLOUD_IDX_CLOSE",
    "C1_RH",
    "C1_DEWPOINT_DEPRESSION",
    "C1_WIND_MEAN",
    "C1_WIND_GUST",
    "flag_fallback_minutes",
    "runs_to_windows",
    "fallback_windows_night",
]

CLOUD_IDX_CLOSE = 0.5
C1_RH = 80.0  # %
C1_DEWPOINT_DEPRESSION = 2.0  # °C
C1_WIND_MEAN = 15.0  # m/s
C1_WIND_GUST = 18.0  # m/s
MERGE_MIN = GAP_MIN_MINUTES
MIN_DURATION_MIN = GAP_MIN_MINUTES
MJD_UNIX = 40587.0


def flag_fallback_minutes(
    efd: pd.DataFrame, cloud: pd.DataFrame | None
) -> pd.DataFrame:
    """Per-minute flags for one night. ``efd`` is the 1-min EFD cache (night rows),
    ``cloud`` the 1-min allsky cache (night rows) or None."""
    out = pd.DataFrame(index=efd.index)
    out["c1_rh"] = (efd["rh_out"] > C1_RH).fillna(False) if "rh_out" in efd else False
    if {"t_out", "dp_out"} <= set(efd.columns):
        out["c1_dpd"] = (
            (efd["t_out"] - efd["dp_out"]) < C1_DEWPOINT_DEPRESSION
        ).fillna(False)
    else:
        out["c1_dpd"] = False
    w = (
        (efd["wind"] > C1_WIND_MEAN)
        if "wind" in efd
        else pd.Series(False, index=efd.index)
    )
    g = (
        (efd["gust"] > C1_WIND_GUST)
        if "gust" in efd
        else pd.Series(False, index=efd.index)
    )
    out["c1_wind"] = (w | g).fillna(False)
    out["c1"] = out[["c1_rh", "c1_dpd", "c1_wind"]].any(axis=1)
    if cloud is not None and len(cloud):
        ci = cloud["cloud_idx"].reindex(efd.index)
        out["cloud_idx"] = ci
        out["cloud"] = (ci > CLOUD_IDX_CLOSE).fillna(False)
    else:
        out["cloud_idx"] = np.nan
        out["cloud"] = False
    out["fallback"] = out["cloud"] | out["c1"]
    return out


def runs_to_windows(
    flag: pd.Series,
    merge_min: float = MERGE_MIN,
    min_duration_min: float = MIN_DURATION_MIN,
) -> np.ndarray:
    """Contiguous True runs of a 1-min boolean series → (n, 2) UTC MJD, merged and filtered."""
    f = flag.to_numpy().astype(bool)
    if not f.any():
        return empty()
    t = np.asarray(flag.index.view("int64"), dtype=float) / 86400e9 + MJD_UNIX
    edges = np.flatnonzero(np.diff(np.r_[0, f.astype(int), 0]))
    win = np.array(
        [[t[s], t[e - 1] + 1 / 1440.0] for s, e in zip(edges[::2], edges[1::2])]
    )
    merged = [list(win[0])]
    for a, b in win[1:]:
        if (a - merged[-1][1]) * 1440.0 < merge_min:
            merged[-1][1] = b
        else:
            merged.append([a, b])
    m = np.array(merged)
    return normalize(m[(m[:, 1] - m[:, 0]) * 1440.0 >= min_duration_min - 1e-6])


def fallback_windows_night(
    efd: pd.DataFrame, cloud: pd.DataFrame | None, t0: float, t1: float
) -> dict[str, np.ndarray]:
    """Fallback windows (any, cloud-only, C1-only) for one night, clipped to [t0, t1]."""
    f = flag_fallback_minutes(efd, cloud)
    return {
        "fallback": clip(runs_to_windows(f["fallback"]), t0, t1),
        "cloud": clip(runs_to_windows(f["cloud"]), t0, t1),
        "c1": clip(runs_to_windows(f["c1"]), t0, t1),
        "c1_rh": clip(runs_to_windows(f["c1_rh"]), t0, t1),
        "c1_dpd": clip(runs_to_windows(f["c1_dpd"]), t0, t1),
        "c1_wind": clip(runs_to_windows(f["c1_wind"]), t0, t1),
        "cloud_minutes_missing": int(f["cloud_idx"].isna().sum()),
    }
