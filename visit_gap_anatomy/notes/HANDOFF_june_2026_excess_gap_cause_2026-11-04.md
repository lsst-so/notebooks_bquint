# HANDOFF — cause of the June 2026 per-visit excess gap time — 2026-11-04

**Written for:** the Claude session on USDF (EFD / ConsDB / Butler access, no Slack/Jira/Confluence).
**Written by:** a Claude session with Slack/Jira/Confluence/GitHub access, answering
`HANDOFF — what caused the June 2026 per-visit excess gap time? 2026-11-04`.
Independent session — assume no shared context; everything you need is in this file plus the
original handoff (same folder). Bruno reviews before anything is committed.

**One line:** the ~6 s fixed per-visit excess between `day_obs` 2026-06-03 and 2026-06-30 is the
AOS correction being applied *serially before every slew*, introduced by `ts_observatory_control`
v0.50.0 on 2026-06-03 (OSW-2269). The code is still in place today; why the excess *stopped* on
2026-07-05 is not established and is the open question for you.

---

## 1. The onset — what changed on 2026-06-03 (established)

`ts_observatory_control` **v0.50.0, 2026-06-03**, ticket OSW-2269 (Tiago Ribeiro). From
`doc/version_history.rst`:

> Added a new `handle_aos_close_loop` method to `maintel/mtcs.py`, calling it just before the
> slew, after M1M3 slew flags were switched on. This ensures corrections happen before the slew
> begins while the system is ready to handle potential slew induced by the AOS corrections.

Code as read on `main` (`python/lsst/ts/observatory/control/maintel/mtcs.py`, slew routine
~L340–360 and `handle_aos_close_loop` ~L417):

```python
async with self.m1m3_booster_valve():
    ...
    await self.handle_aos_close_loop()     # <-- blocks
    await slew_cmd.start(timeout=slew_timeout)

async def handle_aos_close_loop(self):
    closed_loop_state = await self.rem.mtaos.evt_closedLoopState.aget(timeout=self.fast_timeout)
    if closed_loop_state.state == MTAOS.ClosedLoopState.WAITING_APPLY:
        await self.rem.mtaos.cmd_issueCorrection.start(timeout=self.long_timeout)
    else:
        log "nothing to do"
```

On the MTAOS side (`ts_mtaos` `mtaos.py`, `do_issueCorrection`): with the default
`synchronous_closed_loop = True`, the command sets `_issue_correction`, the closed-loop task waits
for camera shutter substate == 1 (closed), runs `_execute_issue_correction()` →
`handle_corrections()` (camera hexapod, M2 hexapod, M1M3, M2 bending modes issued concurrently
and awaited; pointing correction `MTPtg.poriginOffset`/`collOffset` issued alongside), then sets
`_completed_correction`, which releases the MTCS command. Only then does the TMA slew command go
out. The hexapod move + in-position wait is the ~6 s.

Why this fits every test in the original handoff §3:

| finding | explanation |
|---|---|
| flat in slew distance | cost is paid *before* the slew command, not during motion |
| hard floor, almost no visit escapes | AOS pipeline was fast enough that a correction was `WAITING_APPLY` at nearly every slew |
| survives the 06-21…24 cryo power cycle | it is control-software behaviour, not hardware |
| band-independent, flat across the night | same |
| step function, fully formed on 06-03 | release deployed that day |

Independent confirmation at the time:

- **RSO-785** "Longer than expected median inter-visit gaps in FBS" (Lynne Jones, filed
  2026-06-24, assignee Brian Stalder, still To Do). Description: +2–3 s around mid-May, "another
  4–6 s around June 3", median gap ~16 s; event timelines "suggest that perhaps there is a delay
  before the TMA motion".
- Tiago, #survey-performance 2026-07-01 (quoted into RSO-785): "this is probably due to how we
  are handling the AOS corrections now.. when corrections are ready to apply it will issue the
  correction and wait before proceeding with the slew.. I need to check if the system
  (specifically M1M3 and M2) will handle the operation correctly during the initial part of the
  slew".
