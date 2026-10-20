# Observatory high-level performance: survey speed vs. delivered image quality

Technical note for the `observatory_high_level_performance` folder of `lsst-so/notebooks_bquint`.
Status: **WIP**. Interactive version done (2026-10-14; two-window and fiscal-quarter binnings); talk and paper versions pending.
Prepared for the RASAB 2026 talk (Natal, 25 Oct 2026) and as the base of a paper figure.

## 1. Purpose

One figure answers "is the observatory delivering the visits and the image quality that LSST
needs, and how has that changed since Early Operations began?" It places binned periods on a
**survey speed vs. image quality** plane, with a goal region and an "LSST = 1" star, and connects
them in time order. Two binnings are kept, from the same cache:

- **Two windows** (the presentation version): the *best two weeks of Early Ops* (16–29 Nov 2025,
  the 14-night stretch of Oct–Dec 2025 with the most survey visits) against the *first two weeks of
  LSST* (29 Jun–12 Jul 2026). Their nightly points are drawn as context.
- **Fiscal quarters** (FY starts in October: FY26 Q1 = Oct–Dec 2025, Q2 = Jan–Mar 2026, Q3 = Apr–Jun
  2026, Q4 = Jul–Sep 2026). A monthly binning is also produced but is too cluttered for presentation.

It rebuilds the per-night plot in Lynne Jones's `diq_vs_visit_rate.ipynb` (lsst/sp_notebooks) with
these bins, the Rubin colour palette, and three outputs that share one cached table. Weather nights
are counted, never removed (§5):

| Version | File | Status |
|---|---|---|
| Interactive (Bokeh) | `04_interactive.ipynb` → `figures/speed_vs_iq_interactive_<windows|quarterly|monthly>_<min>-<max>.html` | done |
| Static PNG (6×4 in, 12 pt labels, `TRANSPARENT` flag, optional `TITLE`, cropped to contents) | `03_static_png.ipynb` → `figures/speed_vs_iq_static_early_ops_octnov_20251024-20251130.png` (single Early Ops summary; titled, no direct label), `figures/speed_vs_iq_static_early_ops_vs_lsst_20251024-20260714.png` (Early Ops in teal + LSST on-sky stretch in purple, default; talk version; `_white` suffix = opaque background) or `..._<windows|quarterly|monthly>_<min>-<max>.png` (direct labels per period) | done (2026-10-17) |
| Static, talk (16:9, build frames) | `03_static_talk.ipynb` | pending |
| Static, paper (AAS column, PDF + PNG) | `02_static_paper.ipynb` | pending |

## 2. Contents

```
observatory_high_level_performance/
├── README.md
├── ohlp/                      # shared package
│   ├── reference.py           # every non-computed number, with its source
│   ├── data.py                # ConsDB / expected visits / weather → ../data/*.parquet
│   ├── binning.py             # per-night, per-quarter, per-month and per-window tables
│   ├── style.py               # imports ../rubin_color_pallete/rubin_palette.py; role → colour map
│   ├── interactive.py         # Bokeh figure builder
│   └── static.py              # matplotlib figure builder (PNG)
├── 01_data_and_binning.ipynb  # builds the cache, prints the per-quarter and per-window tables, cross-checks ConsDB
├── 03_static_png.ipynb        # matplotlib PNG version (same tables, same palette roles)
├── 04_interactive.ipynb       # Bokeh version
├── data/                      # parquet caches + windows_<tag>.csv, quarterly_<tag>.csv, monthly_<tag>.csv (visits parquet gitignored)
└── figures/                   # outputs (HTML gitignored; static PNGs committed)
```

Notebooks run from this folder (`sys.path.insert(0, ".")`). The only cross-folder dependency is
the palette module, resolved relative to `ohlp/style.py`; copy it into the folder before
extracting this investigation with `git filter-repo`.

## 3. Provenance

