"""Downtime annotation layer for the on-sky utilization (visit timeline) figure.

Reads ``downtime_annotations.csv`` (one row per downtime span, dates are
``day_obs`` calendar dates, inclusive) and draws, on an existing matplotlib axes
whose x axis is matplotlib date numbers of 00:00 UTC on ``day_obs``:

* a pale filled band over each span (``severity`` full/partial), behind the data;
* a hatched strip instead of a band for ``severity == "degraded"`` rows;
* a solid, full-saturation strip along the top edge of the axes for every drawn
  span, which is what actually carries the category colour (pale bands alone do
  not separate under colour-vision deficiency);
* staggered labels above the axes with a leader line to the centre of the span;
* a small category legend, added with ``ax.add_artist`` so the visit legend stays;
* a marker for the start of the LSST (``day_obs`` 20260629): a 45 degree ink arrow
  under the x axis pointing up at the first LSST night, caption left of its tail.

Colours are the Rubin palette (``rubin_color_pallete/rubin_palette.py``) slots,
checked at full saturation with the Machado (2009) protanopia/deuteranopia
simulation: every pair has OKLab dE >= 8 except fault/mixed under deuteranopia
(6.7), which is why the label text and the legend are always present.
"""

from __future__ import annotations

import datetime as dt
import textwrap
from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.legend as mlegend
from matplotlib.legend_handler import HandlerBase
import matplotlib.patches as mpatches
import matplotlib.patheffects as mpe
import matplotlib.text as mtext
import matplotlib.transforms as mtransforms
from matplotlib.font_manager import FontProperties
from matplotlib.lines import Line2D
from matplotlib.textpath import TextPath
import numpy as np
import pandas as pd

__all__ = [
    "CATEGORY_COLORS",
    "CATEGORY_ORDER",
    "LSST_START_DAY_OBS",
    "load_downtime",
    "select_spans",
    "annotate_downtime",
    "right_anchor_transform",
    "below_anchor_transform",
    "xaxis_depth_in",
    "legend_height_in",
    "LEGEND_PAD_IN",
    "fit_margins",
    "annotate_downtime_bokeh",
]

#: Rubin palette hues (light surfaces). Keys are the ``category`` column values.
CATEGORY_COLORS: dict[str, str] = {
    "fault": "#DB5451",  # Rubin red
    "weather": "#058B8C",  # Rubin teal
    "planned": "#00630C",  # Rubin green (darkened)
    "mixed": "#CE7F00",  # Rubin orange (darkened)
    "degraded": "#74369E",  # Rubin purple
    "unknown": "#9AA0A0",  # neutral
}
CATEGORY_ORDER: tuple[str, ...] = (
    "fault",
    "weather",
    "planned",
    "mixed",
    "degraded",
    "unknown",
)
CATEGORY_LEGEND_NAMES: dict[str, str] = {
    "fault": "Fault",
    "weather": "Weather",
    "planned": "Planned",
    "mixed": "Weather + fault",
    "degraded": "Degraded (not closed)",
    "unknown": "Unknown",
}
LSST_START_DAY_OBS = 20260629
_INK = "#313333"
#: Gap in inches between the x axis label and a legend placed under it.
LEGEND_PAD_IN = 0.08


def _to_date(x) -> dt.date:
    return pd.Timestamp(x).date()


def load_downtime(csv_path: str | Path) -> pd.DataFrame:
    """Read the CSV, parse dates, add ``n_nights`` (inclusive night count)."""
    df = pd.read_csv(csv_path, dtype=str, keep_default_na=False)
    df["start"] = [_to_date(s) for s in df["start_date"]]
    df["end"] = [_to_date(e) for e in df["end_date"]]
    df["n_nights"] = [(e - s).days + 1 for s, e in zip(df["start"], df["end"])]
    df["category"] = df["category"].str.strip().str.lower()
    df["severity"] = df["severity"].str.strip().str.lower()
    return df


def select_spans(
    df: pd.DataFrame,
    first_night: dt.date,
    last_night: dt.date,
    min_duration_days: int = 1,
    categories=None,
    label_categories=None,
    include_unknown: bool = False,
    label_flag: str | None = None,
) -> pd.DataFrame:
    """Apply the drawing rules and return ``df`` with ``skip_reason`` and ``labelled``.

    Rows are skipped when they do not touch ``[first_night, last_night]``, when
    their category is not selected, when they are shorter than
    ``min_duration_days`` nights, or when they are single-night weather. The
    ``labelled`` column says whether the row also gets a text label: its category
    must be in ``label_categories`` and, if ``label_flag`` names a 0/1 CSV column
    (for example ``"talk"``), that column must be ``1`` for the row.
    """
    if categories is None:
        categories = [c for c in CATEGORY_ORDER if c != "unknown"]
        if include_unknown:
            categories.append("unknown")
    categories = [c.lower() for c in categories]
    if label_categories is None:
        label_categories = categories
    label_categories = {c.lower() for c in label_categories}

    out = df.copy()
    reasons = []
    for _, r in out.iterrows():
        if r["end"] < first_night or r["start"] > last_night:
            reasons.append("outside x range")
        elif r["category"] not in categories:
            reasons.append("category not selected")
        elif r["n_nights"] < min_duration_days:
            reasons.append(f"shorter than {min_duration_days} nights")
        elif r["category"] == "weather" and r["n_nights"] < 2:
            reasons.append("single-night weather")
        else:
            reasons.append("")
    out["skip_reason"] = reasons
    out["labelled"] = out["category"].isin(label_categories) & (
        out["skip_reason"] == ""
    )
    if label_flag is not None:
        if label_flag not in out.columns:
            raise KeyError(f"column {label_flag!r} not in the downtime CSV")
        out["labelled"] &= out[label_flag].astype(str).str.strip() == "1"
    return out


