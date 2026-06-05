#!/usr/bin/env python
"""Average and maximum number of test cases per test campaign (commissioning
era).

A "campaign" here is a commissioning era — a date range. Each test cycle is
assigned to a campaign by the date embedded in its name. Within a campaign we
report, over its test cycles, the number of cycles and the mean / median / max
number of test cases per cycle (plus the campaign total).

Reads cache/test_case_counts.json (per-cycle unique test-case counts).

Usage:
    PYTHONPATH=../python python stats_test_cases_per_campaign.py
"""
import json
import re
from datetime import datetime
from pathlib import Path

CACHE_DIR = Path(__file__).parent / "cache"
COUNTS_FILE = CACHE_DIR / "test_case_counts.json"
DATE_RE = re.compile(r"(\d{4}-\d{2}-\d{2})")
NOW = datetime(2026, 6, 5)

# Commissioning campaigns (eras): (label, start, end). Half-open [start, end).
# Ranges from investigations/README.md section 3.
CAMPAIGNS = [
    ("ComCam Commissioning on Sky", datetime(2024, 10, 1), datetime(2024, 12, 31)),
    ("AuxTel only (ComCam->LSSTCam swap)", datetime(2024, 12, 31), datetime(2025, 4, 1)),
    ("LSSTCam Commissioning on Sky", datetime(2025, 4, 1), datetime(2025, 9, 22)),
    ("Planned maintenance downtime", datetime(2025, 9, 22), datetime(2025, 10, 17)),
    ("Early Operations", datetime(2025, 10, 17), NOW),
]


def campaign_for(date):
    for label, start, end in CAMPAIGNS:
        if start <= date < end:
            return label
    return "Pre-commissioning / other"


def main():
    rows = list(json.loads(COUNTS_FILE.read_text()).values())

    buckets = {}
    undated = []
    for r in rows:
        m = DATE_RE.search(r.get("name") or "")
        if not m:
            undated.append(r["key"])
            continue
        date = datetime.strptime(m.group(1), "%Y-%m-%d")
        buckets.setdefault(campaign_for(date), []).append(r["n_test_cases"])

    order = [c[0] for c in CAMPAIGNS] + ["Pre-commissioning / other"]
    header = (
        f"{'Campaign':<38} {'#cycles':>7} {'mean':>7} {'median':>7} "
        f"{'max':>5} {'total':>7}"
    )
    print(header)
    print("-" * len(header))
    for label in order:
        counts = sorted(buckets.get(label, []))
        if not counts:
            continue
        n = len(counts)
        mean = sum(counts) / n
        median = counts[n // 2] if n % 2 else (counts[n // 2 - 1] + counts[n // 2]) / 2
        print(
            f"{label:<38} {n:>7} {mean:>7.1f} {median:>7.1f} "
            f"{max(counts):>5} {sum(counts):>7}"
        )

    total_cycles = sum(len(v) for v in buckets.values())
    print("-" * len(header))
    print(f"Dated cycles: {total_cycles}   Undated (excluded): {len(undated)} "
          f"({', '.join(undated) or 'none'})")


if __name__ == "__main__":
    main()
