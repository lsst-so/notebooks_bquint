"""Step 1 - per-night budget: where the -12 deg night went, visit by visit.

This combines two pieces that already exist and re-derives neither:

* **the per-visit gap split** from Lynne Jones' ``sp_notebooks/efficiency.ipynb``.
  ``rubin_nights.rubin_scheduler_addons.add_model_slew_times`` models, for every
  visit, the slew that *should* have preceded it - once with the TMA limits the
  EFD says were applied that night (``slew_model``) and once with the FBS
  kinematic model at 40 % TMA that the simulations assume (``slew_model_ideal``).
  The gap before a visit then splits into an expected part and an excess part.
* **the ROSP-24 block hours** from ``simonyi_time_loss`` (weather / focus +
  alignment / engineering / fault + idle / planned maintenance).  Those are read
  from a copy of that investigation's per-night CSV in ``data/`` - no
  cross-folder import, so this folder stays extractable.

The Science block is split four ways, using survey visits only:

===================== ======================================================
``exposing_h``        sum of ``exp_time``: shutter actually open
``in_visit_h``        sum of (obs_end - obs_start - exp_time): readout etc.
``gap_expected_h``    sum of min(``slew_model_ideal``, gap): the slew the sims assume
``gap_excess_h``      sum of (gap - expected) over survey gaps <= 10 min
===================== ======================================================

``gap_expected_current_h`` repeats the expected part with ``slew_model`` (today's
TMA limits), so the README can separate "the TMA is slower than the sims assume"
from "everything else".

Run from a set-up kernel shell::

    source /sdf/group/rubin/sw/loadLSST.bash; setup lsst_distrib
    python python/night_budget.py --day-obs 20260706
    python python/night_budget.py --day-obs-min 20260629 --day-obs-max 20261101
    python python/night_budget.py --select            # print the night selector
"""

from __future__ import annotations

import argparse
import logging
import os
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).parent
DATA = HERE.parent / "data"

log = logging.getLogger("night_budget")

# --------------------------------------------------------------------------- #
# Environment: the stack needs these before rubin_nights is imported          #
# --------------------------------------------------------------------------- #
_TOKEN_FILE = Path.home() / ".token_file"
if "ACCESS_TOKEN_FILE" not in os.environ and _TOKEN_FILE.exists():
    os.environ["ACCESS_TOKEN_FILE"] = str(_TOKEN_FILE)
os.environ.setdefault("PGPASSFILE", str(Path.home() / ".lsst" / "postgres-credentials.txt"))
os.environ.setdefault("RUBIN_SIM_DATA_DIR", "/sdf/data/rubin/shared/rubin_sim_data")

SEC_PER_DAY = 86400.0
#: ConsDB ``obs_*_mjd`` are TAI; everything downstream here is UTC.
TAI_MINUS_UTC_S = 37.0

#: Survey programs, ``rubin_nights.reference_values.SCIENCE_PROGRAMS`` (0.18.2).
SURVEY_PROGRAMS = (
    "BLOCK-365",
    "BLOCK-407",
    "BLOCK-408",
    "BLOCK-416",
    "BLOCK-417",
    "BLOCK-419",
    "BLOCK-421",
)
#: On-sky image types, as in ``simonyi_time_loss.time_loss.visits``.
ONSKY_IMG_TYPES = ("acq", "science", "cwfs", "focus", "engtest")

#: A gap longer than this is not a survey gap - it is a fault, weather or a
#: transition, and ROSP-24 accounts for it as a block.  Equals
#: ``rubin_nights.rubin_scheduler_addons.SKIPTIME`` (600 s).
MAX_GAP_S = 600.0

#: Lynne's settings in ``efficiency.ipynb``, so the split matches hers.
WAIT_BEFORE_SLEW_S = 1.6
MODEL_SETTLE_S = 1.5
DOME_CRAWL = True
SLEW_WHILE_CHANGING_FILTER = False

#: OSS-REQ-0289: inter-visit interval, shutter closed to next shutter open.
REQ_GAP_MEDIAN_S = 5.0
REQ_GAP_MEAN_S = 10.0

#: Ideal-night open-shutter fraction. ``ideal_osf.py`` fits these per baseline;
#: v5.1 is what ``rubin_nights.estimated_baseline_visit_range`` still uses.
IDEAL_OSF_FITS = {
    "v5.1": {"a": 0.74, "b": 0.02, "high": 0.78},
    "v5.3.4": {"a": 0.7305, "b": 0.0138, "high": 0.7549},
    "v5.3.7": {"a": 0.7261, "b": 0.0169, "high": 0.7518},
    "v5.4.0b": {"a": 0.7315, "b": 0.0190, "high": 0.7534},
}
DEFAULT_BASELINE = "v5.3.7"
NIGHT_MIN_MJD = 61030.5  # 2025-12-21T12:00:00, the modulation epoch
VISIT_S = 30.0  # we observe 1 x 30 s (OSS-REQ-0288 designs for 2 x 15 s)

