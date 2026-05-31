"""Top-level text normalizer."""

from __future__ import annotations

import re
import unicodedata
from urllib.parse import urlsplit

from . import numbers as _numbers
from . import phones as _phones


URL_RE = re.compile(r"\b(?:https?://[^\s]+|www\.[^\s]+)", re.IGNORECASE)
EMAIL_RE = re.compile(r"\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b")
WHITESPACE_RE = re.compile(r"\s+")
TRAILING_URL_PUNCT = ".,!?;:।॥"

PUNCT_TRANSLATION = str.maketrans({
    "“": '"',
    "”": '"',
    "‘": "'",
    "’": "'",
    "—": "-",
    "–": "-",
    "…": ".",
    "，": ",",
    "：": ":",
    "；": ";",
    "？": "?",
    "！": "!",
})

SYMBOL_SPOKEN_FORMS = {
    "%": " प्रतिशत ",
    "٪": " प्रतिशत ",
    "&": " र ",
    "+": " प्लस ",
    "=": " बराबर ",
}

ABBREVIATIONS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"(?<!\w)डा\.?(?!\w)"), "डाक्टर"),
    (re.compile(r"(?<!\w)श्री\.(?!\w)"), "श्री"),
    (re.compile(r"(?<!\w)श्रीमती\.(?!\w)"), "श्रीमती"),
    (re.compile(r"(?<!\w)र[ुू]\.(?!\w)"), "रुपैयाँ"),
    (re.compile(r"(?<!\w)rs\.(?!\w)", re.IGNORECASE), "रुपैयाँ"),
]


def normalize(text: str) -> tuple[str, list[dict]]:
    """Normalize a raw text input into a spoken-form Nepali string.

    Returns: `(normalized_text, decisions)` where `decisions` is a list
    of trace events documenting each substitution.
    """
    decisions: list[dict] = []

    current = unicodedata.normalize("NFC", text)
    current = _record_step(decisions, "unicode_nfc", text, current)

    before = current
    current = current.translate(PUNCT_TRANSLATION)
    current = _record_step(decisions, "punctuation_canonicalization", before, current)

    before = current
    current = EMAIL_RE.sub(lambda match: f" {_verbalize_email(match.group(0))} ", current)
    current = URL_RE.sub(lambda match: f" {_verbalize_url(match.group(0))} ", current)
    current = _record_step(decisions, "web_span_spoken_form", before, current)

    before = current
    for pattern, spoken in ABBREVIATIONS:
        current = pattern.sub(spoken, current)
    current = _record_step(decisions, "abbreviation_expansion", before, current)

    before = current
    for raw, spoken in SYMBOL_SPOKEN_FORMS.items():
        current = current.replace(raw, spoken)
    current = _record_step(decisions, "symbol_spoken_form", before, current)

    before = current
    current = _phones.normalize_phones_in_text(current)
    current = _record_step(decisions, "ne_phone_number", before, current)

    before = current
    current = _numbers.normalize_numbers_in_text(current)
    current = _record_step(decisions, "ne_cardinal_number", before, current)

    before = current
    current = _clean_spacing(current)
    current = _record_step(decisions, "spacing_cleanup", before, current)

    return current, decisions


def _record_step(decisions: list[dict], rule: str, before: str, after: str) -> str:
    if after != before:
        decisions.append({
            "type": "text_normalization",
            "rule": rule,
            "before": before,
            "after": after,
        })
    return after


def _clean_spacing(text: str) -> str:
    text = WHITESPACE_RE.sub(" ", text).strip()
    text = re.sub(r"\s+([,;:!?।॥])", r"\1", text)
    text = re.sub(r"([,;:])(?=\S)", r"\1 ", text)
    return text


def _verbalize_url(raw: str) -> str:
    body, trailing = _split_trailing_punctuation(raw)
    parse_target = body if "://" in body else f"https://{body}"
    parsed = urlsplit(parse_target)
    parts: list[str] = []
    if body.lower().startswith("https://"):
        parts.extend(["H", "T", "T", "P", "S"])
    elif body.lower().startswith("http://"):
        parts.extend(["H", "T", "T", "P"])
    if body.lower().startswith("www."):
        parts.extend(["W", "W", "W"])

    host = parsed.netloc or parsed.path.split("/", 1)[0]
    if host:
        parts.extend(_verbalize_domain(host))

    path = parsed.path
    if parsed.netloc and path:
        parts.extend(_verbalize_path(path))
    if parsed.query:
        parts.append("question")
        parts.extend(_verbalize_path(parsed.query.replace("&", "/")))
    return " ".join(part for part in parts if part) + trailing


def _verbalize_email(raw: str) -> str:
    local, domain = raw.split("@", 1)
    parts = _verbalize_identifier(local)
    parts.append("at")
    parts.extend(_verbalize_domain(domain))
    return " ".join(part for part in parts if part)


def _verbalize_domain(domain: str) -> list[str]:
    out: list[str] = []
    for idx, label in enumerate(part for part in domain.split(".") if part):
        if idx:
            out.append("dot")
        out.extend(_verbalize_identifier(label))
    return out


def _verbalize_path(path: str) -> list[str]:
    out: list[str] = []
    for part in path.strip("/").split("/"):
        if out:
            out.append("slash")
        out.extend(_verbalize_identifier(part))
    return out


def _verbalize_identifier(value: str) -> list[str]:
    out: list[str] = []
    chunk = ""
    separators = {
        ".": "dot",
        "-": "dash",
        "_": "underscore",
        "+": "plus",
        "=": "equals",
    }
    for ch in value:
        if ch.isalnum():
            chunk += ch
            continue
        if chunk:
            out.append(chunk)
            chunk = ""
        spoken = separators.get(ch)
        if spoken:
            out.append(spoken)
    if chunk:
        out.append(chunk)
    return out


def _split_trailing_punctuation(raw: str) -> tuple[str, str]:
    idx = len(raw)
    while idx and raw[idx - 1] in TRAILING_URL_PUNCT:
        idx -= 1
    return raw[:idx], raw[idx:]
