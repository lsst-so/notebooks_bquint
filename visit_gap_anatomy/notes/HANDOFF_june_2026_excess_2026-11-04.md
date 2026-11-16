# HANDOFF — what caused the June 2026 per-visit excess gap time? 2026-11-04

**Written for:** a Claude session (or person) with access to Rubin **Slack, Jira and Confluence**,
which this session does not have. Independent session — assume no shared context with the work
below; everything you need is in this file.

**The ask in one line:** between `day_obs` **2026-06-03 and 2026-06-30**, every Simonyi survey
visit paid a roughly **fixed ~6 s of extra dead time** that the kinematic slew model cannot
explain. I have characterised it tightly from ConsDB and ruled out the obvious mechanisms. I
cannot identify *what changed*, because that needs config/deployment history and Slack/Jira.
**Please find the change.**

Nothing here needs to be taken on trust: `visit_gap_anatomy/python/june_2026_excess.py` in
`lsst-so/notebooks_bquint` (branch `u/bquint/latam-2026-figures`) prints every number below.

---

## 1. What is measured

- **Gap** = `obs_start` of a visit − `obs_end` of the previous visit, reset each `day_obs`.
  ConsDB `cdb_lsstcam.visit1`. Readout is inside the visit, not the gap.
- **Survey visits only** — both visits of a pair in BLOCK-407/408/416/417/419/421. Engineering,
  AOS and focus visits excluded, and the gaps either side of them.
- **`slew_model`** = the kinematic slew-time prediction per gap (TMA/dome/rotator
  velocity+acceleration model), from `night_budget/data/visits_slew_*.parquet`. It covers
  **2026-05-29 → 2026-10-30 only**.
- **`excess` = `gap − slew_model`** — dead time the kinematic model does *not* account for.

## 2. The finding: a step function with hard edges

Median `excess` per night. The episode and non-episode ranges **do not overlap** — every one of
the 15 June observing nights is worse than every other night in the cache:

| window | nights | median excess |
|---|---|---|
| 2026-05-29 … 05-31 | 3 | 2.13 – 3.38 s |
| **2026-06-03 … 06-30** | **15** | **6.13 – 9.06 s** |
| 2026-07-05 … 07-13 | 8 | 0.97 – 1.59 s |
| 2026-10-27 … 10-30 | 3 | 0.78 – 3.14 s |

It appears **fully formed on the first visit of 2026-06-03** (first dozen excesses that night:
6.4, 9.4, 7.4, 20.5, 6.4, 24.3, 8.6, 6.9, 4.6, 3.8, 6.9, 5.5 s — against 2.4, 2.7, 2.4, 2.6 … on
2026-05-31). Not a ramp.

### Independent of the slew model

Dropping `slew_model` entirely and using **raw** gaps over the full nine-month window
(Oct 2025 – Jul 2026, n = 61,681) reproduces it, so it is not a model artefact nor an artefact of
the short "before" window:

| month | n | p5 gap | median gap |
|---|---|---|---|
| 2025-10 … 2026-05 | 46,807 | 3.5 – 7.5 s | 7.5 – 10.8 s |
| **2026-06** | **9,313** | **11.14 s** | **14.79 s** |
| 2026-07 | 5,561 | 6.28 s | 8.17 s |

Ranking all nine months of nights by their **5th-percentile** gap: **15 of the top 20 nights are
in June 2026** — and June 2026 has exactly 15 observing nights with ≥100 survey gaps. Every single
June night is in the worst 20 of nine months.

## 3. What it is *not* (please don't re-derive these)

| hypothesis | verdict | evidence |
|---|---|---|
| A second slew/settle ("late AOS correction with a pointing offset") | **ruled out** | excess is **flat in slew distance**: 7.73 s for slews <1°, 7.66 s at 2–3°, 7.70 s at 6–10°, 7.50 s >10°. A slew or settle cost scales with distance. `slew_distance` itself is unchanged (3.01° vs 3.03°). |
| A subpopulation of affected visits (the old "12 % of visits in a 14–20 s band") | **ruled out** | there is a **hard floor**. June's p1 = 3.60 s, p5 = 4.65 s, vs p1 = 0.13 s, p5 = 0.33 s in July. Almost no visit escaped. The whole distribution is displaced ~6 s; it is not bimodal. |
| Reduced TMA velocity limits | **ruled out** | `tma_ax_maxv`/`tma_alt_maxv` give the real limits. **Only 2026-06-11** ran reduced (0.5 vs 2.0 °/s) — and there `slew_model` itself rose to 13.23 s, correctly absorbing it. **14 of 15** episode nights ran at full 2.0 °/s and still show 6.13–8.92 s. |
| Thermal / drifting calibration | **ruled out** | flat across the night (early/mid/late thirds: 7.65 / 7.75 / 7.61 s), and it **survived the four-night full stop** for the camera cryo outage (2026-06-21…24): 2026-06-19 = 8.24 s → 2026-06-25 = 7.81 s. A power cycle did not clear it. |
| Filter/band dependent | **ruled out** | all six bands 7.34–8.64 s. |
| Weather | **ruled out** | June was heavily cloud-affected, but weather removes *nights*; it does not add a constant per-visit floor on the nights that did observe. The best June nights (06-26: "~11.5 h no faults, seeing 0.98″"; 06-29, first LSST night) still show 6.13 and 8.12 s. |

## 4. The lead: both edges fall on multi-night closures

