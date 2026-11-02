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


def _save(fig, stem: str):
    fig.savefig(FIG / f"{stem}.png", dpi=200, transparent=True)
    fig.savefig(FIG / f"{stem}_white.png", dpi=200, facecolor="white")
    print("wrote", FIG / f"{stem}[_white].png")


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
        ax.set_ylabel(f"fraction of {NIGHT} night")
        ax.yaxis.set_major_formatter(mpl.ticker.PercentFormatter(1.0))
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


if __name__ == "__main__":
    main()
