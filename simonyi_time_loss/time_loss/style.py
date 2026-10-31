"""Colours: import the repo palette, never redefine hex values.

Path resolved relative to this file (``../../rubin_color_pallete``); copy the
palette module into this folder before extracting the investigation.

One palette across the LSST@LATAM talk figures (B1, B3, B11). Category colours
come from ``rp.CATEGORY_COLORS`` (2026-10-31), the table every figure in the repo
shares and whose roles follow the nightly survey speed plot: survey = brand blue,
Focus and Alignment = green, engineering = orange, weather = neutral grey,
fault + idle = wine. Validation and the deliberate exceptions are in the palette
README. The Dynalene closure is drawn in the fault colour, hatched.
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
    "on_sky": rp.CATEGORY_COLORS["survey"],  # survey (A)
    "focus": rp.CATEGORY_COLORS["focus"],  # Focus and Alignment
    "engineering": rp.CATEGORY_COLORS["engineering"],  # B2
    "weather": rp.CATEGORY_COLORS["weather"],  # C
    "nonweather_loss": rp.CATEGORY_COLORS["fault_idle"],  # D + E fault + idle
    "downtime": rp.NEUTRALS["muted"],
    "ink": rp.NEUTRALS["ink"],
    "ink_secondary": rp.NEUTRALS["ink_secondary"],
    "muted": rp.NEUTRALS["muted"],
    "grid": rp.NEUTRALS["grid"],
}
