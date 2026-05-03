"""Akshara parser tests.

Cases drawn from data/frontend/akshara_cases.tsv plus additional
explicit test fixtures covering features the TSV doesn't yet exercise.
"""

from __future__ import annotations

import csv
from pathlib import Path

from nepali_frontend.g2p import akshara as ak

DATA = Path(__file__).resolve().parent.parent / "data" / "frontend"


def _phones_of(text: str) -> list[str]:
    out: list[str] = []
    for a in ak.parse(text):
        out.extend(a.phones)
    return out


def test_inherent_vowel_single_consonant():
    # क → k + inherent ax
    assert _phones_of("क") == ["k", "ax"]


def test_consonant_with_matra():
    # का → k + aa
    assert _phones_of("का") == ["k", "aa"]


def test_explicit_virama():
    # क् → k (no vowel)
    assert _phones_of("क्") == ["k"]


def test_conjunct_two_consonants():
    # क्र → k + r + ax
    assert _phones_of("क्र") == ["k", "r", "ax"]


def test_conjunct_repha():
    # र्क → r + k + ax
    assert _phones_of("र्क") == ["r", "k", "ax"]


def test_independent_vowel_with_chandrabindu():
    # अँ → axn
    assert _phones_of("अँ") == ["axn"]


def test_independent_vowel_with_anusvara():
    # अं → axn (default; contextual rule may rewrite later)
    assert _phones_of("अं") == ["axn"]


def test_long_vowel_collapses():
    # ई → i (orthographic length collapsed in default mode)
    assert _phones_of("ई") == ["i"]


def test_diphthong_ai():
    # ऐ → axj
    assert _phones_of("ऐ") == ["axj"]


def test_diphthong_au():
    # औ → axw
    assert _phones_of("औ") == ["axw"]


def test_aaja_today():
    # आज → aa + dz + ax (project labels; default mode)
    # In Khatiwada IPA: /ad͡zʌ/
    assert _phones_of("आज") == ["aa", "dz", "ax"]


def test_sibilant_collapse_default():
    # शिक्षा "education" → s + i + k + s + aa (श → s, क्ष conjunct → k+s)
    # Default mode collapses श → s.
    out = _phones_of("शिक्षा")
    assert out[0] == "s"  # श is s in default mode
    # Conjunct क्ष should produce k, s, aa at the end
    assert "k" in out and "aa" in out


def test_palatal_nasal_collapses():
    # ञ → n in default mode
    assert _phones_of("ञ") == ["n", "ax"]


def test_retroflex_nasal_collapses():
    # ण → n in default mode
    assert _phones_of("ण") == ["n", "ax"]


def test_visarga_emits_h():
    # कः → k + ax + h (rare in Nepali; appears in Sanskrit loans)
    assert _phones_of("कः") == ["k", "ax", "h"]


def test_word_final_virama_no_inherent():
    # राम् → r + aa + m (no schwa)
    assert _phones_of("राम्") == ["r", "aa", "m"]


def test_word_with_inherent_at_end():
    # राम → r + aa + m + ax (schwa not deleted by parser; post-rule does that)
    assert _phones_of("राम") == ["r", "aa", "m", "ax"]


def test_devanagari_digit_passthrough():
    aksharas = ak.parse("५")
    assert len(aksharas) == 1
    assert aksharas[0].type == "digit"


def test_danda_passthrough():
    aksharas = ak.parse("राम।")
    assert aksharas[-1].type == "punct"
    assert aksharas[-1].text == "।"


def test_spans_are_lossless():
    """Every character lands in exactly one akshara span."""
    text = "नमस्ते।"
    aksharas = ak.parse(text)
    covered = set()
    for a in aksharas:
        for k in range(a.span[0], a.span[1]):
            assert k not in covered, f"position {k} double-covered"
            covered.add(k)
    assert covered == set(range(len(text)))


def test_tsv_cases():
    """Run every row in akshara_cases.tsv; fail with case_id on mismatch."""
    path = DATA / "akshara_cases.tsv"
    with open(path, encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            raw = row["raw_text"]
            expected = row["expected_units"].split("+")
            got = _phones_of(raw)
            assert got == expected, (
                f"{row['case_id']}: {raw!r} expected {expected}, got {got}"
            )
