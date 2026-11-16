"""Shared helpers for the nightly_survey_speed notebooks.

Query ConsDB visits, classify them by science program, compute per-night twilight
times, and provide the Rubin plotting colors. Both the reproduction and the
interactive on-sky utilization notebooks import from here, and the planned image
quality vs visit rate notebook is meant to reuse ``get_consdb_client``,
``fetch_visits`` and ``categorize_visits`` unchanged.

Conventions
-----------
* Nights are always identified by the integer ``day_obs`` (YYYYMMDD) from ConsDB,
  never by the UTC calendar date of the exposure. A Chilean night spans roughly
  23:00 to 11:00 UTC, so one night straddles two UTC dates.
* Times within a night are expressed in hours after 00:00 UTC on the calendar day
  *after* ``day_obs`` (the morning side of the night). This is what the original
  sp_notebooks figure does; its markdown calls it "local midnight" but the code
  uses UTC midnight. Local midnight at the summit is 03:00 UTC (CLST) or 04:00 UTC
  (CLT).
"""

from __future__ import annotations

import datetime
import logging
import os
import sys
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd
from astropy.time import Time

__all__ = [
    "SURVEY_PROGRAMS_EARLY_OPS",
    "FOCUS_PROGRAMS",
    "IMG_TYPES",
    "CATEGORY_ORDER",
    "SUMMIT_TZ",
    "get_consdb_client",
    "fetch_visits",
    "categorize_visits",
    "category_changes",
    "programs_in_range",
    "day_obs_to_time",
    "day_obs_range",
    "hours_after_utc_midnight",
    "local_offset_hours",
    "to_local_hours",
    "add_time_columns",
    "twilight_table",
    "rubin_category_colors",
]

# --------------------------------------------------------------------------- #
# Reference values (same as lsst/sp_notebooks on-sky_utilization.ipynb)        #
# --------------------------------------------------------------------------- #

#: Feature Based Scheduler programs counted as "Survey Programs" in the original
#: notebook (Early Operations list). ``rubin_nights.reference_values.SCIENCE_PROGRAMS``
#: additionally contains BLOCK-365, which the original treats as engineering.
SURVEY_PROGRAMS_EARLY_OPS: tuple[str, ...] = (
    "BLOCK-407",
    "BLOCK-408",
    "BLOCK-416",
    "BLOCK-417",
    "BLOCK-419",
    "BLOCK-421",
)

#: Optical focus and alignment block (exact match; BLOCK-T539_hexapods is not matched).
FOCUS_PROGRAMS: tuple[str, ...] = ("BLOCK-T539",)

#: ``img_type`` values kept by the original query. Note that on-sky ``engtest``
#: exposures are dropped by this filter.
IMG_TYPES: tuple[str, ...] = ("acq", "science", "cwfs", "focus")

#: Display order of the categories. Also the drawing order (last on top).
CATEGORY_ORDER: tuple[str, ...] = (
    "Engineering",
    "Survey Programs",
    "Focus and Alignment",
)

SUMMIT_TZ = ZoneInfo("America/Santiago")

_PLATESCALE = 0.2  # arcsec / pixel, rubin_nights.reference_values.PLATESCALE
_SIGMA_TO_FWHM = 2.0 * np.sqrt(2.0 * np.log(2.0))

log = logging.getLogger(__name__)


# --------------------------------------------------------------------------- #
# ConsDB access                                                                #
# --------------------------------------------------------------------------- #


