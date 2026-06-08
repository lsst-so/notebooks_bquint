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
# Poster-resolution outputs. The figure is 16 in wide, so saving the PNG at
# 300 dpi gives ~4800 px == ~40 cm at 300 dpi print resolution. The PDF is
# vector and scales to any poster size without quality loss.
OUT_POSTER_PNG = Path(__file__).parent / "test_cases_timeline_weekly_poster.png"
OUT_POSTER_PDF = Path(__file__).parent / "test_cases_timeline_weekly_poster.pdf"
OUT_POSTER_SVG = Path(__file__).parent / "test_cases_timeline_weekly_poster.svg"
POSTER_DPI = 300
# Font/line scale-up for the poster build, so text stays legible from a
# distance and bars read more boldly.
POSTER_SCALE = 1.7
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
     "LSSTComCam Commissioning\n on Sky", RUBIN["dark_teal"]),
    (datetime(2024, 12, 15), datetime(2025, 4, 15),
     "AuxTel only\n(LSSTComCam\nto LSSTCam swap)", RUBIN["cool_gray"]),
    (datetime(2025, 4, 15), DT_START,
     "LSSTCam Commissioning on Sky", RUBIN["purple"]),
    (DT_END, None,  # None -> extend to the right edge of the plot
     "Early Operations", RUBIN["blue"]),
]


