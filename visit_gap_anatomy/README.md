# visit_gap_anatomy

Time between consecutive survey visits (the "gap"): distribution and weekly trend, Oct 2025 to
Jul 2026. Built for the LSST@LATAM 2026 talk (slide 7, "A visit: 30 seconds of light, and a gap").

**Status:** figures done (2026-10-23; split into two talk panels and the 14–20 s "second settle"
shading **removed** 2026-11-04 — see "The 14–20 s band" below). The June 2026 excess is a fixed
~6 s per-visit delay and its **cause is identified**: AOS corrections applied serially before each
slew, `ts_observatory_control` v0.50.0 / OSW-2269, 2026-06-03 (**RSO-785**). See "What happened in
June 2026". The weekly panel is labelled accordingly: "+6 s per visit, Jun 2026: AOS correction
before each slew". Open: why it stopped after the 1 Jul 2026 summit rebuild. Ticket: none (talk
material); references RSO-785 and RTN-122 §3.

## Contents

- `python/make_visit_gap_figure.py` — gap computation and the figures. Both layouts come from the
  same two panel functions, so they cannot drift apart:
  - no flag — the combined figure and the two split panels;
  - `--combined` — only the 16:9 two-panel figure;
  - `--split` — only the two standalone quarter-slide panels;
  - `--excess` — additionally the excess-gap diagnostic (off by default, not for the talk).
- `python/check_late_correction.py` — the three tests that retired the "second settle" shading
  (see below). Read-only; writes nothing.
