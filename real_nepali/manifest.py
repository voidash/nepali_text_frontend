"""Rephonemize and audit TTS manifests with the canonical frontend."""

from __future__ import annotations

import argparse
from collections import Counter
import csv
import sys
from pathlib import Path

from nepali_frontend import __version__ as FRONTEND_VERSION
from nepali_frontend import frontend

from .profiles import STANDARD_CLEAR_NEPALI

CANONICAL_FRONTEND = "nepali_frontend.frontend.process"

DEFAULT_COLUMNS = [
    "audio_path",
    "speaker_id",
    "gender",
    "duration_sec",
    "text",
    "normalized_text",
    "phones",
    "g2p_path",
    "frontend",
    "frontend_profile",
    "frontend_version",
    "frontend_warning_count",
    "frontend_warning_codes",
    "source",
]


def rephonemize_row(
    row: dict[str, str],
    *,
    profile: str,
    include_punctuation: bool = True,
) -> dict[str, str]:
    text = row.get("text", "")
    result = frontend.process(
        text,
        profile=profile,
        include_punctuation=include_punctuation,
    )
    source_counts = Counter(token.source for token in result.tokens if token.source)
    warning_counts = Counter(warning["code"] for warning in result.warnings)
    out = dict(row)
    out["normalized_text"] = result.normalized_text
    out["phones"] = " ".join(result.phone_sequence)
    out["g2p_path"] = _source_summary(source_counts, profile=profile)
    out["frontend"] = CANONICAL_FRONTEND
    out["frontend_profile"] = profile
    out["frontend_version"] = FRONTEND_VERSION
    out["frontend_warning_count"] = str(sum(warning_counts.values()))
    out["frontend_warning_codes"] = ",".join(
        f"{code}:{count}" for code, count in sorted(warning_counts.items())
    )
    return out


def audit_rows(
    rows: list[dict[str, str]],
    *,
    profile: str | None = None,
    verify_phones: bool = False,
    strict_warnings: bool = False,
) -> list[str]:
    errors: list[str] = []
    for idx, row in enumerate(rows, start=2):
        row_id = row.get("id") or row.get("audio_path") or f"line {idx}"
        if row.get("frontend") != CANONICAL_FRONTEND:
            errors.append(f"{row_id}: frontend is not {CANONICAL_FRONTEND}")
        if profile and row.get("frontend_profile") != profile:
            errors.append(f"{row_id}: frontend_profile is not {profile}")
        if not row.get("frontend_version"):
            errors.append(f"{row_id}: missing frontend_version")
        if not row.get("normalized_text"):
            errors.append(f"{row_id}: missing normalized_text")
        if not row.get("phones"):
            errors.append(f"{row_id}: missing phones")
        if strict_warnings and _warning_count(row) > 0:
            errors.append(f"{row_id}: frontend warnings present: {row.get('frontend_warning_codes', '')}")
        if verify_phones:
            expected = rephonemize_row(
                row,
                profile=row.get("frontend_profile") or profile or STANDARD_CLEAR_NEPALI.name,
            )
            if row.get("normalized_text") != expected["normalized_text"]:
                errors.append(f"{row_id}: normalized_text does not match current frontend")
            if row.get("phones") != expected["phones"]:
                errors.append(f"{row_id}: phones do not match current frontend")
    return errors


def read_manifest(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        if reader.fieldnames is None:
            raise ValueError(f"{path} has no header")
        return list(reader.fieldnames), list(reader)


def write_manifest(path: Path, columns: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=columns, delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--in", dest="src", type=Path, required=True,
                        help="input unified manifest TSV")
    parser.add_argument("--out", dest="dst", type=Path,
                        help="output manifest TSV")
    parser.add_argument("--profile", default=STANDARD_CLEAR_NEPALI.name)
    parser.add_argument("--audit-only", action="store_true",
                        help="validate that an existing manifest used the canonical frontend")
    parser.add_argument("--verify-phones", action="store_true",
                        help="rerun the frontend and verify normalized_text/phones match")
    parser.add_argument("--strict-warnings", action="store_true",
                        help="fail audit when frontend warnings are present")
    parser.add_argument("--no-punctuation", action="store_true",
                        help="omit punctuation/prosody phones when rephonemizing")
    args = parser.parse_args(argv)

    if not args.src.exists():
        print(f"ERROR: {args.src} does not exist", file=sys.stderr)
        return 1

    try:
        columns, rows = read_manifest(args.src)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    if "text" not in columns:
        print("ERROR: manifest missing required column 'text'", file=sys.stderr)
        return 1

    if args.audit_only:
        errors = audit_rows(
            rows,
            profile=args.profile,
            verify_phones=args.verify_phones,
            strict_warnings=args.strict_warnings,
        )
        if errors:
            for error in errors[:50]:
                print(f"ERROR: {error}", file=sys.stderr)
            if len(errors) > 50:
                print(f"ERROR: {len(errors) - 50} more errors", file=sys.stderr)
            return 1
        print(f"OK: {args.src} uses {CANONICAL_FRONTEND} ({len(rows)} rows)")
        return 0

    if args.dst is None:
        print("ERROR: --out is required unless --audit-only is set", file=sys.stderr)
        return 1

    rows = [
        rephonemize_row(
            row,
            profile=args.profile,
            include_punctuation=not args.no_punctuation,
        )
        for row in rows
    ]
    columns = _output_columns(columns)
    write_manifest(args.dst, columns, rows)
    print(f"wrote {args.dst} ({len(rows)} rows, profile={args.profile}, frontend={CANONICAL_FRONTEND})")
    return 0


def _output_columns(columns: list[str]) -> list[str]:
    out = list(columns)
    for column in DEFAULT_COLUMNS:
        if column not in out:
            out.append(column)
    return out


def _source_summary(source_counts: Counter[str], *, profile: str) -> str:
    suffix = ",".join(f"{source}:{count}" for source, count in sorted(source_counts.items()))
    return f"{CANONICAL_FRONTEND}:{profile}" + (f":{suffix}" if suffix else "")


def _warning_count(row: dict[str, str]) -> int:
    raw = row.get("frontend_warning_count", "").strip()
    if not raw:
        return 0
    try:
        return int(raw)
    except ValueError:
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