def main(poster=False):
    # Scale fonts and line/bar weights up for the poster build; keep the
    # manuscript build at its original, compact sizing.
    s = POSTER_SCALE if poster else 1.0
    # Era labels sit inside narrow campaign spans, so they get a gentler bump
    # than the axis/title/legend text to avoid overlapping each other.
    era_s = 1.2 if poster else 1.0
    bar_w = 6.5 if poster else 6.0
    bar_edge = 0.6 if poster else 0.3

    rows = list(json.loads(COUNTS_FILE.read_text()).values())

    dates, counts_all, counts_exec, undated = [], [], [], []
    for r in rows:
        m = DATE_RE.search(r.get("name") or "")
        if m:
            dates.append(datetime.strptime(m.group(1), "%Y-%m-%d"))
            counts_all.append(r["n_test_cases"])   # all cases added to the cycle
            counts_exec.append(r[COUNT_FIELD])      # executed (not Not Executed)
        else:
            undated.append(r["key"])

    idx = pd.DatetimeIndex(dates)
    weekly_all = pd.Series(counts_all, index=idx).sort_index().resample("W").mean().dropna()
    weekly_exec = pd.Series(counts_exec, index=idx).sort_index().resample("W").mean().dropna()
    print(f"{len(dates)} dated cycles -> {len(weekly_exec)} weeks with data "
          f"({len(undated)} undated: {', '.join(undated) or 'none'})")

    # Plot x-range: a small margin around the first/last weekly bin. The Early
    # Operations span (end=None) is drawn out to plot_right.
    plot_left = weekly_all.index.min().to_pydatetime() - timedelta(days=7)
    plot_right = weekly_all.index.max().to_pydatetime() + timedelta(days=7)

    fig, ax = plt.subplots(figsize=(16, 7.5))

    # Era spans + labels.
    era_texts = []
    for start, end, label, color in ERAS:
        span_end = end if end is not None else plot_right
        ax.axvspan(start, span_end, color=color, alpha=0.12, zorder=0)
        # The ComCam span is narrow; on the poster (bigger fonts) wrap its
        # label onto more lines so it stays inside the span.
        label_text = label
        if poster and label.startswith("LSSTComCam"):
            label_text = "LSSTComCam\nCommissioning\non Sky"
        t = ax.text(start + (span_end - start) / 2, ax.get_ylim()[1], label_text,
                    ha="center", va="top", fontsize=9.5 * era_s, color=color,
                    fontweight="bold", style="italic")
        era_texts.append(t)

    # Weekly bars (width ~6 days so bars nearly touch). Grey bars (all test cases
    # added to the cycle) sit behind; teal bars (executed) sit in front, so the
    # grey peeking above each teal bar is the un-executed remainder.
    ax.bar(weekly_all.index, weekly_all.values, width=bar_w, color="#9AA0A0",
           edgecolor="white", linewidth=bar_edge, zorder=2,
           label="All test cases per cycle")
    ax.bar(weekly_exec.index, weekly_exec.values, width=bar_w, color="#006073",
           edgecolor="white", linewidth=bar_edge, zorder=3,
           label="Executed test cases per cycle")

    # Headroom above the tallest (grey) bar so the era labels (placed near the
    # top) don't overlap the bars.
    ax.set_ylim(0, weekly_all.max() * 1.20)
    # Legend in the right part of the plot, above the (shorter) bars there.
    # On the poster the legend is larger, so pin it to the upper-right corner
    # inside the axes instead of anchoring its left edge (which overflowed).
    if poster:
        ax.legend(loc="upper right", bbox_to_anchor=(0.985, 0.88),
                  frameon=True, framealpha=0.9, fontsize=9.5 * s)
    else:
        ax.legend(loc="upper left", bbox_to_anchor=(0.80, 0.80),
                  frameon=True, framealpha=0.9, fontsize=9.5 * s)

    fig.suptitle("Rubin Observatory — Commissioning Plans Test Activity",
                 fontsize=15 * s, fontweight="bold")
    ax.set_title("Test cases per test cycle, binned by ISO week "
                 "(weekly average)", fontsize=11 * s)
    ax.set_xlabel("Test cycle date (ISO week)", fontsize=11 * s)
    # Single line fits the manuscript height; at the poster's larger font it
    # would be taller than the axis, so wrap it onto two lines.
    ylabel = ("Weekly average number of\ntest cases per cycle" if poster
              else "Weekly average number of test cases per cycle")
    ax.set_ylabel(ylabel, fontsize=11 * s)
    ax.tick_params(axis="both", labelsize=9.5 * s)
    ax.grid(True, axis="y", alpha=0.3)
    # Monthly ticks for the manuscript; every other month on the poster so the
    # larger date labels don't crowd or collide with the y-axis label.
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=2 if poster else 1))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    fig.autofmt_xdate()
    ax.set_xlim(plot_left, plot_right)

    # Planned downtimes: light hatched overlay (kept lighter than the grey bars)
    # with a vertical label.
    top = ax.get_ylim()[1]
    for start, end, label in DOWNTIMES:
        ax.axvspan(start, end, facecolor="#DCE0E3", alpha=0.8,
                   hatch="///", edgecolor=RUBIN["cool_gray"], linewidth=0.0,
                   zorder=1)
        ax.text(start + (end - start) / 2, top * 0.45, label,
                ha="center", va="center", rotation=90, fontsize=9 * s,
                color=RUBIN["steel"], fontweight="bold")

    # Re-place era labels now that ylim is final.
    for txt in era_texts:
        txt.set_y(top * 0.97)

    fig.tight_layout(rect=[0, 0, 1, 0.96])
    if poster:
        fig.savefig(OUT_POSTER_PNG, dpi=POSTER_DPI)
        fig.savefig(OUT_POSTER_PDF)
        fig.savefig(OUT_POSTER_SVG)
        print(f"Saved -> {OUT_POSTER_PNG} ({POSTER_DPI} dpi, ~40 cm wide)")
        print(f"Saved -> {OUT_POSTER_PDF} (vector)")
        print(f"Saved -> {OUT_POSTER_SVG} (vector, for PowerPoint)")
    else:
        fig.savefig(OUT_PNG, dpi=130)
        print(f"Saved -> {OUT_PNG}")
    plt.close(fig)


if __name__ == "__main__":
    main(poster=False)   # compact manuscript figure
    main(poster=True)    # large-font, thick-bar poster figure
