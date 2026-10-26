# night_efficiency_brackets

One Simonyi night laid on its side, with the denominators of the usual efficiency numbers drawn
as brackets above it. Built for the LSST@LATAM 2026 talk (figure B11, replaces the schematic
efficiency waterfall in `efficiency_waterfall/`). Rule for the deck: the definitions are drawn
inside the plot, not written in a table.

**Status:** done (2026-10-26); bracket labels and night choice confirmed by the deck side the same
day; re-drawn the same day on the **−12° → −12° observable night** (ROSP-22, Done 2026-10-19:
`rubin_nights` `day_obs_sunset_sunrise`, weather and downtime not excluded). The −18° values the
first version used are kept below as a secondary column. Ticket: none (talk material).

## Contents

- `python/make_night_brackets_figure.py` — gap/bracket arithmetic and the figure; prints every
  number below when run.
- `data/visits_20260708.csv` — ConsDB `cdb_lsstcam.visit1` rows of the night (airmass > 0,
  `img_type` in acq/science/cwfs/focus), copied from `engineering_time_budget/data/visit1_*.parquet`
  (itself a copy of the `nightly_survey_speed` cache).
- `data/night_limits_20260708.csv` — −12° and −18° twilights (rubin_nights ephemeris), copied
  from `simonyi_time_loss/data/step0/night_limits.csv`.
- `data/observatory_state_20260708.csv` — Scheduler `observatoryStatus` periods (WEATHER bit
  among them), copied from `simonyi_time_loss/data/step0/obs_state_periods.parquet`.
- `figures/night_brackets_20260708.png` (transparent), `_white.png` — 16:5.

## Chosen night: 2026-07-08 (day_obs 20260708)

Selection rule (handoff 2026-10-26): a 2026 night after 2026-02-25 (WEATHER-bit era) with
≥ 1 h weather closure, ≥ 1 h of fault/idle in a solid block, ≥ 150 survey visits, and few gaps.
Among the 140 nights with the WEATHER bit, **8 Jul 2026 is the only night with ≥ 0.9 h of weather,
a fault/idle block longer than 1 h and ≥ 150 survey visits.** Its loss blocks sit at the start
of the night, which makes the brackets read as nested segments. The WEATHER bit was set for
1.09 h from 23:15 UTC; the whole window lies inside the −12° night (22:53 → 10:44 UTC), so the
weather block is 1.1 h (on the −18° night it was 0.98 h, 6 min of the bit falling before −18°).
The story of the night is in the night report: camera
recovered after the 7 Jul REB power-supply trip (FRACAS-404) and ready at 02:20 UTC, FBS from
03:15 UTC, HV bias trip 03:30–03:50 UTC (OBS-2010), observations done 10:40 UTC; "mostly cloudy
... became worse by 23 UTC when we decided to close ... around 23 UTC clouds cleared".

Runners-up, and why not:

| day_obs | weather (h) | fault + idle (h) | survey visits | why not |
|---|---|---|---|---|
| 20260427 | 2.20 | 2.92 | 341 | fault/idle is scattered over 10 gaps (MTMount/MTPtg faults, OBS-985); largest block 0.76 h |
| 20260319 | 1.99 | 4.01 | 0 | engineering night (BLOCK-T706, 300 visits), no survey visits |
| 20260118 | 3.17 | 1.66 | 277 | before the WEATHER bit; weather from the EFD criteria (3 windows) |

(hours on the −12° night; on the −18° night: 1.73 / 2.92, 1.99 / 3.54, 2.61 / 1.09)

No other post-2026-02-25 night has both ≥ 0.9 h weather and ≥ 1 h fault/idle with ≥ 150 survey
visits.

## Numbers on the figure

All computed by the script from the three data files; definitions are those of
`simonyi_time_loss` (−12° night, gap_min = 10 min) and `engineering_time_budget` (categories).
The figure shows the −12° column; the −18° column is what the first version (same day) showed.

| Quantity | −12° → −12° (on the figure) | −18° → −18° (reference) |
|---|---|---|
| night | 2026-07-08 22:52:47 → 2026-07-09 10:43:31 UTC, **11.846 h** | 23:21:55 → 10:14:24 UTC, 10.875 h |
| WEATHER bit window | 23:15:36 → 00:20:50 UTC (1.087 h), all inside the night | 0.982 h inside the night |
| **Observable night** bracket | **11.8 h** | 10.9 h ("Whole night (OSF)" then) |
| **Survey time only** bracket (night − weather) | **10.8 h** (10.758) | 9.9 h (9.893) |
| **Excluding faults (= on sky)** bracket (night − weather − fault/idle) | **7.3 h** (7.334), two segments: 03:07:00–03:36:21 and 03:52:49–10:43:31 | 6.8 h (6.849) |
| **Exposing + readout** bracket | **4.9 h** (4.895), sum of the 569 visit intervals, all inside the night | 4.5 h (4.538), 528 visits |
| weather | **1.1 h** (1.087) | 0.98 h |
| fault + idle | **3.4 h** (3.424): 0.4 h camera down before the weather closure + 2.8 h camera recovery + 0.3 h HV bias trip | 3.04 h: 2.77 + 0.27 |
| visit-scale overhead (bracket 3 − bracket 4) | 2.4 h (2.439) | 2.3 h (2.311) |

Ratios for slide text (not on the figure), −12° night: 4.9 h exposing + readout ÷ brackets 1 / 2 / 3 =
41 % / 46 % / 67 %; with the 7.3 h on-sky bracket as numerator = 62 % / 68 % / 100 %.

