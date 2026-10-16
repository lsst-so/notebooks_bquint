"""Build the annotated on-sky utilization figure for the RASAB 2026 talk.

Base layer: the visit timeline of ``notebooks/on_sky_utilization_repro.ipynb``
(one strip per night, visits as ticks at the exposure midpoint coloured by
program class, twilight bands) drawn with the helpers in ``utils.py`` on a
matplotlib date axis. Annotation layer: ``downtime.annotate_downtime``.

Outputs (in ``plots/``): ``utilization_annotated.png`` (300 dpi),
``utilization_annotated.pdf`` and ``downtime_summary.md``.

Run from a stack shell (``setup lsst_distrib``) in this folder:
    python make_utilization_annotated.py [--talk]
``--talk`` draws fault, weather and mixed spans of at least 3 nights, labels
only the rows flagged ``talk = 1`` in the CSV, and uses the 9.5 x 4 inch
transparent slide style (writes ``*_talk.*``).
``--y-ref local`` puts the y axis in Chile clock time (America/Santiago, CLT/CLST)
instead of hours after 00:00 UTC (writes ``*_local.*``).
"""

from __future__ import annotations

import argparse
import datetime as dt
from pathlib import Path

import matplotlib
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import downtime
import utils

HERE = Path(__file__).parent
PLOTS = HERE / "plots"
CACHE = HERE / "cache"

DAY_OBS_MIN = 20251026
DAY_OBS_MAX = 20260713  # last night before the July storm
#: Figure styles. "backup" is the full 16:9 slide; "slide" is the talk figure that
#: drops into a 9.5 x 4 inch box on the RASAB slide (transparent background).
STYLES = {
    "backup": dict(
        figsize=(13.3, 7.5),
        axis_label_fs=12,
        tick_fs=11,
        legend_fs=11,
        annot_fs=11,
        transparent=False,
        pad=0.05,
    ),
    "slide": dict(
        figsize=(9.5, 4.0),
        axis_label_fs=10,
        tick_fs=12,
        legend_fs=9,
        annot_fs=12,
        transparent=True,
        pad=0.02,
        legend_loc="right",  # visit legend and downtime legends stacked on the right
        label_mode="numbers",
        short_ylabel=True,  # the axes are short; the long label would overflow
    ),
}
STYLES["backup"].update(legend_loc="inside", label_mode="text", short_ylabel=False)
Y_RANGE = (-1.5, 11.0)  # original figure, hours after 00:00 UTC
Y_RANGE_LOCAL = (-5.5, 7.5)  # 18:30 to 07:30 local; clips only one stray visit at 17:53
BLANK_THRESHOLD = 50  # plotted visits; below this a night counts as lost


def load_data():
    visits = pd.read_parquet(CACHE / "lsstcam_visits_ql_20251026_20260714.parquet")
    visits = visits[
        (visits["day_obs"] >= DAY_OBS_MIN) & (visits["day_obs"] <= DAY_OBS_MAX)
    ]
    visits = utils.add_time_columns(utils.categorize_visits(visits))
    tw_path = CACHE / f"twilight_{DAY_OBS_MIN}_{DAY_OBS_MAX}.parquet"
    if tw_path.exists():
        twilight = pd.read_parquet(tw_path)
    else:
        twilight = utils.twilight_table(DAY_OBS_MIN, DAY_OBS_MAX)
        twilight.to_parquet(tw_path)
    return visits, twilight


to_local = utils.to_local_hours  # kept as a short alias for the notebook


def x_of(day_obs) -> np.ndarray:
    """Matplotlib date number of 00:00 UTC on day_obs (scalar or array)."""
    s = pd.Series(np.atleast_1d(day_obs)).astype(int).astype(str)
    return mdates.date2num(pd.to_datetime(s, format="%Y%m%d").to_numpy())


