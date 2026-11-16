"""Cumulative survey visits through the night (figure B13).

B12 (``make_good_bad_night_figure.py``) shows how much of each night went where;
B13 shows **when**.  For the same two nights - 6 Jul 2026, the selector's
top-ranked clean night, and 8 Jul 2026, the bad night of B11 - it draws the
running count of survey visits against the hours since that night's evening
-12 deg twilight, under two straight reference lines:

* the **simulated survey pace**, (0, 0) to (night length, ``n_vis_ave``), the
  per-night total the v5.3.7 baseline OSF fit predicts;
* the **start-of-survey threshold**, 0.7 of that.

Both references are straight *by construction*: the fit gives a per-night total
only, so this is the night's average pace, not the simulations' instantaneous
rate (see README §5b).  And the RTN-093 0.7 criterion is, as far as we know,
assessed over a stretch of nights rather than per night - on a single-night plot
it is a reference pace, not a pass/fail test.

The x axis is aligned with B12's: both use :mod:`slide_layout`'s side margins in
inches, so the hour ticks of the two stacked figures land on the same pixels.

Inputs are this folder's own cached ``data/visits_slew_*.parquet`` and
``data/night_budget_*.csv``, both written by ``night_budget.py``.  No cross-folder
imports.

Outputs ``../figures/cumulative_visits_<good>_<bad>.png`` and ``_white.png`` at
exactly 9.55 x 2.00 in, 300 dpi, with no title and no legend - the end labels
name the lines, and the slide carries the title.

Run from a set-up kernel shell::

    source /sdf/group/rubin/sw/loadLSST.bash; setup lsst_distrib
    python python/make_cumulative_visits_figure.py
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

from slide_layout import FIG_W, b13_side_margins  # noqa: E402

DATA = ROOT / "data"
FIG = ROOT / "figures"

#: The two nights, the same as B12.
GOOD_DAY_OBS = 20260706
BAD_DAY_OBS = 20260708

#: Survey programs, ``rubin_nights.reference_values.SCIENCE_PROGRAMS`` (0.18.2).
#: Same tuple as ``night_budget.SURVEY_PROGRAMS``; repeated so this script can be
#: read on its own.
SURVEY_PROGRAMS = (
    "BLOCK-365",
    "BLOCK-407",
    "BLOCK-408",
    "BLOCK-416",
    "BLOCK-417",
    "BLOCK-419",
    "BLOCK-421",
)
#: The counts B12 prints; a mismatch means the two figures disagree.
EXPECTED_N = {GOOD_DAY_OBS: 899, BAD_DAY_OBS: 559}

#: RTN-093 survey-start criterion: survey speed > 0.7.
SURVEY_SPEED_CRITERION = 0.7

#: What the longest flat stretch of each night was, named from sources B11/B12
#: already carry: the ROSP-24 blocks in ``data/rosp24_per_night.csv`` and the
#: night-log sweep in ``simonyi_time_loss/data/raw/nightlog_sweep_2026-07.md``.
#: On 6 Jul the cached visits show four ``BLOCK-T668``
#: ``infocus_wavefront_tarts_test`` acquisitions inside the stall, matching the
#: log's "TARTS test abandoned (RA config)"; on 8 Jul the stall is 03:36-03:53
#: UTC, the log's "HV bias tripped 03:30-03:50 UTC (OBS-2010)".
FLAT_STRETCH_CAUSE = {
    GOOD_DAY_OBS: "alignment / TARTS test (BLOCK-T668)",
    BAD_DAY_OBS: "HV bias trip, OBS-2010",
}

#: Line colours, the deck palette as in B12 ("Science" and "Fault + idle").
C_GOOD = "#024243"
C_BAD = "#F5A623"
INK = rp.NEUTRALS["ink"]
GRID = "#D5DDE0"

#: 9.55 in wide, as B12; 2.00 in tall, the box left under it on slide 6.
FIG_H = 2.00

#: The half-width variant (``--half``), for a two-up slide or a column in a note
#: (Bruno, 2026-11-02). Same height, so the aspect goes from 4.8:1 to 2.4:1.
#: At this width the end labels cannot sit beside the axes - the widest is 2.41 in
#: against a 4.78 in figure - so they become an in-axes legend in the empty
#: top-left corner instead (:func:`_draw_corner_legend`), and the axes get nearly
#: the whole width.
FIG_W_HALF = FIG_W / 2
#: Half-width side margins, inches: the y label and tick numbers on the left, and
#: just enough on the right that the last x tick label is not clipped.
HALF_LEFT_IN = 0.60
HALF_RIGHT_IN = 0.12
#: Type sizes for the half-width figure. The plot is half as wide but the same
#: height, so the type cannot shrink with it or it falls under the legible floor;
#: the legend drops to 7.0 pt to keep four rows inside the corner.
PT_LEGEND_HALF = 7.0

#: Type sizes, in real slide points (the figure is placed at 1:1), B12's values.
PT_TICK = 7.5
PT_AXLABEL = 7.5
PT_END = 8.5

#: y axis, fixed so the end labels always have room above 1056.
Y_MAX = 1150
Y_TICKS = (0, 250, 500, 750, 1000)
#: x offset of the end labels, in hours past the end of the night. The widest
#: label, "LSST min criteria (0.7 ideal) · 739 · 62 /h", is 2.41 in at 8.5 pt
#: against ``slide_layout.B13_RIGHT_IN`` = 2.50 in, so the gap has to stay small
#: or the label is clipped at the figure edge.
END_LABEL_DX_H = 0.08
#: Minimum vertical separation between two end labels, in points. Every label is
#: one line now, but the separation is still scaled by the line count so a label
#: carrying a newline keeps its room.
END_LABEL_MIN_SEP_PT = 1.25 * PT_END

RC = {
    "figure.figsize": (FIG_W, FIG_H),
    "font.size": PT_TICK,
    "xtick.labelsize": PT_TICK,
    "ytick.labelsize": PT_TICK,
    "axes.linewidth": 0.6,
    "text.color": INK,
    "axes.labelcolor": INK,
    "axes.edgecolor": rp.NEUTRALS["ink_secondary"],
    "xtick.color": rp.NEUTRALS["ink_secondary"],
    "ytick.color": rp.NEUTRALS["ink_secondary"],
}


def load_inputs(
    visits_path: Path | None = None, budget_path: Path | None = None
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """The most recent cached visits and night budget in ``data/``."""

    def newest(pattern: str, given: Path | None, reader) -> pd.DataFrame:
        if given is None:
            candidates = sorted(DATA.glob(pattern))
            if not candidates:
                raise SystemExit(
                    f"no data/{pattern} - run python/night_budget.py first"
                )
            given = candidates[-1]
        return reader(given)

    visits = newest("visits_slew_*.parquet", visits_path, pd.read_parquet)
    budget = newest("night_budget_*.csv", budget_path, pd.read_csv).set_index("day_obs")
    return visits, budget


def night_curve(
    visits: pd.DataFrame, budget: pd.DataFrame, day_obs: int
) -> tuple[np.ndarray, np.ndarray, float]:
    """Cumulative survey visits for one night, as a step curve.

    x is hours since that night's evening -12 deg twilight, y the running count
    of survey visits completed (one step per ``obs_end``).  The curve is pinned
    to (0, 0) and carried flat to the end of the night, so its last point is the
    night's total at the morning -12 deg crossing.

    ``obs_end_mjd`` in the cached parquet is already UTC (``fetch_visits``
    subtracts TAI-UTC), so no further conversion is applied here.
    """
    t0, t1 = (
        budget.loc[day_obs, "night_start_mjd"],
        budget.loc[day_obs, "night_end_mjd"],
    )
    survey = visits[
        (visits.day_obs == day_obs) & visits.science_program.isin(SURVEY_PROGRAMS)
    ]
    ends = np.sort(survey.obs_end_mjd.to_numpy(dtype=float))
    ends = ends[(ends > t0) & (ends < t1)]
    n = len(ends)
    expected = EXPECTED_N.get(day_obs)
    if expected is not None and n != expected:
        raise SystemExit(
            f"{day_obs}: {n} survey visits inside the night, B12 has {expected}"
        )
    hours = (ends - t0) * 24.0
    night_h = (t1 - t0) * 24.0
    x = np.concatenate(([0.0], hours, [night_h]))
    y = np.concatenate(([0.0], np.arange(1, n + 1), [n]))
    return x, y, night_h


def _place_end_labels(fig, ax, labels: list[tuple[float, str, str, str]]) -> None:
    """Draw the right-hand end labels, nudged apart but never the lines.

    ``labels`` is ``(y_value, text, colour, weight)``.  Neighbours closer than
    :data:`END_LABEL_MIN_SEP_PT` are pushed apart in display space, working from
    the top down, so the two reference labels and the two night labels stay
    readable where curves end close together.  A label with a newline in it is
    two lines tall and claims its neighbours' share of the gap accordingly.
    """
    order = sorted(range(len(labels)), key=lambda i: -labels[i][0])
    fig.canvas.draw()
    to_disp = ax.transData.transform
    from_disp = ax.transData.inverted().transform
    sep_px = END_LABEL_MIN_SEP_PT * fig.dpi / 72.0
    n_lines = [labels[i][1].count("\n") + 1 for i in order]
    y_px = [to_disp((0.0, labels[i][0]))[1] for i in order]
    for k in range(1, len(y_px)):
        # half of each neighbour's height: a two-line label needs the extra line
        gap = sep_px * (n_lines[k - 1] + n_lines[k]) / 2.0
        y_px[k] = min(y_px[k], y_px[k - 1] - gap)
    x_lab = ax.get_xlim()[1] + END_LABEL_DX_H
    for k, i in enumerate(order):
        _y, text, colour, weight = labels[i]
        ax.text(
            x_lab,
            from_disp((0.0, y_px[k]))[1],
            text,
            ha="left",
            va="center",
            fontsize=PT_END,
            color=colour,
            fontweight=weight,
            linespacing=1.15,
            clip_on=False,
        )


def _flat_stretch(x: np.ndarray, y: np.ndarray) -> tuple[float, float, float]:
    """The longest stretch with no survey visit, after the night's first one.

    Returns ``(start_h, end_h, minutes)``.  The lead-in before the first visit is
    excluded: on 8 Jul it is 4.4 h and would swamp every real stall.
    """
    ends = x[1:-1]  # the per-visit steps only
    gaps = np.diff(ends)
    i = int(np.argmax(gaps))
    return float(ends[i]), float(ends[i + 1]), float(gaps[i] * 60.0)


def steady_state_rate(x: np.ndarray, y: np.ndarray) -> tuple[float, float, float]:
    """Visits per hour once the night settled, and when that was.

    "Steady state" is taken to start at the **first visit after the night's
    longest stall** (:func:`_flat_stretch`): on both nights the stall is the last
    interruption, and everything after it is the night running as it meant to.
    The rate is a least-squares fit of the cumulative count against time over
    that stretch, which is what the figure labels and the report both quote; the
    end-to-end rate over the same stretch is returned too, as it is the more
    conservative reading and the two differ by up to 2 % on 8 Jul.

    Returns ``(fit_per_h, end_to_end_per_h, from_h)``.  All three are NaN if the
    stretch holds fewer than two visits.
    """
    ends = x[1:-1]
    _start, from_h, _minutes = _flat_stretch(x, y)
    after = ends >= from_h
    if after.sum() < 2:
        return float("nan"), float("nan"), from_h
    counts = np.arange(1, len(ends) + 1)[after]
    fit = float(np.polyfit(ends[after], counts, 1)[0])
    end_to_end = (counts[-1] - counts[0]) / (ends[after][-1] - ends[after][0])
    return fit, float(end_to_end), from_h


def report(
    curves: dict[int, tuple[np.ndarray, np.ndarray, float]],
    n_vis_ave: int,
    ideal_h: float,
) -> None:
    """The numbers the README and the speaker notes quote."""
    rate = n_vis_ave / ideal_h
    print(f"\nsimulated pace {n_vis_ave} visits over {ideal_h:.3f} h = {rate:.1f} /h")
    print(
        f"LSST min criteria ({SURVEY_SPEED_CRITERION} ideal) "
        f"{round(SURVEY_SPEED_CRITERION * n_vis_ave)} visits"
    )
    for day_obs, (x, y, night_h) in curves.items():
        ends = x[1:-1]
        n = int(y[-1])
        start, end, minutes = _flat_stretch(x, y)
        print(f"\n{day_obs}  ({n} survey visits, night {night_h:.3f} h)")
        print(f"  first survey visit after -12 deg: {ends[0]:.2f} h")
        cause = FLAT_STRETCH_CAUSE.get(day_obs, "")
        print(
            f"  longest flat stretch: {start:.2f} -> {end:.2f} h, {minutes:.0f} min"
            + (f"  ({cause})" if cause else "")
        )
        for h in (2.0, 6.0):
            print(f"  at {h:.0f} h: {int((ends <= h).sum())} vs ideal {int(rate * h)}")
        print(f"  at end: {n} vs ideal {n_vis_ave}  (ratio [{n / n_vis_ave:.2f}])")
        fit, end_to_end, from_h = steady_state_rate(x, y)
        if np.isfinite(fit):
            print(
                f"  steady state (from {from_h:.1f} h, after the stall): "
                f"{fit:.1f} /h least squares, {end_to_end:.1f} /h end to end; "
                f"simulated {rate:.1f} /h  ({fit / rate:.2f} of it)"
            )
        grid = np.linspace(0.0, ideal_h, 20_001)
        cum = np.searchsorted(ends, grid, side="right")
        under = cum < SURVEY_SPEED_CRITERION * n_vis_ave * grid / ideal_h
        print(
            f"  hours spent under the min-criteria line: {under.mean() * ideal_h:.2f} h"
        )


def _grid_clearing_offset(ax, leg, fig, y_ticks=Y_TICKS) -> float:
    """How far to slide ``leg`` down so no row sits on a horizontal gridline.

    The legend handles are short dashed and dotted segments, and a gridline
    crossing one of them reads as part of the dash pattern - on the first draft
    the "LSST min criteria" handle landed within 10 visits of the 1000 line.  A
    small nudge cannot fix it: the rows are ~100 visits apart and the gridlines
    250, so some row is always near one.  This searches downward in small steps
    for the offset whose worst row-to-gridline distance is largest, and returns
    it in data units (negative = down).  Searching rather than hard-coding keeps
    it correct if the type size, the row count or the y ticks change.
    """
    fig.canvas.draw()
    inv = ax.transData.inverted()
    renderer = fig.canvas.get_renderer()
    rows = np.array(
        [
            inv.transform(
                (0, h.get_window_extent(renderer).get_points().mean(axis=0)[1])
            )[1]
            for h in leg.legend_handles
        ]
    )
    grid = np.asarray([t for t in y_ticks if t > 0], dtype=float)
    pitch = float(np.min(np.diff(np.sort(grid)))) if len(grid) > 1 else 250.0
    # one row's half height, so "clear" means the gridline misses the glyph too
    half_row = abs(rows[0] - rows[1]) / 2.0 if len(rows) > 1 else pitch / 4.0
    offsets = np.arange(0.0, -(pitch + 1.0), -pitch / 100.0)
    clearances = [
        np.abs((rows + off)[:, None] - grid[None, :]).min() for off in offsets
    ]
    best = float(offsets[int(np.argmax(clearances))])
    # never push the top row above the axes, nor the bottom row into the curves
    return max(best, -(pitch - half_row))


def _draw_corner_legend(ax, lines: list[dict], fontsize: float) -> None:
    """The four line labels as a legend in the axes' empty top-left corner.

    Used by the half-width figure, where there is no room for end labels beside
    the axes.  The corner is free because every curve starts at (0, 0) and the
    highest of them only reaches ~250 visits by 2 h, so a four-row legend there
    overlaps no data.  Handles are short line segments in each line's own style,
    so legend and curves cannot drift apart; the two night rows stay bold and
    keep their colour, as the end labels do.

    The whole block is then slid down by :func:`_grid_clearing_offset` so that no
    row's handle sits on a horizontal gridline (Bruno, 2026-11-02): a gridline
    through the dashed or dotted handle reads as part of its dash pattern.
    """
    handles = [
        mpl.lines.Line2D(
            [],
            [],
            color=spec["colour"],
            linestyle=spec["linestyle"],
            linewidth=spec["linewidth"],
        )
        for spec in lines
    ]
    leg = ax.legend(
        handles=handles,
        labels=[spec["label"] for spec in lines],
        loc="upper left",
        frameon=False,
        fontsize=fontsize,
        handlelength=1.6,
        handletextpad=0.5,
        labelspacing=0.35,
        borderpad=0.0,
        borderaxespad=0.3,
    )
    for text, spec in zip(leg.get_texts(), lines):
        text.set_color(spec["colour"])
        text.set_fontweight(spec["weight"])

    offset = _grid_clearing_offset(ax, leg, ax.figure)
    if offset:
        # re-anchor in axes coordinates, which is what bbox_to_anchor expects
        y_lo, y_hi = ax.get_ylim()
        leg.set_bbox_to_anchor(
            (0.0, 1.0 + offset / (y_hi - y_lo)), transform=ax.transAxes
        )


def make_figure(
    visits: pd.DataFrame,
    budget: pd.DataFrame,
    good: int,
    bad: int,
    half: bool = False,
) -> tuple[Path, dict]:
    curves = {d: night_curve(visits, budget, d) for d in (good, bad)}
    # The x axis is the good night's -12 deg length, as in B12, where the ideal
    # bar is the longer of the two nights; the simulated pace is that night's.
    ideal_h = float(budget.loc[good, "night_h"])
    n_vis_ave = int(budget.loc[good, "n_vis_ave"])
    threshold = SURVEY_SPEED_CRITERION * n_vis_ave
    # The two reference lines are straight, so their visits/h is just the slope;
    # each night's is its steady-state rate (see steady_state_rate).
    rate = n_vis_ave / ideal_h

    # One spec per line: the curve, the end label and the legend row all come
    # from this, so the figure cannot label a line it did not draw.
    lines = [
        {
            "label": f"simulated pace · {n_vis_ave} · {rate:.0f} /h",
            "y_end": float(n_vis_ave),
            "colour": INK,
            "weight": "normal",
            "linestyle": (0, (4, 2)),
            "linewidth": 0.9,
            "zorder": 2,
            "xy": ([0, ideal_h], [0, n_vis_ave]),
        },
        {
            "label": f"LSST min criteria (0.7 ideal) · {round(threshold)}"
            f" · {SURVEY_SPEED_CRITERION * rate:.0f} /h",
            "y_end": float(threshold),
            "colour": INK,
            "weight": "normal",
            "linestyle": (0, (1, 1.5)),
            "linewidth": 0.8,
            "zorder": 3,
            "xy": ([0, ideal_h], [0, threshold]),
        },
        *[
            {
                "label": f"{pd.Timestamp(str(d)):%-d %b} · {int(curves[d][1][-1])}"
                f" [{curves[d][1][-1] / n_vis_ave:.2f}]"
                f" · {steady_state_rate(*curves[d][:2])[0]:.0f} /h",
                "y_end": float(curves[d][1][-1]),
                "colour": colour,
                "weight": "bold",
                "linestyle": "-",
                "linewidth": 1.3,
                "zorder": z,
                "step": curves[d][:2],
            }
            for d, colour, z in ((good, C_GOOD, 4), (bad, C_BAD, 5))
        ],
    ]

    fig_w = FIG_W_HALF if half else FIG_W
    with mpl.rc_context({**RC, "figure.figsize": (fig_w, FIG_H)}):
        fig, ax = plt.subplots()
        ax.set_axisbelow(True)
        ax.yaxis.grid(True, color=GRID, linewidth=0.4)

        for spec in lines:
            if "step" in spec:
                x, y = spec["step"]
                ax.step(
                    x,
                    y,
                    where="post",
                    linewidth=spec["linewidth"],
                    color=spec["colour"],
                    zorder=spec["zorder"],
                )
            else:
                x, y = spec["xy"]
                ax.plot(
                    x,
                    y,
                    linestyle=spec["linestyle"],
                    linewidth=spec["linewidth"],
                    color=spec["colour"],
                    zorder=spec["zorder"],
                )

        ax.set_xlim(0, ideal_h)
        ax.set_ylim(0, Y_MAX)
        ax.set_xticks(np.arange(0, np.floor(ideal_h) + 1, 2.0))
        ax.set_yticks(Y_TICKS)
        ax.set_xlabel(
            "hours since evening $-12°$ twilight", fontsize=PT_AXLABEL, labelpad=1.5
        )
        ax.set_ylabel("survey visits", fontsize=PT_AXLABEL, labelpad=2.0)
        ax.tick_params(length=2.5, pad=1.5)
        for side in ("top", "right"):
            ax.spines[side].set_visible(False)

        if half:
            fig.subplots_adjust(
                bottom=0.20,
                top=0.97,
                left=HALF_LEFT_IN / fig_w,
                right=1.0 - HALF_RIGHT_IN / fig_w,
            )
            _draw_corner_legend(ax, lines, PT_LEGEND_HALF)
        else:
            fig.subplots_adjust(bottom=0.20, top=0.97, **b13_side_margins())
            _place_end_labels(
                fig,
                ax,
                [
                    (spec["y_end"], spec["label"], spec["colour"], spec["weight"])
                    for spec in lines
                ],
            )

        FIG.mkdir(exist_ok=True)
        stem = FIG / f"cumulative_visits_{good}_{bad}{'_half' if half else ''}"
        fig.savefig(f"{stem}.png", dpi=300, transparent=True)
        fig.savefig(f"{stem}_white.png", dpi=300, facecolor="white")
        plt.close(fig)
        print("wrote", stem, "[_white].png")

    # Only the full-width pass prints: the numbers are identical, and printing
    # them twice in one run would read as though they had been re-measured.
    if not half:
        report(curves, n_vis_ave, ideal_h)
    return stem, curves


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--good", type=int, default=GOOD_DAY_OBS)
    parser.add_argument("--bad", type=int, default=BAD_DAY_OBS)
    parser.add_argument("--visits-parquet", type=Path, default=None)
    parser.add_argument("--budget-csv", type=Path, default=None)
    parser.add_argument(
        "--half",
        action="store_true",
        help="also write the half-width variant, with an in-axes legend",
    )
    args = parser.parse_args()

    visits, budget = load_inputs(args.visits_parquet, args.budget_csv)
    make_figure(visits, budget, args.good, args.bad)
    if args.half:
        make_figure(visits, budget, args.good, args.bad, half=True)


if __name__ == "__main__":
    main()
