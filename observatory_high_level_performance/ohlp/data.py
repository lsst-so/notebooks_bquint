"""Query ConsDB, the expected-visit model and the weather sources; cache to parquet.

Three per-night inputs are built here and cached under ``../data/``:

``visits``
    One row per survey visit (``science_program in SCIENCE_PROGRAMS``) from
    ``cdb_lsstcam.visit1`` LEFT JOIN ``visit1_quicklook``, augmented with
    ``rubin_nights.augment_visits`` so that ``fwhm_geom``, ``idiq_aos_cam`` and
    ``fwhm_500_zenith`` exist, exactly as in ``diq_vs_visit_rate.ipynb``.
``expected``
    One row per calendar ``day_obs`` with the expected visits from
    ``rubin_nights.dayobs_utils.estimated_baseline_visit_range`` and the night
    length between the -12 deg twilights.
``weather``
    One row per calendar ``day_obs`` with WEATHER hours from the EFD observatory
    state and (when an RSP token is available) weather hours from the narrative
    log.

Nights are always the integer ``day_obs`` (rolls over at 12:00 UTC), never the
UTC date of the exposure.

Access: ``get_consdb_client`` tries the RSP token route first and falls back to
the USDF Postgres replica, which is what works from an SDF login node. The EFD
works from both. The narrative log needs a valid token.
"""

from __future__ import annotations

import logging
import os
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from astropy.time import TimeDelta

from . import reference as ref

log = logging.getLogger(__name__)

#: rubin_scheduler almanac data (sunsets.npz etc.), needed by augment_visits.
#: USDF shared copy; set RUBIN_SIM_DATA_DIR yourself to override.
os.environ.setdefault("RUBIN_SIM_DATA_DIR", "/sdf/data/rubin/shared/rubin_sim_data")

HERE = Path(__file__).resolve().parent
DATA_DIR = HERE.parent / "data"

__all__ = [
    "DATA_DIR",
    "get_consdb_client",
    "day_obs_list",
    "fetch_visits",
    "fetch_expected",
    "fetch_weather",
    "build_cache",
    "load_cache",
]


# --------------------------------------------------------------------------- #
# Access                                                                       #
# --------------------------------------------------------------------------- #


def get_consdb_client(prefer: str = "token"):
    """ConsDB client: RSP token if available, else the USDF Postgres replica."""
    from rubin_nights import connections
    from rubin_nights.consdb_query import ConsDbSql

    if prefer == "token":
        logging.disable(logging.ERROR)
        try:
            client = connections.get_clients()["consdb"]
            if len(client.query("SELECT 1 AS one")) == 1:
                log.info("ConsDB via RSP token")
                return client
        except Exception as err:  # noqa: BLE001
            log.info("token route failed (%s); using Postgres", type(err).__name__)
        finally:
            logging.disable(logging.NOTSET)
    os.environ.setdefault(
        "PGPASSFILE", os.path.expanduser("~/.lsst/postgres-credentials.txt")
    )
    client = ConsDbSql(site="usdf")
    log.info("ConsDB via Postgres replica")
    return client


def _endpoints():
    from rubin_nights import connections

    logging.disable(logging.ERROR)
    try:
        return connections.get_clients()
    finally:
        logging.disable(logging.NOTSET)


# --------------------------------------------------------------------------- #
# Nights                                                                       #
# --------------------------------------------------------------------------- #


def day_obs_list(day_obs_min: int, day_obs_max: int) -> list[int]:
    """Every calendar ``day_obs`` from min to max inclusive."""
    import rubin_nights.dayobs_utils as rn_dayobs

    t0 = rn_dayobs.day_obs_to_time(int(day_obs_min))
    t1 = rn_dayobs.day_obs_to_time(int(day_obs_max))
    n = int(round((t1 - t0).jd)) + 1
    return [
        rn_dayobs.time_to_day_obs_int(
            t0 + TimeDelta(i, format="jd") + TimeDelta(0.5, format="jd")
        )
        for i in range(n)
    ]


def _month(day_obs: pd.Series | np.ndarray | int) -> np.ndarray | int:
    """``YYYYMM`` integer for a ``day_obs`` (grouping key for months)."""
    return (
        np.asarray(day_obs, dtype=int) // 100
        if not np.isscalar(day_obs)
        else int(day_obs) // 100
    )


# --------------------------------------------------------------------------- #
# Visits                                                                       #
# --------------------------------------------------------------------------- #