- **Source plot.** `notebooks/diq_vs_visit_rate.ipynb` in [lsst/sp_notebooks](https://github.com/lsst/sp_notebooks),
  read at commit `66e1baa` (2026-10-11). Written by Lynne Jones (first commit `90e7961`, 2026-02-03;
  last code change `b240f69`, 2026-02-20). Brian Stalder added narrative markdown (`c1417f0`).
  Lynne noted on 2026-10-12 that the reference is moving to `baseline_v5.3.4`, which moves the star,
  and that the plot "may be superseded by the newer ROSP metrics".
- **Library.** `rubin_nights` 0.18.2 from the `lsst_distrib` stack (`lsst-scipipe-14.0.0`,
  `d_2026_10_10`): `augment_visits` (seeing columns), `dayobs_utils.estimated_baseline_visit_range`
  (expected visits), `observatory_status.get_observatory_state_times` (weather). `rubin_scheduler`
  4.6.0 and `rubin_sim` are needed by `augment_visits`; `RUBIN_SIM_DATA_DIR` defaults to
  `/sdf/data/rubin/shared/rubin_sim_data`.
- **Palette.** `../rubin_color_pallete/rubin_palette.py` (Rubin Visual Identity Manual V7 hues,
  colour-blind checked).

## 4. Data

**Visits.** `cdb_lsstcam.visit1` LEFT JOIN `cdb_lsstcam.visit1_quicklook` on `visit_id`, with
`science_program IN ('BLOCK-365','BLOCK-407','BLOCK-408','BLOCK-416','BLOCK-417','BLOCK-419','BLOCK-421')`
(`rubin_nights.reference_values.SCIENCE_PROGRAMS`, as in the source notebook). No image-type or
airmass filter, no bad-visit exclusion. Columns kept are listed in `ohlp/data.py::VISIT_COLUMNS`.

**Image-quality statistics** (from `rubin_nights.rubin_scheduler_addons.add_rubin_scheduler_cols`):

| Column | Definition | Role |
|---|---|---|
| `fwhm_geom` | `psf_sigma_median × 2.355 × pixel_scale_median` | total delivered FWHM |
| `idiq_aos_cam` | `sqrt(aos_fwhm² + 0.207²)` | **default y**: the *instrument* contribution to the delivered image quality, iDIQ: optics (AOS estimate) + camera diffusion. Excludes atmosphere, dome/tube seeing and tracking |
| `fwhm_500_zenith` | `sqrt(atm_500_zenith² + idiq_aos_cam²)`, atmosphere scaled by airmass^0.6 and (500 nm / λ)^0.2 | delivered FWHM at a common reference |

**iDIQ vs. sDIQ** (Phil Marshall, 2026-10-20). *iDIQ* is the instrument contribution to the
delivered image quality and does not (purports not to) include dome/tube seeing. *sDIQ* is the
system contribution: everything except the atmosphere, so it does include dome/tube seeing. The
y axis of the figure is iDIQ; the ROST band (§6) is sDIQ. Axis labels and annotations must not call
the y axis "system" image quality. Note that RTN-093 labels its 0.45″ survey-start criterion
"sDIQ" while stating that it "excludes the dome seeing", i.e. it is an iDIQ-like quantity in Phil's
terminology; this README keeps RTN-093's name when quoting it.

`idiq_aos_cam` is the default because Lynne wrote "in general we trust the aos_fwhm version best"
(2026-02-20) and it is the panel she draws first. Coverage of `aos_fwhm` among survey visits is above
96 % in every month from Nov 2025.

**Expected visits per night.** `estimated_baseline_visit_range(day_obs)["n_vis_ave"]`: night length
between the -12° twilights × open-shutter fraction (0.74 − 0.02 cos(seasonal)) / 30 s, calibrated on
`baseline_v5.1.0_10yrs`. It assumes the whole night is available: downtime and weather are **not**
removed from the per-night denominator. They **are** in the reference: the "LSST = 1" star is the v5.1
10-year visit total divided by this estimator summed over 3650 nights, and the v5.1 run goes through
`rubin_scheduler`'s `ModelObservatory` with its defaults, i.e. the historical cloud database (observing
stops above a cloud fraction of 0.3, `cloud_limit=0.3`) plus the scheduled and unscheduled downtime
models (`ScheduledDowntimeData`, `UnscheduledDowntimeMoreY1Data`). The star sits at 0.63, not 1.0, for
that reason. Added to `rubin_nights` in commit `7ffa675` (2026-02-06); not an agreed reference (see §3).

**Weather.** Informational only; see "weather nights are counted, not removed" in §5. Per night, from two
sources:

- EFD Observatory Status `WEATHER` state hours (`get_observatory_state_times`), the primary source per
  the ROSP-24 draft taxonomy (Brian Stalder, 2026-10-10). Exists only from **2026-02-25**.
- Narrative log `time_lost_type == 'weather'` hours (annotation only per ROSP-24). Requires an RSP
  token; from an SDF login node the client returns nothing and the column is empty. Reporting before
  2026-01-15 was inconsistent.

