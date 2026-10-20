"""Pull the EFD channels the weather criteria need, at 1-minute cadence, for every night.

Window per night: [sunset18 - 2 h, sunrise18 + 1 h] UTC, so the pre-opening
state and the end-of-night close are included. Output: one parquet with a UTC
DatetimeIndex and a ``day_obs`` column, ``data/cache/efd_weather_1min.parquet``.
Re-runnable: nights already in the cache are skipped unless --refresh.

Channels (names kept short; provenance in README §3.5):
  t_out, rh_out, dp_out       weather tower ESS:301 temperature / RH / dew point
  wind, gust                  weather tower ESS:301 airFlow speed (1-min mean) and max over the minute
  dp_cam                      camera inlet ESS:111 dew point (inside)
  dp_m2, dp_m1m3              ESS:112, ESS:113 dew points (inside)
  sply                        MTCamera utiltrunk_UT coolPipeSplyTemp (Dynalene supply at camera)
  dyn_az1, dyn_az2, dyn_pier2 MTMount dynaleneCooling temperatures (Azimuth0001/0002, Pier0102)
  shutter                     MTDome apertureShutter positionActual0 (0 closed .. 100 open)
  mcover                      MTMount mirrorCover actualPosition0 (~2 open .. ~135 closed)
  el                          MTMount elevation actualPosition (deg)
"""

from __future__ import annotations

import argparse
import logging
import sys
import time
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from time_loss import access  # noqa: E402

OUT = HERE.parent / "data" / "cache" / "efd_weather_1min.parquet"
LIMITS = HERE.parent / "data" / "step0" / "night_limits.csv"

QUERIES = {
    "t_out": ("lsst.sal.ESS.temperature", "mean(temperatureItem0)", "salIndex=301"),
    "rh_out": (
        "lsst.sal.ESS.relativeHumidity",
        "mean(relativeHumidityItem)",
        "salIndex=301",
    ),
    "dp_out": ("lsst.sal.ESS.dewPoint", "mean(dewPointItem)", "salIndex=301"),
    "wind": ("lsst.sal.ESS.airFlow", "mean(speed)", "salIndex=301"),
    "gust": ("lsst.sal.ESS.airFlow", "max(maxSpeed)", "salIndex=301"),
    "dp_cam": ("lsst.sal.ESS.dewPoint", "mean(dewPointItem)", "salIndex=111"),
    "dp_m2": ("lsst.sal.ESS.dewPoint", "mean(dewPointItem)", "salIndex=112"),
    "dp_m1m3": ("lsst.sal.ESS.dewPoint", "mean(dewPointItem)", "salIndex=113"),
    "sply": ("lsst.sal.MTCamera.utiltrunk_UT", "mean(coolPipeSplyTemp)", None),
    "dyn_az1": (
        "lsst.sal.MTMount.dynaleneCooling",
        "mean(dynaleneTemperatureAzimuth0001)",
        None,
    ),
    "dyn_az2": (
        "lsst.sal.MTMount.dynaleneCooling",
        "mean(dynaleneTemperatureAzimuth0002)",
        None,
    ),
    "dyn_pier2": (
        "lsst.sal.MTMount.dynaleneCooling",
        "mean(dynaleneTemperaturePier0102)",
        None,
    ),
    "shutter": ("lsst.sal.MTDome.apertureShutter", "mean(positionActual0)", None),
    "mcover": ("lsst.sal.MTMount.mirrorCover", "mean(actualPosition0)", None),
    "el": ("lsst.sal.MTMount.elevation", "mean(actualPosition)", None),
}


def pull_night(efd, day_obs: int, t0: pd.Timestamp, t1: pd.Timestamp) -> pd.DataFrame:
    where = f"time >= '{t0:%Y-%m-%dT%H:%M:%S}Z' AND time < '{t1:%Y-%m-%dT%H:%M:%S}Z'"
    cols = []
    for name, (topic, agg, extra) in QUERIES.items():
        w = where + (f" AND {extra}" if extra else "")
        sql = f'SELECT {agg} AS "{name}" FROM "{topic}" WHERE {w} GROUP BY time(1m)'
        for attempt in range(3):
            try:
                d = efd.query(sql)
                break
            except Exception as err:  # noqa: BLE001
                logging.warning(
                    "%s %s attempt %d: %s", day_obs, name, attempt, type(err).__name__
                )
                time.sleep(5)
                d = pd.DataFrame()
        if len(d):
            cols.append(d[[name]])
    if not cols:
        return pd.DataFrame()
    out = pd.concat(cols, axis=1).sort_index()
    out.index = out.index.tz_convert(None)
    out["day_obs"] = int(day_obs)
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--refresh", action="store_true")
    ap.add_argument("--start", type=int, default=None)
    ap.add_argument("--end", type=int, default=None)
    args = ap.parse_args()
    logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(message)s")
    lim = pd.read_csv(LIMITS)
    if args.start:
        lim = lim[lim.day_obs >= args.start]
    if args.end:
        lim = lim[lim.day_obs <= args.end]
    done = set()
    frames = []
    if OUT.exists() and not args.refresh:
        prev = pd.read_parquet(OUT)
        frames.append(prev)
        done = set(prev.day_obs.unique())
    efd = access.get_efd_client()
    t_start = time.time()
    for i, r in enumerate(lim.itertuples(index=False)):
        if r.day_obs in done:
            continue
        t0 = pd.Timestamp(r.sunset18_utc) - pd.Timedelta(hours=2)
        t1 = pd.Timestamp(r.sunrise18_utc) + pd.Timedelta(hours=1)
        d = pull_night(efd, int(r.day_obs), t0, t1)
        frames.append(d)
        if (i + 1) % 10 == 0 or i == len(lim) - 1:
            pd.concat(frames).to_parquet(OUT)
            print(
                f"{r.day_obs} ({i + 1}/{len(lim)}) rows so far {sum(len(f) for f in frames)} elapsed {time.time() - t_start:.0f}s",
                flush=True,
            )
    pd.concat(frames).to_parquet(OUT)
    print("wrote", OUT)


if __name__ == "__main__":
    main()
