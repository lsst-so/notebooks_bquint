# RASAB image-quality highlights

Three one-off ConsDB look-ups for the RASAB 2026 presentation narrative, with the prompt, the
answer and the method saved so they can be quoted and reproduced.

- **Status:** Done (2026-10-20).
- **Ticket:** — (RASAB 2026 talk)

## Results

| Question | Answer | Note |
|---|---|---|
| Best delivered image quality, 24 Oct – 31 Dec 2025 | visit **2025112700095**, i band, 0.65 arcsec | [notes/RASAB best image quality visit Oct-Dec 2025.md](notes/RASAB%20best%20image%20quality%20visit%20Oct-Dec%202025.md) |
| Good FWHM but strongly elliptical PSF, FBS visits 15 Feb – 14 Mar 2026 | visit **2026022800532**, y band, 0.77 arcsec, median \|e\| 0.36 | [notes/RASAB good FWHM bad ellipticity visit Feb-Mar 2026.md](notes/RASAB%20good%20FWHM%20bad%20ellipticity%20visit%20Feb-Mar%202026.md) |
| Best delivered image quality, 1 May – 27 Jul 2026 | survey visit **2026052900643**, y band, 0.54 arcsec (AOS test visit 2026051200642 at 0.536) | [notes/RASAB best image quality visit May-Jul 2026.md](notes/RASAB%20best%20image%20quality%20visit%20May-Jul%202026.md) |

## Contents

- `notes/` — the three saved Q&A notes and
  [HOWTO-reproduce-RASAB-reports.md](notes/HOWTO-reproduce-RASAB-reports.md) (environment,
  exact commands, tables, formulas, judgement calls).
- `python/rasab_iq_reports.py` — reproduces the reports from ConsDB; `best <d0> <d1>` and
  `ellip <d0> <d1> --programs ...` sub-commands. Run from a stack shell with
  `PGPASSFILE=~/.lsst/postgres-credentials.txt` (Postgres replica via `rubin_nights`).
- `data/` — per-visit CSV summaries written by the script (2–6 MB each).

## Method in one paragraph

Science visits (`img_type = 'science'`, `exp_time >= 15 s`) from `cdb_lsstcam.visit1` joined to
`visit1_quicklook`. Delivered FWHM = `psf_sigma` × 2√(2 ln 2) × 0.2 arcsec/pix. Per-detector
spread and PSF ellipticity (from `psf_ixx/ixy/iyy`) from `ccdvisit1_quicklook`, excluding the
corner wavefront sensors. Rankings use raw delivered FWHM; the zenith/500 nm-corrected value is
reported only as a caveat because it favours high-airmass visits.
