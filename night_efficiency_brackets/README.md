# night_efficiency_brackets

One Simonyi night laid on its side, with the denominators of the usual efficiency numbers drawn
as brackets above it. Built for the LSST@LATAM 2026 talk (figure B11, replaces the schematic
efficiency waterfall in `efficiency_waterfall/`). Rule for the deck: the definitions are drawn
inside the plot, not written in a table.

**Status:** done (2026-10-26); bracket labels and night choice confirmed by the deck side the same
day; re-drawn the same day on the **−12° → −12° observable night** (ROSP-22, Done 2026-10-19:
`rubin_nights` `day_obs_sunset_sunrise`, weather and downtime not excluded); re-drawn again the same
evening under the **ROSP-24 loss-cause precedence** (draft, "Verifying"; comments of 2026-10-19 and
2026-10-26 read 2026-10-26): weather → engineering → fault + idle → survey, with the allskycam cloud
index as weather evidence where the WEATHER bit is masked, Focus and Alignment as engineering, the
10-min start-up allowance, and a shutter-open-only fourth bracket. The 26 Oct morning (ROSP-22 only)
and −18° values are kept below as secondary columns. Ticket: none (talk material).

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
- `data/rosp24_intervals_20260708.csv` — the ROSP-24 classification of the night (weather, its bit and
  fallback parts, engineering, fault + idle, survey, start-up allowance interval sets, UTC MJD and UTC),
  exported from `simonyi_time_loss/data/cache/classification.pkl` (`time_loss/classify.py`). Since the
  ROSP-24 re-run the script reads the blocks and brackets from this file instead of recomputing them.