def _x(date: dt.date) -> float:
    """Matplotlib date number of 00:00 UTC on a day_obs calendar date."""
    return mdates.date2num(dt.datetime(date.year, date.month, date.day))


def _assign_levels(centers, half_widths, pad):
    """Greedy staggering: lowest level where a label does not overlap its neighbours."""
    order = np.argsort(centers)
    levels = np.zeros(len(centers), dtype=int)
    right_edge: list[float] = []  # per level, right edge of the last label placed
    for i in order:
        left = centers[i] - half_widths[i]
        for lvl, edge in enumerate(right_edge):
            if left > edge + pad:
                levels[i] = lvl
                right_edge[lvl] = centers[i] + half_widths[i]
                break
        else:
            levels[i] = len(right_edge)
            right_edge.append(centers[i] + half_widths[i])
    return levels


def right_anchor_transform(ax):
    """Transform whose (x, y) are inches right of / above the axes top-right corner.

    Use it as ``bbox_transform`` of legends stacked to the right of the plot so the
    stack keeps its position and spacing when the axes are resized afterwards.
    """
    fig = ax.figure
    return fig.dpi_scale_trans + mtransforms.ScaledTranslation(1, 1, ax.transAxes)


def below_anchor_transform(ax):
    """Transform whose x is axes fraction and y is inches above the axes bottom edge.

    Negative y is below the axes. Use it as ``bbox_transform`` of legends placed
    under the x axis so they keep their distance when the axes are resized.
    """
    fig = ax.figure
    return mtransforms.blended_transform_factory(
        ax.transAxes,
        fig.dpi_scale_trans + mtransforms.ScaledTranslation(0, 0, ax.transAxes),
    )


def xaxis_depth_in(ax) -> float:
    """Inches from the axes bottom edge to the bottom of the x tick labels and label."""
    fig = ax.figure
    fig.canvas.draw()
    bb = ax.xaxis.get_tightbbox(fig.canvas.get_renderer())
    if bb is None:
        return 0.0
    axes_bottom = ax.transAxes.transform((0, 0))[1]
    return (axes_bottom - bb.y0) / fig.dpi


def legend_height_in(legend) -> float:
    """Height of a drawn legend in inches (draws the figure first)."""
    fig = legend.figure
    fig.canvas.draw()
    return legend.get_window_extent(fig.canvas.get_renderer()).height / fig.dpi


def _digit_ink_center_pt(text: str, fontsize: float, weight: str = "bold") -> float:
    """Vertical centre of the glyph ink of ``text`` relative to the baseline, in points.

    Digits have no descender, so centring their font box (``va="center"``) puts
    them visibly high. Placing the baseline at ``y_center - this`` centres the ink.
    """
    path = TextPath((0, 0), text, size=fontsize, prop=FontProperties(weight=weight))
    bb = path.get_extents()
    return 0.5 * (bb.y0 + bb.y1)


class _NumberedHandler(HandlerBase):
    """Legend handle: a coloured chip with a white number, like the strip."""

    def __init__(self, number: int, color: str, fontsize: float):
        super().__init__()
        self.number = number
        self.color = color
        self.fontsize = fontsize

    def create_artists(
        self, legend, orig_handle, xdescent, ydescent, width, height, fontsize, trans
    ):
        rect = mpatches.Rectangle(
            (-xdescent, -ydescent),
            width,
            height,
            facecolor=self.color,
            edgecolor="none",
            transform=trans,
        )
        # The handle DrawingArea works in points (its transform scales to pixels).
        ink_center = _digit_ink_center_pt(str(self.number), self.fontsize)
        txt = mtext.Text(
            -xdescent + width / 2,
            -ydescent + height / 2 - ink_center,
            str(self.number),
            ha="center",
            va="baseline",
            fontsize=self.fontsize,
            fontweight="bold",
            color="white",
            transform=trans,
        )
        return [rect, txt]


