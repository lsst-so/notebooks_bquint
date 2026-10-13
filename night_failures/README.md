# Night failures — CSC faults and script failures per night

Ticket: [RSO-544](https://rubinobs.atlassian.net/browse/RSO-544)

Counts CSC faults and script failures per night (sun altitude ≤ −12° at Cerro Pachón)
from the EFD, attributing script failures to nearby CSC faults.

- **Status:** WIP. The single-night MVP works; the multi-month trending notebook has not
  been run end-to-end in the stack kernel yet (see `notes/`).
- `notebooks/count_night_failures.ipynb` — single-night MVP.
- `notebooks/count_night_failures_trending.ipynb` — multi-month trending version.
- `plots/failures_and_faults_per_night_20260101_20260515.png`
- `notes/SESSION_NOTES_night_failures_trending.md` — design notes and handoff.
