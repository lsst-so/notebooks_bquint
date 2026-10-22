"""Reference values for the survey speed vs. image quality figure, with sources.

Nothing in this file is computed from data. Every number carries the document,
commit or message it was taken from; the README repeats the list in prose.
The default values reproduce the "LSST = 1" star and the green goal region of
Lynne Jones's ``diq_vs_visit_rate.ipynb`` (lsst/sp_notebooks, commit 66e1baa,
cells 8 and 10). Change a value here, never in the plotting code.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

# --------------------------------------------------------------------------- #
# Survey programs and dates                                                   #
# --------------------------------------------------------------------------- #

#: Science programs counted as survey visits. Same list as
#: ``rubin_nights.reference_values.SCIENCE_PROGRAMS`` (0.18.2), which is what
#: diq_vs_visit_rate.ipynb uses (``science_program in SCIENCE_PROGRAMS``).
SCIENCE_PROGRAMS: tuple[str, ...] = (
    "BLOCK-365",
    "BLOCK-407",
    "BLOCK-408",
    "BLOCK-416",
    "BLOCK-417",
    "BLOCK-419",
    "BLOCK-421",
)

#: First night of Early Operations survey visits in ConsDB (LSSTCam, BLOCK-407).
DAY_OBS_EARLY_OPS_START: int = 20251024

#: First night of the 10-year LSST. Source: sp_notebooks weekly_metrics.ipynb
#: ``season_start_day_obs = 20260629`` and the community post
#: "2026-07-10 Early Operations Update: Start of LSST".
DAY_OBS_LSST_START: int = 20260629

#: Last night with LSSTCam visits in ConsDB before the storm (checked
#: 2026-10-14 on the USDF Postgres replica). Nights after this are off sky.
DAY_OBS_LAST_BEFORE_STORM: int = 20260714

#: Label written on the plot across the gap. Source: Bruno Quint, 2026-10-14.
STORM_GAP_LABEL: str = "storm, off sky"

#: Periods that contain the start of the storm and are therefore truncated
#: (FY26 Q4 = Jul-Sep 2026; Jul 2026). Their "all nights" speed counts the
#: closed storm nights as zero visits.
STORM_PERIOD_QUARTER: int = 264
STORM_PERIOD_MONTH: int = 202607

#: Months with fewer nights than this are flagged ("faded") but never dropped.
MIN_NIGHTS_PER_MONTH: int = 5

# --------------------------------------------------------------------------- #
# Image quality                                                                #
# --------------------------------------------------------------------------- #

#: Camera (photoelectron diffusion) FWHM contribution, arcsec. Same constant as
#: ``rubin_nights.rubin_scheduler_addons.CAM_FWHM``; SOTN-004 Table
#: ``tab:diq_budget`` row "photoelectron diffusion".
CAM_FWHM: float = 0.207

#: Dome seeing budget, arcsec. SOTN-004 Table ``tab:diq_budget``;
#: diq_vs_visit_rate.ipynb cell 10 ``dome_fwhm = 0.084``.
DOME_FWHM_BUDGET: float = 0.084

#: System image-quality contribution requirement, arcsec: LSE-29 LSR-REQ-0007
#: (SysIm_0 = 0.40), LSE-30 OSS-REQ-0227/0228, LPM-17 section 3.3.3.1 minimum.
SYS_IQ_REQUIREMENT: float = 0.40

#: Survey start criterion for the system contribution, arcsec, excluding dome
#: seeing: RTN-093 "Survey Start Criteria" table item 1 (sDIQ), reused by RTN-122.
SYS_IQ_START_CRITERION: float = 0.45

#: Lynne's "goal" iDIQ: the 0.40 requirement with the dome term removed in
#: quadrature (0.39, proposed by Phil Marshall, #mtg-summit-kpi, 2026-02-12).
#: Hard-coded as ``idiq = 0.39`` in diq_vs_visit_rate.ipynb cell 10.
IDIQ_GOAL: float = 0.39

#: Lynne's "minimum acceptable" iDIQ: RTN-093's 0.45 with the dome term removed
#: in quadrature. diq_vs_visit_rate.ipynb cell 10 ``min_idiq``.
IDIQ_MIN: float = float(np.sqrt(SYS_IQ_START_CRITERION**2 - DOME_FWHM_BUDGET**2))

#: Fiducial atmospheric seeing at 500 nm, zenith, arcsec. diq_vs_visit_rate.ipynb
#: cell 10 ``fiducial_atm = 0.7`` (SOTN-004 quotes 0.72 for the baseline sims).
FIDUCIAL_ATM_FWHM: float = 0.7

#: Brian Stalder's measured system contribution (sDIQ), arcsec, ROST 21 Sep 2026
#: slide 2 ("0.55-0.60 arcsec, against a 0.40 budget"). It is the quadrature sum
#: of the "measured" rows of SOTN-004 ``tab:diq_budget`` (optical figure 0.4,
#: tracking drift 0.1, jitter 0.02, dome seeing 0.3-0.4, diffusion 0.207) and
#: therefore INCLUDES dome seeing and tracking, which ``idiq_aos_cam`` does not.
#: Terminology (Phil Marshall, 2026-10-20): iDIQ = instrument contribution to the
#: delivered image quality, excluding dome/tube seeing; sDIQ = system contribution,
#: everything except the atmosphere, so including dome/tube seeing. The y axis of
#: the figure is iDIQ; this band is sDIQ. Drawn as a separate, toggleable band;
#: not comparable one-to-one with the box.
SYS_IQ_MEASURED_ROST: tuple[float, float] = (0.55, 0.60)

#: SRD system image-quality budgets (sDIQ, arcsec), LPM-17 section 3.3.3.1,
#: text under Table 9: design 0.35, minimum 0.40, stretch 0.30. All include
#: the dome term (SOTN-004 Table 1 allocates 0.084 of the 0.40 to dome seeing),
#: so each is reduced in quadrature by ``DOME_FWHM_BUDGET`` before it is drawn
#: on the iDIQ axis. Collected in notes/requirements_for_goal_box_2026-10-20.md.
SYS_IQ_SRD_DESIGN: float = 0.35
SYS_IQ_SRD_MINIMUM: float = SYS_IQ_REQUIREMENT  # 0.40
SYS_IQ_SRD_STRETCH: float = 0.30


def idiq_from_sdiq(sdiq: float) -> float:
    """System (sDIQ) budget with the dome-seeing budget removed in quadrature."""
    return float(np.sqrt(sdiq**2 - DOME_FWHM_BUDGET**2))


@dataclass(frozen=True)
class RequirementBox:
    """One nested requirement region: speed above ``f_e``, IQ below ``sys_iq``.

    ``f_e`` is the normalised etendue (RTN-093 section 2; 1.0 = SRD design) and
    is converted to the figure's x unit with ``VISIT_RATE.star_x * f_e``.
    ``sys_iq`` is the system contribution (sDIQ, arcsec); ``idiq`` removes the
    dome term. Boxes are drawn outermost first so that their overlap stacks
    into darker shades for the stricter levels.
    """

    key: str
    label: str
    f_e: float
    sys_iq: float
    source: str

    @property
    def idiq(self) -> float:
        return idiq_from_sdiq(self.sys_iq)

    @property
    def x_min(self) -> float:
        return VISIT_RATE.star_x * self.f_e


#: Lower edge of the green region on the iDIQ axis (purely cosmetic; cell 15 ``y1``).
IDIQ_BOX_BOTTOM: float = 0.1

#: Airmass at which Lynne evaluates the geometric-FWHM reference (cell 10, ``X=1.2``).
REFERENCE_AIRMASS: float = 1.2


def _atm_at(airmass: float) -> float:
    return FIDUCIAL_ATM_FWHM * airmass**0.6


def iq_on_axis(idiq: float, iq_col: str) -> float:
    """Translate an iDIQ value to the y axis of ``iq_col``.

    Follows diq_vs_visit_rate.ipynb cells 10, 15, 16 and 17: iDIQ is used
    directly; FWHM at 500 nm zenith adds the fiducial atmosphere and the dome
    budget in quadrature; geometric FWHM adds the atmosphere at airmass 1.2
    (no dome term, as in the notebook).
    """
    if iq_col == "idiq_aos_cam":
        return float(idiq)
    if iq_col == "fwhm_500_zenith":
        return float(np.sqrt(FIDUCIAL_ATM_FWHM**2 + idiq**2 + DOME_FWHM_BUDGET**2))
    if iq_col == "fwhm_geom":
        return float(np.sqrt(_atm_at(REFERENCE_AIRMASS) ** 2 + idiq**2))
    raise KeyError(iq_col)


_Y_RANGE = {
    "idiq_aos_cam": (0.3, 0.7),
    "fwhm_500_zenith": (0.6, 1.4),
    "fwhm_geom": (0.6, 1.6),
}

# --------------------------------------------------------------------------- #
# Visit rate ("LSST = 1" star and goal region)                                #
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class VisitRateReference:
    """Constants behind the x position of the star and the box edge.

    All values are from diq_vs_visit_rate.ipynb cell 8 (first written in
    sp_notebooks efficiency.ipynb, commit f732da4, 2025-11-22). Sources per
    item are in the field metadata.
    """

    v51_nvisits: int = field(
        default=2075536,
        metadata={"source": "total visits in baseline_v5.1.0_10yrs"},
    )
    v51_wfd_nvisits: int = field(
        default=1692518,
        metadata={"source": "WFD visits in baseline_v5.1.0_10yrs (code only)"},
    )
    v51_median_nvis_per_field: float = field(
        default=762.0,
        metadata={"source": "median WFD visits per field in v5.1 (code only)"},
    )
    nv1_design: float = field(
        default=825.0,
        metadata={"source": "LPM-17 section 3.4.0.1 Table 23, Nv1 design"},
    )
    wfd_time_fraction: float = field(
        default=0.9,
        metadata={"source": "LPM-17 section 3.4, ~90% of time to the main survey"},
    )
    total_est_nvisits: int = field(
        default=3269149,
        metadata={
            "source": "sum of estimated_baseline_visit_range over 10 x 365 nights"
        },
    )
    f_a: float = field(default=0.99, metadata={"source": "RTN-093 fA"})
    f_s: float = field(
        default=1.0, metadata={"source": "diq_vs_visit_rate.ipynb cell 8, fS = 1.0"}
    )
    f_e_min: float = field(
        default=0.7,
        metadata={"source": "RTN-093, lowest allowed normalised etendue 0.7"},
    )

    @property
    def fraction_wfd(self) -> float:
        return self.v51_wfd_nvisits / self.v51_nvisits

    @property
    def f_o_comparison(self) -> float:
        return (
            self.v51_median_nvis_per_field
            / self.nv1_design
            * self.wfd_time_fraction
            / self.fraction_wfd
        )

    @property
    def ratio_sim_nvis(self) -> float:
        return self.v51_nvisits / self.total_est_nvisits

    @property
    def star_x(self) -> float:
        """Acquired/expected visit ratio that corresponds to LSST = 1 (~0.63)."""
        return self.ratio_sim_nvis / self.f_o_comparison / self.f_s / self.f_a

    @property
    def box_x_min(self) -> float:
        """Left edge of the goal region (~0.44)."""
        return self.star_x * self.f_e_min


VISIT_RATE = VisitRateReference()

#: Right edge of the green region. Cosmetic; cell 15 draws it to 1.2.
BOX_X_MAX: float = 1.2

#: The three nested requirement regions, outermost first. Speed thresholds are
#: RTN-093's: fE = 0.7 is "the lowest Normalised Etendue allowed" from the
#: combined SRD minimum specifications (section 3.3) and also the survey-start
#: criterion (Table 2); fE = 1.0 is the SRD design (section 2: "normalized by
#: the corresponding SRD derived design values"). IQ thresholds: RTN-093 0.45
#: for the start criterion; LPM-17 0.40 (minimum) and 0.35 (design).
#: Requested by Phil Marshall, 2026-10-20 ("a new, stricter goal box ...
#: derived from the LSST science requirements"); values to be confirmed with him.
REQUIREMENT_BOXES: tuple[RequirementBox, ...] = (
    RequirementBox(
        key="start",
        label="survey start",
        f_e=VISIT_RATE.f_e_min,
        sys_iq=SYS_IQ_START_CRITERION,
        source="RTN-093 Table 2: Survey Speed > 0.7, sDIQ < 0.45 (dome excluded)",
    ),
    RequirementBox(
        key="minimum",
        label="SRD minimum",
        f_e=VISIT_RATE.f_e_min,
        sys_iq=SYS_IQ_SRD_MINIMUM,
        source="LPM-17 3.3.3.1 minimum 0.40; RTN-093 3.3 fE >= 0.7 from SRD minimum",
    ),
    RequirementBox(
        key="design",
        label="SRD design",
        f_e=1.0,
        sys_iq=SYS_IQ_SRD_DESIGN,
        source="LPM-17 3.3.3.1 design 0.35; RTN-093 2 fE = 1 is the SRD design",
    ),
)


def _y_reference(iq_col: str) -> dict:
    lo, hi = _Y_RANGE[iq_col]
    return {
        "star": iq_on_axis(IDIQ_GOAL, iq_col),
        # Outermost box top, kept for callers that draw a single region.
        "box_top": iq_on_axis(IDIQ_MIN, iq_col),
        "box_tops": {b.key: iq_on_axis(b.idiq, iq_col) for b in REQUIREMENT_BOXES},
        "ymin": lo,
        "ymax": hi,
    }


#: Star y, requirement-box tops and y range for each image-quality statistic.
Y_REFERENCE: dict[str, dict] = {k: _y_reference(k) for k in _Y_RANGE}

# --------------------------------------------------------------------------- #
# Weather                                                                     #
# --------------------------------------------------------------------------- #

#: Fraction of the night (between the -12 deg twilights) that must be flagged as
#: weather for the night to be flagged a "weather night" (informational; never
#: removed from the speed, see README §5). No agreed value exists
#: (ROSP-11 on hold, ROSP-24 draft). 0.7 is what Lynne Jones uses for her
#: open-shutter plots (#ops-logging thread, 2026-08-28); Erik Dennihy uses 0.8.
WEATHER_NIGHT_FRACTION: float = 0.7

#: Primary weather source per the ROSP-24 draft taxonomy (Brian Stalder,
#: 2026-10-10): the EFD Observatory Status WEATHER state, available from
#: 2026-02-25. The narrative log ``time_lost_type == 'weather'`` is kept as a
#: secondary column ("annotation only").
WEATHER_SOURCE_PRIMARY: str = "efd_state"
DAY_OBS_WEATHER_STATE_AVAILABLE: int = 20260225


def summary() -> dict[str, float]:
    """Numbers actually drawn on the plot, for the README and the notebooks."""
    return {
        "star_x (LSST=1 visit ratio)": round(VISIT_RATE.star_x, 3),
        "box_x_min (fE_min * star_x)": round(VISIT_RATE.box_x_min, 3),
        "box_x_max": BOX_X_MAX,
        "star_y (iDIQ goal, arcsec)": IDIQ_GOAL,
        "box_y_max (iDIQ min, arcsec)": round(IDIQ_MIN, 3),
        "box_y_min": IDIQ_BOX_BOTTOM,
        "requirement boxes (x_min, iDIQ top)": {
            b.label: (round(b.x_min, 3), round(b.idiq, 3)) for b in REQUIREMENT_BOXES
        },
        "ROST system IQ band (arcsec)": SYS_IQ_MEASURED_ROST,
        "weather night fraction": WEATHER_NIGHT_FRACTION,
    }