- `python/june_2026_excess.py` — seven tests on the June 2026 excess: it is a **fixed ~6 s
  per-visit delay**, flat in slew distance and band, with a hard floor; test 7 shows it is one
  constant cost paid at a varying *rate*, which is what confirms the OSW-2269 account (see "What
  happened in June 2026"). Read-only; writes nothing.
- `notes/HANDOFF_june_2026_excess_2026-11-04.md` — the handoff asking a Slack/Jira/Confluence
  session to find the change.
- `notes/HANDOFF_june_2026_excess_gap_cause_2026-11-04.md` — **the answer** (OSW-2269 / RSO-785),
  with the deployment timeline, the quotes from #survey-performance and #commissioning-aos, the
  remaining EFD test for the July offset, and an addendum recording what was verified from ConsDB.
- `data/visit1_20251026_20260714.parquet` — ConsDB `cdb_lsstcam.visit1` rows (airmass > 0,
  img_type in acq/science/cwfs/focus), trimmed to the columns used; copied from the
  `nightly_survey_speed` cache so this folder runs offline.
- `data/visit_gap_weekly_<tag>.csv` — weekly n / median / 25 % / 75 %.
- `data/visit_gap_summary_<tag>.csv` — percentiles of the whole sample.

### Figures

| file | size | contents |
|---|---|---|
| `figures/visit_gap_talk_<tag>.png`, `_white.png` | 13.33 × 7.5 in, 16:9 | both panels, with the title and the data footnote on the figure |
| `figures/visit_gap_hist_talk_<tag>.png`, `_white.png` | 6 × 4.84 in | gap histogram: 1 s bins, bars all Rubin teal `#058B8C`, requirement line at 5 s, median line and "median 9.4 s". **No shaded band.** No title |
| `figures/visit_gap_weekly_talk_<tag>.png`, `_white.png` | 6 × 4.84 in | weekly median, 25–75 % band, requirement line, LSST start 29 Jun marker, and a grey span over the May–Jul 2026 rise labelled "+6 s per visit, Jun 2026: AOS correction before each slew". No title |
| `figures/visit_gap_excess_<tag>.png`, `_white.png` | 6 × 4.84 in | `--excess` only, **diagnostic, not a talk figure**: `gap − slew_model`, 0–20 s, **split by epoch** (see note). Different (shorter) window — the slew cache is May–Oct 2026 |

The excess diagnostic is drawn as two curves, Jun 2026 versus everything else, deliberately.
**Pooled it looks bimodal** (peaks at 0.8 s and 6.2 s) and would be read as exactly the
two-population structure the retired band claimed — but that is an artefact of June being 51 % of
the slew cache. Split, each epoch is unimodal (medians 1.5 s and 7.7 s): the whole distribution is
displaced by ~6 s during the episode, which is the opposite conclusion. Pooling two epochs with
different medians manufactures a fake second mode; that trap is why the figure is split.

The two split panels are for a quarter of a 16:9 slide, rendered at **6 × 4.84 in** / 200 dpi
(resized from 8 × 4.4 in on 2026-11-04: 75 % of the width, 10 % more height, so 1.24:1 rather
than the previous 1.82:1). Point sizes were deliberately *not* rescaled, so labels still clear
the 11 pt floor at the ~4.4 in they are placed at. They carry **no title, no
suptitle and no footnote** — the slide carries the title, and the data caption is the next
section of this README.

Each is written **twice**, the same convention as the combined figure: `_white.png` on a white
background, and **`.png` with no suffix for a transparent background** — use that one on the
slide so the deck's own background shows through. The transparent version keeps the dark axis ink,
so it is for **light** slides; on a dark slide call `rp.use(mode="dark")` first, or the labels
will disappear.

### Data caption for the split panels

Put this under the panels on the slide, or in the speaker notes:

> ConsDB `visit1`, scheduler-driven survey blocks only. Gap = start of a visit − end of the
> previous one, reset each night. 63,269 visit pairs; 4.5 % of gaps are longer than 40 s and off
> the histogram scale; weeks with fewer than 100 survey visit pairs are not plotted.

## Definitions

- **Gap** = `obs_start` of a visit minus `obs_end` of the previous visit (rubin_nights
  `augment_visits` definition). In ConsDB `obs_end − obs_start = exp_time + 0.93 s`, so the readout
  is inside the visit, not the gap. The gap is **reset at the start of each `day_obs`**.
- **Survey visits only**: both visits of a pair belong to a scheduler-driven survey block
  (BLOCK-407/408/416/417/419/421, the list used by the on-sky utilization timeline, copied from
  `nightly_survey_speed/utils.py`). Engineering, AOS and focus visits are excluded, and so are the
  gaps on either side of them.
- Histogram: **1 s bins** (`HIST_BIN_S`) to 40 s; longer gaps (4.5 %) are off scale and listed in
  the caption. Widened from 0.5 s on 2026-11-04: at quarter-slide size the half-second bars were
  too thin to read and their bin-to-bin noise looked like structure. The `--excess` diagnostic and
  the tests in `check_late_correction.py` still use 0.5 s, where resolution matters more than
  legibility.
- Weekly panel: weeks start Monday; weeks with fewer than 100 survey visit pairs are not plotted.
- Requirement line: 5 s (OSS-REQ-0289).
- The histogram carries **no shaded band** — see "The 14–20 s band" below.
- **Episode span** on the weekly panel: `#BFBFBF` at 30 % alpha, from the first to the last week
  whose median exceeds `SPAN_MEDIAN_S = 12 s`, searched **inside May–Jul 2026 only**. The script
  prints the edges. Scoping matters: the week of 24 Nov 2025 also clears 12 s (12.86 s), and
  searching the whole window would stretch the span across the panel and contradict its own
  label. The script prints that outlier separately so it is not silently dropped.

## Numbers (26 Oct 2025 – 13 Jul 2026, 63,269 visit pairs)

| | value |
|---|---|
| median gap | 9.4 s (early ops 9.4 s; LSST from 29 Jun 9.1 s) |
| 10 / 25 / 75 / 90 % | 6.8 / 7.7 / 13.0 / 18.2 s |
| gaps below 5 s | 1 % |
| gaps off the histogram scale (> 40 s) | 4.5 % |
| weekly median range | 7.3 s (Mar–Apr 2026) to 17.2 s (week of 15 Jun 2026) |
| episode span (weeks with median > 12 s, May–Jul 2026) | **week of 18 May 2026 to week of 29 Jun 2026** (ISO 2026-W21 to 2026-W27) |

The slide text says "~8 s median"; the measured median over the full window is 9.4 s. The
best weeks (March–April 2026) are at 7.3–8 s. The slide text has to follow the figure.

## The 14–20 s band: why the shading was removed

Earlier versions shaded 14–20 s as a "second settle" population. That band was set by hand
(typical gap + ~8 s between the two slew-flag pairs reported by Tiago Ribeiro,
#survey-performance, 10 Sep 2026) and is not supported by the data: against the `night_budget`
slew model, `slew_model` and `slew_distance` are flat inside vs outside the band while the excess
rises from ~3 s to ~9 s, the band has no separate mode (1.10× a tail fit overall, 0.98× in
Jul 2026), and 82 % of it falls in May–Jul 2026. Treat long gaps as **waiting, concentrated in
Jun 2026** — see "What happened in June 2026" above, which pins that waiting down to a fixed ~6 s
per visit between 2026-06-03 and 06-30 and rules the second-settle mechanism out on its own
(a fixed wait flat in slew distance is not a slew).

A shaded band also *reads* as a measured population, which this one was not — so it was removed
rather than relabelled. `python/check_late_correction.py` runs the three tests below; all numbers
are its output.

**1. Shape — no second mode.** A second settle adds a roughly fixed extra cost, so it should show
up as a separate bump. Fitting the decay either side of the band (8–13 s and 22–30 s) and
interpolating across it, the band sits at **1.10×** that fit over the full window and **0.98×** in
July 2026 — i.e. exactly the ordinary decaying tail. In the best months (Feb–Apr 2026) it is
**0.27×**. The histogram peak is at 7.2 s and never moves into the band except during the episode,
when the *whole* curve slides right (peak 13.2 s) — one mode shifting, not a second appearing.

**2. Time — it is an episode, not a standing cost.** May–Jul 2026 is 42 % of all pairs but
**82 % of the band**; June 2026 alone is 15 % of pairs and 58 % of the band. Drop May–Jul and the
14–20 s fraction falls from **12 % to 3.6 %** (median 9.37 → 8.54 s). So "12 % of visits" is a
window cut through a distribution that was shifted for three months, not a 12 % sub-population of
survey visits.

**3. Mechanism — extra dead time, but no extra slew.** `night_budget/data/visits_slew_*.parquet`
carries the kinematic `slew_model` prediction per gap (May–Oct 2026). Inside the band versus
outside:

| | n | gap | `slew_model` | excess (`gap − slew_model`) | `slew_distance` |
|---|---|---|---|---|---|
| outside 14–20 s | 13,520 | 10.43 s | 6.44 s | 2.97 s | 3.01° |
| inside 14–20 s | 5,254 | 15.99 s | 7.01 s | **8.89 s** | 3.03° |

The modelled slew and the slew distance are **flat**; only the unexplained excess moves, by ~6 s.
Per month the same: `slew_model` holds at 6.5–7.0 s while the excess goes 2.35 (May) → 7.67 (Jun)
→ 1.28 s (Jul). The telescope is **not slewing further or more often — it is waiting.** That rules
out a second *slew*. And the excess-gap distribution has a **single** peak that merely slides
(0.5 s in July → 6.0 s in June), where a fixed-cost second settle on some fraction of visits would
make it bimodal.

**Verdict.** The lost time is real — ~6 s per gap of unexplained dead time during the episode —
but it is **an episode in time, not a band in gap-value**, and its cause is not established from
ConsDB. That mismatch is what made the shading misleading: a time-localised phenomenon drawn as a
gap-value window on a figure integrated over nine months. It is also why the old "12 % of visits"
was unstable (1.5 % in Feb–Apr, 46 % in June): the number only existed because the window averaged
the episode together with the quiet months. That line is gone from the numbers table.

What the figures say instead: the histogram shows the distribution, the requirement and the median,
and nothing else; the weekly panel puts a grey span over the rise, labelled **"+6 s per visit,
Jun 2026: AOS correction before each slew"** — the measured effect and its mechanism, on the panel
where the effect is actually visible in time.

**The mechanism is now known, and it is not a second settle** — it is a wait *before* the slew,
not a second one (next section). So the band should stay off the histogram: there is no measured
per-gap second-settle cost to shade, and the real effect is localised in time rather than in
gap-value. The `--excess` diagnostic shows the dead time the kinematic model cannot explain
(median 1.5 s outside the episode, 7.7 s in Jun 2026); the next section attributes it.

## What happened in June 2026

The May–Jul rise is **not** gradual and not an AOS-convergence problem: between `day_obs`
**2026-06-03 and 2026-06-30** every survey visit paid a roughly **fixed ~6 s** of extra dead time.
`python/june_2026_excess.py` prints the seven tests; the episode and non-episode nightly medians
**do not overlap** (15 June nights at 6.13–9.06 s; all 14 other nights in the slew cache at
0.78–3.38 s), and it is present on the first visit of 2026-06-03 rather than ramping in.

| hypothesis | verdict | why |
|---|---|---|
| second slew / settle | ruled out | excess is **flat in slew distance** — 7.73 s below 1°, 7.70 s at 6–10°, 7.50 s above 10°; `slew_distance` unchanged |
| a subpopulation of affected visits | ruled out | **hard floor**: June p1 = 3.60 s, p5 = 4.65 s vs 0.13 / 0.33 s in July — almost no visit escaped |
| reduced TMA velocity limits | ruled out | only 2026-06-11 ran reduced (0.5 °/s), and there `slew_model` itself rose to 13.2 s; 14 of 15 nights ran at full 2.0 °/s |
| thermal / drifting calibration | ruled out | flat across the night (7.65 / 7.75 / 7.61 s by third) and **survived the 2026-06-21…24 camera-cryo stop** (8.24 → 7.81 s) |
| band or filter dependent | ruled out | all six bands 7.34–8.64 s |

Raw gaps over the full nine months reproduce it without the slew model (June p5 = 11.14 s, median
14.79 s, against 3.5–7.5 / 7.5–10.8 s for every other month), and **15 of the 20 highest-floor
nights in nine months are the 15 June observing nights** — so neither the step nor the floor is a
model artefact.

### The cause: AOS corrections applied serially before every slew

Identified 2026-11-04 from Slack/Jira/GitHub (not from ConsDB — see the two handoffs in `notes/`).
**`ts_observatory_control` v0.50.0, released 2026-06-03 under OSW-2269** (Tiago Ribeiro), added
`handle_aos_close_loop()` to `maintel/mtcs.py` and calls it *immediately before the slew command*,
after the M1M3 slew flags go on. When MTAOS has a correction in `WAITING_APPLY`, the slew **blocks**
until the camera-hexapod / M2-hexapod / M1M3 / M2-bending corrections complete. The hexapod move
and its in-position wait is the ~6 s. Tracking ticket **RSO-785** (Lynne Jones, 2026-06-24:
"+2–3 s around mid-May, another 4–6 s around June 3 … a delay before the TMA motion").

This explains every row of the table above at once: the cost is paid *before* the slew, so it is
flat in distance; the AOS pipeline was fast enough that a correction was pending at nearly every
slew, so there is a hard floor; and it is control-software behaviour, so a four-night power cycle
does not clear it.

**The confirmation from this folder's own data** (test 7, the mixture test) is that the mechanism
predicts a constant cost paid at a varying *rate* — and that is what the data show:

| window | n | rate paying > 4 s | median \| paid | median all |
|---|---|---|---|---|
| late May | 1,780 | 0.28 | 7.78 s | 2.33 s |
| **June** | 9,471 | **0.98** | **7.74 s** | 7.66 s |
| early Jul | 3,408 | 0.25 | 6.27 s | 1.53 s |
| mid Jul | 2,252 | 0.06 | 6.14 s | 1.04 s |
| Oct | 1,778 | 0.20 | 6.49 s | 1.42 s |

The cost per affected gap spans only 6.14–7.78 s while the rate spans 0.06–0.98. **June is the
same pre-slew wait at a ~100 % duty cycle**, not a different phenomenon. The per-night rate also
recovers the mid-May "sometimes" regime (0.25 / 0.31 / 0.37 on 05-29/30/31 → 0.95/0.98/0.99 on
06-03/04/06), reproducing RSO-785's two-step onset from ConsDB alone.

**Still open:** why it stopped after the 2026-07-01 summit OS/Postgres rebuild. `handle_aos_close_loop`
is unchanged on `main`, so the mechanism is still armed — and Oct still sits at a 0.20 rate. The
working hypothesis is that corrections stopped being reliably ready at slew time, making the
pre-slew branch a no-op; the rate *decays* over the first ~10 days of July (0.25 → 0.06) rather
than switching off, which fits a degraded-then-repaired pipeline better than a config revert. The
decisive test is per-gap EFD timings (`MTAOS.logevent_closedLoopState`, `command_issueCorrection`,
hexapod `logevent_inPosition` vs TMA motion start) — needs a JupyterLab kernel, as
`lsst.summit.utils` is not importable on the SDF login node.

**On the figure:** the weekly panel is labelled **"+6 s per visit, Jun 2026: AOS correction before
each slew"** (set 2026-11-04, replacing "AOS stability work, May–Jul 2026", which named the wrong
cause). The label states the measured effect and its mechanism; the grey span still marks *when*,
and its edges are still found from the data by `SPAN_MEDIAN_S`.

Note the span (week of 18 May – week of 29 Jun) is **wider than the episode proper** (3–30 Jun).
That is correct and not a mismatch: the same pre-slew wait was already running at a ~30 % rate
from mid-May, which is what lifts those weekly medians. The label says "Jun 2026" because that is
when the rate reached ~100 % and the +6 s applies to essentially every visit.

## Caveats

- The gap includes everything between shutter close and the next shutter open: slew, settle,
  filter changes, AOS corrections, scheduler latency. Sub-timings are not shown; Lynne Jones is
  redoing the slew-flag matching (two set/clear pairs per gap when the AOS correction carries a
  pointing offset, #survey-performance 10 Sep 2026).
- The June 2026 rise is a fixed ~6 s per-visit delay, 2026-06-03 to 06-30, caused by AOS
  corrections being applied serially before each slew (OSW-2269, RSO-785); the gap came back to
  ~8 s in July. See "What happened in June 2026". It is *not* the AOS stability *work*, which
  earlier versions of this README asserted.
- The slew-model cache used by test 3 covers **May–Oct 2026 only**, so that test speaks to the
  episode and its recovery, not to the full Oct 2025 – Jul 2026 window.
- Filter changes are in the sample (1.9 % of pairs, median gap 148 s) but land far off the
  histogram scale, so they never affected the 14–20 s band either way.

## Colours

The **series colour is the Rubin brand teal `#058B8C`** (`rubin_palette.TEAL`, the same as
`CATEGORICAL[0]`) — histogram bars and the weekly median line. Bruno asked for `058b8cff` on
2026-11-04, i.e. the brand teal at full opacity, in place of the deck's darker Science `#024243`
that these panels briefly carried. Matplotlib has no alpha channel in these hexes, so the `ff` is
the default (fully opaque) and `#058B8C` is equivalent.

The **median rule is drawn twice** (`contrast_vline`), `#2B2B2B` and `#F2F2F2` dashed with
complementary phase at `MEDIAN_ALPHA = 0.5`. A single `#595959` dash had too little contrast
where the rule crosses the tall teal bars; interleaving a light and a dark dash means the light
segments carry the line over the bars and the dark ones over the white ground, at any bar height.
The "median 9.4 s" label takes `#2B2B2B` to match. The **requirement label is rotated 90°** and
sits in the empty 0–5 s margin to the left of its line, rather than over the rising edge of the
distribution.

The **25–75 % band is the same teal at `BAND_ALPHA = 0.5`**, not the deck's flat pale teal
`#D9F7F7`. The pale teal had too little contrast against the grey episode span, and a translucent
tint of the line's own colour reads as "the spread of *this* series" rather than a fourth colour.
Where the band crosses the span the two translucent fills composite, so the overlap goes a shade
darker instead of one hiding the other.

The remaining neutrals come from the deck (`rubin_color_pallete.DECK`, read off slides 2 and 5)
rather than being hard-coded here: median rules and annotation text `#595959`, reference lines and
the episode span `#BFBFBF` (span at 30 % alpha), axis ink `#1F2937`. `DECK` is a deliberate
departure from `rubin_palette.CATEGORICAL` — the deck predates the palette; use `CATEGORICAL` for
anything that is not for this deck. `DECK["band"]` is now unused by these panels.

Note this leaves the panels **off the deck's Science colour**: if slide 7 needs to match the
slide-5 legend exactly, set `C["gap"] = rp.DECK["science"]` (one line). The deck accent `#F5A623`
is no longer on the talk panels at all — it was the 14–20 s shading, and now appears only on the
`--excess` diagnostic. The requirement line keeps the palette red (`CATEGORICAL[3]`) rather than
taking the freed accent: red is what the earlier figure used and what the slide text refers to.

## Run

```bash
python visit_gap_anatomy/python/make_visit_gap_figure.py           # combined + the two panels
python visit_gap_anatomy/python/make_visit_gap_figure.py --split   # just the two panels
python visit_gap_anatomy/python/make_visit_gap_figure.py --excess  # + the excess diagnostic
python visit_gap_anatomy/python/check_late_correction.py           # the three band tests
python visit_gap_anatomy/python/june_2026_excess.py                # the seven June 2026 tests
```

Palette from `../rubin_color_pallete` (copy it in before extraction). To refresh the data,
re-run the `nightly_survey_speed` ConsDB fetch and copy the columns listed in the script.
