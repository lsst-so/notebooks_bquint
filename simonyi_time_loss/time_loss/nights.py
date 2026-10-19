"""Night limits per ``day_obs`` from ephemeris. No judgement, no data.

Two definitions are carried side by side (handoff Section 1):

* ``night_hours_18`` -- sun altitude -18 deg (evening) to -18 deg (morning);
  the operational night used for the loss accounting.
* ``night_hours_12`` -- -12 deg to -12 deg; the window used by
  ``rubin_nights.dayobs_utils.estimated_baseline_visit_range`` (confirmed by
  reading its source: ``day_obs_sunset_sunrise(day_obs, sun_alt=-12)``).

Both come from ``rubin_nights.dayobs_utils.day_obs_sunset_sunrise``, which
uses ``astroplan.Observer`` at the Rubin site with ``which="next"`` from
12:00 TAI of the ``day_obs``. Times are returned in UTC.
"""

from __future__ import annotations

import pandas as pd
from astropy.time import TimeDelta

__all__ = ["day_obs_list", "night_limits"]


def day_obs_list(day_obs_min: int, day_obs_max: int) -> list[int]:
    """Every calendar ``day_obs`` from min to max inclusive."""
    import rubin_nights.dayobs_utils as rn

    t0 = rn.day_obs_to_time(int(day_obs_min))
    t1 = rn.day_obs_to_time(int(day_obs_max))
    n = int(round((t1 - t0).jd)) + 1
    return [
        rn.time_to_day_obs_int(t0 + TimeDelta(i + 0.5, format="jd")) for i in range(n)
    ]


def night_limits(day_obs_min: int, day_obs_max: int) -> pd.DataFrame:
    """One row per ``day_obs`` with the -18 and -12 deg limits (UTC) and hours."""
    import rubin_nights.dayobs_utils as rn

    rows = []
    for d in day_obs_list(day_obs_min, day_obs_max):
        s18, r18 = rn.day_obs_sunset_sunrise(d, sun_alt=-18)
        s12, r12 = rn.day_obs_sunset_sunrise(d, sun_alt=-12)
        rows.append(
            {
                "day_obs": d,
                "sunset18_utc": s18.utc.datetime,
                "sunrise18_utc": r18.utc.datetime,
                "night_hours_18": (r18 - s18).jd * 24,
                "sunset12_utc": s12.utc.datetime,
                "sunrise12_utc": r12.utc.datetime,
                "night_hours_12": (r12 - s12).jd * 24,
                "sunset18_mjd": s18.utc.mjd,
                "sunrise18_mjd": r18.utc.mjd,
                "sunset12_mjd": s12.utc.mjd,
                "sunrise12_mjd": r12.utc.mjd,
            }
        )
    return pd.DataFrame(rows)
