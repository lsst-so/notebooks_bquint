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
DAY_OBS_MAX = 20260714  # last night with the dome open before the winter storm

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
