"""On-sky coverage per night from ConsDB ``cdb_lsstcam.visit1``.

Definitions (handoff §1b):

* An **on-sky visit** is a ``visit1`` row with ``airmass > 0``. This keeps on-sky
  engineering (``engtest``, alignment, AOS triplets) and drops bias/dark/flat/CBP
  rows, whose airmass is NULL or 0. On-sky engineering is observing, not loss.
* ``on_sky_hours`` for a night is the union of the visit intervals
  ``[obs_start, obs_end]`` after *bridging* every gap shorter than ``gap_min``
  (a gap that short is readout, slew, filter change: normal overhead).
* Gaps longer than ``gap_min`` are **loss intervals**. The two edge gaps (from
  the −18° evening limit to the first visit, and from the last visit to the −18°
  morning limit) are treated the same way. Loss intervals are returned as
  windows so that ``accounting.py`` can subtract the weather windows before
  summing them into ``nonweather_loss_hours``.

Timestamps: ``obs_start_mjd`` / ``obs_end_mjd`` in ConsDB are TAI. They are
converted to UTC here (TAI − 37 s in this epoch) so that everything downstream
is UTC. Nights are bucketed by the integer ``day_obs`` that ConsDB assigns.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from . import DAY_OBS_MAX, DAY_OBS_MIN, GAP_MIN_MINUTES

__all__ = [
    "fetch_visits",
    "merge_intervals",
    "night_coverage",
    "coverage_table",
    "mjd_to_timestamp",
]

TAI_MINUS_UTC_S = 37.0
SEC_PER_DAY = 86400.0
MJD_UNIX_EPOCH = 40587.0  # MJD of 1970-01-01T00:00:00 UTC


def mjd_to_timestamp(mjd: float | None) -> pd.Timestamp:
    """UTC MJD → tz-naive pandas Timestamp (UTC), rounded to the second."""
    if mjd is None or not np.isfinite(mjd):
        return pd.NaT
    return pd.Timestamp((mjd - MJD_UNIX_EPOCH) * SEC_PER_DAY, unit="s").round("s")


ONSKY_IMG_TYPES = ("acq", "science", "cwfs", "focus", "engtest")


def fetch_visits(
    client, day_obs_min: int = DAY_OBS_MIN, day_obs_max: int = DAY_OBS_MAX
) -> pd.DataFrame:
    """All ``visit1`` rows with ``airmass > 0`` in the range, start/end in UTC MJD.

    Columns: ``visit_id, day_obs, obs_start_mjd, obs_end_mjd, exp_time, img_type,
    science_program, band, airmass`` (``*_mjd`` already converted to UTC).
    """
    sql = (
        "SELECT visit_id, day_obs, obs_start_mjd, obs_end_mjd, exp_time, img_type, "
        "science_program, band, airmass "
        f"FROM cdb_lsstcam.visit1 WHERE day_obs BETWEEN {int(day_obs_min)} AND {int(day_obs_max)} "
        "AND airmass > 0 ORDER BY obs_start_mjd"
    )
    v = client.query(sql)
    v["day_obs"] = v["day_obs"].astype(int)
    for c in ("obs_start_mjd", "obs_end_mjd"):
        v[c] = v[c].astype(float) - TAI_MINUS_UTC_S / SEC_PER_DAY
    # A handful of rows have obs_end < obs_start or missing end; fall back to exp_time.
    bad = ~(v["obs_end_mjd"] > v["obs_start_mjd"])
    v.loc[bad, "obs_end_mjd"] = (
        v.loc[bad, "obs_start_mjd"] + v.loc[bad, "exp_time"].fillna(30.0) / SEC_PER_DAY
    )
    return v.reset_index(drop=True)


def merge_intervals(
    starts: np.ndarray, ends: np.ndarray, bridge_days: float
) -> np.ndarray:
    """Union of ``[start, end]`` intervals, joining any two closer than ``bridge_days``.

    Returns an ``(n, 2)`` array sorted by start. Empty input gives shape ``(0, 2)``.
    """
    if len(starts) == 0:
        return np.empty((0, 2))
    order = np.argsort(starts)
    s, e = np.asarray(starts)[order], np.asarray(ends)[order]
    out = [[s[0], e[0]]]
    for a, b in zip(s[1:], e[1:]):
        if a - out[-1][1] <= bridge_days:
            out[-1][1] = max(out[-1][1], b)
        else:
            out.append([a, b])
    return np.array(out)


@dataclass
class NightCoverage:
    day_obs: int
    n_visits: int
    on_sky_hours: float
    first_visit_mjd: float | None
    last_visit_mjd: float | None
    on_sky_windows: np.ndarray  # (n, 2) UTC MJD, clipped to the night
    gap_windows: (
        np.ndarray
    )  # (n, 2) UTC MJD inside the night not covered by visits (> gap_min)


def night_coverage(
    visits: pd.DataFrame,
    night_start_mjd: float,
    night_end_mjd: float,
    gap_min: float = GAP_MIN_MINUTES,
) -> NightCoverage:
    """Coverage of one night by the given visits (already filtered to that day_obs)."""
    bridge = gap_min / 1440.0
    day_obs = int(visits["day_obs"].iloc[0]) if len(visits) else -1
    win = merge_intervals(
        visits["obs_start_mjd"].to_numpy(), visits["obs_end_mjd"].to_numpy(), bridge
    )
    # clip to the night
    if len(win):
        win[:, 0] = np.clip(win[:, 0], night_start_mjd, night_end_mjd)
        win[:, 1] = np.clip(win[:, 1], night_start_mjd, night_end_mjd)
        win = win[win[:, 1] > win[:, 0]]
    # gaps = complement inside the night; a gap shorter than gap_min at the edges is still
    # bridged (treated as overhead), consistent with the interior rule
    gaps = []
    cursor = night_start_mjd
    for a, b in win:
        if a - cursor > bridge:
            gaps.append([cursor, a])
        cursor = max(cursor, b)
    if night_end_mjd - cursor > bridge:
        gaps.append([cursor, night_end_mjd])
    gaps = np.array(gaps) if gaps else np.empty((0, 2))
    on_sky_hours = float((win[:, 1] - win[:, 0]).sum() * 24) if len(win) else 0.0
    return NightCoverage(
        day_obs=day_obs,
        n_visits=int(len(visits)),
        on_sky_hours=on_sky_hours,
        first_visit_mjd=float(visits["obs_start_mjd"].min()) if len(visits) else None,
        last_visit_mjd=float(visits["obs_end_mjd"].max()) if len(visits) else None,
        on_sky_windows=win,
        gap_windows=gaps,
    )


def coverage_table(
    visits: pd.DataFrame,
    limits: pd.DataFrame,
    gap_min: float = GAP_MIN_MINUTES,
    start_col: str = "sunset18_mjd",
    end_col: str = "sunrise18_mjd",
) -> tuple[pd.DataFrame, dict[int, NightCoverage]]:
    """One row per night in ``limits`` (from ``nights.night_limits``).

    Returns the per-night table and the dict of ``NightCoverage`` objects (for
    the window-level arithmetic in ``accounting.py``).
    """
    by_night = {d: g for d, g in visits.groupby("day_obs")}
    rows, cov = [], {}
    for r in limits.itertuples(index=False):
        v = by_night.get(int(r.day_obs), visits.iloc[0:0])
        c = night_coverage(v, getattr(r, start_col), getattr(r, end_col), gap_min)
        c.day_obs = int(r.day_obs)
        cov[c.day_obs] = c
        rows.append(
            {
                "day_obs": c.day_obs,
                "n_visits": c.n_visits,
                "on_sky_hours": round(c.on_sky_hours, 3),
                "n_gaps": int(len(c.gap_windows)),
                "gap_hours": round(
                    float((c.gap_windows[:, 1] - c.gap_windows[:, 0]).sum() * 24), 3
                )
                if len(c.gap_windows)
                else 0.0,
                "first_visit_utc": mjd_to_timestamp(c.first_visit_mjd),
                "last_visit_utc": mjd_to_timestamp(c.last_visit_mjd),
            }
        )
    return pd.DataFrame(rows), cov
