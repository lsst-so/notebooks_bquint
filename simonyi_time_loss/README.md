# Simonyi time loss under the ROSP-24 precedence, Oct 2025 – Oct 2026

Technical note for the `simonyi_time_loss` folder of `lsst-so/notebooks_bquint`.
Status: **per-night table and figures done (2026-10-18); re-run on the −12° observable night (2026-10-26, ROSP-22);
re-run under the ROSP-24 loss-cause precedence (2026-10-26, evening); extended through the July 2026 storm to the
latest complete night (2026-11-01, §3.8)**; cross-check against the human tables done;
Q2 (per-ticket fault accounting) deferred. ROSP-24 is a draft under debate ("Verifying", Brian Stalder; comments of
2026-10-10, 10-19 precedence, 10-22, 10-25, 10-26 rules, all read 2026-10-26); the talk says so.
Prepared for the RASAB 2026 talk (Natal, 25 Oct 2026), LSST@LATAM (São Paulo, Nov 2026) and a
later paper figure.

## 1. Purpose

Quantify, per night, how Simonyi night time from the first night of Early Operations (`day_obs` 20251025) to the
latest complete night (20261031) splits into the ROSP-24 loss-cause categories: **survey**, **engineering**,
**Focus and Alignment**, **weather**, **planned maintenance**, **fault + idle**, plus the small start-up allowance
and unattributed remainders. The original specification is `handoff_usdf_time_loss_analysis.md` (2026-10-18); the
ROSP-24 re-run follows `HANDOFF_rosp_precedence_2026-10-26.md` (received 2026-10-26); the extension across the
July 2026 storm follows the handoff of 2026-11-01 (§3.8). This README records what was actually done and the
numbers it rests on.

**Two windows, deliberately.** The range splits at 20260714, the last night with the dome open before the storm.
The **on sky season** (20251025 → 20260714, 263 nights, 2590 h) is the window every share quoted in the talk is
computed over; the **full range** (372 nights, 3734 h) adds 109 nights that are almost entirely closed, which
would otherwise swamp those shares. Both lines are printed in the B3 figure title, season first.

**The night (ROSP-22, Done 2026-10-19).** The observable night is Sun altitude **−12° → −12°**, from
`rubin_nights.dayobs_utils.day_obs_sunset_sunrise`; weather and downtime are not excluded from it
(`NIGHT_SUN_ALT = -12` in `time_loss/__init__.py`). The −18° night is carried as `night_hours_18` for reference.

**The precedence (ROSP-24, comment of 2026-10-19).** One ordered per-minute classifier over the −12° night
(`time_loss/classify.py`) assigns every second of the night to the first category that applies; every figure and
`per_night.csv` come from that one assignment, and the categories sum to the night exactly:

| # | ROSP-24 | here | column(s) | season, to 2026-07-14 | full range, to 2026-10-31 |
|---|---|---|---|---|---|
| 0 | — | **storm windows assigned by rule, not by data**: 2026-07-15 → 2026-10-26 is weather or planned maintenance per Bruno's decision (§3.8). Applied before everything below | `storm_override`, `override_*_hours` | n/a | 1099.3 h over 104 nights |
| 1 | B1 planned maintenance | 2026-09-16 → 2026-10-05, the official downtime block (§3.8); zero in the season (ROSP-28) | `planned_maintenance_hours` | 0 h | 200.5 h, 5.4 % |
| 2 | C weather | WEATHER bit (from 2026-02-25); where the bit is absent or **masked** (FAULT or DOWNTIME set, bit unset): allskycam cloud index > 0.5 or the C1 weather-tower limits (§3c). Plus the storm and recovery windows | `weather_hours`, `bit_weather_hours`, `fallback_weather_hours` (+ `_cloud_`, `_c1_`), `weather_masked_fault_hours` (shadow record) | 305.2 h, 11.8 % | 1215.0 h, 32.5 % |
| 3 | Focus and Alignment | BLOCK-T539 visits, bridged at gaps ≤ 10 min. **Its own category** since 2026-10-27 (Bruno: neither engineering nor survey); was a sub-total inside engineering before | `focus_alignment_hours` | 102.4 h, 4.0 % | 103.0 h, 2.8 % |
| 3b | B2 engineering | the other on-sky visits that are not Survey Programs, bridged at gaps ≤ 10 min | `engineering_hours` | 415.3 h, 16.0 % | 416.4 h, 11.2 % |
| 4+5 | D technical fault + E operational idle | the remainder: unplanned DOWNTIME, faults, idle, closed-dome engineering; **merged** (ROSP-50 open); includes the Dynalene condensation closures (Bruno, 2026-10-26: not weather) | `nonweather_loss_hours`, `dynalene_hours`, `idle_bit_hours` | 875.2 h (909.7 drawn, with F) | 884.7 h (919.2 drawn), Dynalene 77.8 h |
| 6 | A science operations | A1 + A2 (+ D3, ROSP-49 open): Survey-Program visits with gaps ≤ 10 min bridged; A3: the first 10 min after evening −12° up to the first survey visit | `on_sky_hours`, `exp_time_survey_hours`, `startup_hours` | 846.8 h (857.6 drawn, with A3) | 869.2 h (880.0 drawn), A3 10.8 h |
| 7 | F unattributed | UNKNOWN observatory state from 2026-02-25 where it would otherwise be fault + idle; not separable before | `unattributed_hours` | 34.5 h, 1.3 % | 34.5 h, 0.9 % |

Shares, as drawn (start-up inside survey, F inside fault + idle) — **season**: 11.8 % weather, 4.0 % focus,
16.0 % engineering, 35.1 % fault + idle, 33.1 % survey. **Full range**: 32.5 % weather, 5.4 % maintenance,
2.8 % focus, 11.2 % engineering, 24.6 % fault + idle, 23.6 % survey.

The season columns are the numbers the talk quotes. Note the **focus split**: before 2026-10-27
`engineering_hours` contained `focus_alignment_hours`, so the old season engineering figure was 517.7 h
= 415.3 + 102.4; the two are now disjoint and the per-night columns sum to the night without
double counting (checked: residual 0.02 h over 372 nights).

Deferred, with the current rule kept and stated: fault and idle merged (IDLE bit only from 2026-02-25, Q7/ROSP-50);
the 10-min gap rule lumps A2 and D3 (minimum fault duration undecided, Q8/ROSP-49); closed-dome engineering stays in
fault + idle (no source separates it from maintenance); F before 2026-02-25 stays inside fault + idle ("before 25 Feb,
fault + idle includes any time that would be unattributed"). The two human-judged tables (tailgate notes, night
reports) are **annotation only**: the night-report cloud hours used until this morning are kept as
`report_cloud_hours` for the cross-check and are no longer in the accounting.

## 2. Contents

