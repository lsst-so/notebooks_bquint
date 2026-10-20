"""Rubin Observatory colour palette for plots and presentations.

Primary colour is the Rubin brand teal (Pantone 2237 C, ``#058B8C``). The
categorical palette has six slots derived from the Visual Identity Manual
(V7, 2021-02-12) accent hues, with lightness re-stepped so that every slot
reads at >= 3:1 against a white slide and adjacent slots stay apart under
protanopia / deuteranopia (OKLab dE >= 8, worst adjacent pair 9.3 light /
10.0 dark). Hues were kept; only lightness/chroma moved.

Use the slots **in order** (teal, orange, purple, red, green, olive). Do not
re-order or skip: the order is what makes neighbours colour-blind safe.
For scatter plots where any two colours can touch, stay within the first
three slots (teal / orange / purple validate all-pairs); beyond that fold
series into "Other" or facet.

Usage
-----
    import sys; sys.path.insert(0, "/path/to/notebooks_bquint/rubin_color_pallete")
    import rubin_palette as rp

    rp.use()                         # set matplotlib colour cycle (light mode)
    rp.use(mode="dark")              # for dark slides
    ax.plot(x, y, color=rp.TEAL)
    ax.bar(x, y, color=rp.CATEGORICAL)          # list of 6 hex strings
    im = ax.imshow(z, cmap=rp.teal_cmap())      # sequential teal ramp
    rp.preview("rubin_palette_preview.png")     # swatches + CVD simulation
"""

from __future__ import annotations

import matplotlib as mpl
import matplotlib.pyplot as plt
from cycler import cycler
from matplotlib.colors import LinearSegmentedColormap, ListedColormap

__all__ = [
    "TEAL",
    "BRAND",
    "CATEGORICAL",
    "CATEGORICAL_DARK",
    "NAMES",
    "NEUTRALS",
    "SEQUENTIAL_TEAL",
    "cycle",
    "use",
    "teal_cmap",
    "categorical_cmap",
    "preview",
]

# --------------------------------------------------------------------------- #
# Brand colours (Visual Identity Manual V7, pp. 27-30) - verbatim             #
# --------------------------------------------------------------------------- #
TEAL = "#058B8C"  # primary imagotype teal (Pantone 2237 C)

BRAND = {
    "teal": "#058B8C",  # Pantone 2237 C
    "bright_teal": "#00BABC",  # Pantone 2397 C
    "mid_teal": "#009FA1",  # Pantone 320 C
    "dark_teal": "#0C4A47",  # Pantone 3302 C
    "steel": "#313333",  # Pantone 447 C
    "cool_gray": "#6A6E6E",  # Pantone Cool Gray 9 C
    "red": "#ED4C4C",  # Pantone 2348 C
    "green": "#3CAE3F",  # Pantone 7738 C
    "orange": "#FAB364",  # Pantone 1485 C
    "yellow": "#FFE266",  # Pantone 2003 C
    "blue": "#1C81A4",  # Pantone 2454 C
    "purple": "#583671",  # Pantone 7665 C
}

# --------------------------------------------------------------------------- #
# Categorical palette - fixed order, never cycle past 6                       #
# --------------------------------------------------------------------------- #
NAMES = ["teal", "orange", "purple", "red", "green", "olive"]

# Light surfaces (white slides / paper). All >= 3:1 on white.
CATEGORICAL = [
    "#058B8C",  # 1 teal   - brand primary, exact
    "#CE7F00",  # 2 orange - brand orange hue, darkened for contrast
    "#74369E",  # 3 purple - brand purple hue, lifted slightly
    "#DB5451",  # 4 red    - brand red hue
    "#00630C",  # 5 green  - brand green hue, darkened
    "#8A7500",  # 6 olive  - brand yellow hue, darkened (reads as dark gold)
]

