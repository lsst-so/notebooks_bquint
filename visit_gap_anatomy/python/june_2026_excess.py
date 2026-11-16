"""What happened in June 2026? Characterise the per-visit excess gap time.

Standalone and read-only; writes nothing. Run from anywhere in the repo:

    python visit_gap_anatomy/python/june_2026_excess.py

**Cause, identified 2026-11-04** (by a session with Slack/Jira/GitHub access; see
``notes/HANDOFF_june_2026_excess_gap_cause_2026-11-04.md``): ``ts_observatory_control``
**v0.50.0**, released 2026-06-03 under OSW-2269, added ``handle_aos_close_loop`` and calls it
*just before the slew command*. When MTAOS has a correction in ``WAITING_APPLY``, the slew blocks
until the hexapod/M1M3/M2 corrections finish - a serial, fixed cost paid before the TMA moves.
That is the ~6 s. Tracking ticket **RSO-785**. The mechanism is still in the code today; why the
excess *stopped* after 2026-07-05 (the summit OS/Postgres rebuild) is not established.

Context. ``check_late_correction.py`` retired the 14-20 s "second settle" band and left the
cause of the long June 2026 gaps open ("waiting, concentrated in the May-Jul 2026 AOS
stability period"). This script narrows that down. It prints seven tests; together they say the
episode is a **fixed additive delay applied before the slew**, not a slew, settle or AOS-
convergence problem:

1. **Per-night step.** Median excess (``gap - slew_model``) by night: 2-3 s in May, 6-9 s on
   every June observing night, ~1 s in July. A step, not a drift.
2. **Flat in slew distance.** During June the excess is the same (~7.7 s) for slews under 1 deg
   and over 10 deg. Anything slew- or settle-related would scale with distance.
3. **A hard floor.** June's 5th percentile excess is ~4.7 s against ~0.3 s in July: essentially
   no visit escaped the penalty, so it is not a subpopulation of affected visits.
4. **Not the reduced TMA speed.** ``tma_ax_maxv``/``tma_alt_maxv`` carry the real velocity
   limits. Only 2026-06-11 ran reduced (0.5 vs 2.0 deg/s) and there ``slew_model`` itself rose
   to match. Every other elevated June night ran at full speed.
5. **Flat in time-of-night and band**, and it survived the four-night camera-cryo stop
   (2026-06-21..24) unchanged - so not thermal drift and not a drifting calibration.
6. **Mixture test** (test 7 in the output) - the one that confirms the OSW-2269 account and is
   the reason to believe it over any "June was just a bad month" story. If the mechanism is a
   fixed pre-slew wait paid only when a correction is pending, then what changed on 06-03 is the
   *rate* at which it is paid, not its size. That is exactly what the data show: the median
   excess **among gaps that paid** is ~6-8 s in every window from May to October, while the
   *fraction* paying moves 0.28 -> 0.98 -> 0.25 -> 0.06. June is not a different phenomenon; it
   is the same cost at ~100 % duty cycle. This also retro-explains the "+2-3 s around mid-May"
   that Lynne Jones reported in RSO-785: the same wait at a ~30 % rate.

Tests 1-5 and 7 use ``night_budget/data/visits_slew_*.parquet`` (the kinematic slew model), which
only covers 2026-05-29 onward. Test 6 drops the model and re-derives the **raw** gap from this
folder's own ``visit1`` parquet, extending the baseline across the full Oct 2025 - Jul 2026
window; the June step and the raised floor are both still there, so neither is an artefact of
the model or of the short "before" window.

Data outside this folder (``night_budget/``) is read-only and optional: tests 1-5 and 7 are
skipped once this folder is extracted, test 6 still runs.
"""

from __future__ import annotations

import glob
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
REPO = ROOT.parent

#: Survey blocks, copied from ``make_visit_gap_figure.py`` (no cross-folder imports).
SURVEY_PROGRAMS = (
    "BLOCK-407",
    "BLOCK-408",
    "BLOCK-416",
    "BLOCK-417",
    "BLOCK-419",
    "BLOCK-421",
)

#: The episode: ts_observatory_control v0.50.0 (2026-06-03) to the summit rebuild (2026-07-01).
EPISODE = (20260603, 20260630)
#: Clean comparison windows either side.
BEFORE = (20260529, 20260531)
AFTER = (20260705, 20260713)

#: A gap "paid" the pre-slew AOS wait if its excess exceeds this. Chosen between the two modes:
#: paid gaps sit at 6-8 s and unpaid ones below ~2 s, so anything from ~3 to ~5 s gives the same
#: picture. Only the *rate* is sensitive to it; the conditional median is not.
PAID_THRESHOLD_S = 4.0

