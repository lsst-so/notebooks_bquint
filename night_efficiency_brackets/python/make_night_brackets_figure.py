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

* ``rosp24_intervals_<day_obs>.csv`` — the ROSP-24 ordered classification of the night
  (weather / engineering / fault + idle / survey / start-up allowance interval sets) exported
  from ``simonyi_time_loss/data/cache/classification.pkl`` (time_loss/classify.py); since
  2026-10-26 the blocks and brackets are read from it, not recomputed here.
* ``allsky_cloud_1min_<day_obs>.csv`` — allskycam cloud index of the night (Brian Stalder's
  product), the ROSP-24 §C weather fallback where the WEATHER bit is masked.

Definitions (ROSP-24 precedence as implemented in simonyi_time_loss, gap_min = 10 min, −12° night):

* the night is the ROSP-22 observable night, Sun altitude −12° → −12° (``NIGHT_SUN_ALT``;
  rubin_nights ``day_obs_sunset_sunrise``), weather and downtime not excluded. Until
  2026-10-26 the figure used −18°; the −18° limits are still drawn as thin ticks;
* visit categories as in B10: Survey Programs (BLOCK-407/408/416/417/419/421), Focus and
  Alignment (BLOCK-T539), Engineering (everything else on sky);
* time goes to the first category that applies: weather (WEATHER bit, or the allskycam
  cloud index > 0.5 / C1 tower limits where FAULT or DOWNTIME masks the bit) → engineering
  (non-survey visits, Focus and Alignment included) → fault + idle (the remainder) → survey
  (visits bridged at gaps ≤ 10 min) with the first 10 min after −12° as start-up allowance;
* brackets: observable night (−12° → −12°); "Survey time only" = night − weather −
  engineering; "Excluding faults (= on sky)" = survey visits + bridged gaps (+ start-up
  allowance); "Exposing" = shutter-open only, the sum of ``exp_time`` of the survey visits
  (ROSP-24 A1; the "exposing + readout" value is printed for the README).

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
NIGHT_SUN_ALT = (
    -12
)  # ROSP-22 observable night; the other limit (−18°) is drawn as thin ticks
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
    "22:54": "clouds (allsky cam,\nthen WEATHER bit)",
    "00:20": "camera recovery\n(FRACAS-404)",
    "01:47": "clouds (allsky cam)",
    "01:59": "camera recovery\n(FRACAS-404)",
    "03:36": "HV bias trip (OBS-2010)",
}

DATA = ROOT / "data"
FIG = ROOT / "figures"
FIG.mkdir(exist_ok=True)

