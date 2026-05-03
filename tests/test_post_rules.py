"""Post-rule tests."""

from __future__ import annotations

from nepali_frontend.g2p import akshara as ak
from nepali_frontend.g2p import post_rules as pr


def test_anusvara_before_velar_becomes_ng():
    # अंक → ax + ng + k + ax (anusvara → /ŋ/ before /k/)
    aksharas = ak.parse("अंक")
    aksharas, decs = pr.apply_anusvara_context(aksharas)
    out = []
    for a in aksharas:
        out.extend(a.phones)
    # Initial अं resolves to ax + ng before /k/
    assert "ng" in out
    assert any(d["rule"] == "anusvara_context" for d in decs)


def test_anusvara_before_bilabial_becomes_m():
    # बम्बई → b + ax + m + b + ... (anusvara → /m/ before /b/)
    aksharas = ak.parse("बंब")
    aksharas, decs = pr.apply_anusvara_context(aksharas)
    out = []
    for a in aksharas:
        out.extend(a.phones)
    assert "m" in out


def test_anusvara_before_dental_becomes_n():
    # अंत → ax + n + t + ax
    aksharas = ak.parse("अंत")
    aksharas, decs = pr.apply_anusvara_context(aksharas)
    out = []
    for a in aksharas:
        out.extend(a.phones)
    assert "n" in out


def test_schwa_deletion_default_word_final():
    # राम → r aa m (final schwa deleted by default, monomorphemic non-verb non-conjunct)
    text = "राम"
    aksharas = ak.parse(text)
    aksharas, decs = pr.apply_schwa_deletion(text, aksharas)
    out = []
    for a in aksharas:
        out.extend(a.phones)
    assert out == ["r", "aa", "m"]
    assert any(d["rule"] == "schwa_deletion_default" for d in decs)


def test_schwa_retention_conjunct_final():
    # अन्त → ax n t ax (conjunct final, schwa retained)
    text = "अन्त"
    aksharas = ak.parse(text)
    aksharas, decs = pr.apply_schwa_deletion(text, aksharas)
    out = []
    for a in aksharas:
        out.extend(a.phones)
    assert out[-1] == "ax"
    assert any(d["rule"] == "schwa_retention_conjunct" for d in decs)


def test_schwa_retention_verb_form():
    # हुन्छ → ɦ u n tsh ax (verb, schwa retained)
    text = "हुन्छ"
    aksharas = ak.parse(text)
    aksharas, decs = pr.apply_schwa_deletion(text, aksharas)
    out = []
    for a in aksharas:
        out.extend(a.phones)
    # Final phone should be ax (schwa retained)
    assert out[-1] == "ax"


def test_gemination_doubled_consonant():
    # चप्पल → ts ax p: ax l (geminate p)
    aksharas = ak.parse("चप्पल")
    aksharas, decs = pr.apply_gemination(aksharas)
    out = []
    for a in aksharas:
        out.extend(a.phones)
    assert "p:" in out
    assert any(d["rule"] == "gemination" for d in decs)


def test_suffix_strip_genitive_ko():
    lex = {"राम": ["r", "aa", "m"]}
    result = pr.try_suffix_strip("रामको", lex)
    assert result is not None
    root, suffix, root_phones = result
    assert root == "राम"
    assert suffix == "को"


def test_suffix_strip_ergative_le():
    lex = {"उनी": ["u", "n", "i"]}
    result = pr.try_suffix_strip("उनीले", lex)
    assert result is not None
    assert result[1] == "ले"


def test_suffix_strip_no_match_returns_none():
    lex = {"कुनै": ["k", "u", "n", "axj"]}
    result = pr.try_suffix_strip("नयाँ", lex)
    assert result is None


def test_suffix_strip_root_not_in_lexicon_returns_none():
    lex = {}
    result = pr.try_suffix_strip("रामको", lex)
    assert result is None


def test_diphthong_contraction_aa_plus_u():
    # आऊ → aaw (not aa + u)
    aksharas = ak.parse("आऊ")
    aksharas, decs = pr.apply_diphthong_contraction(aksharas)
    out = []
    for a in aksharas:
        out.extend(a.phones)
    assert out == ["aaw"]
    assert any(d["rule"] == "diphthong_contraction" for d in decs)


def test_diphthong_contraction_consonant_plus_independent_vowel():
    # भाइ → bh aaj (consonant + nucleus + offglide → consonant + diphthong)
    aksharas = ak.parse("भाइ")
    aksharas, decs = pr.apply_diphthong_contraction(aksharas)
    out = []
    for a in aksharas:
        out.extend(a.phones)
    assert out == ["bh", "aaj"]


def test_diphthong_contraction_skips_non_diphthong_pairs():
    # जीउ → dz + i + u (not d + iu — /iu/ is not in our diphthong inventory;
    # 2-syllable encoding per project policy).
    aksharas = ak.parse("जीउ")
    aksharas, _ = pr.apply_diphthong_contraction(aksharas)
    out = []
    for a in aksharas:
        out.extend(a.phones)
    assert "iw" not in out and "iu" not in out
    # Should remain as separate phones
    assert "i" in out and "u" in out


def test_compound_schwa_deletion_fires_on_known_compound():
    # Synthetic test: lexicon contains both halves, ≥2 aksharas each.
    aksharas = ak.parse("राजमार्ग")
    lex = {
        "राज": ["r", "aa", "dz"],
        "मार्ग": ["m", "aa", "r", "g"],
        "राजमार्ग": ["r", "aa", "dz", "m", "aa", "r", "g"],
    }
    aksharas, decs = pr.apply_compound_schwa("राजमार्ग", aksharas, lex)
    # We expect the schwa after the first ज to have been deleted
    # (only if "राज" is in lex AND "मार्ग" is in lex AND both have ≥2 aksharas).
    assert any(d["rule"] == "compound_schwa_deletion" for d in decs)


def test_compound_schwa_deletion_does_not_fire_on_short_word():
    # चपल — even if चप happens to be in the lex, ल is only 1 akshara,
    # so the rule must not fire.
    aksharas = ak.parse("चपल")
    lex = {"चप": ["ts", "ax", "p"], "ल": ["l", "ax"], "चपल": ["ts", "p", "l"]}
    aksharas, decs = pr.apply_compound_schwa("चपल", aksharas, lex)
    assert not any(d["rule"] == "compound_schwa_deletion" for d in decs)
