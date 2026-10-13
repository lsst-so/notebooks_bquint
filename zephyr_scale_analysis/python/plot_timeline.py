#!/usr/bin/env python
"""Plot a timeline of test-case count per test cycle in "Commissioning Plans".

Reads cache/test_case_counts.json, extracts the YYYY-MM-DD date embedded in
each cycle name, and plots date vs. number of test cases.

Usage:
    PYTHONPATH=../python python plot_timeline.py
"""
import json
import re
from datetime import datetime
from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.pyplot as plt

CACHE_DIR = Path(__file__).parent / "cache"
COUNTS_FILE = CACHE_DIR / "test_case_counts.json"
OUT_PNG = Path(__file__).parent / "test_cases_timeline.png"
DATE_RE = re.compile(r"(\d{4}-\d{2}-\d{2})")


def main():
    rows = list(json.loads(COUNTS_FILE.read_text()).values())

    points, undated = [], []
    for r in rows:
        m = DATE_RE.search(r.get("name") or "")
        if m:
            points.append((datetime.strptime(m.group(1), "%Y-%m-%d"),
                           r["n_test_cases"], r["key"]))
        else:
            undated.append(r["key"])
    points.sort(key=lambda p: p[0])

    dates = [p[0] for p in points]
    counts = [p[1] for p in points]
    print(f"{len(points)} dated cycles, {len(undated)} undated "
          f"({', '.join(undated) if undated else 'none'})")
    print(f"Date range: {dates[0].date()} -> {dates[-1].date()}")

    fig, ax = plt.subplots(figsize=(15, 6))
    ax.plot(dates, counts, "-", color="#bbb", lw=0.8, zorder=1)
    ax.scatter(dates, counts, s=14, color="#1f77b4", zorder=2)

    ax.set_title("Commissioning Plans — Test Cases per Test Cycle Over Time")
    ax.set_xlabel("Test cycle date")
    ax.set_ylabel("Number of test cases")
    ax.grid(True, alpha=0.3)
    ax.xaxis.set_major_locator(mdates.MonthLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    fig.autofmt_xdate()
    ax.margins(x=0.01)

    fig.tight_layout()
    fig.savefig(OUT_PNG, dpi=130)
    print(f"Saved -> {OUT_PNG}")


if __name__ == "__main__":
    main()
