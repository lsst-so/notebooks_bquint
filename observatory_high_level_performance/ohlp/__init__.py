"""Observatory high-level performance: survey speed vs. delivered image quality.

Small package shared by every version of the figure (interactive, talk, paper).
All numbers that are not computed from data live in :mod:`ohlp.reference`
together with their sources.
"""

from . import binning, data, reference, style  # noqa: F401

__all__ = ["binning", "data", "reference", "style"]