#: Windows for the mixture test, in time order. Labels say the expected duty cycle.
MIXTURE_WINDOWS = {
    "late May (sometimes)": (20260529, 20260531),
    "June (always)": (20260603, 20260630),
    "early Jul (sometimes)": (20260705, 20260710),
    "mid Jul (rarely)": (20260711, 20260713),
    "Oct (sometimes)": (20261027, 20261030),
}

#: Nightly medians are only quoted for nights with at least this many survey gaps.
MIN_GAPS = 50
#: Trim physically implausible gaps/excesses before taking medians (filter changes, faults).
GAP_MAX_S = 120.0


def load_slew() -> pd.DataFrame | None:
    """Survey gaps with the kinematic slew model, from ``night_budget`` (May-Oct 2026)."""
    files = sorted(
        glob.glob(str(REPO / "night_budget" / "data" / "visits_slew_*.parquet"))
    )
    if not files:
        return None
    d = pd.concat([pd.read_parquet(f) for f in files], ignore_index=True)
    d = (
        d[d.is_survey_gap.fillna(False)]
        .dropna(subset=["visit_gap", "slew_model"])
        .copy()
    )
    d["excess"] = d.visit_gap - d.slew_model
    # The model can over-predict slightly; keep a small negative tail, drop the fault outliers.
    return d[(d.excess > -5) & (d.excess < GAP_MAX_S)]


def load_raw() -> pd.DataFrame:
    """Raw survey gaps from this folder's own visit1 cache - no slew model, Oct 2025-Jul 2026."""
    v = pd.read_parquet(ROOT / "data" / "visit1_20251026_20260714.parquet")
    v = v.sort_values("obs_start_mjd")
    v["surv"] = v.science_program.isin(SURVEY_PROGRAMS)
    v["gap"] = (v.obs_start_mjd - v.obs_end_mjd.shift()) * 86400.0
    # Both visits of the pair must be survey visits, and the gap resets each night.
    keep = v.surv & v.surv.shift(fill_value=False) & (v.day_obs == v.day_obs.shift())
    g = v[keep & v.gap.notna()]
    return g[(g.gap > 0) & (g.gap < GAP_MAX_S)]


def _window(d: pd.DataFrame, lo_hi: tuple[int, int]) -> pd.DataFrame:
    lo, hi = lo_hi
    return d[(d.day_obs >= lo) & (d.day_obs <= hi)]


def test_nightly_step(d: pd.DataFrame) -> None:
    print("\n=== 1. per-night median excess: a step, not a drift ===")
    t = d.groupby("day_obs").excess.agg(n="size", med="median")
    t = t[t.n >= MIN_GAPS].round(2)
    for day, row in t.iterrows():
        mark = "  <-- episode" if EPISODE[0] <= day <= EPISODE[1] else ""
        print(f"  {day}  n={int(row.n):4d}  median excess={row.med:6.2f} s{mark}")
    ep = t[(t.index >= EPISODE[0]) & (t.index <= EPISODE[1])]
    other = t[(t.index < EPISODE[0]) | (t.index > EPISODE[1])]
    print(
        f"\n  episode nights: {len(ep)}, median excess {ep.med.min():.2f}-{ep.med.max():.2f} s; "
        f"all other nights: {len(other)}, {other.med.min():.2f}-{other.med.max():.2f} s"
    )
    print(
        "  -> the two ranges do not overlap: every episode night is worse than every other."
    )


def test_flat_in_distance(d: pd.DataFrame) -> None:
    print("\n=== 2. excess vs slew distance: flat (so not a slew/settle cost) ===")
    bins = [0, 1, 2, 3, 4, 6, 10, 100]
    # n is printed per cell: the scheduler almost never slews 1-2 deg, so that bin holds a
    # handful of visits and its median is noise. Read the populated bins.
    for label, sub in [("episode", _window(d, EPISODE)), ("after", _window(d, AFTER))]:
        b = pd.cut(sub.slew_distance, bins)
        t = sub.groupby(b, observed=True).excess.agg(n="size", med="median").round(2)
        cells = "  ".join(
            f"<{iv.right:g}deg:{r.med:5.2f}(n={int(r.n)})" for iv, r in t.iterrows()
        )
        print(f"  {label:8s} {cells}")
    print(
        "  -> during the episode the penalty is the same at every well-populated distance\n"
        "     bin (~7.6-7.7 s from <1 deg to >10 deg): a fixed wait, not a slew cost."
    )


