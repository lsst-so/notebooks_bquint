# DIMM data quality

Ticket: [RSO-656](https://rubinobs.atlassian.net/browse/RSO-656)

Checks whether DIMM seeing is biased under low flux or low wind, and cross-checks it
against the ConsDB donut-blur FWHM.

- `FINDINGS.md` — results so far. `HANDOFF.md` — context and progress log.
- `notebooks/RSO-656 DIMM telemetry exploration.ipynb` — EFD DIMM telemetry vs. flux/wind.
- `notebooks/RSO-656 DIMM vs ConsDB donut-blur cross-check.ipynb` — reads
  `data/consdb_<start>_<end>.csv` (gitignored; same export as `image_quality_trending/data/`).
- `plots/` — figures named by `dayObs` range.
