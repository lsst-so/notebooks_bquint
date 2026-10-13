#!/usr/bin/env python
"""Count test cases per test cycle, split into all vs. *executed* test cases.

Like ``count_test_cases_per_cycle.py``, but for each cycle it also counts how
many of the unique test cases were actually executed -- i.e. whose last
execution is NOT in the ``Not Executed`` status (id 6360081). The ``Not
Executed`` entries are mostly placeholders carried over when a Test Cycle is
cloned from a template, so excluding them gives the "tests genuinely run that
night" count used in the paper.

With ``onlyLastExecutions=True`` the endpoint returns one execution per test
case (its latest), so we use that execution's status as the case's state.

Resilient to timeouts: results are written incrementally to
``cache/test_case_counts_executed.json`` and the script resumes, skipping cycles
already counted. Re-run until it reports 0 remaining.

Usage:
    source ~/.zapi
    PYTHONPATH=/Users/bquint/GitHub/lsst-ts/ts_planning_tool/python \
        python count_executed_test_cases_per_cycle.py
"""
import asyncio
import json
import os
from collections import Counter
from pathlib import Path

from lsst.ts.planning.tool.zephyr_interface import ZephyrInterface

CACHE_DIR = Path(__file__).parent / "cache"
CYCLES_FILE = CACHE_DIR / "test_cycles.json"
COUNTS_FILE = CACHE_DIR / "test_case_counts_executed.json"
NOT_EXECUTED_ID = 6360081
PAGE = 100
CONCURRENCY = 8
RETRIES = 3
SAVE_EVERY = 20


def make_interface():
    return ZephyrInterface(
        zephyr_api_token=os.environ["ZEPHYR_API_TOKEN"],
        jira_api_token=os.environ["JIRA_API_TOKEN"],
        jira_username=os.environ["JIRA_USERNAME"],
    )


def tc_key(execution):
    tc = execution.get("testCase") or {}
    return tc.get("self") or tc.get("key") or tc.get("id")


def status_id(execution):
    st = execution.get("testExecutionStatus") or {}
    return st.get("id")


async def count_cycle(z, cycle_key):
    """Return (n_unique_cases, n_executed_cases) for a cycle.

    Uses the last execution per case; a case counts as executed if its last
    execution status is not ``Not Executed``.
    """
    last_status = {}  # tc_key -> status id (last execution)
    start = 0
    while True:
        resp = await z.get(
            "testexecutions",
            {
                "testCycle": cycle_key,
                "maxResults": PAGE,
                "startAt": start,
                "onlyLastExecutions": "True",
            },
        )
        vals = resp.get("values", [])
        for e in vals:
            last_status[tc_key(e)] = status_id(e)
        if resp.get("isLast", True) or not vals:
            break
        start += PAGE
    n_total = len(last_status)
    n_exec = sum(1 for sid in last_status.values() if sid != NOT_EXECUTED_ID)
    return n_total, n_exec


async def main():
    cycles = json.loads(CYCLES_FILE.read_text())
    results = {}
    if COUNTS_FILE.exists():
        results = json.loads(COUNTS_FILE.read_text())
    todo = [c for c in cycles if c["key"] not in results]
    print(f"{len(cycles)} cycles total, {len(results)} already done, "
          f"{len(todo)} to process")

    z = make_interface()
    sem = asyncio.Semaphore(CONCURRENCY)
    done = 0
    lock = asyncio.Lock()

    async def worker(cycle):
        nonlocal done
        async with sem:
            for attempt in range(1, RETRIES + 1):
                try:
                    n_total, n_exec = await count_cycle(z, cycle["key"])
                    break
                except Exception as exc:  # transient network / rate limit
                    if attempt == RETRIES:
                        print(f"  !! {cycle['key']} failed: {exc}")
                        return
                    await asyncio.sleep(2 * attempt)
            async with lock:
                results[cycle["key"]] = {
                    "key": cycle["key"],
                    "name": cycle.get("name"),
                    "n_test_cases": n_total,
                    "n_executed": n_exec,
                }
                done += 1
                if done % SAVE_EVERY == 0:
                    COUNTS_FILE.write_text(json.dumps(results, indent=2))
                    print(f"  ... {done}/{len(todo)} done (saved)")

    await asyncio.gather(*(worker(c) for c in todo))
    COUNTS_FILE.write_text(json.dumps(results, indent=2))

    remaining = [c for c in cycles if c["key"] not in results]
    total_tc = sum(r["n_test_cases"] for r in results.values())
    total_exec = sum(r["n_executed"] for r in results.values())
    print(f"\nProcessed cycles: {len(results)}/{len(cycles)}  "
          f"(remaining: {len(remaining)})")
    print(f"Total test cases (all):      {total_tc}")
    print(f"Total test cases (executed): {total_exec}")
    print(f"Saved -> {COUNTS_FILE}")


if __name__ == "__main__":
    asyncio.run(main())
