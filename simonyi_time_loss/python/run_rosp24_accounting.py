"""Run the ROSP-24 ordered accounting end to end → ``data/processed/per_night.csv``.

Inputs (all cached; nothing is queried here):
  data/step0/night_limits.csv                      −12° / −18° limits (notebook 01)
  data/step0/visits_onsky_<range>.parquet          ConsDB visit1, airmass > 0 (notebook 03)
  data/step0/obs_state_periods.parquet             Scheduler observatoryStatus periods (notebook 00)
  data/cache/efd_weather_1min.parquet              python/pull_efd_weather_1min.py
  data/cache/allsky_cloud_1min.parquet             python/pull_allsky_cloud_1min.py
  data/step0/nightlog_source2_per_night.csv        night-report table (annotation only)
  data/processed/per_night_20261026_pre_rosp24.csv the 26 Oct table, for report_cloud_hours

Outputs: per_night.csv / .parquet, per_month.csv, data/cache/classification.pkl (interval
sets per night, read by the figure scripts), data/step0/fallback_windows_per_night.csv.
"""

from __future__ import annotations

import pickle
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from time_loss import (
    DAY_OBS_MAX,
    DAY_OBS_MIN,
    DAY_OBS_WEATHER_BIT_START,
    GAP_MIN_MINUTES,
    NIGHT_END_COL,
    NIGHT_START_COL,
)  # noqa: E402
from time_loss import classify as C  # noqa: E402
from time_loss import fallback as FB  # noqa: E402
from time_loss import weather as W  # noqa: E402
from time_loss.intervals import clip, hours  # noqa: E402

ROOT = HERE.parent
STEP0, CACHE, PROC = (
    ROOT / "data" / "step0",
    ROOT / "data" / "cache",
    ROOT / "data" / "processed",
)


def dynalene_windows(
    efd_night: pd.DataFrame, day_obs: int, t0: float, t1: float
) -> np.ndarray:
    """Dynalene-condensation CLOSE windows (weather.py rule by validity window), 10-min merge."""
    f = W.flag_minutes(efd_night, day_obs)
    return clip(
        W.runs_to_windows(f["dynalene"], merge_min=int(GAP_MIN_MINUTES)), t0, t1
    )