#: ROSP-24 per-night hours, copied from ``simonyi_time_loss/data/processed``.
ROSP24_CSV = DATA / "rosp24_per_night.csv"

VISIT_COLUMNS = (
    "visit_id, day_obs, seq_num, obs_start_mjd, obs_end_mjd, exp_time, img_type, "
    "science_program, observation_reason, band, s_ra, s_dec, sky_rotation, airmass"
)


# --------------------------------------------------------------------------- #
# Access                                                                      #
# --------------------------------------------------------------------------- #
def _endpoints() -> dict:
    from rubin_nights import connections

    logging.disable(logging.ERROR)  # noisy 401s when a service is unreachable
    try:
        return connections.get_clients()
    finally:
        logging.disable(logging.NOTSET)


def get_consdb_client():
    """ConsDB client: the RSP token route if it works, else the USDF replica."""
    from rubin_nights.consdb_query import ConsDbSql

    try:
        client = _endpoints()["consdb"]
        if len(client.query("SELECT 1 AS one")) == 1:
            log.info("ConsDB via RSP token")
            return client
    except Exception as err:  # noqa: BLE001
        log.info("ConsDB token route failed (%s); using Postgres", type(err).__name__)
    log.info("ConsDB via Postgres replica")
    return ConsDbSql(site="usdf")


def get_efd_client():
    """Synchronous EFD client (``usdf_efd``), for the applied TMA limits."""
    return _endpoints()["efd"]


# --------------------------------------------------------------------------- #
# Visits                                                                      #
# --------------------------------------------------------------------------- #
def fetch_visits(client, day_obs_min: int, day_obs_max: int) -> pd.DataFrame:
    """On-sky ``visit1`` rows for the range, with the slew-model columns.

    ``obs_start_mjd`` / ``obs_end_mjd`` come back as UTC.  Note the model slew
    needs *all* on-sky visits, not only survey ones: the telescope's position at
    the start of a survey visit depends on wherever the previous visit pointed.
    """
    types = ", ".join(f"'{t}'" for t in ONSKY_IMG_TYPES)
    sql = (
        f"SELECT {VISIT_COLUMNS} FROM cdb_lsstcam.visit1 "
        f"WHERE day_obs BETWEEN {int(day_obs_min)} AND {int(day_obs_max)} "
        f"AND airmass > 0 AND img_type IN ({types}) ORDER BY obs_start_mjd"
    )
    v = client.query(sql)
    if len(v) == 0:
        return v
    v["day_obs"] = v["day_obs"].astype(int)
    v["seq_num"] = v["seq_num"].astype(int)
    for col in ("obs_start_mjd", "obs_end_mjd", "exp_time", "s_ra", "s_dec", "sky_rotation"):
        v[col] = v[col].astype(float)
    # ConsDB stores TAI; convert both ends to UTC before any arithmetic.
    for col in ("obs_start_mjd", "obs_end_mjd"):
        v[col] = v[col] - TAI_MINUS_UTC_S / SEC_PER_DAY
    # A few rows have a missing or inverted end time; fall back to exp_time.
    bad = ~(v.obs_end_mjd > v.obs_start_mjd)
    v.loc[bad, "obs_end_mjd"] = (
        v.loc[bad, "obs_start_mjd"] + v.loc[bad, "exp_time"].fillna(VISIT_S) / SEC_PER_DAY
    )
    return v.sort_values("obs_start_mjd").reset_index(drop=True)