def annotate_downtime(
    ax,
    csv_path: str | Path,
    *,
    min_duration_days: int = 1,
    categories=None,
    label_categories=None,
    label_flag: str | None = None,
    include_unknown: bool = False,
    label_mode: str = "text",
    band_alpha: float = 0.22,
    label_fontsize: float = 11,
    strip_height: float | None = None,
    strip_overlap: float | None = None,
    level_step: float | None = None,
    leader_color: str = _INK,
    legend_loc: str = "below",
    legend_pad: float = LEGEND_PAD_IN,
    legend_offset_in: float = 0.0,
    legend_gap: float = 0.1,
    legend_columns: tuple[float, ...] = (0.25, 0.5, 0.75),
    legend_wrap: int = 23,
    legend_separators: bool = True,
    legend_fontsize: float = 11,
    lsst_start: int | None = LSST_START_DAY_OBS,
    adjust_layout: bool = True,
) -> dict:
    """Draw the downtime annotation layer on ``ax``.

    All annotation geometry outside the axes (identity strips, label rows, the
    legends) is expressed in **inches** relative to the axes edges, so it does
    not change when the axes are resized afterwards. This is what lets
    :func:`fit_margins` tighten the figure after the call.

    Parameters
    ----------
    ax
        Axes of the visit timeline. x must be matplotlib date numbers of 00:00 UTC
        on ``day_obs``; each night occupies ``[x - 0.5, x + 0.5]``.
    csv_path
        ``downtime_annotations.csv``.
    min_duration_days
        Rows with fewer nights (inclusive, ``end - start + 1``) are not drawn.
        Independently, weather rows of a single night are always skipped.
    categories
        Iterable of ``category`` values to draw. ``None`` means every category
        except ``unknown`` (set ``include_unknown=True`` to add it).
    label_categories
        Iterable of ``category`` values that also get a label. ``None`` labels
        every drawn category. Categories drawn without a label still get their
        band, strip and legend entry.
    label_flag
        Name of a 0/1 CSV column; when given, only rows with ``1`` there are
        labelled. ``"talk"`` marks the spans curated for the RASAB 2026 slide.
    label_mode
        ``"text"``: staggered text labels above the plot with leader lines.
        ``"numbers"``: labelled spans get a chronological number drawn inside
        their strip (the strip is widened to fit it) and a second legend that
        lists ``number  label``; nothing is drawn above the strips.
    band_alpha
        Alpha of the pale extent band (drawn behind the data). Partial-severity
        rows use half of it.
    strip_height, strip_overlap, level_step
        Height of the identity strip, how far it reaches down into the axes
        (default 0: the strip stops at the axes top edge, and the axes frame is
        drawn over that shared edge), and spacing of the label rows, all in
        inches. The other defaults scale with ``label_fontsize`` (strip 0.5 or,
        in numbers mode, 1.25 times the font height; label rows 1.6 font heights).
    legend_loc, legend_pad, legend_offset_in, legend_gap, legend_fontsize
        ``"below"`` puts a one-row category legend under the x axis label, at
        ``legend_pad`` inches from it. ``"right"`` stacks the category legend and
        (in numbers mode) the numbered legend to the right of the axes, starting
        ``legend_offset_in`` inches below the axes top (leave room for a legend
        you placed there yourself) with ``legend_gap`` inches between them.
        ``"bottom"`` lays the legends out in columns under the x axis label, at
        ``legend_pad`` inches from it: the category legend at the first x of
        ``legend_columns`` (axes fraction) and, in numbers mode, the numbered
        list split evenly over the remaining columns. The default columns leave
        the first quarter free for the visit legend placed by the caller at the
        same depth (see ``below_anchor_transform`` and ``xaxis_depth_in``). Any
        matplotlib ``loc`` puts the category legend inside the axes.
    legend_wrap
        Wrap numbered-legend labels longer than this many characters.
    legend_separators
        With ``legend_loc="right"``, draw a thin grey line in the middle of each
        gap of the legend stack (also above the first downtime legend when
        ``legend_offset_in > 0``, i.e. below a legend you placed there yourself).
    lsst_start
        ``day_obs`` of the first LSST night (vertical marker), or ``None``.
    adjust_layout
        Move the top and bottom margins so the labels and the legend fit inside
        the figure (a coarse step; call :func:`fit_margins` for a tight result).

    Returns
    -------
    dict
        ``rows`` (the drawn rows as a DataFrame with ``level``, ``-1`` for
        unlabelled rows, and ``number``, 0 for unnumbered rows), ``n_levels``,
        ``legend`` (the category legend), ``legends`` (all legends added, in
        stacking order) and ``skipped`` (rows filtered out, with the reason).
    """
    if label_mode not in ("text", "numbers"):
        raise ValueError(f"label_mode must be 'text' or 'numbers', got {label_mode!r}")
    numbers = label_mode == "numbers"
    font_in = label_fontsize / 72.0
    if strip_height is None:
        strip_height = (1.25 if numbers else 0.5) * font_in
    if strip_overlap is None:
        strip_overlap = 0.0
    if level_step is None:
        level_step = 1.6 * font_in

    df = load_downtime(csv_path)
    x0, x1 = ax.get_xlim()
    first_night = mdates.num2date(x0 + 0.5).date()
    last_night = mdates.num2date(x1 - 0.5).date()
    df = select_spans(
        df,
        first_night,
        last_night,
        min_duration_days=min_duration_days,
        categories=categories,
        label_categories=label_categories,
        include_unknown=include_unknown,
        label_flag=label_flag,
    )
    drawn = df[df["skip_reason"] == ""].copy().reset_index(drop=True)
    skipped = df[df["skip_reason"] != ""][
        ["start_date", "end_date", "label", "category", "skip_reason"]
    ]
    drawn = drawn.sort_values("start").reset_index(drop=True)
    drawn["number"] = 0
    if numbers:
        drawn.loc[drawn["labelled"], "number"] = np.arange(
            1, int(drawn["labelled"].sum()) + 1
        )

    fig = ax.figure
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    inv = ax.transData.inverted()
    # x in data units, y in inches above the axes top edge (follows later resizes).
    above_tr = mtransforms.blended_transform_factory(
        ax.transData,
        fig.dpi_scale_trans + mtransforms.ScaledTranslation(0, 1, ax.transAxes),
    )
    # x in axes fraction, y in inches above the axes bottom edge (negative = below).
    below_tr = below_anchor_transform(ax)
    has_degraded = bool((drawn["severity"] == "degraded").any())
    y_strip_top = strip_height * (2 if has_degraded else 1)

    def _text_width_data(text, fontsize, weight="normal"):
        t = ax.text(0, 0, text, fontsize=fontsize, fontweight=weight, alpha=0)
        bb = t.get_window_extent(renderer)
        t.remove()
        return inv.transform((bb.x1, 0))[0] - inv.transform((bb.x0, 0))[0]

    # 1. Extent bands (behind everything) and identity strips (above the axes top).
    for _, r in drawn.iterrows():
        color = CATEGORY_COLORS.get(r["category"], CATEGORY_COLORS["unknown"])
        xs, xe = _x(r["start"]) - 0.5, _x(r["end"]) + 0.5
        if r["severity"] == "degraded":
            ax.add_patch(
                mpatches.Rectangle(
                    (xs, strip_height),
                    xe - xs,
                    strip_height,
                    transform=above_tr,
                    facecolor="none",
                    edgecolor=color,
                    hatch="////",
                    linewidth=1.0,
                    clip_on=False,
                    zorder=3,
                )
            )
            continue
        alpha = band_alpha * (0.5 if r["severity"] == "partial" else 1.0)
        ax.axvspan(xs, xe, facecolor=color, alpha=alpha, linewidth=0, zorder=0.6)
        sx, se = xs, xe
        if r["number"]:
            # Widen the strip so the number fits with a small padding on each side.
            need = _text_width_data(str(r["number"]), label_fontsize, "bold") + 2 * (
                0.3
                * font_in
                * (x1 - x0)
                / (ax.get_window_extent(renderer).width / fig.dpi)
            )
            if se - sx < need:
                c = 0.5 * (sx + se)
                sx, se = c - need / 2, c + need / 2
                if sx < x0:
                    sx, se = x0, x0 + need
                if se > x1:
                    sx, se = x1 - need, x1
        ax.add_patch(
            mpatches.Rectangle(
                (sx, -strip_overlap),
                se - sx,
                strip_height + strip_overlap,
                transform=above_tr,
                facecolor=color,
                edgecolor="white",
                linewidth=0.6,
                clip_on=False,
                zorder=0.7,  # under the twilight bars (1) and the spines (2.5)
            )
        )
        if r["number"]:
            ink_center_in = (
                _digit_ink_center_pt(str(r["number"]), label_fontsize) / 72.0
            )
            ax.text(
                0.5 * (sx + se),
                0.5 * strip_height - ink_center_in,
                str(r["number"]),
                transform=above_tr,
                ha="center",
                va="baseline",
                fontsize=label_fontsize,
                fontweight="bold",
                color="white",
                clip_on=False,
                zorder=3.4,
            )

    # 2. Text labels (text mode only): measure, stagger, place, connect.
    labelled = drawn[drawn["labelled"]]
    n_levels = 0
    drawn["level"] = -1
    if not numbers and len(labelled):
        centers, halves, texts = [], [], []
        for _, r in labelled.iterrows():
            xs, xe = _x(r["start"]) - 0.5, _x(r["end"]) + 0.5
            cx = 0.5 * (max(xs, x0) + min(xe, x1))
            t = ax.text(
                cx,
                y_strip_top + 0.3 * level_step,
                r["label"],
                transform=above_tr,
                ha="center",
                va="bottom",
                fontsize=label_fontsize,
                color=_INK,
                clip_on=False,
                zorder=4,
                bbox=dict(facecolor="white", edgecolor="none", pad=1.5),
            )
            bb = t.get_window_extent(renderer)
            w_data = inv.transform((bb.x1, 0))[0] - inv.transform((bb.x0, 0))[0]
            centers.append(cx)
            halves.append(0.5 * w_data)
            texts.append(t)
        centers = np.asarray(centers)
        halves = np.asarray(halves)
        pos = np.clip(centers, x0 + halves, x1 - halves)  # keep labels inside
        pad = 0.015 * (x1 - x0)
        levels = _assign_levels(pos, halves, pad)
        n_levels = int(levels.max()) + 1
        for t, cx, px, lvl in zip(texts, centers, pos, levels):
            y_text = y_strip_top + 0.3 * level_step + lvl * level_step
            t.set_position((px, y_text))
            y_knee = y_text - 0.12 * level_step
            ax.plot(
                [cx, cx, px],
                [y_strip_top, y_knee, y_knee],
                transform=above_tr,
                color=leader_color,
                linewidth=0.8,
                clip_on=False,
                zorder=3.5,
                solid_capstyle="round",
            )
        drawn.loc[labelled.index, "level"] = levels

    # 3. LSST start marker: a 45 degree arrow under the x axis whose head touches
    # the axes at the centre of the first LSST night and whose tail sits down-left
    # of it, below the tick labels, with the caption on one line left of the tail.
    # The head is anchored in data x so it stays on the night when the axes are
    # resized later; tail and caption are point offsets from it. The legends
    # (bottom mode) are placed below it.
    lsst_depth = 0.0  # inches below the axes used by the marker
    if lsst_start is not None:
        d = _to_date(pd.Timestamp(str(lsst_start)))
        xc = _x(d)  # night centre, where its visit ticks are drawn
        if x0 <= xc <= x1:
            data_in = mtransforms.blended_transform_factory(
                ax.transData,
                fig.dpi_scale_trans + mtransforms.ScaledTranslation(0, 0, ax.transAxes),
            )
            ax_bb = ax.get_window_extent(renderer)
            tick_bbs = [
                t.get_window_extent(renderer)
                for t in ax.get_xticklabels()
                if t.get_visible() and t.get_text()
            ]
            tick_depth = (
                max(ax_bb.y0 - bb.y0 for bb in tick_bbs) / fig.dpi if tick_bbs else 0.0
            )
            # Tail below the tick labels, far enough that the caption (centred on
            # the tail) clears them too.
            dy = tick_depth + 0.04 + 0.6 * font_in
            ax.annotate(
                "",
                xy=(xc, -0.01),
                xycoords=data_in,
                xytext=(-dy * 72, -dy * 72),
                textcoords="offset points",
                arrowprops=dict(
                    arrowstyle="-|>,head_length=0.5,head_width=0.25",
                    color=_INK,
                    linewidth=1.8,
                    shrinkA=0,
                    shrinkB=0,
                    path_effects=[
                        mpe.Stroke(linewidth=5.0, foreground="white"),
                        mpe.Normal(),
                    ],
                ),
                annotation_clip=False,
                zorder=4,
            )
            caption = ax.annotate(
                "Start of the LSST",
                xy=(xc, -0.01),
                xycoords=data_in,
                xytext=(-(dy + 0.04) * 72, -dy * 72),
                textcoords="offset points",
                ha="right",
                va="center",
                fontsize=label_fontsize,
                fontweight="bold",
                color=_INK,
                annotation_clip=False,
                zorder=4,
            )
            lsst_depth = (ax_bb.y0 - caption.get_window_extent(renderer).y0) / fig.dpi

    # 4. Legends. Category colours first, then (numbers mode) the numbered list.
    handles = []
    for cat in CATEGORY_ORDER:
        if cat not in set(drawn["category"]):
            continue
        color = CATEGORY_COLORS[cat]
        if cat == "degraded":
            h = mpatches.Patch(
                facecolor="none",
                edgecolor=color,
                hatch="////",
                label=CATEGORY_LEGEND_NAMES[cat],
            )
        else:
            h = mpatches.Patch(
                facecolor=color, edgecolor="none", label=CATEGORY_LEGEND_NAMES[cat]
            )
        handles.append(h)
    legends = []
    legend = None
    legend_depth = 0.0  # inches below the axes used by x axis + legend
    right_tr = right_anchor_transform(ax)
    right_pad = 0.12
    y_right = legend_offset_in
    bottom_offset = max(xaxis_depth_in(ax), lsst_depth) + legend_pad
    if handles:
        kw = dict(
            fontsize=legend_fontsize,
            title_fontsize=legend_fontsize,
            framealpha=0.95,
        )
        if legend_loc == "below":
            offset = bottom_offset
            legend_depth = offset + 1.6 * legend_fontsize / 72.0
            kw.update(
                loc="upper center",
                bbox_to_anchor=(0.5, -offset),
                bbox_transform=below_tr,
                ncol=len(handles) + 1,
                frameon=False,
                title=None,
                borderaxespad=0.0,
                columnspacing=1.2,
            )
            handles = [
                mpatches.Patch(facecolor="none", edgecolor="none", label="Downtime:")
            ] + handles
        elif legend_loc in ("right", "bottom"):
            anchor = (
                (right_pad, -y_right)
                if legend_loc == "right"
                else (legend_columns[0], -bottom_offset)
            )
            kw.update(
                loc="upper left",
                bbox_to_anchor=anchor,
                bbox_transform=right_tr if legend_loc == "right" else below_tr,
                frameon=False,
                title="Downtime",
                alignment="left",
                borderaxespad=0.0,
                borderpad=0.2,
                handlelength=1.6,
                labelspacing=0.3,
            )
        else:
            kw.update(loc=legend_loc, title="Downtime")
        legend = mlegend.Legend(ax, handles, [h.get_label() for h in handles], **kw)
        ax.add_artist(legend)
        legend.set_clip_on(False)  # add_artist clips to the axes; keep it in the bbox
        legends.append(legend)
        if legend_loc == "right":
            y_right += legend_height_in(legend) + legend_gap

    if numbers and len(labelled):
        num_handles, num_labels, handler_map = [], [], {}
        for _, r in drawn[drawn["number"] > 0].iterrows():
            h = mpatches.Patch(facecolor="none", edgecolor="none")
            num_handles.append(h)
            num_labels.append("\n".join(textwrap.wrap(r["label"], legend_wrap)))
            handler_map[h] = _NumberedHandler(
                int(r["number"]),
                CATEGORY_COLORS.get(r["category"], CATEGORY_COLORS["unknown"]),
                0.9 * legend_fontsize,
            )
        kw = dict(
            fontsize=legend_fontsize,
            frameon=False,
            handler_map=handler_map,
            handlelength=1.6,
            handleheight=1.2,
            handletextpad=0.6,
            labelspacing=0.9,
            borderaxespad=0.0,
            borderpad=0.2,
        )
        # One legend per column: a single legend in "bottom" mode, otherwise the
        # numbered list is split evenly over the columns after the category legend.
        chunks = [(num_handles, num_labels, None)]
        if legend_loc == "right":
            kw.update(
                loc="upper left",
                bbox_to_anchor=(right_pad, -y_right),
                bbox_transform=right_tr,
            )
        elif legend_loc == "bottom":
            cols = list(legend_columns[1:]) or [legend_columns[0] + 0.25]
            per_col = int(np.ceil(len(num_handles) / len(cols)))
            chunks = [
                (num_handles[i : i + per_col], num_labels[i : i + per_col], x)
                for i, x in zip(range(0, len(num_handles), per_col), cols)
            ]
            kw.update(loc="upper left", bbox_transform=below_tr)
        else:
            kw.update(loc="lower right")
        for hs, ls, x in chunks:
            if x is not None:
                kw["bbox_to_anchor"] = (x, -bottom_offset)
            num_legend = mlegend.Legend(ax, hs, ls, **kw)
            ax.add_artist(num_legend)
            num_legend.set_clip_on(False)
            legends.append(num_legend)

    if legend_loc == "bottom" and legends:
        fig.canvas.draw()
        renderer = fig.canvas.get_renderer()
        axes_bottom = ax.transAxes.transform((0, 0))[1]
        legend_depth = max(
            (axes_bottom - L.get_window_extent(renderer).y0) / fig.dpi for L in legends
        )

    if legend_loc == "right" and legend_separators and legends:
        # One thin line in the middle of each gap above a downtime legend.
        fig.canvas.draw()
        renderer = fig.canvas.get_renderer()
        stack = ([ax.get_legend()] if ax.get_legend() is not None else []) + legends
        width_in = max(L.get_window_extent(renderer).width / fig.dpi for L in stack)
        ax_top_px = ax.transAxes.transform((1, 1))[1]
        for L in legends:
            top_in = (L.get_window_extent(renderer).y1 - ax_top_px) / fig.dpi
            if top_in > -legend_gap / 2:  # nothing above this legend
                continue
            y_sep = top_in + legend_gap / 2
            fig.add_artist(
                Line2D(
                    [right_pad, right_pad + width_in],
                    [y_sep, y_sep],
                    transform=right_tr,
                    color="#BFC4C7",
                    linewidth=0.8,
                    solid_capstyle="butt",
                )
            )

    if adjust_layout:
        W, H = fig.get_size_inches()
        sp = fig.subplotpars
        needed_top = y_strip_top + (n_levels + 0.4) * level_step + 0.05
        if numbers:
            needed_top = y_strip_top + 0.05
        top = min(sp.top, 1.0 - needed_top / H)
        bottom = max(sp.bottom, (legend_depth + 0.05) / H)
        if bottom < top:
            fig.subplots_adjust(top=top, bottom=bottom)

    return {
        "rows": drawn,
        "n_levels": n_levels,
        "legend": legend,
        "legends": legends,
        "skipped": skipped,
    }


