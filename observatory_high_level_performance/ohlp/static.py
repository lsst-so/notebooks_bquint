"""Static (matplotlib) version of the survey speed vs. image quality figure.

Same inputs as :mod:`ohlp.interactive` (the period and nightly tables from
:mod:`ohlp.binning`), reduced to what survives on a small PNG: goal region,
"LSST = 1" star, one point per period with 25-75 % whiskers, the nightly
cloud for windows, and direct labels. Colours come from :mod:`ohlp.style`
(Rubin palette) only.

Weather nights are not removed anywhere: the reference star comes from the
v5.1 baseline simulation, which already includes cloud and downtime losses.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

from . import reference as ref
from .binning import IQ_COLUMNS, period_key
from .style import COLORS, rp, time_colors

__all__ = ["build_static_figure", "save_png"]

#: Shorter y-axis labels for the small static figure (same quantities as IQ_COLUMNS).
Y_LABELS_SHORT = {
    "idiq_aos_cam": "Instr. Delivered Image Quality (iDIQ), arcsec",
    "fwhm_500_zenith": "Delivered FWHM, 500 nm zenith (arcsec)",
    "fwhm_geom": "Delivered FWHM, geometric (arcsec)",
}

#: Fill alpha of each requirement box; the overlap of n boxes shows as 1-(1-a)^n.
BOX_ALPHA = 0.10

MARKER_EARLY = "o"
MARKER_LSST = "s"


def _nights_in_periods(nightly, periods, kind):
    n = nightly[nightly["n_vis"] > 0].copy()
    p_all = periods
    if kind == "window":
        n["t_index"] = np.nan
        for _, r in p_all.iterrows():
            inside = (n["day_obs"] >= r["first_day_obs"]) & (
                n["day_obs"] <= r["last_day_obs"]
            )
            n.loc[inside, "t_index"] = r["t_index"]
        n = n[n["t_index"].notna()].copy()
    else:
        n["period"] = period_key(n["day_obs"], kind)
        n["t_index"] = n["period"].map(p_all.set_index("period")["t_index"])
        n = n[n["t_index"].notna()].copy()
    n["t_index"] = n["t_index"].astype(int)
    return n


def _window_description(r: pd.Series) -> str:
    """``"Early Ops, 24 Oct–30 Nov 2025\n4,708 visits on 29 of 38 nights"``."""
    span = r["label_long"].split("(")[1].split(",")[0]
    return (
        f"{r['label']}, {span}\n{r['n_visits']:,} visits on"
        f" {r['n_nights_with_visits']} of {r['n_nights_calendar']} nights"
    )


def build_static_figure(
    periods: pd.DataFrame,
    nightly: pd.DataFrame,
    iq_col: str = "idiq_aos_cam",
    figsize: tuple[float, float] = (6, 4),
    label_size: float = 12,
    tick_size: float = 10,
    text_size: float = 9,
    transparent: bool = True,
    show_nightly: bool | None = None,
    show_labels: bool | None = None,
    title: str | None = None,
    colors: list[str] | None = None,
    label_offsets: dict[int, tuple[float, float]] | None = None,
    labels_in_legend: bool = False,
    box_legend_loc: str | None = "lower left",
):
    """Return ``(fig, ax)``. Background is transparent unless ``transparent=False``.

    ``show_labels`` controls the direct labels next to each period point. By
    default they are drawn only when there is more than one period; a single
    point is already identified by the legend.

    ``colors`` overrides the per-period colours (one hex per period, in
    ``t_index`` order). By default one period is drawn in the brand teal and
    several periods in the teal ramp, light (first) to dark (latest). Pass
    e.g. ``[rp.TEAL, rp.CATEGORICAL[2]]`` to contrast an Early Ops point (teal)
    with an LSST point (purple); nights and whiskers take the colour of their
    period.

    ``label_offsets`` overrides the direct-label position per ``period`` key as
    an ``(dx, dy)`` offset in points from the point; the sign of each picks the
    text alignment. Periods not listed keep the default placement.

    ``labels_in_legend`` (windows only) moves the period description (date span,
    visits, nights) into the legend entries and draws no direct labels; the
    legend becomes a single column.

    ``box_legend_loc`` places the legend that names the three requirement
    regions (survey start, SRD minimum, SRD design) with their thresholds;
    ``None`` draws no such legend.
    """
    kind = str(periods["period_kind"].iloc[0])
    if show_nightly is None:
        show_nightly = kind == "window"
    yref = ref.Y_REFERENCE[iq_col]
    p_all = periods[periods["n_visits"] > 0]
    p_all = p_all.sort_values("period").reset_index(drop=True)
    # One period: brand teal. Several: the teal ramp, light (first) to dark (latest).
    if colors is None:
        colors = [rp.TEAL] if len(p_all) == 1 else time_colors(len(p_all))
    elif len(colors) < len(p_all):
        raise ValueError(f"colors has {len(colors)} entries for {len(p_all)} periods")
    if labels_in_legend:
        show_labels = False
    elif show_labels is None:
        show_labels = len(p_all) > 1

    with plt.rc_context(
        {
            "font.size": text_size,
            "axes.labelsize": label_size,
            "xtick.labelsize": tick_size,
            "ytick.labelsize": tick_size,
            "axes.titlesize": label_size,
            "text.color": COLORS["ink"],
            "axes.labelcolor": COLORS["ink"],
            "axes.edgecolor": COLORS["ink_secondary"],
            "xtick.color": COLORS["ink_secondary"],
            "ytick.color": COLORS["ink_secondary"],
            "grid.color": COLORS["grid"],
            "axes.linewidth": 0.8,
            "savefig.transparent": transparent,
        }
    ):
        fig, ax = plt.subplots(figsize=figsize, layout="constrained")
        # Tight margins: the PNG is cropped to its contents on save.
        fig.get_layout_engine().set(w_pad=0.02, h_pad=0.02)
        if transparent:
            fig.patch.set_alpha(0)
            ax.patch.set_alpha(0)
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)
        ax.grid(True, lw=0.5, zorder=0)
        ax.set_axisbelow(True)

        # Requirement regions + star ----------------------------------------- #
        # Three nested boxes in one hue and one alpha; where they overlap the
        # shade stacks, so the strictest (SRD design) region reads darkest.
        box_handles = []
        for b in ref.REQUIREMENT_BOXES:
            top = yref["box_tops"][b.key]
            ax.axvspan(
                b.x_min,
                ref.BOX_X_MAX,
                ymin=0,
                ymax=(top - yref["ymin"]) / (yref["ymax"] - yref["ymin"]),
                facecolor=COLORS["goal_region"],
                alpha=BOX_ALPHA,
                edgecolor=COLORS["goal_region"],
                lw=0.8,
                zorder=0.5,
            )
            box_handles.append(
                Patch(
                    facecolor=COLORS["goal_region"],
                    alpha=1 - (1 - BOX_ALPHA) ** (len(box_handles) + 1),
                    edgecolor=COLORS["goal_region"],
                    lw=0.8,
                    label="%s: speed > %.2f, IQ < %.2f″" % (b.label, b.x_min, top),
                )
            )
        if box_legend_loc:
            box_legend = ax.legend(
                handles=box_handles,
                loc=box_legend_loc,
                frameon=False,
                fontsize=text_size,
                labelcolor=COLORS["ink"],
                handlelength=1.4,
                handletextpad=0.5,
                borderaxespad=0.2,
                labelspacing=0.3,
            )
            ax.add_artist(box_legend)
        ax.scatter(
            [ref.VISIT_RATE.star_x],
            [yref["star"]],
            marker="*",
            s=220,
            facecolor=COLORS["star"],
            edgecolor=COLORS["star_edge"],
            lw=0.8,
            zorder=4,
        )
        ax.annotate(
            "LSST = 1",
            (ref.VISIT_RATE.star_x, yref["star"]),
            xytext=(10, 0),
            textcoords="offset points",
            fontsize=text_size,
            color=COLORS["ink"],
            va="center",
        )

        # Nightly cloud ------------------------------------------------------ #
        if show_nightly:
            n = _nights_in_periods(nightly, periods, kind)
            ax.scatter(
                n["ratio"],
                n[f"{iq_col}_med"],
                s=22,
                marker="o",
                facecolor=[colors[i] for i in n["t_index"]],
                alpha=0.35,
                edgecolor=[
                    COLORS["ink_secondary"] if w else "none"
                    for w in n["is_weather_night"]
                ],
                lw=0.7,
                zorder=2,
            )

        # Period points, whiskers, path -------------------------------------- #
        x = p_all["ratio"].to_numpy()
        y = p_all[f"{iq_col}_med"].to_numpy()
        for i, r in p_all.iterrows():
            c = colors[int(r["t_index"])]
            m = MARKER_LSST if r["is_lsst"] else MARKER_EARLY
            a = 0.45 if r["low_n"] else 1.0
            ax.errorbar(
                r["ratio"],
                r[f"{iq_col}_med"],
                # The summed speed can fall outside the nightly IQR (e.g. a
                # quarter of mostly closed nights), so clip whiskers at 0.
                xerr=[
                    [max(r["ratio"] - r["ratio_q25"], 0)],
                    [max(r["ratio_q75"] - r["ratio"], 0)],
                ],
                yerr=[
                    [max(r[f"{iq_col}_med"] - r[f"{iq_col}_q25"], 0)],
                    [max(r[f"{iq_col}_q75"] - r[f"{iq_col}_med"], 0)],
                ],
                fmt="none",
                ecolor=c,
                elinewidth=1,
                alpha=0.5 * a,
                zorder=3,
            )
            ax.scatter(
                r["ratio"],
                r[f"{iq_col}_med"],
                marker=m,
                s=90,
                facecolor=c,
                edgecolor=c,
                alpha=a,
                zorder=5,
            )
        for i in range(len(p_all) - 1):
            c = colors[int(p_all.loc[i + 1, "t_index"])]
            gap = int(p_all.loc[i + 1, "seq"] - p_all.loc[i, "seq"]) > 1
            ax.annotate(
                "",
                xy=(x[i + 1], y[i + 1]),
                xytext=(x[i], y[i]),
                arrowprops=dict(
                    arrowstyle="-|>,head_length=0.5,head_width=0.25",
                    color=c,
                    lw=1.4,
                    ls="--" if gap else "-",
                    shrinkA=6,
                    shrinkB=6,
                ),
                zorder=3,
            )

        # Direct labels ------------------------------------------------------ #
        for i, r in p_all.iterrows() if show_labels else ():
            text = r["label"]
            if kind == "window":
                span = r["label_long"].split("(")[1].split(",")[0]
                text = f"{r['label']}\n{span}"
                text += (
                    f"\n{r['n_visits']:,} visits on {r['n_nights_with_visits']}"
                    f" of {r['n_nights_calendar']} nights"
                )
            elif r["is_lsst"] and not p_all.loc[max(i - 1, 0), "is_lsst"]:
                text += " (LSST start)"
            if kind == "window":
                above = r[f"{iq_col}_med"] >= np.median(y)
                right = len(p_all) < 2 or r["ratio"] <= np.median(x)
            else:  # many close points: alternate above/below along the path
                above = i % 2 == 0
                right = True
            dx, dy = 9 if right else -9, 9 if above else -9
            if label_offsets and int(r["period"]) in label_offsets:
                dx, dy = label_offsets[int(r["period"])]
                right, above = dx >= 0, dy >= 0
            ax.annotate(
                text,
                (r["ratio"], r[f"{iq_col}_med"]),
                xytext=(dx, dy),
                textcoords="offset points",
                fontsize=text_size,
                color=COLORS["ink"],
                ha="left" if right else "right",
                va="bottom" if above else "top",
                zorder=6,
            )

        # Axes --------------------------------------------------------------- #
        ax.set_xlim(0, 1.1)
        ax.set_ylim(yref["ymin"], yref["ymax"])
        ax.set_xlabel("Survey speed: visits acquired / expected")
        ax.set_ylabel(Y_LABELS_SHORT.get(iq_col, IQ_COLUMNS[iq_col]))
        if title:
            ax.set_title(title, color=COLORS["ink"], loc="left", pad=6)

        # Legend ------------------------------------------------------------- #
        mid = colors[len(p_all) // 2]
        early = p_all[~p_all["is_lsst"]]
        lsst = p_all[p_all["is_lsst"]]
        # Few periods (windows): each period is identified by its own colour and
        # the point is a median, so say so. Many periods (quarters, months): the
        # ramp carries time and the legend only tells circles from squares.
        few = len(p_all) <= 2
        handles = []
        if len(early):
            handles.append(
                Line2D(
                    [],
                    [],
                    marker=MARKER_EARLY,
                    color=colors[int(early["t_index"].iloc[0])] if few else mid,
                    ls="",
                    ms=7,
                    label=_window_description(early.iloc[0])
                    if labels_in_legend and kind == "window"
                    else ("Early Ops, median" if few else "Early Ops"),
                )
            )
        if len(lsst):
            handles.append(
                Line2D(
                    [],
                    [],
                    marker=MARKER_LSST,
                    color=colors[int(lsst["t_index"].iloc[0])] if few else colors[-1],
                    ls="",
                    ms=7,
                    label=_window_description(lsst.iloc[0])
                    if labels_in_legend and kind == "window"
                    else ("LSST, median" if few else "LSST"),
                )
            )
        if show_nightly:
            handles.append(
                Line2D(
                    [],
                    [],
                    marker="o",
                    color=COLORS["ink_secondary"] if few and len(p_all) > 1 else mid,
                    alpha=0.4,
                    ls="",
                    ms=5,
                    label="nights",
                )
            )
        ax.legend(
            handles=handles,
            loc="upper right",
            ncol=1 if labels_in_legend else 2,
            labelspacing=0.8 if labels_in_legend else 0.5,
            columnspacing=1.0,
            frameon=False,
            fontsize=text_size,
            labelcolor=COLORS["ink"],
            handletextpad=0.4,
            borderaxespad=0.2,
        )
    return fig, ax


def save_png(fig, path: str | Path, dpi: int = 300, transparent: bool = True) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(
        path, dpi=dpi, transparent=transparent, bbox_inches="tight", pad_inches=0.03
    )
    return path
