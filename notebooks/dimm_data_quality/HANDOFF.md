# RSO-656 — DIMM Data Quality: Handoff Notes

> Working scratchpad for the investigation. Keeps state between sessions so anyone
> (human or Claude) can pick this up. Living findings/conclusions go in
> [`FINDINGS.md`](./FINDINGS.md); this file is the "where we are / what's next" log.

- **Ticket:** [RSO-656](https://rubinobs.atlassian.net/browse/RSO-656)
- **Branch:** `tickets/RSO-656`
- **Started:** 2026-07-01

## The question

Craig flagged (in a thread) that **DIMM seeing measurements might not be real**.

- Known: DIMM data is unreliable for **wind < 4 m/s**.
- Hypothesis (Erik D., Image Quality mtg 2026-06-17): DIMMs also misbehave under
  **clouds** — light flux drops significantly and the DIMM reports **artificially low
  seeing** values.
- **Task:** confirm this in *our* DIMM, find what other variables corrupt the DIMM
  seeing, and determine the **thresholds** below/above which DIMM data should be
  treated as unreliable. Report back to Craig.

## Goal / definition of done

1. Identify factors (flux, wind, clouds, airmass, etc.) that bias DIMM seeing.
2. Quantify thresholds for "unreliable DIMM".
3. Compare DIMM seeing against a trusted reference — **`donut_blur_fwhm`** (ConsDB,
   `visit1_quicklook`) is the comparison metric of record.
4. Summarize for Craig in `FINDINGS.md`.

> Open modeling question: which column holds the *real* atmospheric FWHM? DIMM is
> supposed to measure atmosphere-only seeing but is being contaminated. `donut_blur_fwhm`
> includes a camera contribution (`CAM_FWHM = 0.207"`) that must be removed before
> comparison: `donut_blur_atm_fwhm = sqrt(donut_blur_fwhm**2 - CAM_FWHM**2)`.

## Data sources

### DIMM telemetry — EFD (CSC: `DIMM`)
Reference: <https://ts-xml.lsst.io/sal_interfaces/DIMM.html>. Full topic/field catalog
in `FINDINGS.md`. The key event is **`lsst.sal.DIMM.logevent_dimmMeasurement`**:

| field | meaning | why it matters here |
|---|---|---|
| `fwhm`, `fwhmx`, `fwhmy` | seeing FWHM, arcsec (combined + per-axis) | the DIMM value under scrutiny |
| `flux`, `fluxL`, `fluxR` | avg + per-spot flux, ADU | **cloud/transparency proxy** — the core hypothesis |
| `scintL`, `scintR` | scintillation ratio | seeing/turbulence sanity check |
| `strehlL`, `strehlR` | Strehl ratio | image quality of the spots |
| `secz` | airmass | seeing scales with airmass |
| `nimg` | # images averaged | low count → noisy estimate |
| `r0` | Fried parameter, cm | derived from seeing |

Supporting topics: `lsst.sal.DIMM.cloudSensor` (sky temp, light intensity, rain),
`lsst.sal.DIMM.sky` (clear/cloudy/rain enum + sky temp), `lsst.sal.DIMM.status`
(alt/az, motion state). **Wind** likely comes from a weather station CSC (e.g.
`ESS`/`WeatherStation`) rather than DIMM — TBD which topic.

### Reference metric — ConsDB (`donut_blur_fwhm`)
`visit1_quicklook.donut_blur_fwhm`, joined via `visit1` / `ccdvisit1`. Also available:
`dimm_seeing` (on `visit1`), `ringss_seeing`, `aos_fwhm`, `seeing_zenith_500nm_*`.
See query template in `FINDINGS.md` / the query notebook.

## Environment gotchas

- EFD: `from lsst.summit.utils.efdUtils import getEfdData, makeEfdClient` then
  `getEfdData(client, "lsst.sal.DIMM.logevent_dimmMeasurement", begin=..., end=...)`.
  Or async `EfdClient("usdf_efd").select_time_series(...)`.
- ConsDB needs `os.environ["no_proxy"] += ",.consdb"` before
  `ConsDbClient("http://consdb-pq.consdb:8080/consdb")`, else the in-cluster call is
  proxied and fails.
- Cache ConsDB pulls to `consdb_<start>_<end>.csv`; prefer re-reading over re-querying.
- Plots → `notebooks/dimm_data_quality/plots/`, named by `dayObs`.

## Progress log

- **2026-07-01** — Created branch `tickets/RSO-656`, folder `notebooks/dimm_data_quality/`,
  this handoff + `FINDINGS.md`. Cataloged DIMM SAL topics and collected EFD/ConsDB query
  patterns from `image_quality*` notebooks.
- **2026-07-01 (run 1)** — Ran the exploration notebook (`dayObs` 20260119–20260407, 28 775
  measurements). Key findings (see `FINDINGS.md` §4.1):
  - `makeEfdClient()` was failing; switched to `EfdClient("usdf_efd", output_mode="dataframe")`.
  - **Thin event:** `flux`=0, `nimg`=1, `scintL/R`=0, `r0`/`fwhmx`/`fwhmy`=−1 are all dead.
  - **`fluxL`/`fluxR` are live** → transparency proxy `flux_proxy = fluxL + fluxR`.
  - `DIMM.cloudSensor` / `DIMM.sky` **not in EFD schema** — no direct cloud stream.
  - `fwhm` up to ~42″; adopting `fwhm > 5″` as the "failed measurement" cut.
  - Wind found: `ESS.airFlow`, `"Weather tower airflow"` (`salIndex 301`).
  - Notebook edited: added field-inventory + `flux_proxy` cells, removed dead cloud/sky
    cells, repointed the scatter plot to `flux_proxy` (log-x) with suspect-fwhm highlighting.

- **2026-07-01 (run 2)** — Confirmed `flux_proxy` varies over a wide range → cloud test viable.
  Added §5 to the notebook: `merge_asof` wind→DIMM alignment (2-min tol), a `bin_seeing`
  helper (median, robust σ = IQR/1.349, suspect_frac), flux- and wind-binned tables (wind edge
  at 4 m/s), and a 2×2 summary figure (`dimm_seeing_vs_flux_wind_<range>.png`). Awaiting run.

- **2026-07-01 (run 3)** — Ran §5. **Cloud hypothesis confirmed** (`FINDINGS.md` §4.2): median
  seeing collapses 0.91″→0.16″ as `flux_proxy` drops below ~12k ADU — DIMM reads *artificially
  low* under low flux, exactly Erik's claim. Wind<4 m/s re-confirmed but milder (σ 0.17→0.28″,
  median biased *high* — opposite sign, so distinguishable). Thresholds recorded in §5.

