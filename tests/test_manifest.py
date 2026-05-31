"""Training manifest contract tests."""

from __future__ import annotations

import csv
from pathlib import Path

from real_nepali import manifest


def test_rephonemize_row_stamps_canonical_frontend():
    row = {"audio_path": "a.wav", "text": "AI ले २५% growth देखायो."}
    out = manifest.rephonemize_row(row, profile="real_nepali")
    assert out["frontend"] == manifest.CANONICAL_FRONTEND
    assert out["frontend_profile"] == "real_nepali"
    assert out["frontend_version"]
    assert out["normalized_text"] == "AI ले पच्चिस प्रतिशत growth देखायो."
    assert out["phones"]
    assert out["g2p_path"].startswith(f"{manifest.CANONICAL_FRONTEND}:real_nepali")


def test_manifest_audit_accepts_canonical_rows():
    row = manifest.rephonemize_row(
        {"audio_path": "a.wav", "text": "https://example.com खोल।"},
        profile="real_nepali",
    )
    assert manifest.audit_rows([row], profile="real_nepali", verify_phones=True) == []


def test_manifest_audit_rejects_legacy_rows():
    row = {
        "audio_path": "a.wav",
        "text": "AI ले काम गर्छ।",
        "phones": "e aa i",
        "g2p_path": "legacy",
    }
    errors = manifest.audit_rows([row], profile="real_nepali")
    assert any("frontend is not" in error for error in errors)


def test_manifest_cli_rewrites_and_audits(tmp_path: Path):
    src = tmp_path / "train.tsv"
    dst = tmp_path / "train.frontend.tsv"
    with src.open("w", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["audio_path", "text"], delimiter="\t")
        writer.writeheader()
        writer.writerow({"audio_path": "a.wav", "text": "hello@example.com खोल।"})

    assert manifest.main(["--in", str(src), "--out", str(dst), "--profile", "real_nepali"]) == 0
    assert manifest.main(["--in", str(dst), "--profile", "real_nepali", "--audit-only", "--verify-phones"]) == 0

    _, rows = manifest.read_manifest(dst)
    assert rows[0]["normalized_text"] == "hello at example dot com खोल।"
