# Image-quality trending

Per-visit image-quality trends from ConsDB quicklook metrics (`ccdvisit1_quicklook`):
PSF size and shape, Zernikes, comparison to simulation, correlations and DDF fields.

- **Status:** WIP.
- `notebooks/image_quality_minimal.ipynb` — minimal ConsDB query; caches results to
  `data/consdb_<start>_<end>.csv`.
- `notebooks/image_quality_trending.ipynb` — full trending analysis.
- `data/` — ConsDB CSV caches. They are gitignored (the 2026-01-19 → 2026-04-07 export is
  188 MB, above GitHub's 100 MB limit); regenerate with `image_quality_minimal.ipynb`.
