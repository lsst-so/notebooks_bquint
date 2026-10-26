# AI notes — simonyi_time_loss

Running log of what the Claude session did, decided and left open. Append a dated entry per
session; newest last. The polished write-up is `README.md`; the specification is
`handoff_usdf_time_loss_analysis.md`.

## Context

Bruno Quint (Rubin Summit Support Scientist) wants defensible per-night hours of Simonyi time lost
to weather vs. everything else, 20251025 → 20260714, for RASAB 2026 (25 Oct), LSST@LATAM (Nov)
and a paper figure. Decisions already taken by Bruno (2026-10-18, handoff §1b/§8): −18° night for
accounting with −12° alongside; weather window decided by code (WEATHER bit, EFD thresholds), not
by the human tables; fault + idle reported together as "fault"; Q2 (per-OBS-ticket loss) deferred.

## Decisions taken in-session

- **Folder is `simonyi_time_loss/` at the repo top level**, not `investigations/simonyi_time_loss/`:
  the repo has no `investigations/` prefix (CLAUDE.md: one top-level folder per investigation).
  Bruno to confirm or rename. Nothing was written outside it except the repo README index row.
- Step 0 probe outputs go to `data/step0/`, not `data/raw/` (raw = inputs as received only).
- "On-sky visit" for coverage = `visit1.airmass > 0` (keeps `engtest`; drops bias/dark/flat/CBP).
  Narrower than the on-sky-utilization figure's `img_type` filter, by design (handoff §1b: on-sky
  engineering is not loss).
- Narrative-log `day_obs` = `date_begin` − 12 h → date (API has no day_obs field).
- `time_loss/access.py` wraps `rubin_nights.connections.get_clients()`; it sets `ACCESS_TOKEN_FILE`
  from `~/.token_file` because `rubin_nights` only looks at `~/.lsst/usdf_rsp`, `$ACCESS_TOKEN`,
  `$ACCESS_TOKEN_FILE` or `lsst.rsp`. Without it the narrative-log query silently returns 0 rows
  (the EFD still works via the segwarides credential fallback, ConsDB via Postgres).

## Findings worth remembering (Step 0, 2026-10-18)

- Observatory state records start 2026-02-25 13:09 UTC; WEATHER first set 2026-03-08. 134 of the
  263 nights have no state data at all. Every night from 20260225 has at least one record.
- WEATHER (≤ 20260714): 36 periods, 219.7 h, 33 nights, 18 with ≥ 6 h. Including the storm
  nights 20260715–19 it is 41 periods / 278.4 h.
- DOWNTIME and WEATHER both set for the whole night on 20260320, 20260615, 20260616 (exclusive
  states cover < 10 % of the night). 20260514 and 20260617 are partial versions of the same.
- ConsDB: 76 zero-on-sky-visit nights in 25 runs; 27 of them had the dome shutter > 50 % open at
  some point (mostly the Jan–Feb camera shutdown with the dome open for venting/tests).
- Dome shutter telemetry missing on 20260623–24.
- Narrative log: 501 time-lost entries, 62 weather. Jan–Feb "fault" hours include whole-night and
  multi-night entries (16–27 h per day_obs) from the camera shutdown — the field was used as a
  downtime tally there. 2026-04-28 reproduces the handoff's known example (4.08 h weather).
- `rubin_nights.dayobs_utils.estimated_baseline_visit_range` uses −12° twilights (read the source).
- EFD topic/field names for the Section 5 criteria are in README §3.5. Rain rate is too sparse to
  use; dust counters and all-sky camera are not in the EFD measurement list.
- `InfluxQueryClient.query()` accepts raw InfluxQL; `GROUP BY time(7d)` / `time(1d,12h)` work.
  `select_time_series` with `index=1` filters `salIndex`.

## Environment notes

- SDF login node (sdfiana034), VS Code. `source /sdf/group/rubin/sw/loadLSST.bash; setup lsst_distrib`
  → lsst-scipipe-14.0.0 (w_2026_42), rubin_nights 0.18.2, astroplan 0.10.1, nbconvert 7.17.
  `lsst.summit.utils` is not in lsst_distrib; not needed here.
- `~/.token_file` (usdf-rsp token, renewed 2026-10-17) works for ConsDB, EFD credentials and the
  narrative log. `~/.lsst/postgres-credentials.txt` + `PGPASSFILE` is the ConsDB fallback.
- Notebooks are executed headless with `jupyter nbconvert --execute --inplace` (~2 min for 00).
- The handoff's Slack permalinks and Confluence pages were not fetched (no access from here).