def fit_margins(fig, pad=0.03, iterations: int = 4) -> None:
    """Move the subplot margins so that everything drawn fills the figure.

    Measures the tight bounding box of the whole figure (axes, tick labels, axis
    labels, legends, and the annotation artists drawn outside the axes) and
    shifts ``left``, ``right``, ``bottom`` and ``top`` so that the box sits
    ``pad`` inches from each edge of the figure. ``pad`` is one number for all
    sides or a dict with any of the keys ``left``, ``right``, ``bottom``, ``top``
    (missing keys fall back to ``pad["default"]`` or 0). The figure size is
    unchanged, so the output keeps the requested slide dimensions. Iterates
    because tick label positions move with the axes.
    """
    if not isinstance(pad, dict):
        pad = {"default": float(pad)}
    d = pad.get("default", 0.0)
    pl, pr = pad.get("left", d), pad.get("right", d)
    pb, pt = pad.get("bottom", d), pad.get("top", d)
    W, H = fig.get_size_inches()
    for _ in range(iterations):
        fig.canvas.draw()
        bb = fig.get_tightbbox(fig.canvas.get_renderer())  # inches
        sp = fig.subplotpars
        left = sp.left - (bb.x0 - pl) / W
        right = sp.right + (W - pr - bb.x1) / W
        bottom = sp.bottom - (bb.y0 - pb) / H
        top = sp.top + (H - pt - bb.y1) / H
        if not (0 <= left < right <= 1 and 0 <= bottom < top <= 1):
            break
        fig.subplots_adjust(left=left, right=right, bottom=bottom, top=top)


