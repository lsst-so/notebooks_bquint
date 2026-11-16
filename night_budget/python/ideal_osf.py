"""Step 0 - derive the ideal-night open-shutter fraction from an opsim baseline.

``rubin_nights.dayobs_utils.estimated_baseline_visit_range`` hard-codes the v5.1
fit, ``OSF(season) = 0.74 - 0.02 * cos(2 pi (t - 2025-12-21) / 365)`` with an
upper envelope of 0.78.  The baselines in use have moved on (v5.3 changed the
downtime model), so the per-night ideal has to be re-fit from the opsim that is
actually the reference.

For every simulated night this computes

    OSF = sum(visitExposureTime) / night_length(-12 deg)

keeping only "full" simulated nights - nights the downtime model did not touch -
so that simulated downtime cannot drag the clear-night rate down.  It then fits
the same functional form as the v5.1 fit and takes the 90th percentile of the
residuals as the ``n_vis_high`` analogue.

Writes ``data/ideal_osf_<baseline>.csv`` (one row per kept night) and prints the
fitted a, b and envelope next to the v5.1 values.

Run from a set-up kernel shell::

    source /sdf/group/rubin/sw/loadLSST.bash; setup lsst_distrib
    python python/ideal_osf.py --baseline v5.3.7
"""

from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import curve_fit

DATA = Path(__file__).parent.parent / "data"

#: Candidate baseline opsim databases on USDF, newest mtime first.  The v5.4
#: entry is a beta (``b``) written 2026-09-27, i.e. *older* than v5.3.7
#: (2026-10-31), so the default is the newest non-beta run.
BASELINES = {
    "v5.3.7": "/sdf/data/rubin/shared/fbs_sims/sims_featureScheduler_runs5.3/baseline/baseline_v5.3.7_10yrs.db",
    "v5.4.0b": "/sdf/data/rubin/shared/fbs_sims/sims_featureScheduler_runs5.4/baseline/baseline_v5.4.0b_10yrs.db",
    "v5.3.4": "/sdf/data/rubin/shared/fbs_sims/sims_featureScheduler_runs5.3/baseline/baseline_v5.3.4_10yrs.db",
}
DEFAULT_BASELINE = "v5.3.7"

#: The v5.1 fit that ``estimated_baseline_visit_range`` still uses.
V51 = {"a": 0.74, "b": 0.02, "high": 0.78}

#: A gap longer than this (seconds) means the night was not observed end to end,
#: i.e. the downtime model or weather intervened.  Same threshold as the survey
#: gap cut in ``night_budget.py``.
MAX_GAP_S = 600.0

#: Reference epoch of the seasonal modulation, as in the v5.1 fit.
NIGHT_MIN_MJD = 61030.5  # 2025-12-21T12:00:00


def osf_model(mjd: np.ndarray, a: float, b: float) -> np.ndarray:
    """Seasonal open-shutter fraction, the same form as the v5.1 fit."""
    return a - b * np.cos((mjd - NIGHT_MIN_MJD) / 365 * 2 * np.pi)


