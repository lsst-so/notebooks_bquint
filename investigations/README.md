# Investigations — reference notes

Working notes for ad-hoc analyses against Zephyr Scale / Jira via the
`ts_planning_tool` package. Captures the setup and findings so investigations
don't have to be re-derived.

---

## 1. Environment setup

The package is **not** pip-installed and the active `python` lacks `aiohttp`.
The simplest working combo:

- **Interpreter:** the `lsst-scipipe-12.1.0` conda env already has `aiohttp`,
  `pandas`, `matplotlib` (and `pypdf`, installed for reading the brand manual).
  ```
  /Users/bquint/miniforge3/envs/lsst-scipipe-12.1.0/bin/python
  ```
- **Imports:** point `PYTHONPATH` at the repo's `python/` dir.
- **Credentials:** the three required env vars live in `~/.zapi` (sourced from
  `~/.zshrc`). Source it before running.

Canonical invocation from inside `investigations/`:

```zsh
source ~/.zapi
PYTHONPATH="$PWD/../python" \
  /Users/bquint/miniforge3/envs/lsst-scipipe-12.1.0/bin/python <script>.py
```

Required env vars (see repo top-level `README.md`):
`ZEPHYR_API_TOKEN`, `JIRA_API_TOKEN`, `JIRA_USERNAME`.

---

## 2. How the Zephyr/Jira API works (ZAPI)

Code lives in [`../python/lsst/ts/planning/tool/zephyr_interface.py`](../python/lsst/ts/planning/tool/zephyr_interface.py).

- **Base URLs**
  - Zephyr Scale: `https://api.zephyrscale.smartbear.com/v2/`
  - Jira: `https://rubinobs.atlassian.net/rest/api/2/`
- **Auth**
  - Zephyr: `Authorization: Bearer <ZEPHYR_API_TOKEN>`
  - Jira: HTTP Basic — `BasicAuth(f"{JIRA_USERNAME}@lsst.org", JIRA_API_TOKEN)`
- **Generic getter:** `ZephyrInterface.get(endpoint, params)` hits any Zephyr
  endpoint and returns parsed JSON. This is the escape hatch for endpoints the
  class doesn't wrap (e.g. `folders`).
- **Project key:** `BLOCK` (the Jira project holding commissioning test work).

### Pagination pattern

Zephyr list endpoints return `{"values": [...], "isLast": bool, ...}` and take
`maxResults` (use 100) + `startAt` (multiple of `maxResults`). Loop:

```python
out, start = [], 0
while True:
    resp = await z.get(endpoint, dict(params, maxResults=100, startAt=start))
    vals = resp.get("values", [])
    out.extend(vals)
    if resp.get("isLast", True) or not vals:
        break
    start += 100
```

### Useful endpoints

| Endpoint            | Purpose                                   | Key params |
|---------------------|-------------------------------------------|------------|
| `folders`           | List folders                              | `projectKey`, `folderType` (`TEST_CYCLE`/`TEST_CASE`/`TEST_PLAN`) |
| `testcycles`        | List/filter test cycles                   | `projectKey`, `folderId` (folder filter is **not** recursive) |
| `testexecutions`    | Executions in a cycle or case             | `testCycle=BLOCK-R##` or `testCase=BLOCK-T##`, `onlyLastExecutions` |
| `testcases/{key}`   | Single test case                          | — |
| `testcycles/{key}`  | Single test cycle                         | — |

### Key relationship: test cases per cycle

A test cycle contains test cases **through test executions** (adding a case to a
cycle creates an execution). To count **test cases in a cycle**, query
`testexecutions?testCycle=<key>&onlyLastExecutions=True` and count **unique
`testCase`** entries (use `testCase.self` as the dedup key — it encodes
key+version). `onlyLastExecutions=True` returns one execution per case, so the
count equals the number of test cases.

### CLI

A `zapi` CLI exists ([`../python/lsst/ts/planning/tool/cli.py`](../python/lsst/ts/planning/tool/cli.py)) but only
supports `get {test_case,test_cycle,test_execution,steps,user}` and
`list test_executions`. It has **no folder support and no count command**, so
folder-level analyses use `ZephyrInterface.get()` directly (as the scripts here
do). The CLI is only on PATH if the package is `pip install`-ed.

---

## 3. Known facts / IDs

- **"Commissioning Plans" folder** (TEST_CYCLE): `id = 16248621`, top-level
  (`parentId = None`), flat (no subfolders).
