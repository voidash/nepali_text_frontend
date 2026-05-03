"""Nepali number verbalization.

Converts integer digit strings (Devanagari ०-९ or ASCII 0-9) into
space-separated Nepali word forms suitable for downstream G2P.

Coverage:

- Cardinals 0-99 (lookup, idiosyncratic per Nepali grammar)
- Hundreds, thousands, lakhs, crores (compositional)
- Devanagari and ASCII digit input
- Decimal and fractional numbers (TODO)
- Ordinals (TODO — needs separate ordinal forms)

Source for the 0-99 table: cross-referenced against Wikipedia "Numbers
in Nepali language", imnepal.com, omniglot.com. eSpeak NG ne_list
matches on the multiples-of-10 entries.
"""

from __future__ import annotations

import re

# 0-99 cardinals. The table is idiosyncratic per Nepali grammar: each
# number 1-99 has its own word, not a regular composition like in
# English ("twenty-three" vs Nepali तेईस).
CARDINALS_0_99: dict[int, str] = {
    0: "शून्य",
    1: "एक",
    2: "दुई",
    3: "तीन",
    4: "चार",
    5: "पाँच",
    6: "छ",
    7: "सात",
    8: "आठ",
    9: "नौ",
    10: "दश",
    11: "एघार",
    12: "बाह्र",
    13: "तेह्र",
    14: "चौध",
    15: "पन्ध्र",
    16: "सोह्र",
    17: "सत्र",
    18: "अठार",
    19: "उन्नाइस",
    20: "बीस",
    21: "एक्काइस",
    22: "बाइस",
    23: "तेईस",
    24: "चौबिस",
    25: "पच्चिस",
    26: "छब्बिस",
    27: "सत्ताइस",
    28: "अठ्ठाईस",
    29: "उनन्तिस",
    30: "तीस",
    31: "एकत्तिस",
    32: "बत्तिस",
    33: "तेत्तिस",
    34: "चौँतिस",
    35: "पैँतिस",
    36: "छत्तिस",
    37: "सैँतीस",
    38: "अठतीस",
    39: "उनन्चालीस",
    40: "चालीस",
    41: "एकचालीस",
    42: "बयालीस",
    43: "त्रियालीस",
    44: "चवालीस",
    45: "पैँतालीस",
    46: "छयालीस",
    47: "सच्चालीस",
    48: "अठचालीस",
    49: "उनन्चास",
    50: "पचास",
    51: "एकाउन्न",
    52: "बाउन्न",
    53: "त्रिपन्न",
    54: "चउन्न",
    55: "पचपन्न",
    56: "छपन्न",
    57: "सन्ताउन्न",
    58: "अन्ठाउन्न",
    59: "उनन्साठी",
    60: "साठी",
    61: "एकसट्ठी",
    62: "बयसट्ठी",
    63: "त्रिसट्ठी",
    64: "चौंसट्ठी",
    65: "पैंसट्ठी",
    66: "छयसट्ठी",
    67: "सतसट्ठी",
    68: "अठसट्ठी",
    69: "उनन्सत्तरी",
    70: "सत्तरी",
    71: "एकहत्तर",
    72: "बहत्तर",
    73: "त्रिहत्तर",
    74: "चौहत्तर",
    75: "पचहत्तर",
    76: "छयहत्तर",
    77: "सतहत्तर",
    78: "अठहत्तर",
    79: "उनासी",
    80: "असी",
    81: "एकासी",
    82: "बयासी",
    83: "त्रियासी",
    84: "चौरासी",
    85: "पचासी",
    86: "छयासी",
    87: "सतासी",
    88: "अठासी",
    89: "उनान्नब्बे",
    90: "नब्बे",
    91: "एकान्नब्बे",
    92: "बयानब्बे",
    93: "त्रियान्नब्बे",
    94: "चौरान्नब्बे",
    95: "पन्चानब्बे",
    96: "छयान्नब्बे",
    97: "सन्तान्नब्बे",
    98: "अन्ठान्नब्बे",
    99: "उनान्सय",
}

HUNDRED = "सय"
THOUSAND = "हजार"
LAKH = "लाख"
CRORE = "करोड"

DEVA_DIGIT_TO_INT = {
    "०": 0, "१": 1, "२": 2, "३": 3, "४": 4,
    "५": 5, "६": 6, "७": 7, "८": 8, "९": 9,
}

ANY_DIGIT_RE = re.compile(r"[०-९\d]+")


def parse_digits(s: str) -> int | None:
    """Parse a digit string (Devanagari or ASCII) into an int.

    Returns None if `s` is not a pure digit run.
    """
    if not s:
        return None
    out = 0
    for ch in s:
        if ch.isdigit():
            out = out * 10 + int(ch)
        elif ch in DEVA_DIGIT_TO_INT:
            out = out * 10 + DEVA_DIGIT_TO_INT[ch]
        else:
            return None
    return out


def cardinal(n: int) -> list[str]:
    """Return the Nepali word(s) for a non-negative integer."""
    if n < 0:
        raise ValueError("negative numbers not supported in v0")
    if n < 100:
        return [CARDINALS_0_99[n]]
    if n < 1000:
        h, rem = divmod(n, 100)
        out = cardinal(h) + [HUNDRED]
        if rem:
            out.extend(cardinal(rem))
        return out
    if n < 100_000:
        t, rem = divmod(n, 1000)
        out = cardinal(t) + [THOUSAND]
        if rem:
            out.extend(cardinal(rem))
        return out
    if n < 10_000_000:
        l, rem = divmod(n, 100_000)
        out = cardinal(l) + [LAKH]
        if rem:
            out.extend(cardinal(rem))
        return out
    c, rem = divmod(n, 10_000_000)
    out = cardinal(c) + [CRORE]
    if rem:
        out.extend(cardinal(rem))
    return out


def verbalize_digit_run(s: str) -> list[str]:
    """Convert a digit string into Nepali word tokens.

    Returns a list of Devanagari word tokens. Empty list if input is
    not a pure digit string.
    """
    n = parse_digits(s)
    if n is None:
        return []
    return cardinal(n)


def normalize_numbers_in_text(text: str) -> str:
    """Replace every digit run in `text` with its Nepali word form,
    joined by single spaces. Non-digit content is preserved verbatim.

    Mixes ASCII and Devanagari digits transparently.
    """
    def repl(match: re.Match) -> str:
        words = verbalize_digit_run(match.group(0))
        return " ".join(words) if words else match.group(0)
    return ANY_DIGIT_RE.sub(repl, text)
