"""Rephonemize a unified training manifest with the real_nepali profile."""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

from .g2p import phonemize_text
from .profiles import STANDARD_CLEAR_NEPALI

DEFAULT_COLUMNS = [
    "audio_path",
    "speaker_id",
    "gender",
    "duration_sec",
    "text",
    "phones",
    "g2p_path",
    "source",
]


def rephonemize_row(row: dict[str, str], *, profile: str) -> dict[str, str]:
    text = row.get("text", "")
    words = phonemize_text(text, profile=profile)
    phones_flat: list[str] = []
    sources: list[str] = []
    for word in words:
        if not word.phones:
            continue
        phones_flat.extend(word.phones)
        phones_flat.append("|")
        sources.append(f"real_nepali:{word.source}")
    if phones_flat and phones_flat[-1] == "|":
        phones_flat.pop()
    out = dict(row)
    out["phones"] = " ".join(phones_flat)
    out["g2p_path"] = "+".join(sources)
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--in", dest="src", type=Path, required=True,
                        help="input unified manifest TSV")
    parser.add_argument("--out", dest="dst", type=Path, required=True,
                        help="output manifest TSV")
    parser.add_argument("--profile", default=STANDARD_CLEAR_NEPALI.name)
    args = parser.parse_args(argv)

    if not args.src.exists():
        print(f"ERROR: {args.src} does not exist", file=sys.stderr)
        return 1

    with open(args.src, encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        if reader.fieldnames is None:
            print(f"ERROR: {args.src} has no header", file=sys.stderr)
            return 1
        columns = list(reader.fieldnames)
        for required in ("text", "phones", "g2p_path"):
            if required not in columns:
                print(f"ERROR: manifest missing required column {required!r}", file=sys.stderr)
                return 1
        rows = [rephonemize_row(r, profile=args.profile) for r in reader]

    args.dst.parent.mkdir(parents=True, exist_ok=True)
    with open(args.dst, "w", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=columns, delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)
    print(f"wrote {args.dst} ({len(rows)} rows, profile={args.profile})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

