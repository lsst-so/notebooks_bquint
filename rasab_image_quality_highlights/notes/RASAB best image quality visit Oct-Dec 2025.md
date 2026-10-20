# Best image-quality visit, Oct–Dec 2025 (RASAB presentation)

Date: 2026-10-20. Q&A between Bruno Quint and Claude Code, saved for the RASAB talk.
Data source: ConsDB `cdb_lsstcam.visit1` + `visit1_quicklook` (+ `ccdvisit1_quicklook` for the
per-detector check), queried through the USDF Postgres replica (`rubin_nights.ConsDbSql`).

## Prompt

> I am generating a presentation for RASAB. As part of the narrative, I want to tell the audience
> that we reached very good image quality in the period between Oct (start of operations) and Dec,
> where we truly believed that we can start the LSST. What was visit with the best image quality in
> this period?

## Answer

The best delivered image quality in Oct–Dec 2025 was visit **2025112700095**, taken on the night of
2025-11-27 (dayObs 20251127, seq_num 95). It is a 30 s i-band LSSTCam science visit from the survey
block BLOCK-407, on a low-dust survey field.

Key numbers for that visit, from the ConsDB quicklook tables. The rows are the same as in
`RASAB best image quality visit May-Jul 2026.md`, grouped as conditions, delivered image quality,
uniformity across the focal plane, and PSF shape, so the two periods can be compared row by row.

| Quantity | 2025112700095 |
|---|---|
| Night / seq_num | 2025-11-27 / 95 |
| Band / exposure | i / 30 s |
| Image type, program, reason | science, BLOCK-407, `template_blob_i_33.0` (survey, low-dust field) |
| Observation start (UTC) | 2025-11-28 03:09:38 |
| Field (RA, Dec) | 31.08, -42.29 deg |
| Altitude / airmass | 74.4 deg / 1.04 |
| Azimuth / sky rotation | 216.7 / 310.7 deg |
| Wind speed / air temperature | 9.1 m/s / 13.2 °C |
| DIMM seeing | 0.67 arcsec |
| Donut-blur seeing estimate | 0.68 arcsec |
| AOS residual (optics) FWHM | 0.38 arcsec |
| **Delivered PSF FWHM, median over 188 detectors** | **0.646 arcsec** |
| FWHM corrected to zenith (× airmass^-0.6) | 0.631 arcsec |
| Delivered / DIMM | 0.97 |
| Delivered / donut blur | 0.95 |
| FWHM across focal plane, min / 5th pct / 95th pct / max | 0.60 / 0.61 / 0.69 / 0.74 arcsec |
| FWHM uniformity, 5th to 95th percentile span | 0.08 arcsec |
| PSF ellipticity, median / 95th pct | 0.095 / 0.234 |
| Fraction of detectors with ellipticity > 0.2 | 9 % |
| Median e1 / e2 | +0.005 / +0.075 |
| Guider mean e1 / e2 | -0.036 / +0.018 |

For the narrative, three points are worth stating alongside it:

- **The delivered FWHM equals the seeing.** DIMM and donut blur both gave about 0.67 arcsec, and the
  telescope delivered 0.65 arcsec. The system contribution that night was essentially negligible.
- **It was not a one-off.** The next best visits were all on 2025-11-26 and 2025-11-27 in i band, at
  0.67 to 0.72 arcsec. That night had 326 science visits with 28 below 0.75 arcsec and a nightly
  median of 0.89 arcsec.
- **Per-band bests in the period** were g 0.78 (2025-11-14), r 0.77 (2025-12-18), i 0.65
  (2025-11-27), z 0.72 (2025-12-03), y 0.69 (2025-11-25), u 0.88 (2025-11-24) arcsec.

One caveat on the ranking. The ranking is on raw delivered FWHM, which is what the audience will care
about. Corrected to zenith and 500 nm, the best is visit 2025121600078 on 2025-12-16, but that one
was at airmass 2.2, so its raw FWHM was 0.92 arcsec and it is a weaker slide. The selection was
restricted to 7479 science-type visits with exposures of at least 15 s, which excludes acquisition
and engineering-test images. Monthly median delivered FWHM was 1.25 arcsec in late October, 1.07 in
November and 1.06 in December.

## Method

- Period: dayObs 20251024–20251231; `img_type = 'science'`, `exp_time >= 15 s`,
  `psf_sigma_median IS NOT NULL`.
- Delivered FWHM = `psf_sigma_median` × 2√(2 ln 2) × 0.2 arcsec/pixel.
- Zenith/500 nm correction (caveat only): FWHM × airmass^-0.6 × (λ_eff/500 nm)^0.2.
- Per-detector spread for the winning visit from `ccdvisit1_quicklook.psf_sigma`, excluding the
  corner wavefront sensors (detectors 191, 192, 195, 196, 199, 200, 203, 204). Ellipticity from
  `psf_ixx/ixy/iyy`: e1 = (Ixx − Iyy)/(Ixx + Iyy), e2 = 2 Ixy/(Ixx + Iyy), |e| = √(e1² + e2²).
  Guider e1/e2 are `visit1_quicklook.guider_e1_mean/guider_e2_mean`.
- Table numbers via `describe_visit()` in `../python/rasab_iq_reports.py` (re-queried 2026-10-20).