```
simonyi_time_loss/
├── README.md                              # this file
├── ai_notes.md                            # session log, decisions, open items (handoff for the next session)
├── handoff_usdf_time_loss_analysis.md     # the specification, as received 2026-10-18
├── time_loss/                             # shared package (notebooks run from notebooks/ with sys.path.insert(0, ".."))
│   ├── __init__.py                        # DAY_OBS_MIN/MAX, NIGHT_SUN_ALT = -12, GAP_MIN_MINUTES = 10, DAY_OBS_WEATHER_BIT_START = 20260225, STORM_PERIODS + DAY_OBS_BACK_ON_SKY (§3.8)
│   ├── access.py                          # ConsDB / EFD / narrative-log clients (token or Postgres fallback)
│   ├── nights.py                          # −12° and −18° limits per day_obs
│   ├── weather.py                         # WEATHER-bit windows; EFD CLOSE criteria by validity window (Dynalene rule still used, as a fault tag)
│   ├── visits.py                          # ConsDB on-sky coverage, gap bridging
│   ├── intervals.py                       # interval-set arithmetic (union / intersect / subtract) in UTC MJD
│   ├── fallback.py                        # ROSP-24 §C weather fallback: allskycam cloud index > 0.5, C1 tower limits → windows
│   ├── classify.py                        # the ROSP-24 ordered per-minute classifier (one assignment per night) + label rule + storm_override (§3.8)
│   ├── accounting.py                      # the pre-ROSP-24 arithmetic (kept for per_night_20261026_pre_rosp24.csv; no longer run)
│   ├── style.py                           # imports ../rubin_color_pallete; the one talk palette (survey green, engineering orange, weather grey, fault blue)
│   └── downtime.py                        # copy of nightly_survey_speed/downtime.py (outage spans → axes annotations)
├── python/pull_efd_weather_1min.py        # 15 EFD channels × 372 nights at 1-min cadence → data/cache/ (resumes from cache; --start to extend)
├── python/pull_allsky_cloud_1min.py       # Brian Stalder's allskycam cloud index → 1-min grid, data/cache/allsky_cloud_1min.parquet
├── python/run_rosp24_accounting.py        # the whole accounting from the caches → per_night.csv, per_month.csv, classification.pkl (~5 s)
├── python/make_latam_figures.py           # LSST@LATAM 2026 talk figures B1 (monthly) and B3 (nightly) from per_night.csv
├── python/gap_min_sensitivity.py          # gap histogram, season totals for gap_min 2–30 min, state inside the ambiguous gaps (§3b)
├── notebooks/00 … 06                      # all executed in order (00 inventory → 06 figures)
├── data/
│   ├── downtime_annotations.csv           # copy of nightly_survey_speed/downtime_annotations.csv (talk = 1 rows are labelled)
│   ├── raw/                               # inputs as received (handoffs, human tables, criteria table, night-log CSV)
│   ├── step0/                             # inventory + intermediate tables (parquet gitignored); rosp24_step0_per_night.csv, fallback_windows_per_night.csv, allsky_cloud_coverage.csv
│   ├── cache/                             # EFD + allsky 1-min caches, window pickles, classification.pkl (gitignored)
│   └── processed/                         # per_night.csv/.parquet (deliverable), per_month.csv, per_period.csv (nights + hours per storm period, §3.8), per_night_with_human.csv, per_night_20261026_pre_rosp24.csv (the table before the ROSP-24 re-run), per_night_v0.csv (2026-10-18, historical)
├── HANDOFF_2026-10-18.md                  # state of the work after the first build, how to resume
├── HANDOFF_rosp_precedence_2026-10-26.md  # the ROSP-24 re-run specification, as received 2026-10-26
└── figures/                               # time_loss_{nightly,monthly}_{talk,paper}_<tag>.png (+ _white variants of the talk versions)
```

## 3. Step 0: what exists, for which dates (2026-10-18)

All counts below are from `notebooks/00_step0_data_coverage.ipynb`; the tables are in `data/step0/`.
Range as inventoried in October 2026: 263 calendar nights, `day_obs` 20251025 → 20260714 — the **on sky season**.
The range was later extended to 20261031 (372 nights) across the storm; §3.8 covers the added nights, and the
counts in §3.1–3.7 below are left as they were taken, over the season.

### 3.1 Ephemeris (`night_limits.csv`)

| | −18° → −18° | −12° → −12° |
|---|---|---|
| shortest night | 6.7 h | 7.9 h |
| longest night | 11.0 h | 11.9 h |
| total, 263 nights | 2319.6 h | 2590.2 h |

