# HANDOFF — Re-run the LSST@LATAM time-loss figures under the ROSP-24 precedence order (deck Claude → USDF Claude, 2026-10-26)

Received 2026-10-26 (file `HANDOFF_rosp_precedence_2026-10-26 (2).md`); saved here verbatim as the specification of the
ROSP-24 re-run. The reply is `../HANDOFF_rosp24_usdf_reply_2026-10-26.md`.

Branch `u/bquint/latam-2026-figures` of `lsst-so/notebooks_bquint`, head `e2bfa09` (your second reply of
today). Same rules as before: don't invent, cite every number, don't push without asking, report Step 0
before touching the pipeline, quote the READMEs. Deadline: the talk is 2–6 Nov; Bruno needs the figures
by **Fri 30 Oct**.

## Why

Bruno's standing rule: every plot in the talk follows requirements and ROSP. The draft loss-cause
taxonomy (ROSP-24, status Verifying, Brian Stalder) fixed a precedence order on 2026-10-19 and added
rules on 2026-10-26. The current `simonyi_time_loss` accounting matches it in part (weather subtracted
first, unplanned DOWNTIME counted as fault, −12° night) and departs from it in the places listed under
"Rules". ROSP is new and under debate; Bruno will say so in the talk and cannot change any definition
himself. Where the draft is silent he has chosen an interpretation (marked **Decision**), and where a
question is still open we keep the current rule and say so (marked **Deferred**).

Sources, all read 2026-10-26:
- ROSP-24 (Jira) comments of 2026-10-10, 10-19 (new precedence), 10-22, 10-25, 10-26 (rules).
- Confluence 2033909769 v5, "Time-Loss Accounting (weather / fault / scheduled)".
- ROSP-22 Done 2026-10-19: observable night −12° → −12°, weather and downtime not excluded.
- ROSP-28: planned maintenance is not separable from other downtime in the observatory states; the
  only planned-downtime block in the ledger is 14 Sep → 5 Oct 2026 (noon UTC to noon UTC).

## The precedence (ROSP-24, 2026-10-19)

Time goes to the first category in this list that applies:

1. **B1 Planned maintenance**
2. **C Weather** — masks faults, idle and unplanned downtime; fault time during a closure goes to a
   shadow record, not the headline
3. **B2 Engineering**
4. **D Technical fault** (D2 long, D1 short, D4 unplanned DOWNTIME, D3 gap excess beyond the slew model)
5. **E Operational idle**
6. **A Science operations** (A1 shutter open, A2 necessary overhead, A3 night start-up within allowance)
7. **F Unattributed**

Implement it as one ordered per-minute classifier over the −12° night, in `time_loss/`, so every
figure and `per_night.csv` come from the same assignment. Keep the shadow record: minutes that would
have been fault but were masked by weather, as a separate column (`weather_masked_fault_hours`).

## Rules, category by category

**B1 Planned maintenance.** None in 25 Oct 2025 – 14 Jul 2026 (ROSP-28). Category exists in the code,
is zero in the period; the README says so.

**C Weather.** Evidence hierarchy from ROSP-24 §C:
- From `day_obs` 20260225: the WEATHER bit is the decision and the primary source (as now).
- Fallback, used whenever the bit is absent (before 20260225) **or masked** (FAULT or DOWNTIME active
  and the bit not set): the allskycam cloud index > 0.5 (Brian's product, USDF
  `/sdf/data/rubin/user/stalder/allsky/`, 2021-07 onward) plus the EFD weather-tower limits of C1:
  RH > 80 %, dew-point depression < 2.0 °C, wind > ~15 m/s average or gusts > ~18 m/s (20/25 m/s from
  Oct 2026, outside our range), precipitation or snow/ice on the dome.
- Night-report cloud hours (55.7 h on 19 nights) are **dropped** as an hour source: narrative log and
  night reports are annotation only. Keep them in `per_night.csv` as `report_cloud_hours` for the
  cross-check table, not in the accounting.
- **Decision (Bruno, 2026-10-26): the Dynalene − dew-point condensation rule is no longer weather.**
  The system was designed to observe in those conditions; failing to is a fault. Its windows
  (109.0 h, Dec 2025 – Jan 2026, FRACAS-330) go to D (D4-like), tagged `dynalene_closure`, and are
  drawn hatched inside the fault colour. Only minutes that also meet a C1 condition (dew-point
  depression < 2 °C, RH > 80 %) stay weather. ROSP-47 ("dome closed by policy") is open; the talk says
  so. Keep `dynalene_hours` in `per_night.csv` so the shift can be quoted.
- C3 weather standby (idle while confirming conditions) counts as weather only where the bit or the
  fallback says so; we have no other evidence for it.

**B2 Engineering.** Every on-sky visit that is not a survey visit, using the categories of
`engineering_time_budget` (Survey Programs = BLOCK-407/408/416/417/419/421; everything else is
engineering). Blocks bridged at gaps under 10 min, as there. Comes **out of "on sky"**: the green in
B1/B3/B11 becomes survey visits only.
- **[Bruno to confirm, default = yes]** Focus and Alignment (BLOCK-T539) counts as engineering. The
  26 Oct rule reads "engineering = system available but not in survey operations; calibrations count
  as engineering, tracked separately". Report it as a sub-total so it can be moved if he says no.
  On 8 Jul this is 7 min; the slide text currently says "no engineering" and will change to 0.1 h.
