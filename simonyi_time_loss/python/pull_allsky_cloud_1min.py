"""Resample Brian Stalder's allskycam cloud index to the 1-minute grid of the EFD cache.

Source: ``/sdf/data/rubin/user/stalder/allsky/cloud/<day_obs>.parquet`` (one row per
allskycam frame, ~1 per minute while the Sun is below −12°; ``cloud_idx`` = 1 − observed /
expected bright stars under the clear-sky completeness model, clipped to [0, 1]; pipeline
v5 of 2026-10-10, products dated 2026-10-18 when read on 2026-10-26). ROSP-24 §C names this
product, with the threshold ``cloud_idx > 0.5``, as the weather fallback where the WEATHER
bit is absent or masked.

Output: ``data/cache/allsky_cloud_1min.parquet`` with a UTC DatetimeIndex (1-min), columns
``cloud_idx``, ``frac_sky_cloudy``, ``geometry_ok``, ``day_obs``. A minute gets the value of
the nearest frame within ``MAX_GAP_MIN``; otherwise NaN (no frame = no evidence).
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from time_loss import DAY_OBS_MAX, DAY_OBS_MIN  # noqa: E402

ALLSKY = Path("/sdf/data/rubin/user/stalder/allsky/cloud")
OUT = HERE.parent / "data" / "cache" / "allsky_cloud_1min.parquet"
LIMITS = HERE.parent / "data" / "step0" / "night_limits.csv"
MAX_GAP_MIN = 3.0  # a minute more than this far from any frame is NaN
MJD_UNIX = 40587.0


def main() -> None:
    lim = pd.read_csv(LIMITS)
    lim = lim[(lim.day_obs >= DAY_OBS_MIN) & (lim.day_obs <= DAY_OBS_MAX)]
    frames, missing = [], []
    for r in lim.itertuples(index=False):
        f = ALLSKY / f"{int(r.day_obs)}.parquet"
        if not f.exists():
            missing.append(int(r.day_obs))
            continue
        c = pd.read_parquet(
            f, columns=["mjd", "cloud_idx", "frac_sky_cloudy", "geometry_ok"]
        ).sort_values("mjd")
        t0 = (pd.Timestamp(r.sunset18_utc) - pd.Timedelta(hours=2)).floor("min")
        t1 = (pd.Timestamp(r.sunrise18_utc) + pd.Timedelta(hours=1)).ceil("min")
        grid = pd.date_range(t0, t1, freq="1min")
        gm = grid.view("int64") / 86400e9 + MJD_UNIX
        pos = np.searchsorted(c.mjd.to_numpy(), gm)
        lo = np.clip(pos - 1, 0, len(c) - 1)
        hi = np.clip(pos, 0, len(c) - 1)
        dlo = np.abs(gm - c.mjd.to_numpy()[lo])
        dhi = np.abs(gm - c.mjd.to_numpy()[hi])
        near = np.where(dlo <= dhi, lo, hi)
        dist_min = np.minimum(dlo, dhi) * 1440.0
        ok = dist_min <= MAX_GAP_MIN
        d = pd.DataFrame(index=grid)
        for col in ("cloud_idx", "frac_sky_cloudy"):
            v = c[col].to_numpy()[near].astype(float)
            v[~ok] = np.nan
            d[col] = v
        g = c.geometry_ok.to_numpy()[near].astype(float)
        g[~ok] = np.nan
        d["geometry_ok"] = g
        d["day_obs"] = int(r.day_obs)
        frames.append(d)
    out = pd.concat(frames)
    out.to_parquet(OUT)
    print(
        f"wrote {OUT}: {len(out)} minutes, {out.day_obs.nunique()} nights, "
        f"cloud_idx NaN {out.cloud_idx.isna().mean():.1%}; nights without a cloud file: {missing}"
    )


if __name__ == "__main__":
    main()
