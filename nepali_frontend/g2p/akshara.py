"""Devanagari akshara parser.

Parses a Devanagari string into a sequence of orthographic units
(`Akshara`s). Each unit carries its source span, its parsed
components, and the base phones it maps to (before post-rules).

The parser handles:

- Independent vowels (with optional anusvara/chandrabindu/visarga)
- Consonant + matra + modifier syllables
- Conjuncts (consonant + virama + consonant + ...)
- Nukta-marked consonants (फ़ ज़ etc.)
- Word-final virama (halant) — suppresses inherent vowel
- Devanagari digits, dandas, and unknown characters (passed through)

It does NOT apply:

- Schwa deletion (use post_rules.apply_schwa_deletion)
- Anusvara contextual resolution (use post_rules.apply_anusvara_context)
- Suffix-strip morphology (use post_rules.apply_suffix_strip)

Reference:
- Khatiwada 2009 — IPA Handbook illustration of Nepali
- Regmi 2025 — Variation in Nepali Verb Roots (orthography↔phonology)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from . import base_map as bm


@dataclass
class Akshara:
    """One orthographic unit produced by the parser.

    `phones` is the base-map output (no schwa deletion, no contextual
    nasal resolution). Post-rules transform it further.
    """

    type: str                   # 'vowel' | 'syllable' | 'digit' | 'punct' | 'sign' | 'other'
    text: str                   # source span (the Devanagari characters consumed)
    span: tuple[int, int]       # (start, end_exclusive) in original string
    phones: list[str] = field(default_factory=list)
    components: dict = field(default_factory=dict)
    notes: str = ""


def parse(text: str) -> list[Akshara]:
    """Parse a Devanagari string into a list of Aksharas.

    Lossless of the source — every character lands in exactly one
    Akshara via its `span`. The output `phones` is the *base* phone
    sequence without post-rule application.
    """
    out: list[Akshara] = []
    n = len(text)
    i = 0
    while i < n:
        ch = text[i]

        # 1. Independent vowel
        if bm.is_independent_vowel(ch):
            phones, components, j = _parse_independent_vowel(text, i)
            out.append(Akshara(
                type="vowel",
                text=text[i:j],
                span=(i, j),
                phones=phones,
                components=components,
            ))
            i = j
            continue

        # 2. Consonant (start of a syllable, possibly conjunct)
        if bm.is_consonant(ch):
            phones, components, j = _parse_syllable(text, i)
            out.append(Akshara(
                type="syllable",
                text=text[i:j],
                span=(i, j),
                phones=phones,
                components=components,
            ))
            i = j
            continue

        # 3. Standalone modifier (anusvara/chandrabindu/visarga without preceding letter)
        if bm.is_modifier(ch):
            out.append(Akshara(
                type="sign",
                text=ch,
                span=(i, i + 1),
                phones=[],
                notes=f"standalone {ch!r}",
            ))
            i += 1
            continue

        # 4. Devanagari digit (passed through; verbalizer handles)
        if bm.is_devanagari_digit(ch):
            out.append(Akshara(
                type="digit",
                text=ch,
                span=(i, i + 1),
                phones=[],
                components={"value": bm.DIGIT_NAME[ch]},
            ))
            i += 1
            continue

        # 5. Danda or double-danda
        if ch in (bm.DANDA, bm.DOUBLE_DANDA):
            out.append(Akshara(
                type="punct",
                text=ch,
                span=(i, i + 1),
                phones=[],
            ))
            i += 1
            continue

        # 6. Anything else — whitespace, ASCII, ZWJ/ZWNJ, unknown
        out.append(Akshara(
            type="other",
            text=ch,
            span=(i, i + 1),
            phones=[],
        ))
        i += 1
    return out


# ---- internal helpers ----------------------------------------------------


def _parse_independent_vowel(text: str, i: int) -> tuple[list[str], dict, int]:
    ch = text[i]
    base = bm.INDEPENDENT_VOWEL[ch]
    phones = base.split()
    components: dict = {"vowel": ch, "modifiers": []}
    j = i + 1

    # Collect trailing modifiers (anusvara, chandrabindu, visarga)
    while j < len(text) and bm.is_modifier(text[j]):
        m = text[j]
        components["modifiers"].append(m)
        j += 1

    # Apply nasalization (default: vowel nasalization for chandrabindu;
    # anusvara is contextual but at start-of-word with no following consonant
    # it is also vowel nasalization).
    if any(m in (bm.CHANDRABINDU, bm.ANUSVARA) for m in components["modifiers"]):
        if phones:
            last = phones[-1]
            phones[-1] = bm.NASALIZE.get(last, last)

    if bm.VISARGA in components["modifiers"]:
        phones.append("h")

    return phones, components, j


def _parse_syllable(text: str, i: int) -> tuple[list[str], dict, int]:
    """Parse one consonant-headed syllable, possibly a conjunct."""
    n = len(text)
    consonants: list[dict] = []
    j = i

    # Collect: consonant ( + nukta ) ( + virama + consonant ( + nukta ) )*
    while j < n and bm.is_consonant(text[j]):
        c = text[j]
        j += 1
        has_nukta = j < n and text[j] == bm.NUKTA
        if has_nukta:
            j += 1
        consonants.append({"char": c, "nukta": has_nukta})
        # If virama follows, this is a conjunct — consume the virama and
        # continue collecting consonants.
        if j < n and text[j] == bm.VIRAMA:
            # Look ahead: is the next char a consonant? If yes, conjunct
            # continues. If no, the virama is word-final (halant); break
            # the loop with no further consonant.
            if j + 1 < n and bm.is_consonant(text[j + 1]):
                j += 1  # consume virama, continue
                continue
            else:
                # Word-final virama or virama before non-consonant
                j += 1  # consume the virama
                # No more consonants follow; vowel will be None below.
                break
        else:
            # No virama → end of conjunct, vowel/matra follows
            break

    # Determine vowel: matra, inherent ax, or no vowel (final virama)
    vowel_phones: list[str] = []
    matra: Optional[str] = None
    final_virama = j > i and text[j - 1] == bm.VIRAMA

    if not final_virama:
        if j < n and bm.is_matra(text[j]):
            matra = text[j]
            vowel_phones = bm.MATRA[matra].split()
            j += 1
        else:
            # Inherent vowel (will be subject to schwa deletion in post-rules)
            vowel_phones = ["ax"]

    # Collect modifiers after vowel (anusvara, chandrabindu, visarga)
    modifiers: list[str] = []
    while j < n and bm.is_modifier(text[j]):
        modifiers.append(text[j])
        j += 1

    # Build phones for the consonants (apply nukta transforms)
    cons_phones: list[str] = []
    for cons in consonants:
        base = bm.CONSONANT.get(cons["char"], "?")
        if cons["nukta"]:
            base = bm.NUKTA_TRANSFORM.get(base, base)
        cons_phones.append(base)

    # Assemble: consonant cluster + vowel
    phones = list(cons_phones) + list(vowel_phones)

    # Apply chandrabindu: vowel nasalization on the last vowel phone
    has_chandrabindu = bm.CHANDRABINDU in modifiers
    has_anusvara = bm.ANUSVARA in modifiers
    has_visarga = bm.VISARGA in modifiers

    if has_chandrabindu and vowel_phones:
        last = phones[-1]
        phones[-1] = bm.NASALIZE.get(last, last)

    # Anusvara: default — nasalize the vowel. The contextual rule
    # (nasal consonant before homorganic plosive) applies cross-syllable
    # and is therefore deferred to post_rules.apply_anusvara_context.
    if has_anusvara and vowel_phones:
        last = phones[-1]
        phones[-1] = bm.NASALIZE.get(last, last)

    if has_visarga:
        phones.append("h")

    components = {
        "consonants": consonants,
        "matra": matra,
        "final_virama": final_virama,
        "modifiers": modifiers,
        "inherent_vowel": (not final_virama and matra is None),
    }
    return phones, components, j


def render(aksharas: list[Akshara]) -> str:
    """Render aksharas back to a phone-string for inspection."""
    parts = []
    for a in aksharas:
        if a.phones:
            parts.append(" ".join(a.phones))
    return " ".join(parts)
