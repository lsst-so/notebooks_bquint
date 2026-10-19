# Simonyi weather-closure criteria with validity windows (for Q1b telemetry check)

Compiled 2026-10-18. Thresholds are the operating rules observers followed; they are the test for "should the dome have been closed", not a measurement of what happened. Sources: Confluence "Weather Constraints" (OOD 39696225, v29 2026-10-14, Draft, https://rubinobs.atlassian.net/wiki/spaces/OOD/pages/39696225/Weather+Constraints), "Temporary Guidelines – LSSTCam on-sky" (OOD 630095945, v198), Slack #obs-1479-tea-water-condensation, #summit-simonyi, #summit-control-room, #summit-announce. Slack items cite channel / author / date; permalinks `[check]`.

Night definition for the analysis: sun altitude −12° → −12°. Code source: `rubin_nights.dayobs_utils.estimated_baseline_visit_range` (commit 7ffa675, 2026-02-06; −12° twilights, 30 s visits, calibrated on baseline v5.1) and the ROSP open-shutter-fraction page (1907359761). No explicit written statement by Lynne found in Slack — `[check: confirm with Lynne]`. Note the operational dome-close time differs from the analysis night (see row 1).

## A. General constraints (steady-state rules)

| # | Quantity | Sensor / EFD source `[check exact topic]` | OK | Monitor / borderline | CLOSE (or do not open) | Valid from → to | Source |
|---|---|---|---|---|---|---|---|
| 1 | Dome close time (end of night) | sun altitude | — | — | close at −18° (astronomical twilight); last 3 h azimuth restricted so next day's sun stays > 45° from pointing; manual blocks 270 < az < 315 | 2025-10-27 → `[check: date changed to −12°]` | Bob Blum, #summit-announce 2025-10-27 19:30 |
| 1b | Dome close time | sun altitude | — | — | close at nautical twilight −12° (BLOCK-T196) | `[check]` → present | Temporary Guidelines v198 |
| 2 | Wind gusts | weather tower (ESS) | < 15 m/s open | 12–15 monitor; 15–20 borderline (check dust counters ESS:127/128/129) | 20 m/s average or 25 m/s sustained gusts; re-open after ≥ 15 min below 20 | whole range `[check: earlier values]` | Weather Constraints v29 |
| 3 | Ambient − dew point (outside) | ESS:301 outside dew point | > 5 °C | ~5 monitor; 2.5–3 borderline | 2 °C, or any sensor within 2 °C for ~20 min → close, telescope to horizon | whole range | Weather Constraints v29; Temp. Guidelines |
| 4 | Expected lowest temp − dew point (forecast) | forecast | > 5 °C | — | do not open if < 2 °C (opening-section text) | whole range | Weather Constraints v29 |
| 5 | Relative humidity | ESS | — | — | de-prioritized; dew-point difference is final (older opening text: don't open if RH > 70%) | RH rule superseded `[check: date]` | Weather Constraints v29 |
| 6 | Precipitation probability | forecast | < 5% | — | do not open if > 5% | whole range | Weather Constraints v29 |
| 7 | Cloud | visual / all-sky cam | not heavy/dark, east peak visible | — | re-open at night only if stable 30 min AND > 1 h before sunrise | whole range | Weather Constraints v29 |
| 8 | M1M3 mirror vs internal dew point | M1M3TS / ESS inside dew point | — | — | fans off and mirror within 2 °C of internal dew point → close | whole range | Weather Constraints v29 |
| 9 | Cryo hex return temp vs dome dew point | MTCamera | — | — | return temp < dome dew point for ≥ 10 min = frost risk (action per Temp. Guidelines) | whole range | Temporary Guidelines v198 |
| 10 | Generator power | — | — | observe south/west only | — | while on generator | Weather Constraints v29 |
| 11 | Downdraft fan | wind | — | — | downdraft fan only if wind < 10 m/s | whole range | Temporary Guidelines v198 |

Formula used on the summit: T_dew = T − (100 − RH)/5. Dashboards: Chronograf 707 (MTDome Weather Monitor), 327, 572 (cryo leading indicators); LOVE weather view id=123.

## B. Dynalene / condensation rule — time-dependent (the one that changed)

Quantity: Dynalene temperature at the camera minus dew point. Predicted Dynalene at TEA = `lsst.MTCamera.utiltrunk_ut.CoolPipeSplyTemp` − 1.5 °C (Temporary Guidelines); some messages use `dynaleneTemperaturePier0102` supply temp. Dew points: ESS:111 (TEA top-end, inside), ESS:112 (near camera), ESS:502 (inside TEA), ESS:301 (weather tower, outside). Ticket/channel: OBS-1479, #obs-1479-tea-water-condensation. FRACAS-330.

| Window | Rule in force | Evidence |
|---|---|---|
| before 2025-12-15 | no Dynalene-vs-dew-point rule (dew-point rules only on ambient, row 3) | first discussion at the 2025-12-15 tailgate (Danica Zilkova, #summit-control-room, values recorded 2025-12-15T20:36) |
| 2025-12-15 → ~2025-12-30 | **temporary close-dome condition: Dynalene − dew point ≤ +2 °C**; telescope to horizon, covers on when condensation seen | Bruno Quint, #summit-simonyi 2025-12-23; Kshitija Kelkar, #simonyi-discussion 2025-12-26 (heavy condensation, at horizon); Paulo Lago 2025-12-27 values |
| 2025-12-30 → 2026-01-19 | **before opening: outside (weather tower) dew point must be ≥ 2 °C below Dynalene, plus visual inspection of TEA before opening mirror covers**; if inside conditions are bad, go to horizon. Dynalene setpoint raised in steps to ≈5 °C by 2025-12-31 ("about as high as we can go") | Elana Urbach procedure summary, #obs-1479 2025-12-30; Kevin Fanning, #cam-summit-ops 2025-12-31; Anastasia Alexov 2026-01-07 ("2 or 3 setpoint updates during the break") |
| ~2026-01-19 | **wait to open until Dynalene supply − outside dew point > +1.0 °C for > 20 min** ("current guidelines") | Erik Dennihy, #obs-1479 2026-01-19 19:15 |
| 2026-01-20 → present | **on-sky allowed as long as Dynalene − dew point ≥ −2 °C**; close if < −2 °C for ~20 min; before opening, outside dew point 2 °C below Dynalene; −1 to −2 borderline, ~0 monitor | Kevin Reil, #summit-simonyi 2026-01-20 14:52; Erik Dennihy same day ("experiment with a limit of −2C"); Weather Constraints v29 |

Notes
- Closing the dome does not fix condensation (no dehumidifier, dome leaky) — Yousuke Utsumi, #obs-1479 2025-12-30. Condensation closures therefore show as telescope-at-horizon/covers-closed, not necessarily as dome-closed; check mirror-cover and elevation telemetry as well as the shutter.
- Insulation of Dynalene lines and setpoint raise were the fixes (FRACAS-330, Jan 2026 status meeting).
- Ready-made prior work: Karla Peña Ramírez, #obs-1479 2026-01-13 — dome events Nov 2025 → Jan 2026 colour-coded by shutter state and by Dynalene_mean − Dewpoint_outside_mean criterion `[check: get notebook]`.
- Anastasia Alexov 2026-01-14/15: condensation counts as FAULT in narrative-log time loss, not weather.

## C. How the USDF analysis should use this
1. For each night (−12° → −12°), compute per-minute flags for rows 2, 3, 8 and the Section B rule valid on that date.
2. Report the fraction of night minutes violating any CLOSE threshold, and the longest contiguous violation.
3. Compare with WEATHER-bit intervals (from ~2026-02-25) and with shutter/mirror-cover state; disagreements go in a list, not averaged.
4. Dec 2025–Jan 2026: label condensation-driven closures separately (they are "weather" physically, "fault" in the narrative log).

## D. Still to verify
- Date the dome-close time moved from −18° to −12°.
- Whether wind thresholds (row 2) were different before 2026 (page history of 39696225; v29 is the only version read).
- EFD topic/field names for every sensor above.
- Permalinks for the Slack items.