def main() -> None:
    limits = pd.read_csv(STEP0 / "night_limits.csv")
    limits = limits[
        (limits.day_obs >= DAY_OBS_MIN) & (limits.day_obs <= DAY_OBS_MAX)
    ].reset_index(drop=True)
    visits = pd.read_parquet(
        STEP0 / f"visits_onsky_{DAY_OBS_MIN}_{DAY_OBS_MAX}.parquet"
    )
    periods = pd.read_parquet(STEP0 / "obs_state_periods.parquet")
    efd = pd.read_parquet(CACHE / "efd_weather_1min.parquet")
    cloud = pd.read_parquet(CACHE / "allsky_cloud_1min.parquet")
    efd_by = {d: g.drop(columns="day_obs") for d, g in efd.groupby("day_obs")}
    cloud_by = {d: g.drop(columns="day_obs") for d, g in cloud.groupby("day_obs")}
    _, bit_res = W.weather_bit_table(periods, limits)
    fb, dyn, fb_rows = {}, {}, []
    for r in limits.itertuples(index=False):
        d = int(r.day_obs)
        t0, t1 = getattr(r, NIGHT_START_COL), getattr(r, NIGHT_END_COL)
        e = efd_by.get(d)
        if e is None:
            fb[d] = {
                "fallback": np.empty((0, 2)),
                "cloud": np.empty((0, 2)),
                "c1": np.empty((0, 2)),
                "cloud_minutes_missing": int(round((t1 - t0) * 1440)),
            }
            dyn[d] = np.empty((0, 2))
        else:
            fb[d] = FB.fallback_windows_night(e, cloud_by.get(d), t0, t1)
            dyn[d] = dynalene_windows(e, d, t0, t1)
        fb_rows.append(
            dict(
                day_obs=d,
                fallback_hours=round(hours(fb[d]["fallback"]), 3),
                cloud_hours=round(hours(fb[d]["cloud"]), 3),
                c1_hours=round(hours(fb[d]["c1"]), 3),
                c1_rh_hours=round(hours(fb[d].get("c1_rh", np.empty((0, 2)))), 3),
                c1_dpd_hours=round(hours(fb[d].get("c1_dpd", np.empty((0, 2)))), 3),
                c1_wind_hours=round(hours(fb[d].get("c1_wind", np.empty((0, 2)))), 3),
                dynalene_rule_hours=round(hours(dyn[d]), 3),
                cloud_minutes_missing=fb[d]["cloud_minutes_missing"],
            )
        )
    pd.DataFrame(fb_rows).to_csv(STEP0 / "fallback_windows_per_night.csv", index=False)
    t, res = C.classify_all(limits, visits, bit_res, fb, dyn, periods)
    # annotation-only columns
    old = pd.read_csv(PROC / "per_night_20261026_pre_rosp24.csv")
    t = t.merge(
        old[["day_obs", "cloud_reassigned_hours", "closed_unexplained_hours"]].rename(
            columns={"cloud_reassigned_hours": "report_cloud_hours"}
        ),
        on="day_obs",
        how="left",
    )
    s2 = pd.read_csv(STEP0 / "nightlog_source2_per_night.csv")
    s2["day_obs"] = s2.day_obs.astype(str).str.replace("-", "").astype(int)
    t = t.merge(
        s2[["day_obs", "p_weather", "p_fault"]].rename(
            columns={"p_weather": "report_p_weather", "p_fault": "report_p_fault"}
        ),
        on="day_obs",
        how="left",
    )
    t.to_csv(PROC / "per_night.csv", index=False)
    t.to_parquet(PROC / "per_night.parquet")
    with open(CACHE / "classification.pkl", "wb") as fh:
        pickle.dump(res, fh)
    cols = [
        "night_hours",
        "on_sky_hours",
        "focus_alignment_hours",
        "engineering_hours",
        "weather_hours",
        "nonweather_loss_hours",
        "startup_hours",
        "unattributed_hours",
        "planned_maintenance_hours",
    ]
    t["month"] = t.day_obs // 100
    m = (
        t.groupby("month")[cols + ["night_hours_18", "dynalene_hours"]]
        .sum()
        .round(2)
    )
    for c in (
        "on_sky",
        "focus_alignment",
        "engineering",
        "weather",
        "nonweather_loss",
        "startup",
        "unattributed",
    ):
        m[f"{c}_frac"] = (m[f"{c}_hours"] / m.night_hours).round(3)
    m.to_csv(PROC / "per_month.csv")
    tot = t[cols].sum()
    print("totals (h):", tot.round(1).to_dict())
    print(
        "shares:",
        {k: f"{v / tot.night_hours:.1%}" for k, v in tot.items() if k != "night_hours"},
    )
    print(
        "check sum = night:",
        round(float(tot.drop("night_hours").sum() - tot.night_hours), 3),
    )
    print("labels:", t.label.value_counts().to_dict())
    print(
        "weather by source:",
        t.groupby("weather_source")
        .weather_hours.agg(["sum", "count"])
        .round(1)
        .to_dict(),
    )
    print(
        "bit era masked fallback h:",
        round(
            t[t.day_obs >= DAY_OBS_WEATHER_BIT_START].fallback_weather_hours.sum(), 1
        ),
        "| pre-bit fallback h:",
        round(t[t.day_obs < DAY_OBS_WEATHER_BIT_START].fallback_weather_hours.sum(), 1),
        "(cloud",
        round(t.fallback_cloud_hours.sum(), 1),
        "C1",
        round(t.fallback_c1_hours.sum(), 1),
        ")",
    )
    print(
        "dynalene: total rule h",
        round(t.dynalene_total_hours.sum(), 1),
        "| in fault+idle",
        round(t.dynalene_hours.sum(), 1),
        "| in weather",
        round(t.dynalene_weather_hours.sum(), 1),
    )
    print(
        "focus h",
        round(t.focus_alignment_hours.sum(), 1),
        "| startup h",
        round(t.startup_hours.sum(), 1),
        "| idle bit h",
        round(t.idle_bit_hours.sum(), 1),
        "| unattributed h",
        round(t.unattributed_hours.sum(), 1),
        "| masked fault (shadow) h",
        round(t.weather_masked_fault_hours.sum(), 1),
        "| weather∩onsky",
        round(t.weather_and_onsky_hours.sum(), 1),
    )
    print(m[[c for c in m.columns if c.endswith("_frac")]].to_string())


if __name__ == "__main__":
    main()
