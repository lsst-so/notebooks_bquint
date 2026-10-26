"""LSST@LATAM 2026 talk figures from ``data/processed/per_night.csv``.

Two figures, each saved transparent and as a ``_white`` variant (16:9, large type):

* ``time_loss_nightly_talk_<tag>.png`` — hours per night on sky / weather / fault + idle,
  the −12° night-length curve (ROSP-22 observable night, ``NIGHT_SUN_ALT``), the WEATHER-bit date, and three long-outage annotations
  read from ``data/downtime_annotations.csv`` (copied from ``nightly_survey_speed/``;
  no imports across investigation folders).
* ``time_loss_monthly_talk_<tag>.png`` — monthly fractions; slice labels are dropped
  below 10 % so none sits on a bar edge.

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
    DAY_OBS_MAX,
    DAY_OBS_MIN,
    DAY_OBS_WEATHER_BIT_START,
    NIGHT_SUN_ALT,
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
    "text.color": COLORS["ink"],
    "axes.labelcolor": COLORS["ink"],
    "axes.edgecolor": COLORS["ink_secondary"],
    "xtick.color": COLORS["ink_secondary"],
    "ytick.color": COLORS["ink_secondary"],
    "grid.color": COLORS["grid"],
}


def load_per_night() -> pd.DataFrame:
    t = pd.read_csv(PROC / "per_night.csv")
    t["date"] = pd.to_datetime(t.day_obs.astype(str))
    t["month"] = t.day_obs // 100
    return t


CAT = [
    ("on_sky_hours", "on sky", COLORS["on_sky"]),
    ("weather_hours", "weather", COLORS["weather"]),
    ("nonweather_loss_hours", "fault + idle", COLORS["nonweather_loss"]),
]


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


def nightly(t: pd.DataFrame, tot: pd.Series):
    with mpl.rc_context(TALK_RC):
        fig, ax = plt.subplots()
        ymax = 14.8
        # Outage bands first, behind the data.
        spans = outage_spans()
        for _, r in spans.iterrows():
            x0 = pd.Timestamp(r.start) - pd.Timedelta(hours=12)
            x1 = pd.Timestamp(r.end) + pd.Timedelta(hours=12)
            # Bracket along the top edge: a horizontal rule with short ticks, label above it.
            yb = 12.3
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
        bottom = np.zeros(len(t))
        for col, lab, c in CAT:
            ax.bar(
                t.date,
                t[col],
                bottom=bottom,
                width=1.0,
                color=c,
                label=lab,
                linewidth=0,
            )
            bottom += t[col].to_numpy()
        ax.plot(
            t.date, t.night_hours, color=COLORS["ink"], lw=1.0, label=f"night ({NIGHT})"
        )
        xb = pd.Timestamp(str(DAY_OBS_WEATHER_BIT_START))
        ax.axvline(xb, ymax=11.8 / ymax, color=COLORS["ink_secondary"], lw=1.2, ls="--")
        ax.text(
            xb,
            11.6,
            f" WEATHER bit from {xb:%-d %b %Y} →",
            va="top",
            ha="left",
            color=COLORS["ink_secondary"],
            fontsize=13,
        )
        ax.set_ylabel("hours per night")
        ax.set_ylim(0, ymax)
        ax.set_xlim(
            t.date.min() - pd.Timedelta(days=1), t.date.max() + pd.Timedelta(days=1)
        )
        ax.xaxis.set_major_formatter(mpl.dates.DateFormatter("%b\n%Y"))
        ax.legend(
            frameon=False, ncol=4, loc="upper center", bbox_to_anchor=(0.5, -0.14)
        )
        ax.spines[["top", "right"]].set_visible(False)
        ax.grid(axis="y", alpha=0.6)
        share = {lab: t[col].sum() / tot.night_hours for col, lab, _ in CAT}
        ax.set_title(
            f"Simonyi night time, {t.date.min():%-d %b %Y} – {t.date.max():%-d %b %Y}\n"
            + ", ".join(f"{v:.0%} {k}" for k, v in share.items())
            + f" (of {tot.night_hours:.0f} h between {NIGHT} twilights)",
            loc="left",
        )
        fig.tight_layout()
        _save(fig, f"time_loss_nightly_talk_{TAG}")
        return fig, spans


def monthly(t: pd.DataFrame, min_label: float = 0.10):
    mo = t.groupby("month")[
        ["night_hours", "on_sky_hours", "weather_hours", "nonweather_loss_hours"]
    ].sum()
    mo_n = t.groupby("month").size()
    with mpl.rc_context(TALK_RC):
        fig, ax = plt.subplots()
        x = np.arange(len(mo))
        bottom = np.zeros(len(mo))
        for col, lab, c in CAT:
            frac = (mo[col] / mo.night_hours).to_numpy()
            ax.bar(x, frac, bottom=bottom, color=c, label=lab, width=0.8, linewidth=0)
            for xi, f, b in zip(x, frac, bottom):
                if f >= min_label:
                    ax.text(
                        xi,
                        b + f / 2,
                        f"{f:.0%}",
                        ha="center",
                        va="center",
                        color="white",
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
        ax.legend(frameon=False, ncol=3, loc="upper center", bbox_to_anchor=(0.5, -0.2))
        ax.spines[["top", "right"]].set_visible(False)
        ax.set_title("Simonyi night time by month (partial months: Oct 2025, Jul 2026)")
        fig.tight_layout()
        _save(fig, f"time_loss_monthly_talk_{TAG}")
        return fig


def main():
    t = load_per_night()
    tot = t[
        ["night_hours", "on_sky_hours", "weather_hours", "nonweather_loss_hours"]
    ].sum()
    print(tot.round(1).to_dict())
    print(
        {k: f"{v / tot.night_hours:.1%}" for k, v in tot.items() if k != "night_hours"}
    )
    _, spans = nightly(t, tot)
    print(spans[["start_date", "end_date", "short", "fracas"]].to_string(index=False))
    monthly(t)


if __name__ == "__main__":
    main()
