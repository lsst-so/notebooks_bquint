"""Reproduce the three RASAB image-quality reports from ConsDB.

Reports (see ../notes/RASAB*.md for the saved answers):

  best       best delivered-FWHM visit in a dayObs window
  ellip      good-FWHM but highly elliptical visit in a dayObs window

Usage (from a stack shell, see "Environment" below)::

    python rasab_iq_reports.py best  20251024 20251231
    python rasab_iq_reports.py best  20260501 20260727
    python rasab_iq_reports.py ellip 20260215 20260314 --programs BLOCK-421 BLOCK-407

Environment
-----------
On an SDF login node (VS Code shell) there is no RSP token, so the script talks to the
ConsDB Postgres replica through ``rubin_nights.consdb_query.ConsDbSql``::

    source /sdf/group/rubin/sw/loadLSST.bash
    setup lsst_distrib
    export PGPASSFILE=$HOME/.lsst/postgres-credentials.txt

In a Nublado kernel ``rubin_nights.connections.get_clients()["consdb"]`` works too; swap it
in ``get_client`` if preferred. Any object with ``.query(sql) -> DataFrame`` is fine.

Method
------
* Visits: ``cdb_lsstcam.visit1`` joined to ``visit1_quicklook``; ``img_type = 'science'``,
  ``exp_time >= 15`` s, ``psf_sigma_median IS NOT NULL``, optional ``science_program`` filter.
* Delivered FWHM [arcsec] = psf_sigma [pix] * 2*sqrt(2*ln 2) * 0.2 arcsec/pix.
* Zenith/500 nm correction (reported as a caveat only):
  FWHM * airmass**-0.6 * (lambda_eff / 500 nm)**0.2.
* Per-detector numbers come from ``ccdvisit1`` + ``ccdvisit1_quicklook``, excluding the corner
  wavefront sensors (191, 192, 195, 196, 199, 200, 203, 204).
* Ellipticity from the PSF second moments: e1 = (Ixx-Iyy)/(Ixx+Iyy), e2 = 2 Ixy/(Ixx+Iyy),
  |e| = hypot(e1, e2), PA = 0.5*atan2(e2, e1).
* ``ellip`` keeps visits with >= 150 detectors and median FWHM below ``--fwhm-max`` (0.85"),
  then ranks by per-visit median |e|; also lists the 95th-percentile-|e| and FWHM-variation
  rankings as alternative "bad shape" flavours.

Outputs go to ``../data/`` (per-visit CSV) and the summary is printed to stdout.
"""

from __future__ import annotations

import argparse
import logging
import os
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
DATA = HERE.parent / "data"

PIXEL_SCALE = 0.2  # arcsec / pixel
SIG2FWHM = 2 * np.sqrt(2 * np.log(2))
LAMBDA_EFF = {"u": 367, "g": 482, "r": 622, "i": 755, "z": 869, "y": 971}  # nm
CORNER_WFS = (191, 192, 195, 196, 199, 200, 203, 204)
VISIT_COLS = [
    "visit_id",
    "day_obs",
    "seq_num",
    "band",
    "exp_time",
    "science_program",
    "observation_reason",
    "airmass",
    "altitude",
    "dimm_seeing",
    "psf_fwhm",
    "psf_fwhm_z500",
    "aos_fwhm",
    "donut_blur_fwhm",
    "e_med",
    "n_inputs",
]

pd.set_option("display.width", 260)
pd.set_option("display.max_columns", 40)


def get_client():
    """ConsDB client via the USDF Postgres replica (works on SDF login nodes)."""
    logging.disable(logging.WARNING)
    from rubin_nights.consdb_query import ConsDbSql

    os.environ.setdefault(
        "PGPASSFILE", os.path.expanduser("~/.lsst/postgres-credentials.txt")
    )
    return ConsDbSql(site="usdf")


def _df(result) -> pd.DataFrame:
    return result if isinstance(result, pd.DataFrame) else result.to_pandas()


def program_filter(programs: list[str] | None) -> str:
    if not programs:
        return ""
    quoted = ", ".join(f"'{p}'" for p in programs)
    return f"AND v.science_program IN ({quoted})"


