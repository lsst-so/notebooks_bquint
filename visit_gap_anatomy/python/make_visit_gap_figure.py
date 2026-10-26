"""Visit-gap distribution and weekly trend for the LSST@LATAM 2026 talk (slide 10).

Data: ConsDB ``cdb_lsstcam.visit1`` rows cached in ``../data/visit1_<min>_<max>.parquet``
(``airmass > 0``, ``img_type`` in acq/science/cwfs/focus; same query as the on-sky
utilization timeline). The gap is ``obs_start`` of a visit minus ``obs_end`` of the
previous visit of the same ``day_obs`` (rubin_nights ``augment_visits`` definition;
``obs_end - obs_start = exp_time + 0.93 s``, the readout), **reset at the start of each
night**. Only pairs where both visits belong to a survey program (Feature Based
Scheduler blocks, list copied from ``nightly_survey_speed/utils.py``) are kept.

Outputs ``../figures/visit_gap_talk_<min>-<max>.png`` and ``_white``: left, the gap
histogram with the OSS-REQ-0289 5 s line and the median; right, weekly median with the
25–75 % band. Run: ``python visit_gap_anatomy/python/make_visit_gap_figure.py``.
"""

from __future__ import annotations

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

DAY_OBS_MIN, DAY_OBS_MAX = 20251026, 20260714
LSST_START = 20260629
REQ_GAP_S = 5.0  # OSS-REQ-0289
SURVEY_PROGRAMS = (
    "BLOCK-407",
    "BLOCK-408",
    "BLOCK-416",
    "BLOCK-417",
    "BLOCK-419",
    "BLOCK-421",
)
SECOND_SETTLE = (
    14.0,
    20.0,
)  # gaps with a second settle after a late AOS + pointing offset
HIST_MAX_S = 40.0

DATA = ROOT / "data" / f"visit1_{DAY_OBS_MIN}_{DAY_OBS_MAX}.parquet"
FIG = ROOT / "figures"
FIG.mkdir(exist_ok=True)
TAG = f"{DAY_OBS_MIN}-{DAY_OBS_MAX}"

C = {
    "gap": rp.CATEGORICAL[0],
    "settle": rp.CATEGORICAL[1],
    "req": rp.CATEGORICAL[3],
    "ink": rp.NEUTRALS["ink"],
    "ink2": rp.NEUTRALS["ink_secondary"],
    "muted": rp.NEUTRALS["muted"],
    "grid": rp.NEUTRALS["grid"],
}
TALK_RC = {
    "figure.figsize": (13.33, 7.5),
    "font.size": 18,
    "axes.labelsize": 20,
    "axes.titlesize": 22,
    "xtick.labelsize": 16,
    "ytick.labelsize": 16,
    "legend.fontsize": 16,
    "axes.linewidth": 1.2,
    "text.color": C["ink"],
    "axes.labelcolor": C["ink"],
    "axes.edgecolor": C["ink2"],
    "xtick.color": C["ink2"],
    "ytick.color": C["ink2"],
    "grid.color": C["grid"],
}


def survey_gaps() -> pd.DataFrame:
    v = pd.read_parquet(DATA).sort_values("obs_start_mjd").reset_index(drop=True)
    gap = (v.obs_start_mjd - v.obs_end_mjd.shift()) * 86400.0
    same_night = v.day_obs == v.day_obs.shift()
    surv = v.science_program.isin(SURVEY_PROGRAMS)
    keep = same_night & surv & surv.shift(fill_value=False)
    g = v.loc[
        keep, ["visit_id", "day_obs", "obs_start_mjd", "science_program", "exp_time"]
    ].copy()
    g["gap_s"] = gap[keep]
    g["date"] = pd.to_datetime(g.day_obs.astype(str))
    g["week"] = g.date.dt.to_period("W-SUN").dt.start_time  # weeks start Monday
    return g


def weekly(g: pd.DataFrame, min_visits: int = 100) -> pd.DataFrame:
    w = g.groupby("week").gap_s.agg(
        n="size",
        median="median",
        p25=lambda x: x.quantile(0.25),
        p75=lambda x: x.quantile(0.75),
    )
    return w[w.n >= min_visits]


