"""How much does the gap_min bridging threshold matter, and how many gaps are ambiguous?

Reads the same caches as ``run_rosp24_accounting.py`` (nothing is queried). Writes
  data/processed/visit_gaps.parquet          one row per gap between consecutive visits (−12° night)
  data/processed/gap_min_sensitivity.csv     season totals for gap_min = 2 … 30 min
and prints a summary: gap histogram, hours per bin, totals per gap_min, and what the
observatory was doing during the near-threshold gaps (state, shutter, telescope).
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from time_loss import (  # noqa: E402
    DAY_OBS_MAX,
    DAY_OBS_MIN,
    DAY_OBS_WEATHER_BIT_START,
    GAP_MIN_MINUTES,
    NIGHT_END_COL,
    NIGHT_START_COL,
)
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
GAP_MINS = (2.0, 5.0, 7.5, 10.0, 15.0, 20.0, 30.0)
BINS = [0, 2, 5, 7.5, 10, 15, 20, 30, 60, 120, 1e9]
LABELS = [
    "0–2",
    "2–5",
    "5–7.5",
    "7.5–10",
    "10–15",
    "15–20",
    "20–30",
    "30–60",
    "60–120",
    ">120",
]


def load():
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
    fb, dyn = {}, {}
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
            f = W.flag_minutes(e, d)
            dyn[d] = clip(
                W.runs_to_windows(f["dynalene"], merge_min=int(GAP_MIN_MINUTES)), t0, t1
            )
    return limits, visits, periods, efd, bit_res, fb, dyn


def gap_table(limits, visits, periods, efd, bit_res, fb) -> pd.DataFrame:
    """One row per gap between consecutive visits inside the −12° night."""
    prog = visits["science_program"].astype("string")
    cat = np.where(
        prog.isin(C.FOCUS_PROGRAMS),
        "focus",
        np.where(prog.isin(C.SURVEY_PROGRAMS), "survey", "engineering"),
    )
    visits = visits.assign(cat=cat).sort_values("obs_start_mjd")
    efd_by = {d: g for d, g in efd.groupby("day_obs")}
    rows = []
    for r in limits.itertuples(index=False):
        d = int(r.day_obs)
        t0, t1 = getattr(r, NIGHT_START_COL), getattr(r, NIGHT_END_COL)
        v = visits[visits.day_obs == d]
        if len(v) < 2:
            continue
        s, e = v.obs_start_mjd.to_numpy(), v.obs_end_mjd.to_numpy()
        c = v.cat.to_numpy()
        gs, ge = e[:-1], s[1:]
        keep = (ge > gs) & (ge > t0) & (gs < t1)
        bit_era = d >= DAY_OBS_WEATHER_BIT_START
        bit = (
            clip(bit_res.get(d, np.empty((0, 2))), t0, t1)
            if bit_era
            else np.empty((0, 2))
        )
        fbw = clip(fb[d]["fallback"], t0, t1)
        st = C.state_windows(periods, d, t0, t1)
        en = efd_by.get(d)
        for a, b, ca, cb in zip(gs[keep], ge[keep], c[:-1][keep], c[1:][keep]):
            a2, b2 = max(a, t0), min(b, t1)
            seg = np.array([[a2, b2]])

            def frac(w):
                return hours(C.intersect(seg, w)) / hours(seg) if len(w) else 0.0

            row = dict(
                day_obs=d,
                start_mjd=a2,
                end_mjd=b2,
                gap_min=(b2 - a2) * 1440,
                cat_before=ca,
                cat_after=cb,
                bit_era=bit_era,
                weather_frac=frac(
                    np.vstack([bit, fbw]) if len(bit) + len(fbw) else np.empty((0, 2))
                ),
                fault_frac=frac(st["FAULT"]),
                downtime_frac=frac(st["DOWNTIME"]),
                idle_frac=frac(st["IDLE"]),
                operational_frac=frac(st["OPERATIONAL"]),
            )
            if en is not None:
                ta = pd.Timestamp("1858-11-17") + pd.to_timedelta(a2, unit="D")
                tb = pd.Timestamp("1858-11-17") + pd.to_timedelta(b2, unit="D")
                w = en.loc[ta:tb]
                row.update(
                    shutter_mean=w.shutter.mean(),
                    el_mean=w.el.mean(),
                    mcover_mean=w.mcover.mean(),
                    n_min=len(w),
                )
            rows.append(row)
    g = pd.DataFrame(rows)
    g["bin"] = pd.cut(g.gap_min, BINS, labels=LABELS, right=True)
    return g


def main():
    limits, visits, periods, efd, bit_res, fb, dyn = load()
    g = gap_table(limits, visits, periods, efd, bit_res, fb)
    g.to_parquet(PROC / "visit_gaps.parquet", index=False)
    night_h = hours(np.column_stack([limits[NIGHT_START_COL], limits[NIGHT_END_COL]]))
    print(
        f"\n{len(g)} inter-visit gaps on {g.day_obs.nunique()} nights, {night_h:.0f} h of −12° night"
    )
    h = g.groupby("bin", observed=False).agg(
        n=("gap_min", "size"), hours=("gap_min", lambda s: s.sum() / 60)
    )
    h["cum_hours_if_bridged"] = h.hours.cumsum()
    print("\nGap histogram (hours = total time inside gaps of that length):")
    print(h.round(1).to_string())

    # --- sensitivity of the season totals
    rows = []
    for gm in GAP_MINS:
        t, _ = C.classify_all(limits, visits, bit_res, fb, dyn, periods, gap_min=gm)
        tot = t[
            [
                "on_sky_hours",
                "startup_hours",
                "engineering_hours",
                "weather_hours",
                "nonweather_loss_hours",
                "unattributed_hours",
            ]
        ].sum()
        rows.append(
            dict(
                gap_min=gm,
                survey_h=tot.on_sky_hours + tot.startup_hours,
                engineering_h=tot.engineering_hours,
                weather_h=tot.weather_hours,
                fault_idle_h=tot.nonweather_loss_hours + tot.unattributed_hours,
                **{f"n_{k}": v for k, v in t.label.value_counts().items()},
            )
        )
    s = pd.DataFrame(rows).set_index("gap_min")
    for c in ("survey", "engineering", "weather", "fault_idle"):
        s[f"{c}_pct"] = 100 * s[f"{c}_h"] / night_h
    s.to_csv(PROC / "gap_min_sensitivity.csv")
    print("\nSeason totals vs gap_min (h and % of night):")
    print(s.round(1).to_string())

    # --- the ambiguous gaps: 5–20 min (±factor 2 around the 10-min rule)
    amb = g[(g.gap_min > 5) & (g.gap_min <= 20)]
    print(
        f"\nAmbiguous gaps 5–20 min: {len(amb)} gaps, {amb.gap_min.sum() / 60:.1f} h, "
        f"on {amb.day_obs.nunique()} nights (median {amb.groupby('day_obs').size().median():.0f} per night)"
    )
    just_over = g[(g.gap_min > 10) & (g.gap_min <= 20)]
    print(
        f"  just over the rule (10–20 min, now counted as loss): {len(just_over)} gaps, "
        f"{just_over.gap_min.sum() / 60:.1f} h"
    )
    print(
        "  what the observatory was doing in them (bit era only, fraction of gap time):"
    )
    jo = just_over[just_over.bit_era]
    print(
        "   ",
        {
            k: round(jo[k].mul(jo.gap_min).sum() / jo.gap_min.sum(), 2)
            for k in (
                "operational_frac",
                "fault_frac",
                "downtime_frac",
                "idle_frac",
                "weather_frac",
            )
        },
    )
    print(
        f"    shutter fully open (mean > 95): {(jo.shutter_mean > 95).mean():.0%} of gaps; "
        f"telescope above 20°: {(jo.el_mean > 20).mean():.0%}"
    )
    print(
        "  categories around them:",
        just_over.groupby(["cat_before", "cat_after"])
        .size()
        .sort_values(ascending=False)
        .head(6)
        .to_dict(),
    )
    just_under = g[(g.gap_min > 5) & (g.gap_min <= 10)]
    ju = just_under[just_under.bit_era]
    print(
        f"  just under the rule (5–10 min, now bridged as overhead): {len(just_under)} gaps, "
        f"{just_under.gap_min.sum() / 60:.1f} h"
    )
    print(
        "   ",
        {
            k: round(ju[k].mul(ju.gap_min).sum() / ju.gap_min.sum(), 2)
            for k in (
                "operational_frac",
                "fault_frac",
                "downtime_frac",
                "idle_frac",
                "weather_frac",
            )
        },
    )
    print(
        f"    shutter fully open: {(ju.shutter_mean > 95).mean():.0%}; telescope above 20°: {(ju.el_mean > 20).mean():.0%}"
    )


if __name__ == "__main__":
    main()