def get_consdb_client(prefer: str = "token"):
    """Return a ``rubin_nights`` ConsDB client that works where we are.

    Parameters
    ----------
    prefer : {"token", "postgres"}
        ``"token"`` tries ``rubin_nights.connections.get_clients()`` first (needs
        an RSP token, which Nublado kernels have) and falls back to the direct
        Postgres replica. ``"postgres"`` goes straight to the replica, which is
        what works on an SDF login node (VS Code over SSH). The replica needs
        ``~/.lsst/postgres-credentials.txt``; ``PGPASSFILE`` is pointed at it if
        unset.

    Returns
    -------
    client
        Object with a ``.query(sql) -> pandas.DataFrame`` method.
    """
    from rubin_nights import connections
    from rubin_nights.consdb_query import ConsDbSql

    if prefer == "token":
        logging.disable(logging.ERROR)  # silence the expected "No RSP token found"
        try:
            client = connections.get_clients()["consdb"]
            if len(client.query("SELECT 1 AS one")) == 1:
                log.info("ConsDB via RSP token: %s", client)
                return client
        except Exception as err:  # noqa: BLE001 - any failure means "not on the RSP"
            log.info(
                "Token route failed (%s); falling back to Postgres", type(err).__name__
            )
        finally:
            logging.disable(logging.NOTSET)

    os.environ.setdefault(
        "PGPASSFILE", os.path.expanduser("~/.lsst/postgres-credentials.txt")
    )
    client = ConsDbSql(site="usdf")
    log.info("ConsDB via Postgres replica: %s", client)
    return client


def fetch_visits(
    client,
    day_obs_min: int,
    day_obs_max: int,
    instrument: str = "lsstcam",
    img_types: tuple[str, ...] = IMG_TYPES,
    with_quicklook: bool = True,
    cache_dir: str | Path | None = None,
    use_cache: bool = True,
) -> pd.DataFrame:
    """Fetch ``visit1`` rows for a day_obs range, optionally with PSF quicklook values.

    The WHERE clause is the one from the original notebook: ``airmass > 0``,
    ``img_type IN img_types``, ``day_obs BETWEEN day_obs_min AND day_obs_max``.
    With ``with_quicklook`` the ``visit1_quicklook.psf_sigma_median`` column is
    LEFT JOINed and converted to ``psf_fwhm_arcsec`` (sigma to FWHM, 0.2 arcsec
    per pixel); visits without quicklook results get NaN.

    Results are sorted by ``obs_start_mjd``. If ``cache_dir`` is given, the frame
    is cached as parquet keyed on the arguments.
    """
    cache_file = None
    if cache_dir is not None:
        tag = "ql" if with_quicklook else "v1"
        cache_file = (
            Path(cache_dir)
            / f"{instrument}_visits_{tag}_{day_obs_min}_{day_obs_max}.parquet"
        )
        if use_cache and cache_file.exists():
            visits = pd.read_parquet(cache_file)
            log.info("read %d visits from %s", len(visits), cache_file)
            return visits

    types = ", ".join(f"'{t}'" for t in img_types)
    where = (
        f"visit1.airmass > 0 AND visit1.img_type IN ({types}) "
        f"AND visit1.day_obs >= {int(day_obs_min)} AND visit1.day_obs <= {int(day_obs_max)}"
    )
    if with_quicklook:
        sql = (
            f"SELECT visit1.*, ql.psf_sigma_median "
            f"FROM cdb_{instrument}.visit1 AS visit1 "
            f"LEFT JOIN cdb_{instrument}.visit1_quicklook AS ql ON visit1.visit_id = ql.visit_id "
            f"WHERE {where}"
        )
    else:
        sql = f"SELECT visit1.* FROM cdb_{instrument}.visit1 AS visit1 WHERE {where}"

    visits = client.query(sql)
    if len(visits) == 0:
        log.warning(
            "no visits for %s between %s and %s", instrument, day_obs_min, day_obs_max
        )
        return visits
    visits = visits.sort_values("obs_start_mjd").reset_index(drop=True)
    if with_quicklook:
        visits["psf_fwhm_arcsec"] = (
            visits["psf_sigma_median"] * _SIGMA_TO_FWHM * _PLATESCALE
        )
    if cache_file is not None:
        cache_file.parent.mkdir(parents=True, exist_ok=True)
        visits.to_parquet(cache_file)
        log.info("fetched %d visits, cached to %s", len(visits), cache_file)
    return visits


# --------------------------------------------------------------------------- #
# Categorization                                                               #
# --------------------------------------------------------------------------- #