Confirmed by reading the source: `rubin_nights.dayobs_utils.estimated_baseline_visit_range`
(Lynne's expected-visits model) uses `sun_alt=-12` (handoff §8 item 4). ROSP-22 (Done 2026-10-19)
made −12° → −12° the observable-night definition; this accounting follows it from 2026-10-26.

### 3.2 ConsDB `cdb_lsstcam.visit1` (`consdb_visit1_coverage.csv`, `calendar_coverage.csv`, `zero_visit_nights.csv`)

| Quantity | Value |
|---|---|
| nights with any `visit1` row (incl. bias/dark/flat/CBP) | 219 of 263 |
| nights with any on-sky visit (`airmass > 0`) | 187 |
| nights with ≥ 20 on-sky visits | 183 |
| on-sky visits | 97 777 (of which 1384 `engtest`, 28 `indome` with airmass > 0) |
| nights with **zero** on-sky visits | **76** |

"On-sky" here is `airmass > 0`, which keeps `engtest` and drops bias/dark/flat/CBP (airmass NULL
or 0). This is broader than the on-sky-utilization figure's `img_type IN ('acq','science','cwfs','focus')`,
on purpose: on-sky engineering is not loss (handoff §1b).

The 76 zero-visit nights form 25 runs. The long ones: 20251225–28 (condensation shutdown),
20260120–26 and 20260129–0215 (LSSTCam Dynalene loss / warm-up; dome shutter telemetry shows the
dome *open* on 20260130–31 and 20260204–14 with no camera), 20260320–23, 20260502–10 (TMA azimuth
encoder failure + cryo), 20260608–10 and 20260615–18 and 20260620–24 (weather + pump cart),
20260701–04. The per-night cross-match with shutter state, state bits, narrative log and the human
tables is `zero_visit_nights.csv` (27 of the 76 had the shutter open > 50 % at some point in the
12 h → 12 h UTC day).

### 3.3 Observatory state, `lsst.sal.Scheduler.logevent_observatoryStatus` (`obs_state_periods.parquet`, `obs_state_per_night.csv`)

Via `rubin_nights.observatory_status.get_observatory_state_times` (periods are clipped to the −12°
night by that function; day_obs assigned by rubin_nights).

| State | Periods | Hours | First | Last (≤ 20260714) |
|---|---|---|---|---|
| OPERATIONAL | 504 | 988.5 | 2026-02-26 | 2026-07-15 |
| FAULT | 425 | 185.9 | 2026-02-26 | 2026-07-12 |
| IDLE | 126 | 280.7 | 2026-03-05 | 2026-07-14 |
| UNKNOWN | 174 | 64.3 | 2026-02-26 | 2026-07-11 |
| DOWNTIME | 28 | 243.0 | 2026-03-05 | 2026-07-09 |
| **WEATHER** | **36** | **219.7** | **2026-03-08** | 2026-07-14 |

- First message 2026-02-25 13:09 UTC (Scheduler CSC start). Every night from 20260225 to 20260714
  has at least one record (140 nights). **No state data before 2026-02-25** (134 of the 263 nights).
- WEATHER is set on 33 nights; 18 of them have ≥ 6 h. Nights 20260715–19 (storm, outside range)
  add another 5 × ~11.7 h.
- Coverage holes: on 20260320, 20260615, 20260616 the exclusive states (OPERATIONAL + FAULT +
  IDLE + UNKNOWN) cover < 10 % of the night while WEATHER and DOWNTIME are both set for the full
  night. This is the "DOWNTIME masks WEATHER" overlap from handoff §2; both bits are kept.
- Lynne's reference numbers (handoff §3) are for Mar–Jul 2026 and include the storm; they are not
  reproduced here yet.

### 3.4 Narrative log, `time_lost > 0` (`narrative_log_timelost.parquet`, `narrative_log_timelost_per_night.csv`)

Query: `narrativelog/messages`, `is_valid=true`, `has_date_begin=true`, `min_time_lost > 0`, over
the full range. `day_obs` is derived here from `date_begin` with the 12:00 UTC rollover (the API
has no `day_obs` field; `rubin_nights` indexes by `date_begin` too).

| | |
|---|---|
| entries with time lost | 501 (439 fault, 62 weather) |
| components | Simonyi 359, AuxTel 101, LSSTCam 14, unlabelled 9, Simonyi Calibration 7, Facilities 4, IT 3, Control SW 3, EAS 1 |
| nights with ≥ 1 entry | 178 (first 20251025, last 20260710) |
| non-AuxTel nights with weather loss / fault loss | 21 / 153 |

Non-AuxTel hours by month (fault / weather): Oct 30.5 / 6.5, Nov 33.8 / 3.0, Dec 39.0 / 18.5,
Jan 95.1 / 15.6, Feb 162.6 / 9.2, Mar 28.4 / 6.7, Apr 33.6 / 6.4, May 11.3 / 0.0, Jun 29.6 / 16.3,
Jul 0.9 / 6.0. The Jan–Feb fault total is dominated by whole-night entries during the camera
shutdown (several nights log 16–27 h, i.e. more than the night, so the field was used as a
"downtime" tally). The known 2026-04-28 example (handoff §2) is reproduced: one entry of 4.08 h
weather ("Thick clouds over whole sky since 06:00 UTC") plus 0.61 h LSSTCam fault.

### 3.5 EFD weather telemetry for the operating criteria (`ess_sensor_inventory.csv`, `ess_weekly_counts.csv`, `shutter_daily.csv`)

Topic / field names found for the handoff §5 quantities (the `[check]` items):

| Quantity | EFD topic | Field | `salIndex` / sensor | Cadence | Coverage |
|---|---|---|---|---|---|
| outside dew point | `lsst.sal.ESS.dewPoint` | `dewPointItem` | 301 "Weather tower computed dew point" | ~4 s | every week of the range |
| outside air temperature | `lsst.sal.ESS.temperature` | `temperatureItem0` | 301 "Weather tower air temperature" | ~4 s | every week |
| outside relative humidity | `lsst.sal.ESS.relativeHumidity` | `relativeHumidityItem` | 301 | ~4 s | every week |
| wind speed / gust | `lsst.sal.ESS.airFlow` | `speed`, `maxSpeed` | 301 "Weather tower airflow" | ~1.3 s | every week (`maxSpeed` ≈ `speed` in the sample; check the averaging) |
| inside (camera) dew point | `lsst.sal.ESS.dewPoint` | `dewPointItem` | 111 "Camera-ESS01, camera inlet plane" | ~1.4 s | every week |
| other inside dew points | same | same | 112 (M2), 113 (M1M3) | | every week |
| Dynalene supply temperature | `lsst.sal.MTCamera.utiltrunk_UT` | `coolPipeSplyTemp` (also `coolPipeRetnTemp`) | — | 10 s | every week |
| dome shutter position | `lsst.sal.MTDome.apertureShutter` | `positionActual0/1` (0–100 %) | — | ~0.5 s | 261 of 263 nights (none on 20260623–24) |
| dome shutter state | `lsst.sal.MTDome.logevent_shutterMotion` | `state0/1` | — | event | 4835 events in range |
| rain | `lsst.sal.ESS.rainRate` | `rainRateItem` | — | sparse (12k rows total, mostly Jun–Jul) | not usable as a criterion |
| dust counters ESS:127/128/129, all-sky camera | not found in the EFD measurement list | | | | |

The handoff's `lsst.MTCamera.utiltrunk_ut.CoolPipeSplyTemp` resolves to
`lsst.sal.MTCamera.utiltrunk_UT.coolPipeSplyTemp`. Louver anemometers (ESS 441/443) and louver
temperatures (442) appear from March 2026 only; the WiFi-test sensors (118–120) disappear after
January 2026.

### 3.6 Human-judged tables (`data/raw/`, parsed to `data/step0/*_per_night.csv`)

All inputs received (2026-10-18): `nightlog_simonyi_20251025_20260720.csv` + `manual_notes.csv` (night-report export,
269 rows, 11 nights without a report), `weather_criteria_table.md`, the nine Source 1 month files
`tailgate_sweep_2025-10-11.md` … `tailgate_sweep_2026-07.md`, the ten Source 2 month files
`nightlog_sweep_2025-10.md` … `nightlog_sweep_2026-07.md`, and `crosscheck_S1_vs_S2_2025-10-25_to_2026-07-14.md`
+ `crosscheck_sources.py`. `tailgate_sweep_ALL.md` and `nightlog_sweep_2025-10_to_2026-07.md` are concatenations built
here (the Source 2 one was received as a single file and split back into months for parity).

| | Source 1 (tailgate notes) | Source 2 (night reports) |
|---|---|---|
| parsed file | `tailgate_source1_per_night.csv` | `nightlog_source2_per_night.csv` |
| nights | 264, 2025-10-24 → 2026-07-14, no gaps | 263, 2025-10-25 → 2026-07-14, no gaps |
| status | PARTIAL 101, CLOSED 72, OPEN 60, UNKNOWN 31 | OPEN 106, CLOSED 75, PARTIAL 72, UNKNOWN 10 |
| nights in two month files | 2026-02-01 (Jan row kept; Feb row differs only in P: 0.1/0.95 vs 0.3/1.0), 2026-04-30 (UNKNOWN in both) | none |

Both parsed tables reproduce the cross-check file exactly: all 122 listed rows match on status, P(weather) and P(fault),
and the recomputed status agreement is 171 of 263 nights, as the cross-check states. The parser keeps the first file's row
when a night appears twice. The per-night evidence text and ticket lists are carried into the CSVs for notebook 05.

### 3.7 Allskycam cloud index and the C1 tower limits (ROSP-24 §C fallback; Step 0 of 2026-10-26, `allsky_cloud_coverage.csv`, `rosp24_step0_per_night.csv`)

Brian Stalder's product, `/sdf/data/rubin/user/stalder/allsky/cloud/<day_obs>.parquet` (pipeline v5 of 2026-10-10,
files dated 2026-10-18): one row per allskycam frame while the Sun is below −12°, `cloud_idx` = 1 − observed /
expected bright stars under a per-unit-per-month clear-sky completeness model, clipped to [0, 1]. ROSP-24 §C names
`cloud_idx > 0.5` as the weather evidence where the WEATHER bit is absent or masked.

