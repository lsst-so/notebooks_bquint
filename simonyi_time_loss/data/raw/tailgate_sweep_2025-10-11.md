# Tailgate sweep — Simonyi night status, 2025-10-24 → 2025-11-27 (Source 1: Morning Tailgate notes)

Compiled 2026-10-17 from the "Summit Morning Tailgate Meeting Notes" threads in #summit-announce (C07QCJ7F962).
Each note describes the previous night (Monday notes describe Fri/Sat/Sun). This is Source 1 of 2; Source 2 (night logs) is a separate, independent table with the same columns.

## Column definitions (same for every tailgate and night-log file)

| Column | Meaning |
|---|---|
| day_obs | Chilean local date on which the night STARTS (YYYY-MM-DD). The tailgate note posted on date D describes night day_obs = D−1 (or Fri/Sat/Sun for a Monday note). |
| note (link) | Date of the tailgate note and the Slack thread it came from. |
| status | Simonyi on-sky status that night as judged from the note text: OPEN (observed, at most minor loss), PARTIAL (observed but a stated or clearly implied block of time lost), CLOSED (no Simonyi on-sky observing), UNKNOWN (note missing or silent on Simonyi). |
| P(weather) | Judged probability, 0–1, that the lost time (if any) was caused by weather. 0 when no loss or no weather mentioned. "?" when status is UNKNOWN. |
| P(fault) | Judged probability, 0–1, that the lost time (if any) was caused by faults/technical issues (includes power glitches — see note below). "?" when UNKNOWN. |
| evidence | Verbatim or near-verbatim text from the note that supports the judgement. |
| tickets | OBS/FRACAS/SUMMIT keys mentioned for that night. |

P(weather) and P(fault) are judgements by Claude from the note text only; they are NOT measurements. They need not sum to 1 (a night can have both, or neither when nothing was lost). A night with status OPEN and both at 0 means "nothing significant reported lost".
Power glitches / generator transitions are counted under P(fault), not weather, because the notes never attribute them to weather; flag them in the evidence so the USDF analysis can split them out if wanted.

## Table

