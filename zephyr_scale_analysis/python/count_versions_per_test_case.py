#!/usr/bin/env python
"""Count the number of versions of each test case of project BLOCK.

For every test case (from cache/test_cases.json) this queries
``testcases/{key}/versions`` and counts the version entries returned. Each entry
in the paginated ``values`` list corresponds to one version of the test case.

Resilient to timeouts: results are written incrementally to
``cache/test_case_version_counts.json`` and the script resumes, skipping cases
already counted. Just re-run it until it reports 0 remaining.

Usage:
    source ~/.zapi
    PYTHONPATH=../python python count_versions_per_test_case.py
"""
import asyncio
import json
import os
from pathlib import Path

from lsst.ts.planning.tool.zephyr_interface import ZephyrInterface

CACHE_DIR = Path(__file__).parent / "cache"
CASES_FILE = CACHE_DIR / "test_cases.json"
COUNTS_FILE = CACHE_DIR / "test_case_version_counts.json"
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


async def count_versions(z, case_key):
    """Return the number of versions of a test case (paginated count)."""
    total, start = 0, 0
    while True:
        resp = await z.get(
            f"testcases/{case_key}/versions",
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
                    n = await count_versions(z, case["key"])
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
                    "n_versions": n,
                }
                done += 1
                if done % SAVE_EVERY == 0:
                    COUNTS_FILE.write_text(json.dumps(results, indent=2))
                    print(f"  ... {done}/{len(todo)} done (saved)")

    await asyncio.gather(*(worker(c) for c in todo))
    COUNTS_FILE.write_text(json.dumps(results, indent=2))

    remaining = [c for c in cases if c["key"] not in results]
    counts = [r["n_versions"] for r in results.values()]
    total_versions = sum(counts)
    over20 = sum(1 for c in counts if c > 20)
    print(f"\nProcessed cases: {len(results)}/{len(cases)}  "
          f"(remaining: {len(remaining)})")
    print(f"Total versions across all test cases: {total_versions}")
    print(f"Max versions: {max(counts) if counts else 0}")
    print(f"Cases with > 20 versions: {over20} "
          f"({100 * over20 / len(counts):.1f}%)" if counts else "")
    print(f"Saved -> {COUNTS_FILE}")


if __name__ == "__main__":
    asyncio.run(main())