A night is flagged a **weather night** when `weather_hours_efd / night_hours ≥ 0.7`. No threshold is
agreed (ROSP-11 is on hold); 0.7 is what Lynne Jones uses, Erik Dennihy uses 0.8. Before 2026-02-25 no
night can be flagged. The flag outlines the night in the nightly cloud and is counted per period
(`n_nights_weather`); it never changes the speed.

**Numbers for 20251024 to 20261014** (queried 2026-10-14 on the USDF Postgres replica): 356 calendar
nights, 152 with survey visits, 64 145 survey visits, 21 weather nights (all after 2026-03-20). No LSSTCam visit of any kind exists after `day_obs` 20260714 (storm, off sky).

## 5. Definitions of the binned points

- **Period** = fiscal quarter (`ohlp.binning.period_key(day_obs, "quarter")`, key
  `FY*10 + Q`, e.g. 261 = FY26 Q1). FY26 Q1 starts at 20251024, the first survey night (69 calendar
  nights, 45 with visits). FY27 Q1 runs to the query date and is empty. Months (`day_obs // 100`) are
  available with `period="month"`.
- **Single Early Ops summary** (`03_static_png.ipynb`, `PERIOD = "early_ops"`): one window
  20251024–20251130, the first survey night to the last night before the Dec 2025–Mar 2026 sequence
  of downtimes (water condensation, Dynalene loss, vacuum leak, earthquake; list in
  `nightly_survey_speed/plots/downtime_summary.md`). 38 calendar nights, 29 with visits, 4708 visits of
  28189 expected, speed 0.17 (nightly IQR 0.01–0.25), iDIQ median 0.459″ [0.418–0.517]. No weather
  state exists for these nights. Saved to `data/window_early_ops_octnov_20251024_20251130.{parquet,csv}`.
- **Early Ops vs. LSST** (`03_static_png.ipynb`, `PERIOD = "early_ops_vs_lsst"`, the talk figure):
  the Early Ops window above plus one window for the whole LSST on-sky stretch, 20260629–20260714.
  The end date is chosen to match Lynne Jones's `diq_vs_visit_rate` plot ("20260629 to 20260714") so
  that the two figures, which are shown side by side, give the same number; survey visits end on
  20260713 and 20260714 is a closed weather night (storm). 16 calendar nights, 10 with visits, 7267
  visits of 17273 expected, speed 0.42 (nightly IQR 0.00–0.73), iDIQ median 0.414″ [0.385–0.449].
  Three of the six closed nights (20260702–20260703, 20260714) carry the EFD WEATHER flag and stay
  in the count (see below for why). Ending on 20260713 instead gives speed 0.45. Checked against
  Lynne's figure 2026-10-17: the ten nightly points coincide; her near-zero points are the closed
  nights, which her notebook draws at the period-median iDIQ plus jitter and ours omits (no IQ
  exists for them); both include them in the speed. Her aggregate is the mean of nightly ratios,
  ours the ratio of sums; for this window they agree to 0.001. Early Ops keeps the brand teal, LSST is `CATEGORICAL[2]` purple (nights and
  whiskers in the same hue), passed to `build_static_figure(colors=...)`. Each window is described in
  the legend (`labels_in_legend=True`), so no direct labels are drawn. Saved to
  `data/windows_early_ops_vs_lsst_20251024_20260714.{parquet,csv}`.
- **Windows** (`ohlp.binning.window_table`, `period_kind = "window"`, `period` = window index) are
  named inclusive `day_obs` ranges with the same columns as a quarter. The two windows used:
  - *Best 2 weeks, Early Ops*, 20251116–20251129: the 14-night contiguous window of Oct–Dec 2025
    with the most survey visits (`ohlp.binning.best_window`, `by="n_visits"`; ranking by speed gives
    the same window, the runners-up are the same stretch shifted by one or two nights). 13 of 14
    nights have visits, 2491 visits of 9978 expected, speed 0.25, iDIQ median 0.467″.
  - *First 2 weeks, LSST*, 20260629–20260712: 14 nights from the season start. 9 of 14 nights have
    visits (2 of the closed nights are EFD WEATHER nights, 20260702–20260703), 6588 visits of 15128
    expected, speed 0.44, iDIQ median 0.410″. Survey visits stop on 20260713, so a 15-night window
    would add one more night (7267 visits, speed 0.45).
- **x, survey speed** = Σ visits / Σ expected visits over all calendar nights of the period. Closed
  nights count as zero visits. Chosen over the median of nightly ratios because it keeps lost nights
  in the number and is not driven by short partial nights. The x whisker is the 25–75 % range of the
  nightly ratios (so a period with many closed nights has a lower whisker at 0). Lynne's per-period
  point is instead the **mean of nightly ratios**; `ratio_median_nightly` is kept in the table.
