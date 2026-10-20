"""Bokeh version of the survey speed vs. image quality figure.

``build_figure`` takes the period (fiscal quarter, month or named window) and nightly tables from :mod:`ohlp.binning`
and returns a Bokeh layout with the plot and its controls. All interactivity is
client-side (CustomJS), so the saved HTML is standalone.

Weather nights are counted, never removed: the "LSST = 1" reference is the v5.1
baseline simulation, which already loses nights to its cloud and downtime models.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from bokeh.layouts import column, row
from bokeh.models import (
    Arrow,
    BooleanFilter,
    BoxAnnotation,
    CDSView,
    CheckboxGroup,
    ColorBar,
    ColumnDataSource,
    CustomJS,
    Div,
    FixedTicker,
    HoverTool,
    Label,
    LabelSet,
    Legend,
    LegendItem,
    LinearColorMapper,
    RangeSlider,
    Select,
    VeeHead,
    Whisker,
)
from bokeh.plotting import figure
from bokeh.resources import INLINE

from . import reference as ref
from .binning import IQ_COLUMNS, PERIODS, period_key
from .style import COLORS, time_colors

__all__ = ["build_figure", "save_html"]

MARKER_EARLY = "circle"
MARKER_LSST = "square"


# --------------------------------------------------------------------------- #
# Sources                                                                      #
# --------------------------------------------------------------------------- #


def _period_source(
    m: pd.DataFrame, colors: list[str], iq_col: str, latest: int
) -> ColumnDataSource:
    d = m[m["n_visits"] > 0].sort_values("period").copy()
    label_all = len(d) <= 6  # few points: label every one directly
    data = {
        "period": d["period"].to_numpy(),
        "seq": d["seq"].to_numpy(),
        "t_index": d["t_index"].to_numpy(),
        "label": d["label"].to_numpy(),
        "label_long": d["label_long"].to_numpy(),
        "x": d["ratio"].to_numpy(),
        "x_lo": d["ratio_q25"].to_numpy(),
        "x_hi": d["ratio_q75"].to_numpy(),
        "n_nights_calendar": d["n_nights_calendar"].to_numpy(),
        "n_nights_with_visits": d["n_nights_with_visits"].to_numpy(),
        "n_nights_weather": d["n_nights_weather"].to_numpy(),
        "n_visits": d["n_visits"].to_numpy(),
        "n_vis_expected": d["n_vis_expected"].to_numpy(),
        "low_n": d["low_n"]
        .map({True: "yes (< %d nights)" % ref.MIN_NIGHTS_PER_MONTH, False: "no"})
        .to_numpy(),
        "weather_known": d["weather_known"]
        .map({True: "yes", False: "no (before 2026-02-25)"})
        .to_numpy(),
        "is_lsst": d["is_lsst"].to_numpy(),
        "last_night": d["last_day_obs_with_visits"].to_numpy(),
        "storm_note": np.where(
            (d["period_kind"] != "window")
            & (
                (d["period"] == ref.STORM_PERIOD_QUARTER)
                | (d["period"] == ref.STORM_PERIOD_MONTH)
            ),
            "yes: off sky from %d" % (ref.DAY_OBS_LAST_BEFORE_STORM + 1),
            "no",
        ),
        "marker": np.where(d["is_lsst"], MARKER_LSST, MARKER_EARLY),
        "color": [colors[i] for i in d["t_index"]],
        "fill": [colors[i] for i in d["t_index"]],
        "alpha": np.where(d["low_n"], 0.45, 1.0),
        "size": np.where(d["period"] == latest, 20, 14),
        "period_name": np.where(d["is_lsst"], "LSST", "Early Ops"),
    }
    for c in IQ_COLUMNS:
        if f"{c}_med" in d:
            data[f"{c}_med"] = d[f"{c}_med"].to_numpy()
            data[f"{c}_q25"] = d[f"{c}_q25"].to_numpy()
            data[f"{c}_q75"] = d[f"{c}_q75"].to_numpy()
    data["y"] = data[f"{iq_col}_med"]
    data["y_lo"] = data[f"{iq_col}_q25"]
    data["y_hi"] = data[f"{iq_col}_q75"]
    # Direct labels: every period when there are few, else first, first LSST
    # and latest. Windows carry their date span, since there are only two.
    is_window = bool((d["period_kind"] == "window").all()) if len(d) else False
    text = np.full(len(d), "", dtype=object)
    if is_window:
        text[:] = d["label_long"].to_numpy()
    elif label_all:
        text[:] = d["label"].to_numpy()
    elif len(d):
        text[0] = d["label"].iloc[0]
        text[-1] = d["label"].iloc[-1]
    first_lsst = np.flatnonzero(d["is_lsst"].to_numpy())
    if len(first_lsst) and len(d) and not is_window:
        text[first_lsst[0]] = d["label"].iloc[first_lsst[0]] + " (LSST start)"
    data["text"] = text
    return ColumnDataSource(data)


def _segment_source(
    src: ColumnDataSource, colors: list[str]
) -> tuple[ColumnDataSource, list[dict]]:
    """Consecutive-period segments; dashed where periods are skipped (a gap)."""
    d = pd.DataFrame({k: src.data[k] for k in ("seq", "t_index", "x", "y", "label")})
    rows = []
    for i in range(len(d) - 1):
        a, b = d.iloc[i], d.iloc[i + 1]
        periods_apart = int(b.seq - a.seq)
        rows.append(
            {
                "x0": a.x,
                "y0": a.y,
                "x1": b.x,
                "y1": b.y,
                "t0": int(a.t_index),
                "t1": int(b.t_index),
                "color": colors[int(b.t_index)],
                "dash": "dashed" if periods_apart > 1 else "solid",
                "gap": periods_apart > 1,
                "label": f"{a.label} to {b.label}",
            }
        )
    seg = (
        pd.DataFrame(rows)
        if rows
        else pd.DataFrame(
            columns=[
                "x0",
                "y0",
                "x1",
                "y1",
                "t0",
                "t1",
                "color",
                "dash",
                "gap",
                "label",
            ]
        )
    )
    return ColumnDataSource(seg), rows


def _nightly_source(
    nightly: pd.DataFrame, periods: pd.DataFrame, iq_col: str, kind: str
) -> ColumnDataSource:
    n = nightly[nightly["n_vis"] > 0].copy()
    p_all = periods
    if kind == "window":
        # Assign nights to windows by day_obs range; nights outside any window drop.
        n["t_index"] = np.nan
        for _, r in p_all.iterrows():
            inside = (n["day_obs"] >= r["first_day_obs"]) & (
                n["day_obs"] <= r["last_day_obs"]
            )
            n.loc[inside, "t_index"] = r["t_index"]
        n = n[n["t_index"].notna()].copy()
        n["t_index"] = n["t_index"].astype(int)
    else:
        n["period"] = period_key(n["day_obs"], kind)
        n["t_index"] = n["period"].map(p_all.set_index("period")["t_index"])
    n["date_str"] = n["date"].dt.strftime("%Y-%m-%d")
    n["weather_label"] = np.where(n["is_weather_night"], "weather night", "")
    n["weather_label"] = np.where(
        n["weather_known"].fillna(False),
        n["weather_label"],
        "weather state unavailable",
    )
    n["marker"] = np.where(n["is_lsst"], MARKER_LSST, MARKER_EARLY)
    n["day_ord"] = (n["date"] - n["date"].min()).dt.days
    data = {
        "day_obs": n["day_obs"].to_numpy(),
        "date_str": n["date_str"].to_numpy(),
        "t_index": n["t_index"].to_numpy(),
        "x": n["ratio"].to_numpy(),
        "n_vis": n["n_vis"].to_numpy(),
        "n_vis_expected": n["n_vis_expected"].to_numpy(),
        "weather_label": n["weather_label"].to_numpy(),
        "weather_hours_efd": n["weather_hours_efd"].to_numpy(),
        "marker": n["marker"].to_numpy(),
        "day_ord": n["day_ord"].to_numpy(),
        "line_alpha": np.where(n["is_weather_night"], 0.9, 0.0),
    }
    for c in IQ_COLUMNS:
        if f"{c}_med" in n:
            data[f"{c}_med"] = n[f"{c}_med"].to_numpy()
    data["y"] = data[f"{iq_col}_med"]
    return ColumnDataSource(data)


# --------------------------------------------------------------------------- #
# Figure                                                                       #
# --------------------------------------------------------------------------- #


def build_figure(
    periods: pd.DataFrame,
    nightly: pd.DataFrame,
    iq_col: str = "idiq_aos_cam",
    width: int = 900,
    height: int = 620,
    title: str | None = None,
    show_nightly: bool = False,
):
    """Return a Bokeh layout (plot + controls).

    ``periods`` is the table from :func:`ohlp.binning.period_table` (monthly or
    quarterly) or :func:`ohlp.binning.window_table`; the kind is read from its
    ``period_kind`` column. For windows the nightly points are always shown.
    """
    kind = str(periods["period_kind"].iloc[0])
    kind_word = PERIODS[kind]
    if kind == "window":
        show_nightly = True  # few windows: their nights are the useful context
    p_all = periods[periods["n_visits"] > 0].sort_values("period")
    n_periods = len(p_all)
    latest = int(p_all["period"].max())
    latest_in_table = int(periods["period"].max())
    colors = time_colors(n_periods)

    src_all = _period_source(periods, colors, iq_col, latest)
    seg_all, seg_rows_all = _segment_source(src_all, colors)
    src_night = _nightly_source(nightly, periods, iq_col, kind)
    yref = ref.Y_REFERENCE[iq_col]

    p = figure(
        width=width,
        height=height,
        x_range=(0, 1.1),
        y_range=(yref["ymin"], yref["ymax"]),
        x_axis_label="Survey speed: visits acquired / visits expected (v5.1 baseline model)",
        y_axis_label=IQ_COLUMNS[iq_col],
        tools="pan,wheel_zoom,box_zoom,reset,save",
        active_scroll="wheel_zoom",
        title=title
        or (
            f"Survey speed vs. image quality: {' vs. '.join(p_all['label'])}"
            if kind == "window"
            else f"Survey speed vs. image quality by {kind_word}, {p_all['label'].iloc[0]} to {p_all['label'].iloc[-1]}"
        ),
        output_backend="webgl",
    )
    p.grid.grid_line_color = COLORS["grid"]
    p.axis.axis_label_text_color = COLORS["ink"]
    p.axis.major_label_text_color = COLORS["ink_secondary"]
    p.title.text_color = COLORS["ink"]

    # Goal region and star --------------------------------------------------- #
    box = BoxAnnotation(
        left=ref.VISIT_RATE.box_x_min,
        right=ref.BOX_X_MAX,
        bottom=ref.IDIQ_BOX_BOTTOM,
        top=yref["box_top"],
        fill_color=COLORS["goal_region"],
        fill_alpha=0.12,
        line_color=COLORS["goal_region"],
        line_alpha=0.5,
        line_width=1,
        level="underlay",
    )
    p.add_layout(box)
    box_label = Label(
        x=ref.BOX_X_MAX - 0.02,
        y=yref["box_top"],
        x_units="data",
        y_units="data",
        text="goal region: speed > %.2f, IQ < %.2f″"
        % (ref.VISIT_RATE.box_x_min, yref["box_top"]),
        text_align="right",
        text_baseline="top",
        text_font_size="10pt",
        text_color=COLORS["goal_region"],
        x_offset=0,
        y_offset=-4,
    )
    p.add_layout(box_label)
    src_star = ColumnDataSource({"x": [ref.VISIT_RATE.star_x], "y": [yref["star"]]})
    r_star = p.scatter(
        "x",
        "y",
        source=src_star,
        marker="star",
        size=26,
        fill_color=COLORS["star"],
        line_color=COLORS["star_edge"],
        line_width=1,
    )
    star_label = Label(
        x=ref.VISIT_RATE.star_x,
        y=yref["star"],
        text="LSST = 1",
        text_font_size="10pt",
        text_color=COLORS["ink"],
        x_offset=14,
        y_offset=-6,
    )
    p.add_layout(star_label)

    # ROST measured system (sDIQ) band (iDIQ axis only) ---------------------- #
    rost = BoxAnnotation(
        bottom=ref.SYS_IQ_MEASURED_ROST[0],
        top=ref.SYS_IQ_MEASURED_ROST[1],
        fill_color=COLORS["rost_band"],
        fill_alpha=0.10,
        line_color=COLORS["rost_band"],
        line_alpha=0.4,
        line_dash="dotted",
        level="underlay",
        visible=iq_col == "idiq_aos_cam",
    )
    p.add_layout(rost)
    rost_label = Label(
        x=0.01,
        y=ref.SYS_IQ_MEASURED_ROST[1],
        text="system contribution, sDIQ, measured %.2f–%.2f″ (ROST Sep 2026; includes dome seeing and tracking, so not one-to-one with iDIQ)"
        % ref.SYS_IQ_MEASURED_ROST,
        text_font_size="9pt",
        text_color=COLORS["rost_band"],
        text_baseline="bottom",
        y_offset=2,
        visible=iq_col == "idiq_aos_cam",
    )
    p.add_layout(rost_label)

    # Nightly cloud ---------------------------------------------------------- #
    night_mapper = LinearColorMapper(
        palette=time_colors(256),
        low=float(src_night.data["day_ord"].min()),
        high=float(src_night.data["day_ord"].max()),
    )
    night_filter = BooleanFilter(booleans=[True] * len(src_night.data["x"]))
    r_night = p.scatter(
        "x",
        "y",
        source=src_night,
        view=CDSView(filter=night_filter),
        marker="marker",
        size=9 if kind == "window" else 6,
        fill_color={"field": "day_ord", "transform": night_mapper},
        fill_alpha=0.45 if kind == "window" else 0.30,
        line_color=COLORS["ink_secondary"],
        line_alpha="line_alpha",
        line_width=0.8,
        level="underlay",
        visible=show_nightly,
    )
    p.add_tools(
        HoverTool(
            renderers=[r_night],
            tooltips=[
                ("Night (day_obs)", "@date_str"),
                ("Visits", "@n_vis / @n_vis_expected expected"),
                ("Speed", "@x{0.00}"),
                ("IQ (median)", "@y{0.000}″"),
                ("Weather hours (EFD)", "@weather_hours_efd{0.0}"),
                ("Flag", "@weather_label"),
            ],
        )
    )

    # Monthly path, whiskers, points ----------------------------------------- #
    f_all_pts = BooleanFilter(booleans=[True] * len(src_all.data["x"]))
    f_all_seg = BooleanFilter(booleans=[True] * len(seg_all.data["x0"]))
    r_seg = p.segment(
        "x0",
        "y0",
        "x1",
        "y1",
        source=seg_all,
        view=CDSView(filter=f_all_seg),
        line_color="color",
        line_dash="dash",
        line_width=1.5,
        line_alpha=0.9,
    )
    arrows_all = []
    for s in seg_rows_all:
        a = Arrow(
            end=VeeHead(size=9, fill_color=s["color"], line_color=s["color"]),
            x_start=(s["x0"] + s["x1"]) / 2,
            y_start=(s["y0"] + s["y1"]) / 2,
            x_end=(s["x0"] + s["x1"]) / 2 + (s["x1"] - s["x0"]) * 1e-3,
            y_end=(s["y0"] + s["y1"]) / 2 + (s["y1"] - s["y0"]) * 1e-3,
            line_alpha=0,
        )
        a.tags = [s["t0"], s["t1"]]
        p.add_layout(a)
        arrows_all.append(a)
    wy = Whisker(
        source=src_all,
        base="x",
        upper="y_hi",
        lower="y_lo",
        dimension="height",
        line_color="color",
        line_alpha=0.5,
        line_width=1,
        upper_head=None,
        lower_head=None,
    )
    wx = Whisker(
        source=src_all,
        base="y",
        upper="x_hi",
        lower="x_lo",
        dimension="width",
        line_color="color",
        line_alpha=0.5,
        line_width=1,
        upper_head=None,
        lower_head=None,
    )
    p.add_layout(wy)
    p.add_layout(wx)
    r_pts = p.scatter(
        "x",
        "y",
        source=src_all,
        view=CDSView(filter=f_all_pts),
        marker="marker",
        size="size",
        fill_color="fill",
        fill_alpha="alpha",
        line_color="color",
        line_alpha="alpha",
        line_width=1,
    )
    r_all = [r_seg, r_pts, wy, wx]
    p.add_tools(
        HoverTool(
            renderers=[r_pts],
            tooltips=[
                ("Period", "@label_long (@period_name)"),
                (
                    "Nights with visits",
                    "@n_nights_with_visits of @n_nights_calendar calendar",
                ),
                ("Weather nights (counted, not removed)", "@n_nights_weather"),
                ("Visits", "@n_visits{0,0} / @n_vis_expected{0,0} expected"),
                (
                    "Speed, median [IQR of nights]",
                    "@x{0.00} [@x_lo{0.00}–@x_hi{0.00}]",
                ),
                (
                    "IQ, median [IQR of visits]",
                    "@y{0.000}″ [@y_lo{0.000}–@y_hi{0.000}]",
                ),
                ("Last night with visits", "@last_night"),
                ("Storm-truncated", "@storm_note"),
                ("Few nights", "@low_n"),
                ("Weather state available", "@weather_known"),
            ],
        )
    )

    labels = LabelSet(
        source=src_all,
        x="x",
        y="y",
        text="text",
        x_offset=10,
        y_offset=8,
        text_font_size="10pt",
        text_color=COLORS["ink"],
    )
    p.add_layout(labels)

    # Storm gap note ---------------------------------------------------------- #
    gap_periods = periods[(periods["n_visits"] == 0) & (periods["period"] > latest)]
    if len(gap_periods):
        from .binning import period_label

        first_gap = period_label(int(gap_periods["period"].min()), kind)
        last_gap = period_label(latest_in_table, kind)
        span = first_gap if first_gap == last_gap else f"{first_gap}–{last_gap}"
        gap_text = f"{span}: {ref.STORM_GAP_LABEL}"
        gap_label = Label(
            x=float(src_all.data["x"][-1]),
            y=float(src_all.data["y"][-1]),
            text=gap_text,
            text_font_size="10pt",
            text_font_style="italic",
            text_color=COLORS["gap"],
            x_offset=10,
            y_offset=-16,
        )
        p.add_layout(gap_label)
    for s in seg_rows_all:
        if s["gap"] and kind != "window":
            p.add_layout(
                Label(
                    x=(s["x0"] + s["x1"]) / 2,
                    y=(s["y0"] + s["y1"]) / 2,
                    text=ref.STORM_GAP_LABEL,
                    text_font_size="9pt",
                    text_font_style="italic",
                    text_color=COLORS["gap"],
                    y_offset=6,
                )
            )

    # Colorbar with month ticks ---------------------------------------------- #
    period_mapper = LinearColorMapper(palette=colors, low=-0.5, high=n_periods - 0.5)
    cbar = ColorBar(
        color_mapper=period_mapper,
        ticker=FixedTicker(ticks=list(range(n_periods))),
        major_label_overrides={i: lab for i, lab in enumerate(src_all.data["label"])},
        title=kind_word,
        label_standoff=6,
        width=14,
    )
    p.add_layout(cbar, "right")

    # Legend ----------------------------------------------------------------- #
    legend_src = ColumnDataSource({"x": [np.nan] * 2, "y": [np.nan] * 2})
    l_early = p.scatter(
        "x",
        "y",
        source=legend_src,
        marker=MARKER_EARLY,
        size=11,
        fill_color=colors[len(colors) // 2],
        line_color=colors[len(colors) // 2],
    )
    l_lsst = p.scatter(
        "x",
        "y",
        source=legend_src,
        marker=MARKER_LSST,
        size=11,
        fill_color=colors[-1],
        line_color=colors[-1],
    )
    legend = Legend(
        items=[
            LegendItem(label=f"Early Ops {kind_word}", renderers=[l_early]),
            LegendItem(label=f"LSST {kind_word}", renderers=[l_lsst]),
            LegendItem(label="LSST = 1", renderers=[r_star]),
            LegendItem(label="nightly values", renderers=[r_night]),
        ],
        orientation="horizontal",
        label_text_font_size="9pt",
        border_line_color=None,
        background_fill_alpha=0,
    )
    p.add_layout(legend, "below")

    # Controls ---------------------------------------------------------------- #
    checks = CheckboxGroup(
        labels=[
            "Period points",
            "Nightly points",
            "ROST sDIQ band",
        ],
        active=[
            i
            for i, on in enumerate([True, show_nightly, iq_col == "idiq_aos_cam"])
            if on
        ],
        inline=True,
    )
    stat_select = Select(
        title="Image-quality statistic (y axis)",
        value=iq_col,
        options=[(k, v) for k, v in IQ_COLUMNS.items()],
        width=360,
    )
    slider = RangeSlider(
        start=0,
        end=max(n_periods - 1, 1),
        value=(0, n_periods - 1),
        step=1,
        title=f"{kind_word.capitalize()}s shown (index)",
        width=360,
    )
    note = Div(
        text=(
            "<b>How to read:</b> right is faster, down is sharper. Lightness carries time (light = first %s, dark = latest). "
            "Faded points are %ss with fewer than %d nights. Whiskers are the 25–75%% range: over nights on x, over visits on y. "
            "Weather nights are counted, not removed: the LSST = 1 reference comes from the v5.1 baseline simulation, "
            "which already includes cloud and downtime losses. The EFD WEATHER state (from 2026-02-25) only outlines nights in the hover."
        )
        % (kind_word, kind_word, ref.MIN_NIGHTS_PER_MONTH),
        width=width,
    )

    yref_js = {k: v for k, v in ref.Y_REFERENCE.items()}
    labels_js = {k: v for k, v in IQ_COLUMNS.items()}
    cb_args = dict(
        src_all=src_all,
        src_night=src_night,
        src_star=src_star,
        seg_all=seg_all,
        box=box,
        box_label=box_label,
        star_label=star_label,
        rost=rost,
        rost_label=rost_label,
        yaxis=p.yaxis[0],
        yrange=p.y_range,
        yref=yref_js,
        ylabels=labels_js,
        arrows_all=arrows_all,
        checks=checks,
        box_x_min=ref.VISIT_RATE.box_x_min,
    )
    stat_js = CustomJS(
        args=cb_args,
        code="""
        const stat = cb_obj.value;
        src_all.data['y'] = src_all.data[stat + '_med'];
        src_all.data['y_lo'] = src_all.data[stat + '_q25'];
        src_all.data['y_hi'] = src_all.data[stat + '_q75'];
        src_all.change.emit();
        src_night.data['y'] = src_night.data[stat + '_med'];
        src_night.change.emit();
        for (const [src, seg, arrows] of [[src_all, seg_all, arrows_all]]) {
            const y = src.data['y'];
            const n = seg.data['x0'].length;
            for (let i = 0; i < n; i++) {
                seg.data['y0'][i] = y[i]; seg.data['y1'][i] = y[i + 1];
                const a = arrows[i];
                const xm = (seg.data['x0'][i] + seg.data['x1'][i]) / 2;
                const ym = (y[i] + y[i + 1]) / 2;
                a.x_start = xm; a.y_start = ym;
                a.x_end = xm + (seg.data['x1'][i] - seg.data['x0'][i]) * 1e-3;
                a.y_end = ym + (y[i + 1] - y[i]) * 1e-3;
            }
            seg.change.emit();
        }
        const r = yref[stat];
        box.top = r['box_top'];
        box_label.y = r['box_top'];
        box_label.text = 'goal region: speed > ' + box_x_min.toFixed(2) + ', IQ < ' + r['box_top'].toFixed(2) + '\\u2033';
        src_star.data['y'] = [r['star']]; src_star.change.emit();
        star_label.y = r['star'];
        yaxis.axis_label = ylabels[stat];
        yrange.start = r['ymin']; yrange.end = r['ymax'];
        const is_idiq = (stat === 'idiq_aos_cam');
        rost.visible = is_idiq && checks.active.includes(2);
        rost_label.visible = rost.visible;
        """,
    )
    stat_select.js_on_change("value", stat_js)

    vis_args = dict(
        r_all=r_all,
        arrows_all=arrows_all,
        r_night=r_night,
        rost=rost,
        rost_label=rost_label,
        stat_select=stat_select,
        labels=labels,
        slider=slider,
        f_all_pts=f_all_pts,
        f_all_seg=f_all_seg,
        f_night=night_filter,
        src_all=src_all,
        src_night=src_night,
        seg_all=seg_all,
    )
    vis_code = """
        const act = checks.active;
        const [lo, hi] = slider.value;
        const in_range = (t) => (t >= lo && t <= hi);
        const show_all = act.includes(0);
        for (const r of r_all) r.visible = show_all;
        labels.visible = show_all;
        for (const a of arrows_all) a.visible = show_all && in_range(a.tags[0]) && in_range(a.tags[1]);
        r_night.visible = act.includes(1);
        const is_idiq = (stat_select.value === 'idiq_aos_cam');
        rost.visible = is_idiq && act.includes(2);
        rost_label.visible = rost.visible;
        f_all_pts.booleans = Array.from(src_all.data['t_index'], in_range);
        f_all_seg.booleans = Array.from(seg_all.data['t0'], (t, i) => in_range(t) && in_range(seg_all.data['t1'][i]));
        f_night.booleans = Array.from(src_night.data['t_index'], in_range);
        for (const f of [f_all_pts, f_all_seg, f_night]) f.change.emit();
    """
    checks.js_on_change(
        "active", CustomJS(args=dict(checks=checks, **vis_args), code=vis_code)
    )
    slider.js_on_change(
        "value", CustomJS(args=dict(checks=checks, **vis_args), code=vis_code)
    )

    controls = row(
        stat_select, slider, column(Div(text="<b>Layers</b>", height=12), checks)
    )
    return column(controls, p, note)


def save_html(
    layout, path: str | Path, title: str = "Survey speed vs. image quality"
) -> Path:
    """Write a standalone HTML file (Bokeh JS inlined)."""
    from bokeh.io import output_file, reset_output, save

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    reset_output()
    output_file(str(path), title=title, mode="inline")
    save(layout, filename=str(path), resources=INLINE, title=title)
    reset_output()
    return path