- It holds **526 test cycles** (project `BLOCK`), keyed `BLOCK-R##`.
- Cycle names embed a date, e.g. `"2024-08-26 Commissioning Plan"`.
- Total test cases across all 526 cycles: **13,886** (min 0, median 28,
  mean ~26.4, max 56). One cycle has 0 cases; `BLOCK-R224` has no date in its
  name. This counts case↔cycle memberships (one execution per case per cycle,
  `onlyLastExecutions=True`), so it is a **lower bound** on raw executions.
- **Total test executions** (raw, all re-runs included): **15,768**. Read
  directly from the `total` field of `testexecutions?projectKey=BLOCK` (no need
  to page through — the first response carries the count). Higher than the
  13,886 above because a case can be executed more than once within a cycle.
- **Executions actually run** (excluding the `Not Executed` status, id
  `6360081` — mostly placeholders carried over when a Test Cycle is cloned):
  **12,830** (81.4% of 15,768). Breakdown by `testExecutionStatus` (page through
  all 15,768 and tally; `TEST_EXECUTION` statuses come from
  `statuses?statusType=TEST_EXECUTION`):
  | Status | Count |
  |--------|------:|
  | Pass | 7,372 |
  | Not Executed | 2,938 |
  | Skip | 2,310 |
  | Pass with Deviation | 889 |
  | Fail | 797 |
  | Blocked | 745 |
  | In Progress | 717 |
  All counts here are a mid-2026 snapshot and keep growing with operations.
- **Unique test cases** in project `BLOCK` (the `testcases?projectKey=BLOCK`
  list endpoint): **680**, keyed `BLOCK-T##`. (The 13,886 above counts
  case↔cycle memberships, so cases shared across cycles are counted repeatedly.)
- **Versions per test case** (count of `values` from `testcases/{key}/versions`):
  **961 total** over 680 cases — min 1, median 1, mean ~1.4, max **19**
  (`BLOCK-T227`). **81.6%** exist in a single version; **18.4%** have >1 version;
  only 15 cases (2.2%) have >5 versions; **0 cases exceed 20 versions**. The
  list-endpoint payload has no version field, so versions must be fetched
  per-case from this endpoint.