def base_timeline(visits, twilight, colors, y_ref="utc", style=None):
    """The original visit timeline, unchanged in colour coding, on a date axis.

    ``y_ref="utc"`` is the original y axis (hours after 00:00 UTC on the morning
    date of the night). ``y_ref="local"`` shifts every night by its Chile UTC
    offset so the axis reads as local clock time (CLT in winter, CLST in summer).
    ``style`` is one of the ``STYLES`` dicts (figure size and font sizes).
    """
    style = STYLES["backup"] if style is None else style
    if y_ref not in ("utc", "local"):
        raise ValueError(f"y_ref must be 'utc' or 'local', got {y_ref!r}")
    visits = visits.copy()
    twilight = twilight.copy()
    y_range = Y_RANGE
    if y_ref == "local":
        y_range = Y_RANGE_LOCAL
        visits["t_mid_h"] = to_local(visits["t_mid_h"], visits["day_obs"])
        for c in (
            "evening_nautical_h",
            "evening_astronomical_h",
            "morning_astronomical_h",
            "morning_nautical_h",
        ):
            twilight[c] = to_local(twilight[c], twilight["day_obs"])

    plt.rcParams.update({"font.size": style["tick_fs"]})
    fig, ax = plt.subplots(figsize=style["figsize"])
    ax.set_facecolor("white")  # keep the plot area white even on a transparent figure
    xt = x_of(twilight["day_obs"].to_numpy())
    lo, hi = y_range[0] - 1, y_range[1] + 1
    for b, t, a in [
        (lo, twilight["evening_nautical_h"], 0.4),
        (twilight["evening_nautical_h"], twilight["evening_astronomical_h"], 0.2),
        (twilight["morning_astronomical_h"], twilight["morning_nautical_h"], 0.2),
        (twilight["morning_nautical_h"], hi, 0.4),
    ]:
        ax.bar(
            xt,
            np.asarray(t) - np.asarray(b),
            bottom=b,
            width=1.0,
            color="black",
            alpha=a,
            linewidth=0,
            zorder=1,
            label="-12 deg to -18 deg Twilight" if a == 0.2 and b is lo else None,
        )
    xv = x_of(visits["day_obs"].to_numpy())
    for name, flag in [
        ("Engineering", "is_engineering"),
        ("Survey Programs", "is_survey"),
        ("Focus and Alignment", "is_focus"),
    ]:
        sel = visits[flag].to_numpy()
        ax.hlines(
            visits.loc[sel, "t_mid_h"].to_numpy(),
            xv[sel] - 0.4,
            xv[sel] + 0.4,
            colors=colors[name],
            linewidth=0.9,
            label=name,
            zorder=2,
        )
    ax.set_ylim(*y_range)
    ax.set_xlim(xt.min() - 1.0, xt.max() + 1.0)
    ax.xaxis.set_major_locator(mdates.MonthLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b\n%Y"))
    ax.xaxis.set_minor_locator(mdates.DayLocator(bymonthday=[8, 15, 22]))
    ax.tick_params(axis="x", which="major", labelsize=style["tick_fs"], length=6)
    ax.tick_params(axis="x", which="minor", length=3)
    ax.tick_params(axis="y", labelsize=style["tick_fs"])
    if y_ref == "local":
        ticks = np.arange(np.ceil(y_range[0] / 2) * 2, y_range[1] + 0.01, 2)
        ax.set_yticks(ticks, [f"{int(t) % 24:02d}:00" for t in ticks])
        ylabel = (
            "Local time (Chile)"
            if style["short_ylabel"]
            else "Local clock time (Chile, CLT / CLST)"
        )
    else:
        ylabel = (
            "Hours after 00:00 UTC"
            if style["short_ylabel"]
            else "Time of night (hours after 00:00 UTC)"
        )
    ax.set_ylabel(ylabel, fontsize=style["axis_label_fs"])
    ax.set_xlabel("Night (day_obs)", fontsize=style["axis_label_fs"])
    if style["legend_loc"] == "right":
        ax.legend(
            loc="upper left",
            bbox_to_anchor=(0.12, 0.0),
            bbox_transform=downtime.right_anchor_transform(ax),
            fontsize=style["legend_fs"],
            frameon=False,
            borderaxespad=0.0,
            borderpad=0.2,
            handlelength=1.6,
            labelspacing=0.3,
        )
        # Thicker line keys so the three visit colours read at slide distance.
        for h in ax.get_legend().legend_handles:
            h.set_linewidth(h.get_linewidth() + 2.0)
    else:
        ax.legend(
            loc="upper left",
            fontsize=style["legend_fs"],
            framealpha=0.95,
            markerscale=2,
        )
    return fig, ax


def nights_lost_table(csv_path, nights):
    """One row per CSV span with the count of blank nights inside the plot range."""
    df = downtime.load_downtime(csv_path)
    d0 = dt.date(2025, 10, 26)
    d1 = dt.date(2026, 7, 13)
    lost, in_range = [], []
    for s, e in zip(df["start"], df["end"]):
        if e < d0 or s > d1:
            lost.append(None)
            in_range.append(False)
            continue
        a = int(max(s, d0).strftime("%Y%m%d"))
        b = int(min(e, d1).strftime("%Y%m%d"))
        sub = nights.loc[a:b]
        lost.append(int((sub["n_plot"] < BLANK_THRESHOLD).sum()))
        in_range.append(True)
    df["nights_lost"] = lost
    df["in_range"] = in_range
    return df


def write_summary(df, path, drawn_rows, nights):
    drawn = {(r.start_date, r.end_date) for r in drawn_rows.itertuples()}
    lines = [
        "# Downtime summary, 2025-10-26 to 2026-07-13",
        "",
        "Nights lost = nights inside the span with fewer than "
        f"{BLANK_THRESHOLD} plotted visits in ConsDB (`cdb_lsstcam.visit1`, "
        "airmass > 0, img_type in acq/science/cwfs/focus). Spans marked * are "
        "drawn on `utilization_annotated.png`.",
        "",
        "| Start | End | Nights lost | Label | Category | Severity | Confidence | FRACAS |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for r in df.itertuples():
        lost = "outside range" if pd.isna(r.nights_lost) else str(int(r.nights_lost))
        mark = "*" if (r.start_date, r.end_date) in drawn else ""
        fr = r.fracas.replace(";", ", ") if r.fracas else "-"
        lines.append(
            f"| {r.start_date} | {r.end_date} | {lost} | {r.label}{mark} | {r.category} | "
            f"{r.severity} | {r.confidence} | {fr} |"
        )
    inr = df[df["in_range"]]
    per_cat = inr.groupby("category")["nights_lost"].sum().astype(int)
    per_cat = per_cat.reindex(
        [c for c in downtime.CATEGORY_ORDER if c in per_cat.index]
    )
    lines += ["", "## Nights lost per category (in range, sum over spans)", ""]
    lines += ["| Category | Nights lost |", "|---|---|"]
    for cat, n in per_cat.items():
        lines.append(f"| {cat} | {n} |")
    lines.append(f"| **total** | **{int(per_cat.sum())}** |")
    n_blank = int((nights["n_plot"] < BLANK_THRESHOLD).sum())
    n_unknown = int(per_cat.get("unknown", 0))
    lines += [
        "",
        f"Distinct blank nights in ConsDB over the range: **{n_blank}**, of which "
        f"{n_blank - n_unknown} are covered by a labelled span and {n_unknown} are UNKNOWN.",
        "The per-category sum exceeds this because the degraded span (earthquake, TMA at "
        "5 %) overlaps other spans, so its blank nights are counted twice.",
    ]
    path.write_text("\n".join(lines) + "\n")
    return per_cat


def main():
    matplotlib.use("Agg")
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--talk",
        action="store_true",
        help="fault/weather/mixed of >= 3 nights, numbered where talk=1",
    )
    ap.add_argument(
        "--y-ref",
        choices=["utc", "local"],
        default="utc",
        help="y axis reference: hours after 00:00 UTC (original) or Chile clock time",
    )
    args = ap.parse_args()

    csv_path = HERE / "downtime_annotations.csv"
    visits, twilight = load_data()
    colors = utils.rubin_category_colors()
    style = STYLES["slide" if args.talk else "backup"]
    fig, ax = base_timeline(visits, twilight, colors, y_ref=args.y_ref, style=style)
    fig.subplots_adjust(left=0.065, right=0.99, bottom=0.2, top=0.97)

    if args.talk:
        kw = dict(
            min_duration_days=3,
            categories=["fault", "weather", "mixed"],
            label_categories=["fault"],
            label_flag="talk",
        )
        stem = "utilization_annotated_talk"
    else:
        kw = dict(min_duration_days=1, categories=None)
        stem = "utilization_annotated"
    if args.y_ref == "local":
        stem += "_local"
    if style["legend_loc"] == "right":
        kw.update(
            legend_loc="right",
            legend_offset_in=downtime.legend_height_in(ax.get_legend()) + 0.1,
        )
    result = downtime.annotate_downtime(
        ax,
        csv_path,
        label_fontsize=style["annot_fs"],
        legend_fontsize=style["legend_fs"],
        label_mode=style["label_mode"],
        **kw,
    )
    downtime.fit_margins(fig, pad=style["pad"])

    # transparent=True would also clear the axes patch; keep the plot area white so the
    # twilight greys (alpha black on white) look the same on a dark slide.
    face = "none" if style["transparent"] else "white"
    fig.savefig(PLOTS / f"{stem}.png", dpi=300, facecolor=face)
    fig.savefig(PLOTS / f"{stem}.pdf", facecolor=face)
    print("drawn spans:", len(result["rows"]), "label rows:", result["n_levels"])
    print(
        result["rows"][
            ["start_date", "end_date", "label", "category", "level", "number"]
        ].to_string(index=False)
    )
    print("\nskipped:")
    print(result["skipped"].to_string(index=False))

    if not args.talk and args.y_ref == "utc":
        nights = pd.read_csv(
            CACHE / "nights_20251026_20260713.csv", index_col="day_obs"
        )
        df = nights_lost_table(csv_path, nights)
        per_cat = write_summary(
            df, PLOTS / "downtime_summary.md", result["rows"], nights
        )
        print("\nnights lost per category:")
        print(per_cat.to_string())
        print(
            "total blank nights in range:",
            int((nights["n_plot"] < BLANK_THRESHOLD).sum()),
        )


if __name__ == "__main__":
    main()