# Dark surfaces (dark slides, ~#1a1a19). Same hues, re-stepped; all >= 3:1.
CATEGORICAL_DARK = [
    "#009FA1",  # 1 teal   - brand "mid teal" (Pantone 320 C)
    "#B97200",  # 2 orange
    "#8D4DB9",  # 3 purple
    "#BE4442",  # 4 red
    "#46AD48",  # 5 green
    "#7A6600",  # 6 olive
]

# Text / grid / de-emphasised series ("all test cases" style background bars)
NEUTRALS = {
    "ink": "#313333",  # titles, labels (brand steel)
    "ink_secondary": "#6A6E6E",  # axis labels, legends (brand cool gray)
    "muted": "#9AA0A0",  # background bars, "other"
    "grid": "#DCE0E3",  # grid lines, downtime hatch fill
}

# Sequential ramp on the teal hue (light -> dark), for heatmaps / magnitudes.
SEQUENTIAL_TEAL = ["#E6F4F4", "#9FDADB", "#3DAEB0", "#058B8C", "#256060", "#0C4A47"]


# --------------------------------------------------------------------------- #
# Helpers                                                                     #
# --------------------------------------------------------------------------- #
def _palette(mode: str) -> list[str]:
    if mode == "light":
        return CATEGORICAL
    if mode == "dark":
        return CATEGORICAL_DARK
    raise ValueError(f"mode must be 'light' or 'dark', got {mode!r}")


def cycle(mode: str = "light") -> cycler:
    """Return a matplotlib ``cycler`` for ``axes.prop_cycle``."""
    return cycler(color=_palette(mode))


def use(mode: str = "light") -> None:
    """Set the matplotlib colour cycle (and sensible neutral text colours)."""
    mpl.rcParams["axes.prop_cycle"] = cycle(mode)
    ink = "#F0EFEC" if mode == "dark" else NEUTRALS["ink"]
    mpl.rcParams.update(
        {
            "text.color": ink,
            "axes.labelcolor": ink,
            "axes.edgecolor": NEUTRALS["ink_secondary"],
            "xtick.color": NEUTRALS["ink_secondary"],
            "ytick.color": NEUTRALS["ink_secondary"],
            "grid.color": NEUTRALS["grid"] if mode == "light" else "#3A3A38",
        }
    )


def teal_cmap(reverse: bool = False) -> LinearSegmentedColormap:
    """Continuous sequential colormap, light -> teal -> dark teal."""
    colors = SEQUENTIAL_TEAL[::-1] if reverse else SEQUENTIAL_TEAL
    return LinearSegmentedColormap.from_list("rubin_teal", colors)


def categorical_cmap(mode: str = "light") -> ListedColormap:
    """Discrete colormap with the six categorical slots in order."""
    return ListedColormap(_palette(mode), name=f"rubin_{mode}")


# --------------------------------------------------------------------------- #
# Preview with colour-vision-deficiency simulation                            #
# --------------------------------------------------------------------------- #
_MACHADO = {  # Machado, Oliveira & Fernandes (2009), severity 1.0, linear RGB
    "protanopia": [
        [0.152286, 1.052583, -0.204868],
        [0.114503, 0.786281, 0.099216],
        [-0.003882, -0.048116, 1.051998],
    ],
    "deuteranopia": [
        [0.367322, 0.860646, -0.227968],
        [0.280085, 0.672501, 0.047413],
        [-0.011820, 0.042940, 0.968881],
    ],
    "tritanopia": [
        [1.255528, -0.076749, -0.178779],
        [-0.078411, 0.930809, 0.147602],
        [0.004733, 0.691367, 0.303900],
    ],
}


def simulate_cvd(hex_color: str, kind: str) -> str:
    """Return ``hex_color`` as seen with the given colour-vision deficiency."""
    import numpy as np

    rgb = np.array(mpl.colors.to_rgb(hex_color))
    lin = np.where(rgb <= 0.04045, rgb / 12.92, ((rgb + 0.055) / 1.055) ** 2.4)
    sim = np.clip(np.array(_MACHADO[kind]) @ lin, 0, 1)
    srgb = np.where(sim <= 0.0031308, 12.92 * sim, 1.055 * sim ** (1 / 2.4) - 0.055)
    return mpl.colors.to_hex(srgb)


