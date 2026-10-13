#!/usr/bin/env python
"""Count the number of test cases in each test cycle of the cached
"Commissioning Plans" folder.

A test cycle in Zephyr Scale contains test cases through test executions
(one execution links one test case). With ``onlyLastExecutions=True`` the
testexecutions endpoint returns the last execution per test case, so the
number of unique test cases == the count we want.

Resilient to timeouts: results are written incrementally to
``cache/test_case_counts.json`` and the script resumes, skipping cycles that
are already counted. Just re-run it until it reports 0 remaining.

Usage:
    source ~/.zapi
    PYTHONPATH=../python python count_test_cases_per_cycle.py
"""
import asyncio
import json
import os
from pathlib import Path

from lsst.ts.planning.tool.zephyr_interface import ZephyrInterface

CACHE_DIR = Path(__file__).parent / "cache"
CYCLES_FILE = CACHE_DIR / "test_cycles.json"
COUNTS_FILE = CACHE_DIR / "test_case_counts.json"
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


async def count_cycle(z, cycle_key):
    """Return the number of unique test cases in a cycle."""
    unique, start = set(), 0
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
        unique.update(tc_key(e) for e in vals)
        if resp.get("isLast", True) or not vals:
            break
        start += PAGE
    return len(unique)


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
                    n = await count_cycle(z, cycle["key"])
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
                    "n_test_cases": n,
                }
                done += 1
                if done % SAVE_EVERY == 0:
                    COUNTS_FILE.write_text(json.dumps(results, indent=2))
                    print(f"  ... {done}/{len(todo)} done (saved)")

    await asyncio.gather(*(worker(c) for c in todo))
    COUNTS_FILE.write_text(json.dumps(results, indent=2))

    remaining = [c for c in cycles if c["key"] not in results]
    total_tc = sum(r["n_test_cases"] for r in results.values())
    print(f"\nProcessed cycles: {len(results)}/{len(cycles)}  "
          f"(remaining: {len(remaining)})")
    print(f"Total test cases across all cached cycles: {total_tc}")
    print(f"Saved -> {COUNTS_FILE}")


if __name__ == "__main__":
    asyncio.run(main())
