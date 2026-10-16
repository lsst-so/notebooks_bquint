"""Per-night and per-period aggregation of visits, expected visits and weather.

The period table is the single input of every figure version. Periods are either
calendar months or **fiscal quarters** (the fiscal year starts in October, so
FY26 Q1 is Oct-Dec 2025, Q2 Jan-Mar 2026, Q3 Apr-Jun 2026, Q4 Jul-Sep 2026).
Definitions:

x (survey speed)
    ``n_vis / n_vis_expected`` summed over all calendar nights of the period
    (closed nights count as zero visits in the "all nights" series and are
    dropped in the weather-excluded series). The x whisker is the 25-75 %
    range of the nightly ratios.
y (image quality)
    Median of the per-visit statistic over all visits of the period; the whisker
    is the 25-75 % range over visits. Default statistic ``idiq_aos_cam``.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from . import reference as ref

__all__ = [
    "IQ_COLUMNS",
    "PERIODS",
    "period_key",
    "period_seq",
    "period_label",
    "period_start_day_obs",
    "nightly_table",
    "period_table",
    "monthly_table",
    "quarterly_table",
    "window_table",
    "best_window",
]

#: Image-quality statistics available on the y axis, with axis labels.
IQ_COLUMNS = {
    "idiq_aos_cam": "Image quality added by the system, iDIQ (arcsec)",
    "fwhm_500_zenith": "Delivered FWHM corrected to 500 nm, zenith (arcsec)",
    "fwhm_geom": "Delivered FWHM, geometric (arcsec)",
}

#: Supported binning periods and the word used in labels.
PERIODS = {"month": "month", "quarter": "fiscal quarter", "window": "window"}

_FY_START_MONTH = 10  # October


# --------------------------------------------------------------------------- #
# Period keys                                                                  #
# --------------------------------------------------------------------------- #


def period_key(day_obs, period: str):
    """Integer key of the period containing ``day_obs`` (scalar or array).

    month   -> ``YYYYMM``
    quarter -> ``FY * 10 + Q`` with FY the fiscal year (Oct 2025 -> FY26 -> 261)
    """
    d = np.asarray(day_obs, dtype=int)
    year, month = d // 10000, (d // 100) % 100
    if period == "month":
        out = d // 100
    elif period == "quarter":
        fy = np.where(month >= _FY_START_MONTH, year + 1, year) % 100
        q = ((month - _FY_START_MONTH) % 12) // 3 + 1
        out = fy * 10 + q
    else:
        raise ValueError(f"period must be one of {list(PERIODS)}, got {period!r}")
    return int(out) if np.ndim(day_obs) == 0 else out


def period_seq(key, period: str):
    """Monotonic ordinal of a period key; consecutive periods differ by 1."""
    k = np.asarray(key, dtype=int)
    if period == "month":
        out = (k // 100) * 12 + (k % 100 - 1)
    else:
        out = (k // 10) * 4 + (k % 10 - 1)
    return int(out) if np.ndim(key) == 0 else out


def period_start_day_obs(key: int, period: str) -> int:
    """First calendar ``day_obs`` of a period."""
    key = int(key)
    if period == "month":
        return key * 100 + 1
    fy, q = key // 10, key % 10
    month = (_FY_START_MONTH - 1 + 3 * (q - 1)) % 12 + 1
    year = 2000 + fy - 1 if month >= _FY_START_MONTH else 2000 + fy
    return year * 10000 + month * 100 + 1


def period_end_day_obs(key: int, period: str) -> int:
    """Last calendar ``day_obs`` of a period."""
    start = pd.Timestamp(str(period_start_day_obs(key, period)))
    end = start + (
        pd.offsets.MonthEnd(1) if period == "month" else pd.offsets.MonthEnd(3)
    )
    return int(end.strftime("%Y%m%d"))


def period_label(key: int, period: str, short: bool = True) -> str:
    """``202510`` -> ``"Oct '25"``; ``261`` -> ``"FY26 Q1"`` or ``"FY26 Q1 (Oct-Dec 2025)"``."""
    key = int(key)
    if period == "month":
        ts = pd.Timestamp(str(period_start_day_obs(key, period)))
        return ts.strftime("%b '%y") if short else ts.strftime("%B %Y")
    fy, q = key // 10, key % 10
    label = f"FY{fy:02d} Q{q}"
    if short:
        return label
    t0 = pd.Timestamp(str(period_start_day_obs(key, period)))
    t1 = pd.Timestamp(str(period_end_day_obs(key, period)))
    span = (
        f"{t0:%b}–{t1:%b} {t1:%Y}" if t0.year == t1.year else f"{t0:%b %Y}–{t1:%b %Y}"
    )
    return f"{label} ({span})"


# Backwards-compatible alias used by earlier notebooks
def month_label(month: int, short: bool = True) -> str:
    return period_label(month, "month", short)


def _q(s: pd.Series, q: float) -> float:
    s = s.dropna()
    return float(s.quantile(q)) if len(s) else np.nan


# --------------------------------------------------------------------------- #
# Nightly                                                                      #
# --------------------------------------------------------------------------- #


def nightly_table(
    visits: pd.DataFrame,
    expected: pd.DataFrame,
    weather: pd.DataFrame,
    iq_cols: tuple[str, ...] = tuple(IQ_COLUMNS),
) -> pd.DataFrame:
    """One row per calendar night with counts, ratio, medians and weather flags."""
    g = visits.groupby("day_obs")
    agg = {"n_vis": g.size()}
    for c in iq_cols:
        if c in visits:
            agg[f"{c}_med"] = g[c].median()
            agg[f"{c}_q25"] = g[c].quantile(0.25)
            agg[f"{c}_q75"] = g[c].quantile(0.75)
            agg[f"{c}_n"] = g[c].count()
    per_night = pd.DataFrame(agg)

    out = expected.set_index("day_obs").join(per_night, how="left")
    out["n_vis"] = out["n_vis"].fillna(0).astype(int)
    out = out.join(weather.set_index("day_obs"), how="left")
    out["ratio"] = out["n_vis"] / out["n_vis_expected"]
    out["has_visits"] = out["n_vis"] > 0
    out["is_lsst"] = out.index >= ref.DAY_OBS_LSST_START
    out["date"] = pd.to_datetime(out.index.astype(str), format="%Y%m%d")
    out["is_weather_night"] = out["is_weather_night"].fillna(False).astype(bool)
    out["weather_known"] = out["weather_known"].fillna(False).astype(bool)
    out = out.reset_index()
    out["month"] = period_key(out["day_obs"], "month")
    out["quarter"] = period_key(out["day_obs"], "quarter")
    return out


# --------------------------------------------------------------------------- #
# Period                                                                       #
# --------------------------------------------------------------------------- #


def _aggregate(nights: pd.DataFrame, visits: pd.DataFrame, iq_cols) -> dict:
    n_vis = int(nights["n_vis"].sum())
    n_exp = float(nights["n_vis_expected"].sum())
    row = {
        "n_nights_calendar": int(len(nights)),
        "n_nights_with_visits": int(nights["has_visits"].sum()),
        "n_nights_weather": int(nights["is_weather_night"].sum()),
        "n_nights_weather_known": int(nights["weather_known"].sum()),
        "n_visits": n_vis,
        "n_vis_expected": n_exp,
        "ratio": n_vis / n_exp if n_exp else np.nan,
        "ratio_q25": _q(nights["ratio"], 0.25),
        "ratio_q75": _q(nights["ratio"], 0.75),
        "ratio_median_nightly": _q(nights["ratio"], 0.5),
        "first_day_obs": int(nights["day_obs"].min()),
        "last_day_obs": int(nights["day_obs"].max()),
        "last_day_obs_with_visits": int(
            nights.loc[nights["has_visits"], "day_obs"].max()
        )
        if nights["has_visits"].any()
        else -1,
    }
    for c in iq_cols:
        if c in visits:
            row[f"{c}_med"] = _q(visits[c], 0.5)
            row[f"{c}_q25"] = _q(visits[c], 0.25)
            row[f"{c}_q75"] = _q(visits[c], 0.75)
            row[f"{c}_n"] = int(visits[c].notna().sum())
    return row


def period_table(
    visits: pd.DataFrame,
    nightly: pd.DataFrame,
    period: str = "quarter",
    iq_cols: tuple[str, ...] = tuple(IQ_COLUMNS),
    min_nights: int = ref.MIN_NIGHTS_PER_MONTH,
) -> pd.DataFrame:
    """One row per period per series (``all`` and ``weather_excluded``).

    ``weather_excluded`` drops the nights flagged ``is_weather_night`` from both
    the numerator and the denominator of the visit ratio and from the IQ
    distribution. Periods with fewer than ``min_nights`` nights with visits get
    ``low_n=True``; they are kept. Periods without any visit are kept too, so
    that gaps (the storm) are explicit.
    """
    if period not in ("month", "quarter"):
        raise ValueError(f"period must be 'month' or 'quarter', got {period!r}")
    nightly = nightly.copy()
    nightly["period"] = period_key(nightly["day_obs"], period)
    rows = []
    for key, nights in nightly.groupby("period"):
        vis_p = visits[visits["day_obs"].isin(nights["day_obs"])]
        for series, sel in (
            ("all", np.ones(len(nights), dtype=bool)),
            ("weather_excluded", ~nights["is_weather_night"].to_numpy()),
        ):
            n_sel = nights[sel]
            v_sel = vis_p[vis_p["day_obs"].isin(n_sel["day_obs"])]
            row = {"period": int(key), "period_kind": period, "series": series}
            row.update(_aggregate(n_sel, v_sel, iq_cols))
            rows.append(row)
    out = pd.DataFrame(rows)
    out["seq"] = period_seq(out["period"], period)
    out["label"] = out["period"].map(lambda k: period_label(k, period))
    out["label_long"] = out["period"].map(
        lambda k: period_label(k, period, short=False)
    )
    # A period belongs to LSST only if it starts on or after the LSST start night.
    out["is_lsst"] = (
        out["period"].map(lambda k: period_start_day_obs(k, period))
        >= ref.DAY_OBS_LSST_START
    )
    out["low_n"] = out["n_nights_with_visits"] < min_nights
    out["weather_known"] = out["n_nights_weather_known"] > 0
    out["date"] = pd.to_datetime(
        out["period"].map(lambda k: str(period_start_day_obs(k, period))),
        format="%Y%m%d",
    )
    out = out.sort_values(["series", "period"]).reset_index(drop=True)
    out["t_index"] = out.groupby("series").cumcount()
    return out


def monthly_table(visits, nightly, **kw) -> pd.DataFrame:
    return period_table(visits, nightly, period="month", **kw)


def quarterly_table(visits, nightly, **kw) -> pd.DataFrame:
    return period_table(visits, nightly, period="quarter", **kw)


# --------------------------------------------------------------------------- #
# Arbitrary windows (e.g. "best two weeks of Early Ops" vs "first two weeks   #
# of LSST")                                                                    #
# --------------------------------------------------------------------------- #


def best_window(
    nightly: pd.DataFrame,
    day_obs_min: int,
    day_obs_max: int,
    n_nights: int = 14,
    by: str = "n_visits",
) -> pd.DataFrame:
    """Scan every ``n_nights``-night contiguous window inside a range.

    Returns one row per window start, sorted best first by ``by``
    (``"n_visits"`` or ``"ratio"``). Used to pick the "best two weeks".
    """
    sub = nightly[
        (nightly["day_obs"] >= day_obs_min) & (nightly["day_obs"] <= day_obs_max)
    ]
    sub = sub.sort_values("day_obs").reset_index(drop=True)
    rows = []
    for i in range(len(sub) - n_nights + 1):
        w = sub.iloc[i : i + n_nights]
        n_vis = int(w["n_vis"].sum())
        rows.append(
            {
                "start": int(w["day_obs"].iloc[0]),
                "end": int(w["day_obs"].iloc[-1]),
                "n_visits": n_vis,
                "n_vis_expected": float(w["n_vis_expected"].sum()),
                "ratio": n_vis / w["n_vis_expected"].sum(),
                "nights_with_visits": int(w["has_visits"].sum()),
                "idiq_median_of_nights": float(w["idiq_aos_cam_med"].median()),
            }
        )
    out = pd.DataFrame(rows)
    return out.sort_values(by, ascending=False).reset_index(drop=True)


def window_table(
    visits: pd.DataFrame,
    nightly: pd.DataFrame,
    windows: dict[str, tuple[int, int]],
    iq_cols: tuple[str, ...] = tuple(IQ_COLUMNS),
    min_nights: int = ref.MIN_NIGHTS_PER_MONTH,
) -> pd.DataFrame:
    """Same schema as :func:`period_table` for named ``day_obs`` windows.

    ``windows`` maps a short label to an inclusive ``(day_obs_min, day_obs_max)``
    pair, in time order. ``period`` is the window index, ``period_kind`` is
    ``"window"``.
    """
    rows = []
    for i, (label, (lo, hi)) in enumerate(windows.items()):
        nights = nightly[(nightly["day_obs"] >= lo) & (nightly["day_obs"] <= hi)]
        vis_w = visits[visits["day_obs"].isin(nights["day_obs"])]
        for series, sel in (
            ("all", np.ones(len(nights), dtype=bool)),
            ("weather_excluded", ~nights["is_weather_night"].to_numpy()),
        ):
            n_sel = nights[sel]
            v_sel = vis_w[vis_w["day_obs"].isin(n_sel["day_obs"])]
            row = {
                "period": i,
                "period_kind": "window",
                "series": series,
                "window_label": label,
            }
            row.update(_aggregate(n_sel, v_sel, iq_cols))
            row["first_day_obs"], row["last_day_obs"] = int(lo), int(hi)
            rows.append(row)
    out = pd.DataFrame(rows)
    out["seq"] = out["period"]
    t0 = pd.to_datetime(out["first_day_obs"].astype(str), format="%Y%m%d")
    t1 = pd.to_datetime(out["last_day_obs"].astype(str), format="%Y%m%d")
    span = [
        f"{a:%-d %b}–{b:%-d %b %Y}"
        if a.year == b.year
        else f"{a:%-d %b %Y}–{b:%-d %b %Y}"
        for a, b in zip(t0, t1)
    ]
    out["label"] = out["window_label"]
    out["label_long"] = [
        f"{lab} ({sp}, {n} nights)"
        for lab, sp, n in zip(out["window_label"], span, out["n_nights_calendar"])
    ]
    out["is_lsst"] = out["first_day_obs"] >= ref.DAY_OBS_LSST_START
    out["low_n"] = out["n_nights_with_visits"] < min_nights
    out["weather_known"] = out["n_nights_weather_known"] > 0
    out["date"] = t0
    out = out.sort_values(["series", "period"]).reset_index(drop=True)
    out["t_index"] = out.groupby("series").cumcount()
    return out