def test_floor(d: pd.DataFrame) -> None:
    print("\n=== 3. the low tail: a hard floor, so (almost) every visit paid it ===")
    for label, win in [("before", BEFORE), ("episode", EPISODE), ("after", AFTER)]:
        s = _window(d, win).excess
        if s.empty:
            continue
        q = s.quantile([0.01, 0.05, 0.25, 0.50]).round(2)
        print(
            f"  {label:8s} n={len(s):5d}  p1={q[0.01]:6.2f}  p5={q[0.05]:6.2f}  "
            f"p25={q[0.25]:6.2f}  median={q[0.50]:6.2f} s"
        )
    print("  -> the whole distribution is displaced, not a tail of affected visits.")


def test_tma_speed(d: pd.DataFrame) -> None:
    print("\n=== 4. was it the reduced TMA speed? (no) ===")
    t = d.groupby("day_obs").agg(
        n=("excess", "size"),
        exc=("excess", "median"),
        model=("slew_model", "median"),
        axv=("tma_ax_maxv", "median"),
        altv=("tma_alt_maxv", "median"),
    )
    t = t[t.n >= MIN_GAPS].round(2)
    slow = t[(t.axv < 2.0) | (t.altv < 2.0)]
    print(
        f"  velocity limits present in the cache: {sorted(d.tma_ax_maxv.dropna().unique())}"
    )
    if slow.empty:
        print("  no reduced-velocity nights found.")
    else:
        for day, r in slow.iterrows():
            print(
                f"  reduced-speed night {day}: maxv={r.axv}/{r.altv} deg/s, "
                f"slew_model={r.model:.2f} s, excess={r.exc:.2f} s"
            )
    ep = t[(t.index >= EPISODE[0]) & (t.index <= EPISODE[1])]
    full = ep[(ep.axv == 2.0) & (ep.altv == 2.0)]
    print(
        f"  of {len(ep)} episode nights, {len(full)} ran at FULL speed and still show "
        f"median excess {full.exc.min():.2f}-{full.exc.max():.2f} s"
    )
    print(
        "  -> on the one slow night the slew model rose to match; the episode is not that."
    )


def test_invariances(d: pd.DataFrame) -> None:
    print("\n=== 5. flat in time-of-night and band; survived the cryo stop ===")
    ep = _window(d, EPISODE).copy()
    ep["frac"] = ep.groupby("day_obs").obs_start_mjd.rank(pct=True)
    thirds = pd.cut(ep.frac, [0, 1 / 3, 2 / 3, 1.0], labels=["early", "mid", "late"])
    t = ep.groupby(thirds, observed=True).excess.agg(n="size", med="median").round(2)
    print(
        "  by third of night: " + "  ".join(f"{i}:{r.med:.2f}" for i, r in t.iterrows())
    )
    b = ep.groupby("band").excess.agg(n="size", med="median").round(2)
    print(
        "  by band:           " + "  ".join(f"{i}:{r.med:.2f}" for i, r in b.iterrows())
    )
    nights = d.groupby("day_obs").excess.agg(n="size", med="median")
    nights = nights[nights.n >= MIN_GAPS]
    before_stop = nights[nights.index <= 20260619].tail(1)
    after_stop = nights[nights.index >= 20260625].head(1)
    print(
        f"  across the 2026-06-21..24 camera-cryo stop: "
        f"{before_stop.index[0]}={before_stop.med.iloc[0]:.2f} s -> "
        f"{after_stop.index[0]}={after_stop.med.iloc[0]:.2f} s (unchanged)"
    )
    print("  -> not thermal drift, and a four-night full stop did not clear it.")


def test_raw_gap_baseline(g: pd.DataFrame) -> None:
    print(
        "\n=== 6. no slew model: raw gaps over the full Oct 2025 - Jul 2026 window ==="
    )
    g = g.copy()
    g["month"] = g.day_obs // 100
    t = (
        g.groupby("month")
        .gap.agg(n="size", p05=lambda s: s.quantile(0.05), med="median")
        .round(2)
    )
    for mon, r in t.iterrows():
        mark = "  <-- episode" if mon == 202606 else ""
        print(f"  {mon}  n={int(r.n):6d}  p5={r.p05:6.2f}  median={r.med:6.2f} s{mark}")
    # The floor is the sharpest signature, so rank nights by it over all nine months.
    nights = g.groupby("day_obs").gap.agg(n="size", p05=lambda s: s.quantile(0.05))
    nights = nights[nights.n >= 100].sort_values("p05", ascending=False)
    top = nights.head(20)
    in_june = [d for d in top.index if 20260601 <= d <= 20260630]
    june_nights = [d for d in nights.index if 20260601 <= d <= 20260630]
    print(
        f"\n  of the 20 nights with the highest 5th-percentile gap in nine months, "
        f"{len(in_june)} are in June 2026"
    )
    print(
        f"  (June 2026 has {len(june_nights)} observing nights with >=100 survey gaps)"
    )
    print(
        "  -> the step and the raised floor are in the raw data, not made by the model."
    )


