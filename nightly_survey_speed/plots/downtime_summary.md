# Downtime summary, 2025-10-26 to 2026-07-13

Nights lost = nights inside the span with fewer than 50 plotted visits in ConsDB (`cdb_lsstcam.visit1`, airmass > 0, img_type in acq/science/cwfs/focus). Spans marked * are drawn on `utilization_annotated.png`.

| Start | End | Nights lost | Label | Category | Severity | Confidence | FRACAS |
|---|---|---|---|---|---|---|---|
| 2025-10-29 | 2025-10-29 | 1 | UNKNOWN | unknown | partial | low | - |
| 2025-11-06 | 2025-11-06 | 1 | Power loss (Dynalene/PCS/Cryo)* | fault | partial | high | FRACAS-314 |
| 2025-11-20 | 2025-11-21 | 0 | Dynalene flow lost after power return* | fault | partial | medium | FRACAS-321 |
| 2025-12-05 | 2025-12-05 | 1 | UNKNOWN | unknown | partial | low | - |
| 2025-12-07 | 2025-12-07 | 1 | UNKNOWN | unknown | full | low | - |
| 2025-12-13 | 2025-12-13 | 1 | UNKNOWN | unknown | full | low | - |
| 2025-12-20 | 2026-01-10 | 5 | Water condensation* | fault | partial | medium | FRACAS-330 |
| 2026-01-14 | 2026-01-14 | 1 | UNKNOWN | unknown | full | low | - |
| 2026-01-20 | 2026-01-26 | 7 | Dynalene loss* | fault | full | high | FRACAS-336 |
| 2026-01-29 | 2026-01-29 | 1 | TMA axes PXI (EtherCAT)* | fault | full | high | FRACAS-337 |
| 2026-01-30 | 2026-02-15 | 17 | LSSTCam vacuum leak #1* | fault | full | high | FRACAS-338 |
| 2026-02-12 | 2026-03-19 | 8 | Earthquake: TMA limited to 5% motion* | degraded | degraded | high | FRACAS-346 |
| 2026-02-17 | 2026-02-17 | 1 | UNKNOWN | unknown | full | low | - |
| 2026-02-20 | 2026-02-21 | 2 | UNKNOWN | unknown | full | low | - |
| 2026-02-26 | 2026-03-18 | 1 | PCS chiller flow variations* | fault | partial | medium | FRACAS-352, FRACAS-364 |
| 2026-03-04 | 2026-03-04 | 1 | UNKNOWN | unknown | full | low | - |
| 2026-03-20 | 2026-03-23 | 4 | PCS compressor failure + vacuum leak #2* | fault | full | high | FRACAS-366, FRACAS-367 |
| 2026-04-16 | 2026-04-16 | 1 | Closed-dome engineering day* | planned | full | high | - |
| 2026-04-17 | 2026-04-17 | 1 | UNKNOWN | unknown | full | low | - |
| 2026-04-22 | 2026-04-22 | 1 | UNKNOWN | unknown | full | low | - |
| 2026-05-02 | 2026-05-07 | 6 | TMA encoder incident + camera cryo warm-up* | fault | full | high | FRACAS-381, FRACAS-383, FRACAS-384 |
| 2026-05-08 | 2026-05-10 | 3 | UNKNOWN | unknown | full | low | - |
| 2026-05-14 | 2026-05-15 | 2 | UNKNOWN | unknown | full | low | - |
| 2026-05-20 | 2026-05-20 | 1 | UNKNOWN | unknown | full | low | - |
| 2026-05-27 | 2026-05-27 | 1 | UNKNOWN | unknown | partial | low | - |
| 2026-06-01 | 2026-06-02 | 2 | UNKNOWN | unknown | full | low | - |
| 2026-06-05 | 2026-06-05 | 1 | UNKNOWN | unknown | full | low | - |
| 2026-06-08 | 2026-06-10 | 3 | Weather* | weather | full | high | - |
| 2026-06-15 | 2026-06-18 | 4 | Weather* | weather | full | high | - |
| 2026-06-20 | 2026-06-22 | 3 | UNKNOWN | unknown | full | low | - |
| 2026-06-23 | 2026-06-24 | 2 | Camera cryo* | fault | full | high | - |
| 2026-07-01 | 2026-07-04 | 4 | Weather and TMA faults* | mixed | partial | high | FRACAS-400, FRACAS-403 |
| 2026-07-07 | 2026-07-07 | 1 | UNKNOWN | unknown | full | low | - |
| 2026-07-08 | 2026-07-08 | 0 | LSSTCam REB power supplies tripped* | fault | partial | medium | FRACAS-404 |
| 2026-07-14 | 2026-10-12 | outside range | July storm and recovery | weather | full | high | - |

## Nights lost per category (in range, sum over spans)

| Category | Nights lost |
|---|---|
| fault | 44 |
| weather | 7 |
| planned | 1 |
| mixed | 4 |
| degraded | 8 |
| unknown | 25 |
| **total** | **89** |

Distinct blank nights in ConsDB over the range: **80**, of which 55 are covered by a labelled span and 25 are UNKNOWN.
The per-category sum exceeds this because the degraded span (earthquake, TMA at 5 %) overlaps other spans, so its blank nights are counted twice.
