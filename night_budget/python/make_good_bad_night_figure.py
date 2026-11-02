"""A good night and a bad night against the LSST ideal night (figure B12).

Three horizontal bars of equal length - the -12 deg observable night - stacked
top to bottom: the LSST ideal night, a real good night and a real bad night.
Each bar is the same block form as slide 3, in ROSP-24 precedence order and in
``rubin_palette.CATEGORY_COLORS``, so the three read as the same accounting:

* **Science**, subdivided: exposing (solid), expected gap + in-visit overhead
  (a lighter tint), excess gap (hatched);
* **Alignment**, **Engineering**, **Fault + idle**, **Weather** (hatched).

The dashed tick on each real bar is the hour at which exposing would end if the
night had met the RTN-093 survey-start criterion, survey speed > 0.7, i.e. at
0.7 of the ideal night's exposing time.

Inputs are this folder's own ``data/night_budget_<min>_<max>.csv``, written by
``night_budget.py``. No cross-folder imports.

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

C = {
    "survey": rp.CATEGORY_COLORS["survey"],
    "focus": rp.CATEGORY_COLORS["focus"],
    "engineering": rp.CATEGORY_COLORS["engineering"],
    "fault_idle": rp.CATEGORY_COLORS["fault_idle"],
    "weather": rp.CATEGORY_COLORS["weather"],
    "ink": rp.NEUTRALS["ink"],
    "ink2": rp.NEUTRALS["ink_secondary"],
    "muted": rp.NEUTRALS["muted"],
    "grid": rp.NEUTRALS["grid"],
}

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


def _draw_block(ax, x: float, y: float, w: float, style: str) -> None:
    """One block: solid, a lighter tint, or a hatch over a tint."""
    if w <= 0:
        return
    base = {
        "survey": C["survey"],
        "survey_light": C["survey"],
        "survey_hatch": C["survey"],
        "focus": C["focus"],
        "engineering": C["engineering"],
        "fault_idle": C["fault_idle"],
        "weather_hatch": C["weather"],
    }[style]
    alpha = {"survey_light": 0.42, "survey_hatch": 0.22, "weather_hatch": 0.30}.get(style, 1.0)
    ax.add_patch(
        mpl.patches.Rectangle(
            (x, y - BAR_H / 2), w, BAR_H, facecolor=base, alpha=alpha, edgecolor="none", zorder=1
        )
    )
    if style.endswith("_hatch"):
        ax.add_patch(
            mpl.patches.Rectangle(
                (x, y - BAR_H / 2),
                w,
                BAR_H,
                facecolor="none",
                edgecolor=base,
                hatch="///",
                linewidth=0,
                alpha=0.55,
                zorder=1.1,
            )
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
            for _name, w, style in blocks:
                _draw_block(ax, x, y, w, style)
                x += w

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
        fig.subplots_adjust(left=0.17, right=0.845, bottom=0.14, top=0.88)
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
