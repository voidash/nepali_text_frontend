"""Romanized Nepali detection and phonemization.

This path is for Latin-script Nepali typed as words such as
``mero naam aashish thapa ho``. It deliberately stays conservative: a Latin
span must contain Nepali markers before the frontend labels it as
``ne_roman`` instead of English.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
import re

from .. import data
from . import english


@dataclass
class RomanNepaliClassification:
    is_roman_nepali: bool
    score: float
    markers: list[str] = field(default_factory=list)
    suffix_hits: list[str] = field(default_factory=list)
    token_count: int = 0

    def as_decision(self, span: str) -> dict:
        return {
            "type": "code_switch",
            "rule": "roman_nepali_span_classifier",
            "span": span,
            "score": round(self.score, 3),
            "markers": list(self.markers),
            "suffix_hits": list(self.suffix_hits),
            "after": "ne_roman" if self.is_roman_nepali else "en",
        }


NE_ROMAN_MARKERS: set[str] = {
    "aaja",
    "aja",
    "aba",
    "bhai",
    "bhainchha",
    "bhane",
    "bhanera",
    "bhanney",
    "bhayena",
    "bhayo",
    "cha",
    "chaina",
    "chha",
    "chhaina",
    "chhainchha",
    "dai",
    "dhanyabad",
    "didi",
    "garera",
    "garcha",
    "garchha",
    "garne",
    "hamro",
    "ho",
    "hoina",
    "hola",
    "hudaina",
    "huncha",
    "hunchha",
    "jaane",
    "jana",
    "kahaan",
    "kahile",
    "kasari",
    "kasto",
    "kati",
    "khana",
    "khane",
    "kura",
    "lai",
    "malai",
    "matra",
    "mero",
    "naam",
    "nai",
    "namaste",
    "pani",
    "rahecha",
    "rahechha",
    "raicha",
    "raichha",
    "sakchhu",
    "sakchu",
    "sakchhau",
    "saathi",
    "sathi",
    "sathii",
    "tapai",
    "tapain",
    "timro",
    "tyestai",
    "tyesto",
    "yesto",
}

NE_ROMAN_SUFFIXES: tuple[str, ...] = (
    "chha",
    "cha",
    "eko",
    "eka",
    "haru",
    "haroo",
    "nu",
    "nuhos",
    "unu",
)

SINGLE_TOKEN_MARKERS: set[str] = {
    "dhanyabad",
    "malai",
    "mero",
    "namaste",
    "timro",
}

TOKEN_CLEAN_RE = re.compile(r"[^a-z]+")


def classify_tokens(tokens: Sequence[str]) -> RomanNepaliClassification:
    """Classify a contiguous Latin-token span as English or romanized Nepali."""
    keys = [_clean_token(token) for token in tokens]
    keys = [key for key in keys if key]
    token_count = len(keys)
    if token_count == 0:
        return RomanNepaliClassification(False, 0.0)

    marker_hits = sorted({key for key in keys if key in NE_ROMAN_MARKERS})
    suffix_hits = sorted({
        key
        for key in keys
        if key not in marker_hits and _has_nepali_suffix(key)
    })
    score = min(1.0, ((2 * len(marker_hits)) + len(suffix_hits)) / token_count)
    is_single_high_signal = token_count == 1 and keys[0] in SINGLE_TOKEN_MARKERS
    is_roman = is_single_high_signal or len(marker_hits) >= 2 or (
        token_count >= 3 and score >= 0.45
    )

    return RomanNepaliClassification(
        is_roman_nepali=is_roman,
        score=score,
        markers=marker_hits,
        suffix_hits=suffix_hits,
        token_count=token_count,
    )


def phonemize_roman_nepali(text: str) -> english.LatinResult:
    """Return Nepali phone labels for one romanized Nepali token."""
    cleaned = text.strip()
    if not cleaned:
        return english.LatinResult(
            text=text,
            phones=[],
            source="empty",
            confidence="low",
        )

    key = _clean_token(cleaned)
    if not key:
        return english.LatinResult(
            text=text,
            phones=[],
            source="roman_nepali_empty",
            confidence="low",
        )

    if english.looks_like_acronym(cleaned):
        phones = english.letter_name_phones(cleaned)
        return english.LatinResult(
            text=text,
            phones=phones,
            source="roman_nepali_acronym",
            confidence="medium",
            decisions=[{
                "type": "code_switch",
                "rule": "roman_nepali_acronym_letter_names",
                "span": text,
                "after": " ".join(phones),
            }],
        )

    loanwords = data.latin_loanwords()
    if key in loanwords:
        phones = list(loanwords[key])
        return english.LatinResult(
            text=text,
            phones=phones,
            source="roman_nepali_table",
            confidence="medium",
            decisions=[{
                "type": "code_switch",
                "rule": "roman_nepali_loanword_table",
                "span": text,
                "after": " ".join(phones),
            }],
        )

    phones = english.fallback_phones(key)
    return english.LatinResult(
        text=text,
        phones=phones,
        source="roman_nepali_rule_fallback",
        confidence="low",
        decisions=[{
            "type": "code_switch",
            "rule": "roman_nepali_rule_fallback",
            "span": text,
            "after": " ".join(phones),
        }],
    )


def _clean_token(token: str) -> str:
    return TOKEN_CLEAN_RE.sub("", token.lower().replace("'", ""))


def _has_nepali_suffix(key: str) -> bool:
    return any(
        len(key) > len(suffix) + 2 and key.endswith(suffix)
        for suffix in NE_ROMAN_SUFFIXES
    )
