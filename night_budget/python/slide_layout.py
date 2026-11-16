"""Slide geometry for the stacked LATAM figures B12 and B13.

B12 (``make_good_bad_night_figure.py``) and B13
(``make_cumulative_visits_figure.py``) sit one under the other in the same box on
slide 6 and are both :data:`FIG_W` wide; only the heights differ.  What each one
needs at its sides is quite different, though, so they get **different side
margins** and this module holds both sets:

* B12 spends 1.29 in on the left on its bar labels ("06 Jul 2026" / "smooth").
* B13 needs only its y label and tick numbers there - about 0.6 in - and wants
  the rest on the right, where the longest end label lives.

The consequence is that **the two figures' hour ticks do not line up** when
stacked.  They did in the first version, which shared B12's margins, but that
left B13 with 0.7 in of empty space on the left and forced its longest end label
onto two lines.  Bruno chose the single-row label over the alignment
(2026-11-02); if the alignment is ever wanted back, point B13 at
:func:`b12_side_margins`.
"""

from __future__ import annotations

#: Width of the slide box both figures are placed in, inches (Bruno, 2026-11-02).
FIG_W = 9.55

#: B12: its original ``subplots_adjust(left=0.135, right=0.855)`` in inches.
B12_LEFT_IN = 0.135 * FIG_W  # 1.289 in - the bar labels
B12_RIGHT_IN = (1.0 - 0.855) * FIG_W  # 1.385 in - "899 visits · 0.85"

#: B13 left: the rotated "survey visits" label (0.10 in), the widest tick number
#: ("1000", 0.27 in) and the two label pads, with a little air.
B13_LEFT_IN = 0.60
#: B13 right: the longest end label, "LSST min criteria (0.7 ideal) · 739 · 62 /h",
#: is 2.41 in at 8.5 pt, plus the ``END_LABEL_DX_H`` offset from the axis
#: (~0.05 in) and a hair of margin. This is what buys the label a single row; it
#: grew from 2.08 in when Bruno asked for the visits/h on each label (2026-11-02).
B13_RIGHT_IN = 2.50


def _fractions(left_in: float, right_in: float, fig_w: float) -> dict[str, float]:
    return {"left": left_in / fig_w, "right": 1.0 - right_in / fig_w}


def b12_side_margins(fig_w: float = FIG_W) -> dict[str, float]:
    """B12's ``left`` / ``right`` as ``subplots_adjust`` fractions."""
    return _fractions(B12_LEFT_IN, B12_RIGHT_IN, fig_w)


def b13_side_margins(fig_w: float = FIG_W) -> dict[str, float]:
    """B13's ``left`` / ``right`` as ``subplots_adjust`` fractions."""
    return _fractions(B13_LEFT_IN, B13_RIGHT_IN, fig_w)