def preview(path: str | None = None, mode: str = "light"):
    """Swatches, CVD simulations and a sample chart. Saves to ``path`` if given."""
    import numpy as np

    pal = _palette(mode)
    surface = "#1A1A19" if mode == "dark" else "#FFFFFF"
    ink = "#F0EFEC" if mode == "dark" else NEUTRALS["ink"]

    fig = plt.figure(figsize=(12, 7.5), facecolor=surface)
    gs = fig.add_gridspec(2, 2, height_ratios=[0.9, 1], hspace=0.5, wspace=0.25)

    # swatches: normal + 3 CVD rows
    ax = fig.add_subplot(gs[0, :])
    ax.set_facecolor(surface)
    rows = ["normal vision", "protanopia", "deuteranopia", "tritanopia"]
    for r, kind in enumerate(rows):
        for i, c in enumerate(pal):
            cc = c if kind == "normal vision" else simulate_cvd(c, kind)
            ax.add_patch(plt.Rectangle((i, -r), 0.92, 0.8, color=cc))
            if r == 0:
                ax.text(
                    i + 0.46,
                    1.0,
                    f"{i + 1}  {NAMES[i]}\n{c}",
                    ha="center",
                    va="bottom",
                    fontsize=9,
                    color=ink,
                )
        ax.text(-0.15, -r + 0.4, kind, ha="right", va="center", fontsize=9, color=ink)
    ax.set_xlim(-1.6, len(pal))
    ax.set_ylim(-len(rows) + 0.7, 2.2)
    ax.axis("off")
    ax.set_title(
        f"Rubin categorical palette ({mode} mode) - use slots in order",
        color=ink,
        fontsize=12,
        pad=4,
    )

    # sample bars
    ax = fig.add_subplot(gs[1, 0])
    ax.set_facecolor(surface)
    x = np.arange(4)
    for i, c in enumerate(pal):
        ax.bar(
            x + i * 0.14, 1 + 0.5 * np.sin(x + i), width=0.13, color=c, label=NAMES[i]
        )
    ax.set_xticks(x + 0.35)
    ax.set_xticklabels(["A", "B", "C", "D"], color=ink)
    ax.tick_params(colors=NEUTRALS["ink_secondary"])
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.legend(
        ncol=6,
        fontsize=8,
        frameon=False,
        labelcolor=ink,
        loc="lower center",
        bbox_to_anchor=(0.5, 1.02),
    )
    ax.set_title("grouped bars", color=ink, fontsize=10, pad=22)

    # sample lines on teal cmap background
    ax = fig.add_subplot(gs[1, 1])
    ax.set_facecolor(surface)
    t = np.linspace(0, 10, 200)
    for i, c in enumerate(pal):
        ax.plot(t, np.sin(t / 2 + i * 0.9) + 0.25 * i, color=c, lw=2, label=NAMES[i])
    ax.tick_params(colors=NEUTRALS["ink_secondary"])
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.set_title("lines", color=ink, fontsize=10)
    cb = fig.colorbar(
        mpl.cm.ScalarMappable(cmap=teal_cmap()), ax=ax, fraction=0.05, pad=0.02
    )
    cb.set_label("teal_cmap()", color=ink)
    cb.ax.tick_params(colors=NEUTRALS["ink_secondary"])

    if path:
        fig.savefig(path, dpi=150, bbox_inches="tight", facecolor=surface)
    return fig


if __name__ == "__main__":
    import pathlib

    here = pathlib.Path(__file__).parent
    preview(here / "rubin_palette_preview_light.png", "light")
    preview(here / "rubin_palette_preview_dark.png", "dark")
