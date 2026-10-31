# HANDOFF — Shared category colours + Focus split, 2026-10-31 (VS Code Claude → next session)

Repo `lsst-so/notebooks_bquint`, branch `u/bquint/latam-2026-figures`, pushed, head `393249e`.
For the LSST@LATAM talk (São Paulo, 2–6 Nov 2026). This continues the Cowork handoff of the same
day (summarised below so this file stands alone).

## How Bruno wants to work
- Step by step, small changes, show the diff before moving on. Short replies (≤ 3 paragraphs, high
  level); he asks to go deeper. He presents this talk, so he must understand every change.
- VS Code Claude edits code and pushes; Bruno runs on USDF himself and reports back on the plots.
- For colour choices he decides **by eye**: render mock-ups locally and show him before committing.
  Local matplotlib is in `~/miniforge3/bin/python` (system `python3` has none, no LSST stack).
- After the code is done: slide-by-slide review of the LATAM deck (id
  `1KfSZy5BCR0M3Go_rirQL9rUvOmbdiirxW16iVHgmQbA`). Slide text follows the figures, never the reverse.

## Background (from the Cowork handoff)
- 27 Oct: **Focus and Alignment (BLOCK-T539) is its own category**, neither engineering nor survey.
  Story: early in operations the telescope was realigned many times a night; focus time shrinking over
  the months shows the lookup tables / initial conditions improved.
- Commit `9ef71f7` ("drop WIP") holds the classifier side only: `simonyi_time_loss/time_loss/classify.py`
  (precedence weather → focus → engineering → fault + idle → survey), focus columns in
  `python/run_rosp24_accounting.py` and `python/gap_min_sensitivity.py`. Bruno decides whether to keep
  or squash it.
- Definitions match across `nightly_survey_speed/utils.py`, `engineering_time_budget/` and
  `simonyi_time_loss/`: Survey Programs = BLOCK-407/408/416/417/419/421; Focus and Alignment =
  BLOCK-T539; everything else = Engineering. Known difference: time-loss also counts
  `img_type = engtest` (~1412 visits), nightly survey speed uses acq/science/cwfs/focus only →
  note in README, maybe say it in the talk.

## Done today (steps 1–2 of the plan)
Two commits, both pushed:
- `a901529` — added `CATEGORY_COLORS` to `rubin_color_pallete/rubin_palette.py` (+ README section) and
  pointed every category plot at it:
  - `simonyi_time_loss/time_loss/style.py` (B1/B3; keeps its own `COLORS` keys, values now from the table)
  - `engineering_time_budget/python/make_engineering_hours_figure.py` (B10/B10b)
  - `night_efficiency_brackets/python/make_night_brackets_figure.py` (B11)
  - `nightly_survey_speed/utils.py` — `rubin_category_colors()` now reads the palette instead of the
    `lsst.utils` style; the interactive notebook and `make_utilization_annotated.py` follow through it.
- `393249e` — final colour values after Bruno saw the first version on USDF.

Final table (`rp.CATEGORY_COLORS`, keys in precedence order):

| Key | Category | Colour |
|---|---|---|
| `weather` | Weather | `#B4B8B8` light grey, always hatched and labelled |
| `focus` | Focus and Alignment | `#029E73` green |
| `engineering` | Engineering | `#DE8F05` orange |
| `fault_idle` | Fault + idle | `#4A4D4E` charcoal |
| `survey` | Survey Programs | `#0173B2` blue |

How we got there (so nobody re-proposes the rejected options):
- First version (`a901529`): brand blue `#1C81A4` / palette orange `#CE7F00` / palette green `#00630C` /
  wine `#5E1A33` / grey `#9AA0A0`. Passed the validator, but on USDF Bruno found B1/B3 "horrible":
  the wine dominates (fault + idle is the biggest block) and blue + orange + wine clash. Note: brand blue
  `#1C81A4` is Pantone 2454 C, *not* the Rubin teal `#058B8C`.
- **Bruno's constraint: the nightly survey speed plot must stay exactly as David and Bob have shown it**,
  so survey/engineering/focus take its original seaborn-colorblind values and the other figures follow.
  With those, the old grey `#9AA0A0` fails the normal-vision floor vs the green (14.8) → lighter grey.
- Fault + idle candidates mocked on real B1 monthly and B3 nightly data: charcoal `#4A4D4E`, seaborn pink
  `#CC78BC`, berry `#A2457A`, plum `#563D5C`, dark brown `#56423E`. All reach the same CVD 9.2 (the
  ceiling set by the survey speed orange vs green). Bruno picked **charcoal** "for simplicity, to move
  on" — he finds the nightly plot hard to read with any option, so this may be revisited.
- Validator (dataviz `validate_palette.js`, all pairs, white): worst CVD ΔE 9.2 (orange vs green,
  protan), worst normal ΔE 16.9; the two greys fail band/chroma by design; orange 2.6:1 and weather
  grey 2.0:1 contrast → labels/hover/table. Recorded in the palette README.

Deliberately **not** changed:
- `nightly_survey_speed/downtime.py` (and its copy `simonyi_time_loss/time_loss/downtime.py`): the
  downtime overlay has its own six-category table (fault red, weather teal, planned, mixed, degraded,
  unknown). Bruno: leave it untouched for now, the plot must be the same in all presentations.
- `nightly_survey_speed/notebooks/on_sky_utilization_repro.ipynb` keeps `tab:` colours (it reproduces
  the original figure).
- B4 (`visit_gap_anatomy`), `efficiency_waterfall`, `observatory_high_level_performance`: they use the
  palette for other roles, not these categories.

## Next steps
3. **B1/B3/B11 draw Focus and Alignment as its own block**, legend order = precedence.
   - B1/B3: `simonyi_time_loss/python/make_latam_figures.py`, `CAT` list (~line 75) has no focus entry;
     `engineering_hours` still includes focus in the 26 Oct `per_night.csv`
     (`focus_alignment_hours` column exists; check whether the 9ef71f7 classifier already removes it
     from `engineering_hours` once re-run on USDF). Also check the weather segment gets its hatch.
   - B11: focus visits already drawn as their own category in the strip (now green), but the legend
     label still says "engineering (Focus and Alignment, BLOCK-T539)" and the brackets still fold
     focus into engineering ("Survey time only" = night − weather − engineering).
   - B11: weather (30 % tint of `#B4B8B8`) and fault (18 % tint of `#4A4D4E`) may both read as pale
     greys — ask Bruno how it looked on USDF; adjust tints if needed.
4. Update READMEs: focus is no longer inside engineering (`simonyi_time_loss/README.md` lines ~32, 265,
   369, 388, 438; also `night_efficiency_brackets/README.md` ~line 140 still describes the old colours),
   plus the "numbers that must change" list.
5. Push → Bruno runs on USDF → ask for: season and **monthly focus hours** (does focus shrink month by
   month? that is the slide's claim), new B1/B3 shares, B11 bracket numbers.
6. Slide-by-slide deck review.

## Open items carried over
- B10b policy numbers 8 / 16 / 52 / 26 still `[VERIFY]` (Confluence 1802141753 v6, "Proposed").
- B10b policy line is palette red `#DB5451` next to the orange; red vs orange was below the
  normal-vision floor in earlier checks (it is a labelled line, so lower priority).
- Tower RH sensor reads suspiciously low (README §5 `[check]`); 7 Dec / 13 Dec report-vs-allskycam
  disagreements.
- Shutter-open bracket for B11 waiting on Lynne's waterfall.
- PR once the deck is settled.
