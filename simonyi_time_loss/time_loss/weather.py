"""Weather-closure windows per night, from two independent sources.

1. **Observatory Status WEATHER bit** (``lsst.sal.Scheduler.logevent_observatoryStatus``
   via ``rubin_nights.observatory_status``), available from 2026-02-25. Primary
   source where it exists (handoff §1b).
2. **EFD operating criteria** (handoff §5, ``weather_criteria_table.md``,
   ``handoff_dynalene_condensation_criteria_2025-12_2026-01.md``), evaluated on the
   1-minute cache written by ``python/pull_efd_weather_1min.py``. Primary before
   2026-02-25 and a cross-check afterwards. The rules are applied with the
   validity window in force on each ``day_obs``; nothing is applied backwards.

What the EFD criteria can and cannot see
----------------------------------------
Wind, outside dew-point spread and the Dynalene-vs-dew-point condensation rule
are in telemetry. **Cloud cover is not** (no all-sky camera product in the EFD).
A cloud closure therefore shows up here as "dome closed, no criterion met" and is
left in the non-weather remainder unless a later step reclassifies it from the
night reports. ``closed_unexplained_hours`` is reported per night so that those
cases are visible.

Rules (CLOSE conditions on 1-minute series; ``P`` = persistence in minutes)
--------------------------------------------------------------------------
wind       10-min rolling mean of ``wind`` > 20 m/s, or 10-min rolling *minimum*
           of the per-minute gust ≥ 25 m/s ("sustained gusts"); stays closed until
           15 min with the 10-min mean below 20 m/s.                    whole range
dewpoint   ``t_out - dp_out`` < 2 °C for P = 20 min.                     whole range
dynalene   ``dyn - dp_out`` against a threshold that depends on the date:
             before 2025-12-15      no rule
             2025-12-15..2025-12-29 ≤ +2.0 °C, P = 20   (temporary close-dome rule)
             2025-12-30..2026-01-18 <  +2.0 °C, P = 20   (do-not-open rule, applied as closure)
             2026-01-19             ≤ +1.0 °C, P = 20
             2026-01-20..           <  -2.0 °C, P = 20   (v29 rule)
           ``dyn`` = ``dyn_az1`` (MTMount dynaleneCooling Azimuth0001; it matches
           the "Dynalene at Az" values quoted in the night reports and sits within
           0.3 °C of the handoff's ``coolPipeSplyTemp - 1.5``), falling back to
           ``sply - 1.5`` where Azimuth0001 is missing.

Runs of closed minutes separated by less than ``merge_min`` are merged into one
window. Windows are clipped to the accounting night (−12°, ``NIGHT_SUN_ALT``).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from . import DAY_OBS_WEATHER_BIT_START, NIGHT_END_COL, NIGHT_START_COL

__all__ = [
    "DYNALENE_RULES",
    "flag_minutes",
    "runs_to_windows",
    "efd_weather_night",
    "efd_weather_table",
    "weather_bit_table",
    "combine_weather",
]

#: (first day_obs inclusive, last day_obs inclusive, threshold, closed-if-strictly-below)
DYNALENE_RULES: tuple[tuple[int, int, float, bool], ...] = (
    (20251215, 20251229, 2.0, False),  # dyn - dp <= +2 -> closed
    (
        20251230,
        20260118,
        2.0,
        True,
    ),  # dyn - dp <  +2 -> do not open (applied as closed)
    (20260119, 20260119, 1.0, False),  # dyn - dp <= +1 -> closed
    (20260120, 99999999, -2.0, True),  # dyn - dp <  -2 -> closed
)

WIND_CLOSE_MEAN = 20.0
WIND_CLOSE_GUST = 25.0
WIND_REOPEN_MIN = 15
DEWPOINT_SPREAD_CLOSE = 2.0
PERSIST_MIN = 20
SHUTTER_OPEN_PCT = 50.0


def _dynalene_rule(day_obs: int):
    for lo, hi, thr, strict in DYNALENE_RULES:
        if lo <= day_obs <= hi:
            return thr, strict
    return None


def _persist(flag: pd.Series, minutes: int) -> pd.Series:
    """True where ``flag`` has been True for ``minutes`` consecutive samples."""
    return (
        flag.astype(float)
        .rolling(minutes, min_periods=minutes)
        .min()
        .fillna(0)
        .astype(bool)
    )


def flag_minutes(df: pd.DataFrame, day_obs: int) -> pd.DataFrame:
    """Per-minute CLOSE flags for one night. ``df`` is the 1-min cache for that night."""
    out = pd.DataFrame(index=df.index)
    # wind
    if "wind" in df:
        w10 = df["wind"].rolling(10, min_periods=5).mean()
        g10 = (
            df["gust"].rolling(10, min_periods=5).min()
            if "gust" in df
            else pd.Series(np.nan, index=df.index)
        )
        raw = (w10 > WIND_CLOSE_MEAN) | (g10 >= WIND_CLOSE_GUST)
        # hysteresis: once closed, stay closed until 15 consecutive minutes below the mean limit
        calm15 = _persist(~(w10 > WIND_CLOSE_MEAN), WIND_REOPEN_MIN)
        closed = np.zeros(len(df), bool)
        state = False
        for i, (r, c) in enumerate(zip(raw.to_numpy(), calm15.to_numpy())):
            if r:
                state = True
            elif state and c:
                state = False
            closed[i] = state
        out["wind"] = closed
    else:
        out["wind"] = False
    # outside dew-point spread
    if {"t_out", "dp_out"} <= set(df.columns):
        out["dewpoint"] = _persist(
            (df["t_out"] - df["dp_out"]) < DEWPOINT_SPREAD_CLOSE, PERSIST_MIN
        )
    else:
        out["dewpoint"] = False
    # dynalene condensation rule, by validity window
    rule = _dynalene_rule(day_obs)
    dyn = df["dyn_az1"] if "dyn_az1" in df else pd.Series(np.nan, index=df.index)
    if "sply" in df:
        dyn = dyn.fillna(df["sply"] - 1.5)
    out["dyn_minus_dp"] = dyn - df["dp_out"] if "dp_out" in df else np.nan
    if rule is not None and "dp_out" in df:
        thr, strict = rule
        cond = out["dyn_minus_dp"] < thr if strict else out["dyn_minus_dp"] <= thr
        out["dynalene"] = _persist(cond.fillna(False), PERSIST_MIN)
    else:
        out["dynalene"] = False
    out["any"] = out[["wind", "dewpoint", "dynalene"]].any(axis=1)
    # physical state, for the "closed but no criterion" check
    out["shutter_open"] = (
        (df["shutter"] > SHUTTER_OPEN_PCT) if "shutter" in df else np.nan
    )
    out["mcover_closed"] = (df["mcover"] > 60) if "mcover" in df else np.nan
    out["at_horizon"] = (df["el"] < 5) if "el" in df else np.nan
    return out


def runs_to_windows(flag: pd.Series, merge_min: int = 10) -> np.ndarray:
    """Contiguous True runs of a 1-min boolean series → (n, 2) array of UTC MJD."""
    if not flag.any():
        return np.empty((0, 2))
    idx = flag.index
    f = flag.to_numpy()
    edges = np.flatnonzero(np.diff(np.r_[0, f.astype(int), 0]))
    starts, ends = edges[::2], edges[1::2]
    t = np.asarray(idx.view("int64"), dtype=float) / 86400e9 + 40587.0
    win = [[t[s], t[e - 1] + 1 / 1440.0] for s, e in zip(starts, ends)]
    merged = [win[0]]
    for a, b in win[1:]:
        if (a - merged[-1][1]) * 1440.0 < merge_min:
            merged[-1][1] = b
        else:
            merged.append([a, b])
    return np.array(merged)


def clip_windows(win: np.ndarray, t0: float, t1: float) -> np.ndarray:
    if len(win) == 0:
        return win
    w = win.copy()
    w[:, 0] = np.clip(w[:, 0], t0, t1)
    w[:, 1] = np.clip(w[:, 1], t0, t1)
    return w[w[:, 1] > w[:, 0]]


def hours(win: np.ndarray) -> float:
    return float((win[:, 1] - win[:, 0]).sum() * 24) if len(win) else 0.0


@dataclass
class NightWeather:
    day_obs: int
    windows: np.ndarray  # any-criterion CLOSE windows, UTC MJD, clipped to the night
    hours_by_rule: dict[str, float]
    closed_unexplained_hours: float
    n_minutes: int
    n_minutes_missing: int


def efd_weather_night(
    df: pd.DataFrame, day_obs: int, t0: float, t1: float, merge_min: int = 10
) -> NightWeather:
    """Evaluate the criteria on one night's 1-min cache and clip to [t0, t1] (UTC MJD)."""
    f = flag_minutes(df, day_obs)
    mjd = np.asarray(f.index.view("int64"), dtype=float) / 86400e9 + 40587.0
    innight = (mjd >= t0) & (mjd < t1)
    fin = f[innight]
    by_rule = {
        k: float(fin[k].sum()) / 60.0 for k in ("wind", "dewpoint", "dynalene", "any")
    }
    # dome shut (or telescope at horizon with covers on) inside the night with no criterion met
    phys_closed = (~fin["shutter_open"].fillna(True)) | (
        fin["at_horizon"].fillna(False) & fin["mcover_closed"].fillna(False)
    )
    unexplained = float((phys_closed & ~fin["any"]).sum()) / 60.0
    win = clip_windows(runs_to_windows(f["any"], merge_min), t0, t1)
    missing = (
        int(fin["dyn_minus_dp"].isna().sum())
        if len(fin)
        else int(round((t1 - t0) * 1440))
    )
    return NightWeather(
        int(day_obs), win, by_rule, unexplained, int(innight.sum()), missing
    )


