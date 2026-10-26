"""Colours: import the repo palette, never redefine hex values.

Path resolved relative to this file (``../../rubin_color_pallete``); copy the
palette module into this folder before extracting the investigation.

One palette across the LSST@LATAM talk figures (B1, B3, B11), one colour per
ROSP-24 category (2026-10-26): survey = green (slot 5), engineering = orange
(slot 2, as in B10/B10b), weather = neutral grey (as in B11), fault + idle = brand
blue. Checked with the dataviz palette validator (OKLab, Machado 2009 CVD, WCAG)
on all six pairs, light surface: worst CVD dE 12.3, worst normal-vision dE 15.5,
all PASS. Red (slot 4) and olive (slot 6) fail the normal-vision floor against the
engineering orange (dE 12.4 / 12.3), purple passes but is Focus and Alignment in
B10/B10b, teal passes but is Survey Programs there; blue is the only brand hue
left that passes. The Dynalene closure is drawn in the fault colour, hatched.
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
    "engineering": rp.CATEGORICAL[1],  # B2, orange (B10/B10b)
    "weather": rp.NEUTRALS["muted"],  # C, grey (B11)
    "nonweather_loss": rp.BRAND["blue"],  # D + E fault + idle, brand blue #1C81A4
    "downtime": rp.NEUTRALS["muted"],
    "ink": rp.NEUTRALS["ink"],
    "ink_secondary": rp.NEUTRALS["ink_secondary"],
    "muted": rp.NEUTRALS["muted"],
    "grid": rp.NEUTRALS["grid"],
}
