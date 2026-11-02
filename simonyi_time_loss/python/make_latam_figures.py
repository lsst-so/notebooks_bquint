"""LSST@LATAM 2026 talk figures from ``data/processed/per_night.csv`` (ROSP-24 accounting).

Two figures, each saved transparent and as a ``_white`` variant (16:9, large type):

* ``time_loss_nightly_talk_<tag>.png`` (B3) — hours per night in the four talk
  categories, the −12° night-length curve (ROSP-22), the WEATHER-bit date and three
  long-outage annotations read from ``data/downtime_annotations.csv``.
* ``time_loss_monthly_talk_<tag>.png`` (B1) — monthly fractions; slice labels are
  dropped below 10 %.

Categories (ROSP-24 precedence, drawn bottom → top in reversed precedence order,
science at the bottom): survey (A1 + A2, plus the A3 start-up allowance), fault + idle
(D + E, plus F unattributed from 2026-02-25, one series with the caveat in the README),
engineering (B2), Focus and Alignment (BLOCK-T539, its own category since 2026-10-27),
weather (C) and B1 planned maintenance. The Dynalene-condensation windows now inside
fault + idle (Bruno, 2026-10-26) are hatched in the fault colour.

Since 2026-11-01 the range runs to the latest complete night and covers the July 2026
storm. The three periods of ``STORM_PERIODS`` are drawn as shaded spans with labels and
printed as a per-period table; they are assigned by Bruno's rule, not by the data (see
``classify.storm_override``). The title reports the on-sky season shares (unchanged, the
numbers quoted in the deck) on one line and the full range on a second.

Since 2026-11-02 ``monthly_6bin`` adds a third figure,
``time_loss_monthly_talk_<tag>_6bin[_white].png`` (slide 4 "Where the night goes"): the
same months in six bins — Science, Engineering, Alignment, Fault + idle, Planned
maintenance, Weather — at exactly 6 × 4 in / 300 dpi, in the slide-2 colours
(``SLIDE2_CAT``, a deliberate palette violation, see README §3b.1). It is separate from
``monthly()`` on purpose: B3 shares ``CAT``/``_stack``, which it does not touch.

Run from anywhere: ``python simonyi_time_loss/python/make_latam_figures.py``.
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from time_loss import (  # noqa: E402
    DAY_OBS_BACK_ON_SKY,
    DAY_OBS_LAST_BEFORE_STORM,
    DAY_OBS_MAX,
    DAY_OBS_MIN,
    DAY_OBS_WEATHER_BIT_START,
    NIGHT_SUN_ALT,
    STORM_PERIODS,
)
from time_loss.downtime import load_downtime, select_spans  # noqa: E402
from time_loss.style import COLORS  # noqa: E402

PROC = ROOT / "data" / "processed"
FIG = ROOT / "figures"
FIG.mkdir(exist_ok=True)
TAG = f"{DAY_OBS_MIN}-{DAY_OBS_MAX}"
NIGHT = f"{NIGHT_SUN_ALT}°".replace("-", "−")  # "−12°"

#: The three long faults the talk points at (slide 9). Keys are the CSV ``start_date``.
LATAM_OUTAGES = {
    "2026-01-30": "Camera vacuum leak",
    "2026-05-02": "TMA encoder",
    "2026-06-20": "Camera cryo",
}

TALK_RC = {
    "figure.figsize": (13.33, 7.5),
    "font.size": 18,
    "axes.labelsize": 20,
    "axes.titlesize": 22,
    "xtick.labelsize": 16,
    "ytick.labelsize": 16,
    "legend.fontsize": 17,
    "axes.linewidth": 1.2,
    "hatch.linewidth": 0.8,
    "text.color": COLORS["ink"],
    "axes.labelcolor": COLORS["ink"],
    "axes.edgecolor": COLORS["ink_secondary"],
    "xtick.color": COLORS["ink_secondary"],
    "ytick.color": COLORS["ink_secondary"],
    "grid.color": COLORS["grid"],
}

#: plotted series (column, label, colour); stack order bottom → top
CAT = [
    ("survey_plot", "survey (on sky)", COLORS["on_sky"]),
    ("fault_plot", "fault + idle", COLORS["nonweather_loss"]),
    ("engineering_hours", "engineering", COLORS["engineering"]),
    ("focus_alignment_hours", "Focus and Alignment", COLORS["focus"]),
    ("planned_maintenance_hours", "planned maintenance", COLORS["downtime"]),
    ("weather_hours", "weather", COLORS["weather"]),
]
DYN_LABEL = "of which Dynalene closure"
#: legend / title order = ROSP-24 precedence (top of the stack first)
PRECEDENCE = [
    "weather",
    "planned maintenance",
    "Focus and Alignment",
    "engineering",
    "fault + idle",
    "survey (on sky)",
]


def load_per_night() -> pd.DataFrame:
    t = pd.read_csv(PROC / "per_night.csv")
    t["date"] = pd.to_datetime(t.day_obs.astype(str))
    t["month"] = t.day_obs // 100
    t["survey_plot"] = t.on_sky_hours + t.startup_hours
    t["fault_plot"] = t.nonweather_loss_hours + t.unattributed_hours.fillna(0)
    return t


def outage_spans() -> pd.DataFrame:
    df = load_downtime(ROOT / "data" / "downtime_annotations.csv")
    t0 = pd.Timestamp(str(DAY_OBS_MIN)).date()
    t1 = pd.Timestamp(str(DAY_OBS_MAX)).date()
    sel = select_spans(df, t0, t1, label_flag="talk")
    sel = sel[sel.labelled & sel.start_date.isin(LATAM_OUTAGES)].copy()
    sel["short"] = sel.start_date.map(LATAM_OUTAGES)
    return sel


def _save(fig, stem: str, dpi: int = 200):
    fig.savefig(FIG / f"{stem}.png", dpi=dpi, transparent=True)
    fig.savefig(FIG / f"{stem}_white.png", dpi=dpi, facecolor="white")
    print("wrote", FIG / f"{stem}[_white].png")


#: y-axis treatment of the fraction-of-night stacks (Bruno, 2026-11-02): no axis line, no
#: ticks and no tick labels — only a horizontal rule every 20 % of the night, which the
#: "Night Fraction" label is enough to read. Dropping the labels gives the width back to
#: the bars.
GRID_STEP = 0.20
#: A rule crosses backgrounds from near-white (the margins either side, and the plot area
#: above the short bars) to near-black (``Science`` is #024243), so **no flat colour is
#: visible on all of them** — mock-ups on the real figure settled that on 2026-11-02:
#: white and a light grey vanish in the margins, a mid or dark grey vanishes over Science
#: and Engineering. So each rule is a **pair of touching hairlines, one white one black**
#: (Bruno, 2026-11-02): whichever one matches the background drops away and the other
#: carries the line, on a light or a dark slide alike. Each is offset half its width from
#: the level, so the pair straddles it and the two touch rather than overlap.
#:
#: Weight matters more than it looks: the first try at 0.25 pt / alpha 0.25 was invisible
#: at 300 dpi (0.25 pt ≈ 1 px, antialiased to a quarter-strength sub-pixel line, and the
#: two tones partly cancel to the mid grey that had already failed). 0.5 pt at alpha 0.5
#: is ~2 px each and renders cleanly.
GRID_COLORS = ("white", "black")  # drawn in this order, first one above the level
#: >>> opacity of both hairlines — the knob to tweak if the rules read too strong or too
#: faint on the slide. 0.3 was checked against 0.5 on zoomed crops of the dark teals
#: (Bruno, 2026-11-02) and still holds there; it is about as light as the pair goes. Note
#: it is alpha *and* width together that decide whether a rule survives the raster: at
#: 0.25 pt the same 0.25 alpha was invisible at 300 dpi. <<<
GRID_ALPHA = 0.3
GRID_LW = 0.5
#: how far the rules run past the axes, left and right (Bruno, 2026-11-02). Asymmetric:
#: just a nick on the left, where the "Night Fraction" label is, and a longer run on the
#: right, where there is nothing else.
GRID_OVERHANG_LEFT_PT = 3.0
GRID_OVERHANG_RIGHT_PT = 10.0


def _fraction_yaxis(ax, label: str = "Night Fraction"):
    """Replace the y axis with horizontal rules every ``GRID_STEP`` of the night.

    The spine, the tick marks and the tick labels all go. 0 % is the x axis and 100 % the
    top of the frame, so neither gets a rule. Each rule is a white/black hairline pair
    (see ``GRID_COLORS``) running ``GRID_OVERHANG_PT`` past the axes on both sides, so it
    is re-fitted on every draw: the overhang is a length in points, and the axes width in
    points is only known once the layout engine has run. Call after ``set_ylim``.
    """
    ax.spines["left"].set_visible(False)
    ax.set_ylabel(label)
    ax.tick_params(axis="y", length=0, labelleft=False)
    # x in axes fraction so the overhang can be set as a fraction, y in data units so the
    # rules follow the scale; clip_on=False lets them leave the axes.
    blend = mpl.transforms.blended_transform_factory(ax.transAxes, ax.transData)
    n = int(round(1.0 / GRID_STEP))
    rules = []
    for i in range(1, n):
        y = i * GRID_STEP
        for color, sign in zip(GRID_COLORS, (+1, -1)):
            # half-width offset in points, so the two lines touch at the level itself
            # whatever the figure dpi
            offset = mpl.transforms.ScaledTranslation(
                0, sign * (GRID_LW / 2) / 72.0, ax.figure.dpi_scale_trans
            )
            rules.append(
                ax.add_line(
                    mpl.lines.Line2D(
                        [0, 1],
                        [y, y],
                        transform=blend + offset,
                        color=color,
                        alpha=GRID_ALPHA,
                        linewidth=GRID_LW,
                        solid_capstyle="butt",
                        clip_on=False,
                        zorder=2.5,  # over the bars (1), under the in-bar values (3)
                    )
                )
            )

    def _fit(_event=None):
        w = ax.get_window_extent().width  # pixels, final only after the layout runs
        if w <= 0:
            return
        px_per_pt = ax.figure.dpi / 72.0
        left = GRID_OVERHANG_LEFT_PT * px_per_pt / w
        right = GRID_OVERHANG_RIGHT_PT * px_per_pt / w
        for ln in rules:
            ln.set_xdata([-left, 1.0 + right])

    ax.figure.canvas.mpl_connect("draw_event", _fit)
    _fit()


def _stack(ax, x, t: pd.DataFrame, width: float, denom=None):
    """Stacked bars: weather hatched (palette rule), Dynalene hatched inside fault + idle."""
    bottom = np.zeros(len(t))
    for col, lab, c in CAT:
        y = t[col].to_numpy() / (denom if denom is not None else 1.0)
        # the weather grey is light and low-contrast: hatch it, as the palette requires
        hatch = "\\\\\\\\" if col == "weather_hours" else None
        ax.bar(
            x,
            y,
            bottom=bottom,
            width=width,
            color=c,
            label=lab,
            linewidth=0,
            hatch=hatch,
            edgecolor="white" if hatch else "none",
        )
        if col == "fault_plot":
            dyn = t["dynalene_hours"].to_numpy() / (denom if denom is not None else 1.0)
            ax.bar(
                x,
                dyn,
                bottom=bottom,
                width=width,
                facecolor="none",
                edgecolor="white",
                hatch="////",
                linewidth=0,
                label=DYN_LABEL,
            )
        bottom += y
    return bottom


def _period_table(t: pd.DataFrame) -> pd.DataFrame:
    """Nights and hours per period, so the totals can be checked (handoff 2026-11-01)."""
    rows = []
    blocks = [("On sky season", DAY_OBS_MIN, DAY_OBS_LAST_BEFORE_STORM)]
    blocks += [(lab, lo, hi) for lo, hi, _, lab in STORM_PERIODS]
    blocks += [
        ("Back on sky", DAY_OBS_BACK_ON_SKY, DAY_OBS_MAX),
        ("FULL RANGE", DAY_OBS_MIN, DAY_OBS_MAX),
    ]
    for lab, lo, hi in blocks:
        s = t[(t.day_obs >= lo) & (t.day_obs <= hi)]
        row = {
            "period": lab,
            "from": lo,
            "to": hi,
            "nights": len(s),
            "night_h": s.night_hours.sum(),
        }
        for col, name, _ in CAT:
            row[name] = s[col].sum()
        rows.append(row)
    return pd.DataFrame(rows).round(1)


def _storm_spans(ax, ymax: float, shade_top: float, y_label: float):
    """Shade the storm / maintenance / recovery periods and label them with their dates.

    The three periods are narrow next to the 372-night axis and their names are long,
    so each label is right-aligned at its span's right edge and stacked in height,
    with a leader line down to the span.
    """
    for i, (lo, hi, kind, lab) in enumerate(STORM_PERIODS):
        x0 = pd.Timestamp(str(lo)) - pd.Timedelta(hours=12)
        x1 = pd.Timestamp(str(hi)) + pd.Timedelta(hours=12)
        ax.axvspan(
            x0,
            x1,
            ymin=0,
            ymax=shade_top / ymax,
            color=COLORS["weather"] if kind == "weather" else COLORS["downtime"],
            alpha=0.22,
            linewidth=0,
            zorder=0,
        )
        a, b = pd.Timestamp(str(lo)), pd.Timestamp(str(hi))
        xc = x0 + (x1 - x0) / 2
        y = y_label + 2.1 * (len(STORM_PERIODS) - 1 - i)  # top label = first period
        ax.plot(
            [xc, xc],
            [shade_top, y + 0.25],
            color=COLORS["ink_secondary"],
            lw=0.8,
            zorder=4,
        )
        ax.annotate(
            f"{lab}  {a:%-d %b} – {b:%-d %b}",
            xy=(xc, y + 0.25),
            xytext=(-4, 0),
            textcoords="offset points",
            ha="right",
            va="bottom",
            fontsize=13,
            color=COLORS["ink"],
            zorder=5,
            bbox=dict(boxstyle="square,pad=0.15", fc="white", ec="none", alpha=0.9),
        )


def nightly(t: pd.DataFrame, tot: pd.Series):
    with mpl.rc_context(TALK_RC):
        fig, ax = plt.subplots()
        # headroom: bars reach ~12 h, then the three staggered storm labels, then the
        # fault brackets at the top
        ymax = 21.4
        _storm_spans(ax, ymax, shade_top=12.3, y_label=12.5)
        spans = outage_spans()
        for _, r in spans.iterrows():
            x0 = pd.Timestamp(r.start) - pd.Timedelta(hours=12)
            x1 = pd.Timestamp(r.end) + pd.Timedelta(hours=12)
            yb = 18.3  # above the storm-period labels
            ax.plot(
                [x0, x0, x1, x1],
                [yb - 0.3, yb, yb, yb - 0.3],
                color=COLORS["ink"],
                lw=1.5,
                solid_capstyle="butt",
                clip_on=False,
            )
            xc = x0 + (x1 - x0) / 2
            a, b = pd.Timestamp(r.start), pd.Timestamp(r.end)
            when = (
                f"{a:%-d %b} – {b:%-d %b}"
                if a.month != b.month
                else f"{a:%-d} – {b:%-d %b}"
            )
            ax.text(
                xc,
                yb + 0.25,
                f"{r.short}\n{when}",
                ha="center",
                va="bottom",
                fontsize=15,
                color=COLORS["ink"],
                linespacing=1.15,
            )
        _stack(ax, t.date, t, 1.0)
        ax.plot(
            t.date, t.night_hours, color=COLORS["ink"], lw=1.0, label=f"night ({NIGHT})"
        )
        xb = pd.Timestamp(str(DAY_OBS_WEATHER_BIT_START))
        ax.axvline(xb, ymax=12.3 / ymax, color=COLORS["ink_secondary"], lw=1.2, ls="--")
        ax.text(
            xb,
            12.45,
            f" WEATHER bit from {xb:%-d %b %Y} →",
            va="bottom",
            ha="left",
            color=COLORS["ink_secondary"],
            fontsize=13,
        )
        xr = pd.Timestamp(str(DAY_OBS_BACK_ON_SKY))
        ax.axvline(xr, ymax=12.3 / ymax, color=COLORS["ink"], lw=1.4, ls=":")
        ax.annotate(
            f"back on sky {xr:%-d %b}",
            xy=(xr, 0),
            xytext=(-6, 6),
            textcoords="offset points",
            va="bottom",
            ha="right",
            color=COLORS["ink"],
            fontsize=13,
            bbox=dict(boxstyle="square,pad=0.15", fc="white", ec="none", alpha=0.9),
        )
        ax.set_ylabel(f"hours per {NIGHT} night")
        ax.set_ylim(0, ymax)
        # ticks stop at the longest night: the headroom above holds annotation only
        ax.set_yticks(np.arange(0, 13, 2))
        ax.set_xlim(
            t.date.min() - pd.Timedelta(days=1), t.date.max() + pd.Timedelta(days=1)
        )
        ax.xaxis.set_major_formatter(mpl.dates.DateFormatter("%b\n%Y"))
        handles_, labels_ = ax.get_legend_handles_labels()
        # legend reads top → bottom like the stack (ROSP-24 precedence), then the night curve
        order = (
            PRECEDENCE[:-1]
            + [DYN_LABEL, PRECEDENCE[-1]]
            + [f"night ({NIGHT})"]  # Dynalene sits with fault + idle
        )
        hl = dict(zip(labels_, handles_))
        ax.legend(
            [hl[k] for k in order],
            order,
            frameon=False,
            ncol=3,
            loc="upper center",
            bbox_to_anchor=(0.5, -0.12),
            handlelength=1.6,
            fontsize=15,
            columnspacing=1.4,
        )
        ax.spines[["top", "right"]].set_visible(False)
        ax.grid(axis="y", alpha=0.6)
        short = {
            "survey (on sky)": "survey",
            "fault + idle": "fault + idle",
            "engineering": "engineering",
            "Focus and Alignment": "focus",
            "planned maintenance": "maintenance",
            "weather": "weather",
        }

        def _line(sel: pd.DataFrame) -> str:
            """Shares over ``sel``, precedence order, categories below 1 % dropped."""
            night = sel.night_hours.sum()
            sh = {lab: sel[col].sum() / night for col, lab, _ in CAT}
            return (
                ", ".join(
                    f"{sh[k]:.0%} {short[k]}" for k in PRECEDENCE if sh[k] >= 0.01
                )
                + f" of {night:.0f} h"
            )

        season = t[t.day_obs <= DAY_OBS_LAST_BEFORE_STORM]
        d0 = pd.Timestamp(str(DAY_OBS_LAST_BEFORE_STORM))
        ax.set_title(
            f"Simonyi night time, {t.date.min():%-d %b %Y} – {t.date.max():%-d %b %Y}",
            loc="left",
            pad=78,  # room for the two share blocks drawn just below
        )
        # Shares as a sub-title: the season line is the one quoted in the deck, so it
        # comes first. One heading + one number line each, four lines in all.
        ax.text(
            0.0,
            1.005,
            f"On sky season to {d0:%-d %b %Y}\n{_line(season)}\n"
            f"Full range, incl. the July storm\n{_line(t)}",
            transform=ax.transAxes,
            ha="left",
            va="bottom",
            fontsize=14,
            color=COLORS["ink_secondary"],
            linespacing=1.45,
        )
        fig.tight_layout()
        _save(fig, f"time_loss_nightly_talk_{TAG}")
        return fig, spans


def monthly(t: pd.DataFrame, min_label: float = 0.10):
    cols = ["night_hours", "dynalene_hours"] + [c for c, _, _ in CAT]
    mo = t.groupby("month")[cols].sum()
    mo_n = t.groupby("month").size()
    with mpl.rc_context(TALK_RC):
        fig, ax = plt.subplots()
        x = np.arange(len(mo))
        _stack(ax, x, mo, 0.8, denom=mo.night_hours.to_numpy())
        bottom = np.zeros(len(mo))
        for col, lab, c in CAT:
            frac = (mo[col] / mo.night_hours).to_numpy()
            for xi, f, b in zip(x, frac, bottom):
                if f >= min_label:
                    ax.text(
                        xi,
                        b + f / 2,
                        f"{f:.0%}",
                        ha="center",
                        va="center",
                        color=COLORS["ink"]
                        if col in ("weather_hours", "planned_maintenance_hours")
                        else "white",
                        fontsize=TALK_RC["xtick.labelsize"],
                    )
            bottom += frac
        ax.set_xticks(x)
        ax.set_xticklabels(
            [
                pd.Timestamp(f"{m // 100}-{m % 100:02d}-01").strftime("%b\n%Y")
                + f"\n({n} n)"
                for m, n in zip(mo.index, mo_n)
            ]
        )
        ax.set_ylim(0, 1)
        _fraction_yaxis(ax)
        handles_, labels_ = ax.get_legend_handles_labels()
        order = PRECEDENCE[:-1] + [DYN_LABEL, PRECEDENCE[-1]]
        hl = dict(zip(labels_, handles_))
        ax.legend(
            [hl[k] for k in order],
            order,
            frameon=False,
            ncol=3,
            loc="upper center",
            bbox_to_anchor=(0.5, -0.18),
            handlelength=1.6,
            fontsize=15,
            columnspacing=1.4,
        )
        ax.spines[["top", "right"]].set_visible(False)
        ax.set_title(
            "Simonyi night time by month (partial months: Oct 2025, Oct 2026)\n"
            "Aug–Sep 2026 and most of Oct: July storm, planned maintenance, recovery",
            fontsize=18,
        )
        fig.tight_layout()
        _save(fig, f"time_loss_monthly_talk_{TAG}")
        return fig, mo


# --------------------------------------------------------------------------- #
# B1, six-bin variant for slide 4 "Where the night goes" (handoff 2026-11-02)  #
# --------------------------------------------------------------------------- #

# TEMPORARY: slide-2 colours, palette violation, see handoff 2026-11-02.
# These are read from the night-definition strip on slide 2 of the LSST@LATAM deck
# so B1 matches it; they deliberately break the Rubin palette. Switching back is one
# line: use CAT instead of SLIDE2_CAT in monthly_6bin(). Do not propagate these to
# rubin_palette.CATEGORY_COLORS or to any other figure.
SLIDE2_COLORS = {
    "Science": "#024243",
    "Engineering": "#045B5C",
    "Alignment": "#058B8C",
    "Fault + idle": "#F5A623",
    # Planned maintenance has no slide-2 colour: it is a tone of the weather grey, so the
    # two "closed" bins read as a pair (Bruno, 2026-11-02)
    "Planned maintenance": "#546E7A",
    "Weather": "#9BAEB8",  # lightened from #78909C (Bruno, 2026-11-02)
}
#: bottom → top of the stack; the legend is drawn in the reverse order so it reads
#: like the bars. One constant, as the handoff asks. Hatches: the two "closed" bins are
#: told apart by direction — weather leans one way, planned maintenance the other.
SLIDE2_CAT = [
    ("survey_plot", "Science", None),
    ("engineering_hours", "Engineering", None),
    ("focus_alignment_hours", "Alignment", None),
    ("fault_plot", "Fault + idle", None),
    ("planned_maintenance_hours", "Planned maintenance", "////"),
    ("weather_hours", "Weather", "\\\\\\\\"),
]
#: in-bar value labels (Bruno, 2026-11-02); the one place below the 10 pt tick floor,
#: because it only has to be legible next to its own bar, not from the back of the room
LABEL_PT = 8
#: no value label below this share of the night (Bruno, 2026-11-02)
LABEL_MIN_FRAC = 0.05
#: 6 × 4 in on a 10 × 5.625 in slide, so type must survive the scale-down.
#: Floor is 10 pt everywhere, per the handoff.
SLIDE_RC = {
    "figure.figsize": (6, 4),
    "font.size": 10,
    "axes.labelsize": 10,
    "xtick.labelsize": 10,
    "ytick.labelsize": 10,
    "legend.fontsize": 10,
    "axes.linewidth": 0.8,
    "hatch.linewidth": 0.6,
    "text.color": COLORS["ink"],
    "axes.labelcolor": COLORS["ink"],
    "axes.edgecolor": COLORS["ink_secondary"],
    "xtick.color": COLORS["ink_secondary"],
    "ytick.color": COLORS["ink_secondary"],
}


def _check_split(t: pd.DataFrame, mo: pd.DataFrame) -> None:
    """The split must not move the other bins. Checked against the bins as ``monthly()``
    (the shared ``CAT``) groups them, not against this function's own columns, so the
    comparison is a real one:

    * Science + Engineering + Alignment == the three on-sky bins of ``CAT``;
    * Weather and Fault + idle identical to ``CAT``'s;
    * the six bins still partition the night.
    """
    ref = t.groupby("month")[["night_hours"] + [c for c, _, _ in CAT]].sum()
    onsky_ref = ref.survey_plot + ref.engineering_hours + ref.focus_alignment_hours
    onsky_new = mo.survey_plot + mo.engineering_hours + mo.focus_alignment_hours
    total = sum(mo[c] for c, _, _ in SLIDE2_CAT)
    d_onsky = (onsky_new - onsky_ref).abs()
    d_weather = (mo.weather_hours - ref.weather_hours).abs()
    d_fault = (mo.fault_plot - ref.fault_plot).abs()
    d_night = (total - ref.night_hours).abs()
    print("\n=== B1 six-bin split check (handoff 2026-11-02) ===")
    print(
        f"{'month':>7} {'on sky':>8} {'Δon sky':>8} {'weather':>8} {'Δwth':>6} "
        f"{'fault':>8} {'Δflt':>6} {'night':>8} {'Σ6':>8} {'Δ':>6}"
    )
    for m in mo.index:
        print(
            f"{m:>7} {onsky_new[m]:8.1f} {d_onsky[m]:8.2f} "
            f"{mo.weather_hours[m]:8.1f} {d_weather[m]:6.2f} "
            f"{mo.fault_plot[m]:8.1f} {d_fault[m]:6.2f} "
            f"{ref.night_hours[m]:8.1f} {total[m]:8.1f} {d_night[m]:6.2f}"
        )
    worst = {
        "on sky": d_onsky.max(),
        "weather": d_weather.max(),
        "fault + idle": d_fault.max(),
        "Σ six bins − night": d_night.max(),
    }
    print(
        "worst |Δ| over all months: "
        + ", ".join(f"{k} {v:.3f} h" for k, v in worst.items())
    )
    bad = {k: v for k, v in worst.items() if v >= 0.05}
    assert not bad, f"the split moved bins it must not: {bad}"


def monthly_6bin(t: pd.DataFrame):
    """B1 for slide 4: the six bins at 6 × 4 in, in the slide-2 colours.

    Separate from ``monthly()`` on purpose — B3 shares ``CAT``/``_stack`` and is out of
    scope for this task, so nothing here touches them. The old file is kept; this one
    saves under ``..._6bin[_white].png`` so the two can be compared.
    """
    cols = ["night_hours"] + [c for c, _, _ in SLIDE2_CAT]
    mo = t.groupby("month")[cols].sum()
    _check_split(t, mo)
    with mpl.rc_context(SLIDE_RC):
        # constrained layout + no bbox_inches="tight" keeps the PNG exactly 6 × 4 in;
        # small pads so the axes fill the canvas (Bruno, 2026-11-02: minimise empty space)
        fig, ax = plt.subplots(layout="constrained")
        fig.get_layout_engine().set(w_pad=0.01, h_pad=0.01, wspace=0, hspace=0)
        x = np.arange(len(mo))
        bottom = np.zeros(len(mo))
        denom = mo.night_hours.to_numpy()
        labelled = []  # (xi, centre, text) per segment that gets a value label
        for col, lab, hatch in SLIDE2_CAT:
            c = SLIDE2_COLORS[lab]
            y = (mo[col] / denom).to_numpy()
            # thin white edge between segments: the mitigation for the low ΔE pairs
            # (Engineering↔Science, Alignment↔Weather) the validator flags
            ax.bar(
                x,
                y,
                bottom=bottom,
                width=0.94,  # wide bars: the gaps were dead space (Bruno, 2026-11-02)
                color=c,
                label=lab,
                linewidth=0.6,
                edgecolor="white",
                hatch=hatch,
            )
            # value labels on the four coloured bins only: white type is unreadable on
            # the two light greys, and those bins are the ones the talk does not discuss
            # (Bruno, 2026-11-02). ``b`` is the bottom *before* the increment below, so
            # ``b + f / 2`` is the segment midpoint — with va="center" the label sits in
            # the middle of its own segment, not of the bar.
            if col not in ("weather_hours", "planned_maintenance_hours"):
                for xi, f, b in zip(x, y, bottom):
                    labelled.append((xi, b + f / 2, f"{f:.0%}", f))
            bottom += y
        ax.set_xticks(x)
        # one line per label, year only where it changes: a second line of tick text
        # was costing ~0.3 in of plot height for nothing
        ax.set_xticklabels(
            [
                pd.Timestamp(f"{m // 100}-{m % 100:02d}-01").strftime(
                    "%b\n%Y" if i == 0 or m % 100 == 1 else "%b"
                )
                for i, m in enumerate(mo.index)
            ]
        )
        ax.set_ylim(0, 1)
        # bars run edge to edge; no empty margin either side
        ax.set_xlim(-0.5 - 0.03, len(mo) - 0.5 + 0.03)
        _fraction_yaxis(ax)
        # Value labels, white, centred on their own segment. Two gates (Bruno,
        # 2026-11-02): a hard editorial floor of 5 % — below that the number is not worth
        # reading off the slide — and a measured fit test, LABEL_PT + 2 pt converted to an
        # axis fraction through the drawn axes height, so a segment never gets a label
        # taller than itself even if the figure or font size changes. At 6 × 4 in the 5 %
        # floor is the binding one.
        fig.canvas.draw()  # axes geometry must be final before measuring
        ax_h_pt = ax.get_window_extent().height / fig.dpi * 72.0
        min_frac = max(LABEL_MIN_FRAC, (LABEL_PT + 2.0) / ax_h_pt)
        for xi, centre, text, frac in labelled:
            if frac >= min_frac:
                ax.text(
                    xi,
                    centre,
                    text,
                    ha="center",
                    va="center",
                    color="white",
                    fontsize=LABEL_PT,
                )
        # Legend in stack order (top of the stack first), three columns so it is two
        # rows and steals less height than the 2 × 3 version. matplotlib fills a legend
        # column-first, so transpose the order to make it read left → right, top →
        # bottom: Weather, Planned maintenance, Fault + idle / Alignment, Engineering,
        # Science.
        handles_, labels_ = ax.get_legend_handles_labels()
        hl = dict(zip(labels_, handles_))
        stack_order = [lab for _, lab, _ in SLIDE2_CAT][::-1]
        ncol, nrow = 3, 2
        order = [
            stack_order[r * ncol + c]
            for c in range(ncol)
            for r in range(nrow)
            if r * ncol + c < len(stack_order)
        ]
        ax.legend(
            [hl[k] for k in order],
            order,
            frameon=False,
            ncol=3,
            loc="upper center",
            bbox_to_anchor=(0.5, -0.11),
            handlelength=1.3,
            handletextpad=0.5,
            columnspacing=1.0,
            labelspacing=0.25,
            borderpad=0.0,
        )
        ax.spines[["top", "right"]].set_visible(False)
        # no title and no in-bar labels: the numbers go on the slide, not in the figure
        # (Bruno, 2026-11-02)
        _save(fig, f"time_loss_monthly_talk_{TAG}_6bin", dpi=300)
        return fig, mo


def main():
    t = load_per_night()
    tot = t[["night_hours", "dynalene_hours"] + [c for c, _, _ in CAT]].sum()
    print(tot.round(1).to_dict())
    print(
        {k: f"{v / tot.night_hours:.1%}" for k, v in tot.items() if k != "night_hours"}
    )
    pt = _period_table(t)
    print("\n=== nights and hours per period (handoff 2026-11-01) ===")
    print(pt.to_string(index=False))
    pt.to_csv(PROC / "per_period.csv", index=False)
    print("wrote", PROC / "per_period.csv")
    # the override is a rule, not a measurement: say what it displaced
    ov = t[t.storm_override.fillna("") != ""]
    conflict = ov[
        (ov.override_onsky_hours > 0.01) | (ov.override_operational_hours > 0.01)
    ]
    print(
        f"\nstorm rule applied to {len(ov)} nights; "
        f"displaced on-sky {ov.override_onsky_hours.sum():.1f} h, "
        f"OPERATIONAL {ov.override_operational_hours.sum():.1f} h, "
        f"FAULT {ov.override_fault_hours.sum():.1f} h"
    )
    if len(conflict):
        print("nights where the rule disagrees with the data:")
        print(
            conflict[
                [
                    "day_obs",
                    "storm_override",
                    "override_onsky_hours",
                    "override_operational_hours",
                ]
            ].to_string(index=False)
        )
    _, spans = nightly(t, tot)
    print()
    print(spans[["start_date", "end_date", "short", "fracas"]].to_string(index=False))
    _, mo = monthly(t)
    print(
        (mo[[c for c, _, _ in CAT]].div(mo.night_hours, axis=0) * 100)
        .round(0)
        .astype(int)
        .to_string()
    )
    # slide 4: the same months in six bins at 6 × 4 in (handoff 2026-11-02)
    _, mo6 = monthly_6bin(t)
    cols6 = [c for c, _, _ in SLIDE2_CAT]
    print("\n=== B1 six-bin: hours per bin per month ===")
    print(mo6[["night_hours"] + cols6].round(1).to_string())
    print("\n=== B1 six-bin: % of night per bin per month ===")
    print((mo6[cols6].div(mo6.night_hours, axis=0) * 100).round(1).to_string())
    tot6 = mo6[["night_hours"] + cols6].sum()
    print("\n=== B1 six-bin: full-range totals ===")
    for c, lab, _ in SLIDE2_CAT:
        print(f"  {lab:<22} {tot6[c]:7.1f} h  {tot6[c] / tot6.night_hours:5.1%}")
    print(f"  {'−12° night':<22} {tot6.night_hours:7.1f} h")


if __name__ == "__main__":
    main()
