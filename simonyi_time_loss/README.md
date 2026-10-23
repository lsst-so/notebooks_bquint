# Simonyi time loss: weather vs. non-weather, Oct 2025 – Jul 2026

Technical note for the `simonyi_time_loss` folder of `lsst-so/notebooks_bquint`.
Status: **per-night table and first figures done (2026-10-18)**; cross-check against the human tables done;
Q2 (per-ticket fault accounting) deferred. Nothing committed yet.
Prepared for the RASAB 2026 talk (Natal, 25 Oct 2026), LSST@LATAM (São Paulo, Nov 2026) and a
later paper figure.

## 1. Purpose

Quantify, per night, how much Simonyi night time was lost to **weather** and how much to
**everything else** (faults + idle, reported as "fault" for the talks) between the first night of
Early Operations (`day_obs` 20251025) and the last night with the dome open before the winter
storm (20260714). The specification is `handoff_usdf_time_loss_analysis.md` (received 2026-10-18);
this README records what was actually done and the numbers it rests on.

The deliverable is a per-night table with three measured quantities and one derived label:

| Column | Definition | Source |
|---|---|---|
| `night_hours_18`, `night_hours_12` | hours between sun altitude −18°/−18° and −12°/−12° | ephemeris (`rubin_nights.dayobs_utils.day_obs_sunset_sunrise`) |
| `weather_hours` (+ windows) | time inside the night when the observatory was closed because of weather | Observatory Status WEATHER bit (from 2026-02-25); EFD weather telemetry vs. the operating criteria before that and as a cross-check |
| `nonweather_loss_hours` | `night_hours_18 − weather_hours − on_sky_hours`, where `on_sky_hours` is time covered by ConsDB `visit1` visits with gaps > `gap_min` counted as loss | ConsDB |
| `label` | CLOSED / WEATHER-DOMINATED / FAULT-DOMINATED / OPEN (presentation rule, handoff §1b) | derived |

The two human-judged tables (morning tailgate notes, night logs) are cross-checks, not inputs.

## 2. Contents

```
simonyi_time_loss/
├── README.md                              # this file
├── ai_notes.md                            # session log, decisions, open items (handoff for the next session)
├── handoff_usdf_time_loss_analysis.md     # the specification, as received 2026-10-18
├── time_loss/                             # shared package (notebooks run from notebooks/ with sys.path.insert(0, ".."))
│   ├── __init__.py                        # DAY_OBS_MIN/MAX, GAP_MIN_MINUTES = 10, DAY_OBS_WEATHER_BIT_START = 20260225
│   ├── access.py                          # ConsDB / EFD / narrative-log clients (token or Postgres fallback)
│   ├── nights.py                          # −18° and −12° limits per day_obs
│   ├── weather.py                         # WEATHER-bit windows; EFD CLOSE criteria by validity window; closed_unexplained
│   ├── visits.py                          # ConsDB on-sky coverage, gap bridging, loss windows
│   ├── accounting.py                      # per-night arithmetic, label rule, pre-bit cloud reassignment
│   ├── style.py                           # imports ../rubin_color_pallete; role → colour map
│   └── downtime.py                        # copy of nightly_survey_speed/downtime.py (outage spans → axes annotations)
├── python/pull_efd_weather_1min.py        # 15 EFD channels × 263 nights at 1-min cadence → data/cache/
├── python/make_latam_figures.py           # LSST@LATAM 2026 talk figures (nightly with outage labels, monthly) from per_night.csv
├── notebooks/00 … 06                      # all executed in order (00 inventory → 06 figures)
├── data/
│   ├── downtime_annotations.csv           # copy of nightly_survey_speed/downtime_annotations.csv (talk = 1 rows are labelled)
│   ├── raw/                               # inputs as received (handoffs, human tables, criteria table, night-log CSV)
│   ├── step0/                             # inventory + intermediate tables (parquet gitignored)
│   ├── cache/                             # EFD 1-min cache, window pickles (gitignored)
│   └── processed/                         # per_night.csv/.parquet (deliverable), per_night_v0.csv (before cloud step), per_month.csv, per_night_with_human.csv
├── HANDOFF_2026-10-18.md                  # state of the work, open items, how to resume
└── figures/                               # time_loss_{nightly,monthly}_{talk,paper}_<tag>.png (+ _white variants of the talk versions)
```

