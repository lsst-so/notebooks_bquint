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
COUNTS_FILE = CACHE_DIR / "test_case_counts_executed.json"
COUNT_FIELD = "n_executed"  # executed test cases per cycle (excl. Not Executed)
DATE_RE = re.compile(r"(\d{4}-\d{2}-\d{2})")
NOW = datetime(2026, 6, 5)

# Commissioning campaigns (eras): (label, start, end). Half-open [start, end).
# Boundaries confirmed by the user (2026-06-05); maintenance window is
# approximate (exact dates unclear), ended at the Early Operations start.
CAMPAIGNS = [
    ("ComCam Commissioning on Sky", datetime(2024, 10, 24), datetime(2024, 12, 15)),
    ("AuxTel only (ComCam->LSSTCam swap)", datetime(2024, 12, 15), datetime(2025, 4, 15)),
    ("LSSTCam Commissioning on Sky", datetime(2025, 4, 15), datetime(2025, 9, 22)),
    ("Planned maintenance downtime", datetime(2025, 9, 22), datetime(2025, 10, 26)),
    ("Early Operations", datetime(2025, 10, 26), NOW),
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
        buckets.setdefault(campaign_for(date), []).append(r[COUNT_FIELD])

    # Mean/median are over *active* cycles (>=1 executed Test Case); cycles
    # where nothing was executed are excluded so the average reflects a typical
    # working night rather than being dragged down by empty/placeholder cycles.
    order = [c[0] for c in CAMPAIGNS] + ["Pre-commissioning / other"]
    header = (
        f"{'Campaign':<38} {'#cyc':>5} {'#act':>5} {'mean':>7} {'median':>7} "
        f"{'max':>5} {'total':>7}"
    )
    print(header)
    print("-" * len(header))
    for label in order:
        counts = sorted(buckets.get(label, []))
        if not counts:
            continue
        active = [c for c in counts if c > 0]
        na = len(active)
        if na:
            mean = sum(active) / na
            median = active[na // 2] if na % 2 else (active[na // 2 - 1] + active[na // 2]) / 2
        else:
            mean = median = 0
        print(
            f"{label:<38} {len(counts):>5} {na:>5} {mean:>7.1f} {median:>7.1f} "
            f"{max(counts):>5} {sum(counts):>7}"
        )

    total_cycles = sum(len(v) for v in buckets.values())
    print("-" * len(header))
    print(f"Dated cycles: {total_cycles}   Undated (excluded): {len(undated)} "
          f"({', '.join(undated) or 'none'})")


if __name__ == "__main__":
    main()
