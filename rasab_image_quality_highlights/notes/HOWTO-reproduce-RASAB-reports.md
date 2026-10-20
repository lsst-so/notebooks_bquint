# How the three RASAB image-quality reports were produced

The three notes in this folder (`RASAB best image quality visit Oct-Dec 2025.md`,
`RASAB good FWHM bad ellipticity visit Feb-Mar 2026.md`,
`RASAB best image quality visit May-Jul 2026.md`) were produced on 2026-10-20 from ConsDB
quicklook metrics. Everything is reproducible with `../python/rasab_iq_reports.py`.

## 1. Environment

Run from an SDF login node shell (VS Code over SSH) or any shell with the stack:

```bash
source /sdf/group/rubin/sw/loadLSST.bash
setup lsst_distrib                      # provides rubin_nights, pandas, numpy
export PGPASSFILE=$HOME/.lsst/postgres-credentials.txt
cd rasab_image_quality_highlights/python
```

The login node has no RSP token, so the script queries the ConsDB **Postgres replica**
(`usdf-summitdb-logical-replica-svc.sdf.slac.stanford.edu`) through
`rubin_nights.consdb_query.ConsDbSql(site="usdf")`. The credentials file above is required.
In a Nublado kernel, `rubin_nights.connections.get_clients()["consdb"]` also works and can be
swapped into `get_client()`.

## 2. Commands

```bash
# Report 1: best delivered image quality, 24 Oct – 31 Dec 2025
python rasab_iq_reports.py best 20251024 20251231

# Report 2: good FWHM but bad PSF shape, FBS visits, 15 Feb – 14 Mar 2026
#   NB: BLOCK-T624 only has 12 "checking" visits in ConsDB; the FBS survey science in this
#   window is BLOCK-421 (and BLOCK-407 until early March).
python rasab_iq_reports.py ellip 20260215 20260314 --programs BLOCK-421 BLOCK-407

# Report 3: best delivered image quality, 1 May – 27 Jul 2026
python rasab_iq_reports.py best 20260501 20260727
```

`best` runs in about a minute. `ellip` pulls per-detector rows for every visit (about 1.7 M rows
for a 4-week window) and takes a few minutes.

Each run writes a per-visit CSV to `../data/` (`visits_science_<d0>_<d1>.csv` for `best`,
`visits_fbs_<d0>_<d1>.csv` for `ellip`) and prints the ranking tables, the per-band bests, the
monthly statistics and a per-detector breakdown of the winning visit.

## 3. What the script does

Tables (schema: https://sdm-schemas.lsst.io/cdb_lsstcam.html):

- `cdb_lsstcam.visit1` – visit metadata (band, airmass, altitude, DIMM seeing, program, ...).
- `cdb_lsstcam.visit1_quicklook` – per-visit aggregates (`psf_sigma_median`, `aos_fwhm`,
  `donut_blur_fwhm`, `guider_e1_mean`, ...).
- `cdb_lsstcam.ccdvisit1` + `ccdvisit1_quicklook` – per-detector `psf_sigma`, `psf_ixx`,
  `psf_ixy`, `psf_iyy`.

Selection: `img_type = 'science'`, `exp_time >= 15 s`, `psf_sigma_median IS NOT NULL`, optional
`science_program` list. Corner wavefront sensors (detectors 191, 192, 195, 196, 199, 200, 203,
204) are excluded from per-detector statistics.

Derived quantities:

| Quantity | Formula |
|---|---|
| Delivered FWHM [arcsec] | `psf_sigma` [pix] × 2√(2 ln 2) × 0.2 arcsec/pix |
| Zenith/500 nm FWHM (caveat only) | FWHM × airmass^-0.6 × (λ_eff / 500 nm)^0.2, λ_eff = u 367, g 482, r 622, i 755, z 869, y 971 nm |
| e1, e2 | (Ixx − Iyy)/(Ixx + Iyy), 2 Ixy/(Ixx + Iyy) |
| \|e\|, PA | √(e1² + e2²), ½ atan2(e2, e1) |
| FoV FWHM variation | √(FWHM_p95² − FWHM_p05²) over detectors |

Ranking:

- `best`: sort visits by per-visit median delivered FWHM. Report the raw-FWHM winner (what the
  audience sees), the zenith-corrected winner as a caveat (it favours high-airmass visits), the
  per-band bests, monthly medians, the fraction below 0.8 arcsec, the winner's per-detector
  spread and its night's statistics. If the winner is from an engineering block, the best visit of
  the dominant survey block is reported too.
- `ellip`: keep visits with ≥150 detectors and median FWHM < 0.85 arcsec (`--fwhm-max`), rank by
  per-visit median |e|. Also list the 95th-percentile-|e| ranking (bad corners) and the FoV
  FWHM-variation ranking (strong gradient) as alternative "bad shape" flavours, and a per-raft
  breakdown of the top candidate to show whether the elongation is coherent across the field.

## 4. Judgement calls made in the notes

- Raw delivered FWHM, not zenith-corrected, was used for "best", because that is the number the
  audience will relate to.
- For May–Jul 2026 the overall winner (0.536 arcsec) was an AOS stability test parked at a fixed
  alt/az (BLOCK-T698); the best survey visit (0.540 arcsec) was recommended instead since the
  difference is within noise.
- For the ellipticity report, the guider e1/e2 and the per-raft position-angle scatter were used
  to argue that the elongation was a whole-PSF effect rather than a local one.
