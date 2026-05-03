"""Nepali phone-number verbalization.

Converts 10-digit phone-number runs into pair-grouped Nepali word forms,
which is how Nepali speakers naturally read mobile numbers.

Example: 9810223384 → "अन्ठान्नब्बे दश बाइस तेत्तिस चौरासी"
                      ( 98          10  22    33      84  )

Boundary detection: a run is treated as a phone number iff:

- exactly 10 consecutive digits (Devanagari ०-९ or ASCII 0-9, may be mixed)
- no adjacent digit immediately before or after (no embedding inside a
  longer digit run)

Phone numbers with internal separators (`9810-223384`, `+977 98102 23384`,
`९८१–०२–२३३८४`) are NOT picked up by this pass. Strip the separators
upstream if you want pair-grouping; otherwise the general number
verbalizer (`normalize_numbers_in_text`) will read each chunk as a
cardinal. This is by design — country codes and area codes are usually
read as their own units in spoken Nepali, not as phone-number pairs.
"""

from __future__ import annotations

import re

from .numbers import CARDINALS_0_99, cardinal, parse_digits

# 10-digit run with non-digit (or string-edge) boundary on both sides.
# `\d` in Python `re` is Unicode-aware and matches Devanagari ०-९ as well
# as ASCII 0-9, so this catches mixed-script runs like "9८१०22३३84" too.
PHONE_RE = re.compile(r"(?<!\d)(\d{10})(?!\d)")

PHONE_DIGIT_LEN = 10


def verbalize_phone(digit_str: str) -> list[str]:
    """Convert an exactly-10-digit string to pair-grouped Nepali word tokens.

    Pairs from the left: "9810223384" → [98, 10, 22, 33, 84].
    Each pair is verbalized via :func:`numbers.cardinal`. A leading-zero
    pair (e.g. "01") gets an explicit `शून्य` prefix so the digit isn't
    silently dropped — phone numbers care about leading zeros.
    """
    if len(digit_str) != PHONE_DIGIT_LEN:
        raise ValueError(
            f"verbalize_phone expects exactly {PHONE_DIGIT_LEN} digits, "
            f"got {len(digit_str)}"
        )
    out: list[str] = []
    for i in range(0, PHONE_DIGIT_LEN, 2):
        pair = digit_str[i:i + 2]
        n = parse_digits(pair)
        if n is None:
            # Mixed alpha or unparseable — refuse silently; caller falls back
            return []
        first_is_zero = pair[0] in ("0", "०")
        second_is_zero = pair[1] in ("0", "०")
        if first_is_zero and second_is_zero:
            out.append(CARDINALS_0_99[0])
            out.append(CARDINALS_0_99[0])
        elif first_is_zero:
            out.append(CARDINALS_0_99[0])
            d = parse_digits(pair[1])
            assert d is not None  # checked above via parse_digits(pair)
            out.append(CARDINALS_0_99[d])
        else:
            out.extend(cardinal(n))
    return out


def normalize_phones_in_text(text: str) -> str:
    """Replace every isolated 10-digit run in `text` with its pair-grouped
    Nepali word form, joined by single spaces. Non-phone digit runs and
    surrounding content are preserved verbatim.
    """
    def repl(match: re.Match) -> str:
        digit_str = match.group(0)
        try:
            words = verbalize_phone(digit_str)
        except ValueError:
            return digit_str
        return " ".join(words) if words else digit_str

    return PHONE_RE.sub(repl, text)
