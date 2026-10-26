"""One Simonyi night laid on its side, with the efficiency denominators drawn as brackets
(LSST@LATAM 2026 talk, figure B11; replaces the schematic efficiency waterfall).

Night: ``DAY_OBS`` (8 Jul 2026). Inputs are copies of the B1/B3/B10 pipeline outputs in
``../data/`` (no imports across investigation folders):

* ``visits_<day_obs>.csv`` — ConsDB ``cdb_lsstcam.visit1`` rows of the night (airmass > 0,
  img_type in acq/science/cwfs/focus), from ``engineering_time_budget/data/visit1_*.parquet``.
* ``night_limits_<day_obs>.csv`` — −18° and −12° twilights from
  ``simonyi_time_loss/data/step0/night_limits.csv`` (rubin_nights ephemeris).
* ``observatory_state_<day_obs>.csv`` — Scheduler observatoryStatus periods (WEATHER bit etc.)
  from ``simonyi_time_loss/data/step0/obs_state_periods.parquet``.

Definitions (same as simonyi_time_loss, gap_min = 10 min, −18° night):

* visit categories as in B10: Survey Programs (BLOCK-407/408/416/417/419/421), Focus and
  Alignment (BLOCK-T539), Engineering (everything else on sky);
* gaps between consecutive visits (and the two night edges) longer than 10 min are loss;
  the part inside a WEATHER-bit window is weather, the rest is fault + idle;
* brackets: whole night (−18° → −18°); minus weather; minus weather and fault/idle;
  on sky = sum of the visit intervals (obs_start → obs_end, shutter + readout) inside the night.
  NB: "minus weather and fault/idle" equals B3's bridged ``on_sky_hours`` by construction, so
  the fourth bracket is the un-bridged visit coverage (see README).

Outputs ``../figures/night_brackets_<day_obs>.png`` and ``_white.png`` (16:5).
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

DAY_OBS = 20260708
GAP_MIN_S = 600.0
TAI_MINUS_UTC_S = 37.0
SURVEY_PROGRAMS = (
    "BLOCK-407",
    "BLOCK-408",
    "BLOCK-416",
    "BLOCK-417",
    "BLOCK-419",
    "BLOCK-421",
)
FOCUS_PROGRAMS = ("BLOCK-T539",)
#: Night-report / FRACAS attribution of the fault + idle gaps, keyed by gap start (UTC, HH:MM).
GAP_LABELS = {
    "00:20": "camera recovery\nafter REB trip (FRACAS-404)",
    "03:36": "HV bias trip\n(OBS-2010)",
}

DATA = ROOT / "data"
FIG = ROOT / "figures"
FIG.mkdir(exist_ok=True)

C = {
    "Survey Programs": rp.CATEGORICAL[0],
    "Focus and Alignment": rp.CATEGORICAL[2],
    "Engineering": rp.CATEGORICAL[1],
    "weather": rp.CATEGORICAL[0],
    "fault": rp.CATEGORICAL[1],
    "ink": rp.NEUTRALS["ink"],
    "ink2": rp.NEUTRALS["ink_secondary"],
    "muted": rp.NEUTRALS["muted"],
    "grid": rp.NEUTRALS["grid"],
}
RC = {
    "figure.figsize": (16, 5),
    "font.size": 15,
    "axes.titlesize": 20,
    "xtick.labelsize": 14,
    "axes.linewidth": 1.0,
    "text.color": C["ink"],
    "axes.labelcolor": C["ink"],
    "axes.edgecolor": C["ink2"],
    "xtick.color": C["ink2"],
    "ytick.color": C["ink2"],
}


def mjd_to_ts(mjd: float) -> pd.Timestamp:
    return pd.Timestamp("1858-11-17") + pd.to_timedelta(mjd, unit="D")


def load():
    v = pd.read_csv(DATA / f"visits_{DAY_OBS}.csv").sort_values("obs_start_mjd")
    start = v.obs_start_mjd.to_numpy() - TAI_MINUS_UTC_S / 86400.0
    end = v.obs_end_mjd.to_numpy() - TAI_MINUS_UTC_S / 86400.0
    bad = ~(end > start)
    end[bad] = start[bad] + v.exp_time.to_numpy()[bad] / 86400.0
    prog = v.science_program.astype("string")
    cat = np.where(
        prog.isin(FOCUS_PROGRAMS),
        "Focus and Alignment",
        np.where(prog.isin(SURVEY_PROGRAMS), "Survey Programs", "Engineering"),
    )
    visits = pd.DataFrame(
        {"start": start, "end": end, "category": cat, "program": prog}
    )
    nl = pd.read_csv(DATA / f"night_limits_{DAY_OBS}.csv").iloc[0]
    night = {
        "set18": nl.sunset18_mjd,
        "rise18": nl.sunrise18_mjd,
        "set12": nl.sunset12_mjd,
        "rise12": nl.sunrise12_mjd,
    }
    st = pd.read_csv(
        DATA / f"observatory_state_{DAY_OBS}.csv", parse_dates=["start", "end"]
    )
    wx = st[st.type == "WEATHER"]
    weather = [
        (
            (a - pd.Timestamp("1858-11-17")) / pd.Timedelta(days=1),
            (b - pd.Timestamp("1858-11-17")) / pd.Timedelta(days=1),
        )
        for a, b in zip(wx.start, wx.end)
    ]
    return visits, night, weather


def clip(a, b, lo, hi):
    return max(a, lo), min(b, hi)


def subtract(segments, cuts):
    """Remove the intervals ``cuts`` from the list of ``segments`` (all in MJD)."""
    out = list(segments)
    for ca, cb in cuts:
        new = []
        for sa, sb in out:
            if cb <= sa or ca >= sb:
                new.append((sa, sb))
                continue
            if ca > sa:
                new.append((sa, ca))
            if cb < sb:
                new.append((cb, sb))
        out = new
    return [(a, b) for a, b in out if b > a]


def hours(segments):
    return sum(b - a for a, b in segments) * 24.0


def gaps_and_brackets(visits, night, weather):
    n0, n1 = night["set18"], night["rise18"]
    s, e = visits.start.to_numpy(), visits.end.to_numpy()
    edges = [(n0, s[0])] + [(e[i], s[i + 1]) for i in range(len(s) - 1)] + [(e[-1], n1)]
    long_gaps = [clip(a, b, n0, n1) for a, b in edges if (b - a) * 86400.0 > GAP_MIN_S]
    long_gaps = [(a, b) for a, b in long_gaps if b > a]
    wx = [clip(a, b, n0, n1) for a, b in weather]
    wx = [(a, b) for a, b in wx if b > a]
    # weather gets precedence inside a long gap; the rest of the gap is fault + idle
    weather_blocks = []
    for ga, gb in long_gaps:
        for wa, wb in wx:
            a, b = clip(ga, gb, wa, wb)
            if b > a:
                weather_blocks.append((a, b))
    fault_blocks = subtract(long_gaps, weather_blocks)
    whole = [(n0, n1)]
    minus_weather = subtract(whole, weather_blocks)
    minus_faults = subtract(minus_weather, fault_blocks)
    on_sky = [clip(a, b, n0, n1) for a, b in zip(s, e)]
    on_sky = [(a, b) for a, b in on_sky if b > a]
    brackets = [
        ("Whole night (OSF)", whole),
        ("Survey time only", minus_weather),
        ("Excluding faults", minus_faults),
        ("On sky (exposing + readout)", on_sky),
    ]
    return long_gaps, weather_blocks, fault_blocks, brackets


def make_figure(visits, night, weather):
    long_gaps, weather_blocks, fault_blocks, brackets = gaps_and_brackets(
        visits, night, weather
    )
    n0, n1 = night["set18"], night["rise18"]
    t0 = night["set12"]  # axis origin: evening −12° twilight

    def h(mjd):
        return (np.asarray(mjd) - t0) * 24.0

    with mpl.rc_context(RC):
        fig, ax = plt.subplots()
        y0, y1 = 0.0, 1.0  # strip
        # strip background (the −18° night)
        ax.add_patch(
            mpl.patches.Rectangle(
                (h(n0), y0),
                h(n1) - h(n0),
                y1 - y0,
                facecolor="white",
                edgecolor=C["grid"],
                linewidth=0.8,
                zorder=0,
            )
        )
        # loss blocks: light tint + hatch + direct label
        for blocks, key, name in (
            (weather_blocks, "weather", "weather"),
            (fault_blocks, "fault", "fault + idle"),
        ):
            for a, b in blocks:
                ax.add_patch(
                    mpl.patches.Rectangle(
                        (h(a), y0),
                        h(b) - h(a),
                        y1 - y0,
                        facecolor=C[key],
                        alpha=0.18,
                        edgecolor="none",
                        zorder=1,
                    )
                )
                ax.add_patch(
                    mpl.patches.Rectangle(
                        (h(a), y0),
                        h(b) - h(a),
                        y1 - y0,
                        facecolor="none",
                        edgecolor=C[key],
                        hatch="///",
                        linewidth=0,
                        alpha=0.45,
                        zorder=1.1,
                    )
                )
                hrs = (b - a) * 24.0
                key_hm = mjd_to_ts(a).strftime("%H:%M")
                why = GAP_LABELS.get(key_hm, "")
                label = f"{name}\n{hrs:.1f} h"
                if (b - a) * 24.0 > 0.7:
                    ax.text(
                        h((a + b) / 2),
                        (y0 + y1) / 2,
                        label + (f"\n{why}" if why else ""),
                        ha="center",
                        va="center",
                        fontsize=14,
                        color=C[key],
                        linespacing=1.15,
                        zorder=3,
                    )
                else:  # too narrow: label below the strip with a leader
                    ax.annotate(
                        f"{name} {hrs:.1f} h"
                        + (f", {why.replace(chr(10), ' ')}" if why else ""),
                        xy=(h((a + b) / 2), y1),
                        xytext=(h((a + b) / 2) + 0.25, y1 + 0.17),
                        ha="left",
                        va="center",
                        fontsize=12,
                        color=C[key],
                        arrowprops=dict(
                            arrowstyle="-", color=C[key], lw=0.8, shrinkA=0, shrinkB=0
                        ),
                        zorder=3,
                    )
        # visits (inside the −18° night solid; in twilight lighter)
        for a, b, cat in zip(visits.start, visits.end, visits.category):
            inside = a < n1 and b > n0
            ax.add_patch(
                mpl.patches.Rectangle(
                    (h(a), y0),
                    h(b) - h(a),
                    y1 - y0,
                    facecolor=C[cat],
                    edgecolor="none",
                    alpha=1.0 if inside else 0.4,
                    zorder=2,
                )
            )
        # twilight marks
        for mjd, lab, lw in (
            (n0, "−18°", 1.4),
            (n1, "−18°", 1.4),
            (night["set12"], "−12°", 0.9),
            (night["rise12"], "−12°", 0.9),
        ):
            ax.plot(
                [h(mjd), h(mjd)],
                [y0 - 0.08, y1 + 0.08],
                color=C["ink2"],
                lw=lw,
                zorder=4,
            )
            ax.text(
                h(mjd),
                y0 - 0.10,
                lab,
                ha="center",
                va="top",
                fontsize=12,
                color=C["ink2"],
            )
        # brackets above the strip
        base, step = 1.45, 0.34
        ink = C["ink"]
        for i, (name, segs) in enumerate(brackets):
            y = base + (len(brackets) - 1 - i) * step
            if i == len(brackets) - 1:
                # hundreds of 31 s visits: draw their summed length packed from the first visit
                # (dotted, to say "packed"), not 500 tiny brackets
                b1 = segs[-1][1]  # packed against the morning −18° limit
                segs_draw = [(b1 - hours(segs) / 24.0, b1)]
                ls = (0, (1.5, 1.5))
            else:
                segs_draw, ls = segs, "-"
            for a, b in segs_draw:
                xa, xb = h(a), h(b)
                ax.plot(
                    [xa, xa, xb, xb],
                    [y - 0.07, y, y, y - 0.07],
                    color=ink,
                    lw=1.4,
                    ls=ls,
                    solid_capstyle="butt",
                    zorder=5,
                )
            left = h(segs_draw[0][0])
            ax.text(
                left - 0.08,
                y + 0.02,
                name,
                ha="right",
                va="center",
                fontsize=15,
                color=ink,
            )
            right = h(segs_draw[-1][1])
            ax.text(
                right + 0.08,
                y + 0.02,
                f"{hours(segs):.1f} h",
                ha="left",
                va="center",
                fontsize=15,
                color=ink,
                fontweight="bold",
            )
        ax.text(
            h(n0) + 0.05,
            y0 - 0.66,
            "Each efficiency number divides by a different bracket.",
            ha="left",
            va="top",
            fontsize=14,
            color=C["ink2"],
            style="italic",
        )
        # axes
        ax.set_xlim(h(night["set12"]) - 2.3, h(night["rise12"]) + 1.2)
        ax.set_ylim(y0 - 0.95, base + (len(brackets) - 1) * step + 0.25)
        ax.set_yticks([])
        for sp in ("left", "right", "top"):
            ax.spines[sp].set_visible(False)
        ax.spines["bottom"].set_position(("data", y0 - 0.32))
        ax.spines["bottom"].set_visible(False)
        # ticks at whole UTC hours
        first_hour = np.ceil(night["set12"] * 24.0) / 24.0
        last_hour = np.floor(night["rise12"] * 24.0) / 24.0
        hour_mjd = np.arange(first_hour, last_hour + 1e-9, 1.0 / 24.0)
        ax.set_xticks(h(hour_mjd))
        ax.set_xticklabels(
            [mjd_to_ts(m).round("min").strftime("%H:%M") for m in hour_mjd]
        )
        ax.tick_params(axis="x", length=3, pad=3)
        ax.text(
            h(hour_mjd[-1]) + 0.45,
            y0 - 0.40,
            "UTC",
            ha="left",
            va="top",
            fontsize=12,
            color=C["ink2"],
        )
        ax.set_title(
            f"{pd.Timestamp(str(DAY_OBS)):%Y-%m-%d}  (day_obs {DAY_OBS})", loc="left"
        )
        # legend for the visit colours: only categories present
        handles = [
            mpl.patches.Patch(facecolor=C[c], label=c)
            for c in ("Survey Programs", "Focus and Alignment", "Engineering")
            if (visits.category == c).any()
        ]
        ax.legend(
            handles=handles,
            loc="lower right",
            frameon=False,
            fontsize=13,
            ncol=2,
            bbox_to_anchor=(1.0, 0.0),
            handlelength=1.2,
        )
        fig.subplots_adjust(left=0.01, right=0.99, bottom=0.08, top=0.9)
        stem = FIG / f"night_brackets_{DAY_OBS}"
        fig.savefig(f"{stem}.png", dpi=200, transparent=True)
        fig.savefig(f"{stem}_white.png", dpi=200, facecolor="white")
        print("wrote", stem, "[_white].png")
    return long_gaps, weather_blocks, fault_blocks, brackets


def report(visits, night, weather, long_gaps, weather_blocks, fault_blocks, brackets):
    n0, n1 = night["set18"], night["rise18"]
    f = lambda m: mjd_to_ts(m).strftime("%Y-%m-%d %H:%M:%S")  # noqa: E731
    print(f"night −18°: {f(n0)} → {f(n1)}  {(n1 - n0) * 24:.3f} h")
    print(
        f"night −12°: {f(night['set12'])} → {f(night['rise12'])}  {(night['rise12'] - night['set12']) * 24:.3f} h"
    )
    print(
        "WEATHER bit windows:",
        [(f(a), f(b), round((b - a) * 24, 3)) for a, b in weather],
    )
    print("gaps > 10 min inside the −18° night:")
    for a, b in long_gaps:
        w = hours(
            [clip(a, b, wa, wb) for wa, wb in weather_blocks if min(b, wb) > max(a, wa)]
        )
        print(
            f"  {f(a)} → {f(b)}  {(b - a) * 24:.3f} h  weather {w:.3f} h  fault+idle {(b - a) * 24 - w:.3f} h"
        )
    print(
        "weather hours",
        round(hours(weather_blocks), 3),
        "fault+idle hours",
        round(hours(fault_blocks), 3),
    )
    for name, segs in brackets:
        shown = (
            [(f(a), f(b)) for a, b in segs]
            if len(segs) <= 4
            else f"{len(segs)} visit intervals"
        )
        print(f"bracket {name!r}: {hours(segs):.3f} h, segments", shown)
    inside = visits[(visits.start < n1) & (visits.end > n0)]
    print(
        "visits per category inside −18° night:",
        inside.category.value_counts().to_dict(),
    )
    print(
        "visits per category all:",
        visits.category.value_counts().to_dict(),
        "programs",
        visits.program.value_counts().to_dict(),
    )
    print(
        f"visits after morning −18°: {(visits.start >= n1).sum()}, covering {hours([clip(a, b, n1, 1e9) for a, b in zip(visits.start, visits.end) if b > n1]):.3f} h"
    )
    g = (visits.start.to_numpy()[1:] - visits.end.to_numpy()[:-1]) * 86400.0
    print(
        f"inter-visit gaps: {len(g)}; <= 60 s: {(g <= 60).sum()}; 60 s – 10 min: {((g > 60) & (g < GAP_MIN_S)).sum()}; >= 10 min: {(g >= GAP_MIN_S).sum()}; median {np.median(g):.1f} s"
    )
    bridged = subtract([(n0, n1)], weather_blocks + fault_blocks)
    print(
        f"B3-style bridged on-sky hours: {hours(bridged):.3f}; summed visit intervals inside night: {hours(brackets[3][1]):.3f}; overhead between visits {hours(bridged) - hours(brackets[3][1]):.3f} h"
    )


def main():
    visits, night, weather = load()
    out = make_figure(visits, night, weather)
    report(visits, night, weather, *out)


if __name__ == "__main__":
    main()
