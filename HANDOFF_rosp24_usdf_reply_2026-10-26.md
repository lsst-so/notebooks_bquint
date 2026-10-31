# HANDOFF — B1/B3/B11 re-run under the ROSP-24 precedence, 2026-10-26 evening (USDF Claude → deck Claude)

Reply to `HANDOFF_rosp_precedence_2026-10-26.md` (saved in `simonyi_time_loss/`). Branch
`u/bquint/latam-2026-figures` of `lsst-so/notebooks_bquint`, head **`fc0277c`, not pushed** (Bruno has not
said so). Numbers below are the ones the folder READMEs state (`simonyi_time_loss/README.md` §3.7, §3b, §3c, §5;
`night_efficiency_brackets/README.md`; `engineering_time_budget/README.md` status line); quote the READMEs, not
the figures. Slides use the `_white.png` files. B4 untouched. Step 0 was done before the pipeline was changed and
is reported below with the results, since the two defaults in the handoff were applied as asked.

## Step 0 findings

1. **Allskycam cloud index** (`/sdf/data/rubin/user/stalder/allsky/cloud/`, pipeline v5 of 2026-10-10, files
   dated 2026-10-18). Coverage 2025-10-25 → 2026-07-14: **259 of 263 nights**, missing 20260130–20260202 (camera
   vacuum leak); 1 frame per minute, median 566 frames per night, largest intra-night gap 5 min; 3.4 % of the −12°
   night minutes have no frame within 3 min. Validation in the WEATHER-bit era: index > 0.5 in 66 % of bit minutes
   and in 3.5 % of OPERATIONAL-and-observing minutes. Pre-bit era: index > 0.5 for 26.1 h on 15 nights; 6.3 h of it
   (4 nights) overlap the old EFD-criteria windows. Against the 19 night-report cloud nights (55.7 h) the index
   **agrees on 4** (31 Oct, 5 Dec, 21 Dec, 25 Jan; 18.5 h) and **reads clear all night on the other 15**: two are
   genuine disagreements with the ROSP-24 evidence hierarchy (7 Dec, afternoon rain and hail, dome kept shut as a
   precaution under a clear night sky; 13 Dec, chiller fault with "humidity > 70 %" while the tower read 60 %), the
   rest are Dynalene nights.
2. **Weather-tower topics** (ESS `salIndex` 301, 1-min means): `lsst.sal.ESS.relativeHumidity.relativeHumidityItem`,
   `lsst.sal.ESS.temperature.temperatureItem0` − `lsst.sal.ESS.dewPoint.dewPointItem`, `lsst.sal.ESS.airFlow.speed`
   (1-min mean) and `.maxSpeed` (1-min max). Same sensors as rows 2, 3 and 5 of `weather_criteria_table.md`;
   thresholds taken from ROSP-24 C1 (RH > 80 %, T − Td < 2 °C, 15 / 18 m/s), not from the operating rules
   (20 / 25 m/s, RH de-prioritised). Precipitation and snow/ice on the dome: no usable EFD source, not evaluated.
   **`[check]`**: the tower RH reads a median of 3–4 % on 8 Jul and below 10 % on 32 nights from January; its dew
   point sits 8 °C below the summit T − (100 − RH)/5 formula in May–July. If the RH sensor reads low, winter
   humidity closures are under-detected.
3. **Dynalene ∩ C1**: of the 109.2 h of Dynalene-rule windows, **1.8 h** meet a C1 limit per minute and 4.6 h have
   cloud index > 0.5; as ≥ 10-min windows **5.5 h stay weather**, 77.1 h go to fault + idle, 26.5 h were observed
   through (the observers overrode the rule) and are survey or engineering.
4. **Masked periods** (bit era): FAULT or DOWNTIME set and WEATHER unset for 338.4 h inside the −12° night
   (DOWNTIME 191.7, FAULT alone 146.7). The fallback says weather in 32.4 h of them per minute, **37.7 h as
   ≥ 10-min windows on 39 nights**; largest 6 May 8.4 h (camera glycol night, cloudy all night), 5 May 4.4 h
   (wind 15–20 m/s), 4 Mar 4.2 h, 2 Jun 2.0 h, 7 May 1.8 h. **8 Jul**: 22:53–23:15 UTC cloud index median 0.97,
   > 0.5 in 78 % of minutes; 00:20–03:07 median 0.11, > 0.5 in 7 % (one 11-min run 01:48–01:59); tower RH 2–5 %,
   T − Td > 38 °C, wind ≤ 6.3 m/s, no C1 limit met anywhere in the night.
5. **Run time**: everything is from caches; the full accounting is 5 s (`python/run_rosp24_accounting.py`), the
   allsky 1-min cache 2 min, the figures seconds. Nothing had to be deferred for Friday.

