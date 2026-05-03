"""Number verbalization + tokenization + chunker tests."""

from __future__ import annotations

from nepali_frontend.normalize import numbers as N
from nepali_frontend.normalize import phones as P
from nepali_frontend.normalize import normalize_text
from nepali_frontend.tokenize import script as tk
from nepali_frontend.prosody import chunker as ch


# ---- numbers ----

def test_cardinal_zero():
    assert N.cardinal(0) == ["शून्य"]


def test_cardinal_basic_units():
    assert N.cardinal(1) == ["एक"]
    assert N.cardinal(5) == ["पाँच"]
    assert N.cardinal(9) == ["नौ"]


def test_cardinal_teens():
    assert N.cardinal(11) == ["एघार"]
    assert N.cardinal(15) == ["पन्ध्र"]
    assert N.cardinal(19) == ["उन्नाइस"]


def test_cardinal_specific_idiosyncratic():
    # 21-99 are individual lookup, not regular composition
    assert N.cardinal(21) == ["एक्काइस"]
    assert N.cardinal(29) == ["उनन्तिस"]
    assert N.cardinal(39) == ["उनन्चालीस"]
    assert N.cardinal(99) == ["उनान्सय"]


def test_cardinal_hundreds():
    assert N.cardinal(100) == ["एक", "सय"]
    assert N.cardinal(250) == ["दुई", "सय", "पचास"]
    assert N.cardinal(365) == ["तीन", "सय", "पैंसट्ठी"]


def test_cardinal_thousands_and_lakhs():
    assert N.cardinal(1000) == ["एक", "हजार"]
    assert N.cardinal(1234) == ["एक", "हजार", "दुई", "सय", "चौँतिस"]
    assert N.cardinal(100_000) == ["एक", "लाख"]
    assert N.cardinal(10_000_000) == ["एक", "करोड"]


def test_parse_devanagari_digits():
    assert N.parse_digits("२९") == 29
    assert N.parse_digits("१५") == 15
    assert N.parse_digits("३९") == 39
    assert N.parse_digits("०") == 0


def test_parse_ascii_digits():
    assert N.parse_digits("5") == 5
    assert N.parse_digits("100") == 100


def test_normalize_numbers_in_text_devanagari():
    assert "उनन्तिस" in N.normalize_numbers_in_text("२९ जना")


def test_normalize_numbers_in_text_ascii():
    assert "पाँच" in N.normalize_numbers_in_text("5 सालमा")


# ---- phones ----

def test_verbalize_phone_canonical_example():
    # Project canonical: 9810223384 → 98 10 22 33 84
    expected = ["अन्ठान्नब्बे", "दश", "बाइस", "तेत्तिस", "चौरासी"]
    assert P.verbalize_phone("9810223384") == expected


def test_verbalize_phone_devanagari_digits():
    expected = ["अन्ठान्नब्बे", "दश", "बाइस", "तेत्तिस", "चौरासी"]
    assert P.verbalize_phone("९८१०२२३३८४") == expected


def test_verbalize_phone_leading_zero_pair():
    # Pair "01" must keep the zero: शून्य एक, not just एक
    out = P.verbalize_phone("0123456789")
    assert out[0] == "शून्य"
    assert out[1] == "एक"


def test_verbalize_phone_double_zero_pair():
    out = P.verbalize_phone("0000000000")
    assert out == ["शून्य"] * 10


def test_verbalize_phone_wrong_length_raises():
    import pytest
    with pytest.raises(ValueError):
        P.verbalize_phone("12345")


def test_normalize_phones_in_text_basic():
    out = P.normalize_phones_in_text("मेरो नम्बर 9810223384 हो")
    assert "अन्ठान्नब्बे" in out
    assert "9810223384" not in out


def test_normalize_phones_skips_non_10_digit_runs():
    # 9-digit and 11-digit runs are NOT phone numbers — left alone
    out_9 = P.normalize_phones_in_text("कोड 123456789")
    assert "123456789" in out_9
    out_11 = P.normalize_phones_in_text("बार्कोड 12345678901")
    assert "12345678901" in out_11


def test_normalize_phones_skips_embedded_digit_runs():
    # 10-digit substring inside a longer run must not be hijacked
    out = P.normalize_phones_in_text("कोड 12345678901234")
    assert "12345678901234" in out


# ---- composer ----

def test_normalize_text_phone_then_numbers():
    out = normalize_text("नम्बर 9810223384 र उमेर 25")
    assert "अन्ठान्नब्बे" in out  # phone pair
    assert "पच्चिस" in out         # cardinal 25
    assert "9810223384" not in out
    assert "25" not in out


def test_normalize_text_no_change_when_no_digits():
    src = "नमस्ते कस्तो छ"
    assert normalize_text(src) == src


# ---- tokenizer ----

def test_tokenizer_devanagari_word():
    toks = tk.tokenize("नमस्ते")
    assert len(toks) == 1
    assert toks[0].kind == "devanagari"
    assert toks[0].language == "ne"


def test_tokenizer_latin_word():
    toks = tk.tokenize("Facebook")
    assert toks[0].kind == "latin"
    assert toks[0].language == "en"


def test_tokenizer_mixed_script():
    toks = [t for t in tk.tokenize("Facebook मा post") if t.kind != "space"]
    kinds = [t.kind for t in toks]
    assert kinds == ["latin", "devanagari", "latin"]


def test_tokenizer_separates_punctuation():
    toks = [t for t in tk.tokenize("राम।") if t.kind != "space"]
    assert toks[0].kind == "devanagari"
    assert toks[1].kind == "sentence_end"


def test_tokenizer_question_mark():
    toks = [t for t in tk.tokenize("तपाईं?") if t.kind != "space"]
    assert toks[-1].kind == "question"


def test_tokenizer_digit_run():
    toks = [t for t in tk.tokenize("२९") if t.kind != "space"]
    assert toks[0].kind == "digit"
    assert toks[0].language == "ne"


# ---- chunker ----

def test_chunker_one_declarative_sentence():
    toks = tk.tokenize("राम घर गयो।")
    chunks = ch.chunk(toks)
    assert len(chunks) == 1
    assert chunks[0].sentence_type == "declarative"
    assert chunks[0].boundary_strength == "sentence"


def test_chunker_yes_no_question():
    toks = tk.tokenize("के तपाईं ठिक हुनुहुन्छ?")
    chunks = ch.chunk(toks)
    assert chunks[0].sentence_type == "yes_no_question"
    assert chunks[0].intonation_hint == "rise"


def test_chunker_wh_question():
    toks = tk.tokenize("कहाँ जाने हो?")
    chunks = ch.chunk(toks)
    assert chunks[0].sentence_type == "wh_question"
    assert chunks[0].intonation_hint == "fall"


def test_chunker_two_sentences():
    toks = tk.tokenize("राम घर गयो। सीता खेल्न गई।")
    chunks = ch.chunk(toks)
    assert len(chunks) == 2
    assert all(c.sentence_type == "declarative" for c in chunks)


def test_chunker_exclamation():
    toks = tk.tokenize("वाह!")
    chunks = ch.chunk(toks)
    assert chunks[0].sentence_type == "exclamation"
