#!/usr/bin/env python3
"""Generate static frontend audit cases for the review UI."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from nepali_frontend import frontend

DEFAULT_OUT = ROOT / "review-ui" / "public" / "frontend-data.json"

DEFAULT_CASES = [
    {
        "id": "code_mix_ai",
        "category": "code-mix",
        "text": "AI ले नेपाली TTS राम्रो बनाउँछ।",
    },
    {
        "id": "latin_product_words",
        "category": "code-mix",
        "text": "Facebook मा login गरेर post share गर्नुहोस्।",
    },
    {
        "id": "number_percent",
        "category": "normalization",
        "text": "आज २५% growth देखियो।",
    },
    {
        "id": "phone_number",
        "category": "normalization",
        "text": "मेरो नम्बर 9810223384 हो।",
    },
    {
        "id": "url_email",
        "category": "protected-span",
        "text": "कृपया https://example.com वा hello@example.com खोल्नुहोस्।",
    },
    {
        "id": "punctuation_question",
        "category": "punctuation",
        "text": "के तपाईं online हुनुहुन्छ?",
    },
]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--profile", default="real_nepali")
    args = parser.parse_args()

    items = []
    for case in DEFAULT_CASES:
        result = frontend.process(case["text"], profile=args.profile)
        payload = result.asdict()
        items.append({
            "id": case["id"],
            "category": case["category"],
            "input": case["text"],
            "normalizedText": payload["normalized_text"],
            "phoneSequence": payload["phone_sequence"],
            "tokens": payload["tokens"],
            "chunks": payload["chunks"],
            "warnings": payload["warnings"],
        })

    data = {
        "title": "Nepali Text Frontend Audit",
        "generatedBy": "tools/generate_frontend_eval_data.py",
        "profile": args.profile,
        "items": items,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {args.out} ({len(items)} items)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
