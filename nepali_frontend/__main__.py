"""Command-line entry point for the Nepali text frontend."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

from . import frontend
from .normalize import text as text_norm


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="nepali-frontend")
    parser.add_argument("--profile", default="real_nepali", help="real_nepali or base")
    sub = parser.add_subparsers(dest="command", required=True)

    p_norm = sub.add_parser("normalize", help="print spoken-form normalized text")
    p_norm.add_argument("text", nargs="*")

    p_ph = sub.add_parser("phonemize", help="print phone sequence")
    p_ph.add_argument("text", nargs="*")
    p_ph.add_argument("--json", action="store_true", dest="as_json")
    p_ph.add_argument("--no-punctuation", action="store_true")

    p_trace = sub.add_parser("trace", help="print full frontend trace JSON")
    p_trace.add_argument("text", nargs="*")
    p_trace.add_argument("--no-punctuation", action="store_true")

    p_audit = sub.add_parser("audit", help="summarize frontend behavior on a text file")
    p_audit.add_argument("path", type=Path)

    args = parser.parse_args(argv)

    if args.command == "normalize":
        text = _read_text(args.text)
        normalized, _ = text_norm.normalize(text)
        print(normalized)
        return 0

    if args.command == "phonemize":
        text = _read_text(args.text)
        result = frontend.process(
            text,
            profile=args.profile,
            include_punctuation=not args.no_punctuation,
        )
        if args.as_json:
            print(json.dumps(result.asdict(), ensure_ascii=False, indent=2))
        else:
            print(" ".join(result.phone_sequence))
        return 0

    if args.command == "trace":
        text = _read_text(args.text)
        result = frontend.process(
            text,
            profile=args.profile,
            include_punctuation=not args.no_punctuation,
        )
        print(json.dumps(result.asdict(), ensure_ascii=False, indent=2))
        return 0

    if args.command == "audit":
        return _audit(args.path, profile=args.profile)

    parser.error("missing command")
    return 2


def _read_text(parts: list[str]) -> str:
    if parts:
        return " ".join(parts)
    return sys.stdin.read()


def _audit(path: Path, *, profile: str) -> int:
    counts: Counter[str] = Counter()
    warnings: Counter[str] = Counter()
    lines = 0
    with path.open(encoding="utf-8") as f:
        for line in f:
            text = line.rstrip("\n")
            if not text:
                continue
            lines += 1
            result = frontend.process(text, profile=profile)
            counts.update(token.kind for token in result.tokens)
            warnings.update(warning["code"] for warning in result.warnings)
    payload = {
        "lines": lines,
        "token_kinds": dict(sorted(counts.items())),
        "warnings": dict(sorted(warnings.items())),
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