def add_gaps(visits: pd.DataFrame) -> pd.DataFrame:
    """Add ``visit_gap`` (s) and the survey-gap mask, resetting at each night.

    ``is_survey_gap`` marks the gaps that belong to the Science block: the gap
    before a survey visit, when the previous visit was also a survey visit on
    the same night, and no longer than ``MAX_GAP_S``.  The first gap of the
    night, and the first gap after a non-survey visit, are *not* survey gaps -
    they are a transition, and ROSP-24 accounts for them elsewhere.  (Lynne
    nulls the same gaps via ``skipped_visits``.)
    """
    v = visits.sort_values(["day_obs", "obs_start_mjd"]).reset_index(drop=True)
    v["is_survey"] = v.science_program.isin(SURVEY_PROGRAMS)
    v["prev_obs_end_mjd"] = v.obs_end_mjd.shift(1)
    v["visit_gap"] = (v.obs_start_mjd - v.prev_obs_end_mjd) * SEC_PER_DAY

    same_night = v.day_obs == v.day_obs.shift(1)
    v.loc[~same_night, ["visit_gap", "prev_obs_end_mjd"]] = np.nan
    v["is_survey_gap"] = (
        v.is_survey
        & v.is_survey.shift(1, fill_value=False).astype(bool)
        & same_night
        & v.visit_gap.notna()
        & (v.visit_gap <= MAX_GAP_S)
        & (v.visit_gap > 0)
    )
    # add_model_slew_times needs prev_obs_end_mjd for every visit; where the
    # night resets it uses obs_start_mjd via the SKIPTIME branch, so fill with
    # the visit's own start to make that branch fire.
    v["prev_obs_end_mjd"] = v.prev_obs_end_mjd.fillna(v.obs_start_mjd - 1.0)
    return v


def add_slew_models(visits: pd.DataFrame, efd_client) -> pd.DataFrame:
    """Add ``slew_model`` and ``slew_model_ideal`` (s) for every visit.

    Wraps ``rubin_nights.rubin_scheduler_addons.add_model_slew_times``, which
    walks the night in ``seq_num`` order through a kinematic model parked at the
    start of each night.  ``wait_before_slew`` is not part of that model, so it
    is added here, as in ``efficiency.ipynb``.
    """
    from rubin_nights.rubin_scheduler_addons import add_model_slew_times

    v = visits.set_index("visit_id", drop=False)
    v, _ = add_model_slew_times(
        v,
        efd_client,
        model_settle=MODEL_SETTLE_S,
        dome_crawl=DOME_CRAWL,
        slew_while_changing_filter=SLEW_WHILE_CHANGING_FILTER,
    )
    for col in ("slew_model", "slew_model_ideal"):
        v[col] = v[col].astype(float) + WAIT_BEFORE_SLEW_S
    return v.reset_index(drop=True)


# --------------------------------------------------------------------------- #
# Ideal night                                                                 #
# --------------------------------------------------------------------------- #
def ideal_night(day_obs: int, baseline: str = DEFAULT_BASELINE) -> dict[str, float]:
    """Night length, ideal open-shutter fraction and expected visit counts.

    Same construction as ``rubin_nights.dayobs_utils.estimated_baseline_visit_range``,
    but with the OSF fit of ``baseline`` rather than the hard-coded v5.1 one.
    """
    import rubin_nights.dayobs_utils as rn_dayobs

    fit = IDEAL_OSF_FITS[baseline]
    sunset, sunrise = rn_dayobs.day_obs_sunset_sunrise(int(day_obs), sun_alt=-12)
    night_s = (sunrise - sunset).jd * SEC_PER_DAY
    osf = fit["a"] - fit["b"] * np.cos((sunset.mjd - NIGHT_MIN_MJD) / 365 * 2 * np.pi)
    return {
        "night_h": night_s / 3600.0,
        "night_start_mjd": sunset.mjd,
        "night_end_mjd": sunrise.mjd,
        "ideal_osf": float(osf),
        "ideal_osf_high": float(fit["high"]),
        "n_vis_ave": int(np.floor(osf * night_s / VISIT_S)),
        "n_vis_high": int(np.floor(fit["high"] * night_s / VISIT_S)),
    }


def load_rosp24(path: Path = ROSP24_CSV) -> pd.DataFrame | None:
    """ROSP-24 per-night block hours, from the copied ``simonyi_time_loss`` CSV."""
    if not path.exists():
        log.warning("no ROSP-24 CSV at %s; block hours will be NaN", path)
        return None
    r = pd.read_csv(path)
    r["day_obs"] = r.day_obs.astype(int)
    return r.set_index("day_obs")


