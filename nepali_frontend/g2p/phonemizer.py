"""Phonemizer orchestrator.

Pipeline for a single word:

  Devanagari word
    → lexicon lookup       (if hit, return validated phones)
    → suffix-strip         (if root in lexicon, return root + suffix phones)
    → akshara parse        (Devanagari → orthographic units → base phones)
    → post-rules           (gemination → anusvara context → schwa deletion)
    → phones + trace decisions

The phonemizer is deterministic. Lexicon hits are highest-priority
(validated against project policy). Suffix-strip is the second tier
(structurally aligned with Nepali agglutinative morphology). Rule
G2P is the fallback.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .. import data
from . import akshara as ak
from . import post_rules as pr


@dataclass
class WordResult:
    """Result of phonemizing one word."""
    text: str
    phones: list[str] = field(default_factory=list)
    source: str = "unknown"           # 'lexicon' | 'suffix_strip' | 'g2p_rule' | 'unknown'
    confidence: str = "low"           # 'high' | 'medium' | 'low'
    decisions: list[dict] = field(default_factory=list)
    aksharas: list[ak.Akshara] = field(default_factory=list)


def phonemize_word(text: str, *, style: str = "spoken_nepali") -> WordResult:
    """Convert a single Devanagari word to phones.

    Style is currently only `spoken_nepali` (default). Other modes
    will use different base maps and post-rule sets.
    """
    if style != "spoken_nepali":
        raise NotImplementedError(f"style={style!r} not implemented in v0")

    lex = data.lexicon()
    decisions: list[dict] = []

    # 1. Lexicon hit (highest confidence)
    if text in lex:
        raw = list(lex[text])
        # Apply the anusvara contextual rule even on lexicon entries —
        # Google's source did not pre-apply it, but our v1.0 policy
        # requires it. This brings lexicon-path phones in line with
        # rule-path phones for words like अंग.
        promoted, dec_a = pr.apply_anusvara_to_phone_list(raw)
        decisions = [{
            "type": "lexicon_lookup", "rule": "exact_match",
            "span": text, "after": " ".join(promoted),
            "source": "google_ne_lr_2018:candidate",
        }]
        decisions.extend(dec_a)
        return WordResult(
            text=text, phones=promoted,
            source="lexicon", confidence="high", decisions=decisions,
        )

    # 2. Suffix-strip via lexicon
    strip = pr.try_suffix_strip(text, lex)
    if strip is not None:
        root, suffix, root_phones = strip
        # Phonemize suffix via the rule path (suffixes are short, well-behaved)
        suffix_phones = _g2p_rule_phones(suffix)
        decisions.append({
            "type": "post_rule", "rule": "suffix_strip",
            "span": text,
            "before": text,
            "after": f"{root} + {suffix}",
            "root_phones": " ".join(root_phones),
            "suffix_phones": " ".join(suffix_phones),
        })
        # Concatenate; if last token of root is a syllable boundary, drop it
        merged = list(root_phones)
        if merged and merged[-1] == ".":
            merged.pop()
        # Insert syllable boundary between root and suffix
        if merged and suffix_phones:
            merged.append(".")
        merged.extend(suffix_phones)
        return WordResult(
            text=text, phones=merged, source="suffix_strip",
            confidence="medium", decisions=decisions,
        )

    # 3. Full rule G2P
    aksharas = ak.parse(text)
    aksharas, dec_d = pr.apply_diphthong_contraction(aksharas)
    aksharas, dec_g = pr.apply_gemination(aksharas)
    aksharas, dec_a = pr.apply_anusvara_context(aksharas)
    aksharas, dec_c = pr.apply_compound_schwa(text, aksharas, lex)
    aksharas, dec_s = pr.apply_schwa_deletion(text, aksharas)
    decisions.extend(dec_d + dec_g + dec_a + dec_c + dec_s)

    phones = []
    for a in aksharas:
        if a.phones:
            phones.extend(a.phones)
    decisions.insert(0, {
        "type": "akshara_parse", "rule": "rule_g2p_default",
        "span": text, "after": " ".join(phones),
    })

    return WordResult(
        text=text, phones=phones, source="g2p_rule",
        confidence="low", decisions=decisions, aksharas=aksharas,
    )


def _g2p_rule_phones(text: str) -> list[str]:
    """Internal: rule-only G2P, used for cross-validation and suffix-strip suffixes."""
    lex = data.lexicon()
    aksharas = ak.parse(text)
    aksharas, _ = pr.apply_diphthong_contraction(aksharas)
    aksharas, _ = pr.apply_gemination(aksharas)
    aksharas, _ = pr.apply_anusvara_context(aksharas)
    aksharas, _ = pr.apply_compound_schwa(text, aksharas, lex)
    aksharas, _ = pr.apply_schwa_deletion(text, aksharas)
    phones: list[str] = []
    for a in aksharas:
        if a.phones:
            phones.extend(a.phones)
    return phones


def phonemize_text(text: str, *, style: str = "spoken_nepali",
                    normalize: bool = True) -> list[WordResult]:
    """Tokenize on whitespace + punctuation and phonemize each word.

    By default the input is first text-normalized (numbers verbalized).
    Set `normalize=False` to skip and feed raw input straight to G2P.

    The word pattern excludes the Devanagari punctuation/digit block
    (U+0964 danda, U+0965 double-danda, U+0966-U+096F digits) so that
    "हो।" tokenises as `हो` (lexicon hit) plus a separate punctuation
    token, and `२९` is verbalized to its word form before lookup.
    """
    import re
    if normalize:
        from ..normalize import text as _text_norm
        text, _ = _text_norm.normalize(text)
    word_pattern = re.compile(r"[ऀ-ॣॲ-ॿ]+")
    return [phonemize_word(w, style=style) for w in word_pattern.findall(text)]
