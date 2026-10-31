"""Schematic efficiency waterfall for the LSST@LATAM 2026 talk (slide 8).

Message: the efficiency numbers people quote differ mainly in what they exclude. Five
bars, each the previous one with one kind of loss removed, in the order of the slide
chips: whole night (OSF) -> survey time only -> excluding faults -> scheduler model ->
ideal.

Every value is an input from a named source (``STEPS`` below) and is tagged [VERIFY] in
the talk notes; nothing here is computed from telemetry. The step that has no measured
value is drawn hatched and labelled "not yet measured (ROSP-10)". The figure says
"illustrative" on its face. Replace the numbers (or the whole figure) with Lynne Jones's
OSF-waterfall when it arrives.

Sources
-------
* OSF baseline, Jul 2025 (Keith Bechtol's CCR3/ORR2 deck): whole night 0.44,
  science only 0.61, idealized 0.71, simulation 0.72.
* RTN-122: measured visit rate / ideal visit rate 0.82.
* RTN-093: 0.7 start-of-LSST criterion. Ten-year simulation average 0.63.

Outputs ``../figures/efficiency_waterfall_talk.png`` and ``_white``.
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(
    0, str(ROOT.parent / "rubin_color_pallete")
)  # copy the module here before extraction
import rubin_palette as rp  # noqa: E402

FIG = ROOT / "figures"
FIG.mkdir(exist_ok=True)

#: (chip label, denominator excludes..., value or None, source)
STEPS = [
    (
        "whole night\n(OSF)",
        "all night hours\n(−12° twilights)",
        0.44,
        "OSF baseline, Jul 2025 (CCR3/ORR2)",
    ),
    (
        "survey time\nonly",
        "minus engineering,\ncalibration, AOS",
        0.61,
        "OSF baseline, Jul 2025 (CCR3/ORR2)",
    ),
    (
        "excluding\nfaults",
        "minus weather and\nfault closures",
        None,
        "not yet measured (ROSP-10)",
    ),
    (
        "scheduler\nmodel",
        "visits / scheduler-\nmodel visits",
        0.82,
        "RTN-122, measured / ideal visit rate",
    ),
    ("ideal", "no overheads\nbeyond readout", 1.0, "by definition"),
]
REFERENCE_LINES = [
    (0.70, "LSST start criterion 0.70 (RTN-093)"),
    (0.63, "10-year simulation 0.63"),
]

C = {
    "bar": rp.CATEGORICAL[0],
    "ideal": rp.NEUTRALS["muted"],
    "ref": rp.CATEGORICAL[1],
    "ink": rp.NEUTRALS["ink"],
    "ink2": rp.NEUTRALS["ink_secondary"],
    "grid": rp.NEUTRALS["grid"],
}
TALK_RC = {
    "figure.figsize": (13.33, 7.5),
    "font.size": 18,
    "axes.labelsize": 20,
    "axes.titlesize": 22,
    "xtick.labelsize": 18,
    "ytick.labelsize": 16,
    "axes.linewidth": 1.2,
    "hatch.linewidth": 1.5,
    "hatch.color": C["bar"],
    "text.color": C["ink"],
    "axes.labelcolor": C["ink"],
    "axes.edgecolor": C["ink2"],
    "xtick.color": C["ink"],
    "ytick.color": C["ink2"],
    "grid.color": C["grid"],
}


def make_figure():
    x = np.arange(len(STEPS))
    with mpl.rc_context(TALK_RC):
        fig, ax = plt.subplots()
        for xi, (label, excl, val, src) in zip(x, STEPS):
            if val is None:
                # Unmeasured: hatched outline between the neighbours' values.
                lo = STEPS[1][2]
                hi = STEPS[3][2]
                ax.bar(
                    xi,
                    hi - lo,
                    bottom=lo,
                    width=0.62,
                    facecolor="none",
                    edgecolor=C["bar"],
                    hatch="///",
                    linewidth=1.5,
                )
                ax.text(
                    xi,
                    hi + 0.02,
                    "not yet\nmeasured\n(ROSP-10)",
                    ha="center",
                    va="bottom",
                    color=C["ink"],
                    fontsize=16,
                    linespacing=1.1,
                )
            else:
                color = C["ideal"] if val >= 1.0 else C["bar"]
                ax.bar(xi, val, width=0.62, color=color, linewidth=0)
                ax.text(
                    xi,
                    val + 0.02,
                    f"{val:.2f}",
                    ha="center",
                    va="bottom",
                    color=C["ink"],
                    fontsize=20,
                    fontweight="bold",
                )
            ax.text(
                xi,
                -0.2,
                excl,
                ha="center",
                va="top",
                color=C["ink2"],
                fontsize=14,
                linespacing=1.1,
                transform=ax.get_xaxis_transform(),
            )
        for y, text in REFERENCE_LINES:
            ax.axhline(y, color=C["ref"], lw=2, ls=(0, (6, 3)), zorder=0)
            ax.text(
                -0.55,
                y + 0.012,
                text,
                ha="left",
                va="bottom",
                color=C["ref"],
                fontsize=14,
            )
        ax.set_xticks(x)
        ax.set_xticklabels([s[0] for s in STEPS])
        ax.set_ylim(0, 1.12)
        ax.set_xlim(-0.6, len(STEPS) - 0.4)
        ax.set_ylabel("efficiency")
        ax.yaxis.set_major_formatter(mpl.ticker.PercentFormatter(1.0, decimals=0))
        ax.set_yticks(np.arange(0, 1.01, 0.2))
        ax.spines[["top", "right"]].set_visible(False)
        ax.grid(axis="y", alpha=0.6)
        ax.set_title(
            "Survey efficiency: the same telescope, five denominators (illustrative)",
            loc="left",
        )
        fig.text(
            0.01,
            0.01,
            "Each bar removes one kind of loss from the denominator of the one before it; the hatched step has no "
            "measured value yet.\nSources: OSF baseline, Jul 2025 (CCR3/ORR2) for 0.44 and 0.61; RTN-122 for 0.82. "
            "All values still to be verified.",
            ha="left",
            va="bottom",
            color=C["ink2"],
            fontsize=12.5,
            linespacing=1.2,
        )
        fig.subplots_adjust(left=0.08, right=0.98, bottom=0.27, top=0.92)
        stem = FIG / "efficiency_waterfall_talk"
        fig.savefig(f"{stem}.png", dpi=200, transparent=True)
        fig.savefig(f"{stem}_white.png", dpi=200, facecolor="white")
        print("wrote", stem, "[_white].png")


if __name__ == "__main__":
    make_figure()