def make_figure(g: pd.DataFrame, w: pd.DataFrame):
    med = g.gap_s.median()
    n_all = len(g)
    f_settle = g.gap_s.between(*SECOND_SETTLE).mean()
    f_req = (g.gap_s < REQ_GAP_S).mean()
    f_over = (g.gap_s > HIST_MAX_S).mean()
    with mpl.rc_context(TALK_RC):
        fig, (ax, ax2) = plt.subplots(
            1, 2, gridspec_kw={"width_ratios": [1, 1.25], "wspace": 0.22}
        )

        # --- left: histogram
        bins = np.arange(0, HIST_MAX_S + 0.5, 0.5)
        counts, edges = np.histogram(g.gap_s[g.gap_s < HIST_MAX_S], bins=bins)
        frac = counts / n_all
        centers = 0.5 * (edges[:-1] + edges[1:])
        in_settle = (centers >= SECOND_SETTLE[0]) & (centers <= SECOND_SETTLE[1])
        ax.bar(
            centers[~in_settle],
            frac[~in_settle],
            width=0.5,
            color=C["gap"],
            linewidth=0,
        )
        ax.bar(
            centers[in_settle],
            frac[in_settle],
            width=0.5,
            color=C["settle"],
            linewidth=0,
        )
        ymax = frac.max() * 1.3
        ax.set_ylim(0, ymax)
        ax.set_xlim(0, HIST_MAX_S)
        ax.axvline(REQ_GAP_S, color=C["req"], lw=2.5)
        ax.text(
            REQ_GAP_S + 0.6,
            ymax * 0.98,
            f"requirement < {REQ_GAP_S:.0f} s",
            ha="left",
            va="top",
            color=C["req"],
            fontsize=16,
        )
        ax.axvline(med, color=C["ink"], lw=2, ls=(0, (4, 3)))
        ax.text(
            med + 0.6,
            ymax * 0.84,
            f"median {med:.1f} s",
            ha="left",
            va="top",
            color=C["ink"],
            fontsize=16,
        )
        ax.text(
            SECOND_SETTLE[1] + 1.0,
            0.03,
            f"second settle\n{SECOND_SETTLE[0]:.0f}–{SECOND_SETTLE[1]:.0f} s: {f_settle:.0%} of visits",
            ha="left",
            va="bottom",
            color=C["settle"],
            fontsize=15,
            linespacing=1.1,
        )
        ax.set_xlabel("gap between visits (s)")
        ax.set_ylabel("fraction of visits")
        ax.yaxis.set_major_formatter(mpl.ticker.PercentFormatter(1.0, decimals=0))
        ax.spines[["top", "right"]].set_visible(False)
        ax.grid(axis="y", alpha=0.6)
        fig.text(
            0.02,
            0.01,
            f"{n_all:,} visit pairs; {f_over:.1%} of gaps are longer than {HIST_MAX_S:.0f} s "
            f"and off the histogram scale; weeks with fewer than 100 survey visits are not plotted",
            ha="left",
            va="bottom",
            color=C["ink2"],
            fontsize=13,
        )

        # --- right: weekly median
        x = w.index + pd.Timedelta(days=3.5)
        ax2.fill_between(
            x, w.p25, w.p75, color=C["gap"], alpha=0.2, lw=0, label="25–75 % of visits"
        )
        ax2.plot(
            x,
            w["median"],
            color=C["gap"],
            lw=3,
            marker="o",
            ms=7,
            label="weekly median",
        )
        ax2.axhline(
            REQ_GAP_S, color=C["req"], lw=2.5, label=f"requirement < {REQ_GAP_S:.0f} s"
        )
        ax2.set_ylim(0, 25)
        ax2.set_xlim(x.min() - pd.Timedelta(days=7), x.max() + pd.Timedelta(days=7))
        xl = pd.Timestamp(str(LSST_START))
        ax2.axvline(xl, color=C["ink2"], lw=1.2, ls="--")
        ax2.text(
            xl,
            24.5,
            "LSST start\n29 Jun ",
            ha="right",
            va="top",
            color=C["ink2"],
            fontsize=14,
            linespacing=1.1,
        )
        ax2.set_ylabel("gap (s)")
        ax2.xaxis.set_major_locator(mpl.dates.MonthLocator(interval=2))
        ax2.xaxis.set_major_formatter(mpl.dates.DateFormatter("%b\n%Y"))
        ax2.spines[["top", "right"]].set_visible(False)
        ax2.grid(axis="y", alpha=0.6)
        ax2.legend(frameon=False, loc="upper left", ncol=1, handlelength=1.6)
        # Direct label for the second-settle episode (June 2026)
        jun = w[(w.index >= "2026-05-25") & (w.index <= "2026-06-28")]
        if len(jun):
            i = jun["median"].idxmax()
            ax2.annotate(
                "second settle\non most visits",
                (i + pd.Timedelta(days=3.5), jun.loc[i, "median"]),
                xytext=(-20, 10),
                textcoords="offset points",
                ha="right",
                va="bottom",
                color=C["settle"],
                fontsize=14,
                linespacing=1.1,
            )

        fig.suptitle(
            f"Time between consecutive survey visits, {g.date.min():%-d %b %Y} – {g.date.max():%-d %b %Y}",
            x=0.02,
            y=0.985,
            ha="left",
            fontsize=22,
            color=C["ink"],
        )
        fig.text(
            0.02,
            0.925,
            "ConsDB visit1, scheduler-driven survey blocks only; gap = start of a visit − end of the "
            "previous one, reset each night",
            ha="left",
            va="top",
            fontsize=15,
            color=C["ink2"],
        )
        fig.subplots_adjust(left=0.08, right=0.98, bottom=0.2, top=0.86, wspace=0.22)
        stem = FIG / f"visit_gap_talk_{TAG}"
        fig.savefig(f"{stem}.png", dpi=200, transparent=True)
        fig.savefig(f"{stem}_white.png", dpi=200, facecolor="white")
        print("wrote", stem, "[_white].png")
    return dict(
        n=n_all,
        median_s=med,
        frac_below_req=f_req,
        frac_second_settle=f_settle,
        frac_over_hist=f_over,
    )


def main():
    g = survey_gaps()
    w = weekly(g)
    stats = make_figure(g, w)
    print({k: (round(v, 3) if isinstance(v, float) else v) for k, v in stats.items()})
    print(
        "median by period: early ops",
        round(g[g.day_obs < LSST_START].gap_s.median(), 2),
        "| LSST",
        round(g[g.day_obs >= LSST_START].gap_s.median(), 2),
    )
    print(
        "weekly median range:",
        w["median"].round(2).min(),
        "-",
        w["median"].round(2).max(),
    )
    w.round(2).to_csv(ROOT / "data" / f"visit_gap_weekly_{TAG}.csv")
    g.gap_s.describe(percentiles=[0.1, 0.25, 0.5, 0.75, 0.9]).round(2).to_csv(
        ROOT / "data" / f"visit_gap_summary_{TAG}.csv"
    )


if __name__ == "__main__":
    main()
