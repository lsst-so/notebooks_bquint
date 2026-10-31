"""Engineering vs survey on-sky hours per week, with the LSST engineering-time policy
line (LSST@LATAM 2026 talk, slide 11).

Data: ConsDB ``cdb_lsstcam.visit1`` rows cached in ``../data/visit1_<min>_<max>.parquet``
(``airmass > 0``, ``img_type`` in acq/science/cwfs/focus; same query and the same three
categories as the on-sky utilization timeline — list copied from
``nightly_survey_speed/utils.py``, no import across folders):

* Survey Programs — scheduler-driven survey blocks (BLOCK-407/408/416/417/419/421)
* Focus and Alignment — BLOCK-T539
* Engineering — every other on-sky visit

Hours are **telescope time on sky**: consecutive visits of the same category within one
night form a block (gaps under ``BLOCK_GAP_S`` are bridged); the block lasts from the
start of its first visit to the end of its last. Shutter-open hours (sum of exposure
times) are also written to the weekly CSV for reference; they are ~1.5–1.9x smaller.

Policy numbers (Confluence 1802141753, "On-sky engineering time during LSST") are
``[VERIFY]``: 8 h/week pre-authorised, 16 h in any 4 weeks, <= 52 engineering nights in
the first six months (simulations assumed 26).

Outputs ``../figures/engineering_hours_weekly_talk_<min>-<max>.png`` and ``_white``
(figure B10) and ``engineering_hours_weekly_policy_<min>-<max>[_white].png`` (figure B10b:
same bars, the policy drawn on the plot — 8 h line solid only from the LSST start,
"LSST start · policy applies" marker, 16 h / 4 weeks and the 52-night envelope as text,
engineering hours labelled on the three LSST weeks and the 9 Mar peak).
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
SURVEY_PROGRAMS = (
    "BLOCK-407",
    "BLOCK-408",
    "BLOCK-416",
    "BLOCK-417",
    "BLOCK-419",
    "BLOCK-421",
)
FOCUS_PROGRAMS = ("BLOCK-T539",)
BLOCK_GAP_S = 600.0

POLICY_WEEKLY_H = 8.0  # [VERIFY] pre-authorised on-sky engineering, hours per week
POLICY_4WEEK_H = 16.0  # [VERIFY] cap over any four weeks
POLICY_NIGHTS = (
    52,
    26,
)  # [VERIFY] max engineering nights in the first six months; nights assumed by the sims

DATA = ROOT / "data" / f"visit1_{DAY_OBS_MIN}_{DAY_OBS_MAX}.parquet"
FIG = ROOT / "figures"
FIG.mkdir(exist_ok=True)
TAG = f"{DAY_OBS_MIN}-{DAY_OBS_MAX}"

CATS = [
    "Engineering",
    "Focus and Alignment",
    "Survey Programs",
]  # stack order, bottom first: engineering sits on the policy line
C = {  # category colours shared by every figure (rubin_palette.CATEGORY_COLORS)
    "Survey Programs": rp.CATEGORY_COLORS["survey"],
    "Focus and Alignment": rp.CATEGORY_COLORS["focus"],
    "Engineering": rp.CATEGORY_COLORS["engineering"],
    "policy": rp.CATEGORICAL[3],
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


def categorize(v: pd.DataFrame) -> pd.DataFrame:
    prog = v.science_program.astype("string")
    cat = np.where(
        prog.isin(FOCUS_PROGRAMS),
        "Focus and Alignment",
        np.where(prog.isin(SURVEY_PROGRAMS), "Survey Programs", "Engineering"),
    )
    v = v.assign(category=pd.Categorical(cat, categories=CATS))
    v["date"] = pd.to_datetime(v.day_obs.astype(str))
    v["week"] = v.date.dt.to_period("W-SUN").dt.start_time  # weeks start on Monday
    return v


def weekly_hours(v: pd.DataFrame) -> pd.DataFrame:
    v = v.sort_values("obs_start_mjd").reset_index(drop=True)
    gap_s = (v.obs_start_mjd - v.obs_end_mjd.shift()) * 86400.0
    new_block = (
        (gap_s > BLOCK_GAP_S)
        | (v.category != v.category.shift())
        | (v.day_obs != v.day_obs.shift())
    )
    v["block"] = new_block.cumsum()
    blocks = v.groupby("block").agg(
        category=("category", "first"),
        week=("week", "first"),
        day_obs=("day_obs", "first"),
        t0=("obs_start_mjd", "min"),
        t1=("obs_end_mjd", "max"),
    )
    blocks["hours"] = (blocks.t1 - blocks.t0) * 24.0
    on_sky = (
        blocks.groupby(["week", "category"], observed=False)
        .hours.sum()
        .unstack(fill_value=0.0)
    )
    shutter = (
        v.groupby(["week", "category"], observed=False)
        .exp_time.sum()
        .unstack(fill_value=0.0)
        / 3600.0
    )
    nights = v.groupby("week").day_obs.nunique().rename("nights_with_visits")
    eng_nights = (
        v[v.category == "Engineering"]
        .groupby("week")
        .day_obs.nunique()
        .rename("nights_with_engineering")
    )
    out = (
        on_sky.add_prefix("on_sky_h_")
        .join(shutter.add_prefix("shutter_h_"))
        .join(nights)
        .join(eng_nights)
    )
    return out.fillna(0.0)


def make_figure(w: pd.DataFrame):
    weeks = pd.date_range(w.index.min(), w.index.max(), freq="7D")
    w = w.reindex(weeks, fill_value=0.0)
    x = weeks + pd.Timedelta(days=3.5)
    cols = [f"on_sky_h_{c}" for c in CATS]
    with mpl.rc_context(TALK_RC):
        fig, ax = plt.subplots()
        bottom = np.zeros(len(w))
        for c, col in zip(CATS, cols):
            ax.bar(
                x, w[col], bottom=bottom, width=6.2, color=C[c], label=c, linewidth=0
            )
            bottom += w[col].to_numpy()
        ymax = bottom.max() * 1.18
        ax.set_ylim(0, ymax)
        # policy line
        ax.axhline(POLICY_WEEKLY_H, color=C["policy"], lw=2.5, ls=(0, (6, 3)), zorder=5)
        ax.text(
            x[0] - pd.Timedelta(days=3),
            ymax * 0.99,
            f"LSST policy (dashed line): {POLICY_WEEKLY_H:.0f} h of on-sky engineering per week pre-authorised,\n"
            f"{POLICY_4WEEK_H:.0f} h in any four weeks",
            ha="left",
            va="top",
            color=C["policy"],
            fontsize=15,
            linespacing=1.15,
        )
        # LSST start
        xl = pd.Timestamp(str(LSST_START))
        ax.axvline(xl, color=C["ink2"], lw=1.2, ls="--")
        ax.text(
            xl - pd.Timedelta(days=2),
            ymax * 0.98,
            "LSST start\n29 Jun 2026",
            ha="right",
            va="top",
            color=C["ink2"],
            fontsize=15,
            linespacing=1.1,
        )
        # Early-ops engineering block (Mar 2026) direct label
        eng = w["on_sky_h_Engineering"]
        i = eng.idxmax()
        ax.annotate(
            "AOS stability\ntests",
            (i + pd.Timedelta(days=3.5), w.loc[i, cols].sum()),
            xytext=(0, 8),
            textcoords="offset points",
            ha="center",
            va="bottom",
            color=C["Engineering"],
            fontsize=15,
            linespacing=1.1,
        )
        ax.set_ylabel("telescope hours on sky per week")
        ax.set_xlim(x.min() - pd.Timedelta(days=5), x.max() + pd.Timedelta(days=5))
        ax.xaxis.set_major_locator(mpl.dates.MonthLocator())
        ax.xaxis.set_major_formatter(mpl.dates.DateFormatter("%b\n%Y"))
        ax.spines[["top", "right"]].set_visible(False)
        ax.grid(axis="y", alpha=0.6)
        ax.legend(
            frameon=False, ncol=3, loc="upper center", bbox_to_anchor=(0.5, -0.16)
        )
        ax.set_title(
            f"On-sky time by visit category, week by week, {weeks.min():%-d %b %Y} – {(weeks.max() + pd.Timedelta(days=6)):%-d %b %Y}",
            loc="left",
        )
        fig.text(
            0.01,
            0.01,
            "ConsDB visit1 on-sky visits; hours = first-to-last visit of consecutive same-category visits "
            f"(gaps under {BLOCK_GAP_S / 60:.0f} min bridged). Policy: <= {POLICY_NIGHTS[0]} engineering nights "
            f"in the first six months of LSST (simulations assumed {POLICY_NIGHTS[1]}). Policy numbers to verify "
            "(Confluence 1802141753).",
            ha="left",
            va="bottom",
            color=C["ink2"],
            fontsize=12,
            wrap=True,
        )
        fig.subplots_adjust(left=0.07, right=0.98, bottom=0.25, top=0.9)
        stem = FIG / f"engineering_hours_weekly_talk_{TAG}"
        fig.savefig(f"{stem}.png", dpi=200, transparent=True)
        fig.savefig(f"{stem}_white.png", dpi=200, facecolor="white")
        print("wrote", stem, "[_white].png")


def make_policy_figure(w: pd.DataFrame):
    """B10b: the B10 bars with the policy drawn on the figure (LSST@LATAM 2026-10-26)."""
    weeks = pd.date_range(w.index.min(), w.index.max(), freq="7D")
    w = w.reindex(weeks, fill_value=0.0)
    x = weeks + pd.Timedelta(days=3.5)
    cols = [f"on_sky_h_{c}" for c in CATS]
    xl = pd.Timestamp(str(LSST_START))
    x0 = x.min() - pd.Timedelta(days=5)
    x1 = x.max() + pd.Timedelta(days=5)
    with mpl.rc_context(TALK_RC):
        fig, ax = plt.subplots()
        bottom = np.zeros(len(w))
        for c, col in zip(CATS, cols):
            ax.bar(
                x, w[col], bottom=bottom, width=6.2, color=C[c], label=c, linewidth=0
            )
            bottom += w[col].to_numpy()
        ymax = bottom.max() * 1.18
        ax.set_ylim(0, ymax)
        ax.set_xlim(x0, x1)
        # 8 h/week: reference (light grey dashed) before the LSST start, policy (solid) after
        ax.plot(
            [x0, xl],
            [POLICY_WEEKLY_H] * 2,
            color=C["muted"],
            lw=1.8,
            ls=(0, (6, 3)),
            zorder=5,
        )
        ax.plot([xl, x1], [POLICY_WEEKLY_H] * 2, color=C["policy"], lw=3.0, zorder=5)
        ax.annotate(
            f"{POLICY_WEEKLY_H:.0f} h/week\npre-authorized (RSO)\n{POLICY_4WEEK_H:.0f} h per 4 weeks",
            xy=(x1, POLICY_WEEKLY_H),
            xytext=(6, 4),
            textcoords="offset points",
            ha="left",
            va="top",
            color=C["policy"],
            fontsize=15,
            linespacing=1.15,
            annotation_clip=False,
        )
        # LSST start marker
        ax.axvline(xl, color=C["ink2"], lw=1.2, ls="--")
        ax.text(
            xl - pd.Timedelta(days=2),
            ymax * 0.98,
            "LSST start\npolicy applies\n29 Jun 2026",
            ha="right",
            va="top",
            color=C["ink2"],
            fontsize=15,
            linespacing=1.1,
        )
        # envelope box, top left
        ax.text(
            0.01,
            0.98,
            f"Envelope: {POLICY_NIGHTS[0]} full-night equivalents\nin the first 6 months of LSST\n"
            f"(simulations assumed {POLICY_NIGHTS[1]})",
            transform=ax.transAxes,
            ha="left",
            va="top",
            fontsize=14,
            color=C["ink"],
            linespacing=1.15,
            bbox=dict(facecolor="white", edgecolor=C["grid"], boxstyle="round,pad=0.4"),
        )
        # direct labels: engineering hours on the LSST weeks and on the 9 Mar peak
        eng = w["on_sky_h_Engineering"]
        tot = w[cols].sum(axis=1)
        for i in w.index[w.index >= xl - pd.Timedelta(days=6)]:
            first_lsst_week = i == xl
            ax.annotate(
                f"{eng[i]:.1f} h",
                (i + pd.Timedelta(days=3.5), tot[i]),
                # the week of 29 Jun starts at the LSST line: left-align its label just
                # right of the line so the text sits on that bar, not across the marker
                xytext=(5 if first_lsst_week else 0, 5),
                textcoords="offset points",
                ha="left" if first_lsst_week else "center",
                va="bottom",
                color=C["Engineering"],
                fontsize=14,
            )
        i = eng.idxmax()
        # the 9 Mar peak label goes above the neighbouring bars (2 Mar, 16 Mar, 6 Apr are
        # taller than the 9 Mar total), with a short vertical leader down to the bar
        ax.annotate(
            f"AOS stability tests\n{eng[i]:.0f} h engineering",
            (i + pd.Timedelta(days=3.5), tot[i] + 0.8),
            xytext=(i + pd.Timedelta(days=3.5), ymax * 0.875),
            textcoords="data",
            ha="center",
            va="bottom",
            color=C["Engineering"],
            fontsize=15,
            linespacing=1.1,
            arrowprops=dict(
                arrowstyle="-", color=C["Engineering"], lw=1.0, shrinkA=2, shrinkB=0
            ),
        )
        ax.set_ylabel("telescope hours on sky per week")
        ax.xaxis.set_major_locator(mpl.dates.MonthLocator())
        ax.xaxis.set_major_formatter(mpl.dates.DateFormatter("%b\n%Y"))
        ax.spines[["top", "right"]].set_visible(False)
        ax.grid(axis="y", alpha=0.6)
        ax.legend(
            frameon=False, ncol=3, loc="upper center", bbox_to_anchor=(0.5, -0.16)
        )
        ax.set_title(
            f"On-sky time by visit category, week by week, {weeks.min():%-d %b %Y} – {(weeks.max() + pd.Timedelta(days=6)):%-d %b %Y}",
            loc="left",
        )
        fig.text(
            0.01,
            0.01,
            "ConsDB visit1 on-sky visits; hours = first-to-last visit of consecutive same-category visits "
            f"(gaps under {BLOCK_GAP_S / 60:.0f} min bridged). Dashed grey: the 8 h line before LSST is a reference, "
            'not a rule. Policy: Confluence 1802141753 v6 (2026-07-28), still titled "Proposed".',
            ha="left",
            va="bottom",
            color=C["ink2"],
            fontsize=12,
            wrap=True,
        )
        fig.subplots_adjust(left=0.07, right=0.80, bottom=0.25, top=0.9)
        stem = FIG / f"engineering_hours_weekly_policy_{TAG}"
        fig.savefig(f"{stem}.png", dpi=200, transparent=True)
        fig.savefig(f"{stem}_white.png", dpi=200, facecolor="white")
        print("wrote", stem, "[_white].png")
        print(
            "labelled engineering hours:",
            {
                str(i.date()): round(eng[i], 1)
                for i in w.index[w.index >= xl - pd.Timedelta(days=6)]
            },
            "peak",
            str(i.date()),
            round(eng.max(), 1),
        )


def main():
    v = categorize(pd.read_parquet(DATA))
    w = weekly_hours(v)
    w.round(2).to_csv(ROOT / "data" / f"weekly_hours_by_category_{TAG}.csv")
    make_figure(w)
    make_policy_figure(w)
    tot = w[[f"on_sky_h_{c}" for c in CATS]].sum().round(1)
    print("on-sky hours by category:", tot.to_dict())
    print(
        "shutter-open hours by category:",
        w[[f"shutter_h_{c}" for c in CATS]].sum().round(1).to_dict(),
    )
    lsst = w[w.index >= pd.Timestamp(str(LSST_START)) - pd.Timedelta(days=6)]
    print(
        "weeks from LSST start:\n",
        lsst[[f"on_sky_h_{c}" for c in CATS] + ["nights_with_engineering"]].round(1),
    )
    early = w[w.index < "2026-06-29"]
    e = early["on_sky_h_Engineering"]
    print(
        "Early ops: engineering h/week median %.1f, max %.1f (week of %s); weeks over 8 h: %d of %d"
        % (e.median(), e.max(), e.idxmax().date(), (e > POLICY_WEEKLY_H).sum(), len(e))
    )
    lsst_eng = w[w.index >= "2026-06-29"]["on_sky_h_Engineering"]
    print("LSST weeks engineering h:", lsst_eng.round(1).tolist())


if __name__ == "__main__":
    main()
