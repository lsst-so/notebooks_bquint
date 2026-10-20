"""Colours: import the repo palette, never redefine hex values.

Path resolved relative to this file (``../../rubin_color_pallete``); copy the
palette module into this folder before extracting the investigation.
"""

from __future__ import annotations

import sys
from pathlib import Path

_PALETTE_DIR = Path(__file__).resolve().parents[2] / "rubin_color_pallete"
if str(_PALETTE_DIR) not in sys.path:
    sys.path.insert(0, str(_PALETTE_DIR))
import rubin_palette as rp  # noqa: E402

__all__ = ["rp", "COLORS"]

#: Roles -> palette slots. Weather = teal (primary), non-weather loss = orange,
#: on-sky = green, downtime = muted grey. Change the role mapping here only.
COLORS = {
    "weather": rp.CATEGORICAL[0],
    "nonweather_loss": rp.CATEGORICAL[1],
    "on_sky": rp.CATEGORICAL[4],
    "downtime": rp.NEUTRALS["muted"],
    "ink": rp.NEUTRALS["ink"],
    "ink_secondary": rp.NEUTRALS["ink_secondary"],
    "muted": rp.NEUTRALS["muted"],
    "grid": rp.NEUTRALS["grid"],
}
