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

## Handoff (2026-10-13, end of first session)

State: branch `u/bquint/summit-performance-on-sky-utilization`, 6 local commits on top of
`main` (`ee3c466`), nothing pushed, no PR. Working tree clean apart from pre-existing untracked
files in `notebooks/`.

Done: Steps 1 to 4 of the task. Reproduction verified against the JOR 2026 screenshot;
interactive notebook and `utils.py` executed headless from an SDF login node via the Postgres
replica; README written.

Not yet verified:
- The token route (`CLIENT_PREFER="token"`, `rubin_nights.connections.get_clients()`) in a
  Nublado kernel. Only the Postgres fallback was exercised.
- The Bokeh figure rendered in a live browser (hover, legend toggles, wheel zoom). The HTML was
  inspected for the expected models only. No headless browser on the login node.
- `[check: Rubin visual identity palette]` in README section 6.

Open decisions for Bruno: push and open the PR; start the DIQ versus visit rate notebook
(`diq_vs_visit_rate.ipynb` in lsst/sp_notebooks, Lynne Jones) in this folder reusing
`utils.get_consdb_client`, `fetch_visits`, `categorize_visits`.

Scratch locations outside the repo (safe to delete): `~/tmp_clones/sp_notebooks`,
`~/tmp_clones/rtn-122` (read-only clones), `/tmp/nss_build/` (notebook builder scripts
`build_repro.py`, `build_interactive.py`, `cvd_check.py`, comparison crops).

## Step 5: downtime annotations for the RASAB 2026 talk (2026-10-16)

Decisions and findings, in order:

- Blank night = fewer than 50 visits passing the plot filter (`cache/nights_20251026_20260713.csv`
  has the per-night counts; the raw per-night-per-img_type query is next to it). 80 blank nights
  in 27 runs over 261 nights. 75 of them have zero plotted visits.
- CSV edits (Bruno confirmed the proposals): low/medium rows moved to the observed runs with
  confidence high and "dates from ConsDB" in notes; partial rows kept with a ConsDB check note;
  18 UNKNOWN rows for unexplained blank runs (25 nights), not drawn by default. Bruno: small gaps
  are probably minor faults or weather, UNKNOWN is fine, do not plot them. High rows never touched,
  so the tails 20260417 and 20260508-10 are UNKNOWN rows rather than extensions.
- `talk` column (0/1) in the CSV marks the five spans labelled on the slide. Label of the March
  event shortened to "PCS compressor failure + vacuum leak #2" so it wraps on two legend lines.
- The y axis: 0 is 00:00 UTC on the morning date, i.e. 21:00 CLST / 20:00 CLT, so the evening
  twilight crossing zero in summer is correct. `Y_REF="local"` shifts each night by its own
  America/Santiago offset (-3 / -4 h); there is a 1 h step at the 2026-04-05 DST change. Local
  y range 18:30 to 07:30 (one stray visit at 17:53 on 20251130 is clipped).
- Colours: Rubin palette slots (fault red `#DB5451`, weather teal `#058B8C`, planned green
  `#00630C`, mixed orange `#CE7F00`, degraded purple `#74369E`, unknown grey). At band alpha the
  pairs fail the CVD check, so the solid strip above the axes carries the identity; at full
  saturation all pairs pass except fault/mixed under deuteranopia (6.7), covered by labels.
- Strips end exactly at the axes top edge (`strip_overlap=0`) and are drawn under the spines.
  Digits are centred on glyph ink (`_digit_ink_center_pt`), not the font box, in strips and in
  the legend chips (the chip DrawingArea is in points; do not multiply by dpi/72 there).
- Slide style (`STYLES["slide"]`): 9.5 x 4 in, transparent figure face with a white axes patch,
  axis labels 10 pt, ticks 12 pt, legends 9 pt, numbers 12 pt, visit-legend keys +2 pt. Legend
  stack on the right is 1.98 in wide; axes about 6.6 x 3.1 in. `fit_margins` tightens the
  margins to 0.02 in after annotating (geometry outside the axes is in inches so it survives).
- Minor x ticks on days 8, 15, 22 (quarter-month marks aligned to the month majors).
- The box right of "4" on the slide is "PCS chiller flow variations" (partial, 26 Feb to 18 Mar,
  one blank night), a different event from the compressor failure (20 to 23 Mar); kept separate.

Verified: all four figure variants render; the notebook executes headless end to end (scratch
copy via nbconvert, Postgres route); PNG alpha checked (corners 0, plot area 255); digit padding
measured in the PNG (9 to 10 px top and bottom at 300 dpi).

Not verified: the Bokeh figure in a live browser (no headless browser on the login node); the
Bokeh label stagger uses estimated text widths; the notebook's Bokeh layer still uses text
labels above the plot, not the numbered mode; the token route in a Nublado kernel.

## Handoff (2026-10-16, end of second session)

State: branch `u/bquint/summit-performance-on-sky-utilization`, nothing pushed, no PR. Two new
commits this session: code (scripts, CSV, utils, notebook, docs) and the regenerated figures.

Files: `downtime_annotations.csv` (35 rows, `talk` column), `downtime.py`
(`annotate_downtime`, `annotate_downtime_bokeh`, `select_spans`, `fit_margins`),
`make_utilization_annotated.py` (`--talk`, `--y-ref utc|local`), `plots/utilization_annotated*`
(8 files), `plots/downtime_summary.md`.

Open for Bruno: research the 18 UNKNOWN rows (FRACAS, narrative log, #summit-announce); dark
slide background would need an ink-colour option (text and chips are dark ink on white boxes);
numbered mode for the Bokeh layer if wanted; push and PR.