# --------------------------------------------------------------------------- #
# The budget                                                                  #
# --------------------------------------------------------------------------- #
def night_budget(
    day_obs: int,
    visits: pd.DataFrame,
    rosp24: pd.DataFrame | None = None,
    baseline: str = DEFAULT_BASELINE,
) -> dict:
    """One night's budget: the Science split, the ROSP-24 blocks and the ratio.

    ``visits`` must already carry the gap and slew-model columns (``add_gaps``
    then ``add_slew_models``) and may span more nights than this one.
    """
    v = visits[visits.day_obs == int(day_obs)]
    survey = v[v.is_survey]
    row: dict = {"day_obs": int(day_obs), "baseline": baseline}
    row.update(ideal_night(day_obs, baseline))

    # --- Science, split four ways (survey visits only) --------------------- #
    row["exposing_h"] = survey.exp_time.sum() / 3600.0
    in_visit_s = (
        (survey.obs_end_mjd - survey.obs_start_mjd) * SEC_PER_DAY - survey.exp_time
    ).clip(lower=0)
    row["in_visit_h"] = in_visit_s.sum() / 3600.0

    gaps = v[v.is_survey_gap]
    for col, out in (("slew_model_ideal", "gap_expected_h"), ("slew_model", "gap_expected_current_h")):
        expected_s = np.minimum(gaps[col].fillna(0.0), gaps.visit_gap)
        row[out] = expected_s.sum() / 3600.0
    expected_ideal_s = np.minimum(gaps.slew_model_ideal.fillna(0.0), gaps.visit_gap)
    row["gap_excess_h"] = (gaps.visit_gap - expected_ideal_s).sum() / 3600.0
    row["gap_total_h"] = gaps.visit_gap.sum() / 3600.0

    # --- Counts, ratio and the gap requirement ---------------------------- #
    row["n_survey"] = int(len(survey))
    row["n_onsky"] = int(len(v))
    row["ratio"] = row["n_survey"] / row["n_vis_ave"] if row["n_vis_ave"] else np.nan
    v51 = ideal_night(day_obs, "v5.1")
    row["ratio_v51"] = row["n_survey"] / v51["n_vis_ave"] if v51["n_vis_ave"] else np.nan
    row["n_survey_gaps"] = int(len(gaps))
    row["gap_median_s"] = float(gaps.visit_gap.median()) if len(gaps) else np.nan
    row["gap_mean_s"] = float(gaps.visit_gap.mean()) if len(gaps) else np.nan
    row["n_gaps_over_2x_model"] = int((gaps.visit_gap > 2 * gaps.slew_model_ideal).sum())
    row["n_filter_changes"] = int((v.band != v.band.shift(1)).sum() - 1) if len(v) else 0

    # --- Start of night, and the non-survey visits ------------------------ #
    if len(v):
        row["start_of_night_h"] = max(
            (v.obs_start_mjd.min() - row["night_start_mjd"]) * 24.0, 0.0
        )
        row["end_of_night_h"] = max((row["night_end_mjd"] - v.obs_end_mjd.max()) * 24.0, 0.0)
    else:
        row["start_of_night_h"] = row["end_of_night_h"] = row["night_h"]
    nonsurvey = v[~v.is_survey]
    row["nonsurvey_visit_h"] = (
        (nonsurvey.obs_end_mjd - nonsurvey.obs_start_mjd).sum() * 24.0 if len(nonsurvey) else 0.0
    )

    # --- ROSP-24 blocks, copied straight through -------------------------- #
    rosp_cols = {
        "weather_hours": "weather_h",
        "focus_alignment_hours": "focus_h",
        "engineering_hours": "engineering_h",
        "planned_maintenance_hours": "planned_maintenance_h",
        "idle_bit_hours": "idle_h",
        "on_sky_hours": "rosp_on_sky_h",
        "night_hours_12": "rosp_night_h",
        "startup_hours": "startup_h",
        "label": "rosp_label",
    }
    if rosp24 is not None and int(day_obs) in rosp24.index:
        r = rosp24.loc[int(day_obs)]
        for src, dst in rosp_cols.items():
            row[dst] = r[src] if src in r.index else np.nan
        # Fault + idle is what the night lost with the dome open and no visit:
        # the -12 deg night minus weather, maintenance and everything accounted
        # for on sky, per the ROSP-24 precedence used in B1/B3/B11.
        accounted = (
            row["exposing_h"]
            + row["in_visit_h"]
            + row["gap_expected_h"]
            + row["gap_excess_h"]
            + row["nonsurvey_visit_h"]
            + np.nan_to_num(row["weather_h"])
            + np.nan_to_num(row["focus_h"])
            + np.nan_to_num(row["engineering_h"])
            + np.nan_to_num(row["planned_maintenance_h"])
        )
        row["fault_idle_h"] = max(row["night_h"] - accounted, 0.0)
    else:
        for dst in rosp_cols.values():
            row[dst] = np.nan
        row["fault_idle_h"] = np.nan
    return row


