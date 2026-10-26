# notebooks_bquint

Bruno Quint's Rubin Observatory commissioning engineering analyses. Each investigation is a
self-contained folder (`notebooks/`, `python/`, `data/`, `plots/` as needed) so it can be
extracted into its own technote repo.

## Start here (Performance Hub, October 2026)

Three folders are relevant to the Survey Performance work. The first two rebuild figures from
`lsst/sp_notebooks` for the RASAB 2026 talk, with the goal of an interactive version, a clear
account of what the metrics are made of, and a presentation look. The third is a per-night
weather vs. fault accounting that includes human-read sweeps of the night logs and the morning
tailgate notes. Each folder README is a technical note: provenance, data, definitions,
differences from the original, caveats, how to run it on USDF.

| Folder | Based on | What is there | Look at |
|---|---|---|---|
| [`nightly_survey_speed/`](nightly_survey_speed/) | `on-sky_utilization.ipynb` (Keith Bechtol, Brian Stalder) | Bokeh version of the visit timeline with hover and switchable options (exclusive categories, real exposure bars, local-time axis, auto y range); downtime annotation layer from a curated CSV of fault and weather closures with FRACAS tickets; per-night hours by category | [talk figure](nightly_survey_speed/plots/utilization_annotated_talk_white.png), [README §4 what the categories and axes mean](nightly_survey_speed/README.md#4-definitions), [README §7 caveats](nightly_survey_speed/README.md#7-caveats-for-anyone-presenting-this-plot), [downtime_annotations.csv](nightly_survey_speed/downtime_annotations.csv), [downtime_summary.md](nightly_survey_speed/plots/downtime_summary.md) |
| [`observatory_high_level_performance/`](observatory_high_level_performance/) | `diq_vs_visit_rate.ipynb` (Lynne Jones) | Binned points on the survey speed vs. iDIQ plane (Early Ops window vs. LSST window; fiscal quarters; months), interactive and static; every reference number in `ohlp/reference.py` with its source; speed as ratio of sums over all calendar nights, weather nights counted not removed; Rubin palette | [talk figure](observatory_high_level_performance/figures/speed_vs_iq_static_early_ops_vs_lsst_20251024-20260714_white.png), [README §5 binned-point definitions](observatory_high_level_performance/README.md#5-definitions-of-the-binned-points), [README §6 reference values](observatory_high_level_performance/README.md#6-reference-values-drawn-on-the-figure), [README §10 open items](observatory_high_level_performance/README.md#10-caveats-and-open-items) |
| [`simonyi_time_loss/`](simonyi_time_loss/) and [`nightlog_weather_fault_loss/`](nightlog_weather_fault_loss/) | Observatory Status WEATHER bit, EFD weather telemetry, ConsDB visit coverage, night reports, tailgate notes | Per-night hours of survey / engineering / weather / fault + idle under the ROSP-24 precedence, 25 Oct 2025 to 14 Jul 2026. Two human-read sweeps, one row per night with status (OPEN / PARTIAL / CLOSED), judged P(weather) and P(fault), verbatim evidence and OBS tickets: the **morning tailgate notes** from Slack and the **night reports**. The night reports are also exported verbatim as a CSV | [nightly figure](simonyi_time_loss/figures/time_loss_nightly_talk_20251025-20260714.png), [per_night.csv](simonyi_time_loss/data/processed/per_night.csv), [tailgate sweep](simonyi_time_loss/data/raw/tailgate_sweep_ALL.md), [night-log sweep](simonyi_time_loss/data/raw/nightlog_sweep_2025-10_to_2026-07.md), [cross-check of the two](simonyi_time_loss/data/raw/crosscheck_S1_vs_S2_2025-10-25_to_2026-07-14.md), [verbatim night reports CSV](nightlog_weather_fault_loss/data/nightlog_simonyi_20251025_20260720.csv) |

Things learned about the metrics that may matter upstream:

- In `on-sky_utilization.ipynb`, Focus and Alignment visits (BLOCK-T539) are also drawn as
  Engineering, so the orange count is inflated; `BLOCK-T539_hexapods` and `BLOCK-365` fall into
  Engineering by exact matching; the y axis is hours after 00:00 UTC, not local midnight; the fixed
  y limits clip a few early-evening visits.
- `estimated_baseline_visit_range` assumes the whole night is available, while the "LSST = 1" star is
  calibrated on a simulation with cloud and downtime models on (hence 0.63). This is why weather
  nights are kept in the measured speed.
- The Observatory Status WEATHER bit exists only from 2026-02-25. Before that, and where FAULT or DOWNTIME
  masks the bit, weather closures come from the ROSP-24 §C fallback: Brian Stalder's allskycam cloud index
  (> 0.5) and the C1 weather-tower limits. Night reports are annotation only (since 2026-10-26).
- Reusable pieces, if wanted in `sp_notebooks` or `rubin_nights`: `nightly_survey_speed/utils.py`
  (ConsDB client with token or Postgres fallback, visit query, categorisation, twilight),
  `nightly_survey_speed/downtime_annotations.csv`, and the two sweep tables above.

The remaining folders are unrelated to this work.

## Index

| Folder | Topic | Ticket | Status |
|---|---|---|---|
| [`nightly_survey_speed/`](nightly_survey_speed/) | On-sky utilization timeline (visits per night by program) reproduced from sp_notebooks, interactive version, downtime annotations (RASAB 2026 figure) | — | Done |
| [`simonyi_time_loss/`](simonyi_time_loss/) | Simonyi night time lost to weather vs. faults per night (WEATHER bit, EFD weather criteria, ConsDB visit coverage; human tables as cross-check) | — | Step 0 done, accounting pending |
| [`nightlog_weather_fault_loss/`](nightlog_weather_fault_loss/) | Simonyi night-report summaries exported verbatim per night (weather vs fault time loss) | — | Export done, classification pending |
| [`efficiency_waterfall/`](efficiency_waterfall/) | Schematic efficiency waterfall: whole night → survey time → excluding faults → scheduler model → ideal (LSST@LATAM 2026 slide; inputs only, all `[VERIFY]`) | — | Superseded by `night_efficiency_brackets/` |
| [`night_efficiency_brackets/`](night_efficiency_brackets/) | One night (8 Jul 2026) on its side with the efficiency denominators drawn as brackets: whole night, minus weather, minus faults, on sky (LSST@LATAM 2026 slide) | — | Done |
| [`visit_gap_anatomy/`](visit_gap_anatomy/) | Time between consecutive survey visits: histogram vs the 5 s requirement, weekly median, second-settle population (LSST@LATAM 2026 slide) | RSO-785 | Done |
| [`engineering_time_budget/`](engineering_time_budget/) | On-sky hours per week by visit category against the 8 h/week engineering policy line (LSST@LATAM 2026 slide) | — | Done, policy numbers to verify |
| [`observatory_high_level_performance/`](observatory_high_level_performance/) | Survey speed vs. delivered image quality, best two weeks of Early Ops vs. first two weeks of LSST, and by fiscal quarter (RASAB 2026 figure; interactive, talk, paper versions) | — | WIP |
| [`zephyr_scale_analysis/`](zephyr_scale_analysis/) | Test cases per cycle, steps and versions per test case in Zephyr Scale (SPIE paper/poster) | — | Done |
| [`dimm_data_quality/`](dimm_data_quality/) | DIMM seeing bias under low flux/wind; cross-check vs. ConsDB donut blur | RSO-656 | WIP |
| [`night_failures/`](night_failures/) | CSC faults and script failures per night | RSO-544 | WIP |
| [`mthexapod_warmup/`](mthexapod_warmup/) | Camera hexapod warm-up: strut motor currents vs. commands, inPosition and error logs | — | WIP |
| [`image_quality_trending/`](image_quality_trending/) | Per-visit image-quality trends from ConsDB | — | WIP |
| [`rasab_image_quality_highlights/`](rasab_image_quality_highlights/) | Best delivered-IQ visits (Oct–Dec 2025, May–Jul 2026) and a good-FWHM / bad-ellipticity visit (Feb–Mar 2026) for the RASAB 2026 narrative; reproducible ConsDB script | — | Done |
| [`focus_offset_temperature/`](focus_offset_temperature/) | Initial focus offset vs. truss temperature | RSO-87 | WIP |
| [`seeing_length_scale/`](seeing_length_scale/) | Correlation length scale of atmospheric seeing (PCA) | RSO-36 | WIP |
| [`tma_slew_velocities/`](tma_slew_velocities/) | TMA maximum slew velocities | — | Done |
| [`tma_tdms_reader/`](tma_tdms_reader/) | TMA TDMS → CSV converter | — | Stub |

## Running the notebooks locally

The notebooks need the LSST Science Pipelines. Install them with
[lsstinstall and eups distrib](https://pipelines.lsst.io/install/lsstinstall.html)
(you may need `sphinx` and `rust` from conda first), then install `lsst_sitcom` on top:

```zsh
mkdir -p ~/lsst_stack && cd ~/lsst_stack
curl -OL https://ls.st/lsstinstall
chmod u+x lsstinstall
./lsstinstall -T w_2026_15
source ~/lsst_stack/loadLSST.zsh
eups distrib install -t w_2026_15 lsst_distrib
eups distrib install -t w_2026_15 lsst_sitcom
```
