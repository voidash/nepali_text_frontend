# Clear-Standard Nepali Policy

Goal: a clear, mainstream Nepali TTS pronunciation target, separated from the
old frontend so we can test listener preference and avoid mixing incompatible
training assumptions.

This is not a claim that other dialects are invalid. It is a production choice:
the voice should sound like neutral, clear Nepali to a broad Nepali audience.

## v0 Decisions

1. **Affricates are the first experimental fork.**
   The existing frontend labels च/छ/ज/झ as `ts/tsh/dz/dzh`, and that is
   research-grounded for the standard described by Khatiwada. For this profile,
   output `ch/chh/j/jh` only as an acoustic/product experiment to test whether
   native listeners prefer that target with our training data.

2. **Keep the existing lexicon and schwa rules for now.**
   Those pieces are already much better than eSpeak and are responsible for the
   old 77% agreement with Wiktionary on common words.

3. **Do not re-import eSpeak behavior wholesale.**
   eSpeak preserves stress, length, too many final schwas, and orthographic
   Sanskrit distinctions. Those are not the target.

4. **Review `व` next.**
   The old reports already show `व` as a large source of disagreement. We need
   native judgments for common words before hard-coding a broad `w -> b` rule.

5. **Careful Sanskritized mode is separate.**
   If the voice should say school-recitation Sanskritized `श/ष/ञ/ण`, that should
   be an explicit style, not the default clear Nepali TTS mode.

For the full evidence table, use [RESEARCH.md](RESEARCH.md).

## Acceptance Tests To Add Over Time

- Common affricate words: `चार`, `छ`, `आज`, `मान्छे`, `चीन`, `सञ्चार`.
- Common `व` words: `वर्ष`, `विकास`, `विश्वास`, `प्रभाव`, `विश्वविद्यालय`.
- Common sibilant words: `शिक्षा`, `शक्ति`, `शासन`, `संस्कृति`.
- Schwa-sensitive words: `सुलोचना`, `नेपालले`, `संविधान`, `अगाडि`.