def budget_range(
    day_obs_min: int,
    day_obs_max: int,
    baseline: str = DEFAULT_BASELINE,
    consdb_client=None,
    efd_client=None,
) -> pd.DataFrame:
    """Run :func:`night_budget` over a ``day_obs`` range; one row per night."""
    consdb_client = consdb_client or get_consdb_client()
    efd_client = efd_client or get_efd_client()

    log.info("fetching visits %s - %s", day_obs_min, day_obs_max)
    visits = fetch_visits(consdb_client, day_obs_min, day_obs_max)
    if len(visits) == 0:
        raise SystemExit(f"no on-sky visits between {day_obs_min} and {day_obs_max}")
    visits = add_gaps(visits)
    log.info("modelling slews for %d visits", len(visits))
    visits = add_slew_models(visits, efd_client)

    rosp24 = load_rosp24()
    rows = [
        night_budget(day_obs, visits, rosp24, baseline)
        for day_obs in sorted(visits.day_obs.unique())
    ]
    return pd.DataFrame(rows), visits


# --------------------------------------------------------------------------- #
# Night selector                                                              #
# --------------------------------------------------------------------------- #
#: First night of the LSST survey era used by the selector (post-return nights
#: from 2026-10-26 are included when ConsDB has them).
LSST_DAY_OBS_MIN = 20260629


def select_nights(budget: pd.DataFrame, n: int = 5) -> pd.DataFrame:
    """The best "good night" candidates: clean nights, ranked by ``ratio``.

    A candidate has no weather loss, under half an hour of fault + idle and
    under half an hour of engineering + alignment, so that the bar shows a night
    that simply ran well rather than one that was short.

    The fault + idle cut is on ROSP-24's published ``idle_bit_hours`` (dome open,
    no visit, no other category), not on this module's ``fault_idle_h``.  The
    latter is a residual of the -12 deg night and so also absorbs the long and
    non-survey gaps that the Science split leaves out; gating on it would reject
    a night for time the figure shows inside the Science block.
    """
    clean = budget[
        (budget.day_obs >= LSST_DAY_OBS_MIN)
        & (budget.weather_hours_total <= 0.0)
        & (budget.idle_h.fillna(np.inf) < 0.5)
        & ((budget.engineering_h.fillna(np.inf) + budget.focus_h.fillna(np.inf)) < 0.5)
    ]
    return clean.nlargest(n, "ratio")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--day-obs", type=int, help="a single night")
    parser.add_argument("--day-obs-min", type=int, default=20260629)
    parser.add_argument("--day-obs-max", type=int, default=20261101)
    parser.add_argument("--baseline", default=DEFAULT_BASELINE, choices=sorted(IDEAL_OSF_FITS))
    parser.add_argument("--select", action="store_true", help="print the good-night candidates")
    parser.add_argument("--no-write", action="store_true")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    lo = hi = args.day_obs
    if args.day_obs is None:
        lo, hi = args.day_obs_min, args.day_obs_max

    budget, visits = budget_range(lo, hi, args.baseline)
    # weather_h is the ROSP-24 column; name the selector input explicitly so a
    # missing ROSP-24 CSV cannot silently pass the "no weather" test.
    budget["weather_hours_total"] = budget.weather_h.fillna(np.inf)

    cols = [
        "day_obs", "night_h", "n_survey", "n_vis_ave", "ratio", "ratio_v51",
        "exposing_h", "in_visit_h", "gap_expected_h", "gap_excess_h",
        "gap_median_s", "gap_mean_s", "start_of_night_h", "fault_idle_h",
    ]
    pd.set_option("display.width", 200)
    print(budget[cols].to_string(index=False, float_format=lambda x: f"{x:.3f}"))

    if not args.no_write:
        DATA.mkdir(parents=True, exist_ok=True)
        out = DATA / f"night_budget_{budget.day_obs.min()}_{budget.day_obs.max()}.csv"
        budget.drop(columns=["weather_hours_total"]).to_csv(out, index=False)
        vout = DATA / f"visits_slew_{budget.day_obs.min()}_{budget.day_obs.max()}.parquet"
        visits.to_parquet(vout, index=False)
        print(f"\nwrote {out.relative_to(DATA.parent)} and {vout.relative_to(DATA.parent)}")

    if args.select:
        print("\ngood-night candidates (weather 0, fault+idle < 0.5 h, eng+align < 0.5 h)")
        sel = select_nights(budget)
        if len(sel) == 0:
            print("  none - no night in range passes the cuts")
        else:
            print(
                sel[
                    [
                        "day_obs", "n_survey", "n_vis_ave", "ratio", "exposing_h",
                        "idle_h", "engineering_h", "focus_h", "fault_idle_h",
                    ]
                ]
                .to_string(index=False, float_format=lambda x: f"{x:.3f}")
            )


if __name__ == "__main__":
    main()