## Session log

### 2026-10-18 — Step 0 (Claude, Fable 5.1, via Claude Code on SDF login node)
- Read the handoff and the attached cross-check; inspected the sibling investigations
  (`observatory_high_level_performance/ohlp/data.py` already has WEATHER-bit and narrative-log
  fetch code; `nightly_survey_speed/utils.py` has the astroplan twilight table) and the repo
  conventions.
- Created the folder, copied the received inputs to `data/raw/`, saved the handoff text as
  `handoff_usdf_time_loss_analysis.md`.
- Probed all five sources (ConsDB, observatory state, narrative log, EFD weather topics, ephemeris)
  and wrote `notebooks/00_step0_data_coverage.ipynb`; executed it clean; outputs in `data/step0/`.
- Wrote `time_loss/{__init__,access,nights,style}.py` (ruff clean); README §3 holds the inventory.
- Added the folder to the repo README index. Nothing committed.
- Reported Step 0 to Bruno; waiting on the three missing files and the open items in README §5
  before writing `weather.py` / `visits.py` / `accounting.py`.

### 2026-10-18 (later) — Source 1 files and weather criteria received (Claude, Fable 5.1)
- Saved `weather_criteria_table.md` and `tailgate_sweep_2025-12.md` … `2026-07.md` to `data/raw/`; built
  `tailgate_sweep_ALL.md` (concatenation, file markers between months) and parsed all month files into
  `data/step0/tailgate_source1_per_night.csv` (229 nights; parser keeps the first file's row for the two
  nights that appear in two files). Cross-checked against the S1 column of the cross-check table: 105/105 match.
- Still missing from Bruno: `tailgate_sweep_2025-10-11.md`, `nightlog_sweep_2025-10_to_2026-07.md`.
- Note for `weather.py`: `weather_criteria_table.md` §B gives the Dynalene-vs-dew-point rule in five validity
  windows (none before 2025-12-15; ≤ +2 °C close 2025-12-15 → ~12-30; outside dew point ≥ 2 °C below Dynalene
  before opening 12-30 → 01-19; > +1 °C for 20 min ~01-19; ≥ −2 °C from 2026-01-20). Condensation closures may
  show as telescope-at-horizon / covers closed rather than dome closed, so mirror-cover and elevation telemetry
  are needed alongside the shutter. The table states the analysis night as −12° → −12°; the handoff §1b (decided
  later the same day) says −18° for accounting with −12° alongside. Following the handoff.

### 2026-10-18 (later still) — all human tables received (Claude, Fable 5.1)
- Saved `tailgate_sweep_2025-10-11.md` and the Source 2 concatenation; split the latter into ten month files
  `nightlog_sweep_<YYYY-MM>.md` so both sources have the same layout, then rebuilt both concatenations.
- Parsed both sources: `data/step0/tailgate_source1_per_night.csv` (264 nights) and
  `data/step0/nightlog_source2_per_night.csv` (263 nights). All 122 rows of the cross-check file match; agreement
  recomputed as 171/263. Nothing is missing from the human side now.
- Bruno asked what `gap_min` is used for; answered in chat (it is the threshold that turns inter-visit gaps in the
  ConsDB visit stream into `nonweather_loss_hours`; see handoff §1b). Default 5 min, sensitivity at 2/5/10.

### 2026-10-18 (evening) — decisions from Bruno (Claude, Fable 5.1)
- **gap_min = 10 min** "for now" (`time_loss.GAP_MIN_MINUTES`); sensitivity still reported at 2/5/10.
- **Pre-Feb-2026 weather hours come from EFD criteria**, with the Dynalene rule applied by validity window as laid
  out in `data/raw/handoff_dynalene_condensation_criteria_2025-12_2026-01.md` (received 2026-10-18). That file also
  asks that Dec 2025 – Jan 2026 condensation closures be reported as their **own category** (not merged into weather
  or fault), that mirror-cover and elevation telemetry be checked alongside the shutter (condensation holds were
  telescope-at-horizon, not necessarily dome-closed), and that I ask Bruno before picking a Dynalene sensor if
  `CoolPipeSplyTemp` and `dynaleneTemperaturePier0102` disagree by more than ~1 °C.

