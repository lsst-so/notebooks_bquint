#!/usr/bin/env python
"""Weekly-binned bar chart of test-case count per test cycle, with
commissioning-era spans annotated.

Each bar is the mean number of test cases per cycle for cycles falling in that
ISO week. Reads cache/test_case_counts.json.

Usage:
    PYTHONPATH=../python python plot_timeline_weekly.py
"""
import json
import re
from datetime import datetime, timedelta
from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd

CACHE_DIR = Path(__file__).parent / "cache"
COUNTS_FILE = CACHE_DIR / "test_case_counts_executed.json"
COUNT_FIELD = "n_executed"  # executed test cases per cycle (excl. Not Executed)
OUT_PNG = Path(__file__).parent / "test_cases_timeline_weekly.png"
DATE_RE = re.compile(r"(\d{4}-\d{2}-\d{2})")
NOW = datetime(2026, 6, 5)

# Official Vera C. Rubin Observatory brand palette, taken from the Visual
# Identity Manual (V7, 2021-02-12), pages 27-30. These are the brand-identity
# colors (HEX / Pantone), NOT the ugrizy filter-plot colors.
RUBIN = {
    "teal":      "#058B8C",  # primary imagotype teal (Pantone 2237 C)
    "bright_teal": "#00BABC",  # Pantone 2397 C
    "dark_teal": "#0C4A47",  # complementary dark teal (Pantone 3302 C)
    "mid_teal":  "#009FA1",  # complementary teal (Pantone 320 C)
    "steel":     "#313333",  # observatory steel gray (RAL-5018, Pantone 447 C)
    "cool_gray": "#6A6E6E",  # Pantone Cool Gray 9 C
    "red":       "#ED4C4C",  # accent warm (Pantone 2348 C)
    "green":     "#3CAE3F",  # accent warm (Pantone 7738 C)
    "orange":    "#FAB364",  # accent warm (Pantone 1485 C)
    "yellow":    "#FFE266",  # accent warm (Pantone 2003 C)
    "blue":      "#1C81A4",  # accent cold (Pantone 2454 C)
    "purple":    "#583671",  # accent cold (Pantone 7665 C)
}

# Planned downtimes, shifted right by half a week so the band aligns with the
# weekly (week-ending) bins. The era boundaries below meet the shifted edges,
# so all spans stay contiguous and never overlap.
HALF_WEEK = timedelta(days=3.5)
DT_START = datetime(2025, 9, 22) + HALF_WEEK
# Right edge nudged one weekly bin left so the (operations) week-ending 2025-10-26
# bar falls in Early Operations, not inside the downtime band.
DT_END = datetime(2025, 10, 19) + HALF_WEEK
DOWNTIMES = [
    (DT_START, DT_END, "Planned maintenance downtime"),
]

# Commissioning eras: (start, end, label, color), tinted with the Rubin palette.
# ComCam left edge sits just left of the week-ending 2024-10-20 ramp-up bar.
ERAS = [
    (datetime(2024, 10, 17), datetime(2024, 12, 15),
     "ComCam Commissioning\n on Sky", RUBIN["dark_teal"]),
    (datetime(2024, 12, 15), datetime(2025, 4, 15),
     "AuxTel only\n(ComCam→LSSTCam swap)", RUBIN["cool_gray"]),
    (datetime(2025, 4, 15), DT_START,
     "LSSTCam Commissioning on Sky", RUBIN["purple"]),
    (DT_END, NOW,
     "Early Operations", RUBIN["blue"]),
]


def main():
    rows = list(json.loads(COUNTS_FILE.read_text()).values())

    dates, counts, undated = [], [], []
    for r in rows:
        m = DATE_RE.search(r.get("name") or "")
        if m:
            dates.append(datetime.strptime(m.group(1), "%Y-%m-%d"))
            counts.append(r[COUNT_FIELD])
        else:
            undated.append(r["key"])

    s = pd.Series(counts, index=pd.DatetimeIndex(dates)).sort_index()
    weekly = s.resample("W").mean()          # mean test cases per cycle, per week
    weekly = weekly.dropna()
    print(f"{len(s)} dated cycles -> {len(weekly)} weeks with data "
          f"({len(undated)} undated: {', '.join(undated) or 'none'})")

    fig, ax = plt.subplots(figsize=(16, 7.5))

    # Era spans + labels.
    era_texts = []
    for start, end, label, color in ERAS:
        ax.axvspan(start, end, color=color, alpha=0.12, zorder=0)
        t = ax.text(start + (end - start) / 2, ax.get_ylim()[1], label,
                    ha="center", va="top", fontsize=9.5, color=color,
                    fontweight="bold", style="italic")
        era_texts.append(t)

    # Weekly bars (width ~6 days so bars nearly touch).
    ax.bar(weekly.index, weekly.values, width=6, color="#006073",
           edgecolor="white", linewidth=0.3, zorder=2)

    # Headroom above the tallest bar so the era labels (placed near the top)
    # don't overlap the bars.
    ax.set_ylim(0, weekly.max() * 1.20)

    fig.suptitle("Rubin Observatory — Commissioning Plans Test Activity",
                 fontsize=15, fontweight="bold")
    ax.set_title("Executed test cases per test cycle, binned by ISO week "
                 "(weekly average)", fontsize=11)
    ax.set_xlabel("Test cycle date (ISO week)")
    ylabel = "Weekly average number of executed test cases per cycle"
    ax.set_ylabel(ylabel)
    ax.grid(True, axis="y", alpha=0.3)
    ax.xaxis.set_major_locator(mdates.MonthLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    fig.autofmt_xdate()
    ax.margins(x=0.01)

    # Mirror the y-axis (ticks + label) on the right side.
    secax = ax.secondary_yaxis("right")
    secax.set_ylabel(ylabel)

    # Planned downtimes: hatched gray overlay with a vertical label.
    top = ax.get_ylim()[1]
    for start, end, label in DOWNTIMES:
        ax.axvspan(start, end, facecolor=RUBIN["steel"], alpha=0.35,
                   hatch="///", edgecolor=RUBIN["steel"], linewidth=0.0,
                   zorder=1)
        ax.text(start + (end - start) / 2, top * 0.45, label,
                ha="center", va="center", rotation=90, fontsize=9,
                color=RUBIN["steel"], fontweight="bold")

    # Re-place era labels now that ylim is final.
    for txt in era_texts:
        txt.set_y(top * 0.97)

    fig.tight_layout(rect=[0, 0, 1, 0.96])
    fig.savefig(OUT_PNG, dpi=130)
    print(f"Saved -> {OUT_PNG}")


if __name__ == "__main__":
    main()
