# Night-log sweep — Simonyi night status, 2025-10-25 → 2026-07-14 (Source 2: Rubin Observatory Night Reports) — all months concatenated

Compiled 2026-10-18 from the monthly files nightlog_sweep_<YYYY-MM>.md, in date order. Each month keeps its own header, table, summary, differences and caveats.

---

# Night-log sweep — Simonyi night status, 2025-10-25 → 2025-10-31 (Source 2: Rubin Observatory Night Reports)

Source: nightlog_simonyi_20251025_20260720.csv (export from the rubin-night-log reports via USDF, 2026-10-18). 7 nights (the export starts on 2025-10-25, the first day_obs of the Operations era); a report exists for every night in the window. Same columns as the tailgate files; "note (link)" is the Nightly Digest link for that day_obs. Times are UTC as written in the report (CLT = UTC−3 in late October).

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
| 2025-10-25 | [ND](https://usdf-rsp.slac.stanford.edu/nightlydigest/?startDayobs=20251025&endDayobs=20251025&telescope=Simonyi) | CLOSED | 0 | 0 | "Observations were canceled today due to the celebration of the end of an era of Rubin Construction." "Observations canceled for the night. Tour demonstrations were given, no problems." Planned (event), not weather/fault. No weather summary. | — |
| 2025-10-26 | [ND](https://usdf-rsp.slac.stanford.edu/nightlydigest/?startDayobs=20251026&endDayobs=20251026&telescope=Simonyi) | OPEN | 0.2 | 0.1 | "Simonyi's first night of operations! All tests run according to plan." Venting 23:30 UTC, prepare-for-on-sky 00:00 UTC, initial alignment BLOCK-T539, stability test, FBS survey BLOCK-T624; "We closed the dome at 7:50 UTC" (DomeAz failed on close, recovered). Daytime faults only (Chiller 1 reset, dome current issue, CalSys). Weather: "cloudy in the last couple of hours … transparency decreased". Mirror cover failed to close twice (OBS-1154). Close at 07:50 UTC is ~1.5 h before twilight but the report gives no reason — slight ambiguity, hence low non-zero P. | OBS-1154, OBS-1294, OBS-1269 |
| 2025-10-27 | [ND](https://usdf-rsp.slac.stanford.edu/nightlydigest/?startDayobs=20251027&endDayobs=20251027&telescope=Simonyi) | OPEN | 0 | 0.9 | "We completed all scheduled Simonyi tests, though we encountered some issues during the run." Louver E1 22:30 UTC, shutters 23:00 UTC; initial alignment converged to 0.4″; "MTRotator FAULT (OBS-902, 20 min lost)"; "MTAOS faulted due to MTRotator not reporting angle (OBS-1304, 48 minutes lost)"; thermal degradation, M1M3TS setpoints adjusted ~04:10 UTC; "We closed the dome at 8:25 UTC". ≈1.1 h lost to faults. Weather: thin clouds, winds 4–9 m/s, no loss stated. AuxTel not operated (ATMCS faults, OBS-1294). | OBS-902, OBS-1304, OBS-1305, OBS-1294 |
| 2025-10-28 | [ND](https://usdf-rsp.slac.stanford.edu/nightlydigest/?startDayobs=20251028&endDayobs=20251028&telescope=Simonyi) | PARTIAL (≈ closed) | 0 | 1.0 | "Unfortunately for Simonyi we lost almost the entire night due to a series of major faults that reduced total on sky time to about 30 - 45 minutes." Dome shutter fault during handover 19:38→23:25 UTC ("~3.5 hours"); "Shortly after getting on sky, dynalene chiller 01 failed and we had to swtich, causing a 3-hour delay for camera"; network crash (IT pixel-firewall work) "lost most AT and MT systems"; "M1M3 faulted … 45 minutes of recovery"; "We closed early and ran dynamic tests instead." Weather: wind dropped to ~3 m/s at open, no weather loss. | — |
| 2025-10-29 | [ND](https://usdf-rsp.slac.stanford.edu/nightlydigest/?startDayobs=20251029&endDayobs=20251029&telescope=Simonyi) | PARTIAL (≈ closed) | 0 | 1.0 | Dome shutter and louver opened 23:34 UTC; "Simonyi was on-sky at ~ 00:10." "Shortly after getting on sky, the camera team alerted us to a dynalene emergency. They had to power off all CCDs and REBs. Recovery took several hours, but we determined that getting back on sky was a risk with the camera in an unsecured state. We spent the remainder of the night doing calibration and CBP testing. (OBS-1310)". "Weather cooperated all night." Daytime: GIS interlocks, M1M3/M2 faults, LOVE lost 2.5 h, MTRotator pull-cord (OBS-875). | OBS-1316, OBS-875, OBS-1318, OBS-1310 |
| 2025-10-30 | [ND](https://usdf-rsp.slac.stanford.edu/nightlydigest/?startDayobs=20251030&endDayobs=20251030&telescope=Simonyi) | OPEN | 0 | 0.3 | "The night was dedicated to AOS testing." Shutter and louver opened 23:14 UTC; initial alignment then LUT-005; "multiple CSCs failed (MTMount, MTRotator, and MTPtg), triggered by the CCW — please refer to OBS-738 … Approximately 20 minutes were lost." "We ran out of time for the last elevation 25." Cryo 6 trip at end of night killed the daily cals only. Weather: "clear skies throughout", wind ~5 m/s. ≈20 min lost to fault. | OBS-1319, OBS-1320, OBS-1323, OBS-1322, OBS-738 |
| 2025-10-31 | [ND](https://usdf-rsp.slac.stanford.edu/nightlydigest/?startDayobs=20251031&endDayobs=20251031&telescope=Simonyi) | PARTIAL (≈ closed) | 1.0 | 0.05 | "Lost majority of tonight due to humidity, and clouds". "We opened dome and louver at 23:18 UTC (humidity ~ 60 %) … humidity reached eventually to 80 % so quickly, so we closed the dome immediately at 23:44 UTC. The dome never go reopened due to fluctuating humidity, continuous drop in ambient outside temperature … and later dense cloud coverage." "First 3 hrs after sunset were humid (>65% relative humidity) and later half of the night was completley overcast". Closed-dome time: TMA dynamic tests, whitelight flats, CBP QE sweeps (tunable laser power-off issue OBS-1230, random rotator fault — no sky loss). "We went on sky for last 1.5 hrs" with bad seeing; initial alignment and focus sweeps. AuxTel also shut down for humidity > 80% (AuxTel statement). | OBS-1326, OBS-1230, OBS-1325 |

## Summary for this window
- Weather closures/losses: Oct 31 (humidity then overcast; dome closed 23:44 UTC, only the last ~1.5 h on sky). Possible minor weather influence on the Oct 26 early close (clouds in the last hours, not stated as the reason).
- Fault closures: Oct 28 (dome shutter ~3.5 h, Dynalene chiller 01 ~3 h, network crash, M1M3 fault; 30–45 min on sky), Oct 29 (Dynalene emergency shortly after 00:10 UTC, camera powered off, rest of night in-dome; OBS-1310). Minor fault losses: Oct 27 (≈1.1 h, OBS-902/OBS-1304), Oct 30 (≈20 min, OBS-738).
- Neither: Oct 25 (observations canceled for the end-of-Construction celebration — planned).
- Power glitches: none reported.
- UNKNOWN: none (all 7 nights have a report).

## Differences vs the tailgate file (Source 1)
- Oct 25: tailgate CLOSED with no reason ("?/?"); night log gives the reason — celebration, planned → 0/0.
- Oct 26: tailgate PARTIAL fault (0.9) from the chiller/dome/mirror-cover items; night log says those were daytime issues and "All tests run according to plan" → OPEN.
- Oct 27: both OPEN; night log quantifies ≈1.1 h of fault loss (20 + 48 min).
- Oct 28: agree (PARTIAL ≈ closed, faults); night log lists no OBS keys, tailgate has OBS-1309/1310/1312.
- Oct 29: tailgate PARTIAL with on-sky time unstated; night log makes it PARTIAL (≈ closed) — on sky ~00:10 UTC, then in-dome the rest of the night.
- Oct 30: tailgate UNKNOWN (no note on the holiday) → night log OPEN, clear skies, ≈20 min fault loss.
- Oct 31: tailgate OPEN (0.2/0.1, humidity stated for AuxTel only) → night log PARTIAL (≈ closed), weather 1.0. The tailgate inference was wrong.

## Caveats
- Single-source table from the night reports; Slack/Confluence not consulted.
- Oct 26 close at 07:50 UTC: the report does not say whether the early close was planned (end of test list), clouds or the DomeAz fault; low mixed P assigned.
- Oct 28: the dome shutter loss (19:38–23:25 UTC) was mostly daytime/twilight; the ≈3 h Dynalene delay and the network crash are the on-sky losses. The network crash is attributed to IT firewall work — counted as fault, not weather.
- Oct 31: the "last 1.5 hrs" on sky has no clock times in the report; the 23:18/23:44 UTC open/close times are the only ones given.
- Hours lost are "≈" where two clock times allow it; otherwise taken from the report's own estimates ("20 min", "48 minutes", "3-hour delay").

---
