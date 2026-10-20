"""Colours and sizes shared by the three figure versions.

Imports Bruno's Rubin palette from ``rubin_color_pallete/rubin_palette.py`` in
this repository (path resolved relative to this file). No colour is defined
here; every value is a name from that module.
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib as mpl
import numpy as np

_PALETTE_DIR = Path(__file__).resolve().parents[2] / "rubin_color_pallete"
if str(_PALETTE_DIR) not in sys.path:
    sys.path.insert(0, str(_PALETTE_DIR))
import rubin_palette as rp  # noqa: E402

__all__ = ["rp", "COLORS", "time_colors", "paper_rc", "talk_rc"]

#: Roles -> palette names. Change the role mapping here, never the hex.
COLORS = {
    "goal_region": rp.CATEGORICAL[4],  # green slot
    "star": rp.CATEGORICAL[1],  # orange slot
    "star_edge": rp.NEUTRALS["ink_secondary"],
    "rost_band": rp.CATEGORICAL[2],  # purple slot
    "path": rp.NEUTRALS["ink_secondary"],
    "gap": rp.NEUTRALS["muted"],
    "ink": rp.NEUTRALS["ink"],
    "ink_secondary": rp.NEUTRALS["ink_secondary"],
    "grid": rp.NEUTRALS["grid"],
    "muted": rp.NEUTRALS["muted"],
}


def time_colors(
    n: int, lo: float = 0.25, hi: float = 1.0, reverse: bool = False
) -> list[str]:
    """``n`` hex colours from the teal ramp, light (first month) to dark (latest).

    The lightest fifth of the ramp is skipped (``lo``) so the first point is
    still visible on white.
    """
    cmap = rp.teal_cmap()
    vals = np.linspace(lo, hi, max(n, 1))
    if reverse:
        vals = vals[::-1]
    return [mpl.colors.to_hex(cmap(v)) for v in vals]


def paper_rc(width_in: float = 3.4) -> dict:
    """rcParams for the AAS-column static version."""
    return {
        "figure.figsize": (width_in, width_in * 0.8),
        "font.size": 8,
        "axes.labelsize": 8.5,
        "axes.titlesize": 9,
        "xtick.labelsize": 8,
        "ytick.labelsize": 8,
        "legend.fontsize": 8,
        "lines.linewidth": 0.8,
        "axes.linewidth": 0.6,
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
    }


def talk_rc(full_slide: bool = True) -> dict:
    """rcParams for the 16:9 talk version."""
    w = 13.33 if full_slide else 6.67
    return {
        "figure.figsize": (w, w * 9 / 16),
        "font.size": 20,
        "axes.labelsize": 22,
        "axes.titlesize": 24,
        "xtick.labelsize": 18,
        "ytick.labelsize": 18,
        "legend.fontsize": 18,
        "lines.linewidth": 3,
        "lines.markersize": 14,
        "axes.linewidth": 1.5,
    }
