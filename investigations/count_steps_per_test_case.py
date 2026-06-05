#!/usr/bin/env python
"""Count the number of steps in each test case of project BLOCK.

For every test case (from cache/test_cases.json) this queries
``testcases/{key}/teststeps`` and counts the steps. Steps are counted as the
raw number of step entries returned by the endpoint (a "call to test" step is
counted as one step; it is NOT expanded into the called case's steps).

Resilient to timeouts: results are written incrementally to
``cache/test_case_step_counts.json`` and the script resumes, skipping cases
already counted. Just re-run it until it reports 0 remaining.

Usage:
    source ~/.zapi
    PYTHONPATH=../python python count_steps_per_test_case.py
"""
import asyncio
import json
import os
from pathlib import Path

from lsst.ts.planning.tool.zephyr_interface import ZephyrInterface

CACHE_DIR = Path(__file__).parent / "cache"
CASES_FILE = CACHE_DIR / "test_cases.json"
COUNTS_FILE = CACHE_DIR / "test_case_step_counts.json"
PAGE = 100
CONCURRENCY = 8
RETRIES = 3
SAVE_EVERY = 50


def make_interface():
    return ZephyrInterface(
        zephyr_api_token=os.environ["ZEPHYR_API_TOKEN"],
        jira_api_token=os.environ["JIRA_API_TOKEN"],
        jira_username=os.environ["JIRA_USERNAME"],
    )


async def count_steps(z, case_key):
    """Return the number of steps in a test case (paginated, raw count)."""
    total, start = 0, 0
    while True:
        resp = await z.get(
            f"testcases/{case_key}/teststeps",
            {"maxResults": PAGE, "startAt": start},
        )
        vals = resp.get("values", [])
        total += len(vals)
        if resp.get("isLast", True) or not vals:
            break
        start += PAGE
    return total


async def main():
    cases = json.loads(CASES_FILE.read_text())
    results = {}
    if COUNTS_FILE.exists():
        results = json.loads(COUNTS_FILE.read_text())
    todo = [c for c in cases if c["key"] not in results]
    print(f"{len(cases)} test cases total, {len(results)} already done, "
          f"{len(todo)} to process")

    z = make_interface()
    sem = asyncio.Semaphore(CONCURRENCY)
    done = 0
    lock = asyncio.Lock()

    async def worker(case):
        nonlocal done
        async with sem:
            for attempt in range(1, RETRIES + 1):
                try:
                    n = await count_steps(z, case["key"])
                    break
                except Exception as exc:  # transient network / rate limit
                    if attempt == RETRIES:
                        print(f"  !! {case['key']} failed: {exc}")
                        return
                    await asyncio.sleep(2 * attempt)
            async with lock:
                results[case["key"]] = {
                    "key": case["key"],
                    "name": case.get("name"),
                    "n_steps": n,
                }
                done += 1
                if done % SAVE_EVERY == 0:
                    COUNTS_FILE.write_text(json.dumps(results, indent=2))
                    print(f"  ... {done}/{len(todo)} done (saved)")

    await asyncio.gather(*(worker(c) for c in todo))
    COUNTS_FILE.write_text(json.dumps(results, indent=2))

    remaining = [c for c in cases if c["key"] not in results]
    total_steps = sum(r["n_steps"] for r in results.values())
    print(f"\nProcessed cases: {len(results)}/{len(cases)}  "
          f"(remaining: {len(remaining)})")
    print(f"Total steps across all test cases: {total_steps}")
    print(f"Saved -> {COUNTS_FILE}")


if __name__ == "__main__":
    asyncio.run(main())
