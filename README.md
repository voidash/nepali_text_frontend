# Nepali Text Frontend

Research-grounded Nepali text normalization and grapheme-to-phoneme frontend
for TTS work.

This repo is the clean text-frontend workspace split out from the larger
private TTS training repo. It intentionally excludes AWS notes, checkpoints,
training logs, sample audio, and internal operational files.

## Packages

- `nepali_frontend`: original deterministic frontend with lexicon lookup,
  akshara parsing, schwa/anusvara rules, normalization, and trace support.
- `real_nepali`: research track for a clear-mainstream Nepali TTS target.
  Start with [`real_nepali/RESEARCH.md`](real_nepali/RESEARCH.md).

## Install

```bash
python3 -m pip install -e ".[test]"
```

## Run Tests

```bash
python3 -m pytest tests/
```

For the pronunciation/retraining checklist, see
[`docs/QUALITY_GATE.md`](docs/QUALITY_GATE.md).

## Try G2P

Original frontend:

```bash
python3 - <<'PY'
from nepali_frontend.g2p import phonemizer
for word in ["चार", "छ", "आज", "मान्छे", "चीन"]:
    print(word, phonemizer.phonemize_word(word).phones)
PY
```

Research profile:

```bash
python3 -m real_nepali.g2p "चार छ आज मान्छे चीन"
```

Generate a native-review TSV:

```bash
python3 tools/emit_review_sheet.py --out /tmp/real_nepali_review.tsv
```

Run the local listening UI:

```bash
python3 tools/generate_review_ui_assets.py
cd review-ui
npm install
npm run dev
```

## Research Position

Do not treat the `real_nepali` affricate relabeling as settled phonology.
The research document explicitly notes that Khatiwada 2009 describes standard
mass-media/eastern Nepali while still analyzing च/छ/ज/झ as alveolar affricates.
The current `real_nepali` profile is an experimental TTS/listener target that
must be validated with native-speaker A/B tests.

## License And Notices

Code is MIT. Data tables include derived pronunciation resources; see
[`NOTICE.md`](NOTICE.md) before publishing or redistributing.
