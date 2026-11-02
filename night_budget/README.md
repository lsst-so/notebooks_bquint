# night_budget — where one night of LSST goes

**Jira:** ROSP-10, ROSP-6, ROSP-24 · **Status:** figure B12 delivered 2026-11-02 ·
**Talk:** LSST@LATAM 2026, São Paulo, 2–6 Nov, slide 6 ("a good night and a bad night")

One night of the Simonyi survey, accounted for from the visit list up: how much of the
−12° observable night the shutter was open, how much of the rest was the slew the
simulations expect, and how much was excess. Three bars — the LSST ideal night, a real
good night, a real bad night — in the same block form as slide 3.

![a good night and a bad night](figures/good_bad_night_20260706_20260708_white.png)

## 1. What the slide says

1. **Expected.** The ideal night: open shutter 74 % of the −12° night, ~1056 visits.
2. **Where we are.** 6 Jul 2026 reached 0.85 of that; 8 Jul 2026 reached 0.53.
3. **Room to improve.** On the good night the gaps between visits are already close to
   what the kinematic model allows: 9.7 s expected against 12.3 s actual, i.e. 2.6 s per
   visit of excess. The remaining shortfall is not the gaps — it is the hour at the start
   of the night and the transitions.

The three Science blocks on each bar are **exposing** (shutter open), **expected gap** (the
slew, readout and settle the kinematic model says each gap needed) and **excess gap** (what
the night spent over that model). See [§4, what "expected gap" and "excess gap"
mean](#what-expected-gap-and-excess-gap-mean) for the definition and the per-gap numbers —
worth reading before presenting, since the split is measured against a *model*, not against
the OSS-REQ-0289 requirement.

Two things for the spoken notes, both in §4 and neither on the figure: the **gap cadence
improved 2.3×** at survey start (median nightly gap 14.9 s before, 8.6 s after), and the one
night with **zero loss in every category still only reached 0.825** — the ceiling is not set
by faults.

## 2. Definitions

| Source | Value | Use on the figure |
|---|---|---|
| OSS-REQ-0288 | visit = 34 s (2 × 15 s design; we observe 1 × 30 s) | text only |
| OSS-REQ-0289 | inter-visit interval (shutter closed → next shutter open): median < 5 s, mean < 10 s | the gap-split numbers in §5 |
| `ideal_osf.py` fit to `baseline_v5.3.7_10yrs` | ideal night: OSF = 0.7261 − 0.0169·cos(season), 30 s visits, −12° night | the "LSST ideal night" bar, and the denominator of `ratio` |
| RTN-093 | survey-start criterion: survey speed > 0.7 | dashed tick on each real bar |
| ROSP-6 | fE = fS·fA·fO, target ≥ 1; fO is this slide's quantity | **not yet measured**; the 2024 sub-factors are not a baseline |
| ROSP-22 / ROSP-24 | −12° → −12° night; category precedence | as in B1/B3/B11 |

The night is the ROSP-22 observable night, Sun altitude −12° → −12°, weather and downtime
**not** excluded. Categories are as in B10/B11: Survey Programs =
BLOCK-365/407/408/416/417/419/421, Focus and Alignment = BLOCK-T539, Engineering =
everything else on sky. Time goes to the first category that applies, weather first.

## 3. The ideal night: re-fitting the open-shutter fraction (step 0)

`rubin_nights.dayobs_utils.estimated_baseline_visit_range` is still the **v5.1** fit —
OSF = 0.74 − 0.02·cos(season), upper envelope 0.78 — so the per-night ideal had to be
re-derived from the baseline actually in use. `python/ideal_osf.py` does that: per
simulated night it takes OSF = Σ`visitExposureTime` / night length(−12°), keeps only
**full** nights (no dead interval > 10 min anywhere, including before the first and after
the last visit, so the v5.3 downtime model cannot drag the clear-night rate down), fits the
same functional form and takes the 90th percentile of the residuals as the `n_vis_high`
analogue.

| baseline | a | b | high | full nights | written 
|---|---|---|---|---|---|
| v5.3.4 (the one in Lynne's `diq_vs_visit_rate`) | 0.7305 | 0.0138 | 0.7549 | 1201 | 2026-07-14 |
| **v5.3.7 (default)** | **0.7261** | **0.0169** | **0.7518** | 1200 | 2026-10-31 |
| v5.4.0b | 0.7315 | 0.0190 | 0.7534 | 1206 | 2026-09-27 |
| v5.1 (what `rubin_nights` still uses) | 0.7400 | 0.0200 | 0.7800 | — | — |

**A v5.4 baseline does exist**, contrary to the handoff — but `baseline_v5.4.0b_10yrs.db`
is a beta written 2026-09-27, i.e. *older* than `baseline_v5.3.7_10yrs.db` (2026-10-31).
The default is therefore v5.3.7, the newest non-beta run. It makes little difference: all
three agree to within 0.008 in `ratio`.

As the handoff expected, v5.3 moved the clear-night OSF very little. 6 Jul goes from
**0.832** (v5.1) to **0.851** (v5.3.7), a move of +0.019 — just inside the 0.02 flag. Every
row keeps a `ratio_v51` column so slide 2's 0.82 can still be compared like for like.

## 4. The per-night budget (step 1)

`python/night_budget.py` writes one row per night to
`data/night_budget_<min>_<max>.csv`. It **combines** two things that already existed and
re-derives neither:

- the **per-visit gap split** from Lynne Jones' `sp_notebooks/notebooks/efficiency.ipynb`:
  `rubin_nights.rubin_scheduler_addons.add_model_slew_times` models the slew that should
  have preceded each visit, once with the TMA limits the EFD says were applied
  (`slew_model`) and once with the FBS kinematic model at 40 % TMA that the simulations
  assume (`slew_model_ideal`). Her settings are used: `wait_before_slew = 1.6 s`,
  `settle = 1.5 s`, `dome_crawl = True`, `slew_while_changing_filter = False`;
- the **ROSP-24 block hours** from `simonyi_time_loss`, read from a copy of its per-night
  CSV at `data/rosp24_per_night.csv` — no cross-folder import, so this folder stays
  extractable with `git filter-repo --subdirectory-filter night_budget`.

The Science block is split four ways over survey visits only:

| column | definition |
|---|---|
| `exposing_h` | Σ `exp_time` — shutter actually open |
| `in_visit_h` | Σ (obs_end − obs_start − exp_time) — readout etc. |
| `gap_expected_h` | Σ min(`slew_model_ideal`, gap) — the slew the sims assume |
| `gap_excess_h` | Σ (gap − expected) over survey gaps ≤ 10 min |
| `gap_expected_current_h` | the same with `slew_model` — today's TMA limits |

### What "expected gap" and "excess gap" mean

A **visit gap** is dead time between two survey visits: from the shutter closing on one to
the shutter opening on the next (the OSS-REQ-0289 inter-visit interval). Across it the
telescope has to read out the last exposure, slew to the next field, rotate, settle, and
sometimes change filter. Some of that is unavoidable physics; the rest is not. The split
separates the two.

For each survey visit, `add_model_slew_times` **simulates the slew that should have
preceded it** — same start and end pointing, same rotator angle, same filter change if one
happened — through the FBS kinematic model at 40 % TMA, the one the baseline simulations
assume. Call that modelled duration *m*, and the gap actually observed *g*. Then:

- **expected gap** = `min(m, g)` — the part of the gap the model says was *necessary*. It
  is capped at *g* so a gap that beat the model never contributes more than it took.
- **excess gap** = `g − min(m, g)` — what the night spent *over* the model. Zero when the
  gap matched or beat the model, positive otherwise.

The two therefore sum to the whole gap by construction, and the split is a comparison
against a physical model, **not** against a requirement. A night can have small excess and
still miss OSS-REQ-0289, which is exactly what 6 Jul does.

Why this is the useful cut for the slide: it answers "could this night have gone faster with
the telescope we have?" separately from "is the telescope as fast as the survey needs?".
Excess gap is the part operations can recover; expected gap can only be reduced by making
the hardware or the scheduler faster.

On 6 Jul, over the night's 897 survey gaps:

| | median | mean | total |
|---|---|---|---|
| actual gap *g* | 9.2 s | 12.3 s | 3.07 h |
| modelled slew *m* | 7.3 s | 9.9 s | — |
| **expected** = min(*m*, *g*) | 7.2 s | 9.7 s | 2.41 h |
| **excess** = *g* − expected | 1.4 s | 2.6 s | 0.66 h |

Two things that table hides. **160 of the 897 gaps had zero excess** — they matched or beat
the model outright. And the excess is not spread evenly: **46 % of it comes from the worst
10 % of gaps** (the longest is 218 s against a 9 s median). So "0.66 h of excess" is mostly
a few dozen bad gaps, not a uniform tax on every visit — which is why the figure also
reports the count of gaps over twice the model (46 on 6 Jul).

**Which model — ideal or current TMA?** `add_model_slew_times` returns both: `slew_model`
uses the TMA limits the EFD says were actually applied that night, `slew_model_ideal` the
40 % TMA model the simulations assume. The figure and `gap_expected_h` use the **ideal**
one, because each bar is read against the simulated ideal night; `gap_expected_current_h`
carries the current-TMA version so "the TMA is slower than the sims assume" can be
separated from "everything else". The difference is small today — 9.7 s against 9.2 s per
visit on 6 Jul — so the limits applied that night were close to the 40 % model. Open for
Bruno to overrule.

Pitfalls handled: gaps reset at each `day_obs`; ConsDB `obs_*_mjd` are TAI, converted to
UTC (−37 s); the first gap of the night and the first gap after a non-survey visit are
**not** survey gaps (the same ones Lynne nulls with `skipped_visits`); the model filter
change is 120 s and does not overlap the slew.

### Night selector

**good** = the largest `ratio` among LSST nights (`day_obs ≥ 20260629`, `LSST_DAY_OBS_MIN`)
with weather = 0, fault + idle < 0.5 h and engineering + alignment < 0.5 h. **bad** = 8 Jul
2026, already explained in B11 — pre-chosen in the handoff rather than selected, so the
audience can be walked from B11's timeline to B12's block form without meeting a new date.
It is also the right *kind* of bad night: 10 Jul was worse (0.387) but is 6.5 h of pure
weather, a bar that is mostly one grey block, where 8 Jul mixes weather (1.6 h), fault +
idle (2.9 h) and a 4.2 h start-of-night, so every category stays visible.

The era floor is deliberate but not a data limit — see
[below](#why-6-jul-and-what-the-month-before-lsst-shows) for the month before survey start.

The fault + idle cut is on ROSP-24's published `idle_bit_hours`, not on this module's
`fault_idle_h`. The latter is a *residual* of the −12° night and so also absorbs the long
and non-survey gaps the Science split leaves out; gating on it rejected 6 Jul (0.645 h) for
time the figure shows inside the Science block, while ROSP-24's own idle bit for that night
is 0.251 h.

Candidates over 20260629–20261030 (14 nights in range; 13 with survey visits — 20260714 was fully clouded out):

| day_obs | visits | n_vis_ave | ratio | exposing | idle | eng | align |
|---|---|---|---|---|---|---|---|
| **20260706** | 899 | 1056 | **0.851** | 7.49 h | 0.25 | 0.18 | 0.13 |
| 20260629 | 875 | 1061 | 0.825 | 6.99 h | 0.00 | 0.00 | 0.00 |
| 20261029 | 624 | 767 | 0.814 | 5.07 h | 0.19 | 0.00 | 0.27 |

Plausible clean nights do cap around 0.82–0.85, as the handoff found. Nights excluded by
the cuts but with a high ratio: 20260705 (0.791, 0.91 h engineering), 20260711 (0.781,
0.96 h engineering), 20261027 (0.762, 1.10 h engineering).

### Why 6 Jul, and what the month before LSST shows

The LSST-era pool is thin — the July 2026 storm means only **13 nights have on-sky visits**
between 20260629 and 20261030 — so on Bruno's suggestion (2026-11-02) the budget was also
run over the month *before* survey start, 20260529–20260628
(`data/night_budget_20260529_20260628.csv`, 16 more nights with visits). Two things come out
of it, and **neither changes the figure**: both stay here and in the spoken notes.

**1. The best single night is pre-LSST, by a hair.** 20260626 reached ratio **0.853** on 906
visits — the most visits and the most exposing time (7.55 h) of any night in either era,
with weather, engineering and alignment all zero and only 0.15 h of idle + fault. It edges
6 Jul's 0.851. It is *not* used, for two reasons: it is a commissioning night before survey
start, so it is off-message on a slide about LSST performance; and it carries 1.59 h of
excess gap against 6 Jul's 0.66 h, which would undercut the slide's third point.

**2. The gap cadence improved sharply at survey start.** This is the finding worth speaking
to, since it is a real change rather than night-to-night luck:

| | pre-LSST (20260529–0628) | LSST (20260629–20261030) |
|---|---|---|
| nights with visits | 16 | 13 |
| median of the nightly gap medians | **14.9 s** | **8.6 s** |
| range of nightly gap medians | 8.9 – 23.2 s | 7.4 – 14.8 s |
| nights with median gap < 10 s | **2 of 16** | **11 of 13** |
| pooled excess gap per survey visit | **8.3 s** | **3.7 s** |

Pre-LSST nights reached a high ratio by being *long* — many visits over a full night — while
running a 13–15 s cadence. The LSST-era nights reach the same ratio by actually moving
faster: excess gap per visit fell **2.3×**. The two exceptions on each side are 20260529 and
20260530 (8.9 and 9.6 s, already fast before the switch) and 20260629 (14.8 s, the slow
night described below).

**3. Only one night has zero in every loss category: 20260629** — weather, focus, alignment,
engineering, idle and fault all 0.000 h, in either era. It is nonetheless the *weaker*
candidate, and instructively so: its loss did not vanish, it moved into the gaps. 2.09 h of
excess gap, a 14.8 s median, and 399 of its 874 gaps in the 15–30 s band where 6 Jul has 61.
Nothing broke; the whole night simply ran slowly. That makes it the strongest available
illustration that **the ceiling is not set by faults** — a fault-free night still only
reached 0.825 — which is worth saying out loud even though the bar on the slide is 6 Jul.

So: 6 Jul is within 0.002 of the best night ever recorded, is in the LSST era, and is the
one whose gap cadence supports "the gaps are already close to the model". Switching the
figure to any of these is one flag, e.g. `--good 20260626`.

## 5. The numbers on the figure (step 2)

Ideal night: 11.86 h, OSF 0.7424 (6 Jul's season), exposing **8.81 h**, 1056 visits.
RTN-093 tick at 0.7 × that = **6.17 h** of exposing.

### Colours and legend — the deck palette, as in slide-4 B1

Bruno asked on 2026-11-02 for the same scheme as
`time_loss_monthly_talk_20251025-20261031_6bin_white.png`, so B12 uses the deck's
`SLIDE2_COLORS` hexes — Science `#024243`, Engineering `#045B5C`, Alignment `#058B8C`,
Fault + idle `#F5A623`, Weather `#9BAEB8` — read off the night-definition strip on slide 2.
The constant is **copied** into `make_good_bad_night_figure.py`, not imported from
`simonyi_time_loss`, so this folder stays extractable; if the deck palette changes it must
change in both places. `rubin_palette.CATEGORY_COLORS` is untouched, and reverting to it is
one line: set `PALETTE = RUBIN_COLORS`.

The first draft looked worse than B1 even though it used the same hexes. The reason was
**alpha**: tinting Science at 45 % / 20 % to make the gap blocks washed them toward the
weather grey. B1 has no transparency anywhere — every block is a solid colour, separated by
white rules and labelled in white. B12 now does the same, which needs one fill that is not
a deck colour:

| block | fill | note |
|---|---|---|
| exposing | `#024243` | Science, the deck colour |
| expected gap + in-visit | `#7FC6C7` | `GAP_TEAL`, a step of `rubin_palette.SEQUENTIAL_TEAL` |
| excess gap | `#7FC6C7` + `///` | **same fill as expected gap**, told apart only by the hatch (Bruno, 2026-11-02) |
| Alignment / Engineering / Fault + idle | deck colours | solid |
| Weather | `#9BAEB8` + `\\\` | hatch direction as on B1 |

`#7FC6C7` was chosen because it clears every one of the six deck colours: nearest is
Weather at ΔE 18.3, then Alignment at 24.7.

One pair still **fails the normal-vision contrast floor**, exactly as slide-4 B1 does:
Science `#024243` against Engineering `#045B5C` is ΔE **10.9**, under the floor of 15,
because they are two steps of one teal ramp. It is mitigated by the **white hairline
separators** at every block join, so each block stays countable without a seventh hue. All
14 other pairs clear the floor (full matrix printed by the ΔE check in the commit message of
`8130bd8`); the worst after that pair is gap vs Weather at 18.3.

**In-bar `%` labels** are drawn on every block wide enough to hold one — the threshold is
`LABEL_MIN_FRAC = 0.055` of the night, about 39 min, below which "6%" would not fit at
7.5 pt. Label colour comes from the same `STYLE` dict as the fill: white on the four dark blocks, ink on
the two light ones. On 6 Jul the Alignment and Engineering blocks (2 % and 1 %) fall below
the threshold and are deliberately unlabelled — their numbers are in the table above.

The legend is **one centred row of seven** under the x label, in stack order. It started as
two rows with `Science:` / `Lost:` titles, but inside a 2.22 in frame each title costs a
line of height and the lower row collided with the x label; the entry labels carry the
grouping instead ("exposing", "expected gap", "excess gap", then the plain category nouns).
Swatches and blocks are both drawn from the single `STYLE` dict, so they cannot drift apart.
The bottom margin is grown in a measure-and-retry loop until the legend actually fits, since
its height depends on font metrics rather than on anything known up front.

**Layout — sized for the slide.** The figure is exactly **9.55 × 2.22 in** at 300 dpi
(`FIG_W` / `FIG_H`, Bruno's slide box, 2026-11-02), so it is placed at ~1:1 and **a point
here is a point on screen**. Every type size is therefore a real slide point and sits near
the 7–8 pt floor: bar labels 8.5, the `N visits · ratio` labels 8.5, ticks and x label and
legend 7.5, in-bar `%` labels 7.5. Line weights came down to match (axis 0.6, separators
0.8, hatch 0.5). There is no title — the slide carries one, and in a frame this short every
line of height counts. `BAR_H = 0.89` at a bar pitch of 1.0, so the gap between bars is 0.11 —
half what it was, with the bars taking up the difference (Bruno, 2026-11-02). The y limits
follow `BAR_H` rather than being fixed, so changing the thickness keeps the air above and
below correct, and the margins hold only what must live outside the axes.

Because the type is pinned to the slide box, **changing `FIG_W`/`FIG_H` alone will not
rescale the figure sensibly** — the point sizes would no longer match the placed size. If the
slide box changes, change the `PT_*` constants with it.

| | ideal | 6 Jul 2026 (good) | 8 Jul 2026 (bad) |
|---|---|---|---|
| night (−12°) | 11.86 h | 11.86 h | 11.85 h |
| survey visits | 1056 | **899** | **559** |
| ratio to ideal | 1.00 | **0.85** | **0.53** |
| `ratio` under v5.1 | — | 0.83 | 0.52 |
| exposing | 8.81 h (74 %) | 7.49 h (63 %) | 4.67 h (39 %) |
| expected gap + in-visit | 3.05 h (26 %) | 2.65 h (22 %) | 1.83 h (16 %) |
| excess gap | — | 0.66 h (6 %) | 0.66 h (6 %) |
| alignment | — | 0.25 h (2 %) | 0.20 h (2 %) |
| engineering | — | 0.18 h (1 %) | — |
| fault + idle | — | 0.65 h (5 %) | 2.87 h (24 %) |
| weather | — | — | 1.61 h (14 %) |
| start of night (−12° → first visit) | 0 | 0.25 h | 4.23 h |
| filter changes | — | 14 | 15 |

### The good night's gap split, per survey visit

| | 6 Jul | requirement (OSS-REQ-0289) |
|---|---|---|
| exposure | 30.0 s | — |
| in-visit (readout etc.) | 0.9 s | — |
| expected gap (ideal model, 40 % TMA) | 9.7 s | — |
| expected gap (current TMA limits) | 9.2 s | — |
| **excess gap** | **2.6 s** | — |
| gap median | 9.2 s | < 5 s |
| gap mean | 12.3 s | < 10 s |
| gaps > 2× model | 46 of 897 | — |

So on the best night of the era the median inter-visit interval is 9.2 s against a
requirement of 5 s, and the mean 12.3 s against 10 s — but only 2.6 s per visit of that is
excess over what the kinematic model allows. The gap is close to as good as the current
model permits; the requirement asks for a faster model.

**fO is not measured here.** ROSP-6's fE = fS·fA·fO needs fS and fA too; this folder
measures only the fO-like ratio, and the 2024 sub-factors are not a baseline.

## 6. Contents

```
night_budget/
├── README.md
├── data/
│   ├── ideal_osf_v5.3.4.csv, _v5.3.7.csv, _v5.4.0b.csv   # per-night simulated OSF (step 0)
│   ├── night_budget_20260629_20261030.csv                # one row per night, LSST era (step 1)
│   ├── night_budget_20260529_20260628.csv                # the month before survey start (§4)
│   ├── rosp24_per_night.csv                              # copy of simonyi_time_loss output
│   └── visits_slew_*.parquet                             # ConsDB + modelled slews (gitignored)
├── figures/
│   └── good_bad_night_20260706_20260708[_white].png      # B12, 9.55 x 2.22 in
└── python/
    ├── ideal_osf.py                    # step 0: fit the ideal-night OSF from an opsim
    ├── night_budget.py                 # step 1: the per-night budget + night selector
    └── make_good_bad_night_figure.py   # step 2: the figure
```

## 7. Reproducing

From an SDF login node (ConsDB via the RSP token, EFD for the TMA limits):

```bash
source /sdf/group/rubin/sw/loadLSST.bash; setup lsst_distrib   # lsst-scipipe-14.0.0, rubin_nights 0.18.2
cd night_budget
python python/ideal_osf.py --all                               # ~7 min, re-fits every baseline
cp ../simonyi_time_loss/data/processed/per_night.csv data/rosp24_per_night.csv
python python/night_budget.py --day-obs-min 20260629 --day-obs-max 20261101 --select
python python/night_budget.py --day-obs-min 20260529 --day-obs-max 20260628   # pre-LSST month, §4
python python/make_good_bad_night_figure.py
```

## 8. Caveats

- **`fault_idle_h` is a residual**, not a measured block: the −12° night minus everything
  else accounted for. It therefore absorbs the long gaps and the time around non-survey
  visits that the Science split excludes. Use ROSP-24's `idle_bit_hours` for the published
  fault + idle number; this column exists so the bar closes.
- **The real bars close by construction**, not by measurement. `fault_idle_h` is the
  residual that makes the blocks sum to the −12° night, so the bar is always exactly the
  night and the scaling step in `real_bar()` is a no-op today (0.0 % on both nights). It
  stays in as a guard: if a future ROSP-24 revision makes the categories overlap the
  Science split, the bar will still be the night rather than overflowing it.
- **The `engtest` difference does not apply here.** Time-loss counts `img_type = engtest`
  where nightly survey speed does not (~1412 visits over the era, noted in the 10-31
  handoff), but 6 and 8 Jul have **zero** `engtest` visits — they are 899/559 `science`
  plus 14/10 `acq`. The two conventions agree on these two nights.
- The ideal bar's visit count (1056) is `n_vis_ave`, the seasonal fit. The upper envelope
  `n_vis_high` is 1070 for this night — 6 Jul is 0.84 of that.
- `add_model_slew_times` needs every on-sky visit, not just survey ones, since the
  telescope's position before a survey visit depends on wherever the previous visit
  pointed. The query therefore keeps acq/science/cwfs/focus/engtest and filters to survey
  programs only inside the split.

## 9. Reference

- EFD schema: https://ts-xml.lsst.io/ · ConsDB LSSTCam: https://sdm-schemas.lsst.io/cdb_lsstcam.html
- Lynne Jones, `sp_notebooks/notebooks/efficiency.ipynb` (the per-visit gap split, reused here)
  and `on-sky_utilization.ipynb`; Brian Stalder, `weekly_metrics.ipynb` §5.
- Visit-level allocations: ROSP-10, Confluence 1907359761.
- In this repo: `simonyi_time_loss/` (ROSP-24 blocks, B1/B3), `night_efficiency_brackets/`
  (B11, the 8 Jul night laid out in time), `visit_gap_anatomy/` (a single gap).
