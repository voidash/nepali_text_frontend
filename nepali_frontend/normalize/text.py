"""Top-level text normalizer.

Pipeline (v0): just numbers. Future stages will add dates, currency,
phone numbers, units, abbreviations, URLs.
"""

from __future__ import annotations

from . import numbers as _numbers


def normalize(text: str) -> tuple[str, list[dict]]:
    """Normalize a raw text input into a spoken-form Nepali string.

    Returns: `(normalized_text, decisions)` where `decisions` is a list
    of trace events documenting each substitution.
    """
    decisions: list[dict] = []

    # 1. Numbers
    before = text
    after = _numbers.normalize_numbers_in_text(before)
    if after != before:
        decisions.append({
            "type": "text_normalization",
            "rule": "ne_cardinal_number",
            "before": before,
            "after": after,
        })
    return after, decisions
