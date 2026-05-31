"""Text normalization submodule.

Translates non-spoken-form text (numerals, dates, currency, abbreviations,
units, URLs) into spoken Nepali words before G2P.

Composition order matters: more specific verbalisers run first so that
their matches are not eaten by the general number pass.
"""

from __future__ import annotations

from .numbers import normalize_numbers_in_text
from .phones import normalize_phones_in_text
from .text import normalize


def normalize_text(text: str) -> str:
    """Run all spoken-form verbalisers in the canonical order.

    Order: phones → numbers. Phone-number pair-grouping must run before
    the general cardinal pass; otherwise a 10-digit run gets read as a
    single (huge) cardinal instead of as five spoken pairs.
    """
    return normalize(text)[0]


__all__ = [
    "normalize_text",
    "normalize",
    "normalize_numbers_in_text",
    "normalize_phones_in_text",
]
