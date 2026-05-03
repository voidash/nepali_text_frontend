"""Frontend trace emitter (per docs/frontend-trace-contract.md)."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

from . import __version__
from .g2p.phonemizer import WordResult


@dataclass
class FrontendTrace:
    input: str
    normalized_text: str
    tokens: list[dict] = field(default_factory=list)
    phones: list[dict] = field(default_factory=list)
    chunks: list[dict] = field(default_factory=list)
    decisions: list[dict] = field(default_factory=list)
    warnings: list[dict] = field(default_factory=list)
    versions: dict[str, str] = field(default_factory=dict)

    def to_json(self, indent: int | None = 2) -> str:
        return json.dumps(self._asdict(), ensure_ascii=False, indent=indent)

    def _asdict(self) -> dict[str, Any]:
        return {
            "input": self.input,
            "normalized_text": self.normalized_text,
            "tokens": self.tokens,
            "phones": self.phones,
            "chunks": self.chunks,
            "decisions": self.decisions,
            "warnings": self.warnings,
            "versions": self.versions,
        }


def build_trace(text: str, words: list[WordResult]) -> FrontendTrace:
    """Stitch per-word results into a top-level trace.

    Also tokenises and chunks the input so the trace carries:
      - `tokens`: every token (Devanagari, Latin, digit, punctuation)
      - `phones`: phone groups for Devanagari word tokens
      - `chunks`: prosody-aware chunk boundaries with sentence-type
        and intonation hints

    Validates that every emitted phone is in the v1.0 inventory and
    records `unknown_phone` warnings for any that aren't.
    """
    from . import data as _data
    from .tokenize import script as _tk
    from .normalize import text as _text_norm
    from .prosody import chunker as _ch
    tokens = []
    phones = []
    decisions = []
    warnings = []

    # Normalize numbers etc. before chunking, so verbalised words
    # appear in chunk text.
    norm_text, norm_decisions = _text_norm.normalize(text)
    decisions.extend(norm_decisions)
    typed = _tk.tokenize(norm_text)
    chunk_objs = _ch.chunk(typed)
    chunks = [
        {
            "id": c.id,
            "token_ids": c.token_ids,
            "text": c.text,
            "boundary_strength": c.boundary_strength,
            "sentence_type": c.sentence_type,
            "intonation_hint": c.intonation_hint,
            "safe_streaming_break_after": c.safe_streaming_break_after,
        }
        for c in chunk_objs
    ]

    cursor = 0
    for tok_id, w in enumerate(words):
        # Find the word's span in the input (best-effort; first match after cursor)
        start = text.find(w.text, cursor)
        if start < 0:
            start = cursor
        end = start + len(w.text)
        cursor = end

        tokens.append({
            "id": tok_id,
            "raw": w.text,
            "normalized": w.text,
            "span": [start, end],
            "script": "devanagari",
            "language": "ne",
            "semiotic_class": "word",
            "protected_span": False,
            "status": "lexicon" if w.source == "lexicon" else
                      "rule" if w.source == "g2p_rule" else
                      "needs_review" if w.source == "unknown" else
                      w.source,
        })
        phones.append({
            "token_id": tok_id,
            "phones": w.phones,
            "source": w.source,
            "style": "spoken_nepali",
            "confidence": w.confidence,
        })
        for d in w.decisions:
            d2 = dict(d)
            d2["token_id"] = tok_id
            decisions.append(d2)
        if w.source == "g2p_rule" and not w.phones:
            warnings.append({
                "code": "unknown_token", "token_id": tok_id, "span": w.text,
            })
        for p in w.phones:
            if p == ".":
                continue  # syllable boundary, not a phone
            # Strip a gemination length marker before checking
            base = p[:-1] if p.endswith(":") else p
            if not _data.is_phone(base):
                warnings.append({
                    "code": "unknown_phone", "token_id": tok_id,
                    "span": w.text, "phone": p,
                })

    return FrontendTrace(
        input=text,
        normalized_text=norm_text,
        tokens=tokens,
        phones=phones,
        chunks=chunks,
        decisions=decisions,
        warnings=warnings,
        versions={
            "frontend": __version__,
            "phone_inventory": "1.0",
            "lexicon": "candidates_google_ne_lr_2018",
            "normalization_config": "spoken_nepali",
        },
    )