| | |
|---|---|
| nights with a file, 20251025 → 20260714 | **259 of 263**; missing 20260130–20260202 (camera vacuum leak, no Simonyi observing) |
| cadence | 1 frame per minute; median 566 frames per night; largest intra-night gap 5 min |
| minutes of the −12° night without a frame within 3 min | 87 h of 2590 (3.4 %), 34 h of it the four nights without a file |
| frames flagged `geometry_ok = False` | kept (the running astrometric solution is applied; a failed gate usually means overcast) |
| **validation, bit era** | WEATHER-bit minutes: cloud index > 0.5 in **66 %**, > 0.3 in 74 %; C1 limits met in 11 %; either in 71 %. OPERATIONAL-and-observing minutes: index > 0.5 in **3.5 %** |
| validation, pre-bit era | minutes covered by visits: index > 0.5 in 0.8 %, C1 in 0.2 % |
| pre-bit era, index > 0.5 inside the night (per minute) | 26.1 h on 15 nights (7 nights ≥ 1 h); 6.3 h of it on 4 nights overlaps the old EFD-criteria windows |
| pre-bit era vs. the 19 night-report cloud nights (55.7 h) | the index agrees on **4** of them (31 Oct 3.7 h, 5 Dec 7.7 h, 21 Dec 5.2 h, 25 Jan 1.6 h; 18.5 h) and reads **clear all night on the other 15**. Two of those are explainable: 7 Dec (rain and hail in the afternoon, dome kept shut as a precaution, clear at night) and 13 Dec (chiller fault, "humidity > 70 %" with the tower reading 60 %); the rest are Dynalene nights where the report's "weather" is the condensation rule |
| pre-bit era, ≥ 1 h cloud with no report cloud | 26 Oct (1.9 h; report: "cloudy in the last couple of hours"), 17 Nov (2.0 h), 3 Feb (1.2 h, camera down) |

C1 tower limits (ROSP-24 §C, 2026-10-26), on the weather tower ESS `salIndex` 301 at 1-min cadence
(`python/pull_efd_weather_1min.py`): RH > 80 % (`relativeHumidity.relativeHumidityItem`), dew-point depression
`temperature.temperatureItem0 − dewPoint.dewPointItem` < 2.0 °C, wind `airFlow.speed` 1-min mean > 15 m/s or
`airFlow.maxSpeed` 1-min max > 18 m/s. These are the sensors of `weather_criteria_table.md` rows 2, 3 and 5; the
thresholds differ from the operating rules there (20 / 25 m/s, RH de-prioritised) because ROSP-24 C1 states 15 / 18
and RH > 80 %. Precipitation and snow/ice on the dome have no usable EFD source (§3.5) and are not evaluated. Over
the range the C1 limits are met 54.9 h per minute (RH 33.2, dew point 15.1, wind 21.9, overlapping), 21.9 h of it
before 2026-02-25. The tower RH reads a median of 3–4 % on the −12° night of 8 Jul and below 10 % on 32 nights
from January; checked 2026-10-27 and found genuine: on those nights the other five ESS humidity sensors (camera 111,
M2 112, M1M3 113, AuxTel 201, laser 404) agree with the tower within 1 %, and the tower RH reproduces its own
T / dew point through the Magnus formula to 0.1 %. The low readings are the dry Pachón winter (April–July), not a
sensor fault; the earlier "8 °C below the T − (100 − RH)/5 formula" remark was an artefact of that approximation,
which only holds above ~50 % RH.

Fallback windows are runs of fallback minutes merged across gaps < 10 min and kept only if ≥ 10 min, the resolution
of the gap rule (`fallback.py`). The minimum-duration choice moves the pre-bit fallback by 1 h and the masked-period
fallback by 2.5 h (5 / 10 / 20 min: 47.7 / 47.3 / 46.4 h and 37.2 / 35.7 / 32.1 h before clipping).

**Masked periods (bit era).** Minutes with FAULT or DOWNTIME set and WEATHER unset: 338.4 h inside the −12° night
(DOWNTIME 191.7 h, FAULT alone 146.7 h). The fallback says weather in 32.4 h of them per minute (28.4 h cloud), 37.7
h as ≥ 10-min windows, on 39 nights; the largest: 6 May 8.4 h (camera glycol night; cloud index > 0.5 all night, the
report says "bad weather prediction" and does not describe the sky), 5 May 4.4 h (wind 15–20 m/s, gusts to 23, no
report), 4 Mar 4.2 h (closed engineering night, "thick clouds after 06:30 UTC"), 2 Jun 2.0 h, 7 May 1.8 h.

### 3.8 The July 2026 storm, downtime and recovery (extension of 2026-11-01)

The range was extended from 20260714 to the latest complete night so that the figure covers the storm and the
return to sky. Three periods between them are classified **by rule, not from the data** (Bruno's decisions,
handoff of 2026-11-01). The boundaries are fixed: they are not to be moved to fit the data.

| Period (`day_obs`) | Category | Nights | −12° hours | Rationale |
|---|---|---|---|---|
| 20260715 → 20260915 | **weather** | 63 | 702.3 | Snowstorm and aftermath: off sky from 13/14 Jul, evacuation 15 Jul, power lost 19 Jul, road cut in 5 places, no regular summit access |
| 20260916 → 20261005 | **planned maintenance** (B1) | 20 | 200.5 | Official start per Kevin Reil, #summit-announce, 2026-09-16 ("Downtime officially started today; most work already underway"). End fixed by Bruno at 2026-10-05 |
| 20261006 → 20261026 | **weather** | 21 | 196.5 | Recovery and return-to-sky period. Bruno's rule: count all of it as weather, since access lost to snow and road closures dominates |
| 20261027 → | normal accounting | 5 | 44.7 | Back on sky; the standard weather / fault / downtime split from the data |

Supporting evidence (from the handoff): 2026-07-21 Christensen / Reil, worst storm in about 30 years, mountain
access unlikely for weeks; 2026-08-27 Reil, "back to normal" next week with minibus then bus, downtime work
starting with overnight stays at Hotel Pachón; 2026-09-16 Reil, downtime officially started, target back on sky
12 Oct; 2026-09-21 / 09-28 / 10-05 Rubin Engineer Leads (Confluence 2070085672, 2099871745, 2129231873), return
target week of 12 Oct; 2026-10-19 (2185428993) "Back on sky still pending", mountain forecast closed 26–30 Oct;
2026-10-26 Christensen, "added weather to operational (it was still downtime earlier in the night)".

**First night back on sky: `20261027`** (determined on USDF, 2026-11-01, as the handoff asked — *Bruno to
confirm*). It is the first `day_obs` after 2026-10-05 with on-sky visits (`airmass > 0`) in ConsDB
`cdb_lsstcam.visit1`: 589 BLOCK-407 + 91 BLOCK-T698 science and 10 BLOCK-T539 acq. There is **nothing** on sky
between 20260715 and 20261026; 20261026 has 1389 rows but all calibration (bias / dark / flat, airmass NULL).
20261028 and 20261031 are again blank (weather 9.0 h, then a FAULT night).

**Why the override is needed, and what it overrides.** As the handoff warned, the observatory-state record calls
this period DOWNTIME, including the storm and the loss of site access:

- 20261006 → 20261026 is logged **DOWNTIME** for the whole night (9.0–9.7 h/night), with IDLE from 20261015.
- 20260715 → 20260719 is logged DOWNTIME *and* WEATHER together (11.7 h each).
- There is **no state record at all** for 20260720 → 20260924.

The underlying telemetry is also absent, which is itself the storm: the EFD returns nothing for any of the 15
weather channels for **20260720 → 20260923** (66 nights), consistent with summit power lost on 19 Jul; and
Brian Stalder's allskycam cloud product has no file for **20260719 → 20261009**. So neither the WEATHER bit nor
the ROSP-24 §C fallback can decide these nights — hence a rule.

The override is implemented as step 0 of the classifier (`classify.storm_override`, windows in
`time_loss/__init__.STORM_PERIODS`) and records what it displaced, so a conflict is visible rather than erased:
`storm_override`, `override_onsky_hours`, `override_operational_hours`, `override_fault_hours` per night. Over the
104 override nights it displaced **0.0 h of on-sky time**, 7.9 h OPERATIONAL and 47.0 h FAULT.