def categorize_visits(
    visits: pd.DataFrame,
    survey_programs=SURVEY_PROGRAMS_EARLY_OPS,
    focus_programs=FOCUS_PROGRAMS,
    exclusive: bool = False,
) -> pd.DataFrame:
    """Return a copy of ``visits`` with boolean membership columns and a ``category``.

    Columns added
    -------------
    is_survey, is_focus, is_engineering : bool
        Membership of each visit in each drawn layer.
    category : str
        One label per visit, used for the exclusive view and for tables.

    Parameters
    ----------
    exclusive : bool
        ``False`` reproduces the original notebook: ``is_engineering = ~is_survey``,
        so focus visits are members of two layers (drawn in orange and again in
        green). ``True`` makes the layers disjoint with the priority
        Focus and Alignment > Survey Programs > Engineering.
    """
    out = visits.copy()
    prog = out["science_program"].astype("string")
    is_survey = prog.isin(list(survey_programs)).fillna(False).to_numpy(dtype=bool)
    is_focus = prog.isin(list(focus_programs)).fillna(False).to_numpy(dtype=bool)

    category = np.where(
        is_focus,
        "Focus and Alignment",
        np.where(is_survey, "Survey Programs", "Engineering"),
    )
    out["category"] = pd.Categorical(category, categories=list(CATEGORY_ORDER))

    if exclusive:
        out["is_focus"] = is_focus
        out["is_survey"] = is_survey & ~is_focus
        out["is_engineering"] = ~(is_survey | is_focus)
    else:
        out["is_focus"] = is_focus
        out["is_survey"] = is_survey
        out["is_engineering"] = ~is_survey
    return out


def category_changes(
    visits: pd.DataFrame,
    survey_programs=SURVEY_PROGRAMS_EARLY_OPS,
    focus_programs=FOCUS_PROGRAMS,
) -> pd.DataFrame:
    """Which visits move between layers when categories are made exclusive.

    Returns one row per (science_program, change) with the visit count and the
    first and last day_obs affected. With the original rules a visit can be in
    more than one layer; the exclusive rules keep exactly one. The only possible
    changes are "leaves Engineering" (focus visits) and "leaves Survey Programs"
    (a program that is in both lists, which is not the case for the defaults).
    """
    orig = categorize_visits(visits, survey_programs, focus_programs, exclusive=False)
    excl = categorize_visits(visits, survey_programs, focus_programs, exclusive=True)
    rows = []
    for layer in ("is_engineering", "is_survey", "is_focus"):
        moved = orig[layer] & ~excl[layer]
        if moved.any():
            grp = orig.loc[moved].groupby("science_program", observed=True)["day_obs"]
            for program, g in grp:
                rows.append(
                    {
                        "science_program": program,
                        "change": f"leaves {layer.removeprefix('is_').replace('survey', 'Survey Programs').replace('engineering', 'Engineering').replace('focus', 'Focus and Alignment')}",
                        "n_visits": int(len(g)),
                        "first_day_obs": int(g.min()),
                        "last_day_obs": int(g.max()),
                    }
                )
    return pd.DataFrame(
        rows,
        columns=[
            "science_program",
            "change",
            "n_visits",
            "first_day_obs",
            "last_day_obs",
        ],
    )


def programs_in_range(
    visits: pd.DataFrame,
    day_obs_min: int | None = None,
    day_obs_max: int | None = None,
    survey_programs=SURVEY_PROGRAMS_EARLY_OPS,
    focus_programs=FOCUS_PROGRAMS,
) -> pd.DataFrame:
    """Table of science programs seen in a sub-range, flagged against the lists.

    Useful to check whether the hard-coded survey list is complete for a period
    (for example the LSST period starting 20260629). ``looks_like_survey`` flags
    ``BLOCK-<digits>`` names (no ``T``), which is the naming pattern of the
    scheduler-driven survey blocks, so an unflagged one deserves a look.
    """
    sel = pd.Series(True, index=visits.index)
    if day_obs_min is not None:
        sel &= visits["day_obs"] >= day_obs_min
    if day_obs_max is not None:
        sel &= visits["day_obs"] <= day_obs_max
    sub = visits.loc[sel]
    tab = (
        sub.groupby("science_program", dropna=False, observed=True)
        .agg(
            n_visits=("visit_id", "size"),
            first_day_obs=("day_obs", "min"),
            last_day_obs=("day_obs", "max"),
        )
        .reset_index()
        .sort_values("n_visits", ascending=False)
        .reset_index(drop=True)
    )
    tab["in_survey_list"] = tab["science_program"].isin(list(survey_programs))
    tab["in_focus_list"] = tab["science_program"].isin(list(focus_programs))
    tab["looks_like_survey"] = (
        tab["science_program"]
        .astype("string")
        .str.fullmatch(r"BLOCK-\d+")
        .fillna(False)
    )
    return tab


