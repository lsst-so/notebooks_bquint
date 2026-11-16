"""Was the 14-20 s band really a "second settle"? (It was not; the shading is gone.)

The band came from the 23 Oct 2026 handoff: typical gap ~6-8 s plus the ~8 s between the
two slew-flag pairs Tiago Ribeiro reported (#survey-performance, 10 Sep 2026, read off
Craig's 6-13 Jul event plots). It was set by hand and never fitted or tested. These are
the tests; they refuted it, and the shading was removed from the figures on 2026-11-04.

Three tests of the claim that the 14-20 s gaps are a distinct population created by a
late AOS correction carrying a pointing offset, which forces a second slew and settle:

1. **Shape.** A second settle adds a roughly fixed extra time, so it should appear as a
   *separate bump* on the gap histogram. Test: is there a local maximum in 12-23 s?
2. **Time.** If it is the AOS stability period, the 14-20 s pairs should concentrate in
   the May-July 2026 window rather than being spread over the whole survey.
3. **Mechanism.** ``night_budget/data/visits_slew_*.parquet`` carries the kinematic
   ``slew_model`` prediction per gap. A second *slew* needs a longer modelled slew or a
   longer slew distance; a late *correction* only adds dead time on top of an unchanged
   slew. Test: inside the band, does ``slew_model`` / ``slew_distance`` grow, or only
   ``visit_gap - slew_model``?

The slew parquets cover May-Oct 2026 only, so test 3 is the episode and its recovery,
not the full window. Both caches are read read-only; nothing is written.

Run: ``python visit_gap_anatomy/python/check_late_correction.py``.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
REPO = ROOT.parent

DATA = ROOT / "data" / "visit1_20251026_20260714.parquet"
#: Kinematic-model cache from ``night_budget``. Read-only and outside this folder, so
#: test 3 is skipped (rather than failing) once this folder is extracted on its own.
SLEW = sorted((REPO / "night_budget" / "data").glob("visits_slew_*.parquet"))

SURVEY_PROGRAMS = (
    "BLOCK-407",
    "BLOCK-408",
    "BLOCK-416",
    "BLOCK-417",
    "BLOCK-419",
    "BLOCK-421",
)
BAND = (14.0, 20.0)
EPISODE = ("2026-05-01", "2026-08-01")  # the AOS stability period, half-open


def survey_gaps() -> pd.DataFrame:
    """Same gap definition as ``make_visit_gap_figure.survey_gaps``."""
    v = pd.read_parquet(DATA).sort_values("obs_start_mjd").reset_index(drop=True)
    gap = (v.obs_start_mjd - v.obs_end_mjd.shift()) * 86400.0
    same_night = v.day_obs == v.day_obs.shift()
    surv = v.science_program.isin(SURVEY_PROGRAMS)
    keep = same_night & surv & surv.shift(fill_value=False)
    g = v.loc[keep, ["visit_id", "day_obs"]].copy()
    g["gap_s"] = gap[keep]
    g["date"] = pd.to_datetime(g.day_obs.astype(str))
    g["month"] = g.date.dt.to_period("M")
    return g


def test_shape(g: pd.DataFrame) -> None:
    """A second settle should add a separate mode, not thicken the existing tail."""
    print("\n=== 1. shape: is there a second mode at 14-20 s? ===")
    epochs = {
        "all": g,
        "Feb-Apr 2026 (best)": g[(g.date >= "2026-02-01") & (g.date < "2026-05-01")],
        "Jun 2026 (episode)": g[g.month == pd.Period("2026-06")],
        "Jul 2026 (recovered)": g[g.date >= "2026-07-01"],
    }
    print(
        "  'excess over tail' = the band's height above a log-linear fit to the decay\n"
        "  either side of it (8-13 s and 22-30 s). A second population stands above\n"
        "  that fit; a smooth decaying tail sits at ~1x. The fit is only meaningful\n"
        "  where the band is on the *falling* side of the distribution, i.e. where the\n"
        "  peak is below 8 s - in the episode the peak has moved into the lower flank,\n"
        "  so the fit measures the shift, not an extra population, and is reported n/a.\n"
    )
    for label, sub in epochs.items():
        counts, edges = np.histogram(
            sub.gap_s[sub.gap_s < 40], bins=np.arange(0, 40.5, 0.5)
        )
        frac = counts / len(sub)
        centers = 0.5 * (edges[:-1] + edges[1:])
        peak = centers[frac.argmax()]

        # Fit the decay on either side of the band and interpolate across it: if the
        # band were a separate population it would stand above that interpolation.
        flank = (
            ((centers >= 8) & (centers < 13)) | ((centers > 22) & (centers <= 30))
        ) & (frac > 0)
        in_band = (centers >= BAND[0]) & (centers <= BAND[1])
        slope, intercept = np.polyfit(centers[flank], np.log(frac[flank]), 1)
        expected = np.exp(intercept + slope * centers[in_band]).sum()
        # Only valid while the lower flank is past the peak and still decaying.
        valid = peak < 8.0 and slope < 0
        ratio = f"{frac[in_band].sum() / expected:4.2f}x" if valid else " n/a"
        print(
            f"  {label:22s} n={len(sub):6d}  median={sub.gap_s.median():5.2f} s  "
            f"peak={peak:4.1f} s  f(14-20)={sub.gap_s.between(*BAND).mean():5.1%}  "
            f"excess over tail={ratio}"
        )
    print(
        "  -> wherever the test is valid the band sits at ~1x or below: it is the\n"
        "     ordinary decaying tail, not an extra population. In the episode the\n"
        "     whole curve slid right (peak 7.2 -> 13.2 s) and the band is simply where\n"
        "     the bulk now lives - a shift of one mode, not the appearance of a second."
    )


def test_time(g: pd.DataFrame) -> None:
    """If it is the AOS episode, the band should not be spread over the survey."""
    print("\n=== 2. time: where do the 14-20 s pairs come from? ===")
    sel = g.gap_s.between(*BAND)
    by_month = g[sel].groupby("month").size()
    share = g.groupby("month").size()
    print("  month      pairs in band   share of band   f(14-20) that month")
    for m, n in by_month.items():
        print(
            f"  {m}      {n:6d}        {n / sel.sum():8.1%}        {n / share[m]:6.1%}"
        )

    ep = (g.date >= EPISODE[0]) & (g.date < EPISODE[1])
    print(
        f"\n  May-Jul 2026 is {ep.mean():.1%} of all pairs but "
        f"{(sel & ep).sum() / sel.sum():.1%} of the band."
    )
    out = g[~ep]
    print(
        f"  Drop that window and f(14-20) falls from {sel.mean():.1%} to "
        f"{out.gap_s.between(*BAND).mean():.1%} (median "
        f"{g.gap_s.median():.2f} -> {out.gap_s.median():.2f} s)."
    )
    print(
        "  -> the band is an episode, not a standing property of a survey visit.\n"
        "     The '12% of visits' label is a window cut through a distribution that\n"
        "     shifted for three months, not a 12% sub-population."
    )


def test_mechanism() -> None:
    """Separate 'another slew' from 'dead time on top of the same slew'."""
    print("\n=== 3. mechanism: extra slew, or extra dead time? ===")
    if not SLEW:
        print("  skipped: night_budget/data/visits_slew_*.parquet not found")
        return
    d = pd.concat([pd.read_parquet(f) for f in SLEW], ignore_index=True)
    g = d[d.is_survey_gap & d.visit_gap.notna()].copy()
    g["month"] = pd.to_datetime(g.day_obs.astype(str)).dt.to_period("M")
    g["excess"] = g.visit_gap - g.slew_model  # dead time the kinematics cannot explain

    print(
        f"  source: {len(g):,} survey gaps with a kinematic model, "
        f"{g.month.min()}-{g.month.max()}"
    )
    print("\n  month     n     gap    slew_model   excess   slew_dist   f(14-20)")
    for m, sub in g.groupby("month"):
        print(
            f"  {m}  {len(sub):5d}  {sub.visit_gap.median():6.2f}  "
            f"{sub.slew_model.median():9.2f}  {sub.excess.median():7.2f}  "
            f"{sub.slew_distance.median():9.2f}  {sub.visit_gap.between(*BAND).mean():7.1%}"
        )

    sel = g.visit_gap.between(*BAND)
    print("\n  inside vs outside the 14-20 s band:")
    for label, sub in [("outside", g[~sel]), ("inside ", g[sel])]:
        print(
            f"    {label}  n={len(sub):6d}  gap={sub.visit_gap.median():6.2f}  "
            f"slew_model={sub.slew_model.median():5.2f}  "
            f"excess={sub.excess.median():5.2f}  "
            f"slew_dist={sub.slew_distance.median():5.2f} deg"
        )
    print(
        "  -> the modelled slew and the slew distance are flat; only the excess moves.\n"
        "     The telescope is not slewing further or more often: it is waiting. That\n"
        "     is consistent with a correction applied late, and it rules out a second\n"
        "     *slew*. Whether the wait is an AOS correction, settle or scheduler\n"
        "     latency cannot be told apart from ConsDB alone - it needs the EFD."
    )

    print("\n  excess-gap profile (a fixed-cost second settle would be bimodal):")
    for label, sub in [
        ("Jul 2026 (recovered)", g[g.month == pd.Period("2026-07")]),
        ("Jun 2026 (episode) ", g[g.month == pd.Period("2026-06")]),
    ]:
        counts, edges = np.histogram(
            sub.excess.clip(-2, 25), bins=np.arange(-2, 25.5, 0.5)
        )
        frac = counts / len(sub)
        peak = edges[:-1][frac.argmax()]
        print(
            f"    {label}  n={len(sub):5d}  median excess={sub.excess.median():5.2f} s  "
            f"single peak at {peak:4.1f} s"
        )
    print(
        "     One peak in both: it slides from ~0.5 s to ~6 s. The whole population\n"
        "     shifted; it did not split into corrected and uncorrected visits."
    )


def main() -> None:
    g = survey_gaps()
    print(f"{len(g):,} survey visit pairs, median gap {g.gap_s.median():.2f} s")
    test_shape(g)
    test_time(g)
    test_mechanism()

    sel = g.gap_s.between(*BAND)
    ep = (g.date >= EPISODE[0]) & (g.date < EPISODE[1])
    print(
        "\n=== verdict ===\n"
        "The band marks real lost time, but 'second settle' is not supported:\n"
        "  * no separate 14-20 s mode in any epoch -> not a distinct population;\n"
        f"  * {(sel & ep).sum() / sel.sum():.0%} of the band is May-Jul 2026 -> an "
        "episode, not a standing cost;\n"
        "  * slew model and slew distance unchanged inside the band -> no second slew,\n"
        "    only dead time, and the excess is unimodal and merely shifted.\n"
        "So the shading was dropped rather than relabelled (2026-11-04): a shaded band\n"
        "reads as a measured population and this is not one. What is defensible is\n"
        "'waiting, concentrated in the May-Jul 2026 AOS stability period', which is what\n"
        "the weekly panel's grey span now says. Testing the second-settle mechanism\n"
        "needs the M1M3 / TMA slew-flag timestamps per gap (Lynne Jones's redone\n"
        "sub-timings, #survey-performance 10 Sep 2026)."
    )


if __name__ == "__main__":
    main()
