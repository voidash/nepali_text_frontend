"""Latin-script code-switch path for Nepali TTS.

This module is intentionally conservative. It does not try to be a complete
English G2P. Its job is to keep Latin spans visible to the TTS pipeline,
handle common product words and acronyms, and mark fallback guesses as low
confidence so they can be reviewed instead of silently disappearing.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from .. import data


@dataclass
class LatinResult:
    text: str
    phones: list[str] = field(default_factory=list)
    source: str = "latin_fallback"
    confidence: str = "low"
    decisions: list[dict] = field(default_factory=list)


LETTER_NAMES: dict[str, list[str]] = {
    "A": ["e"],
    "B": ["b", "i"],
    "C": ["s", "i"],
    "D": ["d", "i"],
    "E": ["i"],
    "F": ["e", "ph"],
    "G": ["dz", "i"],
    "H": ["e", "ts"],
    "I": ["aa", "i"],
    "J": ["dz", "e"],
    "K": ["k", "e"],
    "L": ["e", "l"],
    "M": ["e", "m"],
    "N": ["e", "n"],
    "O": ["o"],
    "P": ["p", "i"],
    "Q": ["k", "y", "u"],
    "R": ["aa", "r"],
    "S": ["e", "s"],
    "T": ["t", "i"],
    "U": ["y", "u"],
    "V": ["bh", "i"],
    "W": ["d", "ax", "b", "l", "y", "u"],
    "X": ["e", "k", "s"],
    "Y": ["w", "aa", "i"],
    "Z": ["dz", "e", "dx"],
}


COMMON_WORDS: dict[str, list[str]] = {
    "ai": ["e", "aa", "i"],
    "app": ["e", "p"],
    "at": ["aa", "tx"],
    "audio": ["aa", "dx", "i", "o"],
    "bank": ["b", "e", "ng", "k"],
    "bus": ["b", "ax", "s"],
    "chat": ["ts", "aa", "tx"],
    "com": ["k", "o", "m"],
    "data": ["dx", "e", "tx", "aa"],
    "dash": ["dx", "aa", "s"],
    "digital": ["dx", "i", "dz", "i", "tx", "ax", "l"],
    "dot": ["dx", "ax", "tx"],
    "download": ["dx", "aa", "u", "n", "l", "o", "dx"],
    "email": ["i", "m", "e", "l"],
    "equals": ["i", "k", "w", "ax", "l", "s"],
    "example": ["e", "k", "z", "aa", "m", "p", "ax", "l"],
    "facebook": ["f", "e", "s", "b", "u", "k"],
    "file": ["f", "aa", "i", "l"],
    "google": ["g", "u", "g", "ax", "l"],
    "growth": ["g", "r", "o", "th"],
    "gmail": ["dz", "i", "m", "e", "l"],
    "hello": ["h", "e", "l", "o"],
    "http": ["e", "ts", ".", "t", "i", ".", "t", "i", ".", "p", "i"],
    "https": ["e", "ts", ".", "t", "i", ".", "t", "i", ".", "p", "i", ".", "e", "s"],
    "internet": ["i", "n", "tx", "ax", "r", "n", "e", "tx"],
    "link": ["l", "i", "ng", "k"],
    "login": ["l", "o", "g", "i", "n"],
    "mobile": ["m", "o", "b", "aa", "i", "l"],
    "net": ["n", "e", "tx"],
    "news": ["n", "y", "u", "z"],
    "online": ["o", "n", "l", "aa", "i", "n"],
    "org": ["o", "r", "g"],
    "post": ["p", "o", "s", "tx"],
    "software": ["s", "o", "ph", "tx", "w", "e", "r"],
    "slash": ["s", "l", "aa", "s"],
    "tts": ["t", "i", "t", "i", "e", "s"],
    "underscore": ["ax", "n", "dx", "ax", "r", "s", "k", "o", "r"],
    "upload": ["ax", "p", "l", "o", "dx"],
    "url": ["y", "u", "aa", "r", "e", "l"],
    "video": ["bh", "i", "dx", "i", "o"],
    "website": ["w", "e", "b", "s", "aa", "i", "tx"],
    "youtube": ["y", "u", "tx", "y", "u", "b"],
}


ROMAN_RULES: list[tuple[str, list[str]]] = [
    ("tion", ["s", "ax", "n"]),
    ("sion", ["s", "ax", "n"]),
    ("ough", ["o"]),
    ("ch", ["ts"]),
    ("sh", ["s"]),
    ("th", ["t"]),
    ("ph", ["f"]),
    ("ng", ["ng"]),
    ("ck", ["k"]),
    ("qu", ["k", "w"]),
    ("oo", ["u"]),
    ("ee", ["i"]),
    ("ai", ["e"]),
    ("ay", ["e"]),
    ("au", ["aa", "w"]),
    ("ou", ["aa", "w"]),
]

SINGLE_LETTER: dict[str, list[str]] = {
    "a": ["ax"],
    "b": ["b"],
    "c": ["k"],
    "d": ["d"],
    "e": ["e"],
    "f": ["f"],
    "g": ["g"],
    "h": ["h"],
    "i": ["i"],
    "j": ["dz"],
    "k": ["k"],
    "l": ["l"],
    "m": ["m"],
    "n": ["n"],
    "o": ["o"],
    "p": ["p"],
    "q": ["k"],
    "r": ["r"],
    "s": ["s"],
    "t": ["tx"],
    "u": ["u"],
    "v": ["bh"],
    "w": ["w"],
    "x": ["k", "s"],
    "y": ["y"],
    "z": ["z"],
}

ACRONYM_RE = re.compile(r"^[A-Z0-9]{2,8}$")


def phonemize_latin(text: str) -> LatinResult:
    """Return Nepali phone labels for one Latin token."""
    cleaned = text.strip()
    if not cleaned:
        return LatinResult(text=text, phones=[], source="empty", confidence="low")

    key = cleaned.lower().replace("'", "")
    if key in COMMON_WORDS:
        phones = list(COMMON_WORDS[key])
        return LatinResult(
            text=text,
            phones=phones,
            source="latin_lexicon",
            confidence="medium",
            decisions=[{
                "type": "code_switch",
                "rule": "latin_lexicon",
                "span": text,
                "after": " ".join(phones),
            }],
        )

    if _looks_like_acronym(cleaned):
        phones = _letter_name_phones(cleaned)
        return LatinResult(
            text=text,
            phones=phones,
            source="latin_acronym",
            confidence="medium",
            decisions=[{
                "type": "code_switch",
                "rule": "latin_acronym_letter_names",
                "span": text,
                "after": " ".join(phones),
            }],
        )

    loanwords = data.latin_loanwords()
    if key in loanwords:
        phones = list(loanwords[key])
        return LatinResult(
            text=text,
            phones=phones,
            source="latin_loanword_table",
            confidence="medium",
            decisions=[{
                "type": "code_switch",
                "rule": "latin_loanword_table",
                "span": text,
                "after": " ".join(phones),
            }],
        )

    phones = _roman_fallback(key)
    return LatinResult(
        text=text,
        phones=phones,
        source="latin_rule_fallback",
        confidence="low",
        decisions=[{
            "type": "code_switch",
            "rule": "latin_rule_fallback_nepali_accent",
            "span": text,
            "after": " ".join(phones),
        }],
    )


def _looks_like_acronym(text: str) -> bool:
    return bool(ACRONYM_RE.match(text)) or (
        len(text) <= 4 and text.isupper() and any(ch.isalpha() for ch in text)
    )


def looks_like_acronym(text: str) -> bool:
    """Public wrapper for other Latin-script code-switch frontends."""
    return _looks_like_acronym(text)


def _letter_name_phones(text: str) -> list[str]:
    out: list[str] = []
    for ch in text:
        if ch.isdigit():
            from ..normalize.numbers import CARDINALS_0_99
            from ..g2p.phonemizer import phonemize_word

            out.extend(phonemize_word(CARDINALS_0_99[int(ch)]).phones)
            continue
        phones = LETTER_NAMES.get(ch.upper())
        if not phones:
            continue
        if out:
            out.append(".")
        out.extend(phones)
    return out


def letter_name_phones(text: str) -> list[str]:
    """Return Nepali phone labels for spelling a Latin acronym."""
    return _letter_name_phones(text)


def _roman_fallback(text: str) -> list[str]:
    out: list[str] = []
    i = 0
    while i < len(text):
        ch = text[i]
        if not ch.isalpha():
            i += 1
            continue
        matched = False
        for raw, phones in ROMAN_RULES:
            if text.startswith(raw, i):
                out.extend(phones)
                i += len(raw)
                matched = True
                break
        if matched:
            continue
        out.extend(SINGLE_LETTER.get(ch, []))
        i += 1
    return out


def fallback_phones(text: str) -> list[str]:
    """Conservative Latin spelling fallback using Nepali phone labels."""
    return _roman_fallback(text.lower())
