# AI notes — nightlog_weather_fault_loss

Running log of context, decisions and hand-offs for AI-assisted work in this folder.
Append a dated entry for each session that changes something. Newest entry last.

## Purpose of the investigation

Bruno Quint (Rubin Summit Support Scientist) wants a per-night table of weather time loss vs
fault time loss for the Simonyi telescope. The work is split in two:

1. **Extraction (this folder, done):** pull the night-report free text verbatim into a CSV.
   No interpretation, no summarising, no corrections.
2. **Judgement (not started):** a separate session reads the CSV and classifies each night
   (weather loss, fault loss, amounts). Results of that step should also land in this folder.

## Data source and access

- Endpoint: `https://usdf-rsp.slac.stanford.edu/nightreport/reports`, params
  `telescopes`, `min_day_obs`, `max_day_obs` (half-open on day_obs), `is_valid=true`.
- Auth: HTTP basic with `("user", <RSP token>)`. The token must be for **usdf-rsp** (not
  usdf-rsp-dev, not summit). Create one at https://usdf-rsp.slac.stanford.edu/auth/tokens with
  the `read:*` scopes; there is no `read:all` scope in the UI. Bruno keeps it in `~/.token_file`.
  Tokens expire; a 401 from nginx (HTML body) means the token is invalid or expired, and
  `GET /auth/api/v1/user-info` with `Authorization: Bearer <token>` confirms it.
- From a USDF login node the in-cluster service names (`*.nightreport:8080`) are not reachable
  (squid proxy 502); use the public URL above.
- `rubin_nights` is **not** installed in the stack kernel. A checkout exists at
  `~/notebooks/lsst-sims/rubin_nights` (old, 2025-04). The export script reproduces the query
  with plain `httpx` instead of importing it.
- `ts_logging_and_reporting` is not installed on this node either.

## Record schema (as returned 2026-10-17)

`id, site_id, day_obs (int), summary, weather, maintel_summary, auxtel_summary, confluence_url,
user_id, user_agent, date_added, date_sent, is_valid, date_invalidated, parent_id,
observers_crew (list)`.

Mapping to CSV columns: `weather` → `weather_summary`; `maintel_summary` → `simonyi_summary`
(it already contains the "Nighttime:" and "Daytime:" sections); `user_id` → `submitted_by`.

## Decisions

- **obs_tickets is a regex extraction** (`\bOBS-\d+\b`) over `summary`, `weather`,
  `maintel_summary`, `auxtel_summary`, de-duplicated in order of appearance. The API has no
  ticket list. The "Detailed issue report (created in the last 24 h)" section of the email is
  assembled by the digest from Jira and is **not** in the night report record, so this column
  is not the same set as the email's. Decided by Bruno, 2026-10-17.
- `observers_crew` column was added beyond the requested list because it is in the record.
- If several valid reports exist for one night, keep the one with the latest `date_sent`
  (fallback `date_added`). In the 2026-10-17 run there were none.
- Rows are written for nights with no report (`report_found=false`, other fields empty).
- No notebooks: nothing interactive to show. Scripts only.
- **Manual annotations live in `data/manual_notes.csv`**, never edited into the main CSV by
  hand. The export script merges them into the `manual_note` column so a rerun does not lose
  them. All other columns stay verbatim from the API.

## Known data caveats

- 11 nights have no Simonyi report: 20260428 to 20260505, 20260701, 20260702 and 20260720 (the last
  night of the range). Not
  investigated; could be shutdown/maintenance or reports filed under another telescope.
- 20251025 (first night of the range) has a report but an empty `weather` field.
- Text is verbatim from LOVE; expect typos, mixed units, inconsistent formatting.

## Session log

### 2026-10-17 — initial export (Claude, Fable 5.1, via Claude Code on SDF login node)
- Located the client (`rubin_nights.logging_query.NightReportClient`), confirmed the endpoint,
  validated against Bruno's expected weather text for 20260526.
- First attempt failed on an expired token (Jan 2026); Bruno issued a new one.
- Wrote `python/export_nightlog.py`, ran it: 262 rows, 252 found, 10 missing, no duplicates.
- Created README and this file. Nothing committed yet.

### 2026-10-17 — range extended to 20260720 (Claude, Fable 5.1)
- Bruno clarified the intended end date is 20 July 2026 (the prompt said 20260713).
- Reran `export_nightlog.py --end 20260720`: 269 rows, 258 found, 11 missing (20260720 added
  to the missing list), still no duplicate reports. Old 20260713 CSV removed; script default
  `--end` updated to 20260720.

### 2026-10-17 — manual_note column, first commit (Claude, Fable 5.1)
- Bruno: 20260720 was totally lost, the big storm that shut down the observatory started that
  night. Added `data/manual_notes.csv` + `manual_note` column (12th) carrying that note; script
  merges it on export. CSV is ~670 KB, committed to git.