def fetch_visits(client, d0: int, d1: int, programs=None) -> pd.DataFrame:
    """Per-visit quicklook summary for science visits in [d0, d1]."""
    sql = f"""
    SELECT v.visit_id, v.day_obs, v.seq_num, v.band, v.physical_filter, v.exp_time,
           v.img_type, v.science_program, v.observation_reason, v.target_name,
           v.airmass, v.altitude, v.azimuth, v.sky_rotation, v.dimm_seeing, v.wind_speed,
           v.air_temp, v.s_ra, v.s_dec, v.obs_start,
           q.psf_sigma_median, q.psf_sigma_min, q.psf_sigma_max, q.aos_fwhm,
           q.donut_blur_fwhm, q.psf_ixx_median, q.psf_ixy_median, q.psf_iyy_median,
           q.n_inputs
    FROM cdb_lsstcam.visit1 v
    JOIN cdb_lsstcam.visit1_quicklook q ON v.visit_id = q.visit_id
    WHERE v.day_obs BETWEEN {d0} AND {d1}
      AND v.img_type = 'science' AND v.exp_time >= 15
      AND q.psf_sigma_median IS NOT NULL
      {program_filter(programs)}
    """
    df = _df(client.query(sql))
    df["psf_fwhm"] = df.psf_sigma_median * SIG2FWHM * PIXEL_SCALE
    lam = df.band.map(LAMBDA_EFF)
    df["psf_fwhm_z500"] = df.psf_fwhm * df.airmass**-0.6 * (lam / 500.0) ** 0.2
    t = df.psf_ixx_median + df.psf_iyy_median
    df["e_med"] = np.hypot(
        (df.psf_ixx_median - df.psf_iyy_median) / t, 2 * df.psf_ixy_median / t
    )
    return df


def fetch_detectors(client, where: str) -> pd.DataFrame:
    """Per-detector PSF size and moments, corner WFS excluded."""
    sql = f"""
    SELECT v.visit_id, v.day_obs, v.seq_num, v.band, v.science_program, v.observation_reason,
           v.airmass, v.altitude, v.azimuth, v.sky_rotation, v.dimm_seeing, v.wind_speed,
           v.obs_start, q.aos_fwhm, q.donut_blur_fwhm, q.guider_e1_mean, q.guider_e2_mean,
           cv.detector, cq.psf_sigma, cq.psf_ixx, cq.psf_ixy, cq.psf_iyy
    FROM cdb_lsstcam.visit1 v
    JOIN cdb_lsstcam.visit1_quicklook q ON v.visit_id = q.visit_id
    JOIN cdb_lsstcam.ccdvisit1 cv ON cv.visit_id = v.visit_id
    JOIN cdb_lsstcam.ccdvisit1_quicklook cq ON cq.ccdvisit_id = cv.ccdvisit_id
    WHERE {where}
      AND cq.psf_sigma IS NOT NULL AND cq.psf_ixx IS NOT NULL
      AND cv.detector NOT IN {CORNER_WFS}
    """
    d = _df(client.query(sql))
    d["fwhm"] = d.psf_sigma * SIG2FWHM * PIXEL_SCALE
    t = d.psf_ixx + d.psf_iyy
    d["e1"] = (d.psf_ixx - d.psf_iyy) / t
    d["e2"] = 2 * d.psf_ixy / t
    d["e"] = np.hypot(d.e1, d.e2)
    d["pa"] = np.degrees(0.5 * np.arctan2(d.e2, d.e1))
    return d


