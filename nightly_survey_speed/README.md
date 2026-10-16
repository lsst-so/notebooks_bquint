# Nightly survey speed: the on-sky utilization timeline

Technical note for the `nightly_survey_speed` folder of `lsst-so/notebooks_bquint`,
branch `u/bquint/summit-performance-on-sky-utilization`. Working notes and the verification log
are in `ai_notes.md`.

## 1. Purpose

We want to understand, reproduce and improve the "Visit Timeline" figure that was shown at the
Joint Operations Review (JOR) 2026 under the title "Efficiency Evolution: Getting Bluer!". The
figure answers one question per night: **when during the night was the telescope taking on-sky
exposures, and under which kind of observing program?** Read down a column it shows how much of
the dark time a night used; read across it shows the trend from engineering-dominated nights to
survey-dominated nights.

The figure does **not** measure survey efficiency, open-shutter fraction, image quality, or
whether the visits were useful. Those are separate metrics (RTN-122 Sections 3 and 4). A blue
column only says that the exposures were tagged with a survey `science_program`.

This folder holds:

| Path | What it is |
|---|---|
| `notebooks/on_sky_utilization_repro.ipynb` | Cell-by-cell reproduction of the original static figure. The reference, quirks included. |
| `notebooks/on_sky_utilization_interactive.ipynb` | Bokeh version with hover, zoom, legend toggles and switchable improvements. |
| `utils.py` | Shared code: ConsDB client, query, categorization, time handling (UTC and Chile local frames), twilight, colors. |
| `downtime_annotations.csv` | Known downtime spans (dates are `day_obs`, inclusive) with cause, category, severity, confidence and FRACAS tickets. Rows with `label = UNKNOWN` are blank runs in ConsDB with no explanation yet. `talk = 1` flags the five spans labelled on the RASAB 2026 slide. |
| `downtime.py` | `annotate_downtime(ax, csv_path, ...)` (matplotlib) and `annotate_downtime_bokeh(p, csv_path, ...)` (Bokeh): draw the CSV spans on the timeline (bands, identity strips, staggered labels, category legend, LSST start marker; hover with the CSV row in Bokeh). |
| `make_utilization_annotated.py` | Builds `plots/utilization_annotated.{png,pdf}` (all categories except unknown; `--talk` for faults of 2+ nights only) and `plots/downtime_summary.md`. |
| `plots/` | Figures (`png`, `pdf`), the reference screenshot, the per-night CSV. Interactive `html` files are produced here but not committed. |
| `cache/` | Parquet cache of the ConsDB query, not committed. |

The next notebook planned for this folder is the image quality versus visit rate plot
(`diq_vs_visit_rate.ipynb` in `lsst/sp_notebooks`, maintained by Lynne Jones). It should reuse
`get_consdb_client`, `fetch_visits` and `categorize_visits` from `utils.py`.

## 2. Provenance

