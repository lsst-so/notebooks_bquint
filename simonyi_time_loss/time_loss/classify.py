"""ROSP-24 ordered per-minute classifier of the −12° observable night.

One assignment feeds every figure and ``per_night.csv``. Time goes to the first
category in the ROSP-24 precedence list (comment of 2026-10-19) that applies:

    1. B1 planned maintenance   none in 2025-10-25 → 2026-07-14 (ROSP-28); the category
                                exists and is zero
    2. C  weather               WEATHER bit (from 2026-02-25); where the bit is absent
                                (before) or masked (FAULT or DOWNTIME set, bit unset)
                                the §C fallback: allskycam cloud index > 0.5 or the C1
                                weather-tower limits (fallback.py)
    3. Focus and Alignment      BLOCK-T539 visits in blocks bridged at gaps ≤ 10 min; its
                                own category (Bruno, 2026-10-27: not engineering, not
                                survey — the explicit split tells the progress story)
    3b. B2 engineering          the other on-sky visits that are not Survey Programs, in
                                blocks bridged at gaps ≤ 10 min (engineering_time_budget
                                rule); a bridged gap between a focus and an engineering
                                visit is engineering
    4. D  technical fault  }    everything in the night not assigned above and not
    5. E  operational idle }    covered by a survey visit or a bridged gap; D and E
                                stay merged ("fault + idle", ROSP-50 open). Includes
                                unplanned DOWNTIME (D4) and the Dynalene condensation
                                windows (D4-like, tag ``dynalene``; Bruno 2026-10-26)
    6. A  science operations    A1 + A2 (+ D3 gap excess, ROSP-49 open) = survey visits
                                with gaps ≤ 10 min bridged; A3 = start-up allowance,
                                the first 10 min after evening −12° up to the first
                                survey visit
    7. F  unattributed          UNKNOWN observatory state (from 2026-02-25) where it
                                would otherwise be fault + idle; not separable before

Implementation detail that follows from strict precedence: minutes inside a
WEATHER window that are also covered by visits go to weather, not to science;
the overlap is reported as ``weather_and_onsky_hours``. Fault-state minutes that
fall inside a bridged on-sky window stay on sky (the handoff defines D + E as the
remainder, not from the state bits). Shadow record: ``weather_masked_fault_hours``
= weather minutes during which FAULT or DOWNTIME was set (bit era only).

All sets are interval arrays in UTC MJD (``intervals.py``); the categories
partition the night exactly, so the per-night columns sum to ``night_hours``.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from . import DAY_OBS_WEATHER_BIT_START, GAP_MIN_MINUTES, NIGHT_END_COL, NIGHT_START_COL
from .intervals import clip, empty, hours, intersect, normalize, subtract, union
from .visits import merge_intervals

__all__ = [
    "SURVEY_PROGRAMS",
    "FOCUS_PROGRAMS",
    "STARTUP_ALLOWANCE_MIN",
    "PLANNED_MAINTENANCE",
    "NightClassification",
    "state_windows",
    "category_blocks",
    "classify_night",
    "classify_all",
    "label_night",
]

#: Survey Programs (engineering_time_budget / nightly_survey_speed categories).
SURVEY_PROGRAMS = (
    "BLOCK-407",
    "BLOCK-408",
    "BLOCK-416",
    "BLOCK-417",
    "BLOCK-419",
    "BLOCK-421",
)
FOCUS_PROGRAMS = ("BLOCK-T539",)
#: A3 start-up allowance (ROSP-24, 2026-10-26): first 10 min after evening −12°.
STARTUP_ALLOWANCE_MIN = 10.0
#: B1 planned-maintenance blocks as (day_obs_first, day_obs_last) inclusive, noon→noon UTC.
#: ROSP-28: the only planned-downtime block in the ledger is 14 Sep → 5 Oct 2026, outside the range.
PLANNED_MAINTENANCE: tuple[tuple[int, int], ...] = ()
MJD_UNIX = 40587.0


def _ts_to_mjd(s: pd.Series) -> np.ndarray:
    return (
        pd.to_datetime(s).dt.tz_localize(None).astype("int64").to_numpy() / 86400e9
        + MJD_UNIX
    )


def state_windows(
    periods: pd.DataFrame, day_obs: int, t0: float, t1: float
) -> dict[str, np.ndarray]:
    """Observatory-state interval sets for one night, clipped to [t0, t1]."""
    p = periods[periods["day_obs"].astype(int) == int(day_obs)]
    out = {}
    for ty in ("WEATHER", "FAULT", "DOWNTIME", "IDLE", "UNKNOWN", "OPERATIONAL"):
        g = p[p["type"] == ty]
        if len(g):
            w = np.column_stack([_ts_to_mjd(g["start"]), _ts_to_mjd(g["end"])])
            out[ty] = clip(normalize(w), t0, t1)
        else:
            out[ty] = empty()
    return out


def category_blocks(visits: pd.DataFrame, bridge_days: float) -> dict[str, np.ndarray]:
    """Visit unions per category (survey / focus / engineering / any), bridged at ≤ gap_min
    *within* the category (engineering_time_budget block rule), plus the all-visit union."""
    prog = visits["science_program"].astype("string")
    cat = np.where(
        prog.isin(FOCUS_PROGRAMS),
        "focus",
        np.where(prog.isin(SURVEY_PROGRAMS), "survey", "engineering"),
    )
    out = {}
    for c in ("survey", "focus", "engineering", "nonsurvey"):
        v = visits[cat == c] if c != "nonsurvey" else visits[cat != "survey"]
        out[c] = (
            merge_intervals(
                v["obs_start_mjd"].to_numpy(), v["obs_end_mjd"].to_numpy(), bridge_days
            )
            if len(v)
            else empty()
        )
    out["first_cat"] = (
        str(cat[np.argmin(visits["obs_start_mjd"].to_numpy())]) if len(visits) else ""
    )
    out["last_cat"] = (
        str(cat[np.argmax(visits["obs_end_mjd"].to_numpy())]) if len(visits) else ""
    )
    out["any"] = (
        merge_intervals(
            visits["obs_start_mjd"].to_numpy(),
            visits["obs_end_mjd"].to_numpy(),
            bridge_days,
        )
        if len(visits)
        else empty()
    )
    out["first_survey_start"] = (
        float(visits.loc[cat == "survey", "obs_start_mjd"].min())
        if (cat == "survey").any()
        else np.nan
    )
    out["exp_time_survey_h"] = (
        float(visits.loc[cat == "survey", "exp_time"].sum()) / 3600.0
    )
    out["n_survey"] = int((cat == "survey").sum())
    out["n_focus"] = int((cat == "focus").sum())
    out["n_engineering"] = int((cat == "engineering").sum())
    return out


@dataclass
class NightClassification:
    day_obs: int
    night: np.ndarray
    planned: np.ndarray
    weather: np.ndarray
    weather_bit: np.ndarray
    weather_fallback: np.ndarray  # fallback windows actually used (absent/masked)
    focus: np.ndarray  # Focus and Alignment (BLOCK-T539), own category
    engineering: np.ndarray  # B2, the other non-survey visits
    fault_idle: np.ndarray
    dynalene: np.ndarray  # subset of fault_idle
    idle_bit: np.ndarray  # subset of fault_idle
    survey: np.ndarray
    startup: np.ndarray
    unattributed: np.ndarray
    masked_fault: np.ndarray  # weather ∩ (FAULT ∪ DOWNTIME), shadow record
    weather_source: str
    extras: dict = field(default_factory=dict)

    def check_partition(self, tol_s: float = 0.5) -> None:
        parts = [
            self.planned,
            self.weather,
            self.focus,
            self.engineering,
            self.fault_idle,
            self.survey,
            self.startup,
            self.unattributed,
        ]
        tot = sum(hours(p) for p in parts)
        assert abs(tot - hours(self.night)) * 3600 < tol_s, (
            self.day_obs,
            tot,
            hours(self.night),
        )
        for i, a in enumerate(parts):
            for b in parts[i + 1 :]:
                assert hours(intersect(a, b)) * 3600 < tol_s, (self.day_obs, "overlap")


def classify_night(
    day_obs: int,
    t0: float,
    t1: float,
    visits: pd.DataFrame,
    bit_windows: np.ndarray,
    fallback: dict[str, np.ndarray],
    dynalene_windows: np.ndarray,
    states: dict[str, np.ndarray],
    gap_min: float = GAP_MIN_MINUTES,
) -> NightClassification:
    N = np.array([[t0, t1]])
    bridge = gap_min / 1440.0
    bit_era = int(day_obs) >= DAY_OBS_WEATHER_BIT_START
    # 1. B1 planned maintenance
    planned = empty()
    for lo, hi in PLANNED_MAINTENANCE:
        if lo <= day_obs <= hi:
            planned = N.copy()
    remainder = subtract(N, planned)
    # 2. C weather: bit, plus fallback where absent or masked
    bit = clip(bit_windows, t0, t1) if bit_era else empty()
    fb_any = clip(fallback["fallback"], t0, t1)
    if bit_era:
        masked = subtract(union(states["FAULT"], states["DOWNTIME"]), bit)
        fb_used = intersect(fb_any, masked)
        source = "WEATHER bit" + (" + fallback (masked)" if hours(fb_used) > 0 else "")
    else:
        fb_used = fb_any
        source = "fallback (allsky cloud + C1)"
    weather = intersect(union(bit, fb_used), remainder)
    remainder = subtract(remainder, weather)
    # 3. Focus and Alignment, 3b. B2 engineering. The non-survey visits bridged together at
    #    ≤ gap_min form the non-survey blocks; the Focus and Alignment blocks (BLOCK-T539,
    #    bridged within the programme) are their own category, the rest is engineering, so
    #    a bridged gap between a focus and an engineering visit is engineering.
    blocks = category_blocks(visits, bridge)
    nonsurvey_blocks = blocks["nonsurvey"]
    focus_blocks = blocks["focus"]
    onsky_any = blocks["any"]
    # Edge gaps ≤ gap_min are overhead like interior ones (README §3c step 5): extend the
    # first/last window to the night limit, in the category of the first/last visit.
    if len(onsky_any):
        if 0 < onsky_any[0, 0] - t0 <= bridge:
            onsky_any[0, 0] = t0
            if blocks["first_cat"] != "survey" and len(nonsurvey_blocks):
                nonsurvey_blocks[0, 0] = t0
            if blocks["first_cat"] == "focus" and len(focus_blocks):
                focus_blocks[0, 0] = t0
        if 0 < t1 - onsky_any[-1, 1] <= bridge:
            onsky_any[-1, 1] = t1
            if blocks["last_cat"] != "survey" and len(nonsurvey_blocks):
                nonsurvey_blocks[-1, 1] = t1
            if blocks["last_cat"] == "focus" and len(focus_blocks):
                focus_blocks[-1, 1] = t1
    nonsurvey_blocks = clip(nonsurvey_blocks, t0, t1)
    focus_blocks = clip(intersect(focus_blocks, nonsurvey_blocks), t0, t1)
    onsky_any = clip(onsky_any, t0, t1)
    focus = intersect(focus_blocks, remainder)
    remainder = subtract(remainder, focus)
    engineering = intersect(subtract(nonsurvey_blocks, focus_blocks), remainder)
    remainder = subtract(remainder, engineering)
    # 6a. A1/A2 survey on sky = all-visit union minus the non-survey blocks (a bridged gap
    #     between a survey and a non-survey visit goes to science overhead), after weather
    survey = intersect(subtract(onsky_any, nonsurvey_blocks), remainder)
    remainder = subtract(remainder, survey)
    # 6b. A3 start-up allowance: first 10 min after evening −12°, up to the first survey
    #     visit; only on nights that reached a survey visit (no start-up without a start)
    fs = blocks["first_survey_start"]
    startup = empty()
    if np.isfinite(fs):
        a3_end = min(t0 + STARTUP_ALLOWANCE_MIN / 1440.0, fs)
        if a3_end > t0:
            startup = intersect(np.array([[t0, a3_end]]), remainder)
    remainder = subtract(remainder, startup)
    # 7. F unattributed (bit era): UNKNOWN state where it would otherwise be fault + idle
    unattributed = intersect(states["UNKNOWN"], remainder) if bit_era else empty()
    remainder = subtract(remainder, unattributed)
    # 4+5. D + E fault + idle = what is left
    fault_idle = remainder
    dynalene = intersect(clip(dynalene_windows, t0, t1), fault_idle)
    idle_bit = intersect(states["IDLE"], fault_idle) if bit_era else empty()
    masked_fault = (
        intersect(weather, union(states["FAULT"], states["DOWNTIME"]))
        if bit_era
        else empty()
    )
    nc = NightClassification(
        day_obs=int(day_obs),
        night=N,
        planned=planned,
        weather=weather,
        weather_bit=bit,
        weather_fallback=fb_used,
        engineering=engineering,
        focus=focus,
        fault_idle=fault_idle,
        dynalene=dynalene,
        idle_bit=idle_bit,
        survey=survey,
        startup=startup,
        unattributed=unattributed,
        masked_fault=masked_fault,
        weather_source=source,
        extras=dict(
            onsky_any=onsky_any,
            weather_and_onsky_hours=hours(intersect(weather, onsky_any)),
            fallback_cloud_hours=hours(
                intersect(clip(fallback["cloud"], t0, t1), fb_used)
            ),
            fallback_c1_hours=hours(intersect(clip(fallback["c1"], t0, t1), fb_used)),
            fallback_any_hours=hours(fb_any),
            dynalene_total_hours=hours(clip(dynalene_windows, t0, t1)),
            dynalene_weather_hours=hours(
                intersect(clip(dynalene_windows, t0, t1), weather)
            ),
            n_visits=int(len(visits)),
            n_survey=blocks["n_survey"],
            n_focus=blocks["n_focus"],
            n_engineering=blocks["n_engineering"],
            exp_time_survey_h=blocks["exp_time_survey_h"],
            cloud_minutes_missing=fallback.get("cloud_minutes_missing", 0),
        ),
    )
    nc.check_partition()
    return nc


def label_night(row: pd.Series) -> str:
    """Presentation label (handoff §1b, adapted to the ROSP-24 categories): CLOSED if
    nothing was on sky (survey or engineering) for 0.5 h; OPEN if the lost time
    (weather + fault/idle + unattributed) is below 10 % of the night; otherwise
    WEATHER- or FAULT-DOMINATED by the larger of weather and fault/idle. Not a definition."""
    if row["on_sky_any_hours"] < 0.5:
        return "CLOSED"
    unattr = (
        row["unattributed_hours"] if np.isfinite(row["unattributed_hours"]) else 0.0
    )
    loss = row["weather_hours"] + row["nonweather_loss_hours"] + unattr
    if loss < 0.10 * row["night_hours"]:
        return "OPEN"
    return (
        "WEATHER-DOMINATED"
        if row["weather_hours"] >= row["nonweather_loss_hours"]
        else "FAULT-DOMINATED"
    )


def _fmt(w: np.ndarray) -> str:
    f = lambda m: pd.Timestamp((m - MJD_UNIX) * 86400, unit="s").strftime("%m-%d %H:%M")  # noqa: E731
    return "; ".join(f"{f(a)}–{f(b)}" for a, b in w)


def classify_all(
    limits: pd.DataFrame,
    visits: pd.DataFrame,
    bit_windows: dict[int, np.ndarray],
    fallback: dict[int, dict],
    dynalene_windows: dict[int, np.ndarray],
    periods: pd.DataFrame,
    gap_min: float = GAP_MIN_MINUTES,
) -> tuple[pd.DataFrame, dict[int, NightClassification]]:
    by_night = {d: g for d, g in visits.groupby("day_obs")}
    rows, res = [], {}
    for r in limits.itertuples(index=False):
        d = int(r.day_obs)
        t0, t1 = getattr(r, NIGHT_START_COL), getattr(r, NIGHT_END_COL)
        v = by_night.get(d, visits.iloc[0:0])
        nc = classify_night(
            d,
            t0,
            t1,
            v,
            bit_windows.get(d, empty()),
            fallback.get(d, {"fallback": empty(), "cloud": empty(), "c1": empty()}),
            dynalene_windows.get(d, empty()),
            state_windows(periods, d, t0, t1),
            gap_min,
        )
        res[d] = nc
        x = nc.extras
        rows.append(
            dict(
                day_obs=d,
                night_hours=round(hours(nc.night), 3),
                night_hours_18=round(float(r.night_hours_18), 3),
                night_hours_12=round(float(r.night_hours_12), 3),
                planned_maintenance_hours=round(hours(nc.planned), 3),
                weather_hours=round(hours(nc.weather), 3),
                weather_source=nc.weather_source,
                weather_windows_utc=_fmt(nc.weather),
                bit_weather_hours=round(hours(nc.weather_bit), 3)
                if d >= DAY_OBS_WEATHER_BIT_START
                else np.nan,
                fallback_weather_hours=round(hours(nc.weather_fallback), 3),
                fallback_cloud_hours=round(x["fallback_cloud_hours"], 3),
                fallback_c1_hours=round(x["fallback_c1_hours"], 3),
                fallback_any_hours=round(x["fallback_any_hours"], 3),
                engineering_hours=round(hours(nc.engineering), 3),
                focus_alignment_hours=round(hours(nc.focus), 3),
                nonweather_loss_hours=round(hours(nc.fault_idle), 3),
                dynalene_hours=round(hours(nc.dynalene), 3),
                dynalene_total_hours=round(x["dynalene_total_hours"], 3),
                dynalene_weather_hours=round(x["dynalene_weather_hours"], 3),
                idle_bit_hours=round(hours(nc.idle_bit), 3)
                if d >= DAY_OBS_WEATHER_BIT_START
                else np.nan,
                on_sky_hours=round(hours(nc.survey), 3),
                startup_hours=round(hours(nc.startup), 3),
                unattributed_hours=round(hours(nc.unattributed), 3)
                if d >= DAY_OBS_WEATHER_BIT_START
                else np.nan,
                on_sky_any_hours=round(hours(nc.extras["onsky_any"]), 3),
                weather_and_onsky_hours=round(x["weather_and_onsky_hours"], 3),
                weather_masked_fault_hours=round(hours(nc.masked_fault), 3)
                if d >= DAY_OBS_WEATHER_BIT_START
                else np.nan,
                exp_time_survey_hours=round(x["exp_time_survey_h"], 3),
                n_visits=x["n_visits"],
                n_survey_visits=x["n_survey"],
                n_focus_visits=x["n_focus"],
                n_engineering_visits=x["n_engineering"],
                cloud_minutes_missing=x["cloud_minutes_missing"],
                gap_min=gap_min,
            )
        )
    t = pd.DataFrame(rows)
    t["label"] = t.apply(label_night, axis=1)
    return t, res
