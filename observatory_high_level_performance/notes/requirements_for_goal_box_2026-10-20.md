# Requirements behind the goal box (collected 2026-10-20)

Context: Phil Marshall, 2026-10-20: "The green box goal was only for early operations, since it
represents the LSST survey start criteria. We need a new, stricter goal box now, derived from the
LSST science requirements." This note collects the primary-source numbers so the new box can be
agreed with Phil. Sources read in full: LPM-17 (SRD, rev. 2018-01-30), RTN-093 (rev. 2025-11-25,
draft), SOTN-004 (rev. 2026-06-27), RTN-122 (Jun 2026). LSE-29 (LSR) and LSE-30 (OSS) are behind
the Docushare login and were NOT re-read; the LSR-REQ-0007 / OSS-REQ-0227/0228 citations in
`ohlp/reference.py` are carried over unverified.

## Image quality

LPM-17 §3.3.3.1 (text under Table 9): "The design specification values reflect an error budget
of 0.35 arcsec (for both telescope and camera, and including static and dynamic errors), which is
added in quadrature. The minimum specification and stretch goal are computed using error budgets
of 0.4 and 0.3 arcsec, respectively. The system contribution to the delivered image quality should
not exceed 0.4 arcsec in any other band." Also: "for the median atmospheric seeing, the system
contribution to the delivered image quality never exceeds 15%" and the requirement holds
"irrespective of the airmass".

| SRD level | system contribution (sDIQ), arcsec | with 0.084″ dome removed in quadrature (iDIQ) |
|---|---|---|
| stretch | 0.30 | 0.288 |
| **design** | **0.35** | **0.340** |
| minimum | 0.40 | 0.391 (the current "LSST = 1" star y, Phil's 0.39) |
| RTN-093 survey start | 0.45 | 0.442 (current green box top) |

LPM-17 Table 10 (system budget at airmass 2, SXE): design 0.52, minimum 0.59, stretch 0.45.
Table 9 (delivered seeing medians for fiducial atmosphere 0.44/0.60/0.80″): design 0.56/0.69/0.87,
minimum 0.59/0.72/0.89, stretch 0.53/0.67/0.85; r and i bands.

The SRD 0.35/0.40 budgets are for "telescope and camera" as a whole; SOTN-004 Table 1 allocates
them as optical figure 0.202, top-end/M1M3 vibration 0.091, tracking drift 0.025, jitter 0.083,
dome seeing 0.084, mirror seeing 0.027, photoelectron diffusion 0.207, total 0.4. So the SRD
number is an sDIQ (dome included) and the dome term must be removed to compare with the iDIQ axis.

RTN-093 §2 on its own Figure 2: "The boundaries of the green box are defined by the minimum design
specification from the SRD (upper) and stretch goals (lower) for the system image quality
contribution ... The LSST specifications are accomplished with nominal speed fE = 1.0 and
sDIQ = 0.4″ in this diagram." The 0.45″ / 0.7 box of Figure 4 and Table 2 is explicitly the
*start* criterion ("the region in this space within which we can confidently start the LSST while
working to maintain and improve performance").

Wrinkle (already in README §4): RTN-093 §3.1 says its 0.45″ "excludes the dome seeing", i.e. it is
iDIQ-like, yet Lynne's notebook removes the dome term again (0.442). Immaterial at the 0.01″ level.

## Survey speed

The SRD has no explicit "survey speed" or fE requirement. The speed side comes from LPM-17 §3.4:
"about 90% of the observing time allocated for the main LSST survey"; Table 22 Asky
18,000 / 15,000 / 20,000 deg² (design / minimum / stretch); Table 23 Nv1 825 / 750 / 1000
(design / minimum / stretch); Table 24 "the median number of visits per field for all bands is 824";
§3.4.0.1 "over 2,500,000 10 deg² visits" in 10 years.

RTN-093 §2 defines fE = fS × fA × fO × SA, "normalized by the corresponding SRD derived design
values", so fE = 1 is the SRD design (Nv1 = 825 over 18,000 deg²). RTN-093 §3.3: "Using the
combined SRD minimum specifications the lowest Normalized Étendue allowed is 0.7"
(750/825 × 15,000/18,000 = 0.76; the document rounds to 0.7). The stretch analogue is
1000/825 × 20,000/18,000 = 1.35. RTN-093 Table 1 "Performance at Start of LSST": fA 0.99,
fS 1.30, fO 1.05, SA 0.75, fE 0.7; "a nominal LSST System Availability of 1.0 means idealized
open shutter time of 71%".

In the figure's x unit (acquired / expected visits, `ohlp.reference.VISIT_RATE`):

| fE | meaning | x |
|---|---|---|
| 0.7 | SRD minimum, RTN-093 start criterion | 0.440 (current box left edge) |
| **1.0** | **SRD design ("LSST = 1" star)** | **0.629** |
| 1.35 | SRD stretch | 0.847 |

## Candidate stricter boxes (to confirm with Phil)

1. **SRD minimum box**: speed ≥ fE 1.0 (x ≥ 0.63) and sDIQ ≤ 0.40″ (iDIQ ≤ 0.39″). Its corner
   is exactly the current star, which is what RTN-093 Figure 2 calls "LSST specifications
   accomplished". Also the level LSR/OSS are believed to carry (0.40″).
2. **SRD design box**: speed ≥ fE 1.0 and sDIQ ≤ 0.35″ (iDIQ ≤ 0.34″). Stricter; the star would
   then sit on the box edge in x but above it in y, unless the star is moved to the design value too.

Open point for Phil: the current star mixes the SRD *minimum* IQ (0.40″) with the SRD *design*
speed (fE = 1). If the new box is "design", the star should probably move to (0.63, 0.34″).

Colour: `rp.CATEGORICAL[2]` purple is already used for the LSST on-sky points in the
`early_ops_vs_lsst` figure, so a purple box would clash there. Nested same-hue (outer start box
at low alpha, inner SRD box darker / outlined, both labelled) avoids that.

## Implemented (2026-10-22)

Instead of replacing the green box, the figure now draws **three nested regions** in the same
green, each at alpha 0.10, so the overlap shades the stricter levels darker (`ohlp.reference.
REQUIREMENT_BOXES`, drawn by `ohlp/static.py` and `ohlp/interactive.py`):

| region | speed (x) | iDIQ top | derived from |
|---|---|---|---|
| survey start | > 0.440 (fE 0.7) | 0.442″ | RTN-093 Table 2 (0.45″ sDIQ, dome removed); the former single box |
| SRD minimum | > 0.440 (fE 0.7) | 0.391″ | RTN-093 §3.3 fE ≥ 0.7; LPM-17 0.40″ minimum, dome removed |
| SRD design | > 0.629 (fE 1.0) | 0.340″ | RTN-093 §2 fE = 1 is the SRD design; LPM-17 0.35″ design, dome removed |

The star is unchanged (0.63, 0.39″) pending Phil's answer on the open point above. The nested
same-hue option was chosen over a purple box because purple is the LSST-points colour in the talk
figure.