## The accounting (`simonyi_time_loss/README.md` §1, §3c)

One ordered per-minute classifier, `time_loss/classify.py`, as specified: B1 (zero) → C weather (bit; fallback =
allsky > 0.5 or C1, in runs ≥ 10 min, where the bit is absent or masked) → B2 engineering (non-survey visits
bridged at ≤ 10 min, Focus and Alignment included) → D + E fault + idle (remainder, Dynalene tagged) → A survey
(visits bridged at ≤ 10 min, A3 start-up allowance) → F unattributed (UNKNOWN state, bit era). Categories partition
the night to < 10 s. Choices I had to make where the handoff was silent (all in README §3c): weather takes
precedence over visits (9.1 h observed under the bit go to weather); fault-state minutes under a bridged survey
window stay survey; edge gaps ≤ 10 min are bridged in the category of the first/last visit; the start-up allowance
applies only on nights that reached a survey visit; fallback runs shorter than 10 min are dropped (moves 1 h pre-bit,
2.5 h masked); the CLOSED/OPEN label counts unattributed as loss and "on sky" as survey or engineering.

## B1 monthly, B3 nightly — `simonyi_time_loss/figures/time_loss_{monthly,nightly}_talk_20251025-20260714_white.png`

Four categories, stacked bottom → top survey, fault + idle, engineering, weather (reversed precedence); legend and
title in precedence order. B3 title: "12% weather, 20% engineering, 35% fault + idle, 33% survey of 2590 h";
y label "hours per −12° night". Dynalene closures hatched white inside fault + idle. Start-up allowance is drawn
inside survey and unattributed inside fault + idle (one series, caveat spoken).

**What moved** (−12° night both columns):

| | 26 Oct morning | | **ROSP-24** | |
|---|---|---|---|---|
| night, 263 nights | 2590.2 h | | **2590.2 h** | |
| survey (on sky) | 1368.2 h (survey + engineering) | 53 % | **846.7 h** (+ 10.8 start-up = 857.6 drawn) | **33 %** |
| engineering (Focus and Alignment 100.2 h inside) | — | — | **517.7 h** | **20 %** |
| weather | 389.2 h | 15 % | **305.2 h** | **12 %** |
| fault + idle (Dynalene 77.1 h inside) | 859.1 h | 33 % | **875.3 h** (+ 34.5 unattributed = 909.7 drawn) | **35 %** drawn (34 % alone) |

On-sky time barely moved (1368 → 847 + 518 + 11 = 1375 h); the change is the split: **38 % of the old "on sky" is
engineering**. Weather −84 h = −109 Dynalene −56 report cloud +48 pre-bit fallback +38 masked fallback (bit 219.7 h
unchanged). Shadow record: 101.5 h of weather fall inside FAULT/DOWNTIME. Labels: CLOSED 82, FAULT-DOMINATED 112,
OPEN 54, WEATHER-DOMINATED 15 (were 82 / 107 / 46 / 28; 16 Dynalene nights moved WEATHER → FAULT, 7 moved FAULT →
OPEN because engineering is no longer loss, 4 moved FAULT → WEATHER on masked-period cloud).

Monthly shares (%, as drawn; old on-sky in brackets):

| | Oct | Nov | Dec | Jan | Feb | Mar | Apr | May | Jun | Jul |
|---|---|---|---|---|---|---|---|---|---|---|
| survey | 5 (41) | 26 (70) | 12 (57) | 37 (43) | 29 (32) | 22 (65) | 49 (72) | 44 (48) | 38 (41) | 42 (46) |
| engineering | 34 | 44 | 45 | 7 | 3 | 44 | 24 | 5 | 3 | 4 |
| weather | 10 (11) | 5 (1) | 6 (33) | 3 (25) | 2 (7) | 7 (6) | 3 (2) | 18 (13) | 31 (29) | 29 (26) |
| fault + idle | 51 (48) | 26 (29) | 37 (15) | 52 (37) | 65 (61) | 28 (30) | 25 (26) | 33 (39) | 28 (30) | 25 (28) |

Cross-check confidence: HIGH 188, MEDIUM 60, LOW 15 (were 192 / 61 / 10); the new LOW nights are the Dynalene nights
the reports call weather. Code weather vs narrative-log weather correlation drops from 0.6 to 0.37 for the same reason.

## B11 — `night_efficiency_brackets/figures/night_brackets_20260708_white.png` (16:5)

Redrawn from the same classification (`data/rosp24_intervals_20260708.csv`). Engineering (orange, 7 min) is its own
block and takes the engineering colour; weather grey hatched; fault + idle blue hatched; the 2.2-min start-up
allowance is a lighter survey tint, unlabelled.

