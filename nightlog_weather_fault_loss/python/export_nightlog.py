"""Export Simonyi night-report summaries to a per-night CSV.

Queries the USDF night-report REST service (the same source the Nightly Digest
and the nightly "Rubin Observatory Night Report" email read from) for every
day_obs in a range and writes one row per night, verbatim, without any
interpretation.

Usage (from a USDF login node or RSP terminal)::

    python export_nightlog.py [--start 20251025] [--end 20260720]
                              [--telescope Simonyi] [--token-file ~/.token_file]

Authentication is an RSP token for usdf-rsp (https://usdf-rsp.slac.stanford.edu/auth/tokens,
any read:* scopes). The token is read from --token-file, else $ACCESS_TOKEN.

The query is the one used by ``rubin_nights.logging_query.NightReportClient``;
it is reproduced here with httpx so the script has no stack dependencies.
"""

from __future__ import annotations

import argparse
import csv
import os
import re
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

import httpx

API_BASE = "https://usdf-rsp.slac.stanford.edu"
ENDPOINT = API_BASE + "/nightreport/reports"
DIGEST_URL = API_BASE + "/nightlydigest/?startDayobs={d}&endDayobs={d}&telescope={tel}"
OBS_KEY_RE = re.compile(r"\bOBS-\d+\b")

# Text fields of the record that are scanned for OBS keys.
TEXT_FIELDS = ("summary", "weather", "maintel_summary", "auxtel_summary")

COLUMNS = [
    "day_obs",
    "report_found",
    "date_sent",
    "summary",
    "weather_summary",
    "simonyi_summary",
    "auxtel_summary",
    "obs_tickets",
    "submitted_by",
    "observers_crew",
    "nightly_digest_url",
    "manual_note",
]

# Optional hand-written annotations merged into the ``manual_note`` column.
# Columns: day_obs, manual_note. Everything else in the CSV is verbatim from the API.
MANUAL_NOTES = Path(__file__).parent.parent / "data" / "manual_notes.csv"


def day_obs_range(start: int, end: int):
    d = datetime.strptime(str(start), "%Y%m%d").date()
    last = datetime.strptime(str(end), "%Y%m%d").date()
    while d <= last:
        yield d
        d += timedelta(days=1)


def dayobs_int(d: date) -> int:
    return int(d.strftime("%Y%m%d"))


def read_token(token_file: str | None) -> str:
    if token_file:
        p = Path(token_file).expanduser()
        if p.exists():
            return p.read_text().strip()
    tok = os.environ.get("ACCESS_TOKEN", "")
    if not tok:
        sys.exit("No RSP token: pass --token-file or set ACCESS_TOKEN.")
    return tok


def fetch_reports(client: httpx.Client, d: date, telescope: str) -> list[dict]:
    params = {
        "telescopes": telescope,
        "min_day_obs": dayobs_int(d),
        "max_day_obs": dayobs_int(d + timedelta(days=1)),
        "is_valid": "true",
    }
    for attempt in range(3):
        r = client.get(ENDPOINT, params=params)
        if r.status_code == 200:
            break
    r.raise_for_status()
    # The service returns [min, max) on day_obs but keep only the exact night.
    return [rec for rec in r.json() if rec.get("day_obs") == dayobs_int(d)]


def extract_obs_keys(rec: dict) -> str:
    keys: list[str] = []
    for f in TEXT_FIELDS:
        for k in OBS_KEY_RE.findall(rec.get(f) or ""):
            if k not in keys:
                keys.append(k)
    return ";".join(keys)


def read_manual_notes(path: Path = MANUAL_NOTES) -> dict[int, str]:
    if not path.exists():
        return {}
    with path.open(newline="", encoding="utf-8") as fh:
        return {int(r["day_obs"]): r["manual_note"] for r in csv.DictReader(fh)}


def record_to_row(d: date, rec: dict | None, telescope: str) -> dict:
    ds = dayobs_int(d)
    row = {c: "" for c in COLUMNS}
    row["day_obs"] = ds
    row["report_found"] = "true" if rec else "false"
    row["nightly_digest_url"] = DIGEST_URL.format(d=ds, tel=telescope)
    if rec:
        row["date_sent"] = rec.get("date_sent") or ""
        row["summary"] = rec.get("summary") or ""
        row["weather_summary"] = rec.get("weather") or ""
        row["simonyi_summary"] = rec.get("maintel_summary") or ""
        row["auxtel_summary"] = rec.get("auxtel_summary") or ""
        row["obs_tickets"] = extract_obs_keys(rec)
        row["submitted_by"] = rec.get("user_id") or ""
        row["observers_crew"] = ";".join(rec.get("observers_crew") or [])
    return row


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--start", type=int, default=20251025)
    ap.add_argument("--end", type=int, default=20260720)
    ap.add_argument("--telescope", default="Simonyi", choices=["Simonyi", "AuxTel"])
    ap.add_argument("--token-file", default="~/.token_file")
    ap.add_argument(
        "--out",
        default=None,
        help="CSV path (default: ../data/nightlog_<tel>_<start>_<end>.csv)",
    )
    args = ap.parse_args()

    out = (
        Path(args.out)
        if args.out
        else Path(__file__).parent.parent
        / "data"
        / f"nightlog_{args.telescope.lower()}_{args.start}_{args.end}.csv"
    )
    out.parent.mkdir(parents=True, exist_ok=True)

    token = read_token(args.token_file)
    manual_notes = read_manual_notes()
    rows: list[dict] = []
    missing: list[int] = []
    multiple: dict[int, list[str]] = {}

    with httpx.Client(auth=("user", token), timeout=60) as client:
        for d in day_obs_range(args.start, args.end):
            recs = fetch_reports(client, d, args.telescope)
            rec = None
            if recs:
                recs.sort(key=lambda r: r.get("date_sent") or r.get("date_added") or "")
                rec = recs[-1]
                if len(recs) > 1:
                    multiple[dayobs_int(d)] = [
                        f"{r.get('id')} sent {r.get('date_sent')}"
                        + (" [kept]" if r is rec else "")
                        for r in recs
                    ]
            else:
                missing.append(dayobs_int(d))
            row = record_to_row(d, rec, args.telescope)
            row["manual_note"] = manual_notes.get(dayobs_int(d), "")
            rows.append(row)
            print(
                f"{dayobs_int(d)} {'ok ' if rec else '-- '}{len(recs)}", file=sys.stderr
            )

    with out.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(
            fh, fieldnames=COLUMNS, quoting=csv.QUOTE_ALL, lineterminator="\n"
        )
        w.writeheader()
        w.writerows(rows)

    n_found = len(rows) - len(missing)
    print(f"\nWrote {out}")
    print(f"Nights: {len(rows)}  report_found=true: {n_found}  false: {len(missing)}")
    print("Missing day_obs:", ", ".join(map(str, missing)) if missing else "none")
    if multiple:
        print("\nNights with more than one valid report (latest date_sent kept):")
        for ds, items in multiple.items():
            print(f"  {ds}:")
            for it in items:
                print(f"    {it}")
    else:
        print("Nights with more than one valid report: none")


if __name__ == "__main__":
    main()