| day_obs | note (link) | status | P(weather) | P(fault) | evidence | tickets |
|---|---|---|---|---|---|---|
| 2025-10-24 (Fri) | Oct 27 [thread](https://rubin-obs.slack.com/archives/C07QCJ7F962/p1761569152123739?thread_ts=1761569152.123739&cid=C07QCJ7F962) | OPEN | 0 | 0.2 | "Friday night – We had a few unexpected behaviors of scripts and software control. The only news that caught my attention was OBS-1294 Azimuth max tachometer difference exceeded." | OBS-1294 |
| 2025-10-25 (Sat) | Oct 27 (same) | CLOSED | ? | ? | "Saturday night - no observations" — no reason given. (Construction→Operations handover day.) | — |
| 2025-10-26 (Sun) | Oct 27 (same) | PARTIAL | 0 | 0.9 | "Issue with OSS that required reset Chiller 1 at level 1"; "issue with the dome that prevented rotation. ExitFault and Home solved the issue"; "Mirror cover failed to close twice (OBS-1154)"; AuxTel "Lots of faults – closed early". Simonyi duration of loss not stated. | OBS-1154, OBS-1287 |
| 2025-10-27 (Mon) | Oct 28 [thread](https://rubin-obs.slack.com/archives/C07QCJ7F962/p1761655808343679?thread_ts=1761655808.343679&cid=C07QCJ7F962) | OPEN | 0 | 0.2 | "Completed all the AOS tests. During FBS, AOS faulted because the Rotator was not reporting angle telemetry (OBS-1304)". "Louver E1 opened as planned". | OBS-1304 |
| 2025-10-28 (Tue) | Oct 29 [thread](https://rubin-obs.slack.com/archives/C07QCJ7F962/p1761743526168039?thread_ts=1761743526.168039&cid=C07QCJ7F962) | PARTIAL (≈ closed) | 0 | 1.0 | "We lost almost the entire night due to a series of major faults that reduced total on-sky time to about 30 - 45 minutes." Dome shutter e-stop/GIS issue "a couple of hours" (OBS-1309); "Major Dynalene failure on Chiller 1 … We lost ~ 3 hours. OBS-1310"; network crash OBS-1312. Daytime note: "38 km/h – we cannot perform work with opening the dome shutter" (daytime EIE work, not an observing closure). | OBS-1309, OBS-1310, OBS-1312 |
| 2025-10-29 (Wed) | Oct 30 [thread](https://rubin-obs.slack.com/archives/C07QCJ7F962/p1761829719331699?thread_ts=1761829719.331699&cid=C07QCJ7F962) | PARTIAL | 0 | 1.0 | "Another Dynalene meltdown … cRIO lost the connection … David J created FRACAS-312"; "Tried TMA Balance Check, but M1M3 went to fault". Amount of on-sky time not stated. | FRACAS-312, OBS-1316, SUMMIT-11490 |
| 2025-10-30 (Thu) | — (no note Oct 31, holiday) | UNKNOWN | ? | ? | No tailgate note on Fri Oct 31; the Mon Nov 3 note only covers Fri/Sat/Sun. | — |
| 2025-10-31 (Fri) | Nov 3 [thread](https://rubin-obs.slack.com/archives/C07QCJ7F962/p1762175235431449?thread_ts=1762175235.431449&cid=C07QCJ7F962) | OPEN | 0.2 | 0.1 | Simonyi "Friday: Minor issues; the tunable laser did not power off correctly (OBS-1230) … There was also a random rotator fault." AuxTel "Friday … little observation time due to high humidity". Humidity closure stated for AuxTel only; Simonyi impact not stated — check night log. | OBS-1230 |
| 2025-11-01 (Sat) | Nov 3 (same) | OPEN | 0.2 | 0.1 | Simonyi "Saturday: Some software issues but no major disruptions." AuxTel "Saturday … little observation time due to … strong winds". Wind closure stated for AuxTel only — check night log. | — |
| 2025-11-02 (Sun) | Nov 3 (same) | OPEN | 0 | 0 | "Sunday: Quiet night with no issues." | — |
| 2025-11-03 (Mon) | Nov 4 [thread](https://rubin-obs.slack.com/archives/C07QCJ7F962/p1762261434796759?thread_ts=1762261434.796759&cid=C07QCJ7F962) | PARTIAL | 0 | 0.9 | "MTCamera went into fault due to a jgroups meltdown (OBS-1336)"; "Dome motion state error (OBS-646) … quickly recovered"; calibration script failed (OBS-1337). Duration not stated. Daytime Nov 4: "Strong wind; outdoor activities paused, shutter closed." | OBS-1336, OBS-646, OBS-1337, OBS-1316 |
| 2025-11-04 (Tue) | Nov 5 [thread](https://rubin-obs.slack.com/archives/C07QCJ7F962/p1762346865780479?thread_ts=1762346865.780479&cid=C07QCJ7F962) | OPEN | 0 | 0.1 | "Overall, a smooth night. There were a few issues with the Rotator and with the Scheduler." Daytime Nov 5 09:15: UPS zero-power event, Dynalene recovered (daytime, FRACAS to be created). | — |
| 2025-11-05 (Wed) | Nov 6 [thread](https://rubin-obs.slack.com/archives/C07QCJ7F962/p1762433934036609?thread_ts=1762433934.036609&cid=C07QCJ7F962) | PARTIAL | 0 | 1.0 | "Night start: GIS interlock on OSS. Delayed going on-sky by 3 hours." "End of night – another GIS interlock while parking … parked very late, around 8:30am." "M1M3 thermal system problems". GIS problems "possibly related to power issues yesterday". | — |
| 2025-11-06 (Thu) | Nov 7 [thread](https://rubin-obs.slack.com/archives/C07QCJ7F962/p1762523489290759?thread_ts=1762523489.290759&cid=C07QCJ7F962) | CLOSED | 1.0 | 0.1 | "High humidity above 80%. Only in dome observation. Calibration all night long. no major issue to report." Also "Multiple incidences of M1M3TS faulting … OBS-1344" and "Louver H1 was expected to be operated during the night, but this is not possible due to last weather conditions." No AuxTel observation. | OBS-1344 |
| 2025-11-07 (Fri) | Nov 10 [thread](https://rubin-obs.slack.com/archives/C07QCJ7F962/p1762781474421789?thread_ts=1762781474.421789&cid=C07QCJ7F962) | UNKNOWN | ? | ? | Monday note gives no Simonyi night summary for the weekend (only "Telescope was request at Calibration position"; AuxTel no observation, ATMCS faults OBS-568/1294). | OBS-1359 (TMA fluid leak), OBS-992 |
| 2025-11-08 (Sat) | Nov 10 (same) | UNKNOWN | ? | ? | as above | — |
| 2025-11-09 (Sun) | Nov 10 (same) | UNKNOWN | ? | ? | as above | — |
| 2025-11-10 (Mon) | Nov 11 [thread](https://rubin-obs.slack.com/archives/C07QCJ7F962/p1762865752842729?thread_ts=1762865752.842729&cid=C07QCJ7F962) | PARTIAL | 0 | 1.0 | "OSS fault required 2.5 hours and electronics support to recover (OBS-1364)"; "M1M3 went to fault after parking". AuxTel did not go on sky (OBS-1294). | OBS-1364, OBS-1294 |
| 2025-11-11 (Tue) | Nov 12 [thread](https://rubin-obs.slack.com/archives/C07QCJ7F962/p1762953299846989?thread_ts=1762953299.846989&cid=C07QCJ7F962) | PARTIAL | 0 | 0.9 | "Multiple faults in M1M3TS and M1M3 … thermal equipment interlock"; "Rapid Analysis data were not being received, preventing AOS corrections" (OBS-1366 nan seeing header, OBS-1367 quota). On sky but degraded; duration not stated. AuxTel closed 04:38 UTC (OBS-1371). | OBS-1366, OBS-1367, OBS-1371 |
| 2025-11-12 (Wed) | Nov 13 [thread](https://rubin-obs.slack.com/archives/C07QCJ7F962/p1763039499777699?thread_ts=1763039499.777699&cid=C07QCJ7F962) | OPEN | 0 | 0.1 | "Calm night. M1M3 faulted in the morning, no calibrations taken." "last night we used 3 louvers". | — |
| 2025-11-13 (Thu) | Nov 14 [thread](https://rubin-obs.slack.com/archives/C07QCJ7F962/p1763125397865199?thread_ts=1763125397.865199&cid=C07QCJ7F962) | OPEN | 0 | 0 | "Calm night"; "The camera worked fine during the night". | — |
| 2025-11-14 (Fri) | Nov 17 [thread](https://rubin-obs.slack.com/archives/C07QCJ7F962/p1763383538184049?thread_ts=1763383538.184049&cid=C07QCJ7F962) | UNKNOWN | ? | ? | "No meeting notes today". AI notes link posted (Slack canvas F08U92XHEKA, not read). | — |
| 2025-11-15 (Sat) | Nov 17 (same) | UNKNOWN | ? | ? | as above | — |
| 2025-11-16 (Sun) | Nov 17 (same) | UNKNOWN | ? | ? | as above | — |
| 2025-11-17 (Mon) | Nov 18 [thread](https://rubin-obs.slack.com/archives/C07QCJ7F962/p1763471158355779?thread_ts=1763471158.355779&cid=C07QCJ7F962) | OPEN | 0 | 0.1 | "No big issues to report, except for an encoder fault OBS-965". | OBS-965 |
| 2025-11-18 (Tue) | Nov 19 [thread](https://rubin-obs.slack.com/archives/C07QCJ7F962/p1763557457780999?thread_ts=1763557457.780999&cid=C07QCJ7F962) | PARTIAL | 0 | 1.0 | "OBS-1396 – Cryo 6 failed due to EAS auto-adjusted setpoint … near 21:30 CLT. It cost two hours in the sky." Also M1M3 faults during bump tests (OBS-1392/1393), unreliable in-dome temps ESS:112/113 (OBS-1394) "probably impacted image quality". AuxTel closed (OBS-568). | OBS-1392…1396, OBS-568 |
| 2025-11-19 (Wed) | Nov 20 [thread](https://rubin-obs.slack.com/archives/C07QCJ7F962/p1763643237112499?thread_ts=1763643237.112499&cid=C07QCJ7F962) | OPEN | 0 | 0.3 | "OBS-1400 M2Hex went to fault while slewing … It happened twice"; "OBS-1398 DIMM.2 suddenly on FAULT". AuxTel could not observe (az drive). Context: "very warm temperatures and needed to turn on the AHU and open the louvers". | OBS-1400, OBS-1398 |
| 2025-11-20 (Thu) | Nov 21 [thread](https://rubin-obs.slack.com/archives/C07QCJ7F962/p1763730321629859?thread_ts=1763730321.629859&cid=C07QCJ7F962) | PARTIAL (≈ closed) | 0 | 1.0 | "Major issue with Dynalene – FRACAS-321 … near 15h CLT"; "Major telescope faults – … Pxi? No obs ticket. 4.5 hours" (EtherCAT/drive faults, PXI reset, EUI restart); "Camera focal plane stuck in ACTIVE state". Discussion links it to a generator/commercial power transition ("70 seconds of no power"). | FRACAS-321, OBS-1109 |
| 2025-11-21 (Fri) | Nov 24 [thread](https://rubin-obs.slack.com/archives/C07QCJ7F962/p1763989469818259?thread_ts=1763989469.818259&cid=C07QCJ7F962) | PARTIAL | 0 | 1.0 | "Issues with TMA Drives (OBS-1401), OSS (OBS-1267), and MTCamera focal plane issues (LSSTCAM-148). Could collect ~ 3 hours of data from our target-of-opportunity. Total time loss ~ 45 min." | OBS-1401, OBS-1267, LSSTCAM-148 |
| 2025-11-22 (Sat) | Nov 24 (same) | PARTIAL | 0 | 1.0 | "same LSSTCAM-148 issue … Recovered in ~ 5 min"; "OBS-1336 jgroups meltdown (took ~1h to recover)". | LSSTCAM-148, OBS-1336 |
| 2025-11-23 (Sun) | Nov 24 (same) | PARTIAL (≈ closed) | 0 | 1.0 (power glitch) | "Power glitch caused major issues at the summit. Almost every system went to fault and it took ~ 6.5 hours to recover everything." Glitch at 21:34 CLT; eight tickets under OBS-1412. "There were two power cuts in two minutes." | OBS-1412 (OBS-1406…1411), SUMMIT-11629, OBS-1413 |
| 2025-11-24 (Mon) | Nov 25 [thread](https://rubin-obs.slack.com/archives/C07QCJ7F962/p1764077159866439?thread_ts=1764077159.866439&cid=C07QCJ7F962) | OPEN | 0 | 0.3 | "Less problematic night. Fault: Camera MCM … recovered; EIB and OSS fault while homing the axes". Workstation login issue IHS-9524. | IHS-9524 |
| 2025-11-25 (Tue) | Nov 26 [thread](https://rubin-obs.slack.com/archives/C07QCJ7F962/p1764164515162889?thread_ts=1764164515.162889&cid=C07QCJ7F962) | OPEN | 0 | 0.3 | "Productive night time, completing all planned tests, despite of faults." "Dynalene flow rate dropped to zero (OBS-1416). David J remotely reset"; camera: "I think we lost like 15 min." Workstations OBS-1421. | OBS-1416, OBS-1421 |
| 2025-11-26 (Wed) | Nov 27 [thread](https://rubin-obs.slack.com/archives/C07QCJ7F962/p1764247241972239?thread_ts=1764247241.972239&cid=C07QCJ7F962) | PARTIAL | 0 | 1.0 | "OBS-1427 – GIS Communication Loss – 45 minutes to recover. Did not take calibrations." | OBS-1427 |
| 2025-11-27 (Thu) | Nov 28 [thread](https://rubin-obs.slack.com/archives/C07QCJ7F962/p1764333658555719?thread_ts=1764333658.555719&cid=C07QCJ7F962) | PARTIAL | 0 | 1.0 (power glitch + faults) | "Power glitch – we were 10 min on generator. Subsequent faults took 1.5 hours to recover" (OBS-1401 TMA EtherCAT, OBS-1402 MTRotator); "Cascade of MTDome faults – OBS-1428 … and OBS-1427 – ended early – 1h loss"; "M1M3 with high thermal gradient in Z". Daytime Nov 28: "Wind speed: 45 Km/h", "too windy today. Cannot open the dome shutter" (daytime work). | OBS-1401, OBS-1402, OBS-1427, OBS-1428, OBS-572 |

Nights 2025-11-28 → 11-30 are covered by the Dec 1 note (next file).

## Summary for this window (Simonyi, tailgate source only)
- Weather closure stated explicitly: **1 night** — 2025-11-06 (humidity > 80%, calibrations only).
- Possible weather impact, not confirmed for Simonyi: 2025-10-31 (humidity) and 2025-11-01 (wind) — stated for AuxTel only.
- Nights mostly lost to faults: 2025-10-28, 2025-11-20, 2025-11-23 (power glitch); large partial losses 2025-11-05 (3 h), 2025-11-10 (2.5 h), 2025-11-18 (2 h), 2025-11-27 (1.5 h + 1 h).
- Dynalene/cooling events in the window: Oct 28, Oct 29, Nov 20, Nov 23 (degraded), Nov 25.
- No information (UNKNOWN): Oct 25 (reason), Oct 30, Nov 7–9, Nov 14–16 — 8 nights. Night logs must fill these.
- Daytime wind repeatedly stopped crane/shutter work (Oct 29, Nov 4, Nov 5, Nov 20, Nov 28) — not observing losses, but worth cross-checking against EFD wind for those evenings.

## Caveats
- "No mention" of weather ≠ no weather; several early notes contain no Simonyi weather field at all.
- Monday notes compress three nights and sometimes omit Simonyi entirely (Nov 10, Nov 17).
- The notes rarely give hours lost; where they do, it is quoted. Treat P values as a reading aid, not data.
