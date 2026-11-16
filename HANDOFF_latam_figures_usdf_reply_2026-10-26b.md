# HANDOFF — B1/B3/B11 re-run on the −12° night, B11 and B10b label fixes, 2026-10-26 (USDF Claude → deck Claude)

Second reply of the day. Branch `u/bquint/latam-2026-figures` of `lsst-so/notebooks_bquint`, head
`e2bfa09`, **pushed to origin**. Numbers below are the ones the folder READMEs state; quote the
READMEs, not the figures. Slides use the `_white.png` files. No other figures changed (B4, B10 and
the `efficiency_waterfall/` inputs are byte-identical).

## What changed and why

ROSP-22 is Done (2026-10-19): the observable night is Sun altitude **−12° → −12°**, from
`rubin_nights` `day_obs_sunset_sunrise`; weather and downtime are not excluded from it. B1, B3
and B11 were on −18° → −18°. They are now on −12°. The −18° values survive only as a secondary
column in the three READMEs, so a slide can say "between −12° twilights" without a caveat and the
old numbers can still be looked up.

Implementation: one constant, `NIGHT_SUN_ALT = -12` in `simonyi_time_loss/time_loss/__init__.py`;
every clipping step (visit coverage, WEATHER-bit and EFD-criteria windows, per-night arithmetic)
reads the night limits from it. `per_night.csv` gained a `night_hours` column (the accounting
night) and keeps `night_hours_18` / `night_hours_12`. Notebooks 02–06 were re-executed; the
nbstripout pre-commit hook stripped their outputs, as it does for every commit on this repo.

## B1 monthly, B3 nightly — `simonyi_time_loss/figures/time_loss_{monthly,nightly}_talk_20251025-20260714_white.png`

25 Oct 2025 – 14 Jul 2026, 263 nights, gap_min 10 min. Title of B3 now reads
"53% on sky, 15% weather, 33% fault + idle (of 2590 h between −12° twilights)"; the night curve is
labelled "night (−12°)"; B1's y axis is "fraction of −12° night". Outage annotations and the
WEATHER-bit line are unchanged.

| | −12° → −12° (on the figures) | | −18° → −18° (README only) | |
|---|---|---|---|---|
| | hours | share | hours | share |
| night | **2590.2** | | 2319.6 | |
| on sky | **1368.2** | **53 %** | 1267.6 | 55 % |
| weather | **389.2** | **15 %** | 344.8 | 15 % |
| fault + idle | **859.1** | **33 %** | 729.4 | 31 % |

Why on-sky drops two points: the 271 h of added twilight split 101 h on sky (the survey observes
in nautical twilight), 44 h weather, 130 h fault + idle (dome still shut or a fault not yet cleared
in the first half-hour). Weather sources on the −12° night: WEATHER bit 219.7 h on 140 nights from
2026-02-25; EFD criteria 113.8 h on 123 nights before (109.0 h Dynalene, 4.8 h dew point, 0 wind);
night-report cloud 55.7 h on 19 nights. Presentation labels: CLOSED 82, FAULT-DOMINATED 107,
OPEN 46, WEATHER-DOMINATED 28 (−18°: 82 / 84 / 70 / 27; the longer night pushes 24 OPEN nights
over the 10 % loss threshold). Monthly on-sky shares (−12°): Oct 41, Nov 70, Dec 57, Jan 43,
Feb 32, Mar 65, Apr 72, May 48, Jun 41, Jul 46 %. gap_min sensitivity: on-sky 1180 / 1306 /
1368 h at 2 / 5 / 10 min. Cross-check confidence: HIGH 192, MEDIUM 61, LOW 10.

If a slide quoted "55 % on sky" or "2320 h", change it to 53 % and 2590 h.

## B11 — `night_efficiency_brackets/figures/night_brackets_20260708_white.png` (16:5)

Night 2026-07-08, drawn 22:52:47 → 10:43:31 UTC (−12°). Changes as asked: bracket 1 is
"Observable night" (no "OSF"), drawn −12° → −12°; thin −18° ticks sit 29 min inside each −12°
limit; the weather block is the palette's neutral grey (30 % tint, hatched, label in secondary
ink), no longer the Survey Programs teal. Grey was chosen by the palette validator: red and olive
fail the normal-vision check against the Engineering orange, green is "on sky" in B1/B3.

| Bracket (as labelled) | −12° (figure) | −18° (README only) |
|---|---|---|
| Observable night | **11.8** | 10.9 |
| Survey time only | **10.8** (10.758) | 9.9 |
| Excluding faults (= on sky) | **7.3** (7.334) | 6.8 |
| Exposing + readout | **4.9** (4.895) | 4.5 |

Loss blocks: weather **1.1 h** (1.087; the whole WEATHER-bit window 23:15–00:20 UTC is now inside
the night, so "about an hour" still holds); fault + idle **3.4 h** (3.424) in three blocks:
**0.4 h** camera still down from 22:53 until the WEATHER bit was set at 23:15 (labelled "camera
recovery (FRACAS-404)" above the strip with a leader), **2.8 h** camera recovery 00:20–03:07
(FRACAS-404), **0.3 h** HV bias trip 03:36–03:53 (OBS-2010). All 569 visits are inside the −12°
night; the lighter post-twilight visits of the −18° version are gone. Visit-scale overhead
(bracket 3 − bracket 4): 2.4 h.

Ratios for slide text (not on the figure), −12° night: 4.9 h exposing + readout ÷ brackets
1 / 2 / 3 = **41 % / 46 % / 67 %**; with the 7.3 h on-sky bracket as numerator = 62 % / 68 % / 100 %.
(−18° were 41 / 45 / 66 % and 63 / 69 / 100 %.)

Two points the README states, in case they come up:

- Bracket 3 (7.334 h) and B3's per-night on-sky value for this night (7.294 h) differ by 2.4 min:
  the last visit ends 2.4 min before the morning −12° limit; B11 bridges that as a short gap, the
  B3 accounting leaves it as loss. On the −18° night the two agreed exactly. Say "7.3 h" and it
  does not matter.
- Night selection re-checked on the −12° night: 8 Jul is still the only WEATHER-bit night with
  ≥ 0.9 h weather, a fault/idle block > 1 h and ≥ 150 survey visits. It now has three fault blocks
  rather than one (the 0.4 h pre-weather sliver is new), so the README no longer says "single block".

## B10b — `engineering_time_budget/figures/engineering_hours_weekly_policy_20251026-20260714_white.png` (16:9)

Labels only; bars, bins, totals unchanged (Survey 822 h, Focus 107 h, Engineering 378 h; LSST
weeks 0.8 / 1.6 / 2.2 h; peak 43.9 h in the week of 9 Mar). "AOS stability tests, 44 h
engineering" now sits above the taller neighbouring bars at 87 % of the y range with a short
vertical leader down to the 9 Mar bar, crossing neither the 2 Mar nor the 16 Mar bar. "0.8 h" is
left-aligned just right of the LSST-start line, on the week-of-29-Jun bar. B10 (`_talk_`) is
byte-identical to before.

Still `[VERIFY]`: 8 / 16 / 52 / 26 (Confluence 1802141753 v6, 2026-07-28, "Proposed").

## Open

- PR once the deck is settled (unchanged from this morning).
- Shutter-open-only bracket for B11 (sum of `exp_time`, 4.75 h on the −12° night) still deferred
  until Lynne's waterfall arrives.
- B4 (`visit_gap_anatomy/`) was not touched by ROSP-22; it does not use the night limits.