- **y, image quality** = median of the statistic over all visits of the period; whisker = 25–75 %
  range over visits. Not a median of nightly medians.
- **Weather nights are counted, not removed** (decision 2026-10-17). An earlier version carried a
  second, "weather-excluded" series (hollow markers) that dropped the flagged nights from numerator,
  denominator and IQ distribution. It was removed because the reference it would be compared with
  already pays for weather: the "LSST = 1" star is calibrated on the v5.1 baseline simulation, which
  runs with the cloud and downtime models on (§4), so excluding weather from the measured speed would
  count the loss once on one side and not on the other. The star, the goal edge and the filled points
  are therefore on the same footing. `n_nights_weather` stays in the tables and in the hover.
- **low_n**: fewer than 5 nights with visits. Drawn faded, never dropped. No quarter with data
  is affected; in the monthly table only Oct 2025 is.
- **is_lsst**: periods starting on or after 20260629, i.e. FY26 Q4 (Jul–Sep 2026) onward; drawn as
  squares, Early Ops periods as circles. FY26 Q3 contains two LSST nights and stays Early Ops.
- **Storm truncation**: survey visits end on 20260713. FY26 Q4 has 8 nights with visits out of 92
  calendar nights, so its speed (0.06) counts 84 closed nights as zero (only six of them,
  20260714–20260719, carry an EFD WEATHER flag). Hover shows the last night with visits and a storm note. FY27 Q1 has zero
  visits and stays in the table; a path segment that skips a period is dashed and labelled
  "storm, off sky".

## 6. Reference values drawn on the figure

All in `ohlp/reference.py`; the figure never hard-codes a number.

| Drawn | Value | Derivation and source |
|---|---|---|
| Star x ("LSST = 1") | 0.629 | `ratio_sim_nvis / fO / fS / fA` with `ratio_sim_nvis = 2075536 / 3269149` (v5.1 visits over the 10-yr sum of the estimator), `fO = 762/825 × 0.9 / (1692518/2075536)`, `fA = 0.99` (RTN-093), `fS = 1`. 825 = Nv1 design, LPM-17 §3.4.0.1 Table 23; 0.9 = main-survey share, LPM-17 §3.4; 762 and 1692518 are v5.1 WFD numbers that appear only in code. From sp_notebooks `efficiency.ipynb` (`f732da4`, 2025-11-22), copied into the source notebook |
| Box left edge | 0.440 | star x × `fE_min = 0.7` (RTN-093: lowest allowed normalised étendue, survey-start criterion "Survey Speed > 0.7") |
| Box right edge | 1.2 | cosmetic, as in the source |
| Star y (iDIQ) | 0.39″ | 0.40″ system requirement (LSE-29 LSR-REQ-0007 SysIm_0; LSE-30 OSS-REQ-0227/0228; LPM-17 §3.3.3.1 minimum) with the 0.084″ dome budget removed in quadrature. Proposed by Phil Marshall, #mtg-summit-kpi, 2026-02-12. Hard-coded `idiq = 0.39` in the source |
| Box top (iDIQ) | 0.442″ | RTN-093 survey-start criterion 0.45″ (called "sDIQ" there but explicitly excluding dome seeing, see §4; reused in RTN-122) with 0.084″ removed in quadrature |
| Star y (FWHM 500 nm zenith) | 0.806″ | `sqrt(0.7² + 0.39² + 0.084²)`; fiducial atmosphere 0.7″ from the source (SOTN-004 quotes 0.72″ for the baseline sims) |
| Box top (FWHM 500 nm zenith) | 0.832″ | `sqrt(0.7² + 0.442² + 0.084²)` |
| Star y / box top (FWHM geom) | 0.873″ / 0.897″ | atmosphere at airmass 1.2 (`0.7 × 1.2^0.6`), no dome term, as in the source |
| 0.207″ (camera), 0.084″ (dome) | | SOTN-004 Table `tab:diq_budget` |
| ROST band | 0.55–0.60″ | Brian Stalder, ROST 21 Sep 2026, slide 2: measured **system** contribution (sDIQ) against a 0.40″ budget. Quadrature sum of the SOTN-004 "measured" rows: optical figure 0.4, tracking drift 0.1, jitter 0.02, dome seeing 0.3–0.4, diffusion 0.207. **Not the same quantity** as `idiq_aos_cam`, which omits dome seeing and tracking; the ~0.15″ difference is mostly measured dome seeing. Shown as a separate toggleable band ("ROST sDIQ band") on the iDIQ axis only |

