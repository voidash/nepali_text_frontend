"""Compare local Nepali G2P outputs against Wiktionary's ne-IPA module.

The script fetches Wiktionary outputs at runtime instead of vendoring
Wiktionary module code or testcase data into this repository.

Two comparison views are emitted:

- broad_match keeps the old/new affricate target difference.
- affricate_neutral_match aliases tS/dZ-style and ts/dz-style affricates.

This makes Wiktionary useful as a regression sanity check without letting its
affricate policy decide the product voice target by itself.
"""

from __future__ import annotations

import argparse
import csv
import html
import json
import re
import sys
import unicodedata
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from nepali_frontend import data
from nepali_frontend.g2p import phonemizer as old_g2p
from real_nepali import g2p as real_g2p

TESTCASES_RAW_URL = (
    "https://en.wiktionary.org/w/index.php?"
    "title=Module:ne-IPA/testcases&action=raw"
)
EXPAND_API_URL = "https://en.wiktionary.org/w/api.php"
DEFAULT_WORDS = ROOT / "real_nepali" / "data" / "review_words.tsv"
DEFAULT_USER_AGENT = (
    "nepali_text_frontend/0.1 "
    "(https://github.com/voidash/nepali_text_frontend; local evaluation)"
)


@dataclass(frozen=True)
class WikiCase:
    text: str
    wiki_ipa: str
    comment: str = ""
    source: str = "wiktionary"


def fetch_text(url: str, *, user_agent: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": user_agent})
    with urllib.request.urlopen(req, timeout=30) as response:
        return response.read().decode("utf-8")


def fetch_json(
    url: str,
    fields: dict[str, str],
    *,
    user_agent: str,
) -> dict:
    data_bytes = urllib.parse.urlencode(fields).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data_bytes,
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": user_agent,
        },
    )
    with urllib.request.urlopen(req, timeout=45) as response:
        return json.loads(response.read().decode("utf-8"))


def load_testcases(*, user_agent: str) -> list[WikiCase]:
    raw = fetch_text(TESTCASES_RAW_URL, user_agent=user_agent)
    cases: list[WikiCase] = []
    pattern = re.compile(r'\{"([^"]+)",\s*"([^"]+)"(?:,\s*"([^"]+)")?\}')
    for match in pattern.finditer(raw):
        cases.append(WikiCase(
            text=match.group(1),
            wiki_ipa=match.group(2),
            comment=match.group(3) or "",
            source="Module:ne-IPA/testcases",
        ))
    if not cases:
        raise RuntimeError("no Wiktionary testcases parsed")
    return cases