**One flagged conflict**, as the guardrail requires: **20261026** is inside the recovery window (→ weather) but
the state record gives it 7.9 h OPERATIONAL. That night has no on-sky visits, only 1389 calibration frames, and
the state record *itself* already logged 7.7 h WEATHER for it — Eric Christensen's note of that date ("added
weather to operational, it was still downtime earlier in the night") is the same event. The rule and the data
agree on the conclusion; no boundary change is proposed. No other night conflicts.

Per-period nights and hours are written to `data/processed/per_period.csv` and printed by
`python/make_latam_figures.py`.

## 3b. Results (2026-10-26 evening, ROSP-24 precedence, gap_min 10 min, −12° night)

Per night in `data/processed/per_night.csv`; monthly in `per_month.csv`; figures in `figures/`, regenerated by
`python python/run_rosp24_accounting.py && python python/make_latam_figures.py`. The talk versions
(`*_talk_*.png`, transparent, and `*_talk_*_white.png`) are B1 (monthly) and B3 (nightly), plus the six-bin
slide-4 B1 of §3b.1 (`*_6bin*`); notebook 06 produces the `_paper` versions. On the plots the start-up allowance is drawn inside survey and the
unattributed hours inside fault + idle (one series, caveat spoken); the Dynalene closures are hatched inside fault +
idle, and weather is hatched throughout (the palette grey is light and low-contrast). Legend and title list the
categories in precedence order.

### 3b.1 Slide-4 B1: six bins at 6 × 4 in (2026-11-02)

`monthly_6bin()` in `python/make_latam_figures.py` draws a second B1 for slide 4 of the LSST@LATAM deck,
`figures/time_loss_monthly_talk_20251025-20261031_6bin[_white].png`. The original `monthly()` and its files are
kept unchanged so the two can be compared. The figure is **exactly 6 × 4 in at 300 dpi** (constrained layout,
no `bbox_inches="tight"`) so it drops onto the 10 × 5.625 in slide without rescaling; tick and legend type is
≥ 10 pt. There is no title — the headline numbers belong on the slide, not in the figure. Range is the full
one, 25 Oct 2025 – 31 Oct 2026, 372 nights, **3734.2 h** of −12° night (the 2590.2 h / 263-night season figure
is the subset to 14 Jul).

**In-bar value labels** (Bruno, 2026-11-02): each segment of the four coloured bins carries its percentage in
white, `LABEL_PT = 8` pt — below the 10 pt floor the rest of the figure keeps, since it only needs to be legible
beside its own bar. Weather and Planned maintenance are never labelled (white type is illegible on the light
greys, and the talk does not quote those two per month). Labels are centred on their own segment, not on the
bar. Two gates, `min_frac = max(LABEL_MIN_FRAC, (LABEL_PT + 2 pt) / axes height)`:

* **`LABEL_MIN_FRAC = 0.05`** — an editorial floor; below 5 % of the night the number is not worth reading off
  the slide. This is the binding gate at 6 × 4 in.
* **the measured fit test** — `LABEL_PT + 2 pt` converted to an axis fraction through the *drawn* axes height,
  so a label can never be taller than its own segment if the figure size or `LABEL_PT` changes.

The gate tests the true fraction, not the rounded label, so a 4.6 % segment is dropped rather than printed as
"5%". Unlabelled in the current figure: the Alignment slivers in Jan–Mar and May–Jun 2026, Oct 2025 Science
(4.7 %) and the 3 % Fault slice in Oct 2026.

**Minimising empty space** (same session): bars are 0.94 wide with x-limits at ±0.03 so they run nearly edge to
edge; the year appears on the first month and each January only (printing "2026" on eleven ticks cost ~0.3 in of
plot height); layout pads are 0.01; the legend is three columns × two rows. Because matplotlib fills a legend
column-first, the handle order is **transposed** so it reads left → right in stack order (Weather, Planned
maintenance, Fault + idle / Alignment, Engineering, Science).

**The y axis** (Bruno, 2026-11-02) is a horizontal ruling instead of an axis: `_fraction_yaxis()`, shared by
`monthly()` and `monthly_6bin()`, drops the left spine, the tick marks *and* the tick labels — the "Night
Fraction" label alone is enough to read a 20 % ruling, and dropping the labels gives the width back to the bars
(the 6-bin axes goes to 5.78 of the 6 in). A rule is drawn at each interior 20 %; 0 % is the x axis and 100 % the
top of the frame, so neither gets one. Each runs past the axes — **3 pt left** (a nick, beside the ylabel) and
**10 pt right** — re-fitted on every draw, since the overhang is a length in points but `Line2D` x-data is an
axes fraction and the axes width is only final once the layout engine has run.

Each rule is a **pair of touching 0.5 pt hairlines, one white one black, both at alpha 0.3**, offset ±¼ pt so the
pair straddles the level. Whichever tone matches the background drops away and the other carries the line. That
is not fussiness — the rules cross backgrounds from near-white (the margins, and the plot area above the short
bars) to near-black (Science is `#024243`), and **no flat colour is visible on all of them**. Five attempts, each
rendered on the real figure, settled it: white and light grey `#CCCCCC` vanish in the margins; mid grey
`#6E7374` and `#333333` vanish over Science and Engineering; white-inside-with-ink-overhangs looks like a drawing
error at the join. A white core over a dark halo (`path_effects`) also worked but read heavier, with a faint
doubling on the light greys. Tune the weight at `GRID_ALPHA` / `GRID_LW`, but note the two interact: the first
try at 0.25 pt / alpha 0.25 was invisible at 300 dpi (≈ 1 px antialiased to quarter strength, and the two tones
composite toward the mid grey that had already failed). 0.3 at 0.5 pt was checked against 0.5 on zoomed crops of
the Apr/May teals and holds.

The six bins are the categories the classifier already produces — no new classification. Stack bottom → top,
legend top → bottom in the same order, both from the single constant `SLIDE2_CAT`:

| Plot bin | Source column | Full range | % of night | ROSP-24 draft (Verifying, 30 Oct 2026; sign-off target 16 Nov) |
|---|---|---|---|---|
| Science | `on_sky_hours + startup_hours` | 880.0 h | 23.6 % | A — science operations (A1 exposure, A2 overhead; A3 start-up allowance) |
| Engineering | `engineering_hours` | 416.4 h | 11.2 % | B2a — on-sky engineering |
| Alignment | `focus_alignment_hours` | 103.0 h | 2.8 % | B2a, except start-up within ~10 min of −12° (A3); overrun = D1 (draft rule) |
| Fault + idle | `nonweather_loss_hours + unattributed_hours` | 919.2 h | 24.6 % | D (D1–D4) + E idle + **F unattributed** |
| Planned maintenance | `planned_maintenance_hours` | 200.5 h | 5.4 % | B1 — planned maintenance |
| Weather | `weather_hours` | 1215.0 h | 32.5 % | C (C1–C3; C4 road access does not occur in this period) |

Two notes on the mapping. **F unattributed is inside Fault + idle**, not separate: `load_per_night()` sets
`fault_plot = nonweather_loss_hours + unattributed_hours`, so the 34.5 h of F (all of it from 2026-02-25 on) is
drawn in the fault colour — the caveat is spoken, as for the older B1. **Planned maintenance is a real bin
here**, unlike in the season-scoped B1 where it was 0.0 h: the storm extension brings in 151.5 h in Sep 2026
and 48.9 h in Oct 2026.

