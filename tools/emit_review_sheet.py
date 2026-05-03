"""Emit an old-vs-real_nepali review sheet for native judgment.

The output is a TSV with both phone strings and audit notes. It is meant to be
reviewed by a native speaker before using the experimental profile for TTS
training.
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from nepali_frontend.g2p import phonemizer as old_g2p
from real_nepali import g2p as real_g2p

DEFAULT_WORDS = ROOT / "real_nepali" / "data" / "review_words.tsv"


def phones_str(items: list[str]) -> str:
    return " ".join(items)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--words", type=Path, default=DEFAULT_WORDS,
                        help="input TSV with text/focus/why columns")
    parser.add_argument("--out", type=Path, required=True,
                        help="output review TSV")
    args = parser.parse_args()

    rows: list[dict[str, str]] = []
    with open(args.words, encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            text = row["text"]
            old = old_g2p.phonemize_word(text)
            real = real_g2p.phonemize_word(text)
            rows.append({
                "text": text,
                "focus": row.get("focus", ""),
                "why": row.get("why", ""),
                "old_source": old.source,
                "old_phones": phones_str(old.phones),
                "real_source": real.source,
                "real_phones": phones_str(real.phones),
                "changed": "yes" if old.phones != real.phones else "no",
                "reviewer_preference": "",
                "reviewer_phones": "",
                "reviewer_notes": "",
            })

    args.out.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "text",
        "focus",
        "why",
        "old_source",
        "old_phones",
        "real_source",
        "real_phones",
        "changed",
        "reviewer_preference",
        "reviewer_phones",
        "reviewer_notes",
    ]
    with open(args.out, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)

    changed = sum(1 for row in rows if row["changed"] == "yes")
    print(f"wrote {args.out} ({len(rows)} rows, {changed} changed)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