- Closed-dome engineering: no source that gives hours (DOWNTIME mixes it with maintenance). It stays
  in fault + idle; the README says so. **Deferred.**

**D Technical fault + E Operational idle.** Everything in the night not assigned above and not covered
by a visit or a bridged gap, i.e. the current non-weather loss, now also minus engineering and plus the
Dynalene windows. Includes unplanned DOWNTIME (D4).
- Fault and idle stay **merged** ("fault + idle"); the IDLE bit exists only from 20260225 and Q7
  (fold idle into short faults?) is open under ROSP-50. **Deferred.** Report `idle_bit_hours`
  separately from 20260225 so the split can be quoted.
- The 10-minute gap rule stays. ROSP would split gaps into A2 (up to the slew model plus scatter) and
  D3 (excess), with a minimum fault duration still undecided (ROSP-49, Q8). **Deferred.** State in
  the README that gaps under 10 min are counted as on sky and therefore lump A2 and D3.

**A Science operations.**
- **A3 start-up allowance (new, 26 Oct):** the first 10 min after evening −12°, up to the first
  science visit, is science operations, not lost time. Overrun beyond 10 min is fault + idle (or
  weather / engineering if those apply first). Column `startup_hours`.
- A1 vs A2: on sky = survey visits plus bridged gaps (A1 + A2 + D3, see above). For B11 only:
  **[Bruno to confirm, default = yes]** bracket 4 becomes **shutter-open only** (A1, sum of
  `exp_time`, 4.75 h on the −12° night), labelled "Exposing"; "exposing + readout" (4.895 h) stays
  in the README. This follows ROSP's A1; readout is overhead there.

**F Unattributed.** From 20260225: minutes in the UNKNOWN observatory state → F, column
`unattributed_hours`, reported in the README (ROSP wants it small and shrinking). Before 20260225 there
are no states, so F cannot be separated from fault + idle. **Decision (Bruno): one series on the
plots, with the caveat spoken and in the README** ("before 25 Feb, fault + idle includes any time
that would be unattributed").

Night start/end: unchanged, `NIGHT_SUN_ALT = -12` from ROSP-22.

## Figures to regenerate (same file names, `_white.png` for the deck)

- **B1** `time_loss_monthly_talk_20251025-20260714_white.png` — stacked fractions, now four
  categories: survey (on sky), engineering, weather, fault + idle, with the Dynalene closure hatched
  inside fault + idle. Legend order = precedence order reversed (science at the bottom).
- **B3** `time_loss_nightly_talk_20251025-20260714_white.png` — same four categories per night under
  the −12° night curve; outage annotations and the WEATHER-bit line unchanged; title header updated
  to the new season shares.
- **B11** `night_brackets_20260708_white.png` — redraw with: engineering (purple, 7 min) as its own
  category if confirmed; bracket 2 "Survey time only" = night − weather − engineering; bracket 3
  "Excluding faults (= on sky)" = survey visits + bridged gaps; bracket 4 per the A1 choice above;
  start-up allowance: the first 10 min after 22:53 belong to A3, so the 0.4 h pre-weather fault block
  becomes ~0.2 h (recompute). Weather stays grey hatched; keep the three fault labels.
- **B10b** — recheck only: categories unchanged, so it should be byte-identical. Confirm.
- **B4** — not touched (no night-limit or category dependence).

**One palette across all talk figures**, one colour per category: survey green, engineering orange
(as in B10b), weather grey (as in B11), fault + idle a fourth colour that passes your palette
validator against the other three (today's B1/B3 use orange for fault + idle, which now collides with
engineering). Dynalene closure = fault colour, hatched.

## Step 0, report before changing anything

1. Allskycam index: coverage for 2025-10-25 → 2026-07-14 (nights with data, cadence, gaps), and the
   number of pre-20260225 nights where index > 0.5 overlaps the current EFD-criteria or
   report-cloud windows.
2. Weather-tower EFD topics and fields you will use for RH, dew point, wind; confirm against
   `weather_criteria_table.md` (Bruno's) and ROSP-24 C1.
3. How many hours the Dynalene windows overlap a C1 condition (those stay weather).
4. Masked periods from 20260225: total hours with FAULT or DOWNTIME set and WEATHER unset where the
   fallback says weather. For 8 Jul: the allskycam index and tower values for 22:53–23:15 and
   00:20–03:07 UTC.
5. Estimated run time. If any of 1–4 cannot be done by Friday, say which and propose the fallback
   (for 1: keep the EFD criteria without report cloud and say so).

## Deliverable

Same form as today's reply: per figure, the new numbers from the READMEs, a **"what moved" table**
with the 26 Oct −12° values beside the new ones (season hours and shares; monthly on-sky shares; B11
brackets and loss blocks; CLOSED / FAULT-DOMINATED / OPEN / WEATHER-DOMINATED counts), the Step 0
findings, and the list of slide texts that must change. Update the three READMEs with the new
accounting, the precedence list, the decisions and deferrals above, and the ROSP-24 ticket version
you read. `per_night.csv` gains: `engineering_hours`, `focus_alignment_hours`, `dynalene_hours`,
`startup_hours`, `idle_bit_hours`, `unattributed_hours`, `weather_masked_fault_hours`,
`report_cloud_hours`. Commit on the same branch; do not push until Bruno says so.
