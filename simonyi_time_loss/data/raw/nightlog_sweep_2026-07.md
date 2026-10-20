# Night-log sweep — Simonyi night status, 2026-07-01 → 2026-07-14 (Source 2: Rubin Observatory Night Reports)

Source: nightlog_simonyi_20251025_20260720.csv (export from the rubin-night-log reports via USDF, 2026-10-18). 14 nights; reports missing for 2026-07-01 and 2026-07-02 (database outage OBS-2000). Same columns as the tailgate files; "note (link)" is the Nightly Digest link for that day_obs. Times are UTC as written in the report (CLT = UTC−4 in July).

| Column | Meaning |
|---|---|
| day_obs | Chilean local date on which the night STARTS. |
| note (link) | Nightly Digest link for the night (the night report itself is on the rubin-night-log list). |
| status | Simonyi on-sky status judged from the report: OPEN / PARTIAL / CLOSED / UNKNOWN (report missing or silent). |
| P(weather) | Judged probability, 0–1, that lost time was weather. 0 when no loss. "?" when UNKNOWN. |
| P(fault) | Judged probability, 0–1, that lost time was fault/technical (incl. power glitches, flagged). "?" when UNKNOWN. |
| evidence | Verbatim or near-verbatim text from the report; clock times when given. |
| tickets | OBS keys listed in the report. |

Loss that is neither weather nor fault (staffing, planned work) has both P at 0 and the reason in the evidence.