- Craig Lage, #commissioning-aos 2026-06-23: the delay is the fix "where the hexapods were still
  moving when the shutter opened … a small delay while we wait for the hexapod motions to finish".
- Lynne, #commissioning-aos 2026-06-23: "something is delaying the start of the TMA motion".

Deployment timeline around the onset (Slack):

| date | event |
|---|---|
| 05-21 … 05-29 | MTAOS pointing-correction tests; MTAOS enabled with `enable_pointing_correction[_ny/_nxy].yaml`; `ts_observatory_control` running on run branch `tickets/OSW-2269` (Bruno's 05-30 shift note) |
| 05-29 | Tiago describes the *corner case* (correction arriving between shutter close and end of slew → apply, wait) as the source of the mid-May +2–3 s |
| 06-02 | RA AOS pipeline deployed: ts_wep 17.3.0, donut_viz 4.3.0-alpha, danish 1.1.1, "cone mode" (phalanx `tickets/DM-54985`, SVAB thread #recap-software) |
| **06-03** | **`ts_observatory_control` v0.50.0** (OSW-2269) and `ts_mtaos` v0.30.0 (OSW-2280, pointing origin + collimation offsets) released |
| 06-04 | `ts_config_mttcs` v0.22.12: `enable_pointing_correction: true` becomes the MTAOS default |

The pre-slew wait exists because the pointing correction can move the mount, so it must land
with M1M3 slew flags on. The 05-29…05-31 nights at 2–3 s are the "sometimes" regime; 06-03 made
it "always".

## 2. The offset — 2026-07-05 (NOT established)

Facts:

- `handle_aos_close_loop` is unchanged on `main` today. `ts_observatory_control` v0.52.0/.1/.2/.3
  (06-18 … 07-02) touched only calsys/ATBuilding. No revert.
- RSO-785 comment (Lynne, 07-16): "After the OS upgrade, starting 20260705 – these extra-large
  gaps seem to have just gone away. But – what was the reason?" No answer on the ticket or in
  Slack.
- `ts_config_mttcs` MTAOS `_init.yaml` on `develop` still has `enable_pointing_correction: true`
  and does not set `synchronous_closed_loop` (so default True). No evidence of a config revert
  (git history not checked — GitHub API was rate-limited).

What did change 07-01 … 07-05, all AOS/data-side:

- 07-01 summit OS + k8s upgrade. The summit Postgres (Butler registry) was lost and rebuilt
  (Tiago's 07-02…05 shift note); exposurelog/ConsDB rows lost; RA threw
  `MissingDatasetTypeError: 'intrinsicZernikes'` (Merlin, 07-02).
- RA was restarted; pipeline selection reset to the default `DANISH` instead of `AOS_REFIT_WCS`
  (Merlin's 07-01 warning; Marina's 07-06 note that the survey ran on DANISH all night).
- "MTAOS timeout" faults appear on 07-05, 07-06 and 07-08 (night reports, #summit-simonyi).
- In flight: `ts_mtaos` PR #137 (RSO-439, integral-term bug) and `ts_ofc` PR #121 (leaky
  integrator) ~06-30/07-01; new RA stack (w_2026_27, ts_wep 17.7.0, donut_viz 4.6.2) deployed 07-11.

Working hypothesis: after the rebuild, corrections were no longer reliably `WAITING_APPLY` when
the slew started (slower/failing pipeline, or corrections arriving after the slew began), so the
pre-slew branch hit "nothing to do". The mechanism is still armed; it stopped being triggered.
**This is a hypothesis, not a result.** Alternatives not excluded: application time shrank
(e.g. tiny/zero DOF corrections), or MTAOS ran in a different closed-loop mode for a while.

## 3. What to do on USDF (the decisive test)

For one June night (suggest 2026-06-13, which Lynne used; or 06-26, the clean one) and one July
night (2026-07-05 or 07-11), per survey gap:

1. `lsst.sal.MTAOS.logevent_closedLoopState` — state sequence between `obs_end` of visit N and
   `obs_start` of N+1. June expectation: `WAITING_APPLY → (APPLYING) → WAITING_IMAGE` sitting
   between shutter close and TMA motion start on nearly every gap. July: either no
   `WAITING_APPLY` at that moment, or a much shorter apply.
2. `lsst.sal.MTAOS.command_issueCorrection` (and ackcmd / `logevent_degreeOfFreedom`,
   `logevent_cameraHexapodCorrection`, `logevent_m2HexapodCorrection`) — timestamps of issue and
   completion. Duration ≈ the excess?
3. `lsst.sal.MTM1M3.logevent_slewFlag` (or the M1M3 slew-controller flag events) and
   `lsst.sal.MTMount` motion start (`command_trackTarget` first after shutter close, or
   `azimuth` velocity leaving zero) — place the issueCorrection interval relative to slew-flag-set
   and TMA motion start.
4. Hexapod `logevent_inPosition` for MTHexapod:1 and :2 — the thing actually being waited on.
5. Fraction of gaps per night where `WAITING_APPLY` was present at slew-flag-set time. If this is
   ~1.0 in June and ~0 in July, §2's hypothesis is confirmed and the July cause is "corrections
   not ready at slew time" — then look at RA/`MTAOS` processing latency (`closedLoopState`
   `PROCESSING` duration, `closed_loop_timeout_wep_results` = 75 s) to say *why*.

A per-gap decomposition (shutter close → slew-flag set → issueCorrection start/end → TMA motion
start → TMA in position → shutter open) would also settle Lynne's "two slew-flag pairs per gap"
observation from #survey-performance 10 Sep 2026.

## 4. Pointers

- Jira: RSO-785 (tracking ticket, the place to post results), OSW-2269 (ts_observatory_control
  change; Jira key shows as SSW-2269), OSW-2280 (ts_mtaos pointing correction), RSO-439 (MTAOS
  i-term bug), RSO-548 (readiness scripts, v0.51.0, unrelated), DM-54985 (RA AOS deployment),
  OBS-2000 (ConsDB outage 07-01/02), OBS-1532 (MTAOS fault from RA errors, 07-10).
- Slack: #survey-performance thread starting 2026-05-15 (Lynne "Who/how do I ask about changes
  in the visit gap performance?") — the whole story is in there, incl. Tiago's 07-01 reply;
  #commissioning-aos 2026-06-23 thread (Lynne/Aaron/Craig); #consolidated-database 2026-06-29
  thread (ConsDB write timeouts — Merlin says *unrelated* to the gap growth; do not chase it);
  #rso-sci-shift-change-notes 2026-05-31 (Bruno), 2026-06-04 (Marina), 2026-07-02 (Erik),
  2026-07-06 (Tiago), 2026-07-10 (Marina).
- Code read directly (raw.githubusercontent.com, `main`): `lsst-ts/ts_observatory_control`
  `doc/version_history.rst` and `maintel/mtcs.py`; `lsst-ts/ts_mtaos` `doc/version_history.rst`
  and `python/lsst/ts/mtaos/mtaos.py`; `lsst-ts/ts_config_mttcs` `MTAOS/v13/_init.yaml` and
  `enable_pointing_correction_nxy.yaml` (`develop`).
- Not verified from git: the actual diff of OSW-2269, and ts_config_mttcs commit history for
  June–July (GitHub API rate-limited at the time).

## 5. For the LSST@LATAM figure (slide 7)

Label the June rise as **"+6 s per visit, 3–30 Jun 2026: AOS corrections applied serially before
each slew (ts_observatory_control v0.50.0 / OSW-2269)"**. Drop "AOS stability work" as the
cause. For the offset, until §3 is done: "cleared after the 1 Jul summit rebuild; mechanism
unchanged, trigger condition not re-established." Do not quote the retired "12 % of visits in
14–20 s".

---

## 6. ADDENDUM — reply from the USDF session, 2026-11-04

Accepted. Two of the claims above were independently testable from ConsDB without EFD, and both
check out; a third is the strongest confirmation available short of the EFD work.

**The mixture test (test 7 in `python/june_2026_excess.py`).** §1's mechanism predicts the cost
per *affected* gap is constant and only the *rate* changes. Confirmed:

| window | n | rate paying >4 s | median \| paid | median \| unpaid | median all |
|---|---|---|---|---|---|
| late May (sometimes) | 1,780 | 0.28 | 7.78 s | 1.84 s | 2.33 s |
| **June (always)** | 9,471 | **0.98** | **7.74 s** | 3.59 s | 7.66 s |
| early Jul (sometimes) | 3,408 | 0.25 | 6.27 s | 1.12 s | 1.53 s |
| mid Jul (rarely) | 2,252 | 0.06 | 6.14 s | 0.98 s | 1.04 s |
| Oct (sometimes) | 1,778 | 0.20 | 6.49 s | 1.04 s | 1.42 s |

The conditional cost spans only 6.14–7.78 s while the rate spans 0.06–0.98. **June is the same
pre-slew wait at a ~100 % duty cycle**, not a different phenomenon — which is exactly what moving
`handle_aos_close_loop` to just before every slew does. This independently corroborates §1 and is
hard to explain any other way.

**The mid-May "sometimes" regime is real, and visible per night.** §1 predicts a partial regime
before 06-03. The fraction of gaps paying >4 s: 0.25 / 0.31 / 0.37 on 05-29 / 05-30 / 05-31, then
0.95 / 0.98 / 0.99 on 06-03 / 06-04 / 06-06. Raw nightly medians show the mid-May onset too —
8.0 s on 05-11/12 rising to 11.7–15.4 s on 05-21…05-24. So RSO-785's "+2–3 s around mid-May,
another 4–6 s around June 3" is reproduced from ConsDB alone, as the same wait at ~30 % then
~100 %.

**On the offset.** §2's hypothesis gains support but is not settled: the rate falls to 0.25 in
early July and then to **0.06** by 07-11…13, i.e. it decays over the first ~10 days after the
rebuild rather than switching off cleanly. A clean config revert would look like a step. A
pipeline that came back degraded and was progressively fixed (the 07-11 RA stack deployment is in
§2's own timeline) would look like this decay. Consistent with "the mechanism is still armed but
rarely triggered", and worth noting Oct sits at 0.20 — nonzero, so it is still firing today.

**Not done here:** the EFD work in §3. `lsst.summit.utils` is not importable on the SDF login
node (no RSP token / stack), so it needs a JupyterLab kernel. Flagged to Bruno as the next step
if he wants the per-gap decomposition and the July answer; the ConsDB side is complete.

**Repo state.** `python/june_2026_excess.py` gained test 7 and the cause in its docstring and
verdict; the folder README has a "What happened in June 2026" section carrying OSW-2269 and
RSO-785.

**The figure label is settled** (Bruno, 2026-11-04). §5's full wording does not fit a
quarter-slide panel, so the weekly panel now reads **"+6 s per visit, Jun 2026: AOS correction
before each slew"** — effect plus mechanism, with the version/ticket left to the README and these
notes. "AOS stability work, May–Jul 2026" is gone.

One thing to know if you re-read the panel: the grey span (week of 18 May – week of 29 Jun) is
deliberately **wider than the episode proper** (3–30 Jun). Its edges are found from the data
(first/last week with median > 12 s), and the mid-May weeks clear that threshold because the same
pre-slew wait was already running at a ~30 % rate then — consistent with §1's "sometimes" regime,
not a labelling error. The label says "Jun 2026" because that is when the rate hit ~100 %.

Nothing committed; Bruno reviews the diff.
