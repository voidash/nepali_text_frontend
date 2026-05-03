"""TSV loaders for project data files. Read-only, cached."""

from __future__ import annotations

import csv
from functools import lru_cache
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "frontend"


def _read_tsv(path: Path) -> list[dict[str, str]]:
    with open(path, encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        return list(reader)


@lru_cache(maxsize=1)
def phones() -> dict[str, dict[str, str]]:
    """All v1.0 phones keyed by phone label.

    Each value is a dict with keys: class, status, notes.
    """
    rows = _read_tsv(DATA_DIR / "phones.tsv")
    return {r["phone"]: r for r in rows}


@lru_cache(maxsize=1)
def ipa_map() -> dict[str, str]:
    """phone label → IPA candidate string."""
    rows = _read_tsv(DATA_DIR / "ipa_map.tsv")
    return {r["phone"]: r["ipa_candidate"] for r in rows}


@lru_cache(maxsize=1)
def lexicon() -> dict[str, list[str]]:
    """Devanagari spelling → list of phone tokens (default mode).

    First pronunciation wins for spellings with multiple variants.
    Use `lexicon_variants()` to access all variants.
    """
    out: dict[str, list[str]] = {}
    for r in _read_tsv(DATA_DIR / "candidates_lexicon.tsv"):
        text = r["text"]
        if text in out:
            continue  # keep first
        out[text] = r["phones"].split()
    return out


@lru_cache(maxsize=1)
def lexicon_variants() -> dict[str, list[list[str]]]:
    """Devanagari spelling → list of all attested pronunciation variants.

    Each value is a list of phone-token sequences. For most spellings
    the list has length 1.
    """
    out: dict[str, list[list[str]]] = {}
    for r in _read_tsv(DATA_DIR / "candidates_lexicon.tsv"):
        out.setdefault(r["text"], []).append(r["phones"].split())
    return out


def is_phone(p: str) -> bool:
    """True if p is a phone label in the v1.0 inventory."""
    return p in phones() or p == "."