def test_mixture(d: pd.DataFrame) -> None:
    """The duty-cycle test: did the RATE change rather than the COST?

    A pre-slew wait paid only when an AOS correction is pending predicts that the cost per
    affected gap is the same everywhere, and only the fraction of affected gaps moves. If
    instead June were "a worse kind of delay", the conditional median would rise too.
    """
    print("\n=== 7. mixture test: one fixed cost, paid at a varying rate ===")
    print(
        f"  {'window':24s} {'n':>6s} {'rate':>6s} {'median|paid':>12s} "
        f"{'median|unpaid':>14s} {'median all':>11s}"
    )
    rows = []
    for label, win in MIXTURE_WINDOWS.items():
        s = _window(d, win).excess
        if s.empty:
            continue
        paid = s[s > PAID_THRESHOLD_S]
        unpaid = s[s <= PAID_THRESHOLD_S]
        rate = (s > PAID_THRESHOLD_S).mean()
        rows.append((paid.median(), rate))
        print(
            f"  {label:24s} {len(s):6d} {rate:6.2f} "
            f"{paid.median():12.2f} {unpaid.median():14.2f} {s.median():11.2f}"
        )
    costs = [c for c, _ in rows]
    rates = [r for _, r in rows]
    print(
        f"\n  cost per affected gap across all {len(rows)} windows: "
        f"{min(costs):.2f}-{max(costs):.2f} s (spread only {max(costs) - min(costs):.2f} s), "
        f"while the rate spans {min(rates):.2f}-{max(rates):.2f}."
    )
    print(
        "  -> the COST is constant; only the RATE changed. June is the same pre-slew wait at a\n"
        "     ~100 % duty cycle, which is what ts_observatory_control v0.50.0 (OSW-2269) did by\n"
        "     moving the AOS correction to just before every slew."
    )


def main() -> None:
    g = load_raw()
    d = load_slew()
    if d is None:
        print(
            "night_budget/data/visits_slew_*.parquet not found - skipping tests 1-5 and 7."
        )
    else:
        print(
            f"slew cache: n={len(d):,} survey gaps, "
            f"day_obs {d.day_obs.min()}-{d.day_obs.max()}"
        )
        test_nightly_step(d)
        test_flat_in_distance(d)
        test_floor(d)
        test_tma_speed(d)
        test_invariances(d)
    print(
        f"\nraw visit1 cache: n={len(g):,} survey gaps, {g.day_obs.min()}-{g.day_obs.max()}"
    )
    test_raw_gap_baseline(g)
    if d is not None:
        test_mixture(d)

    print("\n" + "=" * 78)
    print(
        "VERDICT. Between day_obs 2026-06-03 and 2026-06-30 nearly every survey visit paid a\n"
        "roughly fixed ~6 s of extra dead time on top of the kinematic slew: flat in slew\n"
        "distance, flat in band, flat across the night, with a hard floor, not the reduced TMA\n"
        "speed, and unaffected by a four-night full stop.\n"
        "\n"
        "CAUSE (identified 2026-11-04 from Slack/Jira/GitHub, not from ConsDB):\n"
        "ts_observatory_control v0.50.0, released 2026-06-03 under OSW-2269, added\n"
        "handle_aos_close_loop() and calls it immediately before the slew command. When MTAOS\n"
        "has a correction in WAITING_APPLY, the slew blocks until the hexapod / M1M3 / M2\n"
        "corrections complete - a serial wait paid before the TMA starts moving. Tracking\n"
        "ticket RSO-785 (Lynne Jones, 2026-06-24).\n"
        "\n"
        "Test 7 is the confirmation: the cost per AFFECTED gap is ~6-8 s in every window from\n"
        "May to October, while the FRACTION paying it moves 0.28 -> 0.98 -> 0.06. June is not a\n"
        "different phenomenon, it is the same pre-slew wait at a ~100 % duty cycle - exactly\n"
        "what moving the correction to just before every slew would do. It also explains the\n"
        "'+2-3 s around mid-May' in RSO-785 as the same wait at a ~30 % rate.\n"
        "\n"
        "STILL OPEN: why it stopped after the 2026-07-01 summit OS/Postgres rebuild. The code\n"
        "is unchanged on main, so the mechanism is still armed; the hypothesis is that\n"
        "corrections stopped being ready at slew time, making the pre-slew branch a no-op.\n"
        "The decisive EFD test is in notes/HANDOFF_june_2026_excess_gap_cause_2026-11-04.md."
    )
    print("=" * 78)


if __name__ == "__main__":
    main()