def load_nights(db_path: str) -> pd.DataFrame:
    """Per-simulated-night open-shutter time, night length and gap statistics."""
    import rubin_nights.dayobs_utils as rn_dayobs

    with sqlite3.connect(f"file:{db_path}?mode=ro", uri=True) as conn:
        obs = pd.read_sql(
            "SELECT observationStartMJD, visitExposureTime, visitTime, night "
            "FROM observations ORDER BY observationStartMJD",
            conn,
        )

    # day_obs from the MJD: the observing night rolls over at local noon, and
    # the simulations are at Cerro Pachon (UTC-4 ... -3), so the MJD integer
    # part already labels the night once the local-noon offset is applied.
    obs["day_obs"] = rn_dayobs.mjd_to_dayobs_array(obs.observationStartMJD.to_numpy())

    # Gap between the end of one visit and the start of the next, within a night.
    obs["obs_end_mjd"] = obs.observationStartMJD + obs.visitTime / 86400.0
    gap = (obs.observationStartMJD - obs.obs_end_mjd.shift(1)) * 86400.0
    gap[obs.day_obs != obs.day_obs.shift(1)] = np.nan  # reset at each night
    obs["gap_s"] = gap

    nights = obs.groupby("day_obs").agg(
        n_visits=("visitExposureTime", "size"),
        exposing_s=("visitExposureTime", "sum"),
        max_gap_s=("gap_s", "max"),
        first_mjd=("observationStartMJD", "min"),
        last_mjd=("obs_end_mjd", "max"),
    )

    # -12 deg night length, the same bracket the real nights use.
    lengths, starts, ends = [], [], []
    for day_obs in nights.index:
        sunset, sunrise = rn_dayobs.day_obs_sunset_sunrise(int(day_obs), sun_alt=-12)
        lengths.append((sunrise - sunset).jd * 86400.0)
        starts.append(sunset.mjd)
        ends.append(sunrise.mjd)
    nights["night_s"] = lengths
    nights["night_start_mjd"] = starts
    nights["night_end_mjd"] = ends

    nights["osf"] = nights.exposing_s / nights.night_s
    # Dead time at the two ends of the night counts as a gap: a night the
    # downtime model truncated looks "gap free" in the visit list otherwise.
    nights["head_s"] = (nights.first_mjd - nights.night_start_mjd) * 86400.0
    nights["tail_s"] = (nights.night_end_mjd - nights.last_mjd) * 86400.0
    nights["max_dead_s"] = nights[["max_gap_s", "head_s", "tail_s"]].max(axis=1)
    return nights.reset_index()


def select_full_nights(nights: pd.DataFrame) -> pd.DataFrame:
    """Nights the simulated downtime model did not touch.

    A night is "full" when it is observed end to end: no dead interval longer
    than ``MAX_GAP_S`` anywhere, including before the first and after the last
    visit.  v5.3's downtime model removes whole and partial nights, and those
    must not lower the clear-night rate we are calling ideal.
    """
    return nights[nights.max_dead_s <= MAX_GAP_S].copy()


def fit(full: pd.DataFrame) -> dict[str, float]:
    """Fit ``a - b cos(season)`` and the ~90th-percentile upper envelope."""
    mjd = full.first_mjd.to_numpy()
    osf = full.osf.to_numpy()
    (a, b), _ = curve_fit(osf_model, mjd, osf, p0=[V51["a"], V51["b"]])
    resid = osf - osf_model(mjd, a, b)
    high = float(a + np.percentile(resid, 90))
    return {"a": float(a), "b": float(b), "high": high, "n_full": len(full)}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--baseline",
        default=DEFAULT_BASELINE,
        choices=sorted(BASELINES),
        help=f"which baseline opsim to fit (default {DEFAULT_BASELINE})",
    )
    parser.add_argument(
        "--all", action="store_true", help="fit every baseline in BASELINES and compare"
    )
    args = parser.parse_args()

    names = sorted(BASELINES) if args.all else [args.baseline]
    results = {}
    for name in names:
        nights = load_nights(BASELINES[name])
        full = select_full_nights(nights)
        res = fit(full)
        results[name] = res

        DATA.mkdir(parents=True, exist_ok=True)
        out = DATA / f"ideal_osf_{name}.csv"
        nights["is_full"] = nights.max_dead_s <= MAX_GAP_S
        nights.to_csv(out, index=False)
        print(f"\n{name}: {len(nights)} simulated nights, {res['n_full']} full -> {out.name}")
        print(f"  OSF(season) = {res['a']:.4f} - {res['b']:.4f} * cos(...)")
        print(f"  upper envelope (90th pct)   = {res['high']:.4f}")
        print(f"  v5.1 fit for comparison     = {V51['a']} - {V51['b']} cos, high {V51['high']}")
        print(f"  mean OSF of full nights     = {full.osf.mean():.4f}")

    if len(results) > 1:
        print("\nsummary")
        print(f"{'baseline':10s} {'a':>8s} {'b':>8s} {'high':>8s} {'n_full':>8s}")
        for name, res in results.items():
            print(
                f"{name:10s} {res['a']:8.4f} {res['b']:8.4f} {res['high']:8.4f} {res['n_full']:8d}"
            )
        print(f"{'v5.1':10s} {V51['a']:8.4f} {V51['b']:8.4f} {V51['high']:8.4f} {'-':>8s}")


if __name__ == "__main__":
    main()