- `data/allsky_cloud_1min_20260708.csv` — allskycam cloud index of the night on the 1-min grid (Brian
  Stalder's product, via `simonyi_time_loss/python/pull_allsky_cloud_1min.py`).
- `figures/night_brackets_20260708.png` (transparent), `_white.png` — 16:5.

## Chosen night: 2026-07-08 (day_obs 20260708)

Selection rule (handoff 2026-10-26): a 2026 night after 2026-02-25 (WEATHER-bit era) with
≥ 1 h weather closure, ≥ 1 h of fault/idle in a solid block, ≥ 150 survey visits, and few gaps.
Among the 140 nights with the WEATHER bit, **8 Jul 2026 is the only night with ≥ 0.9 h of weather,
a fault/idle block longer than 1 h and ≥ 150 survey visits.** Its loss blocks sit at the start
of the night, which makes the brackets read as nested segments. The WEATHER bit was set for
1.09 h from 23:15 UTC; the whole window lies inside the −12° night (22:53 → 10:44 UTC). Under ROSP-24
the allskycam cloud index adds 0.5 h of weather while the bit was masked by DOWNTIME (22:55–23:15 and
01:48–01:59 UTC), so the weather block is 1.6 h (1.1 h on the 26 Oct morning version, 0.98 h on the −18°
night).
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

All computed by `simonyi_time_loss/time_loss/classify.py` (ROSP-24 ordered classifier, −12° night, gap_min = 10 min,
categories of `engineering_time_budget`) and read here from `rosp24_intervals_20260708.csv`; the script prints every
number below. The figure shows the ROSP-24 column; the other two are what the two earlier versions of the same day showed.

| Quantity | **ROSP-24 (on the figure)** | 26 Oct morning (ROSP-22 only) | −18° → −18° (first version) |
|---|---|---|---|
| night | 2026-07-08 22:52:47 → 2026-07-09 10:43:31 UTC, **11.846 h** | 11.846 h | 10.875 h |
| weather | **1.6 h** (1.614): WEATHER bit 23:15:36–00:20:50 (1.087) + allskycam cloud index > 0.5 while the bit was masked by DOWNTIME, 22:54:59–23:15:36 (0.343) and 01:47:59–01:59:00 (0.183) | 1.1 h (1.087, bit only) | 0.98 h |
| engineering | **0.1 h** (0.118): 10 Focus and Alignment visits (BLOCK-T539), 03:07:00–03:14:06 | — (inside on sky) | — |
| fault + idle | **2.9 h** (2.860): 1.5 h (1.453) 00:20:50–01:47:59 + 1.1 h (1.133) 01:59:00–03:07:00, camera recovery after the REB power-supply trip (FRACAS-404), + 0.3 h (0.274) 03:36:21–03:52:49, HV bias trip (OBS-2010) | 3.4 h (3.424): 0.4 + 2.8 + 0.3 | 3.04 h |
| start-up allowance (A3) | 2.2 min, 22:52:47–22:54:59 (drawn inside survey) | — | — |
| **Observable night** bracket | **11.8 h** | 11.8 h | 10.9 h |
| **Survey time only** bracket (night − weather − engineering) | **10.1 h** (10.113) | 10.8 h (10.758; night − weather) | 9.9 h |
| **Excluding faults (= on sky)** bracket (survey visits + bridged gaps + start-up allowance) | **7.3 h** (7.253), three segments: 22:52:47–22:54:59, 03:14:06–03:36:21, 03:52:49–10:43:31 | 7.3 h (7.334) | 6.8 h |
| **Exposing** bracket (shutter open: sum of `exp_time` of the 559 survey visits) | **4.7 h** (4.665) | 4.9 h (4.895, "Exposing + readout", 569 visit intervals) | 4.5 h |
| exposing + readout (sum of the survey visit intervals, README only) | 4.8 h (4.810) | 4.9 h (4.895, all 569 visits) | 4.5 h |
| visit-scale overhead (bracket 3 − exposing + readout) | 2.4 h (2.443) | 2.4 h (2.439) | 2.3 h |

Partition: weather 1.614 + engineering 0.118 + fault/idle 2.860 + on sky 7.253 = 11.846 h = the night; the same
numbers are the `per_night.csv` row of this night in `simonyi_time_loss` (`weather_hours` 1.614, `engineering_hours`
0.118, `nonweather_loss_hours` 2.860, `on_sky_hours` 7.216 + `startup_hours` 0.037).

Ratios for slide text (not on the figure): exposing 4.7 h ÷ brackets 1 / 2 / 3 = **39 % / 46 % / 64 %**; on sky 7.3 h ÷
brackets 1 / 2 = 61 % / 72 %; exposing + readout 4.8 h ÷ 1 / 2 / 3 = 41 % / 48 % / 66 %. (26 Oct morning: 41 / 46 / 67 %
with exposing + readout; 62 / 68 / 100 % with on sky.)

What moved on this night, and why:

- **Weather 1.1 → 1.6 h.** Under ROSP-24 §C the allskycam cloud index is the evidence where FAULT or DOWNTIME masks
  the WEATHER bit. DOWNTIME was set all the way from −12° to 03:02 UTC. The index reads > 0.5 in 78 % of the minutes
  22:53–23:15 (median 0.97: the clouds the night report describes, "became worse by 23 UTC when we decided to close"),
  in 44 % of the bit window (median 0.42, clearing), and in 7 % of 00:20–03:07 (median 0.11; one 11-min run above
  0.5 at 01:48–01:59). The C1 tower limits never fire (RH 2–5 %, T − Td > 38 °C, wind ≤ 6.3 m/s). So the 0.4 h
  "camera still down before the weather closure" block of the morning version is now 0.34 h weather plus 2.2 min of
  start-up allowance, and 11 min of the camera recovery are weather. ROSP-24 says weather masks the fault; the camera
  was down in both windows (shadow record: all 1.614 h of weather fall inside DOWNTIME).
- **Engineering 0.1 h.** The 10 BLOCK-T539 visits (03:07–03:14) are engineering under the 26 Oct rule ("calibrations
  count as engineering"; Bruno to confirm, default yes). Bracket 2 excludes them.
- **Fault + idle 3.4 → 2.9 h**: −0.34 h (cloud before the bit), −0.18 h (cloud at 01:48), −0.04 h (start-up allowance).
- **Exposing 4.7 h** replaces "Exposing + readout 4.9 h" (ROSP-24 A1 is shutter open; readout is A2 overhead).

Visits: 569 on-sky visits, 559 Survey Programs (all BLOCK-407; bands i 256, r 211, z 99, u 3), 10 Focus and Alignment
(BLOCK-T539), 0 other engineering; all inside the −12° night; the last visit ends 10:41:04 UTC, 2.4 min before the
morning −12° limit, so that edge gap is bridged into survey. All exposures are 30 s (31 s start to end). Inter-visit
gaps: 546 ≤ 60 s (median 9 s), 21 of 2–4 min (white slivers), 1 ≥ 10 min (the HV bias trip).

## Definitions, decisions and deferrals

- **Precedence (ROSP-24, 2026-10-19).** Time goes to the first category that applies: planned maintenance
  (none in the range, ROSP-28) → weather → engineering → fault + idle → science. The classification is the one
  of `simonyi_time_loss` (`time_loss/classify.py`, README §3c there); this folder only draws it.
- **Weather** = the WEATHER bit, plus, where FAULT or DOWNTIME masks the bit, the allskycam cloud index > 0.5
  or a C1 weather-tower limit (RH > 80 %, T − Td < 2 °C, wind > 15 m/s or gust > 18 m/s) in runs ≥ 10 min.
  Weather takes precedence over everything below it, including visits.
- **Categories** as in B10 / the on-sky utilization timeline: Survey Programs = BLOCK-407/408/416/417/419/421;
  everything else on sky is **engineering**, Focus and Alignment (BLOCK-T539) included (26 Oct rule,
  "calibrations count as engineering"; **Bruno to confirm, default yes**; 7 min on this night, reported as a
  sub-total in `per_night.csv`). Engineering blocks are the non-survey visits bridged at gaps ≤ 10 min.
- **Fault + idle** is the remainder; D and E stay merged (ROSP-50 open); the 10-min gap rule stays, so gaps
  under 10 min are on sky and lump A2 with D3 (ROSP-49 open). Includes unplanned DOWNTIME.
- **Science** = Survey-Program visits with gaps ≤ 10 min bridged (A1 + A2), plus the **start-up allowance**
  (A3, 26 Oct rule): the first 10 min after evening −12° up to the first survey visit, 2.2 min here because
  the cloud fallback starts at 22:55. Drawn as a lighter survey tint, no label.
- **Brackets 1–3** are the observable night (−12° → −12°), the night minus weather and engineering
  ("Survey time only": what the survey could have used), and the night minus weather, engineering and
  fault/idle ("Excluding faults (= on sky)" = B3's `on_sky_hours` + `startup_hours` for this night, the green
  of B1/B3). No figure codes on the image; the link lives here.
- **Bracket 4, "Exposing"** (deck decision 2026-10-26, default applied): shutter-open only, the sum of
  `exp_time` of the survey visits inside the night, ROSP-24's A1; readout is A2 overhead. Drawn as the summed
  length packed against the end of the last survey visit, dotted to say "packed, not a time span", and never
  called "on sky". "Exposing + readout" (sum of the visit intervals) is in the table above for the README only.
- **Colours**: one palette across B1, B3 and B11 (2026-10-26): survey green (palette slot 5), engineering
  orange (slot 2, as B10/B10b; Focus and Alignment takes the engineering colour now), weather neutral grey
  (30 % tint, hatched, label in secondary ink), fault + idle brand blue `#1C81A4` (18 % tint, hatched).
  Checked with the dataviz palette validator on all six pairs (worst CVD ΔE 12.3, worst normal-vision ΔE 15.5,
  PASS); red and olive fail the normal-vision floor against the orange, purple and teal pass but are taken by
  B10b's Focus and Survey.
- Thin −18° ticks are drawn inside the −12° limits (29 min after the evening one, 29 min before the
  morning one) so the astronomical-twilight night (10.9 h) can be compared with the 11.8 h bracket.

## Run

```bash
python night_efficiency_brackets/python/make_night_brackets_figure.py
```

Needs pandas, matplotlib and the repo palette (`../rubin_color_pallete`, copy the module into this
folder before extracting the investigation). To redo the figure for another night, change `DAY_OBS`
(and `NIGHT_SUN_ALT` to switch back to −18°), re-extract the three data files from the `simonyi_time_loss`
and `engineering_time_budget` caches, and export that night's interval sets from
`simonyi_time_loss/data/cache/classification.pkl` to `rosp24_intervals_<day_obs>.csv` (see the file list
above); `GAP_LABELS` holds the ticket text per block start (UTC HH:MM).
