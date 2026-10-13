# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Running scripts

Scripts require three things set up before invocation:

```zsh
source ~/.zapi   # sets ZEPHYR_API_TOKEN, JIRA_API_TOKEN, JIRA_USERNAME

PYTHONPATH="/Users/bquint/GitHub/lsst-ts/ts_planning_tool/python" \
  /Users/bquint/miniforge3/envs/lsst-scipipe-12.1.0/bin/python python/<script>.py
```

The `lsst-scipipe-12.1.0` conda env is required because system Python lacks `aiohttp`. `PYTHONPATH` must point to the `ts_planning_tool` package (not pip-installed here).

## Architecture

All scripts are standalone async Python programs. The common pattern:

1. **Cache phase** — `cache_*.py` scripts hit the Zephyr/Jira API and write raw JSON to `data/`. Run these first; subsequent analysis scripts read from cache and work offline.
2. **Count/analysis phase** — `count_*.py` and `stats_*.py` scripts read cached data, hit the API for per-item detail (with concurrency 8, retries, and incremental saves every 20 items), and write results back to `data/`. These are **resume-safe**: re-run them if they time out — they skip already-processed items.
3. **Plot phase** — `plot_*.py` reads `data/` and writes `.png`/`.pdf`/`.svg` outputs to `plots/`. Fully offline.

### API interface

`ZephyrInterface` (from `ts_planning_tool`) wraps:
- Zephyr Scale: `https://api.zephyrscale.smartbear.com/v2/` — Bearer token auth
- Jira: `https://rubinobs.atlassian.net/rest/api/2/` — BasicAuth (`{JIRA_USERNAME}@lsst.org`, `JIRA_API_TOKEN`)

Generic escape hatch: `await z.get(endpoint, params)` hits any Zephyr endpoint. Jira calls go through the Jira client.

### Pagination

All Zephyr list endpoints follow the same pattern (`maxResults=100`, `startAt` advancing by 100, stop when `isLast=True` or empty `values`). See `python/cache_test_cycles.py:34-46` for the canonical helper.

### Project structure

- **Project key:** `BLOCK` (Jira project for commissioning test work)
- **"Commissioning Plans" folder** (TEST_CYCLE): `id = 16248621`
- **526 test cycles** keyed `BLOCK-R##`; cycle names embed a date (`"2024-08-26 Commissioning Plan"`)
- **680 unique test cases** keyed `BLOCK-T##`

Key relationship: a test case belongs to a cycle **through a test execution**. To count cases per cycle, query `testexecutions?testCycle=<key>&onlyLastExecutions=True` and count unique `testCase.self` entries.

`Not Executed` status id is `6360081` — these are cloned placeholders, excluded from "executed" counts.

### Commissioning eras

Used for plot annotations (date ranges are user-confirmed):

| Era | Range |
|-----|-------|
| ComCam Commissioning on Sky | 2024-10-24 → 2024-12-15 |
| AuxTel only (ComCam→LSSTCam swap) | 2024-12-15 → 2025-04-15 |
| LSSTCam Commissioning on Sky | 2025-04-15 → 2025-09-22 |
| Planned maintenance downtime | 2025-09-22 → 2025-10-26 |
| Early Operations | 2025-10-26 → present |

### Rubin brand colors

Defined in `python/plot_timeline_weekly.py:40-53` as the `RUBIN` dict. Use these (not ugrizy filter colors) for Rubin-branded figures. The six accent colors (red, green, orange, yellow, blue, purple) are the approved data-visualization palette.
