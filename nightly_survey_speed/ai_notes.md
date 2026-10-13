# AI working notes: nightly_survey_speed

Working notes kept while rebuilding the "On-sky utilization / Visit Timeline" plot.
The polished write-up is `README.md`; this file records what was checked, decisions
taken, and open items. Dates are absolute (YYYY-MM-DD).

## Provenance

- Original notebook: `notebooks/on-sky_utilization.ipynb` in https://github.com/lsst/sp_notebooks
  - Clone used (read-only, outside this repo): commit `66e1baa8f5de348cda2a63fda00122b1c03f6da6`
    (2026-10-11, "Bump CI actions to Node.js 24 releases (#22)").
  - History of that file: `1a64cdd` 2026-07-16 Keith Bechtol, "SP-3121: Add on-sky utilization
    notebook (#8)" (plot logic, unchanged since); `138d4da` black formatting; `cf187d3` 2026-07-26
    Brian Stalder, ConsDB connection via `rubin_nights.connections.get_clients()`; `c1417f0` markdown
    narrative; `2feac29` 2026-10-05 strip execution metadata.
  - Times Square sidecar `on-sky_utilization.yaml`: author Brian Stalder, defaults
    `day_obs_min=20260629`, `day_obs_max=20260713`.
- RTN-122 "Rubin Observatory Early Operations On-sky Performance", Keith Bechtol, 2026-06-27,
  source https://github.com/lsst/rtn-122 commit `3f1c6326283652a36f1a38c6a405497f6c0c942b`.
  Section 3 "On-sky Utilization and Visit Rate", figure `on-sky_utilization_20251026-20260531.pdf`.
  Caption: "Time is referenced relative to 00:00 UTC on each calendar date. Shaded regions indicate
  the intervals between -12 deg and -18 deg solar elevation twilight."
- `rubin_nights` 0.18.2 as shipped in the `lsst_distrib` stack (`lsst-scipipe-14.0.0`, d_2026_10_10).

## What the original code actually does (verified 2026-10-13)

- Query: `SELECT * FROM cdb_lsstcam.visit1 WHERE airmass > 0 AND img_type in ('acq','science',
  'cwfs','focus') AND day_obs BETWEEN day_obs_min AND day_obs_max`, sorted by `obs_start_mjd`.
- Survey = `science_program` in exact-match list [BLOCK-407, 408, 416, 417, 419, 421].
  Focus and Alignment = `science_program == 'BLOCK-T539'`. Engineering = NOT survey.
  So BLOCK-T539 visits are plotted twice (orange first, green last, green wins visually).
- y value = `(exp_midpt_mjd - (MJD of 00:00 UTC on day_obs + 1 day)) * 24` hours. The reference
  is 00:00 UTC of the calendar day after day_obs. Not local midnight (notebook markdown is wrong,
  RTN-122 caption is right). Local midnight at the summit is 03:00 UTC (CLST) or 04:00 UTC (CLT).
- Marker `"_"`, size 20, at exposure midpoint. `time_obs_start_mjd` / `time_obs_end_mjd` inside
  the loop are both copies of `exp_midpt_mjd` (copy-paste slip), unused.
- x value = MJD of 00:00 UTC on day_obs. Numeric axis, not categorical. Twilight bands drawn for
  every calendar day in range, so empty nights show as shaded columns without ticks.
  Tick labels only at nights with data.
- Twilight: `astroplan.Observer.at_site("LSST")`; midnight = `observer.midnight(Time(day_obs
  23:59 UTC), which="nearest")`; evening twilights `which="previous"`, morning `which="next"`,
  nautical (-12) and astronomical (-18). Four `fill_between` layers: -12 to -18 at alpha 0.2,
  brighter than -12 at alpha 0.4, all black.
- `plt.ylim(-1.5, 11.0)`, `figsize=(16, 8)`, `dpi=200`, legend upper left, `set_rubin_plotstyle()`.

## ConsDB numbers for 20251026 to 20260714 (queried 2026-10-13, Postgres replica)

- 262 calendar nights, 219 with any `visit1` row, 187 with rows passing the filters.
- 96365 visits pass the filters. 88276 of them have `visit1_quicklook.psf_sigma_median`.
- Excluded on-sky rows: 1384 `engtest`, 28 `indome` with airmass > 0. Bias/dark/flat/cbp have
  airmass NULL or 0 and are excluded by `airmass > 0` anyway.
- BLOCK-T539: 6666 visits (Early Ops) + 202 (LSST period). Zero overlap with the survey list.
- Not matched by exact string: `BLOCK-T539_hexapods` (560, 2025-10-27 to 2025-11-14) is
  Engineering. `BLOCK-365` (389, March 2026) is Engineering here but is in
  `rubin_nights.reference_values.SCIENCE_PROGRAMS`.
- LSST period 20260629-20260714 programs: BLOCK-407 7267, BLOCK-T539 202, BLOCK-T720 161,
  BLOCK-T668 83, BLOCK-T746 48, `test` 1. Hard-coded survey list is complete for this period.
- Exposure midpoints fall in 23:00 to 10:59 UTC (plus 4 stray visits at 20 to 21 UTC).

## Environment and access (SDF login node via VS Code, 2026-10-13)

- Stack: `source /sdf/group/rubin/sw/loadLSST.bash; setup lsst_distrib`. Gives rubin_nights
  0.18.2, bokeh 3.9.2, astroplan 0.10.1, matplotlib 3.10, `lsst.utils.plotting`.
  `lsst.summit.utils` is NOT in lsst_distrib (needs `setup summit_utils` or a Nublado kernel).
- `rubin_nights.connections.get_clients()` needs an RSP token. None valid on the login node
  (`~/.token_file` returns 401 from usdf-rsp). In a Nublado kernel the token is injected.
- Fallback that works: `rubin_nights.consdb_query.ConsDbSql(site="usdf")`, Postgres logical
  replica `usdf-summitdb-logical-replica-svc.sdf.slac.stanford.edu`, credentials from
  `~/.lsst/postgres-credentials.txt`, requires `PGPASSFILE` to point at that file.
- In-cluster `http://consdb-pq.consdb:8080` does not resolve from the login node.

## Colors

- `lsst.utils.plotting.publication_plots`: no categorical palette. `rubin.mplstyle` cycle is the
  seaborn colorblind palette: `#0173B2` blue, `#DE8F05` orange, `#029E73` green, `#D55E00`,
  `#CC78BC`, ... `accent_color()` returns `#DE8F05`. RTN-045 band colors exist but are for ugrizy.
- Decision: use the first three cycle colors in the same roles as the original tab colors
  (survey blue, engineering orange, focus green). Keeps the "getting bluer" reading.
- [check: a Rubin visual identity palette in machine-readable form was not found in the stack]

## Decisions

- Folder `nightly_survey_speed/` is self-contained (notebooks, utils, plots, docs) so it can be
  lifted into its own repo or tech note later. `cache/` is gitignored.
- Repro notebook keeps the original logic cell by cell, quirks included. Only the connection
  cell (token first, Postgres fallback) and the parameters differ.
- Interactive notebook puts shared logic in `utils.py` with switches that default to the
  original behavior so every improvement can be toggled for comparison.

## Step 2: comparison with the JOR 2026 screenshot (2026-10-13)

Reference: `plots/reference_jor2026_screenshot.png` (slide 5, "Efficiency Evolution: Getting
Bluer!", Joint Operations Review, 1 to 3 September 2026). Reproduction:
`plots/on_sky_utilization_repro_20251026-20260714.png`.

Same in both: date range (first tick 20251026, last 20260714), twilight band shapes and alpha,
legend text and order, y limits -1.5 to 11 with ticks 0 to 10, x tick label style, the gap
pattern (late Dec to early Jan humidity gap, two late Jan to mid Feb LSSTCam gaps with the single
night 20260128 between them, 20260619 isolated), the mid March orange AOS block, and the all-blue
LSST period from 20260629.

Differences and likely causes:

1. Marker density. Colored pixels cover 35.5 % of the axes in the screenshot and 41.6 % in the
   reproduction. Shares by color agree to within 2 points (blue 0.645 vs 0.623, orange 0.271 vs
   0.281, green 0.083 vs 0.096). Cause: the screenshot is a slide render at about 1700 px for the
   axes, versus 3000 px here, so thin "_" markers (size 20) vanish when downsampled. Not a data
   difference.
2. Slightly more green visible here, consistent with point 1 (green ticks are the sparsest, so
   downsampling hides proportionally more of them).
3. No column present in one figure and absent in the other was found. ConsDB `visit1` rows come
   from image headers at ingest, so the row set for a finished night does not change later.
   [check: the slide figure may have been made from a notebook version before `cf187d3`, but
   the plot cell is byte-identical across all versions, so this cannot cause a difference]

Conclusion: the reproduction is faithful. Bookkeeping: 96365 visits on 187 of 262 nights;
63605 survey, 6868 focus (all drawn twice), 32760 "engineering" including the 6868 focus visits.
Data span -3.11 to 10.75 h, so the hard-coded `ylim(-1.5, 11)` clips a few early-evening
visits (the 4 at 20 to 21 UTC and some at 22 UTC).

## Step 3: utils.py and interactive notebook (2026-10-13)

- `utils.py`: `get_consdb_client` (token first, Postgres fallback), `fetch_visits` (original
  WHERE clause plus LEFT JOIN of `visit1_quicklook.psf_sigma_median`, parquet cache),
  `categorize_visits(exclusive=False|True)`, `category_changes`, `programs_in_range`,
  `day_obs_to_time`, `day_obs_range`, `hours_after_utc_midnight`, `add_time_columns`,
  `twilight_table`, `rubin_category_colors`. Ruff clean.
- Checks on 20251026-20260714: layers original 32760/63605/6868, exclusive 25892/63605/6868
  (sum 96365). Only BLOCK-T539 (6868) moves. Exposure durations 1.9 to 180.9 s, median 30.9 s.
  Twilight table 262 rows in 32 s. `hours_after_utc_midnight(mjd of 03:00 UTC) == 3.0`.
- Bokeh: ticks are `scatter(marker="dash")` with WebGL (fixed screen size, like the matplotlib
  "_" marker; `segment` with data-space width was tried first and made the HTML heavy without
  gain). Bars are `vbar` from `t_start_h` to `t_end_h`. One renderer per layer, legend
  `click_policy="hide"`, HoverTool `snap_to_data`. All models built inside `build_timeline()`;
  `render()` does `reset_output()` before save and before show, because a Bokeh model may belong to one document only and a failed render otherwise poisons the kernel.
- Headless run of the default variant: 2.5 min, 17.7 MB HTML, no errors. A second run with
  exclusive + bars + categorical on 20251026-20260131 also clean (test artifacts deleted).
- Colorblind check (Python port of the dataviz validator, OKLab dE x100, Machado 2009 sev 1.0):
  rubin cycle blue/orange/green worst pair 9.2 (protan, orange vs green), normal-vision worst 18.5:
  PASS. Original tab10 orange vs green: 0.7 under protanopia: FAIL. Orange contrast on white
  2.6:1, so values are also in hover and the CSV.
- No headless browser on the login node, so Bokeh PNG export is not possible here; static
  snapshots are matplotlib renders of the same data in the notebook.
