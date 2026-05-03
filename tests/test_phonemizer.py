"""Phonemizer orchestrator tests."""

from __future__ import annotations

from nepali_frontend.g2p import phonemizer as ph


def test_lexicon_hit_returns_high_confidence():
    # आज is in the candidate lexicon.
    r = ph.phonemize_word("आज")
    assert r.source == "lexicon"
    assert r.confidence == "high"
    assert r.phones, "lexicon hit should return non-empty phones"


def test_unknown_word_falls_through_to_g2p_rule():
    # A made-up word unlikely to be in the lexicon
    r = ph.phonemize_word("ज़्ज़्क्ष़")
    assert r.source in ("g2p_rule", "suffix_strip")


def test_suffix_strip_when_root_in_lexicon():
    # Pick a root we know is in the lexicon and append a case suffix.
    # If the lexicon has "नेपाल" we can test "नेपालले" or "नेपालमा".
    from nepali_frontend import data
    lex = data.lexicon()
    # Find a sample root that's in the lexicon and short enough
    candidate_root = None
    for word in ("नेपाल", "राम", "घर", "आज"):
        if word in lex:
            candidate_root = word
            break
    if candidate_root is None:
        return  # skip if none of the common ones are present
    inflected = candidate_root + "मा"
    if inflected in lex:
        return  # the inflected form is itself in the lexicon, skip
    r = ph.phonemize_word(inflected)
    assert r.source == "suffix_strip"
    assert r.phones


def test_phonemize_text_splits_words():
    results = ph.phonemize_text("राम र सीता।")
    # Three Devanagari words
    assert len(results) == 3
    for r in results:
        assert r.phones
