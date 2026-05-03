"""Devanagari grapheme → project phone label mappings (default mode).

Tracks Khatiwada (2009) IPA Handbook chart and project pronunciation
policy v1.0. The mappings encode the policy's collapse decisions
(श/ष/स → s; ञ/ण → n; ी/ू orthographic length collapsed to i/u).

Careful_sanskritized and loan-aware modes apply different mappings;
those are not implemented in v0 default.
"""

from __future__ import annotations

# ---- Unicode constants ----------------------------------------------------

CHANDRABINDU = "ँ"  # ँ
ANUSVARA = "ं"      # ं
VISARGA = "ः"       # ः
NUKTA = "़"         # ़
VIRAMA = "्"        # ्
DANDA = "।"         # ।
DOUBLE_DANDA = "॥"  # ॥
ZWJ = "‍"
ZWNJ = "‌"

# ---- Independent vowels --------------------------------------------------
# Phones may be multi-token (e.g. ऋ → "r i"). Caller splits on whitespace.
INDEPENDENT_VOWEL: dict[str, str] = {
    "अ": "ax",    # अ
    "आ": "aa",    # आ
    "इ": "i",     # इ
    "ई": "i",     # ई — orthographic length, collapsed in default mode
    "उ": "u",     # उ
    "ऊ": "u",     # ऊ — orthographic length, collapsed
    "ऋ": "r i",   # ऋ — vocalic r, realised as /ri/
    "ऌ": "l i",   # ऌ — vocalic l, very rare
    "ए": "e",     # ए
    "ऐ": "axj",   # ऐ — diphthong /ʌi̯/
    "ओ": "o",     # ओ
    "औ": "axw",   # औ — diphthong /ʌu̯/
}

# ---- Vowel matras (dependent vowel signs) --------------------------------
MATRA: dict[str, str] = {
    "ा": "aa",    # ा
    "ि": "i",     # ि
    "ी": "i",     # ी — collapsed
    "ु": "u",     # ु
    "ू": "u",     # ू — collapsed
    "ृ": "r i",   # ृ — vocalic r matra
    "े": "e",     # े
    "ै": "axj",   # ै
    "ो": "o",     # ो
    "ौ": "axw",   # ौ
}

# ---- Consonants (default mode: collapses Sanskrit/loan distinctions) -----
CONSONANT: dict[str, str] = {
    # Velars
    "क": "k",     # क
    "ख": "kh",    # ख
    "ग": "g",     # ग
    "घ": "gh",    # घ
    "ङ": "ng",    # ङ
    # Alveolar affricates (not palatal — Khatiwada 2009)
    "च": "ts",    # च
    "छ": "tsh",   # छ
    "ज": "dz",    # ज
    "झ": "dzh",   # झ
    "ञ": "n",     # ञ — palatal nasal collapses to /n/ in default
    # Retroflex stops (Khatiwada 2019: cacuminal post-alveolar acoustic target)
    "ट": "tx",    # ट
    "ठ": "txh",   # ठ
    "ड": "dx",    # ड
    "ढ": "dxh",   # ढ
    "ण": "n",     # ण — retroflex nasal collapses to /n/ in default
    # Dentals
    "त": "t",     # त
    "थ": "th",    # थ
    "द": "d",     # द
    "ध": "dh",    # ध
    "न": "n",     # न
    # Bilabials
    "प": "p",     # प
    "फ": "ph",    # फ — default; nukta variant फ़ → f via NUKTA_TRANSFORM
    "ब": "b",     # ब
    "भ": "bh",    # भ
    "म": "m",     # म
    # Sonorants and fricatives
    "य": "y",     # य
    "र": "r",     # र
    "ल": "l",     # ल
    "ळ": "l",     # ळ — retroflex lateral; rare in Nepali, mapped to l in default
    "व": "w",     # व — project default w
    "श": "s",     # श — collapses to /s/ in default
    "ष": "s",     # ष — collapses to /s/ in default
    "स": "s",     # स
    "ह": "h",     # ह — IPA /ɦ/
    # Pre-composed nukta consonants (Unicode includes some directly)
    "क़": "k",     # क़ — Persian/Arabic loan, default uses k
    "ख़": "kh",    # ख़
    "ग़": "g",     # ग़
    "ज़": "z",     # ज़ — loan_only phone
    "ड़": "dx",    # ड़ — retroflex flap, project uses dx
    "ढ़": "dxh",   # ढ़
    "फ़": "f",     # फ़ — loan_only phone
    "य़": "y",     # य़
}

# ---- Nukta transformations -----------------------------------------------
# When a base consonant is followed by U+093C nukta, transform.
NUKTA_TRANSFORM: dict[str, str] = {
    "ph": "f",   # फ + ़ → फ़ (English /f/)
    "dz": "z",   # ज + ़ → ज़ (English /z/)
    "tx": "dx",  # ट + ़ → ट़ — variant; treat as retroflex flap
    "dx": "dx",  # ड + ़ → ड़ already a retroflex flap
    "dxh": "dxh",
    "k": "k",    # क़ kept as k in default (loan)
    "kh": "kh",
    "g": "g",
}

# ---- Independent vowels: nasalized counterparts --------------------------
# Used when the parser sees an independent vowel followed by chandrabindu/anusvara.
# Maps oral phone → nasalized phone.
NASALIZE: dict[str, str] = {
    "ax": "axn",
    "aa": "aan",
    "i": "in",
    "u": "un",
    "e": "en",
    "o": "o",       # /õ/ is not phonemic per Khatiwada — no /on/
    "axj": "axjn",
    "axw": "axwn",
    "aaj": "aajn",
    "aaw": "aawn",
    "oj": "ojn",
    "ow": "own",
}

# ---- Devanagari digits → spoken-form Nepali words (placeholder) ----------
# Real verbalization belongs in normalize/verbalizers/ne_numbers.py.
# Here we only expose the digit mapping; verbalizer composes them.
DIGIT_NAME: dict[str, str] = {
    "०": "0",
    "१": "1",
    "२": "2",
    "३": "3",
    "४": "4",
    "५": "5",
    "६": "6",
    "७": "7",
    "८": "8",
    "९": "9",
}


def is_consonant(ch: str) -> bool:
    return ch in CONSONANT


def is_independent_vowel(ch: str) -> bool:
    return ch in INDEPENDENT_VOWEL


def is_matra(ch: str) -> bool:
    return ch in MATRA


def is_modifier(ch: str) -> bool:
    return ch in (CHANDRABINDU, ANUSVARA, VISARGA)


def is_devanagari_digit(ch: str) -> bool:
    return ch in DIGIT_NAME
