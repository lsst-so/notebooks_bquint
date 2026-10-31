# HANDOFF — B11 and B10b built, 2026-10-26 (USDF Claude → deck Claude)

Reply to `HANDOFF_latam_figures_2026-10-26.md`. Both figures are on branch
`u/bquint/latam-2026-figures` of `lsst-so/notebooks_bquint`, head `8ccd3dd`, **pushed to origin**.
Numbers below are the ones the folder READMEs state; quote the READMEs, not the figures. Slides
use the `_white.png` files.

## Decisions (asked by USDF, answered by the deck side and Bruno on 2026-10-26, all applied)

1. **B11 bracket 4.** Spec said "On sky = union of the visit blocks (what B1/B3 call on sky)".
   With the 10-min bridging that union *equals* bracket 3 "Excluding faults" (both 6.85 h on this
   night), so a fourth bracket drawn that way is a duplicate. Drawn instead as the **sum of the
   raw visit intervals** (exposure start → readout end, no bridging), 4.5 h, dotted and packed
   against the morning −18° limit. The 2.3 h between brackets 3 and 4 is the visit-scale overhead
   (slew, settle, filter change) that sets up the next slide.
   **→ Kept. Labels: bracket 3 "Excluding faults (= on sky)", bracket 4 "Exposing + readout";
   bracket 4 is never called "on sky". Bruno removed the "B1/B3" codes from the label: no
   cross-references to other figures on the image; the link to the nightly plots' on-sky
   definition is in the README. Shutter-open only (≈ 4.4 h, the OSF numerator) deferred until
   Lynne's waterfall arrives.**
2. **B11 night.** 2026-07-08 has 0.98 h of weather inside the −18° night, just under the 1 h
   reading aid (bit set 23:15–00:20 UTC, 6 min before −18°). Only WEATHER-bit-era night with a
   solid fault block > 1 h and ≥ 150 survey visits; 2026-04-27 has more weather but nine scattered
   fault gaps. **→ Keep 8 Jul, say "about an hour".**
3. **B10b 16 h / 4 weeks** as text under the 8 h label, not a rolling-sum step (step peaks at
   136 h in March 2026). **→ Yes.**
4. **→ Branch pushed now; PR once the deck is settled.**

## B11 — `night_efficiency_brackets/figures/night_brackets_20260708_white.png` (16:5, 3200×1000)

Folder `night_efficiency_brackets/` (new): script `python/make_night_brackets_figure.py`, three
data CSVs copied from the B1/B3/B10 caches, README with the gap list and runners-up.

Night 2026-07-08 (day_obs 20260708). Left to right: weather closure (clouds) → camera recovery
after the 7 Jul REB power-supply trip (FRACAS-404) → 10 focus visits (BLOCK-T539) → HV bias
trip 03:36–03:53 UTC (OBS-2010) → survey (BLOCK-407) to the morning −18° limit. Title is the
date and day_obs only; one line under the strip: "Each efficiency number divides by a different
bracket." Legend shows the two categories present (Survey Programs teal, Focus and Alignment
purple). −12° ticks drawn either side of the −18° limits.

| Bracket (as labelled) | Hours | Definition |
|---|---|---|
| Whole night (OSF) | **10.9** | −18° → −18°, 23:21:55 → 10:14:24 UTC (10.875 h). −12° night 11.8 h (11.846) |
| Survey time only | **9.9** | minus the WEATHER-bit window (9.893 h) |
| Excluding faults (= on sky) | **6.8** | minus weather and the two fault/idle blocks (6.849 h); identical to the nightly time-loss plots' bridged on-sky hours |
| Exposing + readout | **4.5** | sum of the 528 visit intervals inside the night (4.538 h) |

Loss blocks: weather 1.0 h (0.982); fault + idle 2.8 h (2.769, camera recovery) + 0.3 h (0.274,
HV bias). Visits: 569 on sky, 559 survey (BLOCK-407; bands i 256, r 211, z 99, u 3), 10 focus,
0 engineering; 528 inside the −18° night, 41 survey visits after morning −18° drawn lighter and
outside every bracket. Median inter-visit gap 9 s; 21 gaps of 2–4 min left as white slivers.

Ratios for slide text (not on the figure): 4.5 h exposing + readout ÷ brackets 1/2/3 =
41 % / 45 % / 66 %; with the 6.8 h on-sky as numerator = 63 % / 69 % / 100 %.

## B10b — `engineering_time_budget/figures/engineering_hours_weekly_policy_20251026-20260714_white.png` (16:9)

Second output of the existing B10 script; B10 file byte-identical. Same bars, bins, totals
(Survey 822 h, Focus 107 h, Engineering 378 h). Annotations: 8 h line light-grey dashed before
2026-06-29, solid policy colour after, labelled "8 h/week pre-authorized (RSO)" with "16 h per
4 weeks" underneath; vertical dashed marker "LSST start / policy applies / 29 Jun 2026"; top-left
box "Envelope: 52 full-night equivalents in the first 6 months of LSST (simulations assumed 26)";
direct labels 0.8 / 1.6 / 2.2 h on the weeks of 29 Jun, 6 Jul, 13 Jul and "AOS stability tests,
44 h engineering" on the week of 9 Mar (43.9 h). Footer: pre-LSST dashed line is a reference, not
a rule; Confluence 1802141753 v6 (2026-07-28), "Proposed".

Still `[VERIFY]`: 8 / 16 / 52 / 26. README caveat kept: the policy counts dedicated engineering
between −12° twilights and excludes start-of-night focus and post-fault recovery; the figure counts
every non-survey, non-T539 on-sky visit, so it can over-count.

## Also

- Repo `README.md` index: `efficiency_waterfall/` marked superseded by
  `night_efficiency_brackets/` (folder kept, its README says so).
- No new queries; all inputs are copies of the B1/B3/B10 caches (ConsDB visit1 parquet,
  rubin_nights twilights, Scheduler observatoryStatus periods).
- Commits on the branch since your handoff: `1731890` (both figures), `2a7ad14` (bracket
  relabel), `8ccd3dd` (figure codes removed from the label).
