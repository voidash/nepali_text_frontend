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

For TTS integration, use the manifest contract in
[`docs/FRONTEND_CONTRACT.md`](docs/FRONTEND_CONTRACT.md). Training pipelines
should consume stamped manifests from `python3 -m real_nepali.manifest`, not
call lower-level G2P functions directly.

## Try G2P

Full frontend pipeline:

```bash
python3 -m nepali_frontend normalize "AI ले २५% growth देखायो."
python3 -m nepali_frontend phonemize "AI ले २५% growth देखायो."
python3 -m nepali_frontend trace "AI ले २५% growth देखायो."
```

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

Generate and audit a canonical TTS manifest:

```bash
python3 -m real_nepali.manifest \
  --in train.tsv \
  --out train.frontend.tsv \
  --profile real_nepali

python3 -m real_nepali.manifest \
  --in train.frontend.tsv \
  --profile real_nepali \
  --audit-only \
  --verify-phones
```

Generate a native-review TSV:

```bash
python3 tools/emit_review_sheet.py --out /tmp/real_nepali_review.tsv
```

Run the local listening UI:

```bash
python3 tools/generate_frontend_eval_data.py
python3 tools/generate_review_ui_assets.py
cd review-ui
npm install
npm run dev
```

The UI now has two views:

- `Frontend`: raw text, normalized text, token classes, code-switched spans,
  punctuation phones, chunks, and warnings.
- `Listening`: fixed-vocoder G2P A/B samples for native review.

## Research Position

Do not treat the `real_nepali` affricate relabeling as settled phonology.
The research document explicitly notes that Khatiwada 2009 describes standard
mass-media/eastern Nepali while still analyzing च/छ/ज/झ as alveolar affricates.
The current `real_nepali` profile is an experimental TTS/listener target that
must be validated with native-speaker A/B tests.

## License And Notices

Code is MIT. Data tables include derived pronunciation resources; see
[`NOTICE.md`](NOTICE.md) before publishing or redistributing.