# --------------------------------------------------------------------------- #
# Time handling                                                                #
# --------------------------------------------------------------------------- #


def day_obs_to_time(day_obs) -> Time:
    """00:00 UTC on the calendar date written in ``day_obs`` (scalar or array)."""
    s = pd.Series(np.atleast_1d(day_obs)).astype(int).astype(str)
    iso = s.str[0:4] + "-" + s.str[4:6] + "-" + s.str[6:8] + " 00:00:00"
    t = Time(iso.to_list(), format="iso", scale="utc")
    return t[0] if np.ndim(day_obs) == 0 else t


def day_obs_range(day_obs_min: int, day_obs_max: int) -> np.ndarray:
    """Every calendar day_obs from min to max inclusive, as integers."""
    d0 = datetime.date(
        int(str(day_obs_min)[:4]),
        int(str(day_obs_min)[4:6]),
        int(str(day_obs_min)[6:8]),
    )
    d1 = datetime.date(
        int(str(day_obs_max)[:4]),
        int(str(day_obs_max)[4:6]),
        int(str(day_obs_max)[6:8]),
    )
    days = pd.date_range(d0, d1, freq="D")
    return days.strftime("%Y%m%d").astype(int).to_numpy()


def hours_after_utc_midnight(mjd, day_obs) -> np.ndarray:
    """Hours between an MJD and 00:00 UTC on the day after ``day_obs``.

    This is the y coordinate of the original figure (``convertTime``). Negative
    values are the evening side before UTC midnight; a visit at 03:00 UTC is 3.0.
    """
    ref = np.atleast_1d(day_obs_to_time(day_obs).mjd) + 1.0
    hours = (np.asarray(mjd, dtype=float) - ref) * 24.0
    return float(hours[0]) if np.ndim(mjd) == 0 and np.ndim(day_obs) == 0 else hours


def local_offset_hours(day_obs) -> np.ndarray:
    """UTC offset of ``SUMMIT_TZ`` (hours, negative) at 00:00 UTC on day_obs + 1.

    The Chilean night does not cross a daylight-saving change (changes happen at
    24:00 local on a Saturday, i.e. 03:00/04:00 UTC on Sunday, which is in the
    middle of the night, but the ``day_obs`` rollover at 12:00 UTC keeps whole
    nights on one side), so one value per night is enough: -3 (CLST, summer) or
    -4 (CLT, winter).
    """
    s = pd.Series(np.atleast_1d(day_obs)).astype(int).astype(str)
    t = pd.to_datetime(s, format="%Y%m%d", utc=True) + pd.Timedelta(days=1)
    return np.array(
        [x.tz_convert(SUMMIT_TZ).utcoffset().total_seconds() / 3600 for x in t]
    )


def to_local_hours(hours_utc, day_obs) -> np.ndarray:
    """Hours after 00:00 UTC on day_obs + 1 -> hours after local clock midnight."""
    return np.asarray(hours_utc, dtype=float) + local_offset_hours(day_obs)


def add_time_columns(visits: pd.DataFrame) -> pd.DataFrame:
    """Add plotting and hover time columns to a categorized visit frame.

    Columns added: ``t_mid_h``, ``t_start_h``, ``t_end_h`` (hours after 00:00 UTC
    on day_obs + 1), ``night_utc`` (datetime of 00:00 UTC on day_obs, for a
    continuous x-axis), ``day_obs_str``, ``utc_mid`` and ``local_mid`` (strings
    for hover, local = America/Santiago).
    """
    out = visits.copy()
    day_obs = out["day_obs"].to_numpy()
    out["t_mid_h"] = hours_after_utc_midnight(out["exp_midpt_mjd"].to_numpy(), day_obs)
    out["t_start_h"] = hours_after_utc_midnight(
        out["obs_start_mjd"].to_numpy(), day_obs
    )
    out["t_end_h"] = hours_after_utc_midnight(out["obs_end_mjd"].to_numpy(), day_obs)
    out["day_obs_str"] = out["day_obs"].astype(int).astype(str)
    out["night_utc"] = pd.to_datetime(out["day_obs_str"], format="%Y%m%d", utc=True)
    mid = pd.to_datetime(
        Time(out["exp_midpt_mjd"].to_numpy(), format="mjd").utc.isot, utc=True
    )
    out["utc_mid"] = mid.strftime("%Y-%m-%d %H:%M:%S")
    out["local_mid"] = mid.tz_convert(SUMMIT_TZ).strftime("%Y-%m-%d %H:%M:%S %Z")
    return out


