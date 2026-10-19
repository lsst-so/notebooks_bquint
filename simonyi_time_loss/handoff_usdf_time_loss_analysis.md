# Handoff — Simonyi time loss (weather vs fault), Oct 2025 → Jul 2026
**For the USDF Claude session (EFD/ConsDB access). Draft 2026-10-17, updated 2026-10-18 after the Source 1 / Source 2 cross-check and Bruno's decisions on the per-night accounting (Section 1b).**

You are helping me (Bruno Quint, Rubin Summit Support Scientist) quantify how much Simonyi night time was lost to weather versus faults between the start of Early Operations (2025-10-25) and the last night on sky before the winter storm (2026-07-13). This feeds two talks (RASAB 2026, Natal, 25 Oct; LSST@LATAM, São Paulo, Nov) and a later paper figure. I mostly need defensible numbers and an honest statement of their uncertainty.

Read everything below before writing code. Report back after Step 0. Don't invent, don't push, cite every number to its source, ask me when something is missing.

---

## 0. Where this lives — repo layout

Repo: `lsst-so/notebooks_bquint` on USDF. This is a new investigation, sibling of `summit_performance/` and `observatory_high_level_performance/`. Proposed name: `investigations/simonyi_time_loss/` (rename if Bruno prefers). Create it before any analysis; nothing goes outside it.

```
investigations/simonyi_time_loss/
├── README.md              # tech-note style: purpose, the three numbers (Section 1b), night definitions, data sources
│                          #   and their date ranges, parameters (gap_min, thresholds), how to rerun, figure list
├── ai_notes.md            # running log of what the Claude session did, decided, and left open; update every session
├── handoff_usdf_time_loss_analysis.md   # this file, as received
├── data/
│   ├── raw/               # inputs as received: nightlog_simonyi_20251025_20260720.csv, manual_notes.csv,
│   │                      #   tailgate_sweep_ALL.md, nightlog_sweep_2025-10_to_2026-07.md,
│   │                      #   crosscheck_S1_vs_S2_*.md, weather_criteria_table.md
│   └── processed/         # per-night table (parquet + csv): day_obs, night_hours_18, night_hours_12, weather_hours,
│                          #   weather_windows, on_sky_hours, nonweather_loss_hours, n_visits, label, provenance
├── time_loss/             # small package shared by the notebooks
│   ├── nights.py          # ephemeris: −18° and −12° limits per day_obs
│   ├── weather.py         # WEATHER-bit windows; EFD thresholds with validity windows (Section 5)
│   ├── visits.py          # ConsDB visit1 coverage per night, gap detection, on-sky vs in-dome
│   ├── accounting.py      # combines the three into the per-night table
│   └── style.py           # imports the repo palette (do not redefine colours)
├── notebooks/
│   ├── 00_step0_data_coverage.ipynb   # what exists for which date range, per source (Section 9 guardrail)
│   ├── 01_night_limits.ipynb
│   ├── 02_weather_windows.ipynb
│   ├── 03_visit_coverage.ipynb
│   ├── 04_per_night_table.ipynb       # builds data/processed, prints it for spot-checks
│   ├── 05_crosscheck_vs_human_tables.ipynb
│   └── 06_figures.ipynb               # talk and paper versions
└── figures/
```

Rules: use the repo's existing palette; same per-night table feeds every figure; `ai_notes.md` is the handoff for the next session; don't commit or push without asking.

---

## 1. The two questions

