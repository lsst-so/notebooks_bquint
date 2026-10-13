# Session notes — night-failures trending notebook

_Last updated: 2026-05-22_

## What this is

Building a multi-month "trending" companion to the working MVP
`count_night_failures.ipynb`, which counts CSC faults & script failures for a
single night. New notebook: **`count_night_failures_trending.ipynb`** (repo root).

Runs in the LSST stack kernel (Nublado / USDF RSP) — `lsst_efd_client`, astropy,
pandas, numpy, bokeh, matplotlib. It cannot be executed in a plain local Python
(no astropy/numpy/nbformat there).

## State: built, NOT yet executed end-to-end in the stack

JSON validated (38 cells) and logic traced by hand. Still needs a real run in the
stack kernel to confirm.

### What the notebook does
- **Night windows**: one vectorized `get_sun` over the whole period, split into
  contiguous `sun <= -12 deg` runs at Cerro Pachon; run *k* = night of `START + k`.
- **Query strategy**: weekly sequential chunks (`CHUNK_DAYS=7`) over
  `[first night start, last night end]`. Logevents are sparse, so volume is small;
  weekly chunks bound per-query latency / timeout risk.
- **Signal 1 — CSC faults**: transitions into `summaryState == 3`, consecutive-dup
  dedup done on the *concatenated* per-CSC series (chunk-boundary safe).
- **Script failures**: `Script.logevent_state` states 10/11, deduped per night.
- **Correlation**: script failure within `[-35s, +5s]` of a CSC fault is attributed
  to the fault; `unique_total = csc_faults + standalone_script_failures`.
- **Signal 2 — errorCode** (added this session, aligned with the official
  `lsst/schedview_notebooks/nightly/ErrCounts.ipynb`): all `*.logevent_errorCode`
  topics via `client.get_topics()`, non-zero codes counted as *events* (not
  transitions), grouped by subsystem (EnvSys/CalSys/Simonyi/AuxTel/Other). It is a
  **parallel** signal and is deliberately **NOT** in `unique_total` (a FAULT usually
  also emits an errorCode -> would double-count).
- **Plots (Bokeh)**: stacked bar of faults + standalone script failures with
  7-night mean; top-8 CSC offenders; errorCode events by subsystem. Plus a
  matplotlib publication bar.
- **Anomaly table**: nights exceeding the trailing `ANOMALY_WINDOW`-night mean
  (night excluded via `closed='left'`) by more than `ANOMALY_THRESHOLD`.

### Decisions made this session
- Query strategy: weekly chunks, sequential.
- Binning: night-window only (sun <= -12 deg). **Not** adopted: standard Rubin
  `day_obs = floor(MJD-0.5)` (would make plots joinable to consdb/butler/dashboards
  — left as a possible future toggle).
- Code: self-contained notebook (no shared module).
- errorCode signal: added. **Not** adopted: `rubin_nights.connections` (avoided the
  extra dependency).

## Verify on first real run
1. `client.get_topics()` exists on the deployed `EfdClient` and returns
   `lsst.sal.*` strings (code degrades to empty errorCode if not).
2. Printed `n_topics x n_chunks` query count — ~2000+ for a few months across all
   errorCode topics. If too slow, set `ERRORCODE_SUBSYSTEMS = {'Simonyi'}`.
3. `errorCode` is the literal field name for the topics of interest.
4. `Script.logevent_state.ScriptID` — MVP saw `None`; if unusable here the code
   keeps every terminal-state row (could inflate standalone-script counts).
5. `build_nights` prints a WARNING if night-segment count != date count.
6. Sanity check: run a short 3-night `START`/`END` and compare to the MVP first.

## Open items / next steps
- **MTDome subsystem decomposition** (still a stub): CSC-level MTDome errors are now
  caught by the errorCode signal, but mapping errorCode *values* to subsystems
  (AMCS, LWSCS, ApSCS, ThCS, MonCS, RAD) needs the errorCode->subsystem map from the
  MTDome SAL XML (unverified). `get_dome_subsystem_faults()` remains a stub for that.
- Optional: add a `day_obs` binning toggle for cross-dataset comparability.
- Optional: bounded-concurrency query dispatch (asyncio.gather + semaphore) if the
  sequential errorCode sweep is too slow.

## Files
- `count_night_failures.ipynb` — MVP (single night), working.
- `count_night_failures_trending.ipynb` — this work (multi-month).
- Reference: `lsst/schedview_notebooks/nightly/ErrCounts.ipynb` (official nightly
  error counts; uses `rubin_nights`, errorCode, `day_obs` binning).
