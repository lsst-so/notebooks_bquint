# Handoff — Dynalene condensation weather criteria, Dec 2025 → Jan 2026
**For the USDF Claude session (EFD/ConsDB access). Compiled 2026-10-18 from `weather_criteria_table.md`, `handoff_usdf_time_loss_analysis.md` §5, `tailgate_sweep_2025-12.md` and `nightlog_sweep_2025-10_to_2026-07.md`. Open items marked `[check: ...]`.**

This supplements Section 5 of `handoff_usdf_time_loss_analysis.md`. It covers the one weather criterion that changed over the Oct 2025 → Jul 2026 range: the Dynalene-vs-dew-point rule introduced after water condensed on the uninsulated TEA Dynalene lines. Use the rule that was valid on each `day_obs` when flagging nights in Dec 2025 – Jan 2026; do not apply the current (v29) rule backwards.

---

## 1. What happened

- The Dynalene chiller was running at a −1 °C setpoint; the lines on the TMA/TEA were uninsulated. On humid nights water condensed on the lines, on M1M3 (splatter pattern reported Dec 21) and on refrigeration lines around the TMA.
- First discussed at the 2025-12-15 tailgate (Danica Zilkova, #summit-control-room, values recorded 2025-12-15T20:36 UTC). First night governed by the rule: 2025-12-21.
- Dec 25: Simonyi shut down over liquid in several areas in and around the TMA; a separate Dynalene failure the same night (FRACAS-823, ~1.57 h to recover).
- Fixes: Dynalene setpoint raised in steps (−1 → +1 → +2 °C over Dec 27–30; ≈5 °C by Dec 31, "about as high as we can go"; "2 or 3 setpoint updates during the break" per Anastasia Alexov 2026-01-07) and insulation of the Dynalene lines (FRACAS-330, Jan 2026 status meeting).
- Tickets / channels: OBS-1479 (main), OBS-1490 (setpoint raise attempt failed on Dec 22), OBS-1501 (M1M3TS/EGW pump fault, Dec 30), FRACAS-330, FRACAS-823; Slack #obs-1479-tea-water-condensation, #summit-simonyi, #cam-summit-ops, #simonyi-discussion.

---

## 2. The quantity

**Dynalene temperature at the camera minus dew point.**

- Predicted Dynalene at TEA = `lsst.MTCamera.utiltrunk_ut.CoolPipeSplyTemp` − 1.5 °C (Temporary Guidelines – LSSTCam on-sky, OOD page 630095945, v198). Some Slack messages use `dynaleneTemperaturePier0102` supply temp instead; night reports refer to a "Dynalene_at_Az" sensor `[check: EFD topic/field for each]`.
- Dew-point sensors: ESS:111 (TEA top-end, inside), ESS:112 (near camera), ESS:502 (inside TEA), ESS:301 (weather tower, outside) `[check: exact topics]`.
- Summit formula when only T and RH are at hand: T_dew = T − (100 − RH)/5.
- Dashboards: Chronograf 707 (MTDome Weather Monitor), 327, 572 (cryo leading indicators); LOVE weather view id=123.

---

## 3. Rule by validity window

| Window | Rule in force | Evidence |
|---|---|---|
| before 2025-12-15 | No Dynalene-vs-dew-point rule. Dew-point rules applied only to ambient air (ambient − outside dew point: open > 5 °C, close at 2 °C). | Weather Constraints page history `[check: earlier versions]` |
| 2025-12-15 → ~2025-12-30 | **Temporary close-dome condition: Dynalene − dew point ≤ +2 °C.** Telescope to horizon, mirror covers on when condensation seen. A 20-min persistence was adopted around Dec 22. | Bruno Quint, #summit-simonyi 2025-12-23; Kshitija Kelkar, #simonyi-discussion 2025-12-26; Paulo Lago 2025-12-27 values; Dec 23 tailgate: "Close the dome if the dewpoint is less than 2 deg below the Dynalene" |
| 2025-12-30 → 2026-01-19 | **Before opening: outside (weather tower) dew point must be ≥ 2 °C below Dynalene**, plus visual inspection of the TEA before opening mirror covers; if inside conditions are bad, go to horizon. Setpoint raised to ≈5 °C by Dec 31. | Elana Urbach procedure summary, #obs-1479 2025-12-30; Kevin Fanning, #cam-summit-ops 2025-12-31; Anastasia Alexov 2026-01-07 |
| ~2026-01-19 | Wait to open until Dynalene supply − outside dew point > +1.0 °C for > 20 min ("current guidelines"). | Erik Dennihy, #obs-1479 2026-01-19 19:15 |
| 2026-01-20 → present | **On-sky allowed while Dynalene − dew point ≥ −2 °C**; close if < −2 °C for ~20 min; before opening, outside dew point must be ≥ 2 °C below Dynalene; −1 to −2 borderline, ~0 monitor, > 0 open. | Kevin Reil, #summit-simonyi 2026-01-20 14:52; Erik Dennihy same day ("experiment with a limit of −2C"); Weather Constraints, OOD page 39696225, v29 (2026-10-14, Draft) |

Side rules seen in the same period:
- Roberto (Dec 22 tailgate): dome stays closed when humidity > 40 % and when Dynalene and outside dew points converge. Treat as an operator's rule of thumb, not a written threshold.
- The older "don't open if RH > 70 %" text was de-prioritized; the dew-point difference is final `[check: date superseded]`.
- Related rows unchanged across the range: M1M3 fans off and mirror within 2 °C of internal dew point → close; cryo hex return temp < dome dew point for ≥ 10 min = frost risk.

`[check: Slack permalinks for every evidence item]`

---

## 4. Nights affected (for cross-checking the flags)

From the tailgate (Source 1) and night-report (Source 2) sweeps. P(weather)/P(fault) as judged there.

| day_obs | Status | Tailgate P(w)/P(f) | Night report P(w)/P(f) | Notes |
|---|---|---|---|---|
| 2025-12-20 | OPEN? | — | — | "humidity was high", no stated loss |
| 2025-12-21 | CLOSED | 0.6 / 0.5 | 0.8 / 0.2 | First night under the rule. Louvers opened 00:16 UTC, closed 30 min later (refrigerant line < 2 °C from dew point). 03:01 UTC outside dew point (−0.7 °C) met Dynalene at Az (−0.6 °C). Thick clouds too. OBS-1479 |
| 2025-12-22 | PARTIAL | ? (note silent) | 0.8 / 0.2 | Dome closed until difference > 2 °C; opened 03:50 UTC, closed 08:39 UTC. Daytime attempt to raise setpoint to 2 °C failed (OBS-1490). |
| 2025-12-23 | OPEN | ? (no tailgate note) | 0 / 0.6 | "no weather-related delays". Rotator CCW telemetry issue (OBS-922). |
| 2025-12-24 | PARTIAL | ? | 0.8 / 0.2 | Late opening at 01:43 UTC after dew-point discussion and visual inspection. |
| 2025-12-25 | CLOSED | ? ("Dynalene faulted on Thursday") | 0.8 / 0.2 | Shutdown for liquid around TMA; 8 h lost; Dynalene failure FRACAS-823 (1.57 h). Clear sky, RH 55–65 %. |
| 2025-12-26 | CLOSED | 0.6 / 0.6 | `[check: Source 2 row]` | "closed all weekend" for condensation; camera back Saturday. |
| 2025-12-27 | CLOSED | 0.6 / 0.5 | `[check]` | Same; glycol setpoint raised, camera delivered 4.5 °C. |
| 2025-12-28 | CLOSED | 0.6 / 0.5 | `[check]` | Same; mirror cover X+ issue. |
| 2025-12-29 | OPEN | 0 / 0.2 | `[check]` | Mostly smooth. |
| 2025-12-30 | OPEN | 0 / 0.2 | `[check]` | No condensation risk given dew point and Dynalene temps; setpoint +2 °C from Dec 29; M1M3TS/EGW fault OBS-1501. |
| 2025-12-31 / 2026-01-01 | UNKNOWN | ? | `[check: Jan file]` | Jan 2 note: "remained at horizon until temperature conditions were safe to avoid condensation" — ambiguous which night. |

Jan 2026: late openings while waiting for the outside dew point to drop ≥ 2 °C below Dynalene `[check: pull from nightlog_sweep_2025-10_to_2026-07.md January section]`.

---

## 5. Attribution — how to label these

- Physically these are weather-triggered (humid air) on an engineering weakness (cold, uninsulated lines). The tailgate sweep scores both P near 0.5–0.6 so they can be re-split against telemetry; the night-report sweep scores them mostly weather with P(fault) 0.2–0.4.
- **Narrative log convention (Anastasia Alexov, 2026-01-14/15): condensation counts as FAULT, not weather.** Expect disagreement with any weather-telemetry flag for these nights.
- Closing the dome does not stop condensation (no dehumidifier, leaky dome — Yousuke Utsumi, #obs-1479 2025-12-30). Condensation holds show as telescope-at-horizon / mirror covers closed, not necessarily as shutter closed. Check mirror-cover state and elevation telemetry as well as the dome shutter.
- Report Dec 2025 – Jan 2026 condensation closures as their own category in the Q1 comparison, not merged into weather or fault.

---

## 6. What to compute at USDF

1. For each night (−12° → −12°, bucket by `day_obs`), compute per-minute Dynalene − dew point using the predicted-TEA definition (§2), plus the ambient − outside dew point row.
2. Apply the rule valid on that date (§3 table). Flag minutes violating the CLOSE condition; report the fraction of night minutes and the longest contiguous violation per night.
3. Compare against: shutter state, mirror-cover state, elevation (horizon holds), the narrative-log time-loss entries, and the two human-judged tables (§4).
4. Prior work to reuse rather than redo: Karla Peña Ramírez, #obs-1479 2026-01-13 — dome events Nov 2025 → Jan 2026 colour-coded by shutter state and by Dynalene_mean − Dewpoint_outside_mean `[check: get the notebook]`.
5. Ask me before choosing which Dynalene sensor to use if `CoolPipeSplyTemp` and `dynaleneTemperaturePier0102` disagree by more than ~1 °C.

---

## 7. Still to verify

- EFD topic/field names for every sensor in §2.
- Slack permalinks for the evidence column in §3.
- Date the RH > 70 % rule was formally superseded.
- Whether any Weather Constraints page version between v1 and v29 recorded the temporary +2 °C rule in writing.
- Source 2 scores for Dec 26–31 and the January late openings (fill §4).
