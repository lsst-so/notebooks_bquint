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

Key numbers for that visit, from the ConsDB quicklook table:

| Quantity | Value |
|---|---|
| Delivered PSF FWHM (median over 188 detectors) | 0.65 arcsec |
| FWHM range across the focal plane (5th to 95th percentile) | 0.61 to 0.69 arcsec |
| AOS residual (optics) FWHM | 0.38 arcsec |
| DIMM seeing at the time | 0.67 arcsec |
| Donut-blur seeing estimate | 0.68 arcsec |
| Airmass / altitude | 1.04 / 74 deg |
| Field (RA, Dec) | 31.08, -42.29 deg |
| Observation start (UTC) | 2025-11-28 03:09:38 |

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
  corner wavefront sensors (detectors 191, 192, 195, 196, 199, 200, 203, 204).
