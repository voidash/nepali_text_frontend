"""End-to-end frontend tests for normalization, code-switching, and punctuation."""

from __future__ import annotations

from nepali_frontend import frontend
from nepali_frontend.code_switch.english import phonemize_latin
from nepali_frontend.code_switch.roman_nepali import classify_tokens
from real_nepali import g2p


def test_latin_lexicon_word_gets_phones():
    result = phonemize_latin("Facebook")
    assert result.source == "latin_lexicon"
    assert result.phones == ["f", "e", "s", "b", "u", "k"]


def test_latin_acronym_gets_letter_names():
    result = phonemize_latin("AI")
    assert result.source == "latin_lexicon"
    assert result.phones == ["e", "aa", "i"]


def test_latin_loanword_table_before_rule_fallback():
    result = phonemize_latin("school")
    assert result.source == "latin_loanword_table"
    assert result.phones == ["s", "k", "u", "l"]


def test_uppercase_initialism_beats_loanword_table():
    result = phonemize_latin("A")
    assert result.source == "latin_acronym"
    assert result.phones == ["e"]


def test_real_nepali_phonemize_text_keeps_latin_spans():
    rows = g2p.phonemize_text("AI ले Facebook मा login गर्यो।")
    by_text = {row.text: row for row in rows}
    assert {"AI", "Facebook", "login"}.issubset(by_text)
    assert by_text["Facebook"].phones
    assert by_text["login"].source == "latin_lexicon"


def test_frontend_process_normalizes_and_keeps_punctuation():
    result = frontend.process("AI ले २५% growth देखायो.", profile="real_nepali")
    assert "पच्चिस प्रतिशत" in result.normalized_text
    assert any(token.raw == "AI" and token.kind == "latin" for token in result.tokens)
    assert "sent" in result.phone_sequence
    assert result.chunks[0]["sentence_type"] == "declarative"


def test_frontend_unknown_latin_warns_for_review():
    result = frontend.process("यो foobarbaz हो।", profile="real_nepali")
    assert any(warning["code"] == "low_confidence_latin" for warning in result.warnings)


def test_frontend_url_uses_spoken_parts_not_generic_label():
    result = frontend.process("https://example.com खोल।", profile="real_nepali")
    assert result.normalized_text == "H T T P S example dot com खोल।"
    token_texts = [token.raw for token in result.tokens]
    assert token_texts[:8] == ["H", "T", "T", "P", "S", "example", "dot", "com"]
    assert "यू" not in token_texts


def test_roman_nepali_classifier_marks_user_sentence():
    result = classify_tokens(["mero", "naam", "aashish", "thapa", "ho"])
    assert result.is_roman_nepali
    assert {"mero", "naam", "ho"}.issubset(set(result.markers))


def test_frontend_marks_roman_nepali_sentence():
    result = frontend.process("mero naam aashish thapa ho", profile="real_nepali")
    latin_tokens = [token for token in result.tokens if token.kind == "latin"]
    assert [token.raw for token in latin_tokens] == ["mero", "naam", "aashish", "thapa", "ho"]
    assert {token.language for token in latin_tokens} == {"ne_roman"}
    assert {token.semiotic_class for token in latin_tokens} == {"roman_nepali_word"}
    assert {token.source for token in latin_tokens} == {"roman_nepali_table"}
    assert result.phone_sequence == [
        "m", "e", ".", "r", "o",
        "n", "aa", "m",
        "aa", ".", "s", "i", "s",
        "th", "aa", ".", "p", "aa",
        "h", "o",
    ]


def test_english_latin_span_without_nepali_markers_stays_english():
    result = frontend.process("school computer", profile="real_nepali")
    latin_tokens = [token for token in result.tokens if token.kind == "latin"]
    assert {token.language for token in latin_tokens} == {"en"}
    assert {token.semiotic_class for token in latin_tokens} == {"latin_word"}