def load_words(path: Path, *, limit: int | None = None) -> list[str]:
    words: list[str] = []
    with open(path, encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            words.append(row["text"])
            if limit is not None and len(words) >= limit:
                break
    return words


def fetch_template_ipa(
    words: list[str],
    *,
    user_agent: str,
    chunk_size: int = 35,
) -> list[WikiCase]:
    cases: list[WikiCase] = []
    for start in range(0, len(words), chunk_size):
        chunk = words[start:start + chunk_size]
        text = "\n".join(
            f"@@WTCASE_{start + index}@@ "
            f"{{{{ne-IPA|{word}}}}}"
            for index, word in enumerate(chunk)
        )
        payload = fetch_json(
            EXPAND_API_URL,
            {
                "action": "expandtemplates",
                "format": "json",
                "prop": "wikitext",
                "text": text,
            },
            user_agent=user_agent,
        )
        expanded = payload["expandtemplates"]["wikitext"]
        for index, word in enumerate(chunk):
            marker = f"@@WTCASE_{start + index}@@"
            next_marker = (
                f"@@WTCASE_{start + index + 1}@@"
                if index + 1 < len(chunk)
                else "@@WTCASE_"
            )
            marker_pos = expanded.find(marker)
            if marker_pos < 0:
                raise RuntimeError(f"missing Wiktionary marker for {word}")
            next_pos = expanded.find(next_marker, marker_pos + len(marker))
            block = expanded[marker_pos: next_pos if next_pos >= 0 else None]
            match = re.search(
                r'<span class="IPA nowrap">\[([^\]]+)\]</span>',
                block,
            )
            if not match:
                raise RuntimeError(f"no IPA span parsed for {word}: {block[:200]}")
            cases.append(WikiCase(
                text=word,
                wiki_ipa=html.unescape(match.group(1)),
                source="{{ne-IPA}} live expansion",
            ))
    return cases


def phone_ipa_map() -> dict[str, str]:
    mapping = data.ipa_map().copy()
    mapping.update({
        # real_nepali experimental clear-profile affricates.
        "ch": "t͡ʃ",
        "chh": "t͡ʃʰ",
        "j": "d͡ʒ",
        "jh": "d͡ʒʱ",
    })
    return mapping


def phones_to_ipa(phones: Iterable[str], mapping: dict[str, str]) -> str:
    out: list[str] = []
    for phone in phones:
        if phone == ".":
            continue
        base = phone
        geminated = False
        if base.endswith(":"):
            base = base[:-1]
            geminated = True
        ipa = mapping.get(base, base)
        out.append(f"{ipa}ː" if geminated else ipa)
    return "".join(out)


def broad_ipa(value: str, *, affricate_neutral: bool = False) -> str:
    """Normalize IPA for broad G2P comparison, not phonetic identity."""
    s = value.strip().strip("[]/")
    s = s.replace("(", "").replace(")", "")
    s = s.replace("ä", "a").replace("ā", "a")
    s = s.replace("ɾ", "r").replace("ɽ", "ɖ")
    s = s.replace("ɦ", "h")
    s = s.replace("ʰ", "h").replace("ʱ", "h")
    s = s.replace("t͡s", "ts").replace("d͡z", "dz")
    s = s.replace("t͡ʃ", "tʃ").replace("d͡ʒ", "dʒ")
    s = unicodedata.normalize("NFD", s)

    out: list[str] = []
    for char in s:
        category = unicodedata.category(char)
        if char in {
            ".",
            " ",
            "‿",
            "\u0361",  # tie bar
            "\u031a",  # no audible release
            "\u032a",  # dental
            "\u0320",  # retracted
            "\u0324",  # breathy voice
            "\u032f",  # non-syllabic
            "ː",
            "ˑ",
        }:
            continue
        if category.startswith("M") and char != "\u0303":
            continue
        out.append(char)
    s = "".join(out)
    s = s.replace("ŋ", "ng").replace("ɡ", "g")
    s = s.replace("ʈ", "T").replace("ɖ", "D")
    if affricate_neutral:
        s = s.replace("tʃ", "ts").replace("dʒ", "dz")
    return s


def levenshtein(a: str, b: str) -> int:
    previous = list(range(len(b) + 1))
    for i, ca in enumerate(a, start=1):
        current = [i]
        for j, cb in enumerate(b, start=1):
            current.append(min(
                previous[j] + 1,
                current[-1] + 1,
                previous[j - 1] + (ca != cb),
            ))
        previous = current
    return previous[-1]


def similarity(a: str, b: str) -> float:
    denom = max(len(a), len(b), 1)
    return 1.0 - (levenshtein(a, b) / denom)


def compare(cases: list[WikiCase]) -> list[dict[str, str]]:
    mapping = phone_ipa_map()
    rows: list[dict[str, str]] = []
    for case in cases:
        old = old_g2p.phonemize_word(case.text)
        real = real_g2p.phonemize_word(case.text)
        old_ipa = phones_to_ipa(old.phones, mapping)
        real_ipa = phones_to_ipa(real.phones, mapping)
        wiki_broad = broad_ipa(case.wiki_ipa)
        old_broad = broad_ipa(old_ipa)
        real_broad = broad_ipa(real_ipa)
        wiki_neutral = broad_ipa(case.wiki_ipa, affricate_neutral=True)
        old_neutral = broad_ipa(old_ipa, affricate_neutral=True)
        real_neutral = broad_ipa(real_ipa, affricate_neutral=True)
        rows.append({
            "text": case.text,
            "source": case.source,
            "comment": case.comment,
            "wiktionary_ipa": case.wiki_ipa,
            "old_source": old.source,
            "old_phones": " ".join(old.phones),
            "old_ipa": old_ipa,
            "real_source": real.source,
            "real_phones": " ".join(real.phones),
            "real_ipa": real_ipa,
            "changed": "yes" if old.phones != real.phones else "no",
            "wiki_broad": wiki_broad,
            "old_broad": old_broad,
            "real_broad": real_broad,
            "old_broad_match": "yes" if old_broad == wiki_broad else "no",
            "real_broad_match": "yes" if real_broad == wiki_broad else "no",
            "old_similarity": f"{similarity(old_broad, wiki_broad):.3f}",
            "real_similarity": f"{similarity(real_broad, wiki_broad):.3f}",
            "old_affricate_neutral_match": (
                "yes" if old_neutral == wiki_neutral else "no"
            ),
            "real_affricate_neutral_match": (
                "yes" if real_neutral == wiki_neutral else "no"
            ),
        })
    return rows


def summarize(rows: list[dict[str, str]]) -> dict[str, str]:
    total = len(rows)
    changed = sum(row["changed"] == "yes" for row in rows)

    def count(key: str) -> int:
        return sum(row[key] == "yes" for row in rows)

    def avg(key: str) -> float:
        return sum(float(row[key]) for row in rows) / total if total else 0.0

    return {
        "rows": str(total),
        "changed_rows": str(changed),
        "old_broad_matches": f"{count('old_broad_match')}/{total}",
        "real_broad_matches": f"{count('real_broad_match')}/{total}",
        "old_affricate_neutral_matches": (
            f"{count('old_affricate_neutral_match')}/{total}"
        ),
        "real_affricate_neutral_matches": (
            f"{count('real_affricate_neutral_match')}/{total}"
        ),
        "old_avg_similarity": f"{avg('old_similarity'):.3f}",
        "real_avg_similarity": f"{avg('real_similarity'):.3f}",
    }


def write_rows(rows: list[dict[str, str]], out: Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "text",
        "source",
        "comment",
        "wiktionary_ipa",
        "old_source",
        "old_phones",
        "old_ipa",
        "real_source",
        "real_phones",
        "real_ipa",
        "changed",
        "wiki_broad",
        "old_broad",
        "real_broad",
        "old_broad_match",
        "real_broad_match",
        "old_similarity",
        "real_similarity",
        "old_affricate_neutral_match",
        "real_affricate_neutral_match",
    ]
    with open(out, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--source",
        choices=("testcases", "words"),
        default="testcases",
        help="compare Wiktionary's testcase module or live {{ne-IPA}} words",
    )
    parser.add_argument("--words", type=Path, default=DEFAULT_WORDS)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--user-agent", default=DEFAULT_USER_AGENT)
    args = parser.parse_args()

    if args.source == "testcases":
        cases = load_testcases(user_agent=args.user_agent)
    else:
        words = load_words(args.words, limit=args.limit)
        cases = fetch_template_ipa(words, user_agent=args.user_agent)

    rows = compare(cases)
    summary = summarize(rows)
    if args.out:
        write_rows(rows, args.out)
        print(f"wrote {args.out}")
    for key, value in summary.items():
        print(f"{key}\t{value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
