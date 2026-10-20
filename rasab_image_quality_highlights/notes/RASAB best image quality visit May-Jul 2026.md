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

### Best survey visit: **2026052900643**

Night 2026-05-29 (dayObs 20260529), seq_num 643, 30 s y band, BLOCK-407 `template_blob_y_33.0`,
low-dust field, observed 2026-05-30 07:26 UTC. This is the best of 25 923 Feature Based Scheduler
survey visits in the window.

| Quantity | Value |
|---|---|
| Delivered PSF FWHM (median over 188 detectors) | 0.54 arcsec |
| FWHM 5th–95th percentile across the focal plane | 0.51 – 0.64 arcsec |
| Median PSF ellipticity | 0.11 |
| AOS residual (optics) FWHM | 0.33 arcsec |
| DIMM seeing | 0.63 arcsec |
| Donut-blur seeing estimate | 0.76 arcsec |
| Airmass / altitude / azimuth | 1.08 / 68 / 64 deg |
| Field (RA, Dec) | 308.88, −19.20 deg |
| Wind / air temperature | 4.3 m/s / 11.2 °C |

### Best visit overall: **2026051200642**

Night 2026-05-12 (dayObs 20260512), seq_num 642, 30 s i band, BLOCK-T698
`fbs_driven_aos_stability_test`, observed 2026-05-13 05:36 UTC. Median FWHM **0.536 arcsec**
(5th–95th percentile 0.51–0.60), AOS residual 0.35 arcsec, donut blur 0.62 arcsec, median
ellipticity 0.12. The telescope was parked at alt 70 / az 0 with the rotator at zero for an AOS
closed-loop stability test, so it is not a survey pointing. The eleven best raw-FWHM visits of the
window are from this test on this night (0.536–0.556 arcsec), with the survey visit above being the
third best overall at 0.540 arcsec. The difference between the two is 0.004 arcsec, well inside the
measurement noise, so the survey visit is the safer slide.

### Context

- **Compared with Oct–Dec 2025** the best visit improved from 0.65 to 0.54 arcsec, and the fraction
  of survey visits sharper than 0.8 arcsec rose from 3 % to 19 %. Monthly median delivered FWHM:
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
  `psf_ixx/ixy/iyy`.
- Zenith/500 nm correction (caveat only): FWHM × airmass^-0.6 × (λ_eff/500 nm)^0.2.
