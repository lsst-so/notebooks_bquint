"""A good night and a bad night against the LSST ideal night (figure B12).

Three horizontal bars of equal length - the -12 deg observable night - stacked
top to bottom: the LSST ideal night, a real good night and a real bad night.
Each bar is the same block form as slide 3, in ROSP-24 precedence order and in the
deck's own ``SLIDE2_COLORS`` (as slide-4 B1; see ``PALETTE`` below and README §5),
so the three read as the same accounting:

* **Science**, subdivided: exposing (solid), expected gap + in-visit overhead
  (a lighter tint), excess gap (hatched);
* **Alignment**, **Engineering**, **Fault + idle**, **Weather** (hatched).

The dashed tick on each real bar is the hour at which exposing would end if the
night had met the RTN-093 survey-start criterion, survey speed > 0.7, i.e. at
0.7 of the ideal night's exposing time.

Inputs are this folder's own ``data/night_budget_<min>_<max>.csv``, written by
``night_budget.py``. No cross-folder imports.

The legend sits in two rows under the x axis: ``Science:`` with the three
subdivisions, then ``Lost:`` with the categories that are not Science.

Outputs ``../figures/good_bad_night_<good>_<bad>.png`` and ``_white.png``, 16:6.

Run from a set-up kernel shell::

    source /sdf/group/rubin/sw/loadLSST.bash; setup lsst_distrib
    python python/make_good_bad_night_figure.py
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(
    0, str(ROOT.parent / "rubin_color_pallete")
)  # copy the module here before extraction
import rubin_palette as rp  # noqa: E402

DATA = ROOT / "data"
FIG = ROOT / "figures"

#: The two nights on the slide. 6 Jul is the selector's top-ranked clean night
#: (ratio 0.851); 8 Jul is the bad night already explained in B11.
GOOD_DAY_OBS = 20260706
BAD_DAY_OBS = 20260708
#: One word per bar, as on slide 5.
BAR_NOTE = {GOOD_DAY_OBS: "smooth", BAD_DAY_OBS: "camera + clouds"}

#: RTN-093 survey-start criterion: survey speed > 0.7.
SURVEY_SPEED_CRITERION = 0.7
VISIT_S = 30.0

# TEMPORARY: slide-2 colours, the same deliberate palette violation as slide-4 B1
# (``SLIDE2_COLORS`` in ``simonyi_time_loss/python/make_latam_figures.py``, see that
# README §3b.1). Copied rather than imported so this folder stays extractable; if the
# deck palette changes, change it in both places. Bruno asked for the deck colours on
# 2026-11-02 so B12 matches slides 4 and 5. Switching back to the Rubin palette is one
# line: use ``RUBIN_COLORS`` instead of ``SLIDE2_COLORS`` below.
SLIDE2_COLORS = {
    "Science": "#024243",
    "Engineering": "#045B5C",
    "Alignment": "#058B8C",
    "Fault + idle": "#F5A623",
    "Planned maintenance": "#546E7A",
    "Weather": "#9BAEB8",
}
#: The canonical Rubin palette, kept so the violation can be reverted in one line.
RUBIN_COLORS = {
    "Science": rp.CATEGORY_COLORS["survey"],
    "Engineering": rp.CATEGORY_COLORS["engineering"],
    "Alignment": rp.CATEGORY_COLORS["focus"],
    "Fault + idle": rp.CATEGORY_COLORS["fault_idle"],
    "Planned maintenance": rp.NEUTRALS["muted"],
    "Weather": rp.CATEGORY_COLORS["weather"],
}

PALETTE = SLIDE2_COLORS

C = {
    "survey": PALETTE["Science"],
    "focus": PALETTE["Alignment"],
    "engineering": PALETTE["Engineering"],
    "fault_idle": PALETTE["Fault + idle"],
    "weather": PALETTE["Weather"],
    "ink": rp.NEUTRALS["ink"],
    "ink2": rp.NEUTRALS["ink_secondary"],
    "muted": rp.NEUTRALS["muted"],
    "grid": rp.NEUTRALS["grid"],
}

#: Legend rows: the Science subdivisions, then the categories that are not Science.
#: ``(style, label)``; drawn in two rows under the x axis, in stack order.
LEGEND_ROWS = (
    (
        "Science",
        [
            ("survey", "exposing (shutter open)"),
            ("survey_light", "expected gap + in-visit overhead"),
            ("survey_hatch", "excess gap"),
        ],
    ),
    (
        "Lost",
        [
            ("focus", "Alignment"),
            ("engineering", "Engineering"),
            ("fault_idle", "Fault + idle"),
            ("weather_hatch", "Weather"),
        ],
    ),
)

RC = {
    "figure.figsize": (16, 6),
    "font.size": 15,
    "axes.titlesize": 20,
    "xtick.labelsize": 14,
    "axes.linewidth": 1.0,
    "text.color": C["ink"],
    "axes.labelcolor": C["ink"],
    "axes.edgecolor": C["ink2"],
    "xtick.color": C["ink2"],
    "ytick.color": C["ink2"],
}

BAR_H = 0.52  # bar thickness in y units


def load_budget(path: Path | None = None) -> pd.DataFrame:
    """The most recent ``night_budget_*.csv`` in ``data/`` unless given a path."""
    if path is None:
        candidates = sorted(DATA.glob("night_budget_*.csv"))
        if not candidates:
            raise SystemExit("no data/night_budget_*.csv - run python/night_budget.py first")
        path = candidates[-1]
    b = pd.read_csv(path)
    return b.set_index("day_obs")


def ideal_bar(night_h: float, osf: float) -> list[tuple[str, float, str]]:
    """The ideal night's blocks: exposing at the fitted OSF, the rest overhead.

    The simulations have no weather, no fault and no alignment block - the whole
    non-exposing remainder is the modelled slew, settle and readout.
    """
    exposing = night_h * osf
    return [
        ("exposing", exposing, "survey"),
        ("overhead", night_h - exposing, "survey_light"),
    ]


def real_bar(row: pd.Series) -> list[tuple[str, float, str]]:
    """One real night's blocks, in ROSP-24 precedence order.

    Science comes first (exposing, then the expected overhead, then the excess
    gap), then alignment, engineering, fault + idle and weather.  The blocks are
    scaled at the end so the bar is exactly the -12 deg night: the ROSP-24
    categories and the visit-level Science split are measured independently and
    need not sum to the night to the minute.
    """
    blocks = [
        ("exposing", row.exposing_h, "survey"),
        ("expected", row.gap_expected_h + row.in_visit_h, "survey_light"),
        ("excess", row.gap_excess_h, "survey_hatch"),
        ("alignment", np.nan_to_num(row.focus_h) + row.nonsurvey_visit_h, "focus"),
        ("engineering", np.nan_to_num(row.engineering_h), "engineering"),
        ("fault_idle", np.nan_to_num(row.fault_idle_h), "fault_idle"),
        ("weather", np.nan_to_num(row.weather_h), "weather_hatch"),
    ]
    total = sum(h for _, h, _ in blocks)
    if total > 0:
        scale = row.night_h / total
        blocks = [(name, h * scale, style) for name, h, style in blocks]
    return blocks


#: One spec per block style: ``(colour, alpha, hatch)``. The blocks and the legend
#: swatches are both drawn from this, so they cannot drift apart. The three Science
#: styles are one hue at three strengths, as the slide-3 form asks; Weather keeps the
#: slide-4 B1 hatch direction so the two figures read the same way.
STYLE = {
    "survey": (C["survey"], 1.00, None),
    "survey_light": (C["survey"], 0.45, None),
    "survey_hatch": (C["survey"], 0.20, "///"),
    "focus": (C["focus"], 1.00, None),
    "engineering": (C["engineering"], 1.00, None),
    "fault_idle": (C["fault_idle"], 1.00, None),
    "weather_hatch": (C["weather"], 0.45, "\\\\\\"),
}


def _draw_block(ax, x: float, y: float, w: float, style: str, zorder: float = 1.0) -> None:
    """One block: a solid colour, a lighter tint, or a hatch over a tint."""
    if w <= 0:
        return
    base, alpha, hatch = STYLE[style]
    ax.add_patch(
        mpl.patches.Rectangle(
            (x, y - BAR_H / 2),
            w,
            BAR_H,
            facecolor=base,
            alpha=alpha,
            edgecolor="none",
            zorder=zorder,
        )
    )
    if hatch:
        ax.add_patch(
            mpl.patches.Rectangle(
                (x, y - BAR_H / 2),
                w,
                BAR_H,
                facecolor="none",
                edgecolor=base,
                hatch=hatch,
                linewidth=0,
                alpha=0.85,
                zorder=zorder + 0.1,
            )
        )


def _legend_handles(style: str, label: str) -> mpl.patches.Patch:
    """A legend swatch drawn from the same :data:`STYLE` spec as the blocks."""
    base, alpha, hatch = STYLE[style]
    return mpl.patches.Patch(
        facecolor=base, alpha=alpha, hatch=hatch, edgecolor=base if hatch else "none", label=label
    )


def make_figure(budget: pd.DataFrame, good: int, bad: int, baseline: str) -> Path:
    good_row, bad_row = budget.loc[good], budget.loc[bad]
    # The ideal bar uses the longer of the two nights, so all three bars share
    # one x axis; the seasonal OSF is taken from the good night.
    night_h = max(good_row.night_h, bad_row.night_h)
    ideal_osf = good_row.ideal_osf
    ideal_exposing_h = night_h * ideal_osf

    bars = [
        ("LSST ideal night", "v5.3 baseline", ideal_bar(night_h, ideal_osf), None),
        (f"{pd.Timestamp(str(good)):%d %b %Y}", BAR_NOTE.get(good, ""), real_bar(good_row), good_row),
        (f"{pd.Timestamp(str(bad)):%d %b %Y}", BAR_NOTE.get(bad, ""), real_bar(bad_row), bad_row),
    ]

    with mpl.rc_context(RC):
        fig, ax = plt.subplots()
        ys = [2.0, 1.0, 0.0]
        for y, (label, note, blocks, row) in zip(ys, bars):
            # the night outline, so a short night still reads as a full bar
            ax.add_patch(
                mpl.patches.Rectangle(
                    (0, y - BAR_H / 2),
                    night_h,
                    BAR_H,
                    facecolor="white",
                    edgecolor=C["grid"],
                    linewidth=0.8,
                    zorder=0,
                )
            )
            x = 0.0
            edges = []
            for _name, w, style in blocks:
                _draw_block(ax, x, y, w, style)
                x += w
                if w > 0:
                    edges.append(x)
            # Hairline separators at the joins. The deck palette puts Engineering
            # (#045B5C) next to exposing (#024243), which are two steps of one teal
            # ramp and merge where they touch; a white rule keeps every block
            # countable without adding a sixth hue.
            for edge in edges[:-1]:
                ax.plot(
                    [edge, edge],
                    [y - BAR_H / 2, y + BAR_H / 2],
                    color="white",
                    linewidth=1.1,
                    solid_capstyle="butt",
                    zorder=2,
                )

            # left-hand labels: date, then one word
            ax.text(-0.25, y + 0.10, label, ha="right", va="center", fontsize=16, color=C["ink"])
            if note:
                ax.text(
                    -0.25, y - 0.16, note, ha="right", va="center", fontsize=13, color=C["ink2"]
                )

            # right-hand label: visits and the ratio to the ideal night
            if row is None:
                n_vis = int(np.floor(ideal_exposing_h * 3600.0 / VISIT_S))
                right = f"{n_vis} visits  ·  1.00"
            else:
                right = f"{int(row.n_survey)} visits  ·  {row.ratio:.2f}"
            ax.text(
                night_h + 0.25, y, right, ha="left", va="center", fontsize=16, color=C["ink"]
            )

            # RTN-093 tick: where exposing would end at survey speed 0.7
            if row is not None:
                ax.plot(
                    [ideal_exposing_h * SURVEY_SPEED_CRITERION] * 2,
                    [y - BAR_H / 2 - 0.06, y + BAR_H / 2 + 0.06],
                    linestyle=(0, (4, 3)),
                    linewidth=1.6,
                    color=C["ink"],
                    zorder=3,
                )

        ax.set_xlim(0, night_h)
        ax.set_ylim(-0.75, 2.75)
        ax.set_yticks([])
        for side in ("left", "right", "top"):
            ax.spines[side].set_visible(False)
        ax.set_xticks(np.arange(0, np.floor(night_h) + 1, 1.0))
        ax.set_xlabel("hours into the observable night (Sun at $-12°$ → $-12°$)")
        ax.tick_params(axis="x", length=3, pad=3)
        ax.set_title(
            f"One night of LSST: expected, a good night, a bad night   ({baseline} ideal)",
            loc="left",
        )

        # wide side margins: the bar labels and the "N visits · ratio" labels
        # are drawn in data coordinates outside the x limits
        # Two legend rows under the x axis: the Science subdivisions, then the
        # categories that are not Science. Separate legends so each row can carry
        # its own "Science:" / "Lost:" title; the second is added as an artist
        # because an Axes holds only one legend.
        for i, (title, entries) in enumerate(LEGEND_ROWS):
            leg = ax.legend(
                handles=[_legend_handles(style, label) for style, label in entries],
                title=f"{title}:",
                loc="upper left",
                bbox_to_anchor=(0.0, -0.17 - 0.175 * i),
                ncol=len(entries),
                frameon=False,
                fontsize=13,
                handlelength=1.3,
                handleheight=1.1,
                columnspacing=1.6,
                borderpad=0.0,
                borderaxespad=0.0,
            )
            leg.set_title(f"{title}:", prop={"size": 13})
            leg._legend_box.align = "left"
            if i < len(LEGEND_ROWS) - 1:
                ax.add_artist(leg)

        fig.subplots_adjust(left=0.17, right=0.845, bottom=0.30, top=0.90)
        FIG.mkdir(exist_ok=True)
        stem = FIG / f"good_bad_night_{good}_{bad}"
        fig.savefig(f"{stem}.png", dpi=200, transparent=True)
        fig.savefig(f"{stem}_white.png", dpi=200, facecolor="white")
        print("wrote", stem, "[_white].png")

    # the numbers behind the bars, for the README and the slide
    print(f"\nideal night: {night_h:.2f} h, OSF {ideal_osf:.4f}, exposing {ideal_exposing_h:.2f} h")
    print(f"RTN-093 0.7 tick at {ideal_exposing_h * SURVEY_SPEED_CRITERION:.2f} h of exposing")
    for label, _note, blocks, row in bars:
        if row is None:
            continue
        print(f"\n{label}  ({int(row.n_survey)} visits, ratio {row.ratio:.3f})")
        for name, h, _style in blocks:
            if h > 0:
                print(f"  {name:12s} {h:6.3f} h  ({h / night_h * 100:4.1f} %)")
        per_visit = 3600.0 / row.n_survey if row.n_survey else np.nan
        print(
            f"  per survey visit: exposing {row.exposing_h * per_visit:5.1f} s, "
            f"in-visit {row.in_visit_h * per_visit:4.1f} s, "
            f"expected gap {row.gap_expected_h * per_visit:5.1f} s "
            f"(current TMA {row.gap_expected_current_h * per_visit:5.1f} s), "
            f"excess gap {row.gap_excess_h * per_visit:5.1f} s"
        )
        print(
            f"  gap median {row.gap_median_s:.1f} s (req < 5), "
            f"mean {row.gap_mean_s:.1f} s (req < 10), "
            f"{int(row.n_gaps_over_2x_model)} gaps > 2x model"
        )
    return stem


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--good", type=int, default=GOOD_DAY_OBS)
    parser.add_argument("--bad", type=int, default=BAD_DAY_OBS)
    parser.add_argument("--budget-csv", type=Path, default=None)
    args = parser.parse_args()

    budget = load_budget(args.budget_csv)
    baseline = str(budget.baseline.iloc[0])
    make_figure(budget, args.good, args.bad, baseline)


if __name__ == "__main__":
    main()
