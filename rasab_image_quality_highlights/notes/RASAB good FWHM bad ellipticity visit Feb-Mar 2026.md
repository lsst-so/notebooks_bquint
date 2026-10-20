# Good-FWHM, bad-shape visit, 15 Feb – 14 Mar 2026 (RASAB presentation)

Date: 2026-10-20. Q&A between Bruno Quint and Claude Code, saved for the RASAB talk.
Companion to `RASAB best image quality visit Oct-Dec 2025.md`.
Data source: ConsDB `cdb_lsstcam.visit1`, `visit1_quicklook`, `ccdvisit1`, `ccdvisit1_quicklook`
via the USDF Postgres replica (`rubin_nights.ConsDbSql`). Per-visit summary cached in
`../data/visits_fbs_20260215_20260314.csv`.

## Prompt

> I want the same analysis between the last two weeks of Feb 2026 and the first two weeks of March
> 2026 considering only Feature Based Scheduler observations (BLOCK-T624). However, the idea here is
> to look for an image with a good average FWHM but with a large ellipticity or bad shapes. Not sure
> if you will have access to metrics that can tell that.

## Answer

**Program note.** BLOCK-T624 is not the survey block: ConsDB has only 12 visits under it in total
(Oct 2025 – Apr 2026, observation reason "checking"). The Feature Based Scheduler science in this
window was recorded as **BLOCK-421** (6818 visits) and **BLOCK-407** (1993 visits, until early
March). Both were used; all the candidates below are BLOCK-421.

**Shape metrics are available.** `ccdvisit1_quicklook` has the per-detector PSF second moments
(`psf_ixx`, `psf_ixy`, `psf_iyy`), from which e1 = (Ixx − Iyy)/(Ixx + Iyy), e2 = 2 Ixy/(Ixx + Iyy),
|e| = √(e1² + e2²) and the position angle follow for each of the 189 science detectors. The
visit-level table also carries `guider_e1_mean` / `guider_e2_mean` (guider-star ellipticity) and
`psf_star_delta_e1/e2` (PSF-model residuals, which measure model fidelity, not PSF shape).

### Recommended visit: **2026022800532**

Night 2026-02-28 (dayObs 20260228), seq_num 532, 30 s y band, BLOCK-421 `template_blob_y_33.0`,
observed 2026-03-01 07:49 UTC.

| Quantity | Value |
|---|---|
| Delivered PSF FWHM (median over 174 detectors) | 0.77 arcsec |
| FWHM 5th–95th percentile across the focal plane | 0.68 – 1.03 arcsec |
| Median ellipticity \|e\| | 0.36 |
| Ellipticity 5th–95th percentile | 0.25 – 0.45 |
| Detectors with \|e\| > 0.2 | 98 % |
| Median e1 / e2 | −0.20 / +0.29 |
| PSF position angle (median, std over detectors) | 62 deg, 4 deg |
| Guider e1 / e2 | −0.19 / +0.28 |
| AOS residual FWHM / donut-blur seeing / DIMM | 0.46 / 0.84 / 0.70 arcsec |
| Altitude / azimuth / rotator sky angle | 73 / 31 / 120 deg |
| Wind | 3.4 m/s |

Why this one works as the slide:

- **FWHM is in the best 10 % of the window** (window median 0.99 arcsec, 5th percentile 0.80) while
  the ellipticity is the highest of any sub-0.85 arcsec visit, and the 7th highest of all 8811 visits
  (window median \|e\| 0.10, 99th percentile 0.26).
- **The distortion is coherent, not local.** Every raft has \|e\| between 0.25 and 0.44 and the
  position angle is the same to 4 deg across the whole field. The guider stars show the same e1/e2,
  so this is an elongation of the whole PSF, not a few bad corners.
- **The atmosphere was fine.** DIMM 0.70 arcsec and AOS residual 0.46 arcsec, so the elongation is
  not seeing. It looks like a tracking/rotator or wind-shake-type shape error, worth a few words in
  the talk.

### Runner-up: **2026022800518**

Same night, seq_num 518, y band, 10 minutes earlier. FWHM 0.80 arcsec, median \|e\| 0.31 with
e1 = −0.31 and e2 ≈ 0 across all 21 rafts (98 % of detectors above 0.2), i.e. a pure stretch along
one detector axis. Cleaner single-direction case if that is easier to explain.

### Context for the night

Night 20260228 had 568 FBS visits with a nightly median \|e\| of 0.13 and 16 % of visits above
0.2, versus 5 % for the full window. Elliptical visits came in short bursts (seq 508–509, 518–521,
531–532, 568–572, 591–595) while the FWHM stayed at 0.65–0.80 arcsec. Seven of the ten most
elliptical good-FWHM visits in the window are from this night. For contrast, visit 2026022800539
seven minutes later is the sharpest visit of the window (0.63 arcsec, median \|e\| 0.16).

### Other "bad shape" flavours, if preferred

- **Bad corners, good centre:** 2026030900361 (2026-03-09, y, BLOCK-407). FWHM 0.81 arcsec,
  median \|e\| only 0.08, but 95th percentile 0.44.
- **Largest FWHM variation across the field:** 2026022600566 (2026-02-26, r). FWHM 0.82 arcsec
  median but 0.66 to 1.19 arcsec from 5th to 95th percentile, with low ellipticity.

## Method

- Window: dayObs 20260215–20260314; `img_type = 'science'`, `exp_time >= 15 s`,
  `science_program IN ('BLOCK-421', 'BLOCK-407')`; detectors with non-null `psf_ixx`, excluding the
  corner wavefront sensors (191, 192, 195, 196, 199, 200, 203, 204); visits with ≥150 detectors.
  1.66 M detector rows, 8811 visits.
- FWHM = `psf_sigma` × 2√(2 ln 2) × 0.2 arcsec/pixel, per detector, then per-visit median and
  5th/95th percentiles. Ellipticity from the second moments as above, per detector, then per-visit
  median and 95th percentile.
- "Good FWHM" = per-visit median FWHM < 0.85 arcsec (1082 visits); ranked by median \|e\|.
