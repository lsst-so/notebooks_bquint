# visit_gap_anatomy

Time between consecutive survey visits (the "gap"): distribution and weekly trend, Oct 2025 to
Jul 2026. Built for the LSST@LATAM 2026 talk (slide 10, "A visit: 30 seconds of light, and a gap").

**Status:** figure done (2026-10-23). Ticket: none (talk material); references RSO-785 (Bob Blum's
gap time series in #survey-performance) and RTN-122 §3.

## Contents

- `python/make_visit_gap_figure.py` — gap computation and the two-panel figure.
- `data/visit1_20251026_20260714.parquet` — ConsDB `cdb_lsstcam.visit1` rows (airmass > 0,
  img_type in acq/science/cwfs/focus), trimmed to the columns used; copied from the
  `nightly_survey_speed` cache so this folder runs offline.
- `data/visit_gap_weekly_<tag>.csv` — weekly n / median / 25 % / 75 %.
- `data/visit_gap_summary_<tag>.csv` — percentiles of the whole sample.
- `figures/visit_gap_talk_<tag>.png`, `_white.png` — 16:9.

## Definitions

- **Gap** = `obs_start` of a visit minus `obs_end` of the previous visit (rubin_nights
  `augment_visits` definition). In ConsDB `obs_end − obs_start = exp_time + 0.93 s`, so the readout
  is inside the visit, not the gap. The gap is **reset at the start of each `day_obs`**.
- **Survey visits only**: both visits of a pair belong to a scheduler-driven survey block
  (BLOCK-407/408/416/417/419/421, the list used by the on-sky utilization timeline, copied from
  `nightly_survey_speed/utils.py`). Engineering, AOS and focus visits are excluded, and so are the
  gaps on either side of them.
- Histogram: 0.5 s bins to 40 s; longer gaps (4.5 %) are off scale and listed in the footnote.
- Weekly panel: weeks start Monday; weeks with fewer than 100 survey visit pairs are not plotted.
- Requirement line: 5 s (OSS-REQ-0289).
- "Second settle" shading: gaps of 14–20 s, the population where a late AOS correction with a
  pointing offset forces a second slew/settle.

## Numbers (26 Oct 2025 – 13 Jul 2026, 63,269 visit pairs)

| | value |
|---|---|
| median gap | 9.4 s (early ops 9.4 s; LSST from 29 Jun 9.1 s) |
| 10 / 25 / 75 / 90 % | 6.8 / 7.7 / 13.0 / 18.2 s |
| gaps below 5 s | 1 % |
| gaps 14–20 s | 12 % |
| weekly median range | 7.3 s (Mar–Apr 2026) to 17.2 s (week of 15 Jun 2026) |

The slide text says "~8 s median"; the measured median over the full window is 9.4 s. The
best weeks (March–April 2026) are at 7.3–8 s. The slide text has to follow the figure.

## Caveats

- The gap includes everything between shutter close and the next shutter open: slew, settle,
  filter changes, AOS corrections, scheduler latency. Sub-timings are not shown; Lynne Jones is
  redoing the slew-flag matching (two set/clear pairs per gap when the AOS correction carries a
  pointing offset, #survey-performance 10 Sep 2026).
- The June 2026 rise is the AOS stability period; the gap came back to ~8 s in July.

## Run

```bash
python visit_gap_anatomy/python/make_visit_gap_figure.py
```

Palette from `../rubin_color_pallete` (copy it in before extraction). To refresh the data,
re-run the `nightly_survey_speed` ConsDB fetch and copy the columns listed in the script.
