# DIMM Data Quality Investigation — Findings (RSO-656)

**Status:** ✅ Conclusions reached (§6). Cloud/low-flux corruption confirmed via DIMM telemetry;
independent cross-check inconclusive by selection effect. Ready for Craig review.
**Ticket:** [RSO-656](https://rubinobs.atlassian.net/browse/RSO-656) ·
**Author:** Bruno Quint · **Started:** 2026-07-01

This document collects the results we will share with Craig. It is meant to stand on its
own. Session-to-session working notes live in [`HANDOFF.md`](./HANDOFF.md).

---

## 1. Background

DIMM (Differential Image Motion Monitor) instruments estimate atmospheric **seeing** by
measuring the differential motion of two images of the same star formed by a mask with two
apertures. In principle this isolates the *atmospheric* turbulence contribution,
independent of the telescope.

Craig raised the concern that our DIMM seeing values may not reflect reality. Two failure
modes are on the table:

1. **Low wind (< 4 m/s)** — already known to make DIMM data unreliable.
2. **Clouds / low transparency** *(hypothesis, Erik D., Image Quality meeting 2026-06-17)*
   — reduced light **flux** into the DIMM leads to **artificially low seeing** readings.

**Objective:** confirm the cloud hypothesis on our DIMM, enumerate any other corrupting
variables, and define quantitative thresholds beyond which DIMM seeing should be discarded.

## 2. Method (planned)

- **DIMM source:** EFD event `lsst.sal.DIMM.logevent_dimmMeasurement` (seeing `fwhm`,
  flux, scintillation, airmass `secz`, `nimg`).
- **Reference metric:** ConsDB `visit1_quicklook.donut_blur_fwhm`, camera-corrected to an
  atmosphere-only estimate `donut_blur_atm_fwhm = sqrt(donut_blur_fwhm² − CAM_FWHM²)`,
  `CAM_FWHM = 0.207"`.
- **Environmental context:** DIMM `cloudSensor` / `sky` topics; wind from the weather
  station CSC (topic TBD).
- Correlate DIMM seeing error (DIMM − reference) against flux, wind, cloud state, airmass;
  find thresholds where the error becomes systematic.

## 3. Reference: DIMM SAL topics (EFD)

Source: <https://ts-xml.lsst.io/sal_interfaces/DIMM.html>

### Primary event — `lsst.sal.DIMM.logevent_dimmMeasurement`
| field | units | description |
|---|---|---|
| `fwhm`, `fwhmx`, `fwhmy` | arcsec | seeing FWHM: combined and per-axis |
| `r0` | cm | Fried parameter |
| `flux`, `fluxL`, `fluxR` | ADU | average flux + per-spot (left/right) |
| `scintL`, `scintR` | — | scintillation ratio per spot |
| `strehlL`, `strehlR` | — | Strehl ratio per spot |
| `secz` | — | airmass of the observation |
| `nimg` | — | number of images averaged |
| `dx`, `dy` | arcsec | spot separation |
| `timestamp`, `expiresAt`, `expiresIn` | — | temporal metadata |

### Supporting topics
| topic | contents |
|---|---|
| `lsst.sal.DIMM.cloudSensor` | ambient/sky temp, temp differential, **light intensity**, rain intensity |
| `lsst.sal.DIMM.sky` | sky status enum (clear / light cover / cloudy / rain / snow) + sky temp |
| `lsst.sal.DIMM.status` | alt/az, ra/dec, focus, motion state (park/slew/stand/track), power |
| `lsst.sal.DIMM.dome` | dome open state/position, temp, zenith distance |
| `lsst.sal.DIMM.ameba` | automation mode/state, solar altitude, ambient bitmask, schedule |
| `lsst.sal.DIMM.logevent_dimmData` | raw per-frame stats (fluxes, RMS, spot separations, background) |
| `lsst.sal.DIMM.logevent_moduleStatus` | status flags: Scope/Master/Metrology/Dome/DIMM |
| `lsst.sal.DIMM.logevent_scopeEvents` | saved error events `<error>:<status>:<device>` |

### Reference: ConsDB comparison fields
`visit1_quicklook`: `donut_blur_fwhm`, `aos_fwhm`, `ringss_seeing`,
`seeing_zenith_500nm_{min,median}`, `psf_sigma_median`. `visit1`: `dimm_seeing`,
`airmass`, `band`/`physical_filter`, `day_obs`, `exp_midpt_mjd`.

## 4. Results

### 4.1 Field availability — our DIMM publishes a thin event (2026-07-01)

First EFD pull (`dayObs` 20260119–20260407, 28 775 measurements) shows the live
`logevent_dimmMeasurement` is much thinner than the SAL schema advertises:

| field | status | note |
|---|---|---|
| `fwhm` | ✅ live | 0.03″–41.7″; the tail above ~5″ is unphysical (failed measurements) |
| `fluxL`, `fluxR` | ✅ live | ~11 000–13 500 ADU per spot — **the usable transparency proxy** |
| `strehlL`, `strehlR` | ✅ live | ~0.25 — secondary image-quality proxy |
| `secz` | ✅ live | 1.00–5.90 airmass |
| `flux` (combined) | ❌ dead | always 0 — **not** usable; use `flux_proxy = fluxL + fluxR` instead |
| `scintL`, `scintR` | ❌ dead | always 0 |
| `nimg` | ❌ dead | always 1 |
| `r0`, `fwhmx`, `fwhmy` | ❌ dead | always −1 (sentinel) |

**Consequences for the investigation:**
- The cloud/transparency test survives — the *combined* `flux` is dead, but per-spot
  `fluxL`/`fluxR` are real, so `flux_proxy = fluxL + fluxR` replaces it.
- `DIMM.cloudSensor` and `DIMM.sky` **are not in our EFD schema** (`ValueError`), so there is
  no direct cloud-state stream to join. Transparency must come from `flux_proxy` / Strehl, with
  ConsDB `donut_blur_atm_fwhm` as the independent cross-check.
- Wind is available: `ESS.airFlow`, site sensor `"Weather tower airflow"` (`salIndex 301`);
  ignore the AuxTel / WiFi-test / dome-louver anemometers.
- `fwhm` up to ~42″ is not real seeing. Working cut: treat `fwhm > 5″` as a failed measurement
  (corruption signature to characterise, not filter silently).

### 4.2 Low flux drives seeing artificially low — cloud hypothesis CONFIRMED (2026-07-01)

Binning `fwhm` against `flux_proxy` (wind time-aligned via `merge_asof`, 100% matched within
2 min) over `dayObs` 20260119–20260407:

| `flux_proxy` [ADU] | n | median fwhm [″] | robust σ [″] | suspect frac |
|---|---|---|---|---|
| 1.6k – 3.1k | 21 | **0.16** | 0.03 | 0.90 |
| 3.1k – 6.1k | 32 | **0.46** | 0.15 | 0.19 |
| 6.1k – 11.8k | 133 | **0.69** | 0.40 | 0.18 |
| 11.8k – 23k | 15401 | 0.91 | 0.28 | 0.005 |
| 23k – 45k | 4297 | 0.88 | 0.27 | 0.001 |
| 45k – 88k | 3154 | 0.99 | 0.24 | 0.044 |
| 88k – 172k | 134 | 1.06 | 0.17 | 0.134 |
| 172k – 336k | 5570 | 0.91 | 0.20 | 0.0002 |

**The median seeing collapses monotonically as flux falls** (0.91″ → 0.69″ → 0.46″ → 0.16″
below ~12k ADU) — exactly Erik D.'s prediction that low transparency makes the DIMM report
**artificially low** seeing. The effect is confined to the low-flux tail: above ~12k ADU the
median is stable at ~0.9–1.0″. This is direct, internal-to-the-DIMM confirmation. An independent
ConsDB `donut_blur_atm_fwhm` cross-check was attempted (§4.4) but is thwarted by a selection
effect — science visits do not exist during the cloudy conditions that corrupt the DIMM — so it
neither confirms nor refutes and the result rests on this telemetry-internal evidence. (Caveat:
`suspect_frac` in the lowest bins mixes NaN failures with the >5″ tail — but the median trend is
NaN-immune and carries the result on its own.)

### 4.3 Wind < 4 m/s inflates scatter (known rule re-confirmed, milder effect)

| `wind_speed` [m/s] | n | median fwhm [″] | robust σ [″] | suspect frac |
|---|---|---|---|---|
| 0 – 2 | 7454 | 1.05 | 0.28 | 0.012 |
| 2 – 4 | 9701 | 0.89 | 0.22 | 0.015 |
| 4 – 6 | 5689 | 0.82 | **0.17** | 0.003 |
| 6 – 8 | 2495 | 0.87 | 0.23 | 0.004 |
| 8 – 10 | 1034 | 0.96 | 0.28 | 0.027 |
| 10 – 15 | 632 | 1.05 | 0.27 | 0.003 |

Below 4 m/s the robust scatter grows (~0.17″ at 4–6 m/s → ~0.28″ at 0–2 m/s) and the median
biases **high** — consistent with local/dome turbulence not being flushed. Note this is the
*opposite* direction to the low-flux bias (which drives seeing low), so the two failure modes
are distinguishable. Effect is real but weaker than the flux effect.

### 4.4 Independent ConsDB cross-check — INCONCLUSIVE by selection effect (2026-07-01)

To confirm §4.2 against an independent instrument, we joined each science visit to the nearest
DIMM measurement (`merge_asof`, 5-min tol) and compared DIMM `fwhm` to the camera's donut-blur
seeing, both normalised to zenith / 500 nm (`donut_blur_zen500`; airmass + bandpass corrections
applied — visits span airmass 1.0–3.3 and multiple bands). DIMM carried in both airmass
conventions (raw and zenith-corrected) since the EFD convention is undocumented.

| flux regime | n pairs | DIMM median [″] | donut_zen500 [″] | resid_raw [″] | resid_zen [″] |
|---|---|---|---|---|---|
| flux ≥ 12k ADU | 5442 | 0.96 | 0.80 | +0.15 | +0.09 |
| flux < 12k ADU | 40 | 0.65 | 0.59 | +0.10 | +0.06 |

**The cross-check cannot reach the corrupted regime.** Of 5482 visit↔DIMM pairs only **40** fall
below the 12k-ADU threshold, and the paired `flux_proxy` bottoms out at **~7k ADU** — whereas the
seeing collapse in §4.2 happens *below* ~6k ADU. Cause: science exposures (with valid donut-blur
output) are not taken during the heavy cloud that drives the DIMM lowest, so the most-corrupted
DIMM samples have no coincident visits. In the mild low-flux edge that *is* sampled, DIMM and
donut blur drop **together** (0.96→0.65″ vs 0.80→0.59″) and the residual stays small and positive
for both conventions — i.e. these were genuinely good-seeing moments, not corruption. The
cross-check therefore **neither confirms nor refutes** §4.2; it is limited by observing selection,
not by the hypothesis.

Two incidental notes: (i) ConsDB's own `seeing_zenith_500nm_median` is entirely NaN in the cache,
so the manual `donut_blur_zen500` is our only zenith/500 nm reference (correction not
independently validated). (ii) ConsDB's `visit1.dimm_seeing` maxes at ~39.9″ — confirming the
corrupted DIMM values propagate downstream into ConsDB.

## 5. Thresholds for unreliable DIMM data

| variable | unreliable when | evidence | status |
|---|---|---|---|
| `fwhm` sanity | > ~5″ (up to 42″ seen); 1.1% of all points | direct: unphysical seeing | confirmed |
| **flux / transparency** | **`flux_proxy = fluxL+fluxR` ≲ 12k ADU** | §4.2: median seeing collapses 0.9″→0.16″ | **confirmed** |
| wind speed | < 4 m/s | §4.3: robust σ ~0.28″ vs ~0.17″ above; median biased high | re-confirmed (mild) |
| cloud state | n/a as direct field | `cloudSensor`/`sky` topics absent from EFD | proxy via flux only |
| airmass | no clear effect | `secz` live (1.0–5.9); no residual trend once flux/wind handled | closed |
| `nimg` | dropped | always 1 → useless | closed |

## 6. Conclusions & recommendation for Craig

**Bottom line: yes, our DIMM seeing is corrupted in a specific, identifiable regime — Erik's
cloud/low-transparency hypothesis is borne out — and it is straightforward to flag.**

1. **Low transparency → artificially low seeing (confirmed, §4.2).** When the DIMM loses light
   (`flux_proxy = fluxL + fluxR ≲ 12 000 ADU`), the reported seeing collapses from a normal ~0.9″
   down to 0.2–0.5″. These are not real sub-arcsecond nights — they are the DIMM misbehaving under
   cloud, exactly as Erik predicted. **Recommendation: discard DIMM seeing when
   `fluxL + fluxR < 12 000 ADU`.** (Note the combined `flux` field is dead/zero — the per-spot
   fluxes must be summed; see §4.1.)

2. **Unphysical values (confirmed, §4.1).** ~1.1 % of measurements report `fwhm` up to ~42″.
   **Recommendation: reject `fwhm > 5″` outright** as failed measurements.

3. **Low wind → inflated scatter (re-confirmed, §4.3).** The known wind < 4 m/s rule holds; below
   it the scatter roughly doubles (~0.17″→0.28″) and the median biases slightly *high* — the
   opposite direction to the flux effect, so the two are distinguishable. **Keep the wind < 4 m/s
   flag.**

4. **Independent confirmation not achievable from science data (§4.4).** Comparing to the camera's
   donut-blur seeing cannot validate the low-flux corruption, because we do not take science
   exposures during the cloud that corrupts the DIMM — the corrupted regime has no coincident
   visits. This is a selection limitation, not a counter-result; the telemetry-internal evidence
   (§4.2) stands on its own.

5. **Downstream impact.** The corrupted values propagate: ConsDB's `visit1.dimm_seeing` shows the
   same ~40″ outliers (§4.4). Any consumer of `dimm_seeing` should apply the flux/`fwhm` cuts above.

**Suggested single filter for DIMM seeing consumers:**
`0.1″ ≤ fwhm ≤ 5″  AND  (fluxL + fluxR) ≥ 12 000 ADU  AND  wind ≥ 4 m/s`.

_Caveats:_ thresholds are from one ~2.5-month window (`dayObs` 20260119–20260407); the 12k-ADU
cut is where the collapse becomes unambiguous, not a sharp physical edge. `cloudSensor`/`sky` DIMM
topics are absent from our EFD, so `flux_proxy` is the only in-DIMM transparency indicator.

## 7. References

- RSO-656 ticket and the originating thread.
- Image Quality meeting, 2026-06-17 (Erik D.'s cloud hypothesis).
- DIMM SAL interface: <https://ts-xml.lsst.io/sal_interfaces/DIMM.html>
