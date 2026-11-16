"""A good night and a bad night against the LSST ideal night (figure B12).

Three horizontal bars of equal length - the -12 deg observable night - stacked
top to bottom: the LSST ideal night, a real good night and a real bad night.
Each bar is the same block form as slide 3, in ROSP-24 precedence order and in the
deck's own ``SLIDE2_COLORS`` (as slide-4 B1; see ``PALETTE`` below and README §5),
so the three read as the same accounting:

* **Science**, subdivided: exposing in the Science colour, then expected gap +
  in-visit overhead and excess gap, which share ``GAP_TEAL`` and differ only by
  the hatch on the excess;
* **Alignment**, **Engineering**, **Fault + idle**, **Weather** (hatched).

Every fill is solid - no alpha anywhere - and blocks are parted by white rules and
carry an in-bar ``%`` label where they are wide enough, as on slide-4 B1.

The dashed tick on each real bar is the hour at which exposing would end if the
night had met the RTN-093 survey-start criterion, survey speed > 0.7, i.e. at
0.7 of the ideal night's exposing time.

Inputs are this folder's own ``data/night_budget_<min>_<max>.csv``, written by
``night_budget.py``. No cross-folder imports.

The legend sits in one centred row of seven under the x label, in stack order
(see :data:`LEGEND_ENTRIES`).

Outputs ``../figures/good_bad_night_<good>_<bad>.png`` and ``_white.png`` at
exactly 9.55 x 2.22 in (:data:`FIG_W`, :data:`FIG_H`), 300 dpi, with no title -
the slide carries one, and in a frame this short every line of height counts.

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

from slide_layout import b12_side_margins  # noqa: E402

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

#: The gap blocks need a fifth fill that is not one of the six deck colours. An alpha
#: tint of Science washed out toward the weather grey, which is why the first draft
#: read worse than slide-4 B1: there every block is a *solid* colour. This is the
#: Rubin sequential-teal step (``rubin_palette.SEQUENTIAL_TEAL``) that clears all six
#: deck colours - nearest is Weather at dE 18.3, then Alignment at 24.7.
GAP_TEAL = "#7FC6C7"

C = {
    "survey": PALETTE["Science"],
    "gap": GAP_TEAL,
    "focus": PALETTE["Alignment"],
    "engineering": PALETTE["Engineering"],
    "fault_idle": PALETTE["Fault + idle"],
    "weather": PALETTE["Weather"],
    "ink": rp.NEUTRALS["ink"],
    "ink2": rp.NEUTRALS["ink_secondary"],
    "muted": rp.NEUTRALS["muted"],
    "grid": rp.NEUTRALS["grid"],
}

#: Legend entries, ``(style, label)``, in stack order: the three Science
#: subdivisions first, then the categories that are not Science. One row of seven,
#: not two rows of three and four: inside a 2.22 in frame the two ``Science:`` /
#: ``Lost:`` row titles cost a line of height each and collided with the x label.
#: The labels carry the grouping instead ("exposing" / "... gap" / plain nouns).
LEGEND_ENTRIES = [
    ("survey", "exposing"),
    ("gap_expected", "expected gap"),
    ("gap_excess", "excess gap"),
    ("focus", "Alignment"),
    ("engineering", "Engineering"),
    ("fault_idle", "Fault + idle"),
    ("weather", "Weather"),
]

#: Exact size of the box the figure occupies on the slide (Bruno, 2026-11-02).
#: The width is shared with B13; the side margins are B12's own, and live in
#: :mod:`slide_layout` next to B13's (see that module on why they differ).
#: At this size the figure is placed at ~1:1, so a point here is a point on the
#: slide and the type sizes below are the real on-screen sizes. The frame is wide
#: and *short* - three bars, an axis and two legend rows inside 2.22 in - so every
#: type size is near the 7-8 pt floor and there is no room for a title.
FIG_W, FIG_H = 9.55, 2.22

#: Type sizes, in real slide points. The bar labels are the largest thing here
#: because they are what the audience reads first.
PT_BAR_LABEL = 8.5  # the date on the left of each bar
PT_BAR_NOTE = 7.0  # the one-word note under the date
PT_RIGHT = 8.5  # "899 visits · 0.85"
PT_TICK = 7.5  # x tick numbers
PT_XLABEL = 7.5
PT_LEGEND = 7.5

RC = {
    "figure.figsize": (FIG_W, FIG_H),
    "font.size": PT_LEGEND,
    "xtick.labelsize": PT_TICK,
    "axes.linewidth": 0.6,
    "hatch.linewidth": 0.5,
    "text.color": C["ink"],
    "axes.labelcolor": C["ink"],
    "axes.edgecolor": C["ink2"],
    "xtick.color": C["ink2"],
    "ytick.color": C["ink2"],
}

#: Bar thickness in y units. Bars sit at a pitch of 1.0, so the gap between them
#: is ``1 - BAR_H``: 0.89 leaves 0.11, half the 0.22 it was (Bruno, 2026-11-02),
#: and the bars take up the difference. Thick bars also leave room for the
#: in-bar ``%`` labels.
BAR_H = 0.89


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
        ("overhead", night_h - exposing, "gap_expected"),
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
        ("expected", row.gap_expected_h + row.in_visit_h, "gap_expected"),
        ("excess", row.gap_excess_h, "gap_excess"),
        ("alignment", np.nan_to_num(row.focus_h) + row.nonsurvey_visit_h, "focus"),
        ("engineering", np.nan_to_num(row.engineering_h), "engineering"),
        ("fault_idle", np.nan_to_num(row.fault_idle_h), "fault_idle"),
        ("weather", np.nan_to_num(row.weather_h), "weather"),
    ]
    total = sum(h for _, h, _ in blocks)
    if total > 0:
        scale = row.night_h / total
        blocks = [(name, h * scale, style) for name, h, style in blocks]
    return blocks


#: One spec per block style: ``(colour, hatch, text)``. The blocks and the legend
#: swatches are both drawn from this, so they cannot drift apart. Every fill is
#: **solid** - as in slide-4 B1, where the white separators and white in-bar labels
#: do the separating, not transparency. ``text`` is the in-bar label colour.
#: Expected and excess gap share ``GAP_TEAL`` and differ only by the hatch (Bruno,
#: 2026-11-02); Weather keeps the slide-4 B1 hatch direction.
STYLE = {
    "survey": (C["survey"], None, "white"),
    "gap_expected": (C["gap"], None, C["ink"]),
    "gap_excess": (C["gap"], "///", C["ink"]),
    "focus": (C["focus"], None, "white"),
    "engineering": (C["engineering"], None, "white"),
    "fault_idle": (C["fault_idle"], None, "white"),
    "weather": (C["weather"], "\\\\\\", C["ink"]),
}


#: No in-bar % label below this share of the night - it would not fit. Same idea as
#: ``LABEL_MIN_FRAC`` in slide-4 B1, tuned for a horizontal bar: a label needs about
#: 3 characters ("63%") across the block.
LABEL_MIN_FRAC = 0.055
#: In-bar label size, in real slide points (see :data:`FIG_W`).
LABEL_PT = 7.5


def _draw_block(ax, x: float, y: float, w: float, style: str, zorder: float = 1.0) -> None:
    """One solid block, hatched if its style says so."""
    if w <= 0:
        return
    base, hatch, _text = STYLE[style]
    ax.add_patch(
        mpl.patches.Rectangle(
            (x, y - BAR_H / 2), w, BAR_H, facecolor=base, edgecolor="none", zorder=zorder
        )
    )
    if hatch:
        # the hatch is drawn in white over the solid fill, as in slide-4 B1, so the
        # hatched and unhatched blocks of one colour stay the same weight
        ax.add_patch(
            mpl.patches.Rectangle(
                (x, y - BAR_H / 2),
                w,
                BAR_H,
                facecolor="none",
                edgecolor="white",
                hatch=hatch,
                linewidth=0,
                zorder=zorder + 0.1,
            )
        )


def _label_block(ax, x: float, y: float, w: float, style: str, night_h: float) -> None:
    """The in-bar ``%`` label, where the block is wide enough to hold one."""
    frac = w / night_h
    if frac < LABEL_MIN_FRAC:
        return
    _base, _hatch, text = STYLE[style]
    ax.text(
        x + w / 2,
        y,
        f"{frac * 100:.0f}%",
        ha="center",
        va="center",
        fontsize=LABEL_PT,
        color=text,
        zorder=3,
    )


def _legend_handles(style: str, label: str) -> mpl.patches.Patch:
    """A legend swatch drawn from the same :data:`STYLE` spec as the blocks."""
    base, hatch, _text = STYLE[style]
    return mpl.patches.Patch(
        facecolor=base, hatch=hatch, edgecolor="white" if hatch else "none", label=label
    )


def make_figure(budget: pd.DataFrame, good: int, bad: int, baseline: str) -> Path:
    good_row, bad_row = budget.loc[good], budget.loc[bad]
    # The ideal bar uses the longer of the two nights, so all three bars share
    # one x axis; the seasonal OSF is taken from the good night.
    night_h = max(good_row.night_h, bad_row.night_h)
    ideal_osf = good_row.ideal_osf
    ideal_exposing_h = night_h * ideal_osf

    bars = [
        ("LSST ideal night", f"{baseline} baseline", ideal_bar(night_h, ideal_osf), None),
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
                    linewidth=0.5,
                    zorder=0,
                )
            )
            x = 0.0
            edges = []
            for _name, w, style in blocks:
                _draw_block(ax, x, y, w, style)
                _label_block(ax, x, y, w, style, night_h)
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
                    linewidth=0.8,
                    solid_capstyle="butt",
                    zorder=2,
                )

            # left-hand labels: date, then one word
            ax.text(
                -0.18, y + 0.14, label, ha="right", va="center", fontsize=PT_BAR_LABEL, color=C["ink"]
            )
            if note:
                ax.text(
                    -0.18, y - 0.20, note, ha="right", va="center", fontsize=PT_BAR_NOTE, color=C["ink2"]
                )

            # right-hand label: visits and the ratio to the ideal night
            if row is None:
                n_vis = int(np.floor(ideal_exposing_h * 3600.0 / VISIT_S))
                right = f"{n_vis} visits  ·  1.00"
            else:
                right = f"{int(row.n_survey)} visits  ·  {row.ratio:.2f}"
            ax.text(
                night_h + 0.18, y, right, ha="left", va="center", fontsize=PT_RIGHT, color=C["ink"]
            )

            # RTN-093 tick: where exposing would end at survey speed 0.7
            if row is not None:
                ax.plot(
                    [ideal_exposing_h * SURVEY_SPEED_CRITERION] * 2,
                    [y - BAR_H / 2 - 0.06, y + BAR_H / 2 + 0.06],
                    linestyle=(0, (3, 2)),
                    linewidth=1.0,
                    color=C["ink"],
                    zorder=3,
                )

        ax.set_xlim(0, night_h)
        # tight y limits: half a bar of air above and below, no more. The figure
        # goes on a slide, so empty space costs on-screen size.
        ax.set_ylim(-BAR_H / 2 - 0.06, 2 + BAR_H / 2 + 0.06)
        ax.set_yticks([])
        for side in ("left", "right", "top"):
            ax.spines[side].set_visible(False)
        ax.set_xticks(np.arange(0, np.floor(night_h) + 1, 1.0))
        ax.set_xlabel(
            "hours into the observable night (Sun at $-12°$ → $-12°$)", fontsize=PT_XLABEL, labelpad=1.5
        )
        ax.tick_params(axis="x", length=2, pad=1.5)
        # No title: the slide carries it, and a title here would only add empty
        # space. The baseline is named in the ideal bar's sub-label instead.

        # One legend row under the x label, centred: seven entries in stack order.
        leg = ax.legend(
            handles=[_legend_handles(style, label) for style, label in LEGEND_ENTRIES],
            loc="upper center",
            bbox_to_anchor=(0.5, -0.30),
            ncol=len(LEGEND_ENTRIES),
            frameon=False,
            fontsize=PT_LEGEND,
            handlelength=1.1,
            handleheight=1.0,
            columnspacing=1.0,
            handletextpad=0.4,
            borderpad=0.0,
            borderaxespad=0.0,
        )

        # Side margins hold the bar labels and the "N visits · ratio" labels, which
        # are drawn in data coordinates outside the x limits.
        fig.subplots_adjust(bottom=0.22, top=0.98, **b12_side_margins(FIG_W))
        # Grow the bottom margin until the legend row actually fits: its height
        # depends on the font metrics, so measure rather than guess.
        fig.canvas.draw()
        for _ in range(16):
            if leg.get_window_extent().y0 >= 4:
                break
            fig.subplots_adjust(bottom=ax.get_position().y0 + 0.02)
            fig.canvas.draw()
        FIG.mkdir(exist_ok=True)
        stem = FIG / f"good_bad_night_{good}_{bad}"
        # 300 dpi: the figure is placed at 1:1 on the slide, so this is the real
        # on-screen resolution rather than something that gets scaled down.
        fig.savefig(f"{stem}.png", dpi=300, transparent=True)
        fig.savefig(f"{stem}_white.png", dpi=300, facecolor="white")
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
