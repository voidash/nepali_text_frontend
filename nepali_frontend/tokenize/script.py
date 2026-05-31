"""Token classifier and script tagger.

Walks a normalized text string and emits a sequence of typed tokens.
Each token carries:

- `text`: source span text
- `span`: (start, end) character offsets in the original input
- `kind`: one of 'devanagari' | 'latin' | 'digit' | 'punct' |
  'question' | 'exclamation' | 'sentence_end' | 'space' | 'other'
- `language`: 'ne' | 'en' | 'unknown' (heuristic only at v0)

This is a thin classifier — it does not phonemize. The phonemizer
calls this to split mixed-script input.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from ..g2p import base_map as bm

DEVA_RUN = re.compile(r"[ऀ-ॣॲ-ॿ]+")
LATIN_RUN = re.compile(r"[A-Za-z]+(?:[A-Za-z0-9]*)(?:[-'][A-Za-z0-9]+)*")
DIGIT_RUN = re.compile(r"[०-९\d]+")
WHITESPACE_RUN = re.compile(r"\s+")

# Sentence-final punctuation
SENTENCE_END = {bm.DANDA, bm.DOUBLE_DANDA, ".", "!", "?", "।", "॥"}


@dataclass
class Token:
    text: str
    span: tuple[int, int]
    kind: str
    language: str = "unknown"


def tokenize(text: str) -> list[Token]:
    """Split a string into typed tokens. Lossless on character spans."""
    out: list[Token] = []
    i = 0
    n = len(text)
    while i < n:
        ch = text[i]
        # Whitespace run
        if ch.isspace():
            m = WHITESPACE_RUN.match(text, i)
            out.append(Token(m.group(0), (m.start(), m.end()), "space"))
            i = m.end()
            continue
        # Devanagari run
        if "ऀ" <= ch <= "ॿ" and not bm.is_devanagari_digit(ch) \
                and ch not in (bm.DANDA, bm.DOUBLE_DANDA):
            m = DEVA_RUN.match(text, i)
            out.append(Token(m.group(0), (m.start(), m.end()), "devanagari", "ne"))
            i = m.end()
            continue
        # Devanagari digit run
        if bm.is_devanagari_digit(ch):
            m = DIGIT_RUN.match(text, i)
            out.append(Token(m.group(0), (m.start(), m.end()), "digit", "ne"))
            i = m.end()
            continue
        # ASCII digit run
        if ch.isdigit():
            m = DIGIT_RUN.match(text, i)
            out.append(Token(m.group(0), (m.start(), m.end()), "digit", "unknown"))
            i = m.end()
            continue
        # Latin run
        if ch.isascii() and ch.isalpha():
            m = LATIN_RUN.match(text, i)
            out.append(Token(m.group(0), (m.start(), m.end()), "latin", "en"))
            i = m.end()
            continue
        # Sentence-final punctuation
        if ch in SENTENCE_END:
            kind = (
                "question" if ch == "?"
                else "exclamation" if ch == "!"
                else "sentence_end"
            )
            out.append(Token(ch, (i, i + 1), kind))
            i += 1
            continue
        # Anything else
        out.append(Token(ch, (i, i + 1), "punct"))
        i += 1
    return out