Split check, printed by `_check_split()` on every run and compared against the bins as `monthly()` groups them
(not against this function's own columns, so it is a real comparison): per month, Science + Engineering +
Alignment equals the old "on sky" to **0.000 h**, Weather and Fault + idle move by **0.000 h**, and the six bins
still partition the night to **0.009 h** worst case.

#### Colours — temporary, deliberate palette violation

`SLIDE2_COLORS` / `SLIDE2_CAT` are a **local override in this figure only**, read from the night-definition strip
on slide 2 of the deck so B1 matches it: Science `#024243`, Engineering `#045B5C`, Alignment `#058B8C`,
Fault + idle `#F5A623`, Planned maintenance `#546E7A`, Weather `#9BAEB8`. They break the Rubin palette on
purpose. `rubin_color_pallete/rubin_palette.py` and `CATEGORY_COLORS` are untouched; switching back is one line
(use `CAT` instead of `SLIDE2_CAT` in `monthly_6bin()`). `SLIDE2_COLORS` is the single source for the hexes;
`SLIDE2_CAT` carries only column, label and hatch. Planned maintenance is not a slide-2 colour — it had no
slot, and `#546E7A` is a tone of the weather grey chosen on 2026-11-02 so the two "closed" bins read as a pair.
Weather was lightened from the slide-2 `#78909C` to `#9BAEB8` (Bruno, 2026-11-02) so the large weather blocks
recede; the two greys are told apart by **hatch direction** — Weather `\\\\`, Planned maintenance `////`.

The dataviz CVD validator **fails** on this palette (`scripts/validate_palette.py`, light mode, 6 slots): the
**normal-vision floor fails** at ΔE 8.5 (Engineering↔Science) against a floor of 15, i.e. that pair is hard to
tell apart even with full colour vision, and under `--pairs all` CVD fails at ΔE 5.4 (Planned
maintenance↔Alignment, deutan). The lightness band and chroma floor fail too (the three dark teals sit below
the band and read as near-grey), and Fault + idle warns on contrast vs a white surface at 1.97:1. Lightening
Weather *improved* the worst all-pairs CVD figure from ΔE 3.8 to 5.4. Mitigations applied without changing the
colours, as instructed: a 0.6 pt white edge between every stacked segment, opposed hatch directions on the two
grey bins, and legend order identical to stack order. **The colours are Bruno's call, not the validator's** —
this is recorded so the trade-off is explicit, and reverting to `CATEGORY_COLORS` restores a passing palette.

#### Alignment over time

Alignment as a share of on-sky time does fall over the season, though **not monotonically** — it rises again in
Mar–Apr 2026:

| | Oct 25 | Nov | Dec | Jan 26 | Feb | Mar | Apr | May | Jun | Jul | Oct 26 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Alignment (h) | 3.1 | 27.2 | 22.3 | 8.3 | 3.4 | 12.7 | 15.1 | 6.2 | 2.3 | 1.7 | 0.7 |
| % of on sky | 12.9 | 15.5 | 15.9 | 7.3 | 4.1 | 6.3 | 6.4 | 3.6 | 1.6 | 2.2 | 2.8 |

Full range: 103.0 h, **7.4 %** of on-sky time. Aug–Sep 2026 have no on-sky time (storm, maintenance).

Alignment blocks split by when they start, bridged at ≤ 10 min as the classifier does (wall clock, so gaps
inside a block count — this totals **107.7 h** against the bin's 103.0 h, the difference being what the bin
clips to the night and loses to the weather-first precedence):

| Timing | Hours | Share | Draft ROSP-24 treatment |
|---|---|---|---|
| a) start of night, ≤ 10 min after evening −12° | 26.9 | 25.0 % | A3 science-operations start-up |
| b) start of night, before first science visit, beyond 10 min | 64.2 | 59.6 % | start-up overrun → D1 short fault (draft rule) |
| c) after the first science visit (mid-night realignment) | 16.6 | 15.4 % | B2a on-sky engineering |

So the bulk of alignment — 59.6 % — is start-up that overran the 10-minute allowance, which the draft would
book as a short fault rather than as engineering. Monthly values are printed by the figure script.

**engtest visits**: 1384 of the 99 691 on-sky visits in `visits_onsky_20251025_20261031.parquet` carry
`img_type = engtest`, and **all 1384** fall in the Engineering bin here (mostly `BLOCK-T614`, 1143). They are
not in the nightly survey speed plot's Engineering. The 1412 count quoted in §3c is over 25 Oct – 14 Jul and
counts `engtest` **and** `indome`.

> **This section records the state of 2026-10-26**, over the 263-night season and with Focus and Alignment still
> inside engineering. Two later changes move the numbers below: the **focus split** of 2026-10-27 (engineering
> 517.7 → 415.3 h, focus 102.4 h as its own category) and the **storm extension** of 2026-11-01 (§3.8), which
> adds 109 nights and changes the figure tag to `20251025-20261031`. The season shares the talk quotes are
> unchanged by the extension; §1 carries the current totals for both windows.

**What moved** (both columns on the −12° night; "26 Oct morning" is `per_night_20261026_pre_rosp24.csv`):

| | 26 Oct morning (ROSP-22 only) | | **ROSP-24 (now)** | |
|---|---|---|---|---|
| | hours | share | hours | share |
| night, 263 nights | 2590.2 | | **2590.2** | |
| survey (on sky) | 1368.2 (survey + engineering) | 53 % | **846.7** (+ 10.8 start-up = 857.6 drawn) | **32.7 %** (33.1 % drawn) |
| engineering (incl. Focus and Alignment 100.2 h) | — | — | **517.7** | **20.0 %** |
| weather | 389.2 | 15 % | **305.2** | **11.8 %** |
| fault + idle (incl. Dynalene 77.1 h) | 859.1 | 33 % | **875.3** (+ 34.5 unattributed = 909.7 drawn) | **33.8 %** (35.1 % drawn) |
| start-up allowance (A3) | — | — | 10.8 | 0.4 % |
| unattributed (F, from 25 Feb) | — | — | 34.5 | 1.3 % |
| planned maintenance (B1) | — | — | 0 | 0 |

The on-sky total is almost unchanged (1368.2 → 846.7 + 517.7 + 10.8 = 1375.2 h; the 7 h difference is weather
precedence over visits, 9.1 h, less the edge bridging now applied to engineering): the big move is the **split of
"on sky" into survey and engineering**, 38 % of the old on-sky hours being engineering. Weather falls by 84 h because
the Dynalene windows (109 h) leave it and the night-report cloud hours (56 h) are no longer a source, offset by 48 h of
allskycam/C1 fallback before the bit and 38 h of fallback inside masked FAULT/DOWNTIME periods after it.

Weather by source: WEATHER bit 219.7 h (140 nights, as before); fallback inside masked periods 37.7 h on 39 nights;
fallback before the bit 47.8 h on 19 nights (as ≥ 10-min windows: cloud 26.6 h, C1 24.5 h, overlapping). Dynalene rule:
109.2 h in total, 77.1 h now in fault + idle, 5.5 h stay weather (a C1 or cloud window overlaps), 26.5 h were observed
through (the observers overrode the rule; survey or engineering). Shadow record: 101.5 h of weather fall inside FAULT
or DOWNTIME (`weather_masked_fault_hours`). Weather ∩ visits: 9.1 h, assigned to weather by precedence.

