# Night-log export: weather vs fault time loss

Per-night export of the Simonyi "Rubin Observatory Night Report" free-text fields, as a
verbatim CSV to be judged (weather loss vs fault loss) in a separate step.

- **Ticket:** none yet
- **Status:** data export done (2026-10-17); classification of nights not started
- **Range:** day_obs 20251025 to 20260720 inclusive (269 nights), telescope = Simonyi

## Contents

- `python/export_nightlog.py` — queries the USDF night-report REST service and writes the CSV.
  Needs an RSP token for usdf-rsp in `~/.token_file` (or `$ACCESS_TOKEN`). No stack dependency,
  only `httpx`.
- `data/nightlog_simonyi_20251025_20260720.csv` — one row per day_obs, UTF-8, all fields quoted,
  line breaks preserved inside fields. Columns: `day_obs`, `report_found`, `date_sent`, `summary`,
  `weather_summary`, `simonyi_summary`, `auxtel_summary`, `obs_tickets`, `submitted_by`,
  `observers_crew`, `nightly_digest_url`, `manual_note`.
- `data/manual_notes.csv` — hand-written annotations (`day_obs`, `manual_note`) merged into the
  `manual_note` column at export time. The only non-verbatim content in the CSV. Currently one
  entry: 20260720, night lost to the big storm that shut down the observatory.
- `notes/ai_notes.md` — context, decisions and hand-off notes for AI-assisted sessions.

## Data source

```
GET https://usdf-rsp.slac.stanford.edu/nightreport/reports
    ?telescopes=Simonyi&min_day_obs=<day_obs>&max_day_obs=<day_obs+1>&is_valid=true
```

This is the same service the Nightly Digest (https://usdf-rsp.slac.stanford.edu/nightlydigest)
and the nightly email read from. The query is the one used by
`rubin_nights.logging_query.NightReportClient`.

## Result of the 2026-10-17 export

| | |
|---|---|
| nights in range | 269 |
| report found | 258 |
| no report | 11: 20260428–20260505 (8 nights), 20260701, 20260702, 20260720 |
| nights with more than one valid report | none |

## Re-running

```bash
cd python
python export_nightlog.py --start 20251025 --end 20260720 --telescope Simonyi
```