def describe_visit(client, visit_id: int) -> None:
    d = fetch_detectors(client, f"v.visit_id = {visit_id}")
    f, e = d.fwhm, d.e
    print(
        f"  per-detector (n={len(d)}): FWHM min {f.min():.3f} p5 {f.quantile(0.05):.3f} "
        f"med {f.median():.3f} p95 {f.quantile(0.95):.3f} max {f.max():.3f} arcsec; "
        f"|e| med {e.median():.3f} p95 {e.quantile(0.95):.3f}; "
        f"e1 {d.e1.median():+.3f} e2 {d.e2.median():+.3f}; PA {d.pa.median():.1f} "
        f"(std {d.pa.std():.1f}) deg; frac |e|>0.2 {(e > 0.2).mean():.2f}"
    )
    r = d.iloc[0]
    print(
        f"  obs_start {r.obs_start}  alt {r.altitude:.1f} az {r.azimuth:.1f} rot {r.sky_rotation:.1f} "
        f"airmass {r.airmass:.3f} DIMM {r.dimm_seeing} AOS {r.aos_fwhm:.3f} donut {r.donut_blur_fwhm:.3f} "
        f"wind {r.wind_speed} guider e1/e2 {r.guider_e1_mean} / {r.guider_e2_mean}"
    )