Labels (presentation rule, §3c): CLOSED 82, FAULT-DOMINATED 112, OPEN 54, WEATHER-DOMINATED 15 (26 Oct morning:
82 / 107 / 46 / 28). Of the 28 WEATHER-DOMINATED nights 16 became FAULT-DOMINATED (Dynalene nights) and 1 OPEN;
7 FAULT-DOMINATED became OPEN (engineering no longer counted as loss on the label side) and 4 WEATHER-DOMINATED
(masked-period fallback). Nights with ≥ 0.5 h on sky but < 0.5 h of survey: 36 (engineering nights).

Monthly shares of the −12° night (%, as drawn; 26 Oct morning on-sky in brackets):

| | Oct | Nov | Dec | Jan | Feb | Mar | Apr | May | Jun | Jul |
|---|---|---|---|---|---|---|---|---|---|---|
| survey | 5 (41) | 26 (70) | 12 (57) | 37 (43) | 29 (32) | 22 (65) | 49 (72) | 44 (48) | 38 (41) | 42 (46) |
| engineering | 34 | 44 | 45 | 7 | 3 | 44 | 24 | 5 | 3 | 4 |
| weather | 10 (11) | 5 (1) | 6 (33) | 3 (25) | 2 (7) | 7 (6) | 3 (2) | 18 (13) | 31 (29) | 29 (26) |
| fault + idle | 51 (48) | 26 (29) | 37 (15) | 52 (37) | 65 (61) | 28 (30) | 25 (26) | 33 (39) | 28 (30) | 25 (28) |

Engineering vs. B10: B10 (`engineering_time_budget`) gives 378 + 107 = 485 h of non-survey on-sky time over
20 Oct 2025 – 19 Jul 2026 with same-category bridging and the `img_type` filter acq/science/cwfs/focus; here 517.7 h
over 25 Oct – 14 Jul because `engtest` and `indome` visits with airmass > 0 (1412) are kept, focus and engineering
are bridged together, and edge gaps ≤ 10 min are bridged to the night limit. Same-category B10 bridging on this visit
set gives 500.2 h inside the −12° night.

Cross-check (notebook 05): code CLOSED (nothing on sky for 0.5 h) agrees with Source 2 CLOSED on 75/75 nights and
never contradicts an OPEN. Confidence per night: HIGH 188, MEDIUM 60, LOW 15 (26 Oct morning 192 / 61 / 10). The LOW
nights are the Dynalene nights the reports call weather (22, 24 Dec; 5, 6, 11, 12, 13 Jan) and five nights where the
fallback calls 1–2 h of cloud or RH a weather closure on a night the reports call OPEN or fault (26 Oct, 5 Nov, 17 Nov,
20 Dec, 4 Dec). Against the narrative log's declared hours on 160 nights: code weather 100 h vs declared 88 h
(correlation 0.37, was 0.6 when the Dynalene nights counted as weather on both sides); code fault + idle 450 h vs
declared fault 350 h excluding the whole-night camera-shutdown tallies, correlation 0.64.

**gap_min sensitivity and the ambiguous gaps** (`python/gap_min_sensitivity.py`, 2026-10-27; tables
`data/processed/gap_min_sensitivity.csv`, `visit_gaps.parquet`). The season has 97 152 inter-visit gaps on 185 nights.
Bridging is a step function of gap length, so the question is how much time sits near the 10-min rule:

| gap length (min) | 0–2 | 2–5 | 5–7.5 | 7.5–10 | 10–15 | 15–20 | 20–30 | 30–60 | 60–120 | >120 |
|---|---|---|---|---|---|---|---|---|---|---|
| gaps | 93 471 | 2730 | 354 | 178 | 173 | 84 | 64 | 67 | 17 | 14 |
| hours | 341.0 | 126.2 | 36.5 | 25.5 | 34.7 | 23.7 | 26.5 | 45.2 | 22.6 | 48.8 |

Season totals (−12° night, 2590 h) as the rule moves: survey 29.6 / 32.2 / 32.8 / **33.1** / 33.7 / 33.9 / 34.1 %,
engineering 16.4 / 18.6 / 19.4 / **20.0** / 20.8 / 21.5 / 22.5 %, fault + idle 42.3 / 37.4 / 36.1 / **35.1** / 33.7 /
32.7 / 31.6 % at gap_min 2 / 5 / 7.5 / **10** / 15 / 20 / 30 min; weather 11.8 % throughout (it takes precedence
over visits). Between 5 and 20 min, a factor two either side of the rule, the totals move by ±1.5 points; a
2-min rule is the only choice that changes the picture (−3.5 points of survey), and it counts the ~3-min
filter-change and slew gaps as loss. Nights whose label changes between 5 and 20 min: OPEN 37 → 76,
FAULT-DOMINATED 130 → 91 (CLOSED and WEATHER-DOMINATED are unaffected).

The ambiguous gaps themselves: 789 gaps of 5–20 min, **120.5 h** (4.7 % of the night), on 175 nights, median 4 per
night. The observatory state and the dome tell what they were (bit era, 398 gaps, 63.6 h; the pre-bit 391 gaps,
56.9 h have no state):

| | gaps | h | OPERATIONAL > 50 % | FAULT/DOWNTIME > 50 % | WEATHER | mixed |
|---|---|---|---|---|---|---|
| 5–10 min, bridged as overhead now | 250 | 29.1 | 159 (18.2 h) | 52 (6.2 h) | 13 (1.6 h) | 26 (3.1 h) |
| 10–20 min, counted as loss now | 148 | 34.5 | 54 (12.1 h) | 58 (13.6 h) | 5 (1.3 h) | 31 (7.5 h) |

In every one of them the shutter is open and the telescope above 20°: these are short interruptions of an
observing night, not closures. Half of the bridged 5–10 min gaps are in OPERATIONAL state and a fifth carry a
FAULT, so the 10-min rule mislabels about 6 h of short faults as overhead; conversely about 12 h of the 10–20 min
gaps are OPERATIONAL (scheduler or observer pauses with nothing in fault) and are charged to fault + idle. The two
errors nearly cancel at 10 min, which is a second reason to keep it. A state-aware rule (bridge a gap ≤ 20 min
unless the Scheduler is in FAULT or DOWNTIME) would move ~12 h from fault + idle to survey/engineering and ~6 h the
other way, 0.5 points of the night, and only works in the bit era; it is not applied.

Known limitations: the allskycam index misses closures that were decided on forecast or afternoon weather (7 Dec)
and cannot see humidity, so pre-bit weather is a lower bound (the 15 report-cloud nights it contradicts hold 37 h);
the tower RH `[check]` above; closed-dome engineering sits in fault + idle; the WEATHER bit was not set on some
short cloud interruptions and the masked-period fallback only recovers those inside FAULT/DOWNTIME; the five
Dec–Jan nights where observers overrode the Dynalene rule are now simply observed time.

## 3c. How the numbers are calculated

Every number in §3b is produced by `python/run_rosp24_accounting.py` from the cached inputs (notebooks 00–03 build the
caches; notebook 04 runs the driver; 05 cross-checks; 06 draws the paper figures). All times are UTC; nights are
bucketed by the integer `day_obs` (rolls over at 12:00 UTC). "The night" is the −12° → −12° observable night
(ROSP-22). All categories are interval sets in UTC MJD (`intervals.py`); they partition the night to better than
10 s, so the per-night columns sum to `night_hours`.

### Night length (`nights.py`, notebook 01)

`rubin_nights.dayobs_utils.day_obs_sunset_sunrise(day_obs, sun_alt=-12)` (and −18 for `night_hours_18`).

### Inputs per night