Caveat on labels: the source notebook's "goal" (0.39) is the SRD minimum less dome seeing, and its
"minimum" (0.44) is the RTN-093 survey-start criterion.

## 7. Colours (from `rubin_palette`, no new values)

| Role | Palette name |
|---|---|
| time (month order) | `teal_cmap()` from `SEQUENTIAL_TEAL`, light = Oct 2025, dark = latest; lightness carries order in grayscale |
| Early Ops vs. LSST (two-point static) | `TEAL` for Early Ops, `CATEGORICAL[2]` purple for LSST (`colors=` override in `ohlp.static`) |
| goal region | `CATEGORICAL[4]` green, alpha 0.12 |
| LSST = 1 star | `CATEGORICAL[1]` orange, edge `NEUTRALS["ink_secondary"]` |
| ROST band | `CATEGORICAL[2]` purple, alpha 0.10, dotted edge |
| path, text, gap note | `NEUTRALS` |

## 8. Interactive version (`04_interactive.ipynb`)

- `PERIOD = "window"` (default) reads `windows_<tag>.parquet`; `"quarter"` and `"month"` read the
  other tables. For windows the nightly points are on from the start (size 9, alpha 0.45), the
  direct labels carry the date span and night count, and no storm segment label is drawn.
- Hover on a period point: quarter with its month span and Early Ops / LSST, nights with visits of calendar nights, weather
  nights (counted, not removed), visits / expected, speed median and IQR, IQ median and IQR, last night with visits, storm note,
  low-n flag, weather-state availability. Hover on a nightly point: night, visits / expected, speed, IQ, EFD weather hours, flag.
- Layers: period points, nightly cloud (off by default; faint, coloured by date, weather nights
  outlined), ROST band. Dropdown: y statistic (`idiq_aos_cam`, `fwhm_500_zenith`,
  `fwhm_geom`); the star, box top and y range follow. Range slider: quarters shown by index. `PERIOD = "month"` in the notebook gives the monthly version.
- Direct labels on every quarter (on the first, first-LSST and latest point when there are more than
  six periods); colour bar with period ticks; arrowheads at segment midpoints; dashed segment + "storm, off sky" across skipped months.
- Saved as standalone HTML (~2 MB, Bokeh 3.9.2 inlined) in `figures/`, not committed.

## 9. Running it on USDF

```bash
source /sdf/group/rubin/sw/loadLSST.bash
setup lsst_distrib
export PGPASSFILE=$HOME/.lsst/postgres-credentials.txt    # ConsDB replica from a login node
cd observatory_high_level_performance
jupyter nbconvert --to notebook --execute --inplace 01_data_and_binning.ipynb
jupyter nbconvert --to notebook --execute --inplace 04_interactive.ipynb   # PERIOD in cell 2 picks the binning
```

Parameters are in the second code cell of each notebook (`DAY_OBS_MIN`, `DAY_OBS_MAX`, `REFRESH`).
The ConsDB query, augmentation and EFD weather fetch take about one minute. Inside an RSP kernel the
token route is used automatically and the narrative-log weather column is filled.

`01_data_and_binning.ipynb` ends with an assertion that the binned visits and nights for FY26 Q2,
FY26 Q3, Apr 2026 and Jun 2026 equal a direct `COUNT(*)` on `cdb_lsstcam.visit1` (passed on
2026-10-14: 18 115 / 42, 33 464 / 57, 12 523 / 24, 9 554 / 15).

## 10. Caveats and open items

- The expected-visit model and the star are **in flux** (v5.1 → v5.3.4, new downtime model, ROSP-6
  still a stub). State the version on the figure.
- Speed includes closed nights, by design (§5). The weather flag exists only from 2026-02-25, and only
  from the EFD state. The narrative-log column needs an RSP token (`~/.token_file`, scopes `read:image` and
  `exec:notebook`, created at https://usdf-rsp.slac.stanford.edu/auth/tokens).
- `idiq_aos_cam` (iDIQ) is not comparable to Brian's 0.55–0.60″ (sDIQ, includes dome seeing; see §4 and §6).
- Per-band seeing differences are not removed from `idiq_aos_cam` (it has no atmosphere term) but
  the band mix does change the `fwhm_*` statistics from period to period.
- FY26 Q4 is 8 nights ending at the storm; its speed is dominated by the closed nights (see §5).
