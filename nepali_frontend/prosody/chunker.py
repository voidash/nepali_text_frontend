"""Streaming-safe chunker.

Splits a token stream into chunks at sentence-end punctuation.
Each chunk carries:

- `id`: chunk index within the input
- `tokens`: contiguous slice of token IDs
- `text`: source-text span
- `boundary_strength`: 'sentence' (after ।, !, ?) | 'phrase' (after ,)
  | 'soft' (after a long run of words without punctuation)
- `sentence_type`: 'declarative' | 'yes_no_question' | 'wh_question'
  | 'imperative' | 'exclamation' | 'unknown'
- `intonation_hint`: 'falling' | 'rising' | 'rise_fall' | 'fall_rise'
  | 'unknown'

Chunking is conservative: no split inside a Devanagari word, never
across a digit run, never inside a Latin run. Punctuation is the
primary boundary cue for v0.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from ..tokenize.script import Token

# Wh-question initial words in Nepali. `के` and `को` are excluded
# from the unambiguous set because they double as yes/no question
# markers ("Are you…?") — without semantic context, default to
# yes/no for those.
WH_INITIAL_UNAMBIGUOUS = {"कहाँ", "कहिले", "किन", "कसरी", "कुन", "कति"}


@dataclass
class Chunk:
    id: int
    token_ids: list[int]
    text: str
    boundary_strength: str = "soft"
    sentence_type: str = "unknown"
    intonation_hint: str = "unknown"
    safe_streaming_break_after: bool = False


def chunk(tokens: list[Token], *, max_words: int = 20) -> list[Chunk]:
    """Split tokens into chunks. Splits at sentence-end punctuation."""
    chunks: list[Chunk] = []
    cur_ids: list[int] = []
    cur_word_count = 0
    cur_start: int | None = None

    def emit(boundary: str, sentence_type: str, hint: str) -> None:
        nonlocal cur_ids, cur_word_count, cur_start
        if not cur_ids:
            return
        text_start = tokens[cur_ids[0]].span[0]
        text_end = tokens[cur_ids[-1]].span[1]
        # Reconstruct chunk text by joining consecutive token texts
        text = "".join(tokens[i].text for i in cur_ids)
        chunks.append(Chunk(
            id=len(chunks),
            token_ids=list(cur_ids),
            text=text,
            boundary_strength=boundary,
            sentence_type=sentence_type,
            intonation_hint=hint,
            safe_streaming_break_after=(boundary == "sentence"),
        ))
        cur_ids = []
        cur_word_count = 0
        cur_start = None

    for idx, tok in enumerate(tokens):
        cur_ids.append(idx)
        if tok.kind in ("devanagari", "latin", "digit"):
            cur_word_count += 1
        if tok.kind == "sentence_end":
            stype, hint = _classify_sentence(tokens, cur_ids)
            emit("sentence", stype, hint)
        elif tok.kind == "question":
            stype, hint = _classify_question(tokens, cur_ids)
            emit("sentence", stype, hint)
        elif tok.kind == "exclamation":
            emit("sentence", "exclamation", "fall")
        elif tok.kind == "punct" and tok.text == ",":
            emit("phrase", "unknown", "unknown")
        elif cur_word_count >= max_words:
            emit("soft", "unknown", "unknown")
    if cur_ids:
        emit("sentence", "unknown", "unknown")
    return chunks


def _first_devanagari_word(tokens: list[Token], ids: list[int]) -> str | None:
    for i in ids:
        if tokens[i].kind == "devanagari":
            return tokens[i].text
    return None


def _classify_question(tokens: list[Token], ids: list[int]) -> tuple[str, str]:
    """Identify wh- vs yes-no question by initial word."""
    head = _first_devanagari_word(tokens, ids)
    if head and head in WH_INITIAL_UNAMBIGUOUS:
        return "wh_question", "fall"
    return "yes_no_question", "rise"


def _classify_sentence(tokens: list[Token], ids: list[int]) -> tuple[str, str]:
    """Default sentence classifier for danda-terminated sentences."""
    head = _first_devanagari_word(tokens, ids)
    if head and head in WH_INITIAL_UNAMBIGUOUS:
        return "wh_question", "fall"
    return "declarative", "fall"