# --------------------------------------------------------------------------- #
# Twilight                                                                     #
# --------------------------------------------------------------------------- #


def twilight_table(
    day_obs_min: int, day_obs_max: int, site: str = "LSST"
) -> pd.DataFrame:
    """Evening and morning twilight times for every calendar night in the range.

    Follows the original notebook: ``astroplan.Observer.at_site(site)``, the
    reference midnight is the one nearest to 23:59 UTC on ``day_obs``, evening
    twilights are searched backwards and morning twilights forwards from it.
    Nautical is -12 deg and astronomical is -18 deg solar elevation.

    Returns a frame with one row per day_obs and columns ``day_obs``,
    ``night_utc`` (00:00 UTC on day_obs), ``solar_midnight_h`` (astroplan's
    ``midnight`` is the Sun's anti-transit, about 04:45 UTC at the summit, not
    clock midnight) and the four
    twilight columns ``evening_nautical_h``, ``evening_astronomical_h``,
    ``morning_astronomical_h``, ``morning_nautical_h``, all in hours after
    00:00 UTC on day_obs + 1.
    """
    from astroplan import Observer

    observer = Observer.at_site(site)
    days = day_obs_range(day_obs_min, day_obs_max)
    s = pd.Series(days).astype(str)
    late = Time(
        (s.str[0:4] + "-" + s.str[4:6] + "-" + s.str[6:8] + " 23:59:00").to_list(),
        format="iso",
        scale="utc",
    )
    midnight = observer.midnight(late, which="nearest")

    cols = {
        "evening_nautical_h": observer.twilight_evening_nautical(
            midnight, which="previous"
        ),
        "evening_astronomical_h": observer.twilight_evening_astronomical(
            midnight, which="previous"
        ),
        "morning_astronomical_h": observer.twilight_morning_astronomical(
            midnight, which="next"
        ),
        "morning_nautical_h": observer.twilight_morning_nautical(
            midnight, which="next"
        ),
        "solar_midnight_h": midnight,
    }
    out = pd.DataFrame({"day_obs": days})
    out["night_utc"] = pd.to_datetime(s, format="%Y%m%d", utc=True)
    for name, t in cols.items():
        out[name] = hours_after_utc_midnight(t.utc.mjd, days)
    return out


# --------------------------------------------------------------------------- #
# Colors                                                                       #
# --------------------------------------------------------------------------- #

# Path resolved relative to this file; copy the palette module into this folder
# before extracting the investigation.
_PALETTE_DIR = Path(__file__).resolve().parent.parent / "rubin_color_pallete"


def rubin_category_colors() -> dict[str, str]:
    """Colors for the three categories from the repo's shared category table.

    Reads ``CATEGORY_COLORS`` of ``rubin_color_pallete/rubin_palette.py``, the
    table every figure in the repo shares. Its three values are the seaborn
    colorblind blue, orange and green this plot has always used (the
    ``lsst.utils`` ``rubin.mplstyle`` cycle): Survey Programs blue, Engineering
    orange, Focus and Alignment green, the same roles as the ``tab:`` colors in
    the original figure.
    """
    if str(_PALETTE_DIR) not in sys.path:
        sys.path.insert(0, str(_PALETTE_DIR))
    import rubin_palette as rp

    return {
        "Survey Programs": rp.CATEGORY_COLORS["survey"],
        "Engineering": rp.CATEGORY_COLORS["engineering"],
        "Focus and Alignment": rp.CATEGORY_COLORS["focus"],
    }