### 2026-10-18 (night) — visits module, Dynalene sensor check (Claude, Fable 5.1)
- `time_loss/visits.py` written and unit-tested. On-sky visit = `visit1.airmass > 0`; on-sky windows = union of
  [obs_start, obs_end] after bridging gaps ≤ gap_min; gaps > gap_min (interior and at the −18° edges) are loss windows.
  ConsDB MJDs are TAI and are converted to UTC (−37 s). Cache: `data/step0/visits_onsky_20251025_20260714.parquet`
  (97 777 visits, 187 nights). Coverage table at 2/5/10 min: `data/step0/visit_coverage_gapmin_2_5_10.csv`.
  Totals over the 263 nights (night_hours_18 total 2319.6 h): on_sky 1093 / 1212 / 1268 h at gap_min 2 / 5 / 10.
  Spot checks match the night reports (e.g. 2025-10-31 1.3 h on sky "last 1.5 hrs"; 2026-03-07 2.9 h "~3 hours";
  2026-06-26 10.9 h "~11.5h"; 2026-05-31 1.6 h "≈3.3 h on sky" — that one is low, worth a look).
- **Dynalene sensor comparison** (`data/step0/dynalene_candidates_10min_20251210_20260131.parquet`): relative to the
  handoff's predicted-TEA definition `coolPipeSplyTemp − 1.5`, `dynaleneTemperatureAzimuth0001` sits at −0.3 °C
  (p10/p90 −0.7/+0.2), while `dynaleneTemperaturePier0102` and `Azimuth0002` sit at +1.5 °C (90 % of samples differ by
  > 1 °C). `Pier0101` is dead (−131415). The handoff §6.5 says to ask Bruno if CoolPipeSplyTemp and Pier0102 disagree
  by > 1 °C — they do. Checking which sensor the night reports' "Dynalene_at_Az" is (2025-12-21 03:01 UTC = −0.6 °C).
- EFD facts for `weather.py`: `airFlow.speed` is a ~1.3 s sample and `maxSpeed` ≈ `speed` (no built-in gust statistic),
  so the 20 m/s "average" and 25 m/s "gust" tests need rolling windows computed here. `mirrorCover.actualPosition0`
  ≈ 135 closed / ≈ 2 open; `logevent_mirrorCoversMotionState.state` 0 = opened, 1 = closed, 2/3 = moving.
  `MTMount.elevation.actualPosition` and `mirrorCover` exist for the whole range (checked every 14 d).
  `HVAC.dynalene` only starts 2026-04-22; `HVAC.dynaleneP05` reads all zeros in Dec 2025.
- Started `python/pull_efd_weather_1min.py` (background): 15 channels × 263 nights at 1-min cadence →
  `data/cache/efd_weather_1min.parquet`. `data/cache/` to be gitignored.
- **Dynalene sensor resolved**: the 2025-12-21 night report quotes "Dynalene at Az −0.6 °C" at 03:01 UTC; the EFD gives
  `dynaleneTemperatureAzimuth0001` = −0.62 at that minute (Pier0102 = +1.2, Az0002 = +1.3, sply−1.5 = −0.3). So the
  observers were reading Azimuth0001, which is also the sensor closest to the handoff's predicted-TEA definition.
  `weather.py` uses `dyn_az1` with `sply − 1.5` as fallback. Pier0102 is +1.5 °C warmer and is NOT used; flagged for Bruno
  per handoff §6.5. (The quoted outside dew point −0.7 °C does not match ESS:301 = −2.3 at that minute; the operators
  may have read a different dew-point display. Not resolved.)
- `time_loss/weather.py` written: EFD CLOSE rules (wind 10-min mean > 20 or sustained gust ≥ 25 with 15-min reopen
  hysteresis; outside spread < 2 °C for 20 min; Dynalene − dew point by validity window), WEATHER-bit windows clipped to
  −18°, `combine_weather` picks the bit from 20260225 and the EFD criteria before. Reports `closed_unexplained_hours`
  (shutter closed or telescope at horizon with covers on, no criterion met) because **cloud is not in the EFD**.
- `time_loss/accounting.py` written; first end-to-end run → `data/processed/per_night_v0.csv` (+ `_with_human.csv`
  joined to both human tables). gap_min 10, −18° night, weather = WEATHER bit from 20260225 else EFD criteria.
  Totals: night 2319.6 h, weather 298.1 h, on-sky 1267.6 h, non-weather loss 776.1 h, weather∩on-sky 22.2 h.
  Labels: FAULT-DOMINATED 89, CLOSED 82, OPEN 70, WEATHER-DOMINATED 22.