**Q1 — Which nights or windows were closed because of weather, with a confidence that the attribution is right?**
Approach: (a) replicate the existing observatory-state WEATHER-bit count (Section 4, Lynne's snippet) as the reference; (b) independently flag windows where EFD weather telemetry violated the operating criteria (Section 5) during the night; (c) compare both with the two human-judged tables (Section 6). Agreement between the three gives the confidence.

**Q2 — How much time was lost to faults, per fault, per night?**
Deferred. Time loss is accounted per OBS ticket (Bruno, 2026-10-18: "this is how we are intended to account for time loss"). Design it after Q1 and Section 1b work. Not needed for the talks.

Scope: Simonyi only, 2025-10-25 → 2026-07-14 (last night with the dome open; the partial October is included). Night: two definitions carried side by side (Bruno, 2026-10-18) — **−18° to −18°** is the operational night and the one the loss accounting uses (initial alignment starts as early as possible, in astronomical twilight); **−12° to −12°** is kept for comparison with Lynne's expected-visits model (`rubin_nights.dayobs_utils.estimated_baseline_visit_range` uses −12° twilights — confirm). Chilean nights span two UTC dates: always bucket by `day_obs`, never by UTC calendar date.

## 1b. Per-night accounting (decided 2026-10-18) — this is the deliverable

The human tables' OPEN/PARTIAL/CLOSED label is too coarse: almost every night has some fault loss, so "PARTIAL" carries no information (the cross-check found 41 nights where Source 1 says PARTIAL and Source 2 says OPEN for exactly this reason). Status becomes a derived label; the measured quantity is **hours per night**, in three numbers:

1. **`night_hours_18`** and **`night_hours_12`** — hours between sun altitude −18°/−18° and −12°/−12°, from ephemeris. No judgement. The accounting below runs on the −18° window; the −12° column is reported alongside so totals can be compared with the efficiency plots.
2. **`weather_hours`** — hours inside the night when the observatory was closed (or not observing) because of weather. Determined **by code on USDF, not from the human tables**: primary = the Observatory Status WEATHER bit (from 2026-02-25); before that, and as a cross-check, = EFD weather telemetry vs the Section 5 thresholds with their validity windows. Rationale: weather changes slowly, so a night has a few transitions (open→close, close→open, maybe one more), not many; a window-level answer is adequate. Output the window(s) (UTC start/end) as well as the hours.
3. **`nonweather_loss_hours`** — everything else: `night_hours_18 − weather_hours − on_sky_hours`, where `on_sky_hours` is time covered by Simonyi visits in ConsDB (`visit1`, bucketed by `day_obs`). This bundles **fault + idle**. For the talks it is reported as "fault" (Bruno's decision); splitting fault from idle is per-gap work for later (Q2).

Parameters (state them in the output, don't hide them):
- Gap threshold: a gap between consecutive visits longer than `gap_min` counts as loss (propose 5 min; report sensitivity at 2/5/10 min).
- Engineering/calibration visits: count on-sky engineering as on-sky (it is not loss); in-dome calibrations are not on-sky. This matters most in the −18° → −12° twilight, where alignment, AOS closed-loop and pointing visits are the expected activity.
- Weather and non-weather windows must not overlap: subtract weather windows first, then compute gaps in the remainder.

Role of the human tables after this: Source 1 and Source 2 become **cross-checks**, not inputs. For each night, compare (a) the code's weather window with the tables' P(weather) and stated clock times, and (b) `nonweather_loss_hours` with the hours the logs state ("~2 h CCW", "lost ~45 min"). List disagreements; don't average. The derived label for the figure can be: CLOSED if `on_sky_hours` < 0.5 h; else WEATHER-DOMINATED / FAULT-DOMINATED by whichever loss is larger; else OPEN if total loss < 10% of `night_hours_18`. Treat that as a presentation rule, not a definition.

---

## 2. Definitions (what the observatory states mean)

Source: #survey-performance thread started by Bob Blum, 2026-09-15 (Lynne Jones, Brian Stalder, Robert Lupton replies); #ssw-logging, Robert Lupton 2026-10-09; Scot Kleinman 2026-10-09. `[check: permalinks]`

- There is **no agreed definition of a "weather night"**. ROSP-11 (time-loss accounting) is On Hold; ROSP-24 (Brian, 2026-10-10) drafts a taxonomy where the EFD Observatory Status WEATHER bit is primary and all-sky cam / weather-tower limits are the fallback; narrative log is "annotation only".
- **WEATHER** is an independent state layered on the others (can be true while OPERATIONAL, FAULT, etc.). **DOWNTIME** masks fault/operational, and Brian notes "DOWNTIME may be masking some WEATHER events." OPERATIONAL is not orthogonal to WEATHER (Lupton).
- **DOWNTIME** (Scot Kleinman): declared by management when the telescope is shut down for maintenance, repair, or recovery from natural disasters. The July storm and site-access loss were logged as DOWNTIME.
- Observatory-state flags exist only from **~March 2026** (WEATHER bit deployed 2026-02-25). Before that, only the narrative log, which was inconsistent before ~mid-Jan 2026 (Anastasia Alexov tightened guidance 2026-01-14/15: use START/END tracker for all time loss; condensation counts as fault).
- Lynne's crude weather-night rule: WEATHER hours / night hours > 0.3. Ad hoc alternatives seen: >70% (Lynne), >80% (Erik Dennihy). None agreed.
- NSF quarterly KPI = Operational / (Operational + Fault), ignoring planned downtime and weather.
- Nightly Digest Time Accounting (dev: https://usdf-rsp.slac.stanford.edu/nightlydigest) computes fault three ways: observatory statuses; narrative-log declared faults; "calculated" = total night − MIN(weather time, dome-closed time) − (exposure time + overhead up to 2 min/visit). Lupton (2026-08-14): the calculated fault ignored DOWNTIME. Timestamp handling: https://github.com/lsst-sims/rubin_nights/blob/main/rubin_nights/logging_query.py (~L456).
- Known disagreement example (2026-04-28): narrative log 4.08 h weather vs Observatory Status 2.27 h WEATHER + 2.60 h FAULT.
- Cheat sheet (possibly outdated): https://rubinobs.atlassian.net/wiki/spaces/LSSTCOM/pages/1669857371
- Weather-recovery time (e.g. ice on the dome after a storm) is not captured by any state.

---

## 3. Reference numbers already in circulation (verify before use)

| Metric | Value | Source |
|---|---|---|
| Night hours Mar–Jul 2026 | 1063 h total: 413 science, 59 on-sky eng, 231 weather, 126 fault, 199 downtime (overlapping) | Lynne, #survey-performance, 2026-07-18 |
| 2026-03-01 → 07-19 | 1301 night hours not-weather vs ~1073 historical mean | Lynne, same thread |
| Long-fault nights | 27 observed vs 2 in model (of 92) | Lynne efficiency deck |
| Weather closure overall | ~28–30% | Bianco/Jones JOR breakout |
| Cloud study | all-sky cam Jul 2021–Jul 2026 vs meteoblue/CTIO/DREAM; 0.5 cloud threshold matches open times; Rubin ~5–9% less cloudy than CTIO model | Brian Stalder, #survey-performance, 2026-10-04 |

---

## 4. Code starting point (Q1a)

Lynne's snippet, works on any RSP:
```python
from rubin_nights import connections
import rubin_nights.dayobs_utils as rn_dayobs
import rubin_nights.observatory_status as rn_observatory
endpoints = connections.get_clients()
t_start = rn_dayobs.day_obs_to_time(20260415)
t_end   = rn_dayobs.day_obs_to_time(20260715)
obs_status = rn_observatory.get_observatory_state_times(t_start, t_end, endpoints['efd'])
obs_status, obs_summary = rn_observatory.count_observatory_states(obs_status, None)
```
Related: `rubin_nights` (lsst-sims), `ts_logging_and_reporting` (Nightly Digest code), ROSP-11 `fault_downtime.ipynb` `[check: location]`, `sp_notebooks/efficiency.ipynb` (narrative-log `time_lost_type`).

---

## 5. Weather criteria (Q1b) — thresholds with validity windows

Primary source: Confluence "Weather Constraints", OOD page 39696225, v29 (2026-10-14, Draft). Secondary: "Temporary Guidelines – LSSTCam on-sky", OOD page 630095945, v198.

| Quantity | EFD/ESS source `[check: exact topic/field]` | Open | Monitor / borderline | CLOSE | Valid from |
|---|---|---|---|---|---|
| Wind gusts | weather tower ESS | < 15 m/s | 12–15 monitor; 15–20 borderline (dust counters ESS:127/128/129) | 20 m/s average or 25 m/s sustained gusts; re-open after ≥ 15 min under 20 | `<<date>>` |
| Ambient − dew point (outside) | ESS:301 outside dew point | > 5 °C | ~5 monitor; 2.5–3 borderline | 2 °C, or any sensor within 2 °C for ~20 min → close, telescope to horizon | `<<date>>` |
| Dynalene − dew point | `lsst.MTCamera.utiltrunk_ut.CoolPipeSplyTemp` − 1.5 °C (predicted Dynalene) vs ESS:111 inside dew point | > 0 | ~0 monitor; −1 to −2 borderline | < −2 for ~20 min; before opening, outside dew point must be ≥ 2 °C below Dynalene | `<<date>>` |
| Humidity | — | de-prioritized; dew-point difference is final (older text: don't open if RH > 70%) | | | superseded `<<date>>` |
| Precipitation probability | forecast | < 5% | | | |
| Expected lowest temp − dew point | forecast | > 5 °C | | | |
| Cloud | visual / all-sky | not heavy/dark; east peak visible | | re-open at night only if stable 30 min AND > 1 h before sunrise | |
| M1M3 | mirror temp vs internal dew point | | | fans off and mirror within 2 °C of internal dew point → close | |
| Cryo hex return temp | | | | < dome dew point for ≥ 10 min = frost risk | |
| Dome closure at −12° twilight | | | | BLOCK-T196 | |

Formula used on the summit: T_dew = T − (100 − RH)/5. Dashboards: Chronograf 707 (MTDome Weather Monitor), 327, 572 (cryo leading indicators); LOVE weather view id=123.

**Time dependence (important):** during Dec 2025 – Jan 2026 water condensed on the TEA Dynalene lines (FRACAS-330), and much stricter humidity/dew-point rules were applied (dome closed when T − T_dew < 2 °C; Dynalene setpoint raised; lines insulated). `<<TODO: pull the exact thresholds and dates from the page history of 630095945 / 39696225 and #summit-announce; until then treat Dec 2025–Jan 2026 as a separate criteria window and flag it.>>`

Winter plan (Apr–Aug): precipitation emails from Fabrizzio Bruno. AuxTel constraints: https://obs-ops.lsst.io/Observing-Constraints/AuxTel/index.html (not needed here).

How to use: for each night, compute the fraction of −12°→−12° time where any CLOSE criterion valid on that date was met; flag windows; compare with WEATHER-bit intervals and with the dome-shutter state.

---

## 6. Human-judged tables (Q1c) — two independent sources, same columns

Both tables use these columns (full definitions in each file's header): `day_obs | note (link) | status OPEN/PARTIAL/CLOSED/UNKNOWN | P(weather) 0–1 | P(fault) 0–1 | evidence (verbatim) | tickets`. P values are reading judgements, not measurements; they need not sum to 1. Power glitches are counted under fault and flagged in the evidence.

**Source 1 — Morning Tailgate notes** (#summit-announce threads, one note per weekday, Monday covers Fri–Sun):
- All nine files done: `tailgate_sweep_2025-10-11.md`, `2025-12.md`, `2026-01.md` … `2026-07.md` (Oct 24 → Jul 14, 264 rows). Concatenated by Bruno as `tailgate_sweep_ALL.md`.

**Source 2 — Night logs** (rubin-night-log mailing list, one HTML report per morning, also posted in #nightlog-bot C07TCUJGB1U):
- Export: `nightlog_simonyi_20251025_20260720.csv` produced on USDF from `prompt_usdf_nightlog_export.md` on 2026-10-18 (269 nights; columns: day_obs, report_found, date_sent, summary, weather_summary, simonyi_summary, auxtel_summary, obs_tickets, submitted_by, nightly_digest_url). `report_found = false` for 2026-04-28 → 05-05 and 2026-07-01/02 (OBS-2000 database outage).
- Judged table: `nightlog_sweep_2025-10_to_2026-07.md` — done 2026-10-18 (263 rows, Oct 25 → Jul 14, month by month with `prompt_nightlog_sweep_month.md`).

**Cross-check Source 1 vs Source 2** (`crosscheck_S1_vs_S2_2025-10-25_to_2026-07-14.md`, script `crosscheck_sources.py`, 2026-10-18):
- Status agrees on 171/263 nights. 53 real disagreements, 41 of them S1 PARTIAL vs S2 OPEN (the tailgate lists faults without hours; see Section 1b for why this label is dropped as a measurement). Others: S1 OPEN vs S2 PARTIAL ×7, S1 PARTIAL vs S2 CLOSED ×3, S1 CLOSED vs S2 PARTIAL ×1, S1 CLOSED vs S2 OPEN ×1.
- 30 Source 1 UNKNOWN nights are resolved by Source 2. Still UNKNOWN in both: **2026-04-30** only. Source 2 UNKNOWN where Source 1 judged: 2026-04-28 → 05-05 and 2026-07-01/02 (no night report) — use Source 1 there.
- Weather-vs-fault attribution flips (one source weather, the other fault) worth a look against telemetry: 2025-10-31, 11-06, 12-06, 12-14; 2026-01-16, 03-14, 04-27, 06-01, 06-15, 06-16, 07-03.
- Both OPEN but P(fault) 0 vs 1.0 (a fault logged with no loss): 2025-11-17, 11-28; 2026-02-28, 05-26. Irrelevant for status, relevant for Q2.

Use: join both tables and the code results on `day_obs`. The code's `weather_hours` / `nonweather_loss_hours` are the numbers; the tables are the audit trail. Nights where all three agree are high confidence; disagreements get listed, not averaged.

---

## 7. Known pitfalls
- Bucket by `day_obs`; ConsDB `obs_start` is TAI.
- Observatory-state data starts ~Feb/Mar 2026; before that rely on narrative log + the human tables.
- FAULT and DOWNTIME overlap; the storm period (2026-07-13 → Oct) is DOWNTIME and outside this range.
- The scheduler's 120 s filter change excludes the slew.
- Narrative-log entries before Jan 2026: duplicates, daytime entries, AuxTel-only reporting (Alysha Shugart 2025-11-14; Lynne 2025-11-23, 2025-12-17).
- The Nightly Digest and `rubin_nights` use different fault definitions; name which one every number comes from.

---

## 8. Open questions for Bruno (list, don't guess)
Answered 2026-10-18: night limits −18°/−18° for accounting, −12°/−12° reported alongside; include partial Oct 2025; range ends 2026-07-14; Q2 accounted per OBS ticket (deferred); weather window is decided by code, not by the human tables; fault + idle reported together as "fault" for the talks.

Still open:
1. Weather-night threshold for a per-night label (0.3 / 0.7 / 0.8)? Default: report hours and the full distribution; the label is only for the figure (Section 1b rule).
2. Gap threshold `gap_min` (default 5 min) — confirm after seeing the sensitivity.
3. Condensation-era thresholds (Dec 2025 – Jan 2026) — now in `weather_criteria_table.md` by validity window; still to verify: date of the −18°→−12° dome-close change, pre-2026 wind thresholds, EFD topic names, Slack permalinks.
4. Confirm that Lynne's expected-visits model uses −12° twilights.

## 9. Guardrails
- No invented numbers; every figure cites a source (file, page, thread, or query).
- Report Step 0 (what data exists for which date ranges, per source) before any analysis.
- Don't commit or push without asking. Don't edit Lynne's or anyone else's notebooks; copy and adapt.
- Print per-night tables so I can spot-check against the human tables.
- Step 0 must include: date range of the WEATHER bit, of each EFD weather topic in Section 5, and of ConsDB `visit1` coverage; list nights with zero visits so they can be matched against CLOSED nights in the tables.

## 10. Files to attach to the USDF session
`tailgate_sweep_ALL.md` (or the nine month files), `nightlog_sweep_2025-10_to_2026-07.md`, `crosscheck_S1_vs_S2_2025-10-25_to_2026-07-14.md`, `weather_criteria_table.md`, `nightlog_simonyi_20251025_20260720.csv`, `manual_notes.csv`.
