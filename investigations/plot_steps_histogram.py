#!/usr/bin/env python
"""Histogram of the number of steps per test case (project BLOCK, 680 cases).

Reads cache/test_case_step_counts.json and renders a histogram with the Rubin
brand palette, annotated with summary statistics.

Usage:
    PYTHONPATH=../python python plot_steps_histogram.py
"""
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

CACHE_DIR = Path(__file__).parent / "cache"
COUNTS_FILE = CACHE_DIR / "test_case_step_counts.json"
OUT_PNG = Path(__file__).parent / "steps_per_test_case_histogram.png"

# Web UI base URL for a test case; append the BLOCK-T## key.
TC_BASE_URL = (
    "https://rubinobs.atlassian.net/projects/BLOCK?selectedItem="
    "com.atlassian.plugins.atlassian-connect-plugin:"
    "com.kanoah.test-manager__main-project-page#!/v2/testCase/"
)

# Rubin brand palette (Visual Identity Manual V7, pp. 27-30).
RUBIN = {
    "teal": "#058B8C",
    "dark_teal": "#0C4A47",
    "steel": "#313333",
    "red": "#ED4C4C",
    "orange": "#FAB364",
}


def main():
    rows = list(json.loads(COUNTS_FILE.read_text()).values())
    steps = np.array([r["n_steps"] for r in rows])

    n = steps.size
    mean, median = steps.mean(), np.median(steps)
    mx, mn = steps.max(), steps.min()
    n_zero = int((steps == 0).sum())
    print(f"Test cases: {n}")
    print(f"Steps -> min {mn}, median {median:.0f}, mean {mean:.2f}, max {mx}")
    print(f"Total steps: {steps.sum()}   Test cases with 0 steps: {n_zero}")

    over30 = sorted((r for r in rows if r["n_steps"] > 30),
                    key=lambda r: r["n_steps"], reverse=True)
    print(f"\nTest cases with > 30 steps ({len(over30)}):")
    for r in over30:
        print(f"  {r['key']:<12} {r['n_steps']:>3} steps   {r.get('name')}")
        print(f"      {TC_BASE_URL}{r['key']}")

    fig, ax = plt.subplots(figsize=(11, 6))

    bins = np.arange(0, mx + 2) - 0.5  # one bin per integer step count
    ax.hist(steps, bins=bins, color="#006073", edgecolor="white", linewidth=0.4)

    ax.axvline(mean, color=RUBIN["red"], linestyle="--", linewidth=1.6,
               label=f"mean = {mean:.1f}")
    ax.axvline(median, color=RUBIN["orange"], linestyle="-.", linewidth=1.6,
               label=f"median = {median:.0f}")

    fig.suptitle("Rubin Observatory — Steps per Test Case (project BLOCK)",
                 fontsize=15, fontweight="bold", color=RUBIN["dark_teal"])
    ax.set_title(f"{n} test cases   ·   {steps.sum()} total steps   ·   "
                 f"max {mx} steps", fontsize=11)
    ax.set_xlabel("Number of steps in a test case")
    ax.set_ylabel("Number of test cases")
    ax.grid(True, axis="y", alpha=0.3)
    ax.legend(frameon=False)
    ax.margins(x=0.01)

    # Cap the x-axis at 30 steps; note how many cases fall beyond it.
    XMAX = 30
    n_beyond = int((steps > XMAX).sum())
    ax.set_xlim(-0.5, XMAX + 0.5)
    if n_beyond:
        ax.text(0.985, 0.80,
                f"{n_beyond} cases with > {XMAX} steps not shown\n(max = {mx})",
                transform=ax.transAxes, ha="right", va="top", fontsize=9,
                color=RUBIN["steel"], style="italic")

    fig.tight_layout(rect=[0, 0, 1, 0.96])
    fig.savefig(OUT_PNG, dpi=130)
    print(f"Saved -> {OUT_PNG}")


if __name__ == "__main__":
    main()
