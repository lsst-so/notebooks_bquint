# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

`notebooks_bquint` (GitHub: `lsst-so/notebooks_bquint`) is Bruno Quint's personal collection of
Rubin Observatory / LSST commissioning engineering-analysis notebooks and scripts. Unlike the parent
`notebooks/` working directory (which is *not* a repo), this **is** its own git repository. There is
no package, no test suite, and no build — the deliverables are the notebooks, scripts and plots. The
one reusable module is `rubin_color_pallete/rubin_palette.py`: the Rubin-teal-primary,
colour-blind-checked plotting palette (`CATEGORICAL` / `CATEGORICAL_DARK`, six slots in fixed order,
`teal_cmap()`, `use()` to set the matplotlib cycle; see its README). Use it for new presentation
plots instead of ad-hoc hex values. A broader description of the RSP/SLAC SDF environment lives in
the parent `../../CLAUDE.md`; this file only adds what is specific to this repo.

## Layout: one self-contained folder per investigation

Each investigation lives in its own top-level folder (index in `README.md`) so it can later be
extracted into a standalone technote repo with `git filter-repo --subdirectory-filter <folder>`:

```
<investigation>/
├── README.md     # what it is, Jira ticket, status, contents
├── notebooks/    # Jupyter notebooks
├── python/       # standalone scripts / modules
├── data/         # cached query results (large files gitignored)
├── plots/        # figures
└── notes/        # session notes, handoffs (optional)
```

Rules:
- Only create the subfolders an investigation actually needs.
- **No imports or relative paths across investigation folders** — that breaks extraction. Copy small
  helpers rather than sharing them.
- Notebooks run from `notebooks/`, so they read `../data/` and write `../plots/`. Scripts in
  `python/` resolve paths from `Path(__file__).parent.parent`.
- Folders are named by topic (`dimm_data_quality`); the Jira ticket goes in the folder README and
  in notebook filenames (`RSO-656 DIMM telemetry exploration.ipynb`).

## Environment & tooling

- Runs on the LSST Science Pipelines / `ts_*` stack provided by **EUPS**, not pip. `lsst.*` and
  `lsst_efd_client` are already on the kernel `PYTHONPATH`; do not add pip installs for them.
- A machine-specific `.env` (`PATH`/`PYTHONPATH`/`LD_LIBRARY_PATH` plus every `*_DIR` with a
  matching `SETUP_*` var) lets VS Code's Python extension resolve the stack. It is generated from a
  set-up kernel shell — regenerate, never hand-edit.
- Lint/format with **ruff** (`ruff check <file>` / `ruff format <file>`).
- Notebooks commonly open with `%load_ext autoreload` / `%autoreload 2` and `%load_ext lab_black`
  (Black-on-save for cells). `%matplotlib widget` is used for interactive plots.
- `.gitignore` excludes `**/.ipynb_checkpoints`, `consdb_*.csv` (ConsDB exports exceed GitHub's
  100 MB file limit) and local `.claude/` / `.vscode/` settings — be deliberate about what you add.
- The Zephyr Scale scripts (`zephyr_scale_analysis/`) run outside the stack, against a local conda
  env and `ts_planning_tool`; see that folder's `CLAUDE.md`.

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
  Results are cached to CSV (`<investigation>/data/consdb_<start>_<end>.csv`) so the notebooks can be re-run
  offline — prefer reading the existing CSV over re-querying when the date range matches.
- **Butler / TAP** — used in the image-quality notebooks for image/catalog products.

Image-quality work uses seeing corrections from `lsst.summit.utils`
(`getAirmassSeeingCorrection`, `getBandpassSeeingCorrection`) and plotting helpers from
`lsst.utils.plotting` (`publication_plots`, `get_multiband_plot_colors`). `CAM_FWHM = 0.207` arcsec
is the assumed camera-contribution FWHM.

Plot outputs are written to the investigation's `plots/` folder and named with the `dayObs`/visit
they cover (e.g. `max_slew_velocity_<dayObs>.png`, `plots/<visit_id>.png`).

## Reference documentation

- EFD schema: https://ts-xml.lsst.io/ — commands map to `lsst.sal.<CSC>.command_<name>`, events to
  `lsst.sal.<CSC>.logevent_<name>`, telemetry to `lsst.sal.<CSC>.<telemetry name>`.
- ConsDB schema for LSSTCam: https://sdm-schemas.lsst.io/cdb_lsstcam.html
- LSST Science Pipelines / Butler: https://pipelines.lsst.io/index.html