# --------------------------------------------------------------------------- reports
def report_best(client, d0: int, d1: int, programs=None, n_top=15) -> None:
    sci = fetch_visits(client, d0, d1, programs)
    out = DATA / f"visits_science_{d0}_{d1}.csv"
    sci.to_csv(out, index=False)
    print(
        f"{len(sci)} science visits; programs: {sci.science_program.value_counts().head(6).to_dict()}"
    )
    print(f"saved {out}\n")
    print("Best raw delivered FWHM:")
    print(
        sci.sort_values("psf_fwhm")[VISIT_COLS]
        .head(n_top)
        .round(3)
        .to_string(index=False)
    )
    print("\nBest zenith/500nm-corrected FWHM (caveat only; favours high airmass):")
    print(
        sci.sort_values("psf_fwhm_z500")[VISIT_COLS]
        .head(5)
        .round(3)
        .to_string(index=False)
    )
    print("\nPer-band best:")
    print(
        sci.loc[sci.groupby("band").psf_fwhm.idxmin()][VISIT_COLS]
        .round(3)
        .to_string(index=False)
    )
    print("\nPer-month delivered FWHM:")
    print(
        sci.groupby(sci.day_obs // 100)
        .psf_fwhm.describe(percentiles=[0.05, 0.5])
        .round(3)
        .to_string()
    )
    frac = (sci.psf_fwhm < 0.8).mean()
    print(
        f'\nVisits with FWHM < 0.8": {(sci.psf_fwhm < 0.8).sum()} of {len(sci)} ({100 * frac:.1f}%)'
    )
    best = sci.sort_values("psf_fwhm").iloc[0]
    print(
        f"\nBest visit {int(best.visit_id)} ({best.science_program}, {best.observation_reason}):"
    )
    describe_visit(client, int(best.visit_id))
    night = sci[sci.day_obs == best.day_obs]
    print(
        f"  night {best.day_obs}: {len(night)} visits, median FWHM {night.psf_fwhm.median():.3f}, "
        f'5th pct {night.psf_fwhm.quantile(0.05):.3f}, n<0.75" {(night.psf_fwhm < 0.75).sum()}, '
        f'n<0.60" {(night.psf_fwhm < 0.6).sum()}'
    )
    # If the overall best is an engineering block, also show the best of the main survey block.
    main = sci.science_program.value_counts().idxmax()
    if best.science_program != main:
        b2 = sci[sci.science_program == main].sort_values("psf_fwhm").iloc[0]
        print(
            f"\nBest {main} (main survey block) visit {int(b2.visit_id)}: FWHM {b2.psf_fwhm:.3f}"
        )
        describe_visit(client, int(b2.visit_id))


def report_ellip(
    client, d0: int, d1: int, programs=None, fwhm_max=0.85, min_det=150
) -> None:
    where = (
        f"v.day_obs BETWEEN {d0} AND {d1} AND v.img_type = 'science' AND v.exp_time >= 15 "
        f"{program_filter(programs)}"
    )
    d = fetch_detectors(client, where)  # ~1.7M rows for a 4-week window; a few minutes
    g = d.groupby("visit_id")
    v = pd.DataFrame(
        {
            "day_obs": g.day_obs.first(),
            "seq_num": g.seq_num.first(),
            "band": g.band.first(),
            "program": g.science_program.first(),
            "reason": g.observation_reason.first(),
            "airmass": g.airmass.first(),
            "alt": g.altitude.first(),
            "az": g.azimuth.first(),
            "rot": g.sky_rotation.first(),
            "dimm": g.dimm_seeing.first(),
            "wind": g.wind_speed.first(),
            "obs_start": g.obs_start.first(),
            "aos": g.aos_fwhm.first(),
            "donut": g.donut_blur_fwhm.first(),
            "fwhm50": g.fwhm.median(),
            "fwhm05": g.fwhm.quantile(0.05),
            "fwhm95": g.fwhm.quantile(0.95),
            "e50": g.e.median(),
            "e95": g.e.quantile(0.95),
            "e1_50": g.e1.median(),
            "e2_50": g.e2.median(),
            "guider_e1": g.guider_e1_mean.first(),
            "guider_e2": g.guider_e2_mean.first(),
            "ndet": g.fwhm.size(),
        }
    )
    v["fwhm_var"] = np.sqrt(v.fwhm95**2 - v.fwhm05**2)
    v = v[v.ndet >= min_det]
    out = DATA / f"visits_fbs_{d0}_{d1}.csv"
    v.to_csv(out)
    print(
        f"{len(v)} visits with >= {min_det} detectors; programs: {v.program.value_counts().to_dict()}"
    )
    print(f"saved {out}")
    print(
        "FWHM50 quantiles (5/25/50/75/95):",
        v.fwhm50.quantile([0.05, 0.25, 0.5, 0.75, 0.95]).round(3).tolist(),
    )
    print(
        "|e|50 quantiles  (5/25/50/75/95/99):",
        v.e50.quantile([0.05, 0.25, 0.5, 0.75, 0.95, 0.99]).round(3).tolist(),
    )
    cols = [
        "day_obs",
        "seq_num",
        "band",
        "program",
        "reason",
        "airmass",
        "alt",
        "az",
        "rot",
        "dimm",
        "wind",
        "aos",
        "donut",
        "fwhm50",
        "fwhm05",
        "fwhm95",
        "e50",
        "e95",
        "e1_50",
        "e2_50",
        "ndet",
    ]
    good = v[v.fwhm50 < fwhm_max]
    print(f'\n{len(good)} visits with FWHM50 < {fwhm_max}"')
    print("\n--- Good FWHM ranked by median |e| (whole-field elongation) ---")
    print(good.sort_values("e50", ascending=False)[cols].head(12).round(3).to_string())
    print("\n--- Good FWHM ranked by 95th-pct |e| (bad corners) ---")
    print(good.sort_values("e95", ascending=False)[cols].head(8).round(3).to_string())
    print("\n--- Good FWHM ranked by FoV FWHM variation sqrt(p95^2 - p05^2) ---")
    print(
        good.sort_values("fwhm_var", ascending=False)[cols + ["fwhm_var"]]
        .head(8)
        .round(3)
        .to_string()
    )
    top = int(good.sort_values("e50", ascending=False).index[0])
    print(f"\nTop candidate {top}:")
    describe_visit(client, top)
    x = d[d.visit_id == top].assign(raft=lambda t: t.detector // 9)
    print("  per-raft median |e| / e1 / e2 / FWHM:")
    print(
        x.groupby("raft")
        .agg(
            e=("e", "median"),
            e1=("e1", "median"),
            e2=("e2", "median"),
            fwhm=("fwhm", "median"),
        )
        .round(3)
        .T.to_string()
    )


def main() -> None:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("report", choices=["best", "ellip"])
    ap.add_argument("day_obs_min", type=int)
    ap.add_argument("day_obs_max", type=int)
    ap.add_argument(
        "--programs", nargs="*", help="restrict to these science_program values"
    )
    ap.add_argument(
        "--fwhm-max",
        type=float,
        default=0.85,
        help="ellip: 'good FWHM' threshold [arcsec]",
    )
    a = ap.parse_args()
    DATA.mkdir(exist_ok=True)
    client = get_client()
    if a.report == "best":
        report_best(client, a.day_obs_min, a.day_obs_max, a.programs)
    else:
        report_ellip(client, a.day_obs_min, a.day_obs_max, a.programs, a.fwhm_max)


if __name__ == "__main__":
    main()