- **Steps per test case** (raw count from `testcases/{key}/teststeps`, "call to
  test" steps counted as one, not expanded): **4,028 total** over 680 cases —
  min 1, median 4, mean ~5.9, max 85. Right-skewed, peak at ~4 steps.
- **Web UI base URL** for a test case (append the `BLOCK-T##` key):
  `https://rubinobs.atlassian.net/projects/BLOCK?selectedItem=com.atlassian.plugins.atlassian-connect-plugin:com.kanoah.test-manager__main-project-page#!/v2/testCase/`
- **Test cases with > 30 steps** (10 of 680), the right tail of the histogram:
  | Test case | Steps | Name |
  |-----------|------:|------|
  | [BLOCK-T270](https://rubinobs.atlassian.net/projects/BLOCK?selectedItem=com.atlassian.plugins.atlassian-connect-plugin:com.kanoah.test-manager__main-project-page#!/v2/testCase/BLOCK-T270) | 85 | AOS Closed-Loop M2 Sign Verification |
  | [BLOCK-T273](https://rubinobs.atlassian.net/projects/BLOCK?selectedItem=com.atlassian.plugins.atlassian-connect-plugin:com.kanoah.test-manager__main-project-page#!/v2/testCase/BLOCK-T273) | 85 | AOS Closed-Loop M1M3 Sign Verification |
  | [BLOCK-T252](https://rubinobs.atlassian.net/projects/BLOCK?selectedItem=com.atlassian.plugins.atlassian-connect-plugin:com.kanoah.test-manager__main-project-page#!/v2/testCase/BLOCK-T252) | 49 | WET-001 Optical State M1M3 Bending Modes one by one |
  | [BLOCK-T253](https://rubinobs.atlassian.net/projects/BLOCK?selectedItem=com.atlassian.plugins.atlassian-connect-plugin:com.kanoah.test-manager__main-project-page#!/v2/testCase/BLOCK-T253) | 49 | WET-001 Optical State M2 Bending Modes one by one |
  | [BLOCK-T640](https://rubinobs.atlassian.net/projects/BLOCK?selectedItem=com.atlassian.plugins.atlassian-connect-plugin:com.kanoah.test-manager__main-project-page#!/v2/testCase/BLOCK-T640) | 43 | Kick the robot |
  | [BLOCK-T344](https://rubinobs.atlassian.net/projects/BLOCK?selectedItem=com.atlassian.plugins.atlassian-connect-plugin:com.kanoah.test-manager__main-project-page#!/v2/testCase/BLOCK-T344) | 41 | Normalization weights investigation |
  | [BLOCK-T549](https://rubinobs.atlassian.net/projects/BLOCK?selectedItem=com.atlassian.plugins.atlassian-connect-plugin:com.kanoah.test-manager__main-project-page#!/v2/testCase/BLOCK-T549) | 34 | Shutter timing linearity study (Rotator=-80) |
  | [BLOCK-T550](https://rubinobs.atlassian.net/projects/BLOCK?selectedItem=com.atlassian.plugins.atlassian-connect-plugin:com.kanoah.test-manager__main-project-page#!/v2/testCase/BLOCK-T550) | 34 | Shutter timing linearity study (Rotator=80) |
  | [BLOCK-T612](https://rubinobs.atlassian.net/projects/BLOCK?selectedItem=com.atlassian.plugins.atlassian-connect-plugin:com.kanoah.test-manager__main-project-page#!/v2/testCase/BLOCK-T612) | 32 | LSSTCam stray light from filter holder shiny plate using CBP |
  | [BLOCK-T548](https://rubinobs.atlassian.net/projects/BLOCK?selectedItem=com.atlassian.plugins.atlassian-connect-plugin:com.kanoah.test-manager__main-project-page#!/v2/testCase/BLOCK-T548) | 31 | Shutter timing linearity study (Rotator=0) |
- **Test cases per campaign** (era), over each era's test cycles
  (mean / max cases *per cycle*, and campaign total):
  | Campaign | #cycles | mean | max | total |
  |----------|--------:|-----:|----:|------:|
  | ComCam Commissioning on Sky | 65 | 31.6 | 56 | 2055 |
  | AuxTel only (ComCam→LSSTCam swap) | 48 | 4.5 | 6 | 218 |
  | LSSTCam Commissioning on Sky | 164 | 31.8 | 54 | 5210 |
  | Early Operations | 228 | 26.8 | 42 | 6112 |
  | Pre-commissioning / other | 20 | 12.7 | 24 | 253 |
- Commissioning-era date ranges used for plot annotations:
  | Era | Range |
  |-----|-------|
  | ComCam Commissioning on Sky | 2024-10-01 → 2024-12-31 |
  | AuxTel only (ComCam→LSSTCam swap) | 2024-12-31 → 2025-04-01 |
  | LSSTCam Commissioning on Sky | 2025-04-01 → 2025-09-22 |
  | Planned maintenance downtime | 2025-09-22 → 2025-10-17 |
  | Early Operations | 2025-10-17 → present |

---

## 4. Rubin Observatory brand colors

From the **Visual Identity Manual V7** (`../20210212 Visual Identity Manual —V7
(1).pdf`), pages 27–30. These are the *brand* colors (use these for
Rubin-branded figures), **not** the ugrizy filter-plot colors.

| Name | HEX | RGB | Pantone | Notes |
|------|-----|-----|---------|-------|
| Primary teal | `#058B8C` | 5,139,140 | 2237 C | Main imagotype color |
| Bright teal | `#00BABC` | 0,186,188 | 2397 C | |
| Dark teal | `#0C4A47` | 12,74,71 | 3302 C | Complementary |
| Mid teal | `#009FA1` | 0,159,161 | 320 C | Complementary |
| Light teal | `#B1F2EF` | 177,242,239 | 317 C | |
| Pale teal | `#D9F7F6` | 217,247,246 | 9480 C | |
| Steel gray | `#313333` | 49,51,51 | 447 C | Observatory steel, RAL-5018 |
| Cool gray | `#6A6E6E` | 106,110,110 | Cool Gray 9 C | |
| Light gray | `#DCE0E3` | 220,224,227 | 7541 C | |
| Dark gray | `#1F2121` | 31,33,33 | 419 C | |
| **Accent** red | `#ED4C4C` | 237,76,76 | 2348 C | warm |
| **Accent** green | `#3CAE3F` | 60,174,63 | 7738 C | warm |
| **Accent** orange | `#FAB364` | 250,179,100 | 1485 C | warm |
| **Accent** yellow | `#FFE266` | 255,226,102 | 2003 C | warm |
| **Accent** blue | `#1C81A4` | 28,129,164 | 2454 C | cold |
| **Accent** purple | `#583671` | 88,54,113 | 7665 C | cold |

The manual designates the **six accent colors** (red, green, orange, yellow,
blue, purple) for data visualizations (p.38), tested for B/W and
protanopia/deuteranopia.

> Filter-plot alternative (NOT brand colors): the ugrizy palette from
> [RTN-045](https://rtn-045.lsst.io/) —
> `u #1600ea, g #31de1f, r #b52626, i #370201, z #ba52ff, y #61a2b3`.

---

## 5. Scripts & cached data

| File | What it does | Output |
|------|--------------|--------|
| `cache_test_cycles.py` | Finds the "Commissioning Plans" folder subtree and caches all raw test-cycle payloads | `cache/test_cycles.json`, `cache/folders.json` |
| `count_test_cases_per_cycle.py` | Counts unique test cases per cycle (concurrency 8, **incremental save + resume** — re-run until 0 remaining) | `cache/test_case_counts.json` |
| `plot_timeline_weekly.py` | Weekly-binned bar chart with era spans + downtime, Rubin brand colors | `test_cases_timeline_weekly.png` |
| `plot_timeline.py` | Earlier per-cycle scatter version | `test_cases_timeline.png` |
| `stats_test_cases_per_campaign.py` | Mean/median/max test cases per cycle, grouped by commissioning campaign (era) | stdout table |
| `cache_test_cases.py` | Lists all 680 test cases in project `BLOCK` and caches raw payloads | `cache/test_cases.json` |
| `count_steps_per_test_case.py` | Counts steps per test case via `testcases/{key}/teststeps` (**incremental save + resume**) | `cache/test_case_step_counts.json` |
| `plot_steps_histogram.py` | Histogram of steps per test case, Rubin brand colors | `steps_per_test_case_histogram.png` |
| `count_versions_per_test_case.py` | Counts versions per test case via `testcases/{key}/versions` (**incremental save + resume**) | `cache/test_case_version_counts.json` |

`cache/` holds the offline copies so re-runs and new analyses don't re-hit the
API. `count_test_cases_per_cycle.py` is resume-safe: it skips cycles already in
`test_case_counts.json`, so a timeout just means "run it again."

---

## 6. Handoff — current state (2026-06-05)

Three investigations are **complete**; all data is cached, so the plots/tables
regenerate offline (no API calls needed).

**Done**

- *Versions per test case* — counted versions for all **680** cases via
  `testcases/{key}/versions` (`cache/test_case_version_counts.json`, 680/680).
  Headline for the SPIE paper: max is **19** versions, **none exceeds 20**, and
  ~82% are single-version (stats in §3). Regenerate with
  `count_versions_per_test_case.py` (resume-safe).

- *Test cases per campaign* — grouped the 526 commissioning cycles by era and
  computed mean/median/max cases per cycle (table in §3). Source data:
  `cache/test_case_counts.json` (526 cycles, already populated). Regenerate the
  table with `stats_test_cases_per_campaign.py` (reads cache, instant).
- *Steps per test case* — enumerated all **680** test cases in project `BLOCK`
  (`cache/test_cases.json`) and counted steps for each
  (`cache/test_case_step_counts.json`, 680/680 done, 0 remaining). Histogram:
  `steps_per_test_case_histogram.png` (x capped at 30; 10 cases exceed it). The
  10 cases with > 30 steps are listed with web-UI links in §3.

**Caveats / assumptions to revisit**

- *Step count is raw*: a "call to test" step is counted as **one** step, not
  expanded into the called case's sub-steps. The interface supports recursive
  expansion (`get_steps_in_test_case(..., call_to_test=True)`); re-run with that
  if expanded counts are wanted.
- *Campaign "average/max"* is interpreted as **per cycle** within each era
  (consistent with `plot_timeline_weekly.py`), not a single per-campaign total.
  The per-campaign total is the rightmost column of the §3 table.
- Campaign bucketing uses the date in each cycle's **name**; `BLOCK-R224` has no
  date and is excluded (1 cycle). Cycles before 2024-10-01 fall in
  "Pre-commissioning / other".

**To resume / extend**

- Refresh data: re-run `cache_test_cases.py` then `count_steps_per_test_case.py`
  (resume-safe — delete the relevant `cache/*.json` to force a full refetch).
- Env: `source ~/.zapi` + the `lsst-scipipe-12.1.0` python + `PYTHONPATH` to
  `../python` (see §1).