* **Visits** (`visits.py`, notebook 03): ConsDB `cdb_lsstcam.visit1` rows with `airmass > 0` (keeps on-sky
  engineering, drops bias/dark/flat/CBP); TAI → UTC (−37 s); `obs_end` repaired from `exp_time` where missing.
  Category by `science_program`: Survey Programs = BLOCK-407/408/416/417/419/421; everything else is engineering,
  Focus and Alignment (BLOCK-T539) reported as a sub-total.
* **WEATHER bit** (`weather.py`): `lsst.sal.Scheduler.logevent_observatoryStatus` periods via
  `rubin_nights.observatory_status`, from 2026-02-25; also the FAULT, DOWNTIME, IDLE and UNKNOWN periods.
* **Fallback weather** (`fallback.py`, §3.7): allskycam `cloud_idx > 0.5` (1-min grid, `pull_allsky_cloud_1min.py`)
  or any C1 tower limit (RH > 80 %, T − Td < 2 °C, wind > 15 m/s or gust > 18 m/s) on the 1-min EFD cache; runs
  merged across gaps < 10 min, runs < 10 min dropped.
* **Dynalene rule** (`weather.py`, unchanged): Dynalene(Az1) − outside dew point against the threshold valid on the
  date (≤ +2 °C 2025-12-15 → 12-29; < +2 °C 12-30 → 2026-01-18; ≤ +1 °C 01-19; < −2 °C from 01-20; 20-min
  persistence); now a **tag inside fault + idle**, not a weather source.

### The ordered classifier (`classify.py`)

With N = the night and R = what is still unassigned (starts as N):

1. **B1 planned maintenance**: `PLANNED_MAINTENANCE` blocks (noon → noon UTC); empty over the 263-night season
   to 14 Jul (ROSP-28), but 200.5 h once the storm extension is in range (151.5 h Sep 2026, 48.9 h Oct 2026).
2. **C weather** = WEATHER-bit windows ∪ (fallback windows ∩ masked), where masked = (FAULT ∪ DOWNTIME) − WEATHER
   in the bit era, and = fallback windows before 2026-02-25. Weather takes precedence over visits: minutes observed
   while the bit was set are weather (`weather_and_onsky_hours`, 9.1 h). Shadow record `weather_masked_fault_hours`
   = weather ∩ (FAULT ∪ DOWNTIME).
3. **B2 engineering** = union of the non-survey visit intervals bridged at gaps ≤ 10 min (focus and engineering
   together), an edge gap ≤ 10 min to the night limit bridged when the first/last visit is non-survey; ∩ R.
4. **A1 + A2 survey** = union of all visit intervals bridged at ≤ 10 min (edge gaps ≤ 10 min bridged), minus the
   engineering blocks; ∩ R. A bridged gap between a survey and an engineering visit is survey overhead.
5. **A3 start-up allowance** = [evening −12°, min(+10 min, first survey visit)] ∩ R, only on nights with a survey
   visit; 10.8 h on 74 nights (mean 8.8 min). The handoff's "overrun beyond 10 min is fault + idle" follows.
6. **F unattributed** = UNKNOWN state ∩ R (bit era only); 34.5 h on 61 nights, 26 h of UNKNOWN fall on visits and
   stay survey/engineering.
7. **D + E fault + idle** = R. Tags inside it: `dynalene_hours` (Dynalene rule windows ∩ R), `idle_bit_hours`
   (IDLE state ∩ R, bit era).

`per_night.csv` columns, besides the category hours above: `bit_weather_hours`, `fallback_weather_hours` (used),
`fallback_cloud_hours`, `fallback_c1_hours`, `fallback_any_hours` (all fallback windows of the night, whether used or
not), `dynalene_total_hours`, `dynalene_weather_hours`, `on_sky_any_hours` (survey + engineering blocks),
`exp_time_survey_hours` (shutter-open, A1), `n_*_visits`, `cloud_minutes_missing`, and the annotation-only
`report_cloud_hours`, `closed_unexplained_hours`, `report_p_weather`, `report_p_fault`.

`label` is the presentation rule (handoff §1b), adapted: CLOSED if `on_sky_any_hours` < 0.5 h; else OPEN if
weather + fault/idle + unattributed is below 10 % of the night; else WEATHER-DOMINATED or FAULT-DOMINATED by whichever
of weather and fault/idle is larger. It is not a definition.

### Cross-check (notebook 05)

As before: the two human tables and the narrative log are joined on `day_obs`; disagreement classes are listed, never
averaged; `confidence` per night is HIGH / MEDIUM / LOW by consistency with both, one or neither human source.
"Code CLOSED" now means no survey *or* engineering visit for 0.5 h.

### Not in these numbers

Cloud the allskycam does not see (closures decided on forecast or afternoon weather, humidity without cloud);
closed-dome engineering (inside fault + idle); image-quality-only losses (telescope on sky, data unusable, e.g.
2026-04-24); AuxTel. The 2026-07-15 → 2026-10-26 storm, downtime and recovery period **is** now in the range, by
rule rather than from the data (§3.8); it is excluded from the season shares the talk quotes.

## 4. Environment and access

```bash
source /sdf/group/rubin/sw/loadLSST.bash; setup lsst_distrib      # lsst-scipipe-14.0.0, rubin_nights 0.18.2
export ACCESS_TOKEN_FILE=$HOME/.token_file                         # usdf-rsp token; narrative log needs it
cd simonyi_time_loss/notebooks
jupyter nbconvert --to notebook --execute --inplace 00_step0_data_coverage.ipynb
```

`time_loss/access.py` sets `ACCESS_TOKEN_FILE` (if `~/.token_file` exists), `PGPASSFILE` and
`RUBIN_SIM_DATA_DIR` itself. On 2026-10-18 the RSP token route worked for ConsDB, EFD and the
narrative log from the SDF login node; ConsDB falls back to the Postgres replica otherwise.
The EFD client is `rubin_nights.influx_query.InfluxQueryClient` (synchronous InfluxQL via
`efd.query(...)`); `lsst_efd_client` (async) is not used.

## 5. Open items (for Bruno)

1. ~~**Focus and Alignment = engineering**~~ superseded 2026-10-27: it is **its own category**, neither engineering
   nor survey (102.4 h over the season, 7 min on 8 Jul). Applied in the classifier and drawn as its own block in
   B1/B3 since 2026-11-01; November is the month where it matters most (11 % of the night).
1b. **First night back on sky = 20261027** (§3.8) — determined from ConsDB, *awaiting Bruno's confirmation*. It
   sets the end of the recovery window; if it is wrong, change `DAY_OBS_BACK_ON_SKY` and the last
   `STORM_PERIODS` entry together.
2. **B11 bracket 4 = shutter-open only "Exposing"** (default yes, applied): 4.7 h; "exposing + readout" 4.8 h is in
   the B11 README.
3. ~~Tower RH sanity `[check]`~~ resolved 2026-10-27 (§3.7): the 3–10 % winter readings are confirmed by five
   independent ESS sensors and by the tower's own dew point; no under-detection.
4. The 15 pre-bit nights the night reports call cloud but the allskycam calls clear (§3.7): 37 h now in fault + idle;
   7 Dec (rain/hail precaution) is the clearest case where the ROSP-24 evidence hierarchy and the observers disagree.
5. Masked-period fallback on nights nobody would call weather nights (6 May camera glycol, 8.4 h cloudy): ROSP-24
   says weather masks the fault; the shadow record keeps the fault hours.
6. Deferred by ROSP: fault/idle split (ROSP-50), gap rule and minimum fault duration (ROSP-49), dome closed by
   policy (ROSP-47), closed-dome engineering (ROSP-28).