Visits: 569 on-sky visits, 559 Survey Programs (all BLOCK-407; bands i 256, r 211, z 99, u 3, not shown), 10 Focus
and Alignment (BLOCK-T539, 03:07–03:14 UTC), 0 Engineering. All 569 lie inside the −12° night; the last
visit ends 10:41:04 UTC, 2.4 min before the morning −12° limit, so that edge gap is bridged (on the −18°
night 41 of them fell after the 10:14 morning limit and were drawn lighter). All visits are 30 s
exposures (31 s start-to-end).

Gaps longer than 10 min inside the −12° night (start, end, length, bin, attribution):

| start (UTC) | end (UTC) | length | bin | attribution |
|---|---|---|---|---|
| 2026-07-08 22:52:47 (−12°) | 2026-07-08 23:15:36 | 0.38 h | fault + idle | camera still down after the REB power-supply trip of 7 Jul, FRACAS-404; observatory state IDLE, DOWNTIME bit set; the WEATHER bit is not yet set |
| 2026-07-08 23:15:36 | 2026-07-09 00:20:50 | 1.09 h | weather | WEATHER bit set 23:15–00:20 (clouds; night report) |
| 2026-07-09 00:20:50 | 2026-07-09 03:07:00 | 2.77 h | fault + idle | camera recovery after the REB power-supply trip, FRACAS-404 (`downtime_annotations.csv`); observatory state IDLE 00:20–03:02, DOWNTIME bit set until 03:02 |
| 2026-07-09 03:36:21 | 2026-07-09 03:52:49 | 0.27 h | fault + idle | camera HV bias tripped 03:30, recovered 03:50 UTC, OBS-2010 (night report); state IDLE 03:36–03:52 |

The first three rows are one 4.24 h gap in the visit record (22:53 → 03:07), split by the WEATHER-bit
window: weather takes precedence inside a gap, the remainder is fault + idle. The 21 gaps between 60 s
and 10 min (2–4 min each, slews/filter changes, 0.9 h in total) and the 546 gaps ≤ 60 s (median 9 s)
are the white slivers in the strip and are not coloured.

## Definitions, and the bracket-4 decision

- **Categories** as in B10 / the on-sky utilization timeline: Survey Programs =
  BLOCK-407/408/416/417/419/421, Focus and Alignment = BLOCK-T539, Engineering = every other
  on-sky visit.
- **Loss blocks**: every stretch of the −12° night not covered by a visit and longer than 10 min
  (the two edge gaps included). The part of a block inside a WEATHER-bit window is weather, the
  remainder is fault + idle, exactly the `simonyi_time_loss` accounting; the per-night row there
  gives weather 1.087 h, non-weather loss 3.465 h, on sky 7.294 h for this night. The script
  reproduces weather exactly and gives 3.424 / 7.334 h for the other two: the 2.4 min between the
  last visit and the morning limit is bridged here (gap ≤ 10 min, so not a loss block) but counted
  as loss there, where `on_sky_hours` is the visit union clipped to the night and any edge gap,
  however short, is left over. (On the −18° night both gave 0.982 / 3.044 / 6.849 h.)
- **Weather colour.** The weather block is drawn in the palette's neutral grey (`NEUTRALS["muted"]`,
  30 % tint, hatched, label in secondary ink), not in a categorical slot: Survey Programs already
  owns the teal, and the other free slots fail the palette check against orange/purple (red and
  olive are too close to the Engineering orange for normal vision; green is the B1/B3 "on sky"
  colour). Grey also reads as "sky shut", which is what the block is.
- **Brackets 1–3** are the observable night (−12° → −12°, labelled "Observable night"), the night
  minus weather, and the night minus weather and fault/idle blocks. Bracket 3 equals B3's bridged
  `on_sky_hours` (7.3 h), the definition behind the 53 % on-sky figure of B1/B3, and is labelled
  "Excluding faults (= on sky)" (no figure codes on the image; the B1/B3 link lives here).
- **Bracket 4, "Exposing + readout".** The 2026-10-26 handoff first asked for "union of the visit
  blocks (what B1/B3 call on sky)"; with 10-min bridging that union *is* bracket 3, so the fourth
  bracket would be invisible. Decision (deck side, 2026-10-26): draw the **sum of the visit
  intervals** (obs_start → obs_end, 4.9 h), packed against the end of the last visit and dotted to
  say "packed, not a time span", and never call it "on sky". The 2.4 h gap to bracket 3 is the
  visit-scale overhead (slew, settle, filter change) that the next slide is about. Shutter-open
  only (sum of `exp_time`, ≈ 4.7 h) would be the OSF numerator; deferred until Lynne Jones's
  waterfall arrives.
- Thin −18° ticks are drawn inside the −12° limits (29 min after the evening one, 29 min before the
  morning one) so the astronomical-twilight night (10.9 h) can be compared with the 11.8 h bracket
  without a caveat.

## Run

```bash
python night_efficiency_brackets/python/make_night_brackets_figure.py
```

Needs pandas, matplotlib and the repo palette (`../rubin_color_pallete`, copy the module into this
folder before extracting the investigation). To redo the figure for another night, change `DAY_OBS`
(and `NIGHT_SUN_ALT` to switch back to −18°) and re-extract the three data files from the `simonyi_time_loss` and `engineering_time_budget`
caches (see the file list above); `GAP_LABELS` holds the ticket text per gap start.