- **Key finding — cloud is invisible to the EFD criteria.** On the 140 nights where both exist, the WEATHER bit gives
  203 h and the EFD criteria 5.7 h; 21 nights have bit ≥ 2 h with EFD < 0.5 h, all cloud closures per the night
  reports. So before 2026-02-25 the EFD criteria capture humidity/dew-point/wind/condensation but not cloud, and cloud
  nights (Dec 5, Dec 7, Nov 6 …) fall into non-weather loss. `closed_unexplained_hours` (dome shut or telescope at
  horizon with covers on, no criterion met) totals 181 h in the EFD-criteria era, 47 h of it on nights where Source 2
  gives P(weather) ≥ 0.5. Needs Bruno's decision (reported in chat).
- Code CLOSED (on-sky < 0.5 h) agrees with Source 2 CLOSED on 75/75 nights; zero nights are code-CLOSED and S2-OPEN.
- Dynalene rule fires on 4 nights both human sources call non-weather (2025-12-18, 12-29, 2026-01-18, 01-19); on
  01-19 the observers overrode the criterion after inspection and observed 7.1 h. Reported as `efd_dynalene_hours`
  (own column, per the condensation handoff) and as `weather_and_onsky_hours` overlap.

### 2026-10-18 (late) — Bruno chose option 2 for pre-bit cloud (Claude, Fable 5.1)
- `accounting.reassign_unexplained_closures`: before 20260225, `closed_unexplained_hours` moves into `weather_hours`
  only when Source 2 P(weather) ≥ 0.5; capped by `nonweather_loss_hours`; recorded in `cloud_reassigned_hours`;
  `weather_source` becomes "EFD criteria + night report (cloud)". 18 nights, 46.7 h moved.
  → `data/processed/per_night_v1.csv`. Totals v1: weather 344.8 h, on-sky 1267.6 h, non-weather loss 729.4 h.
  Labels: FAULT-DOMINATED 84, CLOSED 82, OPEN 70, WEATHER-DOMINATED 27.
- Notebooks 01–06 written as thin wrappers over the modules and executed in order; 05 = cross-check (confidence per
  night), 06 = figures (talk + paper PNGs). Results and limitations in README §3b. Nothing committed.
- Wrote `HANDOFF_2026-10-18.md` (state, decisions, open items, how to resume) and README §3c "How the numbers are
  calculated" (method in words, rule table, per-night identity). Removed the interim `per_night_v1.csv` and
  `per_night_v0_with_human.csv`; `per_night.csv` is the deliverable, `per_night_v0.csv` the pre-cloud-step table.

### 2026-10-26 (evening) — ROSP-24 precedence re-run (Claude, Fable 5.1)
- Spec: `HANDOFF_rosp_precedence_2026-10-26.md` (saved in this folder). Step 0 reported first (allskycam coverage,
  C1 topics, Dynalene ∩ C1, masked periods, 8 Jul values), then the pipeline was changed.
- New modules: `intervals.py` (interval sets), `fallback.py` (allskycam `cloud_idx > 0.5` + C1 tower limits → windows,
  merged < 10 min, kept ≥ 10 min), `classify.py` (the ordered classifier; partition asserted per night to 0.5 s).
  Driver `python/run_rosp24_accounting.py` (5 s from the caches); `python/pull_allsky_cloud_1min.py` builds the
  1-min cloud cache. `accounting.py` is kept but no longer run; the pre-ROSP-24 table is
  `per_night_20261026_pre_rosp24.csv`.
- Interpretation choices beyond the handoff (all in README §3c): weather takes precedence over visits (9.1 h);
  fault-state minutes under a bridged survey window stay survey (D + E defined as the remainder); edge gaps ≤ 10 min
  are bridged in the category of the first/last visit; start-up allowance only on nights with a survey visit; the
  presentation label counts unattributed as loss; fallback windows need ≥ 10 min (sensitivity 1 h / 2.5 h).
- Allskycam vs night reports: the index confirms only 4 of the 19 report-cloud nights; 7 Dec (rain/hail precaution,
  clear night) and 13 Dec (chiller fault + humidity 60–70 %) are genuine disagreements with the ROSP-24 evidence
  hierarchy; the rest are Dynalene nights. Flagged in README §3.7 and §5.
- Tower RH `[check]`: ESS 301 RH reads 3–10 % on many winter nights; dew point 8 °C below the summit formula in winter.
- Palette: fault + idle = brand blue `#1C81A4` (validator: worst CVD 12.3, normal 15.5, all pairs PASS against survey
  green, engineering orange, weather grey). Python port of the dataviz validator used (`node` not on the login node).
- B10/B10b regenerated and pixel-compared with HEAD: identical; committed PNGs kept.
- Not done: gap_min sensitivity under the new classifier; B11 night re-selection under ROSP-24.
