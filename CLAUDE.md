# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

`notebooks_bquint` (GitHub: `lsst-sitcom/notebooks_bquint`) is Bruno Quint's personal collection of
Rubin Observatory / LSST commissioning engineering-analysis notebooks. Unlike the parent `notebooks/`
working directory (which is *not* a repo), this **is** its own git repository. There is no package, no
test suite, and no build — the `python/` directory is empty and the deliverables are the notebooks
themselves. A broader description of the RSP/SLAC SDF environment lives in the parent
`../../CLAUDE.md`; this file only adds what is specific to this repo.

All analysis notebooks live under `notebooks/`, grouped loosely by subsystem
(`image_quality/`, `mthexapod/`) or named for the study (`TMA - Maximum Slew Velocities.ipynb`,
`OBS-1479 Condensation Investigation.ipynb`, `rso87.ipynb`). Names encode the Jira ticket or campaign
when there is one — preserve that scheme for new notebooks.

## Environment & tooling

- Runs on the LSST Science Pipelines / `ts_*` stack provided by **EUPS**, not pip. `lsst.*` and
  `lsst_efd_client` are already on the kernel `PYTHONPATH`; do not add pip installs for them.
- `create_dot_env.py` — run from inside a set-up kernel shell (`python create_dot_env.py`) to dump
  `PATH`/`PYTHONPATH`/`LD_LIBRARY_PATH` plus every `*_DIR` with a matching `SETUP_*` var into `.env`
  so VS Code's Python extension can resolve the stack. The generated `.env` is large and
  machine-specific — regenerate, never hand-edit.
- Lint/format with **ruff** (`ruff check <file>` / `ruff format <file>`); a `.ruff_cache/` is present
  under `notebooks/mthexapod/`.
- Notebooks commonly open with `%load_ext autoreload` / `%autoreload 2` and `%load_ext lab_black`
  (Black-on-save for cells). `%matplotlib widget` is used for interactive plots.
- `.gitignore` excludes `**/.ipynb_checkpoints`. Note `Untitled.ipynb` and CSV data caches are
  currently committed/tracked despite being scratch/derived — be deliberate about what you add.

## Data access patterns specific to this repo

Three backends show up across the notebooks:

- **EFD** (telemetry time series) — `makeEfdClient()` + `getEfdData(...)`, or directly
  `lsst_efd_client.EfdClient("usdf_efd")`. TMA slew/track analyses use
  `lsst.summit.utils.tmaUtils.TMAEventMaker` / `TMAState`, scoped by integer `dayObs` (e.g. `20260407`).
- **ConsDB** (per-visit quicklook image-quality metrics) — the image-quality notebooks query it via:
  ```python
  import os
  os.environ["no_proxy"] += ",.consdb"          # required, or the in-cluster call is proxied and fails
  from lsst.summit.utils import ConsDbClient
  client = ConsDbClient("http://consdb-pq.consdb:8080/consdb")
  ```
  Queries are SQL against `ccdvisit1_quicklook` (`psf_sigma`, `psf_ixx/ixy/iyy`, Zernikes `z4..`, etc.).
  Results are cached to CSV (`notebooks/consdb_<start>_<end>.csv`) so the notebooks can be re-run
  offline — prefer reading the existing CSV over re-querying when the date range matches.
- **Butler / TAP** — used in the image-quality notebooks for image/catalog products.

Image-quality work uses seeing corrections from `lsst.summit.utils`
(`getAirmassSeeingCorrection`, `getBandpassSeeingCorrection`) and plotting helpers from
`lsst.utils.plotting` (`publication_plots`, `get_multiband_plot_colors`). `CAM_FWHM = 0.207` arcsec
is the assumed camera-contribution FWHM.

Plot outputs are written to a `plots/` folder next to the notebook and named with the `dayObs`/visit
they cover (e.g. `max_slew_velocity_<dayObs>.png`, `plots/<visit_id>.png`).
