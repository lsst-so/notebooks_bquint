# engineering_time_budget

On-sky hours per week by visit category (survey, focus and alignment, engineering), Oct 2025 to
Jul 2026, against the LSST on-sky engineering-time policy. Built for the LSST@LATAM 2026 talk
(slide 11, "Engineering time is now budgeted, not improvised").

**Status:** figure B10 done (2026-10-23), policy variant B10b done (2026-10-26; label positions
adjusted the same day); policy numbers still `[VERIFY]` against the Confluence page. Ticket: none (talk material).

## Contents

- `python/make_engineering_hours_figure.py` — categorisation, weekly hours, figure.
- `data/visit1_20251026_20260714.parquet` — ConsDB `cdb_lsstcam.visit1` rows (airmass > 0,
  img_type in acq/science/cwfs/focus), trimmed; copied from the `nightly_survey_speed` cache.
- `data/weekly_hours_by_category_<tag>.csv` — per week: on-sky hours and shutter-open hours per
  category, nights with visits, nights with engineering visits.
- `figures/engineering_hours_weekly_talk_<tag>.png`, `_white.png` — 16:9 (B10).
- `figures/engineering_hours_weekly_policy_<tag>.png`, `_white.png` — 16:9 (B10b): same data,
  same bins, same totals as B10; only the annotations change, see below.

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

Source: Rubin Confluence page 1802141753, "On-sky engineering time during LSST", v6 of
2026-07-28, still titled "Proposed". `[VERIFY]` the three numbers against the current version.

- 8 h/week of on-sky engineering pre-authorised (RSO).
- 16 h in any four weeks.
- Envelope: at most 52 full-night equivalents of engineering in the first six months of LSST;
  the simulations assumed 26.

### B10b: the policy drawn on the plot (2026-10-26)

- The 8 h/week line is **solid from 2026-06-29** (start of LSST, when the policy applies) and
  light-grey dashed before that: over Early Operations it is a reference, not a rule. Label at the
  right end: "8 h/week pre-authorized (RSO)".
- Vertical dashed marker at 2026-06-29: "LSST start · policy applies".
- The 4-week cap is a **text annotation** "16 h per 4 weeks" under the 8 h label. A 4-week rolling
  sum drawn as a step was tried and rejected: it peaks at 136 h in March 2026 and doubles the y
  range, burying the LSST weeks; 20 of the 33 Early-Ops 4-week windows exceed 16 h anyway.
- Corner box, top left: "Envelope: 52 full-night equivalents in the first 6 months of LSST
  (simulations assumed 26)".
- Direct labels: engineering hours on the three LSST weeks (0.8, 1.6, 2.2 h) and on the
  9 Mar 2026 peak (44 h, AOS stability tests). The 0.8 h label is left-aligned just right of the
  LSST-start line so it sits on the week-of-29-Jun bar instead of across the marker. The AOS
  label sits above the neighbouring (taller) bars at 87 % of the y range, with a short vertical
  leader down to the week-of-9-Mar bar, so it crosses neither the 2 Mar nor the 16 Mar bar.
- Categories and legend unchanged from B10.

Caveat (applies to both figures): the policy counts *dedicated* engineering between the −12°
twilights and excludes start-of-night focus and post-fault recovery. These figures count every
non-survey, non-T539 on-sky visit between the first and last visit of a same-category block, so
they can over-count engineering relative to the policy's own bookkeeping.

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

Writes the weekly CSV and both figures (B10 and B10b).
