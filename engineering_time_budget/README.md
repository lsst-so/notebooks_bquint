# engineering_time_budget

On-sky hours per week by visit category (survey, focus and alignment, engineering), Oct 2025 to
Jul 2026, against the LSST on-sky engineering-time policy. Built for the LSST@LATAM 2026 talk
(slide 11, "Engineering time is now budgeted, not improvised").

**Status:** figure done (2026-10-23); policy numbers still `[VERIFY]`. Ticket: none (talk material).

## Contents

- `python/make_engineering_hours_figure.py` — categorisation, weekly hours, figure.
- `data/visit1_20251026_20260714.parquet` — ConsDB `cdb_lsstcam.visit1` rows (airmass > 0,
  img_type in acq/science/cwfs/focus), trimmed; copied from the `nightly_survey_speed` cache.
- `data/weekly_hours_by_category_<tag>.csv` — per week: on-sky hours and shutter-open hours per
  category, nights with visits, nights with engineering visits.
- `figures/engineering_hours_weekly_talk_<tag>.png`, `_white.png` — 16:9.

## Definitions

- **Categories** are the ones of the on-sky utilization timeline (`nightly_survey_speed/utils.py`,
  copied): Survey Programs = BLOCK-407/408/416/417/419/421; Focus and Alignment = BLOCK-T539;
  Engineering = every other on-sky visit (AOS tests, sensitivity matrices, BLOCK-365, ...).
- **Hours on sky** = telescope time, not shutter time: consecutive visits of the same category
  within a night form a block (gaps under 10 min are bridged); a block lasts from the start of its
  first visit to the end of its last. Shutter-open hours are also in the CSV and are 1.5–1.9x
  smaller (readout, slews and settles are inside the on-sky hours, not in the shutter hours).
- Weeks start Monday. Weeks with no visits (e.g. the camera vacuum leak, 30 Jan – 15 Feb) are empty.
- Closed-dome engineering (no on-sky visits) is **not** counted: this is on-sky engineering only.

## Policy numbers drawn (to verify on Confluence page 1802141753)

- 8 h/week of on-sky engineering pre-authorised (dashed line).
- 16 h in any four weeks.
- At most 52 engineering nights in the first six months of LSST; the simulations assumed 26.

## Numbers (20 Oct 2025 – 19 Jul 2026)

| | on sky (h) | shutter open (h) |
|---|---|---|
| Survey Programs | 822 | 533 |
| Focus and Alignment | 107 | 57 |
| Engineering | 378 | 217 |

Early operations: engineering median 6.3 h/week, 16 of 33 weeks above 8 h, peak 43.9 h in the
week of 9 Mar 2026 (AOS stability tests, BLOCK-T698/T614/T703/T706). Three LSST weeks from 29 Jun:
0.8, 1.6, 2.2 h of on-sky engineering.

## Run

```bash
python engineering_time_budget/python/make_engineering_hours_figure.py
```
