"""Clear-standard Nepali G2P wrapper.

The first implementation deliberately reuses the mature base frontend for the
parts that are not dialect-specific: lexicon lookup, suffix stripping, schwa
deletion, anusvara resolution, gemination, and text normalization. We then
rewrite only the phone labels whose acoustic target should differ for the new
clear-standard Nepali voice.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass, field
from typing import Iterable

from nepali_frontend.g2p import phonemizer as base_phonemizer

from .profiles import STANDARD_CLEAR_NEPALI, DialectProfile, get_profile


@dataclass
class WordResult:
    """Result of phonemizing one word under a real_nepali profile."""

    text: str
    phones: list[str] = field(default_factory=list)
    source: str = "unknown"
    confidence: str = "low"
    profile: str = STANDARD_CLEAR_NEPALI.name
    base_phones: list[str] = field(default_factory=list)
    decisions: list[dict] = field(default_factory=list)


def _rewrite_phones(phones: Iterable[str], profile: DialectProfile) -> list[str]:
    return [profile.rewrite_phone(p) for p in phones]


def _copy_decisions(decisions: Iterable[dict]) -> list[dict]:
    return [dict(d) for d in decisions]


def phonemize_word(
    text: str,
    *,
    profile: str | DialectProfile = STANDARD_CLEAR_NEPALI.name,
) -> WordResult:
    """Convert one Devanagari word to clear-standard Nepali phone labels."""
    prof = get_profile(profile) if isinstance(profile, str) else profile
    base = base_phonemizer.phonemize_word(text, style="spoken_nepali")
    phones = _rewrite_phones(base.phones, prof)
    decisions = _copy_decisions(base.decisions)
    if phones != base.phones:
        decisions.append({
            "type": "dialect_profile",
            "rule": "clear_standard_affricates",
            "span": text,
            "before": " ".join(base.phones),
            "after": " ".join(phones),
            "profile": prof.name,
        })
    return WordResult(
        text=text,
        phones=phones,
        source=base.source,
        confidence=base.confidence,
        profile=prof.name,
        base_phones=list(base.phones),
        decisions=decisions,
    )


def phonemize_text(
    text: str,
    *,
    profile: str | DialectProfile = STANDARD_CLEAR_NEPALI.name,
    normalize: bool = True,
) -> list[WordResult]:
    """Tokenize and phonemize text under a real_nepali profile."""
    prof = get_profile(profile) if isinstance(profile, str) else profile
    base_words = base_phonemizer.phonemize_text(
        text,
        style="spoken_nepali",
        normalize=normalize,
    )
    out: list[WordResult] = []
    for base in base_words:
        phones = _rewrite_phones(base.phones, prof)
        decisions = _copy_decisions(base.decisions)
        if phones != base.phones:
            decisions.append({
                "type": "dialect_profile",
                "rule": "clear_standard_affricates",
                "span": base.text,
                "before": " ".join(base.phones),
                "after": " ".join(phones),
                "profile": prof.name,
            })
        out.append(WordResult(
            text=base.text,
            phones=phones,
            source=base.source,
            confidence=base.confidence,
            profile=prof.name,
            base_phones=list(base.phones),
            decisions=decisions,
        ))
    return out


def _format_plain(results: list[WordResult]) -> str:
    return "\n".join(f"{r.text}\t{' '.join(r.phones)}" for r in results)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("text", nargs="+", help="Nepali text to phonemize")
    parser.add_argument("--profile", default=STANDARD_CLEAR_NEPALI.name)
    parser.add_argument("--no-normalize", action="store_true")
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args(argv)

    text = " ".join(args.text)
    results = phonemize_text(
        text,
        profile=args.profile,
        normalize=not args.no_normalize,
    )
    if args.as_json:
        print(json.dumps([asdict(r) for r in results], ensure_ascii=False, indent=2))
    else:
        print(_format_plain(results))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