def efd_weather_table(
    cache: pd.DataFrame,
    limits: pd.DataFrame,
    start_col=NIGHT_START_COL,
    end_col=NIGHT_END_COL,
) -> tuple[pd.DataFrame, dict[int, NightWeather]]:
    rows, res = [], {}
    by_night = {d: g.drop(columns="day_obs") for d, g in cache.groupby("day_obs")}
    for r in limits.itertuples(index=False):
        d = int(r.day_obs)
        g = by_night.get(d)
        t0, t1 = getattr(r, start_col), getattr(r, end_col)
        if g is None or len(g) == 0:
            nw = NightWeather(
                d,
                np.empty((0, 2)),
                dict(wind=np.nan, dewpoint=np.nan, dynalene=np.nan, any=np.nan),
                np.nan,
                0,
                int(round((t1 - t0) * 1440)),
            )
        else:
            nw = efd_weather_night(g, d, t0, t1)
        res[d] = nw
        rows.append(
            dict(
                day_obs=d,
                efd_weather_hours=round(hours(nw.windows), 3),
                efd_wind_hours=round(nw.hours_by_rule["wind"], 3),
                efd_dewpoint_hours=round(nw.hours_by_rule["dewpoint"], 3),
                efd_dynalene_hours=round(nw.hours_by_rule["dynalene"], 3),
                closed_unexplained_hours=round(nw.closed_unexplained_hours, 3)
                if np.isfinite(nw.closed_unexplained_hours)
                else np.nan,
                efd_minutes=nw.n_minutes,
                efd_minutes_missing=nw.n_minutes_missing,
                efd_n_windows=int(len(nw.windows)),
            )
        )
    return pd.DataFrame(rows), res


