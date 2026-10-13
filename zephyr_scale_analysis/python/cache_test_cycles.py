#!/usr/bin/env python
"""Cache all test cycles under the "Commissioning Plans" folder (and its
subfolders) from Zephyr Scale, saving raw payloads locally for offline analysis.

Usage:
    source ~/.zapi
    PYTHONPATH=../python python cache_test_cycles.py

Writes:
    cache/test_cycles.json   - list of raw test-cycle payloads
    cache/folders.json       - the TEST_CYCLE folder subtree under the root
"""
import asyncio
import json
import os
from pathlib import Path

from lsst.ts.planning.tool.zephyr_interface import ZephyrInterface

PROJECT_KEY = "BLOCK"
ROOT_FOLDER_NAME = "Commissioning Plans"
CACHE_DIR = Path(__file__).parent / "cache"
PAGE = 100


def make_interface():
    return ZephyrInterface(
        zephyr_api_token=os.environ["ZEPHYR_API_TOKEN"],
        jira_api_token=os.environ["JIRA_API_TOKEN"],
        jira_username=os.environ["JIRA_USERNAME"],
    )


async def get_all(z, endpoint, params):
    """Page through a Zephyr list endpoint, returning all `values`."""
    out = []
    start = 0
    while True:
        p = dict(params, maxResults=PAGE, startAt=start)
        resp = await z.get(endpoint, p)
        vals = resp.get("values", [])
        out.extend(vals)
        if resp.get("isLast", True) or not vals:
            break
        start += PAGE
    return out


def descendants(folders, root_id):
    """Return root_id plus all folder ids transitively under it."""
    children = {}
    for f in folders:
        children.setdefault(f.get("parentId"), []).append(f["id"])
    keep, stack = set(), [root_id]
    while stack:
        fid = stack.pop()
        keep.add(fid)
        stack.extend(children.get(fid, []))
    return keep


async def main():
    CACHE_DIR.mkdir(exist_ok=True)
    z = make_interface()

    # 1. All TEST_CYCLE folders, find the root and its subtree.
    folders = await get_all(
        z, "folders", {"projectKey": PROJECT_KEY, "folderType": "TEST_CYCLE"}
    )
    root = next(f for f in folders if f["name"] == ROOT_FOLDER_NAME)
    target_ids = descendants(folders, root["id"])
    subtree = [f for f in folders if f["id"] in target_ids]
    print(f"Root '{ROOT_FOLDER_NAME}' id={root['id']}; "
          f"{len(target_ids)} folder(s) in subtree")

    # 2. All test cycles in those folders.
    cycles = []
    for f in subtree:
        c = await get_all(
            z, "testcycles", {"projectKey": PROJECT_KEY, "folderId": f["id"]}
        )
        print(f"  folder {f['id']:>10}  {f['name'][:45]:45}  {len(c):>4} cycles")
        cycles.extend(c)

    # 3. Cache.
    (CACHE_DIR / "folders.json").write_text(json.dumps(subtree, indent=2))
    (CACHE_DIR / "test_cycles.json").write_text(json.dumps(cycles, indent=2))
    print(f"\nTOTAL test cycles cached: {len(cycles)}")
    print(f"Saved -> {CACHE_DIR/'test_cycles.json'}")


if __name__ == "__main__":
    asyncio.run(main())