- **Original notebook.** `notebooks/on-sky_utilization.ipynb` in
  [lsst/sp_notebooks](https://github.com/lsst/sp_notebooks). We read it at commit
  `66e1baa8f5de348cda2a63fda00122b1c03f6da6` (2026-10-11). The plot logic was written by Keith
  Bechtol (commit `1a64cdd`, 2026-07-16, "SP-3121: Add on-sky utilization notebook") and has not
  changed since. Brian Stalder later moved the ConsDB connection to `rubin_nights` (`cf187d3`),
  added the markdown narrative (`c1417f0`) and stripped execution metadata (`2feac29`). The
  notebook is published on Times Square (USDF) with Brian Stalder as author and defaults
  `day_obs_min=20260629`, `day_obs_max=20260713`.
- **Document.** RTN-122, "Rubin Observatory Early Operations On-sky Performance", Keith Bechtol,
  2026-06-27, Section 3 "On-sky Utilization and Visit Rate". Source: `lsst/rtn-122` commit
  `3f1c6326283652a36f1a38c6a405497f6c0c942b`. The figure there covers 20251026 to 20260531.
- **Reference image.** `plots/reference_jor2026_screenshot.png`, slide 5 of the JOR 2026 talk
  (1 to 3 September 2026), covering 20251026 to 20260714.
- **Dependencies.** `rubin_nights` 0.18.2 (ConsDB clients), `astroplan` 0.10.1 (twilight),
  `lsst.utils.plotting` (Rubin plot style), `bokeh` 3.9.2, all from the `lsst_distrib` stack
  `d_2026_10_10` (conda env `lsst-scipipe-14.0.0`).

## 3. Data

**Table.** `cdb_lsstcam.visit1` in the Consolidated Database (ConsDB). One row per visit, built
from image headers at ingest. For hover we LEFT JOIN `cdb_lsstcam.visit1_quicklook` for
`psf_sigma_median`.

**Columns used.** `visit_id`, `day_obs`, `exp_midpt_mjd`, `obs_start_mjd`, `obs_end_mjd`,
`science_program`, `observation_reason`, `img_type`, `band`, `exp_time`, `airmass`, and
`psf_sigma_median` (converted to FWHM in arcsec with 2.355 times 0.2 arcsec per pixel).

**Filters** (identical to the original):

```sql
airmass > 0
AND img_type IN ('acq', 'science', 'cwfs', 'focus')
AND day_obs BETWEEN day_obs_min AND day_obs_max
```

`airmass > 0` removes bias, dark, flat and CBP exposures. The `img_type` list also removes
1384 on-sky `engtest` exposures and 28 `indome` exposures in our range, so some engineering time
on sky is **not** in the figure.

**Numbers for 20251026 to 20260714** (queried 2026-10-13):

| Quantity | Value |
|---|---|
| Calendar nights | 262 |
| Nights with any `visit1` row | 219 |
| Nights with visits passing the filters | 187 |
| Visits plotted | 96365 |
| Visits with a quicklook PSF value | 88276 |

## 4. Definitions

### 4.1 Categories

The original uses two hard-coded exact-match lists:

- **Survey Programs** (blue): `science_program` in BLOCK-407, BLOCK-408, BLOCK-416, BLOCK-417,
  BLOCK-419, BLOCK-421. These are the Feature Based Scheduler (FBS) driven pre-LSST and LSST
  observing blocks of the Early Operations period.
- **Focus and Alignment** (green): `science_program` equal to BLOCK-T539.
- **Engineering** (orange): every visit that is **not** in the survey list.

Consequences that are easy to miss:

- The three layers are not disjoint. Every Focus and Alignment visit is also an Engineering visit
  and is drawn twice, orange first and green on top. In our range that is 6868 visits. Visually
  the green wins, so the figure looks right, but the orange count is inflated.
- Matching is exact. `BLOCK-T539_hexapods` (560 visits, 2025-10-27 to 2025-11-14) is Engineering,
  not Focus and Alignment. `BLOCK-365` (389 visits, March 2026) is Engineering here, although
  `rubin_nights.reference_values.SCIENCE_PROGRAMS` lists it as a science program. Two visits
  tagged `BLOCK-640` (2025-11-15) are also Engineering.
- For the LSST period that started on 20260629 the only survey block in ConsDB is BLOCK-407
  (7267 visits up to 20260713). The rest are BLOCK-T539 (202), BLOCK-T720 (161), BLOCK-T668 (83),
  BLOCK-T746 (48) and one visit tagged `test`. The hard-coded list is therefore complete for that
  period, at least up to 20260714.

The interactive notebook has a switch `EXCLUSIVE_CATEGORIES`. When on, each visit gets exactly one
category with priority Focus and Alignment > Survey Programs > Engineering. The only visits that
change are the 6868 BLOCK-T539 visits, which leave the Engineering layer. Nothing else moves
because no program is in both lists.

### 4.2 Time axis

The y value of a visit is

```
hours = (exp_midpt_mjd - MJD(00:00 UTC on the calendar date of day_obs) - 1 day) * 24
```

that is, **hours after 00:00 UTC on the morning side of the night**. The original markdown calls
this "local midnight"; it is not. Clock midnight at the summit is 03:00 UTC during Chilean summer
time and 04:00 UTC during standard time, and the Sun's anti-transit is near 04:45 UTC. The
RTN-122 caption states the reference correctly ("relative to 00:00 UTC on each calendar date").
In our range the data span -3.1 to 10.8 hours; the original's fixed `ylim(-1.5, 11)` clips a few
early-evening visits taken before 22:30 UTC.

Nights are identified by the integer `day_obs`, never by the UTC date of the exposure. A Chilean
night runs roughly 23:00 to 11:00 UTC and straddles two UTC dates; `day_obs` rolls over at
12:00 UTC.

Each visit is drawn as a short horizontal tick at the exposure **midpoint**. The original computes
start and end arrays as well but fills them with the midpoint (copy-paste slip), and never uses
them. The interactive notebook has a switch `DRAW_BARS` that draws each visit from `obs_start_mjd`
to `obs_end_mjd` instead; at full range the two look alike, zoomed in the bars show real exposure
durations (median 30.9 s, range 1.9 to 180.9 s in our data).

### 4.3 Twilight

Computed with `astroplan.Observer.at_site("LSST")`. For each calendar `day_obs` the reference
midnight is the one nearest to 23:59 UTC on that date; evening twilights are searched backwards
from it and morning twilights forwards. Nautical twilight is -12 deg and astronomical twilight is
-18 deg solar elevation. The -12 to -18 deg intervals are drawn at alpha 0.2 and everything
brighter than -12 deg at alpha 0.4, in black. The LSST survey is designed to observe between the
two -12 deg twilights, so the light grey band is the margin and the dark grey is daytime for
survey purposes.

### 4.4 Nights with no data

The original x axis is **numeric** (Modified Julian Date of 00:00 UTC on `day_obs`), not
categorical. Twilight bands are drawn for every calendar night, so a night with no visits is an
empty shaded column. Only the tick **labels** are limited to nights with data, which makes the axis
look categorical at a glance. The interactive notebook keeps this as `X_AXIS="continuous"` and
adds `X_AXIS="categorical"` (one slot per night with data, no gaps) as the alternative, so the two
readings can be compared.

## 5. Reproduction and comparison with the JOR 2026 slide

`notebooks/on_sky_utilization_repro.ipynb` copies the original cells verbatim (post-black
formatting) and changes only the connection cell, the date range, the figure path and a parquet
cache. Running it for 20251026 to 20260714 gives
`plots/on_sky_utilization_repro_20251026-20260714.png`.

Against the screenshot, every structural feature matches: first and last tick labels, the gap
pattern (late December to early January humidity gap, two LSSTCam utility gaps in late January to
mid February with the single night 20260128 between them, 20260619 alone), the mid-March orange
block of Active Optics System (AOS) tests, the all-blue LSST period from 20260629, the twilight
shapes, the legend, and the y range. We found no column present in one and absent in the other.

The only measurable difference is marker density. Colored pixels cover 35.5 percent of the plot
area in the screenshot and 41.6 percent in our render, while the blue, orange and green shares
agree to within two points. The screenshot is a slide render of about 1700 pixels across the axes
and ours is 3000, so the thin tick markers vanish when downsampled. This is a rendering effect, not
a data difference. We conclude that the reproduction is faithful and that the slide was made from
the same code and the same date range.

## 6. The interactive version and how it differs

`notebooks/on_sky_utilization_interactive.ipynb` builds the same figure with Bokeh:

- **Interaction.** Horizontal pan and wheel zoom, box zoom, reset, save. Hover on any visit shows
  visit id, `day_obs`, local (America/Santiago) and UTC midpoint time, `science_program`,
  `observation_reason`, `img_type`, band, exposure time, PSF FWHM when available, and the
  category. Clicking a legend entry hides or shows that category. Legend labels include counts.
- **Switches**, all defaulting to the original behavior: `EXCLUSIVE_CATEGORIES`, `DRAW_BARS`,
  `X_AXIS`, `Y_REF` (`"utc"`, the original reference, or `"local"` for Chile clock time with
  `HH:00` ticks; each night is shifted by its own UTC offset, so the twilight curves step by 1 h
  at the daylight-saving change on 2026-04-05), `Y_RANGE` (None gives twilight-based automatic
  limits instead of the fixed -1.5 to 11, so no visit is clipped), and the two program lists as
  parameters. `ANNOTATE_DOWNTIME` (default on) adds the downtime layer of Section 9 with
  `DOWNTIME_MIN_NIGHTS`, `DOWNTIME_CATEGORIES` and `DOWNTIME_LABEL_CATEGORIES` as selectors;
  it needs the continuous x axis. The default range now ends at 20260713, the last night before
  the July storm.
- **Colors.** `lsst.utils.plotting` has no named categorical palette. We read the color cycle of
  its `rubin.mplstyle`, which the file documents as the seaborn colorblind palette, and keep the
  original roles: slot 1 `#0173B2` blue for Survey Programs, slot 2 `#DE8F05` orange for
  Engineering, slot 3 `#029E73` green for Focus and Alignment. The style's `accent_color()` is
  the same orange. We checked the three colors with an OKLab colour-difference computation under
  simulated protanopia and deuteranopia (Machado, Oliveira and Fernandes 2009, severity 1.0):
  the worst pair (orange versus green under protanopia) has a difference of 9.2, above the
  target of 8, and all pairs are above 15 for normal vision. The original `tab:orange` versus
  `tab:green` scores 0.7 under protanopia, so those two were indistinguishable for red-blind
  readers. The orange has a contrast of 2.6:1 against white, so values are also provided in
  hover and in the per-night table. [check: we did not find a machine-readable Rubin visual
  identity palette in the stack; if one exists it should replace these three values]
- **Outputs.** The figure is saved to `plots/*.html` (self-contained, tens of megabytes, not
  committed) and shown inline. Two static matplotlib snapshots are written for slides, one with the
  current switches and one with all improvements on. A per-night CSV
  (`plots/nightly_summary_<range>.csv`) gives hours of exposure per category, visit counts and
  night length between the -12 deg twilights.

Differences from the original by design: the twilight bands are drawn per night as columns rather
than as a smooth filled curve (identical at the one-night resolution of the figure); the y label
states the UTC reference; the x axis is a real datetime axis when continuous.

## 7. Caveats for anyone presenting this plot

- **Blue means tagged, not efficient.** A blue tick is a visit whose `science_program` is in the
  survey list. It says nothing about open-shutter fraction, slew overheads, image quality or
  whether the visit was later rejected.
- **Orange is a catch-all.** Everything not in the survey list is Engineering, including focus
  sequences (double-counted in the original), test blocks, pointing checks and visits with
  `science_program` unknown. Zero orange does not mean zero engineering activity, since on-sky
  `engtest` exposures and in-dome work are excluded by the `img_type` filter, and daytime work
  is outside the plot.
- **The y axis is UTC, not local time.** Say "hours after 00:00 UTC" or convert in your head
  (subtract 3 or 4 hours for local clock time).
- **Empty columns are nights without filtered visits**, which includes closed nights, lost nights
  and nights with only excluded image types. The figure cannot distinguish weather from faults
  from scheduled downtime. On a categorical axis these nights vanish entirely.
- **The survey list is hard-coded.** A new FBS block that is not added to the list shows up as
  orange. Check `programs_in_range` in the interactive notebook when extending the date range.
- **Marker density depends on the render.** Thin ticks disappear when a figure is shrunk for a
  slide, which can make a night look emptier than it was. The `DRAW_BARS` option and the
  per-night CSV are the robust alternatives.
- **The last night may be partial.** 20260714 has only three filtered visits in ConsDB.

## 8. Running it on USDF

Branch: `u/bquint/summit-performance-on-sky-utilization` in `lsst-so/notebooks_bquint`.

**In a Nublado (RSP) JupyterLab kernel.** The `LSST` kernel already has everything. The ConsDB
client is obtained through `rubin_nights.connections.get_clients()` using the RSP token of the
session. Leave `CLIENT_PREFER="token"`.

**On an SDF login node (for example VS Code over SSH).** There is no RSP token, so the token route
fails and `utils.get_consdb_client` falls back to the Postgres logical replica through
`rubin_nights.consdb_query.ConsDbSql`. Requirements:

```bash
source /sdf/group/rubin/sw/loadLSST.bash
setup lsst_distrib
export PGPASSFILE=$HOME/.lsst/postgres-credentials.txt   # set automatically by utils if unset
cd nightly_survey_speed/notebooks
jupyter nbconvert --to notebook --execute --inplace \
    --ExecutePreprocessor.kernel_name=python3 on_sky_utilization_interactive.ipynb
```

The credentials file is the standard USDF one that `lsst.daf.butler` also uses. Set
`CLIENT_PREFER="postgres"` to skip the token attempt. `lsst.summit.utils` is not needed and is
not part of `lsst_distrib`.

**Parameters** (first code cell of each notebook): `day_obs_min`, `day_obs_max`,
`SURVEY_PROGRAMS`, `FOCUS_PROGRAMS`, `EXCLUSIVE_CATEGORIES`, `DRAW_BARS`, `X_AXIS`, `Y_RANGE`,
`CLIENT_PREFER`, `USE_CACHE`, `INSTRUMENT`. The query for 262 nights takes about 8 seconds on the
replica; the twilight table takes about 30 seconds; the Bokeh render about one minute.

**Caching.** `fetch_visits` writes `cache/lsstcam_visits_ql_<min>_<max>.parquet` and reads it
back when `USE_CACHE=True`. Delete the file or set `USE_CACHE=False` to refresh.

## 9. Downtime annotations (2026-10-16)

For the RASAB 2026 talk the timeline is overlaid with the downtime spans of
`downtime_annotations.csv`, drawn by `downtime.annotate_downtime` and rendered by
`make_utilization_annotated.py` for 20251026 to 20260713 (the last night before the July
storm; the storm row stays in the CSV and is not drawn).

- A night is "blank" when fewer than 50 visits pass the plot's filters. Over the 261 nights
  there are 80 blank nights in 27 contiguous runs. The `low`/`medium` rows of the CSV were
  aligned to these runs (confidence raised to `high`, note "dates from ConsDB"); 18
  `UNKNOWN` rows cover the 25 blank nights with no explanation yet. `UNKNOWN` rows are
  not drawn by default.
- Colours are Rubin palette slots (`rubin_color_pallete/rubin_palette.py`): fault red,
  weather teal, planned green, mixed orange, degraded purple (hatched, no band), unknown
  grey. A solid strip along the top edge of the axes carries the colour at full saturation,
  because the pale extent bands alone do not separate under colour-vision deficiency.
- `plots/downtime_summary.md` lists every span with its count of blank nights and the
  per-category totals.
- `make_utilization_annotated.py` writes four variants. `utilization_annotated` (16:9, white
  background) draws every category but unknown with staggered text labels above the plot; it is
  the backup slide. `utilization_annotated_talk` is the RASAB 2026 slide figure: 9.5 x 4 inch,
  transparent background, fault / weather / mixed spans of 3+ nights as bands, and the five
  spans with `talk = 1` numbered chronologically inside their strip (water condensation,
  Dynalene loss, vacuum leak #1, PCS compressor failure + vacuum leak #2, TMA encoder + cryo
  warm-up: the faults that cost four or more nights and appear in Sandrine Thomas' notes). The
  three legends (visit types, downtime colours, numbered events) are stacked to the right of the
  plot with thin separators. Both come with a `_local` twin (Chile clock time y axis, 18:30 to
  07:30; the June solstice sunset is 17:46 and the earliest twilight end 18:46). The interactive
  notebook draws the same layer with `annotate_downtime_bokeh` (text labels above the plot, with
  the span's dates, category, FRACAS tickets and notes on hover).
