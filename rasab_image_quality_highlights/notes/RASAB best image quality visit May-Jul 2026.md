# Best image-quality visit, 1 May – 27 Jul 2026 (RASAB presentation)

Date: 2026-10-20. Q&A between Bruno Quint and Claude Code, saved for the RASAB talk.
Companion to `RASAB best image quality visit Oct-Dec 2025.md` (same method).
Data source: ConsDB `cdb_lsstcam.visit1` + `visit1_quicklook` (+ `ccdvisit1_quicklook` for the
per-detector check) via the USDF Postgres replica (`rubin_nights.ConsDbSql`). Per-visit summary
cached in `../data/visits_science_20260501_20260727.csv`.

## Prompt

> Finally, I want the visit with the best image quality between May 2026 and Jul 27.

## Answer

Two answers, depending on whether engineering tests count.

### Best survey visit 2026052900643, and best visit overall 2026051200642

The best survey visit is **2026052900643**, the best of 25 923 Feature Based Scheduler survey
visits in the window. The best visit overall is **2026051200642**, an AOS closed-loop stability test
with the telescope parked at alt 70 / az 0 and the rotator at zero, so it is not a survey pointing.
The rows below are the same as in `RASAB best image quality visit Oct-Dec 2025.md`, grouped as
conditions, delivered image quality, uniformity across the focal plane, and PSF shape.

| Quantity | 2026052900643 (survey) | 2026051200642 (AOS test) |
|---|---|---|
| Night / seq_num | 2026-05-29 / 643 | 2026-05-12 / 642 |
| Band / exposure | y / 30 s | i / 30 s |
| Image type, program, reason | science, BLOCK-407, `template_blob_y_33.0` (survey, low-dust field) | science, BLOCK-T698, `fbs_driven_aos_stability_test` (parked alt 70 / az 0) |
| Observation start (UTC) | 2026-05-30 07:26:00 | 2026-05-13 05:35:59 |
| Field (RA, Dec) | 308.88, -19.20 deg | 243.60, -10.24 deg |
| Altitude / airmass | 68.2 deg / 1.08 | 70.1 deg / 1.06 |
| Azimuth / sky rotation | 64.2 / 146.7 deg | 359.4 / 90.0 deg |
| Wind speed / air temperature | 4.3 m/s / 11.2 °C | 4.6 m/s / 12.8 °C |
| DIMM seeing | 0.63 arcsec | not recorded |
| Donut-blur seeing estimate | 0.76 arcsec | 0.62 arcsec |
| AOS residual (optics) FWHM | 0.33 arcsec | 0.35 arcsec |
| **Delivered PSF FWHM, median over 188 detectors** | **0.540 arcsec** | **0.536 arcsec** |
| FWHM corrected to zenith (× airmass^-0.6) | 0.516 arcsec | 0.517 arcsec |
| Delivered / DIMM | 0.86 | n/a |
| Delivered / donut blur | 0.71 | 0.87 |
| FWHM across focal plane, min / 5th pct / 95th pct / max | 0.50 / 0.51 / 0.64 / 0.72 arcsec | 0.50 / 0.51 / 0.60 / 0.69 arcsec |
| FWHM uniformity, 5th to 95th percentile span | 0.14 arcsec | 0.09 arcsec |
| PSF ellipticity, median / 95th pct | 0.114 / 0.207 | 0.119 / 0.225 |
| Fraction of detectors with ellipticity > 0.2 | 6 % | 9 % |
| Median e1 / e2 | +0.086 / +0.002 | +0.080 / +0.038 |
| Guider mean e1 / e2 | -0.110 / +0.060 | -0.188 / +0.016 |

The eleven best raw-FWHM visits of the window are from the BLOCK-T698 test on 2026-05-12
(0.536–0.556 arcsec), with the survey visit above being the third best overall at 0.540 arcsec.
The difference between the two is 0.004 arcsec, well inside the measurement noise, so the survey
visit is the safer slide.

### Context

- **Compared with Oct–Dec 2025** the best visit improved from 0.65 to 0.54 arcsec, and the fraction
  of survey visits sharper than 0.8 arcsec rose from 3 % to 19 %. Row by row against 2025112700095:
  the 2026 survey visit is sharper but less uniform (5th to 95th percentile span 0.14 vs 0.08 arcsec,
  the two outer-raft tails at 0.64 arcsec) and slightly more elliptical in the median (0.114 vs 0.095),
  though with fewer detectors above |e| = 0.2 (6 % vs 9 %); its elongation is along e1 where the
  2025 visit's was along e2. Monthly median delivered FWHM:
  May 0.99, June 0.96, July 1.02 arcsec (vs 1.06–1.25 arcsec in Oct–Dec 2025).
- **The night 2026-05-29** had 881 survey visits with a nightly median of 0.75 arcsec, 457 visits
  below 0.75 arcsec and 93 below 0.60 arcsec. The seven best survey visits of the window are all
  y-band template visits from this night.
- **Per-band bests (survey visits):** u 0.73 (2026-05-19), g 0.64 (2026-05-19), r 0.58
  (2026-05-12), i 0.57 (2026-05-19), z 0.57 (2026-06-26), y 0.54 (2026-05-29) arcsec.
- **Zenith/500 nm corrected** the best is 2026052900256 (same night, i band, airmass 1.68, raw
  0.64 arcsec, corrected 0.51), but as before the raw number is the one to show.

## Method

- Window: dayObs 20260501–20260727; `img_type = 'science'`, `exp_time >= 15 s`,
  `psf_sigma_median IS NOT NULL` → 26 888 visits (25 923 BLOCK-407, 965 BLOCK-T698).
- Delivered FWHM = `psf_sigma_median` × 2√(2 ln 2) × 0.2 arcsec/pixel.
- Per-detector spread for the two visits from `ccdvisit1_quicklook.psf_sigma`, excluding corner
  wavefront sensors (191, 192, 195, 196, 199, 200, 203, 204). Ellipticity from
  `psf_ixx/ixy/iyy`: e1 = (Ixx − Iyy)/(Ixx + Iyy), e2 = 2 Ixy/(Ixx + Iyy), |e| = √(e1² + e2²).
  Guider e1/e2 are `visit1_quicklook.guider_e1_mean/guider_e2_mean`.
- Table numbers via `describe_visit()` in `../python/rasab_iq_reports.py` (re-queried 2026-10-20).
- Zenith/500 nm correction (caveat only): FWHM × airmass^-0.6 × (λ_eff/500 nm)^0.2.