From `simonyi_time_loss/data/raw/nightlog_sweep_2026-0{6,7}.md` (night reports) and
`tailgate_sweep_2026-0{6,7}.md` (morning tailgate notes), already in the repo:

- **Onset.** Last clean night 2026-05-31. Then **2026-06-01** (planned: camera-vacuum RGA, TMA
  locked at horizon, no observing) and **2026-06-02** (whole night lost to TMA/MTMount faults,
  dome closed 03:55 UTC). First night back on sky = **2026-06-03**, already at 6.38 s.
- **Offset.** Last affected night 2026-06-30. Then **2026-07-01 … 07-04**: OS-update recovery,
  OSS faults, M1M3 FA211, the **OBS-2000 ConsDB/data-ingestion blocker** ("a blocker for any
  on-sky observing"), TMA main-cabinet sensor errors, **FRACAS-401**. Night reports for 07-01 and
  07-02 are *missing* because of the database outage. First night back = **2026-07-05**
  ("Flawless FBS night"), at 1.53 s.

A fixed per-visit cost that (a) appears across one maintenance gap, (b) is immune to a four-night
power cycle mid-episode, and (c) vanishes across the next maintenance gap, looks like a
**configuration or software change** — something adding a constant wait per visit — rather than a
mechanical fault or AOS convergence problem.

**Caveat, stated plainly:** (c) is suggestive, not proof. The July 1–4 window changed several
things at once (OS updates *and* a ConsDB outage *and* TMA cabinet work), so "a config change was
reverted there" is a hypothesis, not a result. Please treat §4 as the lead and §3 as the findings.

## 5. What I'd like you to look for

1. **Config / deployment history around both edges.** Any change to `ts_config_ocs`,
   `ts_config_mttcs`, `ts_config_attcs`, the scheduler (FBS) configuration or MTAOS config merged
   or deployed **2026-06-01…06-03**, and anything **reverted or redeployed 2026-07-01…07-05**.
   Cycle/XML deployments in that window. A changed timeout, settle-time, `wait` parameter,
   closed-loop cadence, or a per-visit script step would all fit.
2. **Jira.** OBS / FRACAS / DM tickets June–July 2026 mentioning visit overhead, gap time, slew
   settle time, scheduler script timing, or a per-visit delay. Known keys in the window, for
   thread-pulling: **OBS-1987** (homing/MTMount encoders), **OBS-1994** (MTScheduler
   TimeoutError, 06-29), **OBS-2000** (ConsDB blocker, 07-01/02), **FRACAS-401** (OSS/TMA sensor,
   07-03/04), OBS-1897, OBS-1954, OBS-1002.
3. **Slack.** `#survey-performance`, `#rubinobs-summit-announce`, `#rubinobs-sitcom` for June–July
   2026 discussion of visit overhead / gap regression / slew timing. Also worth checking:
   did anyone *notice* at the time? If the fix in early July was deliberate, someone said so.
4. **If you have EFD access**, the decisive test: per-gap M1M3/TMA **slew-flag timestamps** and
   `lsst.sal.Script` / MTScheduler script timings for a June night vs a July night. That would
   localise the 6 s inside the gap — slew vs settle vs scheduler latency vs AOS wait — which
   ConsDB cannot separate. Tiago Ribeiro (#survey-performance, 10 Sep 2026) reported two
   slew-flag set/clear pairs per gap; Lynne Jones was redoing the sub-timings.

> **ANSWERED, 2026-11-04.** The cause is `ts_observatory_control` v0.50.0 (OSW-2269, 2026-06-03):
> AOS corrections are applied serially *before every slew*, so the slew blocks until the hexapod /
> M1M3 / M2 corrections finish. Ticket **RSO-785**. The reply, with the deployment timeline and the
> remaining EFD test for why it stopped on 2026-07-05, is in
> `HANDOFF_june_2026_excess_gap_cause_2026-11-04.md` (same folder). §5 and §6 below are superseded:
> the figure label is now "+6 s per visit, Jun 2026: AOS correction before each slew". This file is
> kept as the record of what was asked and what had been ruled out from ConsDB alone.

## 6. What this changes in the repo (context, not a request)

`visit_gap_anatomy/` is a figure folder for the LSST@LATAM 2026 talk (slide 7). Earlier versions
shaded 14–20 s as a "second settle" population; that was retired on 2026-11-04
(`python/check_late_correction.py`, and a section in the folder README) because the band was
hand-set and §3 above refutes it. The weekly-trend panel currently labels the rise **"AOS
stability work, May–Jul 2026"**, which on this evidence is itself an unsupported *causal* claim —
flagged to Bruno, not yet changed. **Do not quote the retired "12 % of visits in 14–20 s".**

If you identify the change, the honest label becomes something like "+6 s per visit, Jun 2026"
plus the actual cause; until then the figure should describe *when*, not *why*.

---

## Reproducing

```bash
# branch u/bquint/latam-2026-figures of lsst-so/notebooks_bquint, on USDF
python visit_gap_anatomy/python/june_2026_excess.py      # §2 and §3, all six tests
python visit_gap_anatomy/python/check_late_correction.py # the earlier band tests
```

Inputs: `visit_gap_anatomy/data/visit1_20251026_20260714.parquet` (ConsDB `visit1`, in-repo) and
`night_budget/data/visits_slew_*.parquet` (slew model, May–Oct 2026; outside the folder and
read-only — tests 1–5 skip without it, test 6 still runs).

**Uncommitted** as of writing; Bruno reviews before commit.
