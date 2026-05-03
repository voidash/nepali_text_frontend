"""Trace emitter tests."""

from __future__ import annotations

import json

from nepali_frontend.g2p import phonemizer as ph
from nepali_frontend import trace as t


def test_build_trace_returns_valid_json():
    text = "राम र सीता।"
    words = ph.phonemize_text(text)
    tr = t.build_trace(text, words)
    s = tr.to_json()
    parsed = json.loads(s)
    # Top-level fields per docs/frontend-trace-contract.md
    for k in ("input", "normalized_text", "tokens", "phones", "decisions", "versions"):
        assert k in parsed


def test_trace_versions_populated():
    tr = t.build_trace("क", ph.phonemize_text("क"))
    versions = tr._asdict()["versions"]
    assert versions["frontend"]
    assert versions["phone_inventory"] == "1.0"


def test_trace_phones_carry_source():
    text = "आज"
    tr = t.build_trace(text, ph.phonemize_text(text))
    d = tr._asdict()
    assert d["phones"]
    assert d["phones"][0]["source"] in ("lexicon", "suffix_strip", "g2p_rule")
