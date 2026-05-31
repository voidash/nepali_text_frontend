# Quality Gate for Clear Nepali TTS

The code in this repository can generate deterministic phone strings. That is
not the same thing as proving a TTS voice will sound clear, neutral, and
mainstream to Nepali listeners.

Before using `real_nepali` for a production TTS model, pass these gates.

## Gate 1: Mechanical Correctness

Must pass:

```bash
python3 -m pytest tests/
python3 -m real_nepali.g2p "चार छ आज मान्छे चीन"
python3 tools/emit_review_sheet.py --out /tmp/real_nepali_review.tsv
```

Purpose: make sure tokenization, lexicon lookup, normalization, and the
experimental profile run reproducibly.

Current status: passing at repo creation.

## Gate 2: Phone Inventory Audit

For every emitted phone in a training manifest:

- the phone must exist in the intended model phone inventory,
- no old and new affricate labels should be mixed in one manifest unless the
  model inventory intentionally supports both,
- `g2p_path` should identify which profile produced the row.

Failure mode this prevents: training a model on inconsistent phoneme labels and
then misdiagnosing the resulting accent as a data problem.

## Gate 3: Native Review Sheet

Generate review rows:

```bash
python3 tools/emit_review_sheet.py --out review.tsv
```

Run Wiktionary sanity checks:

```bash
python3 tools/compare_wiktionary_ne_ipa.py --source testcases --out /tmp/wiktionary_ne_ipa_testcases.tsv
python3 tools/compare_wiktionary_ne_ipa.py --source words --out /tmp/wiktionary_review_words.tsv
```

Interpret the strict Wiktionary score carefully: Wiktionary's `Module:ne-IPA`
uses `t͡s/t͡sʰ/d͡z/d͡zʱ` for च/छ/ज/झ, so an affricate-sensitive score will prefer
the old profile. Use the affricate-neutral score to check whether `real_nepali`
changed anything beyond the intended affricate target.

At minimum, collect native judgments for:

- affricates: `चार`, `छ`, `आज`, `मान्छे`, `चीन`, `सञ्चार`
- `व`: `वर्ष`, `विकास`, `विश्वास`, `विश्वविद्यालय`, `प्रभाव`
- sibilants: `शिक्षा`, `शक्ति`, `शासन`, `संस्कृति`
- nasals: `गुण`, `ज्ञान`, `पञ्च`
- schwa: `सुलोचना`, `नेपालले`, `संविधान`, `अगाडि`

Question to ask reviewers:

> Which pronunciation should a clear mainstream Nepali TTS voice use?

Do not ask only "is this valid?" Multiple pronunciations can be valid while
only one fits the product voice.

## Gate 4: Fixed-Synthesizer A/B

Before retraining VITS/Piper, render old and new phone strings through the same
simple synthesizer or phone-audio tool. This isolates G2P from neural-model
training effects.

Pass condition:

- reviewers prefer the `real_nepali` output on targeted categories, or
- reviewers identify a more precise correction that becomes the next profile.

## Gate 5: Canonical Frontend Manifest

When training:

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

Then audit the output manifest before preprocessing. Do not train from an old
manifest or from backend-specific code that calls lower-level G2P directly.
The manifest must be stamped with:

- `frontend=nepali_frontend.frontend.process`
- `frontend_profile=real_nepali`
- `frontend_version`
- `normalized_text`
- `frontend_warning_count`

## Gate 6: Listening Checkpoints

For TTS training, every milestone must include the same fixed sentence set and
speaker IDs. Evaluate by category:

- affricates,
- `व`,
- schwa,
- nasals,
- sibilants,
- loan/code-mix,
- duration clarity.

Do not choose checkpoints by `val_loss` alone. The previous TTS work showed
that loss can improve while intelligibility and voice consistency remain wrong.

## Bottom Line

The intrinsic value of a good TTS voice is intelligibility and clarity, not a
clever phone inventory. This repo is only ready for production training after
the pronunciation target passes native review and A/B listening.
