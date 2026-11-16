"""Simonyi time-loss accounting (weather vs. non-weather), Oct 2025 - Jul 2026.

Modules
-------
access      clients for ConsDB (Postgres replica or RSP token), EFD (rubin_nights
            InfluxQueryClient) and the narrative log; token/credential discovery.
nights      -18 deg / -12 deg night limits per day_obs (ephemeris, no judgement);
            the accounting night is NIGHT_SUN_ALT (−12°, ROSP-22).

weather.py, visits.py and accounting.py (Section 1b of the handoff) are added
after Step 0 is reviewed.
"""

DAY_OBS_MIN = 20251025  # first night of Early Operations (handoff Section 1)
DAY_OBS_MAX = 20261031  # last complete night in the figure (was 20260714)

#: Last night on sky before the July 2026 storm, and the first night back on sky
#: after it. The first night back is ConsDB's answer (USDF, 2026-11-01): the first
#: day_obs after 2026-10-05 with on-sky visits (``airmass > 0``) is 20261027 —
#: 589 BLOCK-407 + 91 BLOCK-T698 science and 10 BLOCK-T539 acq. Nothing on sky
#: between 20260715 and 20261026 (20261026 has 1389 calibration frames only).
DAY_OBS_LAST_BEFORE_STORM = 20260714
DAY_OBS_BACK_ON_SKY = 20261027

#: The storm / downtime / recovery windows, as (first_day_obs, last_day_obs, kind,
#: label) with kind in {"weather", "planned"}. Bruno's decisions (handoff of
#: 2026-11-01); they **override** the observatory-state and narrative-log data,
#: which logged most of this period as DOWNTIME — including the storm and the loss
#: of site access. Boundaries are fixed: do not move them to fit the data, flag the
#: conflict instead.
#:
#: * 20260715–20260915 WEATHER — snowstorm and aftermath: off sky from 13/14 Jul,
#:   evacuation 15 Jul, power lost 19 Jul, road cut, no regular summit access.
#:   Worst storm in ~30 years (Christensen / Reil, #summit-announce, 2026-07-21).
#: * 20260916–20261005 DOWNTIME (planned maintenance) — official start per Kevin
#:   Reil, #summit-announce, 2026-09-16 ("Downtime officially started today; most
#:   work already underway"). End fixed by Bruno at 2026-10-05.
#: * 20261006–20261026 WEATHER — recovery and return to sky. Bruno's rule: all of
#:   it is weather (access lost to snow and road closures dominates). Ends the
#:   night before DAY_OBS_BACK_ON_SKY.
STORM_PERIODS: tuple[tuple[int, int, str, str], ...] = (
    (20260715, 20260915, "weather", "Storm (weather)"),
    (20260916, 20261005, "planned", "Planned maintenance"),
    (20261006, 20261026, "weather", "Recovery (weather)"),
)

#: Sun altitude (deg) defining the accounting night. ROSP-22 (Done 2026-10-19):
#: the observable night is −12° → −12°, from ``rubin_nights`` ``day_obs_sunset_sunrise``;
#: weather and downtime are not excluded from it. The −18° → −18° night is still
#: computed (``night_hours_18``) and reported as a secondary column in the README.
#: Was −18 until 2026-10-26.
NIGHT_SUN_ALT = -12
NIGHT_START_COL = f"sunset{-NIGHT_SUN_ALT}_mjd"
NIGHT_END_COL = f"sunrise{-NIGHT_SUN_ALT}_mjd"
NIGHT_HOURS_COL = f"night_hours_{-NIGHT_SUN_ALT}"

#: Gap between consecutive on-sky visits above which the gap counts as loss
#: (handoff §1b). Bruno, 2026-10-18: "lets use gap_min as 10 min for now".
#: Sensitivity is still reported at 2 / 5 / 10 min.
GAP_MIN_MINUTES = 10.0
GAP_MIN_SENSITIVITY = (2.0, 5.0, 10.0)

#: First day_obs with the Observatory Status WEATHER bit available. Before this
#: weather_hours comes from the EFD criteria in weather.py (Bruno, 2026-10-18,
#: pointing at handoff_dynalene_condensation_criteria_2025-12_2026-01.md).
DAY_OBS_WEATHER_BIT_START = 20260225