| day_obs | note (link) | status | P(weather) | P(fault) | evidence | tickets |
|---|---|---|---|---|---|---|
| 2026-07-01 | [ND](https://usdf-rsp.slac.stanford.edu/nightlydigest/?startDayobs=20260701&endDayobs=20260701&telescope=Simonyi) | UNKNOWN | ? | ? | No night report found (database outage; tailgate: "Could not send the nightlog for the same reason", OBS-2000). | — |
| 2026-07-02 | [ND](https://usdf-rsp.slac.stanford.edu/nightlydigest/?startDayobs=20260702&endDayobs=20260702&telescope=Simonyi) | UNKNOWN | ? | ? | No night report found (same outage). | — |
| 2026-07-03 | [ND](https://usdf-rsp.slac.stanford.edu/nightlydigest/?startDayobs=20260703&endDayobs=20260703&telescope=Simonyi) | CLOSED | 0.7 | 0.9 | "Calibration night due to high wind." Nighttime "wind 15-20 m/s". Also "Main Cabinet special fault occurred four times at 21:02 UTC … attempts to power on OSS were unsuccessful"; PXI–Bosch PLC problem 23:43 UTC; "TMA is recovered at 02:15 UTC"; earthquake 03:10 UTC, recovered 04:45 UTC. Calibration blocks rest of night. Weather and faults overlap; wind was at the CLOSE threshold. | — |
| 2026-07-04 | [ND](https://usdf-rsp.slac.stanford.edu/nightlydigest/?startDayobs=20260704&endDayobs=20260704&telescope=Simonyi) | CLOSED | 0.2 | 1.0 | "Since it was not possible to recover the TMA, there were no night operations for Simonyi today. The main cabinet continued to fault" ("Cabinet Temperature decreased below critical limit", from 23:49 UTC). Weather: "gusts reaching 20 m/s … no Auxtel operations" (AuxTel statement). | OBS-1217 |
| 2026-07-05 | [ND](https://usdf-rsp.slac.stanford.edu/nightlydigest/?startDayobs=20260705&endDayobs=20260705&telescope=Simonyi) | OPEN | 0 | 0.05 | "Flawless FBS night for Simonyi, only one MTAOS timeout that was quickly recovered." FBS from 00:27 UTC to 10:40 UTC. Seeing 2″ early ("summit heat bubble"). | OBS-2003, OBS-1848 |
| 2026-07-06 | [ND](https://usdf-rsp.slac.stanford.edu/nightlydigest/?startDayobs=20260706&endDayobs=20260706&telescope=Simonyi) | OPEN | 0 | 0.1 | "On sky all night, some good seeing." TARTS test abandoned (RA config), FBS whole night. "Slight delay to get on sky as the camera got stuck integrating (guider error) … began alignment around -13". | OBS-2004, OBS-1286 |
| 2026-07-07 | [ND](https://usdf-rsp.slac.stanford.edu/nightlydigest/?startDayobs=20260707&endDayobs=20260707&telescope=Simonyi) | CLOSED | 0 | 1.0 | "Observations with Simonyi were suspended to give time to thoroughly investigate the camera fault that occurred during the day" — "all but 4 of the 71 REBs of the camera powered off spontaneously" at 09:56 local. OSS faulted the mount at the cal screen (OBS-2006). Weather good (cirrus, 0.7″). | OBS-2005, OBS-2006, OBS-2007 |
| 2026-07-08 | [ND](https://usdf-rsp.slac.stanford.edu/nightlydigest/?startDayobs=20260708&endDayobs=20260708&telescope=Simonyi) | PARTIAL | 0.3 | 0.9 | "Camera was recovered and ready to go on sky at 02:20 UTC"; "FBS started at 03:15 UTC"; HV bias tripped 03:30–03:50 UTC (OBS-2010); two MTAOS timeouts; done 10:40 UTC. Weather: "Mostly cloudy … became worse by 23UTC when we decided to close AuxTel and Simonyi … Around 23UTC, clouds cleared". ≈4 h lost at start, camera recovery dominant, clouds coincident. | OBS-2009, OBS-2010, OBS-2011 |
| 2026-07-09 | [ND](https://usdf-rsp.slac.stanford.edu/nightlydigest/?startDayobs=20260709&endDayobs=20260709&telescope=Simonyi) | PARTIAL | 1.0 | 0 | "Delayed start on-sky due to cloud coverage. No faults from Simonyi the entire night!" Alignment waited until 23:00 UTC; survey 01:30–10:44 UTC; "Cloudy sky overall, but we were able to observe through them". | OBS-2012, OBS-1654 |
| 2026-07-10 | [ND](https://usdf-rsp.slac.stanford.edu/nightlydigest/?startDayobs=20260710&endDayobs=20260710&telescope=Simonyi) | PARTIAL | 0.9 | 0.2 | "Weather was very cloudy for most of the night"; alignment stopped 23:33 UTC "due to clouds faulting MTAOS"; in-dome CBP from 03:00 UTC; "Clouds cleared up around 5:20 UTC"; survey 06:10–10:45 UTC. ≈6 h lost to clouds; dome az drives errored on unpark (OBS-646), MTAOS fault from RA errors (OBS-1532). | OBS-2014, OBS-1823, OBS-646, OBS-1532, OBS-1216, OBS-2013, OBS-2009, OBS-2015 |
| 2026-07-11 | [ND](https://usdf-rsp.slac.stanford.edu/nightlydigest/?startDayobs=20260711&endDayobs=20260711&telescope=Simonyi) | OPEN | 0 | 0.05 | "Nearly flawless night … We shutdown 1hr early due to one of the observers not feeling well." Survey 00:10–09:45 UTC; MTRotator fault 08:30 UTC (OBS-1481). 1 h lost to staffing, not weather/fault. | OBS-1481, OBS-1949, OBS-2016 |
| 2026-07-12 | [ND](https://usdf-rsp.slac.stanford.edu/nightlydigest/?startDayobs=20260712&endDayobs=20260712&telescope=Simonyi) | PARTIAL | 0 | 0.1 | "Relatively smooth except for a glycol chiller 2 failure after power glitch" ("power glitch at 06:30 UTC, and glycol chiller 2 stopped (OBS-1214). Oscar remotely started it" — no observing loss stated). "Closed early at 4am due to backup shift drove to reach the summit" (≈3 h lost, staffing). FBS from 23:06 UTC. Power glitch flagged. | OBS-1214, OBS-2017, OBS-2018, OBS-1858, OBS-1654 |
| 2026-07-13 | [ND](https://usdf-rsp.slac.stanford.edu/nightlydigest/?startDayobs=20260713&endDayobs=20260713&telescope=Simonyi) | OPEN | 0 | 0 | "Both Simonyi and Auxtel observed throughout the night without any issue. End of the night around 11:00 UTC." Seeing ~0.6″ at start. | OBS-2019 |
| 2026-07-14 | [ND](https://usdf-rsp.slac.stanford.edu/nightlydigest/?startDayobs=20260714&endDayobs=20260714&telescope=Simonyi) | CLOSED | 1.0 | 0.1 | "Calibration night with many tunable laser faults." "We attempted to run the initial alignment (thin clouds passing), but after one attempt … decided to proceed with the in-dome calibrations as the weather conditions deteriorated." "Cloudy whole night", wind ~12 m/s. (Report's "11:35 UTC" for the suspension is likely a typo for 23:35 UTC `[check]`.) Last night before the storm evacuation. | OBS-2022, OBS-1654 |

## Summary for this window
- Weather closures/losses: Jul 3 (wind, overlapped with TMA faults), Jul 9 (~1 h delay), Jul 10 (~6 h, clouds), Jul 14 (whole night, clouds) — plus clouds coincident with the camera recovery on Jul 8.
- Fault closures: Jul 4 (TMA main cabinet, OBS-1217), Jul 7 (camera REB power-off), Jul 8 start (~4 h camera recovery); Jul 3 TMA unrecoverable until 02:15 UTC.
- Neither: Jul 11 (1 h, observer unwell), Jul 12 (~3 h, backup shift travel).
- Power glitch: Jul 12 06:30 UTC (chiller 2 stopped, OBS-1214).
- UNKNOWN: Jul 1, Jul 2 (no report).

## Differences vs the tailgate file (Source 1)
- Jul 3: tailgate CLOSED fault only; night log adds high wind (15–20 m/s) — mixed.
- Jul 5: tailgate UNKNOWN → night log OPEN (flawless).
- Jul 8: tailgate PARTIAL fault; night log adds coincident clouds and the 02:20/03:15 UTC times.
- Jul 10: tailgate OPEN (inferred from "full weekend of observations"); night log PARTIAL, ~6 h lost to clouds. Tailgate inference was wrong.
- Jul 12: tailgate OPEN; night log PARTIAL (early close for staffing).
- Jul 14: tailgate "closed early due to clouds" (PARTIAL); night log says essentially no on-sky data (CLOSED).