- **2026-07-01 (run 4)** — Scaffolded `RSO-656 DIMM vs ConsDB donut-blur cross-check.ipynb`
  (16 cells, not yet run). Reads the existing `../consdb_20260119_20260407.csv` cache (has
  `donut_blur_atm_fwhm` + `exp_midpt_mjd`; falls back to a ConsDB query if absent), reduces to
  one row/visit, re-pulls DIMM + `flux_proxy`, `merge_asof` time-joins visit→nearest DIMM (5-min
  tol), then plots DIMM vs `donut_blur_atm_fwhm` split at `FLUX_THRESHOLD = 12000` ADU + residual
  vs flux, with a by-regime residual table. Query mirrors `image_quality_minimal.ipynb`.

- **2026-07-01 (run 4b)** — Added airmass + wavelength corrections to the cross-check (Bruno
  flagged they were missing). Donut blur now normalised to **zenith/500 nm** via
  `getAirmassSeeingCorrection(airmass) × getBandpassSeeingCorrection(physical_filter)` →
  `donut_blur_zen500` (visits span airmass 1.0–5.9 + multiple bands, so this was a real bias).
  DIMM airmass convention is unknown, so we carry **both** `dimm_fwhm` (raw) and `dimm_fwhm_zen`
  (`× getAirmassSeeingCorrection(secz)`) and show the residual both ways. Also kept ConsDB's
  `seeing_zenith_500nm_median` as a cross-check on the manual correction. Still not run.

- **2026-07-01 (run 5)** — Ran the cross-check. **Inconclusive by selection effect**
  (`FINDINGS.md` §4.4): of 5482 visit↔DIMM pairs only 40 fall below 12k ADU and the paired flux
  bottoms out at ~7k ADU — the join never reaches the <6k regime where §4.2's collapse happens,
  because science visits aren't taken during heavy cloud. In the sampled mild-low-flux edge, DIMM
  and donut blur drop *together* (residual small & positive, both conventions) → genuinely good
  seeing, not corruption. Neither confirms nor refutes §4.2. Also: ConsDB
  `seeing_zenith_500nm_median` is all-NaN in the cache (manual correction not independently
  validated); ConsDB `dimm_seeing` maxes at ~39.9″ (corruption propagates downstream).
  **Decision (Bruno): record as inconclusive, lean on telemetry.** Wrote `FINDINGS.md` §4.4 + §6.

## Status: DONE — ready for Craig review

Conclusions + recommended filter are in `FINDINGS.md` §6:
`0.1″ ≤ fwhm ≤ 5″  AND  (fluxL+fluxR) ≥ 12 000 ADU  AND  wind ≥ 4 m/s`.

### Optional follow-ups (not blocking)

- [ ] Single cloudy-night time series (`fwhm`, `flux_proxy`, `wind` vs time) — nice illustrative
      figure for Craig, though the aggregate §4.2 result already carries the case.
- [ ] Tighten §4.2: split `suspect_frac` into NaN-failures vs >5″ so the low-flux bins are clean.
- [ ] Resolve the DIMM `fwhm` airmass convention (zenith vs line-of-sight) with the DIMM team to
      remove the last modelling ambiguity.