# --------------------------------------------------------------------------- #
# Bokeh counterpart                                                            #
# --------------------------------------------------------------------------- #

_DAY_MS = 86_400_000.0


def _x_ms(date: dt.date) -> float:
    """Milliseconds since the epoch of 00:00 UTC on a day_obs calendar date."""
    return pd.Timestamp(date, tz="UTC").value / 1e6


def annotate_downtime_bokeh(
    p,
    csv_path: str | Path,
    *,
    day_obs_min: int,
    day_obs_max: int,
    y_top: float,
    min_duration_days: int = 1,
    categories=None,
    label_categories=None,
    label_flag: str | None = None,
    include_unknown: bool = False,
    band_alpha: float = 0.22,
    label_font_size: str = "11px",
    strip_height: float = 0.25,
    level_step: float = 0.6,
    lsst_start: int | None = LSST_START_DAY_OBS,
    frame_width_px: float | None = None,
) -> dict:
    """Bokeh version of :func:`annotate_downtime` for the interactive notebook.

    The figure ``p`` must have a datetime x axis with one night per calendar day
    centred on 00:00 UTC of ``day_obs`` (as in ``on_sky_utilization_interactive``)
    and a ``Range1d`` y range. The annotation area is carved out **above**
    ``y_top`` (the top of the data area, in y data units): the y range is extended
    so the identity strips and the staggered labels fit, a thin line marks
    ``y_top``. Bands and strips are glyph renderers so they can carry a hover
    tooltip with the CSV row (label, dates, category, FRACAS, notes). A second,
    horizontal legend with the category colours is added below the plot.

    ``strip_height`` and ``level_step`` are in y data units (hours). Label widths
    are estimated from the text length (Bokeh cannot measure text server side),
    using ``frame_width_px`` (defaults to ``p.width - 110``).

    Returns the same dict as :func:`annotate_downtime` (``rows``, ``n_levels``,
    ``legend``, ``skipped``).
    """
    from bokeh.models import (
        ColumnDataSource,
        HoverTool,
        Label,
        LabelSet,
        Legend,
        LegendItem,
        Span,
    )

    first_night = pd.Timestamp(str(day_obs_min)).date()
    last_night = pd.Timestamp(str(day_obs_max)).date()
    df = select_spans(
        load_downtime(csv_path),
        first_night,
        last_night,
        min_duration_days=min_duration_days,
        categories=categories,
        label_categories=label_categories,
        include_unknown=include_unknown,
        label_flag=label_flag,
    )
    drawn = df[df["skip_reason"] == ""].copy().reset_index(drop=True)
    skipped = df[df["skip_reason"] != ""][
        ["start_date", "end_date", "label", "category", "skip_reason"]
    ]
    x0 = _x_ms(first_night) - _DAY_MS
    x1 = _x_ms(last_night) + _DAY_MS
    y_bottom = p.y_range.start - 1.0

    def _source(sub):
        return ColumnDataSource(
            dict(
                left=[_x_ms(d) - _DAY_MS / 2 for d in sub["start"]],
                right=[_x_ms(d) + _DAY_MS / 2 for d in sub["end"]],
                label=sub["label"].tolist(),
                start_date=sub["start_date"].tolist(),
                end_date=sub["end_date"].tolist(),
                n_nights=sub["n_nights"].tolist(),
                category=sub["category"].tolist(),
                severity=sub["severity"].tolist(),
                confidence=sub["confidence"].tolist(),
                fracas=[f or "-" for f in sub["fracas"]],
                notes=[n or "-" for n in sub["notes"]],
            )
        )

    band_renderers, strip_renderers, legend_items = [], [], []
    for cat in CATEGORY_ORDER:
        sub = drawn[drawn["category"] == cat]
        if sub.empty:
            continue
        color = CATEGORY_COLORS[cat]
        src = _source(sub)
        if cat == "degraded":
            r_strip = p.quad(
                left="left",
                right="right",
                bottom=y_top + strip_height,
                top=y_top + 2 * strip_height,
                source=src,
                fill_alpha=0.0,
                hatch_pattern="/",
                hatch_color=color,
                hatch_alpha=0.9,
                hatch_scale=6,
                line_color=color,
                line_width=1.0,
                level="annotation",
            )
        else:
            alpha = [
                band_alpha * (0.5 if sev == "partial" else 1.0)
                for sev in sub["severity"]
            ]
            src.add(alpha, "alpha")
            r_band = p.quad(
                left="left",
                right="right",
                bottom=y_bottom,
                top=y_top,
                source=src,
                fill_color=color,
                fill_alpha="alpha",
                line_color=None,
                level="underlay",
            )
            band_renderers.append(r_band)
            r_strip = p.quad(
                left="left",
                right="right",
                bottom=y_top,
                top=y_top + strip_height,
                source=src,
                fill_color=color,
                line_color="white",
                line_width=0.6,
                level="annotation",
            )
        strip_renderers.append(r_strip)
        legend_items.append(
            LegendItem(label=CATEGORY_LEGEND_NAMES[cat], renderers=[r_strip])
        )
    # Bands go under the twilight columns, like zorder 0.6 in the matplotlib version.
    if band_renderers:
        others = [r for r in p.renderers if r not in band_renderers]
        p.renderers = band_renderers + others

    has_degraded = bool((drawn["severity"] == "degraded").any())
    y_strip_top = y_top + strip_height * (2 if has_degraded else 1)

    # Labels: estimated widths, greedy stagger, leader lines.
    labelled = drawn[drawn["labelled"]]
    frame_px = frame_width_px if frame_width_px is not None else (p.width - 110)
    ms_per_px = (x1 - x0) / max(frame_px, 1)
    font_px = float(str(label_font_size).rstrip("px"))
    centers, halves = [], []
    for _, r in labelled.iterrows():
        xs = max(_x_ms(r["start"]) - _DAY_MS / 2, x0)
        xe = min(_x_ms(r["end"]) + _DAY_MS / 2, x1)
        centers.append(0.5 * (xs + xe))
        halves.append(0.5 * 0.55 * font_px * len(r["label"]) * ms_per_px)
    centers = np.asarray(centers)
    halves = np.asarray(halves)
    pos = np.clip(centers, x0 + halves, x1 - halves) if len(centers) else centers
    pad = 0.012 * (x1 - x0)
    levels = _assign_levels(pos, halves, pad) if len(pos) else np.zeros(0, dtype=int)
    n_levels = int(levels.max()) + 1 if len(levels) else 0
    y_text = y_strip_top + 0.35 * level_step + levels * level_step
    if len(levels):
        lsrc = ColumnDataSource(dict(x=pos, y=y_text, text=labelled["label"].tolist()))
        p.add_layout(
            LabelSet(
                x="x",
                y="y",
                text="text",
                source=lsrc,
                text_font_size=label_font_size,
                text_color=_INK,
                text_align="center",
                text_baseline="bottom",
                level="annotation",
            )
        )
        y_knee = y_text - 0.1 * level_step
        p.segment(
            x0=centers,
            y0=np.full(len(centers), y_strip_top),
            x1=centers,
            y1=y_knee,
            line_color=_INK,
            line_width=0.8,
            level="annotation",
        )
        p.segment(
            x0=centers,
            y0=y_knee,
            x1=pos,
            y1=y_knee,
            line_color=_INK,
            line_width=0.8,
            level="annotation",
        )
    drawn["level"] = -1
    drawn.loc[labelled.index, "level"] = levels

    # Extend the y range to make room, and mark the top of the data area.
    p.y_range.end = y_strip_top + (n_levels + 0.6) * level_step
    p.add_layout(
        Span(location=y_top, dimension="width", line_color="black", line_width=1)
    )

    # LSST start marker.
    if lsst_start is not None:
        d = pd.Timestamp(str(lsst_start)).date()
        xl = _x_ms(d) - _DAY_MS / 2
        if x0 <= xl <= x1:
            p.add_layout(
                Span(
                    location=xl,
                    dimension="height",
                    line_color=_INK,
                    line_width=1.4,
                    line_dash="dashed",
                    level="annotation",
                )
            )
            p.add_layout(
                Label(
                    x=xl,
                    y=y_top - 0.15,
                    text="Start of the LSST ",
                    text_align="right",
                    text_baseline="top",
                    text_font_size=label_font_size,
                    text_font_style="bold",
                    text_color=_INK,
                    background_fill_color="white",
                    background_fill_alpha=0.85,
                    level="annotation",
                )
            )

    # Hover on bands and strips.
    hover_targets = band_renderers + strip_renderers
    if hover_targets:
        p.add_tools(
            HoverTool(
                renderers=hover_targets,
                tooltips=[
                    ("downtime", "@label"),
                    ("nights", "@start_date to @end_date (@n_nights)"),
                    ("category / severity", "@category / @severity"),
                    ("confidence", "@confidence"),
                    ("FRACAS", "@fracas"),
                    ("notes", "@notes"),
                ],
            )
        )

    legend = None
    if legend_items:
        legend = Legend(
            items=legend_items,
            orientation="horizontal",
            title="Downtime",
            label_text_font_size=label_font_size,
            title_text_font_size=label_font_size,
            border_line_color=None,
        )
        p.add_layout(legend, "below")

    return {"rows": drawn, "n_levels": n_levels, "legend": legend, "skipped": skipped}
