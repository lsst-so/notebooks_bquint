"""Colours: import the repo palette, never redefine hex values.

Path resolved relative to this file (``../../rubin_color_pallete``); copy the
palette module into this folder before extracting the investigation.

One palette across the LSST@LATAM talk figures (B1, B3, B11), one colour per
category (2026-10-26, Focus and Alignment added 2026-10-27): survey = green
(slot 5), Focus and Alignment = purple (slot 3, as in B10/B10b), engineering =
orange (slot 2, as in B10/B10b), weather = neutral grey (as in B11), fault + idle
= brand blue. Checked with the dataviz palette validator (OKLab, Machado 2009 CVD,
WCAG) on all ten pairs, light surface: worst CVD dE 11.2 (focus vs fault, deutan),
worst normal-vision dE 15.5 (engineering vs weather), all PASS; purple on white
7.6:1. Red (slot 4) and olive (slot 6) fail the normal-vision floor against the
engineering orange (dE 12.4 / 12.3), teal passes but is Survey Programs in B10;
blue is the only brand hue left that passes. The Dynalene closure is drawn in the
fault colour, hatched.
"""

from __future__ import annotations

import sys
from pathlib import Path

_PALETTE_DIR = Path(__file__).resolve().parents[2] / "rubin_color_pallete"
if str(_PALETTE_DIR) not in sys.path:
    sys.path.insert(0, str(_PALETTE_DIR))
import rubin_palette as rp  # noqa: E402

__all__ = ["rp", "COLORS"]

COLORS = {
    "on_sky": rp.CATEGORICAL[4],  # survey (A), green
    "focus": rp.CATEGORICAL[2],  # Focus and Alignment, purple (B10/B10b)
    "engineering": rp.CATEGORICAL[1],  # B2, orange (B10/B10b)
    "weather": rp.NEUTRALS["muted"],  # C, grey (B11)
    "nonweather_loss": rp.BRAND["blue"],  # D + E fault + idle, brand blue #1C81A4
    "downtime": rp.NEUTRALS["muted"],
    "ink": rp.NEUTRALS["ink"],
    "ink_secondary": rp.NEUTRALS["ink_secondary"],
    "muted": rp.NEUTRALS["muted"],
    "grid": rp.NEUTRALS["grid"],
}
