"""Unified Nepali TTS frontend pipeline.

This is the runtime-facing API: normalize raw text, tokenize by script,
phonemize Nepali and Latin/code-switched spans, keep punctuation as prosody
tokens, and emit a JSON-serializable trace.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from .code_switch import english, roman_nepali
from .g2p import phonemizer as base_phonemizer
from .normalize import text as text_norm
from .prosody import chunker
from .tokenize import script as tokenizer


PUNCT_PHONES = {
    "sentence_end": ["sent"],
    "question": ["sent"],
    "exclamation": ["sent"],
    "punct:,": ["brk"],
    "punct:;": ["brk"],
    "punct::": ["brk"],
}


@dataclass
class TokenResult:
    id: int
    raw: str
    normalized: str
    span: tuple[int, int]
    kind: str
    language: str
    semiotic_class: str
    phones: list[str] = field(default_factory=list)
    source: str = ""
    confidence: str = ""
    status: str = ""
    decisions: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class FrontendResult:
    input: str
    normalized_text: str
    profile: str
    tokens: list[TokenResult] = field(default_factory=list)
    phone_sequence: list[str] = field(default_factory=list)
    chunks: list[dict[str, Any]] = field(default_factory=list)
    decisions: list[dict[str, Any]] = field(default_factory=list)
    warnings: list[dict[str, Any]] = field(default_factory=list)

    def asdict(self) -> dict[str, Any]:
        return {
            "input": self.input,
            "normalized_text": self.normalized_text,
            "profile": self.profile,
            "tokens": [asdict(token) for token in self.tokens],
            "phone_sequence": self.phone_sequence,
            "chunks": self.chunks,
            "decisions": self.decisions,
            "warnings": self.warnings,
        }


def process(
    text: str,
    *,
    profile: str = "real_nepali",
    normalize: bool = True,
    include_punctuation: bool = True,
) -> FrontendResult:
    """Run the full frontend over raw text."""
    normalized_text, norm_decisions = text_norm.normalize(text) if normalize else (text, [])
    typed_tokens = tokenizer.tokenize(normalized_text)
    roman_nepali_spans = _roman_nepali_spans(typed_tokens)
    chunk_objs = chunker.chunk(typed_tokens)

    result = FrontendResult(
        input=text,
        normalized_text=normalized_text,
        profile=profile,
        decisions=list(norm_decisions),
        chunks=[
            {
                "id": chunk.id,
                "token_ids": chunk.token_ids,
                "text": chunk.text,
                "boundary_strength": chunk.boundary_strength,
                "sentence_type": chunk.sentence_type,
                "intonation_hint": chunk.intonation_hint,
                "safe_streaming_break_after": chunk.safe_streaming_break_after,
            }
            for chunk in chunk_objs
        ],
    )

    for token_index, tok in enumerate(typed_tokens):
        if tok.kind == "space":
            continue
        token_result = _process_token(
            tok,
            profile=profile,
            include_punctuation=include_punctuation,
            roman_nepali_decision=roman_nepali_spans.get(token_index),
        )
        token_result.id = len(result.tokens)
        result.tokens.append(token_result)
        result.phone_sequence.extend(token_result.phones)
        for decision in token_result.decisions:
            decision = dict(decision)
            decision["token_id"] = token_result.id
            result.decisions.append(decision)
        result.warnings.extend(_warnings_for_token(token_result))

    return result


def _process_token(
    tok: tokenizer.Token,
    *,
    profile: str,
    include_punctuation: bool,
    roman_nepali_decision: dict[str, Any] | None = None,
) -> TokenResult:
    if tok.kind == "devanagari":
        word = _phonemize_devanagari(tok.text, profile=profile)
        return TokenResult(
            id=-1,
            raw=tok.text,
            normalized=tok.text,
            span=tok.span,
            kind=tok.kind,
            language="ne",
            semiotic_class="word",
            phones=list(word.phones),
            source=word.source,
            confidence=word.confidence,
            status="ok" if word.phones else "needs_review",
            decisions=list(word.decisions),
        )

    if tok.kind == "latin":
        is_roman_nepali = roman_nepali_decision is not None
        latin = (
            roman_nepali.phonemize_roman_nepali(tok.text)
            if is_roman_nepali
            else english.phonemize_latin(tok.text)
        )
        phones = _rewrite_for_profile(latin.phones, profile)
        decisions = list(latin.decisions)
        if roman_nepali_decision is not None:
            decisions.insert(0, dict(roman_nepali_decision))
        if phones != latin.phones:
            decisions.append({
                "type": "dialect_profile",
                "rule": "profile_rewrite_on_latin_span",
                "span": tok.text,
                "before": " ".join(latin.phones),
                "after": " ".join(phones),
                "profile": profile,
            })
        return TokenResult(
            id=-1,
            raw=tok.text,
            normalized=tok.text,
            span=tok.span,
            kind=tok.kind,
            language="ne_roman" if is_roman_nepali else "en",
            semiotic_class="roman_nepali_word" if is_roman_nepali else "latin_word",
            phones=phones,
            source=latin.source,
            confidence=latin.confidence,
            status="review" if latin.confidence == "low" else "ok",
            decisions=decisions,
        )

    if tok.kind == "digit":
        return TokenResult(
            id=-1,
            raw=tok.text,
            normalized=tok.text,
            span=tok.span,
            kind=tok.kind,
            language=tok.language,
            semiotic_class="digit",
            phones=[],
            source="unnormalized_digit",
            confidence="low",
            status="needs_review",
        )

    punct_key = f"punct:{tok.text}" if tok.kind == "punct" else tok.kind
    phones = PUNCT_PHONES.get(punct_key, []) if include_punctuation else []
    return TokenResult(
        id=-1,
        raw=tok.text,
        normalized=tok.text,
        span=tok.span,
        kind=tok.kind,
        language="unknown",
        semiotic_class="punctuation",
        phones=phones,
        source="punctuation",
        confidence="high" if phones else "medium",
        status="ok",
    )


def _phonemize_devanagari(text: str, *, profile: str):
    if profile in ("real_nepali", "standard_clear_nepali"):
        from real_nepali import g2p as real_g2p

        return real_g2p.phonemize_word(text, profile=profile)
    if profile in ("base", "spoken_nepali"):
        return base_phonemizer.phonemize_word(text)
    raise ValueError(f"unknown frontend profile: {profile}")


def _rewrite_for_profile(phones: list[str], profile: str) -> list[str]:
    if profile not in ("real_nepali", "standard_clear_nepali"):
        return list(phones)
    from real_nepali.profiles import get_profile

    prof = get_profile(profile)
    return [prof.rewrite_phone(phone) for phone in phones]


def _roman_nepali_spans(tokens: list[tokenizer.Token]) -> dict[int, dict[str, Any]]:
    out: dict[int, dict[str, Any]] = {}
    run: list[tuple[int, tokenizer.Token]] = []

    def flush() -> None:
        if not run:
            return
        classification = roman_nepali.classify_tokens([token.text for _, token in run])
        if classification.is_roman_nepali:
            span_text = " ".join(token.text for _, token in run)
            decision = classification.as_decision(span_text)
            for token_index, _ in run:
                out[token_index] = decision
        run.clear()

    for token_index, token in enumerate(tokens):
        if token.kind == "latin":
            run.append((token_index, token))
            continue
        if token.kind == "space" and run:
            continue
        flush()
    flush()
    return out


def _warnings_for_token(token: TokenResult) -> list[dict[str, Any]]:
    warnings: list[dict[str, Any]] = []
    if token.status == "needs_review":
        warnings.append({
            "code": "needs_review",
            "token_id": token.id,
            "span": token.raw,
            "kind": token.kind,
        })
    if token.kind == "latin" and token.confidence == "low":
        warnings.append({
            "code": (
                "low_confidence_roman_nepali"
                if token.language == "ne_roman"
                else "low_confidence_latin"
            ),
            "token_id": token.id,
            "span": token.raw,
        })
    return warnings