def weather_bit_table(
    periods: pd.DataFrame,
    limits: pd.DataFrame,
    start_col=NIGHT_START_COL,
    end_col=NIGHT_END_COL,
) -> tuple[pd.DataFrame, dict[int, np.ndarray]]:
    """WEATHER-bit windows per night from ``rubin_nights`` periods, clipped to the accounting night."""
    w = periods[periods["type"] == "WEATHER"].copy()
    w["day_obs"] = w["day_obs"].astype(int)
    w["s"] = (
        pd.to_datetime(w["start"]).dt.tz_localize(None).astype("int64") / 86400e9
        + 40587.0
    )
    w["e"] = (
        pd.to_datetime(w["end"]).dt.tz_localize(None).astype("int64") / 86400e9
        + 40587.0
    )
    rows, res = [], {}
    for r in limits.itertuples(index=False):
        d = int(r.day_obs)
        g = w[w.day_obs == d]
        win = (
            clip_windows(
                g[["s", "e"]].to_numpy(dtype=float),
                getattr(r, start_col),
                getattr(r, end_col),
            )
            if len(g)
            else np.empty((0, 2))
        )
        res[d] = win
        available = d >= DAY_OBS_WEATHER_BIT_START
        rows.append(
            dict(
                day_obs=d,
                bit_weather_hours=round(hours(win), 3) if available else np.nan,
                bit_n_windows=int(len(win)) if available else np.nan,
                bit_available=available,
            )
        )
    return pd.DataFrame(rows), res


def combine_weather(bit: pd.DataFrame, efd: pd.DataFrame) -> pd.DataFrame:
    """Primary weather_hours: WEATHER bit where available, EFD criteria before that."""
    t = bit.merge(efd, on="day_obs")
    t["weather_hours"] = np.where(
        t.bit_available, t.bit_weather_hours, t.efd_weather_hours
    )
    t["weather_source"] = np.where(t.bit_available, "WEATHER bit", "EFD criteria")
    return t