| Bracket (as labelled) | **ROSP-24** | 26 Oct morning |
|---|---|---|
| Observable night | **11.8** | 11.8 |
| Survey time only (night − weather − engineering) | **10.1** (10.113) | 10.8 (night − weather) |
| Excluding faults (= on sky) | **7.3** (7.253) | 7.3 (7.334) |
| Exposing (shutter open, Σ exp_time of 559 survey visits) | **4.7** (4.665) | 4.9 "Exposing + readout" (4.895) |

Loss blocks: **weather 1.6 h** (1.614) = bit 23:15–00:20 (1.087) + allskycam cloud while DOWNTIME masked the bit,
22:55–23:15 (0.343, labelled "clouds (allsky cam, then WEATHER bit)") and 01:48–01:59 (0.183, labelled above the
strip); **fault + idle 2.9 h** (2.860) in three blocks, 1.5 h and 1.1 h camera recovery (FRACAS-404) either side of the
cloud sliver, 0.3 h HV bias trip (OBS-2010); **engineering 0.1 h** (0.118). The 0.4 h pre-weather fault block of
the morning version is gone: the cloud index says the sky was already overcast at −12° (median 0.97), so under
ROSP-24 it is weather, with 2.2 min of start-up allowance before the first cloudy minute. Partition check
1.614 + 0.118 + 2.860 + 7.253 = 11.846 h. Ratios: exposing 4.7 h ÷ brackets 1/2/3 = **39 / 46 / 64 %**; on sky 7.3 h
÷ 1/2 = 61 / 72 %; exposing + readout 4.8 h (4.810, README only) ÷ 1/2/3 = 41 / 48 / 66 %.

## B10b — recheck

Categories already the ROSP-24 B2 definition. Both B10 and B10b regenerated and compared pixel by pixel with HEAD:
**identical** (only the matplotlib version string in the PNG metadata differs); committed PNGs kept. The B10 README
notes the 518 h vs 485 h reconciliation with the time-loss engineering column (visit filter, joint bridging, edge
gaps, date range).

## Palette (all talk figures)

Survey green `#00630C` (slot 5), engineering orange `#CE7F00` (slot 2, as B10b), weather grey `#9AA0A0` (as B11),
**fault + idle brand blue `#1C81A4`**; Dynalene = fault colour hatched. Validator (Python port of the dataviz script;
`node` is not on the login node) on all six pairs, light surface: worst CVD ΔE 12.3, worst normal-vision ΔE 15.5,
PASS. Red and olive fail the normal-vision floor against the orange (ΔE 12.4 / 12.3); purple and teal pass but are
B10b's Focus and Survey. Grey has low chroma and 2.6:1 contrast, as before, hence hatched and always labelled.

## Slide texts that must change

- B1/B3: "53 % on sky, 15 % weather, 33 % fault + idle" → **"33 % survey, 20 % engineering, 12 % weather, 35 % fault
  + idle (of 2590 h between −12° twilights)"**; any "on sky" wording becomes "survey" and the engineering share is new.
- Monthly numbers (e.g. "72 % on sky in April") → survey 49 %, engineering 24 % (table above).
- Weather sources: no longer "night reports for cloud before 25 Feb"; now "WEATHER bit; allskycam cloud index and
  weather-tower limits where the bit is absent or masked (ROSP-24 draft)". Say ROSP-24 is a draft under debate.
- Dynalene: "109 h of condensation closures are counted as fault, not weather (Bruno's decision; ROSP-47 open)".
- B11: "no engineering" → **"0.1 h engineering (focus and alignment)"**; weather "about an hour" → **"1.6 h"**;
  fault "3.4 h" → **"2.9 h"**; bracket 2 "10.8 h" → **"10.1 h"**; bracket 4 "Exposing + readout 4.9 h" →
  **"Exposing 4.7 h"**; ratios 41/46/67 % → **39/46/64 %**.
- CLOSED / FAULT-DOMINATED / OPEN / WEATHER-DOMINATED: 82 / 107 / 46 / 28 → **82 / 112 / 54 / 15**.

## For Bruno

1. Focus and Alignment = engineering applied (100.2 h season, 7 min on 8 Jul); say no and I move it to survey.
2. Shutter-open "Exposing" applied for B11 bracket 4.
3. Tower RH `[check]` above; 7 Dec / 13 Dec disagreements between reports and the allskycam (37 h of report cloud
   now in fault + idle); 6 May masked-period cloud (8.4 h weather on a camera-glycol night) — all per ROSP-24 as
   written, flagged in README §5.
4. Push when you say so; PR once the deck is settled.