## 3. Step 0: what exists, for which dates (2026-10-18)

All counts below are from `notebooks/00_step0_data_coverage.ipynb`; the tables are in `data/step0/`.
Range: 263 calendar nights, `day_obs` 20251025 → 20260714.

### 3.1 Ephemeris (`night_limits.csv`)

| | −18° → −18° | −12° → −12° |
|---|---|---|
| shortest night | 6.7 h | 7.9 h |
| longest night | 11.0 h | 11.9 h |
| total, 263 nights | 2319.6 h | 2590.2 h |

Confirmed by reading the source: `rubin_nights.dayobs_utils.estimated_baseline_visit_range`
(Lynne's expected-visits model) uses `sun_alt=-12` (handoff §8 item 4).

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

## 3b. Results (2026-10-18, gap_min 10 min, −18° night)

Per night in `data/processed/per_night.csv`; monthly in `per_month.csv`; figures in `figures/`.
The talk versions (`*_talk_*.png`, transparent, and `*_talk_*_white.png`) are regenerated by
`python python/make_latam_figures.py` (2026-10-23, LSST@LATAM): the nightly figure carries the three
long outages the talk points at (camera vacuum leak 30 Jan – 15 Feb, TMA encoder 2 – 10 May, camera
cryo 20 – 24 Jun; spans from `data/downtime_annotations.csv`) and dates the WEATHER-bit line; the
monthly figure drops slice labels below 10 %. Notebook 06 still produces the `_paper` versions.

| | hours | share of night |
|---|---|---|
| night (−18° → −18°), 263 nights | 2319.6 | |
| on sky | 1267.6 | 55 % |
| weather | 344.8 | 15 % |
| non-weather loss (fault + idle) | 729.4 | 31 % |

Weather source by period: WEATHER bit on 140 nights from 2026-02-25 (203.2 h); EFD criteria on 123 nights before
(65.2 h from wind / dew-point spread / Dynalene rule) plus 46.7 h of **night-report cloud** on 18 nights
(Bruno's option 2: `closed_unexplained_hours` moved to weather only where Source 2 gives P(weather) ≥ 0.5; flagged in
`weather_source` and `cloud_reassigned_hours`). Weather∩on-sky overlap 22.2 h is reported, not double-subtracted.
Labels (presentation rule): CLOSED 82, FAULT-DOMINATED 84, OPEN 70, WEATHER-DOMINATED 27.

gap_min sensitivity: on-sky 1093 / 1212 / 1268 h at 2 / 5 / 10 min; non-weather loss moves by the same amounts.

Cross-check (notebook 05): code CLOSED agrees with Source 2 CLOSED on 75/75 nights and never contradicts an OPEN.
Confidence per night: HIGH 184, MEDIUM 64, LOW 15. The LOW nights are mostly Dec–Jan nights where the Dynalene rule
fires but observers judged no weather loss (12-18, 12-20, 12-29, 01-18, 01-19), and nights where the WEATHER bit was not
set for a short cloud closure the report mentions (03-16, 04-12, 06-06, 06-13). Against the narrative log's declared
hours on 160 nights: code weather 176 h vs declared 88 h; code non-weather 327 h vs declared fault 350 h (excluding the
whole-night camera-shutdown tallies), correlation 0.6 for both.

Known limitations: cloud is invisible to the EFD criteria (hence the night-report step before 2026-02-25); the WEATHER
bit was not set on some short cloud interruptions; the Dynalene rule is applied mechanically on 2026-01-19 although
observers overrode it after inspection; non-weather loss bundles fault, idle, planned engineering off-sky and
staffing (Q2 splits it per ticket).

## 3c. How the numbers are calculated

Every number in §3b is produced by `time_loss/` and the notebooks in order 00 → 06. This section states the
definitions in words so that the method can be checked without reading code. All times are UTC; nights are
bucketed by the integer `day_obs` (rolls over at 12:00 UTC), never by UTC calendar date.

### Night length (`nights.py`, notebook 01)

For each `day_obs`, the Sun's −18° evening crossing (astronomical twilight) and the next −18° morning crossing
are computed with `rubin_nights.dayobs_utils.day_obs_sunset_sunrise(day_obs, sun_alt=-18)`, which wraps
`astroplan.Observer` at the Rubin site. `night_hours_18` is their difference. `night_hours_12` is the same with
−12° (nautical twilight) and is only reported, not used in the accounting. No data enters this step.

### On-sky time (`visits.py`, notebook 03)

1. Query ConsDB `cdb_lsstcam.visit1` for `day_obs` in range and `airmass > 0`. The airmass cut keeps every
   exposure taken through the open dome, including on-sky engineering (`engtest`, alignment, AOS triplets), and
   drops bias, dark, flat and CBP exposures, whose airmass is NULL or 0. On-sky engineering counts as observing.
2. Convert `obs_start_mjd` / `obs_end_mjd` from TAI to UTC (−37 s). Where `obs_end` is missing or earlier than
   `obs_start`, use `obs_start + exp_time`.
3. Sort the night's visits by start time and take the union of their `[start, end]` intervals, **bridging** any
   gap between consecutive visits that is ≤ `gap_min` (10 min). A gap that short is readout, slew, filter change
   or settling: normal overhead, counted as observing.
4. Clip the result to the −18° night. `on_sky_hours` is the total length of these windows.
5. Every stretch of the night not covered by an on-sky window and longer than `gap_min` is a **loss window**.
   This includes the two edge gaps: from the −18° evening limit to the first visit, and from the last visit to
   the −18° morning limit. The three `gap_min` values 2 / 5 / 10 min are all computed and saved; the accounting
   uses 10 (Bruno, 2026-10-18).

### Weather time (`weather.py`, notebook 02)

Two independent sources; the first that exists on a night is the primary.

**A. Observatory Status WEATHER bit (from 2026-02-25).** `rubin_nights.observatory_status.get_observatory_state_times`
turns `lsst.sal.Scheduler.logevent_observatoryStatus` messages into start/end periods per state. The WEATHER
periods of the night are clipped to the −18° night; their total length is `bit_weather_hours`. The bit is set by
the observers through the Scheduler CSC and so already encodes their judgement that the closure was weather.

**B. EFD operating criteria (whole range; primary before 2026-02-25).** `python/pull_efd_weather_1min.py` pulls
15 channels at 1-minute cadence for each night from 2 h before the −18° evening limit to 1 h after the morning
limit. The CLOSE rules from the Confluence "Weather Constraints" page (v29) and from
`data/raw/handoff_dynalene_condensation_criteria_2025-12_2026-01.md` are evaluated per minute:

| rule | channel(s) | CLOSE when | valid |
|---|---|---|---|
| wind | `ESS.airFlow.speed`, `.maxSpeed`, salIndex 301 (weather tower) | 10-min rolling mean > 20 m/s, or 10-min rolling minimum of the per-minute max ≥ 25 m/s ("sustained gusts"); stays CLOSE until 15 consecutive minutes with the 10-min mean below 20 | whole range |
| dew-point spread | `ESS.temperature.temperatureItem0` − `ESS.dewPoint.dewPointItem`, salIndex 301 | < 2 °C for 20 consecutive minutes | whole range |
| Dynalene condensation | `MTMount.dynaleneCooling.dynaleneTemperatureAzimuth0001` − outside dew point (fallback `MTCamera.utiltrunk_UT.coolPipeSplyTemp − 1.5`) | ≤ +2 °C (2025-12-15 → 12-29); < +2 °C (12-30 → 2026-01-18); ≤ +1 °C (01-19); < −2 °C (01-20 →); all for 20 consecutive minutes; no rule before 2025-12-15 | by window |

A minute is CLOSE if any rule fires. Consecutive CLOSE minutes form windows; windows closer than 10 min are merged;
the windows are clipped to the −18° night and summed into `efd_weather_hours` (per-rule hours are kept too).

The Dynalene sensor choice: the 2025-12-21 night report quotes "Dynalene at Az −0.6 °C" at 03:01 UTC, and
`dynaleneTemperatureAzimuth0001` reads −0.62 at that minute (Pier0102 +1.2, Azimuth0002 +1.3). Azimuth0001 is also
within 0.3 °C of the handoff's predicted-TEA value over Dec–Jan, whereas Pier0102 is +1.5 °C warmer.

**Cloud.** The EFD has no cloud product, so rule B cannot see cloud closures. Each minute is also classified as
*physically closed* if the dome shutter (`MTDome.apertureShutter.positionActual0`) is below 50 %, or the telescope
is at horizon (`MTMount.elevation.actualPosition` < 5°) with the mirror covers closed
(`MTMount.mirrorCover.actualPosition0` > 60). Minutes physically closed inside the night with no rule firing are
summed into `closed_unexplained_hours`.

**C. Combination (`combine_weather`, then `reassign_unexplained_closures`).** From 2026-02-25, `weather_hours` =
`bit_weather_hours` and `weather_source` = "WEATHER bit". Before that, `weather_hours` = `efd_weather_hours` and
`weather_source` = "EFD criteria". Then, before 2026-02-25 only and only on nights where the night-report table
(Source 2, `data/step0/nightlog_source2_per_night.csv`) gives P(weather) ≥ 0.5, `closed_unexplained_hours` is moved
from `nonweather_loss_hours` into `weather_hours` (capped by the available loss), recorded in
`cloud_reassigned_hours`, and `weather_source` becomes "EFD criteria + night report (cloud)". This is Bruno's
option 2 (2026-10-18): the night reports are used exactly where telemetry is blind and nowhere else. 18 nights,
46.7 h.

### Per-night arithmetic (`accounting.py`, notebook 04)

With N = the −18° night, W = the weather windows of the primary source, S = the on-sky windows:

```
weather_hours           = |W ∩ N|
on_sky_hours            = |S ∩ N|
weather_and_onsky_hours = |W ∩ S|          observing while the bit/criteria said closed; reported only
nonweather_loss_hours   = |N| − |W ∪ S|    fault + idle + planned off-sky + staffing, bundled
```

Weather and non-weather loss cannot overlap because the loss is what remains after removing the union of both
window sets from the night. The three categories plus the overlap therefore sum to the night:
`on_sky + weather − weather_and_onsky + nonweather_loss = night_hours_18`. The cloud step then moves hours between
`weather_hours` and `nonweather_loss_hours` without changing the sum.

`label` is the handoff's presentation rule: CLOSED if `on_sky_hours` < 0.5 h; else OPEN if total loss is below
10 % of the night; else WEATHER-DOMINATED or FAULT-DOMINATED by whichever loss is larger. It is not a definition.

### Cross-check (notebook 05)

The two human tables and the narrative log are joined on `day_obs` and compared with the code table; disagreement
classes are listed, never averaged. `confidence` per night is HIGH when the code label is consistent with both
human sources, MEDIUM with one, LOW when it contradicts both or no source exists.

### Not in these numbers

Cloud before 2026-02-25 on nights where Source 2 gives P(weather) < 0.5 (stays in non-weather loss); the five
Dec–Jan nights where the Dynalene rule fires but the observers judged no weather loss (stay in weather);
image-quality-only losses (telescope on sky, data unusable, e.g. 2026-04-24); the 2026-07-15 → Oct storm DOWNTIME
(outside the range); AuxTel.

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

1. Folder name: created as `simonyi_time_loss/` at the repo top level (the repo has no
   `investigations/` prefix and no `summit_performance/`; the siblings are
   `observatory_high_level_performance/` and `nightly_survey_speed/`). Rename if preferred.
2. (done — all human-table files received 2026-10-18.)
3. Decided 2026-10-18: `gap_min` = 10 min; pre-bit cloud via night reports (option 2); Dynalene sensor
   `dynaleneTemperatureAzimuth0001`. Still open: the weather-night label threshold (figure uses the §1b rule).
4. Whether the five Dynalene-rule nights the observers judged as non-weather (README §3b) should keep the
   EFD attribution or be overridden from the reports, as was done for cloud.