# One palette across the talk figures (2026-10-26, same as simonyi_time_loss/time_loss/style.py):
# survey = green (slot 5), engineering = orange (slot 2, as B10/B10b), weather = neutral grey,
# fault + idle = brand blue. Validated on all pairs (worst CVD dE 12.3, normal 15.5, PASS).
# Focus and Alignment is engineering under ROSP-24 and takes the engineering colour.
C = {
    "Survey Programs": rp.CATEGORICAL[4],
    "Focus and Alignment": rp.CATEGORICAL[1],
    "Engineering": rp.CATEGORICAL[1],
    "startup": rp.CATEGORICAL[4],
    "weather": rp.NEUTRALS["muted"],
    "weather_text": rp.NEUTRALS["ink_secondary"],
    "fault": rp.BRAND["blue"],
    "fault_text": rp.BRAND["blue"],
    "ink": rp.NEUTRALS["ink"],
    "ink2": rp.NEUTRALS["ink_secondary"],
    "muted": rp.NEUTRALS["muted"],
    "grid": rp.NEUTRALS["grid"],
}
LEGEND_LABEL = {
    "Survey Programs": "survey",
    "Focus and Alignment": "engineering (Focus and Alignment, BLOCK-T539)",
    "Engineering": "engineering",
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
        {
            "start": start,
            "end": end,
            "category": cat,
            "program": prog,
            "exp_time": v.exp_time.to_numpy(),
        }
    )
    nl = pd.read_csv(DATA / f"night_limits_{DAY_OBS}.csv").iloc[0]
    a = -NIGHT_SUN_ALT
    night = {
        "set": nl[f"sunset{a}_mjd"],  # the accounting night (NIGHT_SUN_ALT)
        "rise": nl[f"sunrise{a}_mjd"],
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
    rosp = pd.read_csv(DATA / f"rosp24_intervals_{DAY_OBS}.csv")
    cats = {
        k: [(a, b) for a, b in zip(g.start_mjd, g.end_mjd)]
        for k, g in rosp.groupby("category")
    }
    for k in (
        "weather",
        "weather_bit",
        "weather_fallback",
        "engineering",
        "fault_idle",
        "survey",
        "startup",
    ):
        cats.setdefault(k, [])
    return visits, night, weather, cats


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


def gaps_and_brackets(visits, night, weather, cats):
    """Blocks and brackets from the ROSP-24 classification of the night (``cats``)."""
    n0, n1 = night["set"], night["rise"]
    weather_blocks = [clip(a, b, n0, n1) for a, b in cats["weather"]]
    weather_blocks = [(a, b) for a, b in weather_blocks if b > a]
    fault_blocks = [(a, b) for a, b in cats["fault_idle"] if b > a]
    eng_blocks = [(a, b) for a, b in cats["engineering"] if b > a]
    survey_blocks = [(a, b) for a, b in cats["survey"] if b > a]
    startup_blocks = [(a, b) for a, b in cats["startup"] if b > a]
    long_gaps = sorted(weather_blocks + fault_blocks)
    whole = [(n0, n1)]
    minus_weather_eng = subtract(subtract(whole, weather_blocks), eng_blocks)
    on_sky = sorted(
        survey_blocks + startup_blocks
    )  # = night − weather − engineering − fault/idle
    sv = visits[visits.category == "Survey Programs"]
    inside = sv[(sv.start < n1) & (sv.end > n0)]
    exposing_h = float(inside.exp_time.sum()) / 3600.0
    exp_readout = [clip(a, b, n0, n1) for a, b in zip(inside.start, inside.end)]
    brackets = [
        ("Observable night", whole),
        ("Survey time only", minus_weather_eng),
        ("Excluding faults (= on sky)", on_sky),
        ("Exposing", exposing_h),  # hours, drawn packed against the last visit
    ]
    extras = dict(
        eng_blocks=eng_blocks, startup_blocks=startup_blocks, exp_readout=exp_readout
    )
    return long_gaps, weather_blocks, fault_blocks, brackets, extras


def make_figure(visits, night, weather, cats):
    long_gaps, weather_blocks, fault_blocks, brackets, extras = gaps_and_brackets(
        visits, night, weather, cats
    )
    n0, n1 = night["set"], night["rise"]
    t0 = night["set"]  # axis origin: evening twilight of the accounting night

    def h(mjd):
        return (np.asarray(mjd) - t0) * 24.0

    with mpl.rc_context(RC):
        fig, ax = plt.subplots()
        y0, y1 = 0.0, 1.0  # strip
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
        above_slots = [0]  # stagger narrow-block labels above the strip
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
                        alpha=0.30 if key == "weather" else 0.18,
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
                why = GAP_LABELS.get(mjd_to_ts(a).strftime("%H:%M"), "")
                label = f"{name}\n{hrs:.1f} h"
                if hrs > 1.0:
                    ax.text(
                        h((a + b) / 2),
                        (y0 + y1) / 2,
                        label + (f"\n{why}" if why else ""),
                        ha="center",
                        va="center",
                        fontsize=11 if hrs < 1.6 else 14,
                        color=C[f"{key}_text"],
                        linespacing=1.15,
                        zorder=3,
                    )
                else:  # too narrow: label above the strip with a leader, staggered
                    k = len(above_slots) - 1  # 0, 1, 2 ... → alternate heights
                    above_slots.append(k)
                    ax.annotate(
                        f"{name} {hrs:.1f} h"
                        + (f", {why.replace(chr(10), ' ')}" if why else ""),
                        xy=(h((a + b) / 2), y1),
                        xytext=(h((a + b) / 2) + 0.25, y1 + 0.17 + 0.14 * (k % 2)),
                        ha="left",
                        va="center",
                        fontsize=12,
                        color=C[f"{key}_text"],
                        arrowprops=dict(
                            arrowstyle="-",
                            color=C[f"{key}_text"],
                            lw=0.8,
                            shrinkA=0,
                            shrinkB=0,
                        ),
                        zorder=3,
                    )
        # start-up allowance (A3): lighter survey tint, no label (minutes)
        for a, b in extras["startup_blocks"]:
            ax.add_patch(
                mpl.patches.Rectangle(
                    (h(a), y0),
                    h(b) - h(a),
                    y1 - y0,
                    facecolor=C["startup"],
                    alpha=0.35,
                    edgecolor="none",
                    zorder=1.5,
                )
            )
        # visits (inside the night solid; outside it lighter)
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
        # twilight marks: the accounting night thick, the other definition as thin ticks
        thick, thin = ("12", "18") if NIGHT_SUN_ALT == -12 else ("18", "12")
        for mjd, lab, lw in (
            (night[f"set{thick}"], f"−{thick}°", 1.4),
            (night[f"rise{thick}"], f"−{thick}°", 1.4),
            (night[f"set{thin}"], f"−{thin}°", 0.9),
            (night[f"rise{thin}"], f"−{thin}°", 0.9),
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
        last_end = brackets[2][1][-1][1]
        for i, (name, segs) in enumerate(brackets):
            y = base + (len(brackets) - 1 - i) * step
            if isinstance(segs, float):
                # hundreds of 30 s exposures: draw their summed length packed against the
                # end of the last survey visit (dotted, to say "packed, not a time span")
                hrs = segs
                segs_draw = [(last_end - hrs / 24.0, last_end)]
                ls = (0, (1.5, 1.5))
            else:
                hrs = hours(segs)
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
                f"{hrs:.1f} h",
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
        ax.set_xlim(
            h(min(night["set12"], night["set18"])) - 3.3,
            h(max(night["rise12"], night["rise18"])) + 1.2,
        )
        ax.set_ylim(y0 - 0.95, base + (len(brackets) - 1) * step + 0.25)
        ax.set_yticks([])
        for sp in ("left", "right", "top"):
            ax.spines[sp].set_visible(False)
        ax.spines["bottom"].set_position(("data", y0 - 0.32))
        ax.spines["bottom"].set_visible(False)
        first_hour = np.ceil(min(night["set12"], night["set18"]) * 24.0) / 24.0
        last_hour = np.floor(max(night["rise12"], night["rise18"]) * 24.0) / 24.0
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
        handles = [
            mpl.patches.Patch(facecolor=C[c], label=LEGEND_LABEL[c])
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
    return long_gaps, weather_blocks, fault_blocks, brackets, extras


def report(
    visits,
    night,
    weather,
    cats,
    long_gaps,
    weather_blocks,
    fault_blocks,
    brackets,
    extras,
):
    n0, n1 = night["set"], night["rise"]
    f = lambda m: mjd_to_ts(m).strftime("%Y-%m-%d %H:%M:%S")  # noqa: E731
    print(
        f"accounting night ({NIGHT_SUN_ALT}°): {f(n0)} → {f(n1)}  {(n1 - n0) * 24:.3f} h"
    )
    print(
        f"night −18°: {f(night['set18'])} → {f(night['rise18'])}  {(night['rise18'] - night['set18']) * 24:.3f} h"
    )
    print(
        "WEATHER bit windows (Scheduler):",
        [(f(a), f(b), round((b - a) * 24, 3)) for a, b in weather],
    )
    print(
        "ROSP-24 weather: bit",
        [(f(a), f(b), round((b - a) * 24, 3)) for a, b in cats["weather_bit"]],
        "| fallback (bit masked)",
        [(f(a), f(b), round((b - a) * 24, 3)) for a, b in cats["weather_fallback"]],
    )
    print("loss blocks inside the night:")
    for a, b in long_gaps:
        kind = "weather" if (a, b) in weather_blocks else "fault + idle"
        print(
            f"  {f(a)} → {f(b)}  {(b - a) * 24:.3f} h  {kind}  {GAP_LABELS.get(mjd_to_ts(a).strftime('%H:%M'), '').replace(chr(10), ' ')}"
        )
    print(
        "engineering blocks:",
        [(f(a), f(b), round((b - a) * 24, 3)) for a, b in extras["eng_blocks"]],
    )
    print(
        "start-up allowance:",
        [(f(a), f(b), round((b - a) * 1440, 1)) for a, b in extras["startup_blocks"]],
        "min",
    )
    print(
        "weather hours",
        round(hours(weather_blocks), 3),
        "| engineering hours",
        round(hours(extras["eng_blocks"]), 3),
        "| fault+idle hours",
        round(hours(fault_blocks), 3),
        "| start-up",
        round(hours(extras["startup_blocks"]), 3),
    )
    for name, segs in brackets:
        if isinstance(segs, float):
            print(
                f"bracket {name!r}: {segs:.3f} h (sum of exp_time of the survey visits inside the night)"
            )
        else:
            shown = (
                [(f(a), f(b)) for a, b in segs]
                if len(segs) <= 4
                else f"{len(segs)} segments"
            )
            print(f"bracket {name!r}: {hours(segs):.3f} h, segments", shown)
    er = hours(extras["exp_readout"])
    print(
        f"exposing + readout (sum of survey visit intervals inside the night, README only): {er:.3f} h"
    )
    on_sky = hours(brackets[2][1])
    print(
        f"visit-scale overhead: on sky − exposing + readout = {on_sky - er:.3f} h; on sky − exposing = {on_sky - brackets[3][1]:.3f} h"
    )
    tot = (
        sum(hours(x) for x in (weather_blocks, fault_blocks, extras["eng_blocks"]))
        + on_sky
    )
    print(
        f"partition check: weather + engineering + fault/idle + on sky = {tot:.3f} h vs night {(n1 - n0) * 24:.3f} h"
    )
    inside = visits[(visits.start < n1) & (visits.end > n0)]
    print(
        "visits per category inside the night:",
        inside.category.value_counts().to_dict(),
        "| all:",
        visits.category.value_counts().to_dict(),
        "programs",
        visits.program.value_counts().to_dict(),
    )
    print(f"last visit end → morning limit: {(n1 - visits.end.max()) * 1440:.1f} min")
    g = (visits.start.to_numpy()[1:] - visits.end.to_numpy()[:-1]) * 86400.0
    print(
        f"inter-visit gaps: {len(g)}; <= 60 s: {(g <= 60).sum()}; 60 s – 10 min: {((g > 60) & (g < GAP_MIN_S)).sum()}; >= 10 min: {(g >= GAP_MIN_S).sum()}; median {np.median(g):.1f} s"
    )
    b1, b2, b3, b4 = [
        (hours(x) if not isinstance(x, float) else x) for _, x in brackets
    ]
    print(
        f"ratios: exposing {b4:.2f} h ÷ brackets 1/2/3 = {b4 / b1:.0%} / {b4 / b2:.0%} / {b4 / b3:.0%}; on sky {b3:.2f} h ÷ 1/2 = {b3 / b1:.0%} / {b3 / b2:.0%}; exposing + readout {er:.2f} h ÷ 1/2/3 = {er / b1:.0%} / {er / b2:.0%} / {er / b3:.0%}"
    )


def main():
    visits, night, weather, cats = load()
    out = make_figure(visits, night, weather, cats)
    report(visits, night, weather, cats, *out)


if __name__ == "__main__":
    main()
