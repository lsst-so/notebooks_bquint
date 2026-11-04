"""Visit-gap distribution and weekly trend for the LSST@LATAM 2026 talk (slide 7).

Data: ConsDB ``cdb_lsstcam.visit1`` rows cached in ``../data/visit1_<min>_<max>.parquet``
(``airmass > 0``, ``img_type`` in acq/science/cwfs/focus; same query as the on-sky
utilization timeline). The gap is ``obs_start`` of a visit minus ``obs_end`` of the
previous visit of the same ``day_obs`` (rubin_nights ``augment_visits`` definition;
``obs_end - obs_start = exp_time + 0.93 s``, the readout), **reset at the start of each
night**. Only pairs where both visits belong to a survey program (Feature Based
Scheduler blocks, list copied from ``nightly_survey_speed/utils.py``) are kept.

The histogram shows the requirement line and the median only. Earlier versions shaded
14-20 s as a "second settle" population; that band was set by hand (typical gap + the
~8 s between the two slew-flag pairs reported by Tiago Ribeiro, #survey-performance
10 Sep 2026) and is not supported by the data, so it was removed on 2026-11-04. The
weekly panel annotates the May-Jul 2026 rise instead, which is what the data shows.
See ``check_late_correction.py`` and the README.

Layouts, from the same panel code:

* combined (default) — ``../figures/visit_gap_talk_<tag>.png`` and ``_white``, 16:9,
  both panels side by side with the title and the data footnote on the figure.
* ``--split`` — ``../figures/visit_gap_hist_talk_<tag>_white.png`` and
  ``../figures/visit_gap_weekly_talk_<tag>_white.png``, one panel each at 6 x 4.84 in
  for a quarter of a 16:9 slide. No title and no footnote: the slide carries the
  title and the README carries the data caption.
* ``--excess`` — diagnostic only, **not for the talk**: the excess-gap histogram
  (``gap - slew_model``) as ``../figures/visit_gap_excess_<tag>_white.png``. Needs the
  ``night_budget`` slew cache, which covers May-Oct 2026 only.

Run: ``python visit_gap_anatomy/python/make_visit_gap_figure.py [--split|--combined]
[--excess]``.
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
HIST_MAX_S = 40.0
#: 1 s bins, not the original 0.5 s: at quarter-slide size the half-second bars were
#: too thin to read and their bin-to-bin noise looked like structure (Bruno, 2026-11-04).
HIST_BIN_S = 1.0
#: Opacity of the two-tone median rule (Bruno, 2026-11-04): visible, but clearly an
#: annotation over the data rather than another series.
MEDIAN_ALPHA = 0.5
#: Opacity of the 25-75 % band, drawn in the series teal (Bruno, 2026-11-04).
BAND_ALPHA = 0.5

#: The weekly rise is annotated by a span, not by a hand-set gap-value band: its edges
#: are the first and last week whose median exceeds this, so the annotation follows the
#: data. Searched inside ``EPISODE`` only - the week of 24 Nov 2025 also clears 12 s
#: (12.86 s) and without that scoping the span would stretch across the whole panel and
#: contradict its own label. That outlier is printed separately.
SPAN_MEDIAN_S = 12.0
#: Search window for the span, half-open. Wider than the episode itself (3-30 Jun 2026,
#: ts_observatory_control v0.50.0 to the 1 Jul summit rebuild) because the weekly median
#: is elevated either side of it too: the same pre-slew wait ran at a ~30 % rate from
#: mid-May. The span edges come from the data via ``SPAN_MEDIAN_S``.
EPISODE = ("2026-05-01", "2026-08-01")
#: Excess-gap diagnostic (``--excess``): kinematic model cache from ``night_budget``.
#: Outside this folder and read-only, so ``--excess`` is skipped once extracted.
SLEW_CACHE = sorted(
    (ROOT.parent / "night_budget" / "data").glob("visits_slew_*.parquet")
)
EXCESS_MAX_S = 20.0

DATA = ROOT / "data" / f"visit1_{DAY_OBS_MIN}_{DAY_OBS_MAX}.parquet"
FIG = ROOT / "figures"
FIG.mkdir(exist_ok=True)
TAG = f"{DAY_OBS_MIN}-{DAY_OBS_MAX}"

# Mostly LSST@LATAM deck colours (``rubin_palette.DECK``, read off slide 2 / slide 5)
# for the neutrals, but the series colour is back to the **Rubin brand teal** #058B8C
# (``rp.TEAL``, == ``CATEGORICAL[0]``; Bruno asked for 058b8cff on 2026-11-04, i.e. the
# brand teal at full opacity) rather than the deck's darker Science #024243.
C = {
    "gap": rp.TEAL,  # survey visits: bars and the weekly median
    # The 25-75 % band is now the series teal at ``BAND_ALPHA``, not this flat pale
    # teal; kept so reverting to the deck's fill is one edit in ``panel_weekly``.
    "band": rp.DECK["band"],
    "late": rp.DECK["accent"],  # episode highlight on the excess diagnostic
    "req": rp.CATEGORICAL[3],  # requirement line, see note below
    "median": rp.DECK["median"],  # median label text, and other annotation text
    # The median rule is drawn twice with complementary dash phase (see
    # ``contrast_vline``): #595959 alone had too little contrast against the teal
    # bars it crosses. Near-black over white ground, near-white over the bars.
    "median_dark": "#2B2B2B",
    "median_light": "#F2F2F2",
    "ref": rp.DECK["reference"],  # LSST-start marker, grid
    "ink": rp.DECK["ink"],  # axis labels and ticks
}
# The handoff asked for the deck accent on the requirement line "if in-palette, else
# keep current red". It is in-palette now (``DECK["accent"]``) but it is also the
# late-correction shading, and one hue for two meanings on one panel is ambiguous -
# so the requirement keeps the palette red. One line to switch: C["req"] = C["late"].

_INK_RC = {
    "text.color": C["ink"],
    "axes.labelcolor": C["ink"],
    "axes.edgecolor": C["ink"],
    "xtick.color": C["ink"],
    "ytick.color": C["ink"],
    "grid.color": C["ref"],
    "grid.linewidth": 0.5,
}
#: Combined 16:9 figure.
TALK_RC = {
    "figure.figsize": (13.33, 7.5),
    "font.size": 18,
    "axes.labelsize": 20,
    "axes.titlesize": 22,
    "xtick.labelsize": 16,
    "ytick.labelsize": 16,
    "legend.fontsize": 16,
    "axes.linewidth": 1.2,
    **_INK_RC,
}
#: One panel on a quarter of a slide. Resized on 2026-11-04 (Bruno): 75 % of the
#: previous 8.0 in width and 10 % more height, so 6.0 x 4.84 in - squarer (1.24:1,
#: was 1.82:1). Text is NOT rescaled: the panel still renders ~1.4x its on-slide
#: width, so these point sizes stay above the 11 pt floor when it is placed.
SPLIT_RC = {
    "figure.figsize": (6.0, 4.84),
    "font.size": 15,
    "axes.labelsize": 17,
    "xtick.labelsize": 14,
    "ytick.labelsize": 14,
    "legend.fontsize": 14,
    "axes.linewidth": 1.0,
    **_INK_RC,
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


def episode_span(w: pd.DataFrame) -> tuple[pd.Timestamp, pd.Timestamp] | None:
    """First and last week inside ``EPISODE`` whose median exceeds ``SPAN_MEDIAN_S``."""
    inside = w[(w.index >= EPISODE[0]) & (w.index < EPISODE[1])]
    hot = inside[inside["median"] > SPAN_MEDIAN_S]
    if not len(hot):
        return None
    return hot.index.min(), hot.index.max()


def gap_stats(g: pd.DataFrame) -> dict:
    """The numbers quoted on the panels and in the README table."""
    return dict(
        n=len(g),
        median_s=g.gap_s.median(),
        frac_below_req=(g.gap_s < REQ_GAP_S).mean(),
        p10=g.gap_s.quantile(0.10),
        p25=g.gap_s.quantile(0.25),
        p75=g.gap_s.quantile(0.75),
        p90=g.gap_s.quantile(0.90),
        frac_over_hist=(g.gap_s > HIST_MAX_S).mean(),
    )


# --------------------------------------------------------------------------- #
# Panels - one function each, shared by the combined and the split layouts     #
# --------------------------------------------------------------------------- #
#: Tick labels with a decimal only where one is needed: "0", "5", "20" but "2.5"
#: (Bruno, 2026-11-04 - a column of ".0" is ink that carries nothing). ``%g`` drops
#: trailing zeros, so it does exactly this without a per-axis format string.
TRIM_ZEROS = mpl.ticker.FuncFormatter(lambda v, _pos: f"{v:g}")


def contrast_vline(
    ax, x: float, lw: float = 2.0, dash: float = 4.0, alpha: float = MEDIAN_ALPHA
) -> None:
    """A vertical rule that reads against both the teal bars and the white ground.

    The median rule crosses the tallest bars, where a single mid-grey dash had poor
    contrast (Bruno, 2026-11-04). Two dashed lines are drawn with complementary phase,
    so the dark segments tile the gaps in the light ones: the light dashes carry the
    line over the dark bars and the dark dashes carry it over the white background.
    ``alpha`` softens both so the rule annotates without competing with the data.
    """
    for color, offset in ((C["median_light"], 0.0), (C["median_dark"], dash)):
        ax.axvline(
            x, color=color, lw=lw, ls=(offset, (dash, dash)), alpha=alpha, zorder=4
        )


def panel_hist(ax, g: pd.DataFrame, st: dict, anno: int) -> None:
    """Gap histogram with the requirement line and the median.

    The 14-20 s band is deliberately **not** shaded - see the module docstring.
    """
    med, n_all = st["median_s"], st["n"]
    bins = np.arange(0, HIST_MAX_S + HIST_BIN_S, HIST_BIN_S)
    counts, edges = np.histogram(g.gap_s[g.gap_s < HIST_MAX_S], bins=bins)
    frac = counts / n_all
    centers = 0.5 * (edges[:-1] + edges[1:])
    ax.bar(centers, frac, width=HIST_BIN_S, color=C["gap"], linewidth=0)

    ymax = frac.max() * 1.3
    ax.set_ylim(0, ymax)
    ax.set_xlim(0, HIST_MAX_S)
    ax.axvline(REQ_GAP_S, color=C["req"], lw=2.0)
    # Rotated and to the left of the line (Bruno, 2026-11-04): it now sits in the empty
    # 0-5 s margin instead of over the rising edge of the distribution. Default
    # rotation_mode, so ha/va place the *rotated* box - "center" keeps the glyph column
    # clear of the rule, "top" hangs it from the top of the panel.
    ax.text(
        REQ_GAP_S - 0.9,
        ymax * 0.98,
        f"requirement < {REQ_GAP_S:.0f} s",
        ha="center",
        va="top",
        rotation=90,
        color=C["req"],
        fontsize=anno,
    )
    contrast_vline(ax, med)
    ax.text(
        med + 0.6,
        ymax * 0.82,
        f"median {med:.1f} s",
        ha="left",
        va="top",
        color=C["median_dark"],  # matches the rule's dark dashes, not the #595959 grey
        fontsize=anno,
    )
    ax.set_xlabel("gap between visits (s)")
    ax.set_ylabel("fraction of visits")
    ax.xaxis.set_major_formatter(TRIM_ZEROS)
    ax.yaxis.set_major_formatter(mpl.ticker.PercentFormatter(1.0, decimals=0))
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y")
    ax.set_axisbelow(True)


def panel_weekly(ax, w: pd.DataFrame, anno: int) -> None:
    """Weekly median with the 25-75 % band, the requirement and the LSST start."""
    x = w.index + pd.Timedelta(days=3.5)
    # Teal at 0.5 alpha, not the deck's flat pale teal #D9F7F7 (Bruno, 2026-11-04):
    # that had too little contrast against the grey episode span, and a tint of the
    # line's own colour reads as "the spread of this series". Over the span the two
    # translucent fills composite, which darkens the overlap instead of hiding it.
    ax.fill_between(
        x,
        w.p25,
        w.p75,
        color=C["gap"],
        alpha=BAND_ALPHA,
        lw=0,
        label="25–75 % of visits",
        zorder=1.5,
    )
    ax.plot(
        x,
        w["median"],
        color=C["gap"],
        lw=2.4,
        marker="o",
        ms=5,
        label="weekly median",
        zorder=3,
    )
    ax.axhline(
        REQ_GAP_S,
        color=C["req"],
        lw=2.0,
        label=f"requirement < {REQ_GAP_S:.0f} s",
        zorder=2,
    )
    ax.set_ylim(0, 25)
    ax.set_xlim(x.min() - pd.Timedelta(days=7), x.max() + pd.Timedelta(days=7))

    xl = pd.Timestamp(str(LSST_START))
    ax.axvline(xl, color=C["ref"], lw=0.5, ls="--", zorder=1)
    ax.text(
        xl - pd.Timedelta(days=4),
        24.3,
        "LSST start\n29 Jun",
        ha="right",
        va="top",
        color=C["median"],
        fontsize=anno,
        linespacing=1.15,
    )
    ax.set_ylabel("gap (s)")
    ax.xaxis.set_major_locator(mpl.dates.MonthLocator(interval=2))
    ax.xaxis.set_major_formatter(mpl.dates.DateFormatter("%b\n%Y"))
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y")
    ax.set_axisbelow(True)
    ax.legend(frameon=False, loc="upper left", ncol=1, handlelength=1.6)

    # Span over the episode. Describes *when* the gap grew, which is what the weekly
    # median measures, and not *why*: the cause cannot be pinned down from ConsDB
    # (see ``check_late_correction.py``).
    span = episode_span(w)
    if span is not None:
        lo, hi = span
        ax.axvspan(
            lo,
            hi + pd.Timedelta(days=7),
            color=C["ref"],
            alpha=0.3,
            lw=0,
            zorder=0.5,
        )
        # Low in the panel, clear of the "LSST start" label at the top, and right-
        # aligned just inside the span's left edge so it cannot run off the axes.
        # The label states the measured effect and its cause, not the period: the rise is
        # a fixed ~6 s added before every slew by ts_observatory_control v0.50.0
        # (OSW-2269, 2026-06-03; ticket RSO-785), not "AOS stability work", which was the
        # earlier label and is a wrong attribution. See the README.
        ax.text(
            lo - pd.Timedelta(days=3),
            2.4,
            "+6 s per visit, Jun 2026:\nAOS correction before each slew",
            ha="right",
            va="bottom",
            color=C["median"],
            fontsize=anno,
            linespacing=1.15,
        )


# --------------------------------------------------------------------------- #
# Layouts                                                                      #
# --------------------------------------------------------------------------- #
def make_combined(g: pd.DataFrame, w: pd.DataFrame, st: dict) -> None:
    """The original 16:9 two-panel figure, title and data footnote included."""
    with mpl.rc_context(TALK_RC):
        fig, (ax, ax2) = plt.subplots(
            1, 2, gridspec_kw={"width_ratios": [1, 1.25], "wspace": 0.22}
        )
        panel_hist(ax, g, st, anno=16)
        panel_weekly(ax2, w, anno=14)
        fig.text(
            0.02,
            0.01,
            f"{st['n']:,} visit pairs; {st['frac_over_hist']:.1%} of gaps are longer "
            f"than {HIST_MAX_S:.0f} s and off the histogram scale; weeks with fewer "
            "than 100 survey visits are not plotted",
            ha="left",
            va="bottom",
            color=C["median"],
            fontsize=13,
        )
        fig.suptitle(
            f"Time between consecutive survey visits, "
            f"{g.date.min():%-d %b %Y} – {g.date.max():%-d %b %Y}",
            x=0.02,
            y=0.985,
            ha="left",
            fontsize=22,
            color=C["ink"],
        )
        fig.text(
            0.02,
            0.925,
            "ConsDB visit1, scheduler-driven survey blocks only; gap = start of a "
            "visit − end of the previous one, reset each night",
            ha="left",
            va="top",
            fontsize=15,
            color=C["median"],
        )
        fig.subplots_adjust(left=0.08, right=0.98, bottom=0.2, top=0.86, wspace=0.22)
        stem = FIG / f"visit_gap_talk_{TAG}"
        fig.savefig(f"{stem}.png", dpi=200, transparent=True)
        fig.savefig(f"{stem}_white.png", dpi=200, facecolor="white")
        plt.close(fig)
        print(f"wrote {stem}[_white].png")


def make_split(g: pd.DataFrame, w: pd.DataFrame, st: dict) -> None:
    """The same two panels as standalone quarter-slide PNGs, no title, no footnote.

    Each is written twice, matching the combined figure's convention: ``_white`` on a
    white background, and a transparent one (no ``_white`` suffix) to drop onto a slide
    of any colour. The transparent pair keeps the same dark ink, so it is for light
    slides - on a dark slide the axis labels would need ``rp.use(mode="dark")``.
    """
    # Margins are fractions of the figure, so they had to grow when the panel narrowed
    # to 6 in (2026-11-04): the old left=0.13 clipped the y-axis label.
    panels = (
        (
            "hist",
            lambda ax: panel_hist(ax, g, st, anno=14),
            dict(left=0.17, right=0.97, bottom=0.15, top=0.97),
        ),
        (
            "weekly",
            lambda ax: panel_weekly(ax, w, anno=13),
            dict(left=0.14, right=0.97, bottom=0.17, top=0.97),
        ),
    )
    with mpl.rc_context(SPLIT_RC):
        for name, draw, margins in panels:
            fig, ax = plt.subplots()
            draw(ax)
            fig.subplots_adjust(**margins)
            stem = FIG / f"visit_gap_{name}_talk_{TAG}"
            fig.savefig(f"{stem}_white.png", dpi=200, facecolor="white")
            fig.savefig(f"{stem}.png", dpi=200, transparent=True)
            plt.close(fig)
            print(f"wrote {stem}[_white].png")


def make_excess(g_hist_max: float = EXCESS_MAX_S) -> None:
    """Diagnostic: histogram of ``gap - slew_model``, the dead time the kinematic model
    cannot account for. Not a talk figure - the slew cache covers May-Oct 2026 only, so
    this is a different (shorter) window than the gap histogram.
    """
    if not SLEW_CACHE:
        print("--excess skipped: night_budget/data/visits_slew_*.parquet not found")
        return
    d = pd.concat([pd.read_parquet(f) for f in SLEW_CACHE], ignore_index=True)
    e = d[d.is_survey_gap & d.visit_gap.notna()].copy()
    e["excess"] = e.visit_gap - e.slew_model
    months = pd.to_datetime(e.day_obs.astype(str)).dt.to_period("M")

    # Split by epoch, not pooled. Pooled, this histogram looks bimodal (peaks at ~0.8
    # and ~6.2 s) and would be read as exactly the two-population structure the band
    # was supposed to show - but that is an artefact of June being 51 % of this cache.
    # Each epoch on its own is unimodal; the "two modes" are the two epochs superposed.
    in_episode = months == pd.Period("2026-06")
    series = [
        ("outside the episode", e[~in_episode], C["gap"]),
        ("Jun 2026 episode", e[in_episode], C["late"]),
    ]
    bins = np.arange(0, g_hist_max + 0.5, 0.5)
    centers = 0.5 * (bins[:-1] + bins[1:])

    with mpl.rc_context(SPLIT_RC):
        fig, ax = plt.subplots()
        top = 0.0
        for label, sub, color in series:
            counts, _ = np.histogram(sub.excess[sub.excess < g_hist_max], bins=bins)
            frac = counts / len(sub)
            top = max(top, frac.max())
            ax.step(
                centers,
                frac,
                where="mid",
                color=color,
                lw=2.0,
                label=f"{label} (n={len(sub):,}, median {sub.excess.median():.1f} s)",
            )
        # Headroom for the two-line legend, which is long (it carries n and the median)
        # and does not fit beside the curves at 6 in.
        ax.set_ylim(0, top * 1.55)
        ax.set_xlim(0, g_hist_max)
        ax.set_xlabel("gap − kinematic slew model (s)")
        ax.set_ylabel("fraction of visits")
        ax.xaxis.set_major_formatter(TRIM_ZEROS)
        ax.yaxis.set_major_formatter(mpl.ticker.PercentFormatter(1.0, decimals=0))
        ax.spines[["top", "right"]].set_visible(False)
        ax.grid(axis="y")
        ax.set_axisbelow(True)
        ax.legend(frameon=False, loc="upper left", fontsize=11, handlelength=1.4)
        # Same margins as the histogram panel, which shares this figure size.
        fig.subplots_adjust(left=0.17, right=0.97, bottom=0.15, top=0.97)
        stem = FIG / f"visit_gap_excess_{TAG}"
        fig.savefig(f"{stem}_white.png", dpi=200, facecolor="white")
        fig.savefig(f"{stem}.png", dpi=200, transparent=True)
        plt.close(fig)
        print(f"wrote {stem}[_white].png")
    print(
        f"  excess: n={len(e):,} survey gaps, {months.min()}-{months.max()} "
        f"(slew cache window, not the gap-histogram window); "
        f"median {e.excess.median():.2f} s overall, "
        f"{(e.excess > g_hist_max).mean():.1%} above {g_hist_max:.0f} s"
    )
    for label, sub, _ in series:
        counts, _ = np.histogram(sub.excess[sub.excess < g_hist_max], bins=bins)
        print(
            f"    {label:20s} n={len(sub):6d}  median={sub.excess.median():5.2f} s  "
            f"single peak at {centers[(counts / len(sub)).argmax()]:4.1f} s"
        )


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    mode = ap.add_mutually_exclusive_group()
    mode.add_argument(
        "--split",
        action="store_true",
        help="write only the two standalone quarter-slide panels",
    )
    mode.add_argument(
        "--combined",
        action="store_true",
        help="write only the 16:9 two-panel figure",
    )
    ap.add_argument(
        "--excess",
        action="store_true",
        help="also write the excess-gap diagnostic (not a talk figure)",
    )
    args = ap.parse_args()
    do_combined = not args.split
    do_split = not args.combined

    g = survey_gaps()
    w = weekly(g)
    st = gap_stats(g)
    if do_combined:
        make_combined(g, w, st)
    if do_split:
        make_split(g, w, st)
    if args.excess:
        make_excess()

    print({k: (round(v, 3) if isinstance(v, float) else v) for k, v in st.items()})
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
    span = episode_span(w)
    if span is not None:
        lo, hi = span
        print(
            f"episode span (weeks with median > {SPAN_MEDIAN_S:.0f} s inside "
            f"{EPISODE[0]}..{EPISODE[1]}): {lo:%Y-%m-%d} .. {hi:%Y-%m-%d} "
            f"(ISO {lo.isocalendar().year}-W{lo.isocalendar().week:02d} .. "
            f"{hi.isocalendar().year}-W{hi.isocalendar().week:02d})"
        )
    # Weeks over the threshold outside the episode: the span deliberately excludes
    # these, so say so rather than letting the annotation imply they do not exist.
    outside = w[
        ((w.index < EPISODE[0]) | (w.index >= EPISODE[1]))
        & (w["median"] > SPAN_MEDIAN_S)
    ]
    if len(outside):
        print(
            f"  note: {len(outside)} week(s) outside the episode also exceed "
            f"{SPAN_MEDIAN_S:.0f} s and are NOT in the span: "
            + ", ".join(
                f"{i:%Y-%m-%d} ({m:.2f} s)" for i, m in outside["median"].items()
            )
        )
    w.round(2).to_csv(ROOT / "data" / f"visit_gap_weekly_{TAG}.csv")
    g.gap_s.describe(percentiles=[0.1, 0.25, 0.5, 0.75, 0.9]).round(2).to_csv(
        ROOT / "data" / f"visit_gap_summary_{TAG}.csv"
    )


if __name__ == "__main__":
    main()
