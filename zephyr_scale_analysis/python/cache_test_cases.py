#!/usr/bin/env python
"""List every test case in project BLOCK and cache the raw payloads.

The Zephyr `testcases?projectKey=BLOCK` list endpoint returns one entry per
test case (keyed BLOCK-T##). As of this writing it returns 680 test cases.

Usage:
    source ~/.zapi
    PYTHONPATH=../python python cache_test_cases.py
"""
import asyncio
import json
import os
from pathlib import Path

from lsst.ts.planning.tool.zephyr_interface import ZephyrInterface

CACHE_DIR = Path(__file__).parent / "cache"
OUT_FILE = CACHE_DIR / "test_cases.json"
PAGE = 100
PROJECT = "BLOCK"


def make_interface():
    return ZephyrInterface(
        zephyr_api_token=os.environ["ZEPHYR_API_TOKEN"],
        jira_api_token=os.environ["JIRA_API_TOKEN"],
        jira_username=os.environ["JIRA_USERNAME"],
    )


async def main():
    z = make_interface()
    out, start = [], 0
    while True:
        resp = await z.get(
            "testcases",
            {"projectKey": PROJECT, "maxResults": PAGE, "startAt": start},
        )
        vals = resp.get("values", [])
        out.extend(vals)
        if resp.get("isLast", True) or not vals:
            break
        start += PAGE

    CACHE_DIR.mkdir(exist_ok=True)
    OUT_FILE.write_text(json.dumps(out, indent=2))
    print(f"Cached {len(out)} test cases -> {OUT_FILE}")


if __name__ == "__main__":
    asyncio.run(main())
