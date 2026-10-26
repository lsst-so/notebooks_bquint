# efficiency_waterfall

Schematic "efficiency waterfall" for the LSST@LATAM 2026 talk (slide 8, "Efficiency: one word,
several definitions"). Message: the efficiency numbers people quote differ mainly in what they
exclude from the denominator.

**Status:** superseded on 2026-10-26 by `night_efficiency_brackets/` (one real night, the same
four denominators drawn as brackets; the schematic is kept for reference). Illustrative placeholder (2026-10-23). Every number is an input copied from a named
source and tagged `[VERIFY]` in the talk notes; nothing is computed from telemetry. To be replaced
by Lynne Jones's OSF-waterfall figure if it arrives. Ticket: none (talk material).

## Contents

- `python/make_efficiency_waterfall.py` — the five steps (`STEPS`), the reference lines and the
  figure. Edit the numbers there.
- `figures/efficiency_waterfall_talk.png`, `_white.png` — 16:9, transparent and white background.

## The five steps

| Chip (slide) | Denominator | Value | Source |
|---|---|---|---|
| whole night (OSF) | all night hours | 0.44 | OSF baseline, Jul 2025 (Keith Bechtol, CCR3/ORR2 deck) |
| survey time only | minus engineering, calibration, AOS | 0.61 | same ("science only") |
| excluding faults | minus weather and fault closures | not measured | ROSP-10 |
| scheduler model | visits / scheduler-model visits | 0.82 | RTN-122 |
| ideal | no overheads beyond readout | 1.00 | by definition |

Reference lines: 0.70 start-of-LSST criterion (RTN-093), 0.63 ten-year simulation average.
The OSF deck also quotes idealized 0.71 and simulation 0.72, which are not drawn.

## Run

```bash
python efficiency_waterfall/python/make_efficiency_waterfall.py
```

Needs only matplotlib and the repo palette (`../rubin_color_pallete`); copy that module into this
folder before extracting the investigation.
