"""Generate static review assets for the G2P comparison UI.

This script renders two audio files per review word with eSpeak NG's vocoder:

- existing profile: `nepali_frontend` phones, with affricates rendered as
  alveolar-ish `ts/dz` eSpeak bracket phonemes.
- real_nepali profile: `real_nepali` phones, with affricates rendered as
  postalveolar-ish `tS/dZ` eSpeak bracket phonemes.

The eSpeak rendering is only a fixed-vocoder baseline. It is not a final TTS
quality claim.
"""

from __future__ import annotations

import argparse
import csv
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from nepali_frontend.g2p import phonemizer as old_g2p
from real_nepali import g2p as real_g2p

ESPEAK = shutil.which("espeak-ng") or shutil.which("espeak")
DEFAULT_WORDS = ROOT / "real_nepali" / "data" / "review_words.tsv"
DEFAULT_OUT = ROOT / "review-ui" / "public"

BASE_PHONE_MAP: dict[str, str] = {
    "i": "i",
    "e": "e:",
    "ax": "V",
    "aa": "a:",
    "o": "o:",
    "u": "u",
    "in": "i~",
    "en": "e:~",
    "axn": "V~",
    "aan": "a:~",
    "un": "u~",
    "axj": "VI",
    "axw": "VU",
    "aaj": "aI",
    "aaw": "aU",
    "oj": "oI",
    "ew": "eU",
    "ow": "oU",
    "axjn": "VI~",
    "axwn": "VU~",
    "aajn": "aI~",
    "aawn": "aU~",
    "ojn": "oI~",
    "own": "oU~",
    "p": "p",
    "ph": "p#",
    "b": "b",
    "bh": "b#",
    "t": "t",
    "th": "t#",
    "d": "d",
    "dh": "d#",
    "tx": "t.",
    "txh": "t.#",
    "dx": "d.",
    "dxh": "d.#",
    "k": "k",
    "kh": "k#",
    "g": "g",
    "gh": "g#",
    "m": "m",
    "n": "n",
    "ng": "N",
    "r": "r",
    "s": "s",
    "h": "h",
    "l": "l",
    "y": "j",
    "w": "w",
    "sh": "S",
    "sx": "S.",
    "ny": "n^",
    "nx": "n.",
    "f": "f",
    "z": "z",
}

OLD_PROFILE_MAP = {
    **BASE_PHONE_MAP,
    "ts": "ts",
    "tsh": "ts h",
    "dz": "dz",
    "dzh": "dz h",
}

REAL_PROFILE_MAP = {
    **BASE_PHONE_MAP,
    "ch": "tS",
    "chh": "tS h",
    "j": "dZ",
    "jh": "dZ h",
}


def slug(index: int, text: str) -> str:
    return f"{index:02d}_{text}"


def to_espeak_payload(phones: list[str], mapping: dict[str, str]) -> str:
    out: list[str] = []
    for phone in phones:
        if phone == ".":
            continue
        base = phone
        geminated = False
        if base.endswith(":"):
            base = base[:-1]
            geminated = True
        mapped = mapping.get(base, base)
        out.append(f"{mapped} {mapped}" if geminated else mapped)
    return "[[" + " ".join(out) + "]]"


def synth(payload: str, out_path: Path) -> None:
    if not ESPEAK:
        raise RuntimeError("espeak-ng/espeak not found on PATH")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [ESPEAK, "-v", "ne", "-s", "135", "-w", str(out_path), payload],
        check=True,
        capture_output=True,
        timeout=15,
    )
    if not out_path.exists() or out_path.stat().st_size <= 44:
        raise RuntimeError(f"failed to render audio: {out_path}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--words", type=Path, default=DEFAULT_WORDS)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()

    args.out.mkdir(parents=True, exist_ok=True)
    audio_dir = args.out / "samples"
    audio_dir.mkdir(parents=True, exist_ok=True)

    items: list[dict] = []
    with open(args.words, encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for index, row in enumerate(reader, start=1):
            text = row["text"]
            old = old_g2p.phonemize_word(text)
            real = real_g2p.phonemize_word(text)
            item_slug = slug(index, text)
            old_payload = to_espeak_payload(old.phones, OLD_PROFILE_MAP)
            real_payload = to_espeak_payload(real.phones, REAL_PROFILE_MAP)
            old_wav = audio_dir / f"{item_slug}_old.wav"
            real_wav = audio_dir / f"{item_slug}_real.wav"
            synth(old_payload, old_wav)
            synth(real_payload, real_wav)
            items.append({
                "id": item_slug,
                "text": text,
                "focus": row.get("focus", ""),
                "why": row.get("why", ""),
                "old": {
                    "label": "Existing G2P",
                    "source": old.source,
                    "phones": old.phones,
                    "phoneString": " ".join(old.phones),
                    "espeakPayload": old_payload,
                    "audio": f"/samples/{old_wav.name}",
                },
                "real": {
                    "label": "real_nepali",
                    "source": real.source,
                    "phones": real.phones,
                    "phoneString": " ".join(real.phones),
                    "espeakPayload": real_payload,
                    "audio": f"/samples/{real_wav.name}",
                },
                "changed": old.phones != real.phones,
            })

    payload = {
        "title": "Nepali G2P Listening Review",
        "generatedBy": "tools/generate_review_ui_assets.py",
        "note": (
            "Fixed-vocoder baseline: both samples use eSpeak NG's vocoder. "
            "The audio is for G2P comparison, not final TTS quality."
        ),
        "items": items,
    }
    (args.out / "review-data.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"wrote {args.out / 'review-data.json'} ({len(items)} items)")
    print(f"wrote audio under {audio_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