VISIT_COLUMNS = [
    "visit_id",
    "day_obs",
    "seq_num",
    "exp_midpt_mjd",
    "obs_start_mjd",
    "obs_end_mjd",
    "band",
    "science_program",
    "observation_reason",
    "target_name",
    "img_type",
    "exp_time",
    "airmass",
    "psf_sigma_median",
    "psf_area_median",
    "pixel_scale_median",
    "aos_fwhm",
    "donut_blur_fwhm",
    "fwhm_geom",
    "fwhm_eff",
    "fwhm_500_zenith",
    "atm_500_zenith",
    "idiq_aos_cam",
    "idiq_donut_blur",
]


def fetch_visits(
    client,
    day_obs_min: int,
    day_obs_max: int,
    instrument: str = "lsstcam",
    programs: tuple[str, ...] = ref.SCIENCE_PROGRAMS,
) -> pd.DataFrame:
    """Survey visits with the rubin_nights seeing columns.

    Same selection as diq_vs_visit_rate.ipynb: ``science_program in
    SCIENCE_PROGRAMS``, no image-type or airmass filter. The join and the
    augmentation are the ones in ``rubin_nights.consdb_query.get_visits``.
    """
    from rubin_nights.augment_visits import augment_visits

    progs = ", ".join(f"'{p}'" for p in programs)
    sql = (
        f"SELECT visit1.*, visit1_quicklook.* "
        f"FROM cdb_{instrument}.visit1 AS visit1 "
        f"LEFT JOIN cdb_{instrument}.visit1_quicklook AS visit1_quicklook "
        f"ON visit1.visit_id = visit1_quicklook.visit_id "
        f"WHERE visit1.day_obs >= {int(day_obs_min)} AND visit1.day_obs <= {int(day_obs_max)} "
        f"AND visit1.science_program IN ({progs}) "
        f"ORDER BY visit1.visit_id"
    )
    visits = client.query(sql)
    if len(visits) == 0:
        log.warning("no survey visits between %s and %s", day_obs_min, day_obs_max)
        return visits
    # Duplicate column names from the two tables (visit_id, day_obs, ...)
    visits = visits.loc[:, ~visits.columns.duplicated()]
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        visits = augment_visits(visits, instrument=instrument)
    keep = [c for c in VISIT_COLUMNS if c in visits.columns]
    visits = visits[keep].reset_index(drop=True)
    visits["day_obs"] = visits["day_obs"].astype(int)
    visits["month"] = _month(visits["day_obs"])
    return visits


# --------------------------------------------------------------------------- #
# Expected visits per night                                                    #
# --------------------------------------------------------------------------- #


def fetch_expected(day_obs_min: int, day_obs_max: int) -> pd.DataFrame:
    """Expected visits and night length for every calendar night in the range."""
    import rubin_nights.dayobs_utils as rn_dayobs
    from rubin_nights.dayobs_utils import estimated_baseline_visit_range

    rows = []
    for d in day_obs_list(day_obs_min, day_obs_max):
        est = estimated_baseline_visit_range(d)
        sunset, sunrise = rn_dayobs.day_obs_sunset_sunrise(d, sun_alt=-12)
        rows.append(
            {
                "day_obs": d,
                "n_vis_expected": est["n_vis_ave"],
                "n_vis_expected_high": est["n_vis_high"],
                "night_hours": (sunrise - sunset).jd * 24,
                "sunset12_mjd": sunset.mjd,
                "sunrise12_mjd": sunrise.mjd,
            }
        )
    out = pd.DataFrame(rows)
    out["month"] = _month(out["day_obs"])
    return out


# --------------------------------------------------------------------------- #
# Weather                                                                      #
# --------------------------------------------------------------------------- #


