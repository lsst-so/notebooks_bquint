"""Per-night table: night hours, weather hours, on-sky hours, non-weather loss.

Arithmetic (handoff §1b), all on the −18° → −18° night in UTC MJD:

    weather windows   W  = WEATHER-bit windows (from 2026-02-25) or EFD-criteria windows (before)
    on-sky windows    S  = visit coverage after bridging gaps ≤ gap_min
    night             N  = [sunset18, sunrise18]

    weather_hours         = |W ∩ N|
    on_sky_hours          = |S ∩ N|
    weather_and_onsky     = |W ∩ S|        (observing while the bit/criteria said closed; reported, not subtracted twice)
    nonweather_loss_hours = |N| − |W ∪ S|   (fault + idle, bundled; Bruno 2026-10-18)

Weather and non-weather never overlap: the loss is what is left after removing
both the weather windows and the on-sky windows from the night. The derived
``label`` follows the handoff's presentation rule and is not a definition.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from . import GAP_MIN_MINUTES

__all__ = ["union", "intersect_hours", "per_night_table", "label_night"]


def union(*wins: np.ndarray) -> np.ndarray:
    """Union of several (n, 2) interval arrays."""
    allw = [w for w in wins if len(w)]
    if not allw:
        return np.empty((0, 2))
    w = np.vstack(allw)
    w = w[np.argsort(w[:, 0])]
    out = [list(w[0])]
    for a, b in w[1:]:
        if a <= out[-1][1]:
            out[-1][1] = max(out[-1][1], b)
        else:
            out.append([a, b])
    return np.array(out)


def intersect_hours(a: np.ndarray, b: np.ndarray) -> float:
    if len(a) == 0 or len(b) == 0:
        return 0.0
    tot = 0.0
    for s1, e1 in a:
        lo = np.maximum(b[:, 0], s1)
        hi = np.minimum(b[:, 1], e1)
        tot += float(np.clip(hi - lo, 0, None).sum())
    return tot * 24


def hours(w: np.ndarray) -> float:
    return float((w[:, 1] - w[:, 0]).sum() * 24) if len(w) else 0.0


def label_night(row: pd.Series) -> str:
    """Presentation label (handoff §1b): CLOSED if on-sky < 0.5 h, else by dominant loss, else OPEN."""
    if row["on_sky_hours"] < 0.5:
        return "CLOSED"
    loss = row["weather_hours"] + row["nonweather_loss_hours"]
    if loss < 0.10 * row["night_hours_18"]:
        return "OPEN"
    return (
        "WEATHER-DOMINATED"
        if row["weather_hours"] >= row["nonweather_loss_hours"]
        else "FAULT-DOMINATED"
    )


def per_night_table(
    limits: pd.DataFrame,
    coverage: dict,
    weather_windows: dict[int, np.ndarray],
    weather_source: dict[int, str],
    gap_min: float = GAP_MIN_MINUTES,
) -> pd.DataFrame:
    """Build the deliverable table. ``coverage`` is the dict from ``visits.coverage_table``."""
    rows = []
    for r in limits.itertuples(index=False):
        d = int(r.day_obs)
        N = np.array([[r.sunset18_mjd, r.sunrise18_mjd]])
        c = coverage[d]
        S = c.on_sky_windows
        W = weather_windows.get(d, np.empty((0, 2)))
        night_h = hours(N)
        w_h = intersect_hours(W, N)
        s_h = intersect_hours(S, N)
        ws_h = intersect_hours(W, S)
        covered = intersect_hours(union(W, S), N)
        loss = max(night_h - covered, 0.0)
        rows.append(
            dict(
                day_obs=d,
                night_hours_18=round(night_h, 3),
                night_hours_12=round(float(r.night_hours_12), 3),
                weather_hours=round(w_h, 3),
                weather_source=weather_source.get(d, ""),
                weather_windows_utc="; ".join(_fmt(a, b) for a, b in W),
                on_sky_hours=round(s_h, 3),
                n_visits=c.n_visits,
                weather_and_onsky_hours=round(ws_h, 3),
                nonweather_loss_hours=round(loss, 3),
                gap_min=gap_min,
            )
        )
    t = pd.DataFrame(rows)
    t["label"] = t.apply(label_night, axis=1)
    return t


def _fmt(a: float, b: float) -> str:
    f = lambda m: pd.Timestamp((m - 40587.0) * 86400, unit="s").strftime("%m-%d %H:%M")  # noqa: E731
    return f"{f(a)}–{f(b)}"


# --------------------------------------------------------------------------- #
# Cloud reassignment before the WEATHER bit (Bruno, 2026-10-18: option 2)        #
# --------------------------------------------------------------------------- #

#: Source 2 P(weather) at or above this makes the night eligible for reassignment.
CLOUD_REASSIGN_P_WEATHER = 0.5


def reassign_unexplained_closures(
    table: pd.DataFrame,
    source2: pd.DataFrame,
    p_min: float = CLOUD_REASSIGN_P_WEATHER,
) -> pd.DataFrame:
    """Move ``closed_unexplained_hours`` into ``weather_hours`` where telemetry is blind.

    The EFD criteria cannot see cloud. Before the WEATHER bit exists
    (``weather_source == "EFD criteria"``) a night whose dome was shut, or whose
    telescope sat at horizon with the mirror covers on, while no criterion fired
    is reassigned to weather **only if** the night report (Source 2) gives
    P(weather) >= ``p_min``. The moved hours are capped by the night's
    ``nonweather_loss_hours`` (they come out of it), recorded in
    ``cloud_reassigned_hours`` and the night is flagged ``weather_source =
    "EFD criteria + night report (cloud)"``. Nothing changes from 2026-02-25 on.
    """
    s2 = source2.copy()
    s2["day_obs"] = s2["day_obs"].astype(str).str.replace("-", "").astype(int)
    s2["pw"] = pd.to_numeric(s2["p_weather"], errors="coerce")
    t = table.merge(s2[["day_obs", "pw"]], on="day_obs", how="left")
    eligible = (
        (t["weather_source"] == "EFD criteria")
        & (t["pw"] >= p_min)
        & (t["closed_unexplained_hours"] > 0)
    )
    moved = np.where(
        eligible,
        np.minimum(t["closed_unexplained_hours"].fillna(0), t["nonweather_loss_hours"]),
        0.0,
    )
    t["cloud_reassigned_hours"] = np.round(moved, 3)
    t["weather_hours"] = np.round(t["weather_hours"] + moved, 3)
    t["nonweather_loss_hours"] = np.round(t["nonweather_loss_hours"] - moved, 3)
    t.loc[eligible, "weather_source"] = "EFD criteria + night report (cloud)"
    t["label"] = t.apply(label_night, axis=1)
    return t.drop(columns="pw")