def fetch_weather(
    day_obs_min: int, day_obs_max: int, expected: pd.DataFrame
) -> pd.DataFrame:
    """Per-night weather hours from the EFD state (primary) and narrative log.

    Columns: ``weather_hours_efd``, ``fault_hours_efd``, ``downtime_hours_efd``,
    ``weather_hours_log``, ``fault_hours_log``, ``weather_frac`` (EFD weather hours
    over the -12 deg night length) and the boolean ``is_weather_night``
    (``weather_frac >= WEATHER_NIGHT_FRACTION``). Nights before the WEATHER state
    existed (2026-02-25) get NaN in the EFD columns and ``is_weather_night=False``;
    the ``weather_known`` column records which nights have a usable source.
    """
    import rubin_nights.dayobs_utils as rn_dayobs
    from rubin_nights import observatory_status

    endpoints = _endpoints()
    t0 = rn_dayobs.day_obs_to_time(int(day_obs_min))
    t1 = rn_dayobs.day_obs_to_time(int(day_obs_max)) + TimeDelta(1, format="jd")

    out = expected[["day_obs", "night_hours"]].copy()

    # EFD observatory state periods (overlapping; WEATHER usually spans the night)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        periods = observatory_status.get_observatory_state_times(
            t0, t1, endpoints["efd"]
        )
    if len(periods) > 0:
        hours = periods.groupby(["day_obs", "type"]).hours.sum().unstack(fill_value=0.0)
        hours.index = hours.index.astype(int)
        for state, col in [
            ("WEATHER", "weather_hours_efd"),
            ("FAULT", "fault_hours_efd"),
            ("DOWNTIME", "downtime_hours_efd"),
            ("OPERATIONAL", "operational_hours_efd"),
        ]:
            out[col] = out["day_obs"].map(
                hours[state] if state in hours else pd.Series(dtype=float)
            )
    else:
        for col in (
            "weather_hours_efd",
            "fault_hours_efd",
            "downtime_hours_efd",
            "operational_hours_efd",
        ):
            out[col] = np.nan
    # Nights after the state was deployed but with no record at all: zero, not NaN
    deployed = out["day_obs"] >= ref.DAY_OBS_WEATHER_STATE_AVAILABLE
    for col in (
        "weather_hours_efd",
        "fault_hours_efd",
        "downtime_hours_efd",
        "operational_hours_efd",
    ):
        out.loc[deployed & out[col].isna(), col] = 0.0

    # Narrative log (needs an RSP token; silently empty without one)
    out["weather_hours_log"] = np.nan
    out["fault_hours_log"] = np.nan
    try:
        logs = endpoints["narrative_log"].query_log(
            t0, t1, {"min_time_lost": "0.00001"}
        )
    except Exception as err:  # noqa: BLE001
        log.warning("narrative log unavailable: %s", type(err).__name__)
        logs = pd.DataFrame()
    out["narrative_log_available"] = len(logs) > 0
    if len(logs) > 0:
        logs = logs.query("not component.str.contains('AuxTel')", engine="python")
        for kind, col in [
            ("weather", "weather_hours_log"),
            ("fault", "fault_hours_log"),
        ]:
            s = logs.query("time_lost_type == @kind").groupby("day_obs").time_lost.sum()
            s.index = s.index.astype(int)
            out[col] = out["day_obs"].map(s).fillna(0.0)

    out["weather_frac"] = out["weather_hours_efd"] / out["night_hours"]
    out["weather_known"] = out["weather_hours_efd"].notna()
    out["is_weather_night"] = (
        out["weather_frac"] >= ref.WEATHER_NIGHT_FRACTION
    ).fillna(False)
    return out.drop(columns="night_hours")


# --------------------------------------------------------------------------- #
# Cache                                                                        #
# --------------------------------------------------------------------------- #


def _paths(day_obs_min: int, day_obs_max: int, data_dir: Path) -> dict[str, Path]:
    tag = f"{day_obs_min}_{day_obs_max}"
    return {
        "visits": data_dir / f"visits_{tag}.parquet",
        "expected": data_dir / f"expected_{tag}.parquet",
        "weather": data_dir / f"weather_{tag}.parquet",
    }


def build_cache(
    day_obs_min: int,
    day_obs_max: int,
    data_dir: Path = DATA_DIR,
    refresh: bool = False,
    client=None,
) -> dict[str, pd.DataFrame]:
    """Fetch (or read) the three tables and write them as parquet."""
    data_dir.mkdir(parents=True, exist_ok=True)
    paths = _paths(day_obs_min, day_obs_max, data_dir)
    out: dict[str, pd.DataFrame] = {}

    if not refresh and all(p.exists() for p in paths.values()):
        return load_cache(day_obs_min, day_obs_max, data_dir)

    if client is None:
        client = get_consdb_client()
    out["visits"] = fetch_visits(client, day_obs_min, day_obs_max)
    out["expected"] = fetch_expected(day_obs_min, day_obs_max)
    out["weather"] = fetch_weather(day_obs_min, day_obs_max, out["expected"])
    for key, df in out.items():
        df.to_parquet(paths[key])
        log.info("wrote %d rows to %s", len(df), paths[key])
    return out


def load_cache(
    day_obs_min: int, day_obs_max: int, data_dir: Path = DATA_DIR
) -> dict[str, pd.DataFrame]:
    paths = _paths(day_obs_min, day_obs_max, data_dir)
    return {k: pd.read_parquet(p) for k, p in paths.items()}
