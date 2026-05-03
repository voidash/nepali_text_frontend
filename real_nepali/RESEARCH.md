# Research Basis for the `real_nepali` G2P Track

Status: working research brief for the next G2P/TTS iteration.

This document is intentionally stricter than the code. It separates:

- **source-grounded phonological decisions** that should be stable,
- **engineering representation decisions** that are practical for a TTS model,
- **product hypotheses** that must be tested with native listeners.

It also corrects an important mistake in the first `real_nepali` fork: the
published literature does not support the simple statement "`ts/tsh/dz/dzh`
means Newari Nepali." Khatiwada's 2009 IPA illustration describes a standard
mass-media/eastern Nepali variety and still analyzes the affricates as alveolar.
So the affricate relabeling in this folder is only an experimental acoustic
profile until listening tests prove it helps.

## 1. Source Hierarchy

### Primary phonology sources

1. **Khatiwada 2009, "Nepali", Journal of the International Phonetic
   Association.** This is the strongest single source for standard Nepali
   segmental phonology. It describes a standard variety used in national mass
   media, based mainly on an eastern-Nepal speaker, and documents vowels,
   consonants, affricates, retroflexes, rhotics, nasals, aspiration, gemination,
   stress, and dialect notes. Source: Cambridge Core,
   DOI `10.1017/S0025100309990181`.
   <https://www.cambridge.org/core/journals/journal-of-the-international-phonetic-association/article/nepali/A887820E3B1293EFD43FBD3259D41F73>

2. **Khatiwada 2019, "Retroflexion in Nepali", Gipan.** This gives direct
   palatographic/linguographic evidence for retroflex variability and supports
   keeping a retroflex category while recognizing that the phonetic target is
   often cacuminal/post-alveolar rather than strongly sub-apical.
   <https://www.nepjol.info/index.php/gipan/article/download/35453/27733/103194>

3. **Regmi 2025, "Variation in Nepali Verb Roots: A Phonological Perspective",
   Gipan.** This is recent TU work using 1,892 verb roots from a Nepali
   dictionary. It gives a compact phoneme-to-Devanagari mapping, says Nepali has
   no length contrast for `i/u`, maps `ञ/ण` to `n`, maps `श/ष` to `s`, and
   discusses schwa deletion and syllable structure.
   <https://www.nepjol.info/index.php/gipan/article/view/84240>

4. **Pokharel 1989, Experimental Analysis of Nepali Sound System.** We use it
   through Khatiwada/Regmi citations and the TU library record because the full
   thesis is not locally available in this repo. It is still important for
   diphthongs, rhotics, and affricate/retroflex experimental background.
   <https://opac.tucl.edu.np/cgi-bin/koha/opac-detail.pl?biblionumber=6217>

### Engineering and comparison sources

5. **Google language-resources Nepali lexicon / SLTU 2018 paper.** This is the
   largest structured open Nepali pronunciation lexicon we have. The Google
   paper states that its released resources include audio, pronunciation
   lexicons, and phonology definitions for Nepali and other low-resource
   languages.
   <https://research.google/pubs/a-step-by-step-process-for-building-tts-voices-using-open-source-data-and-framework-for-bangla-javanese-khmer-nepali-sinhala-and-sundanese/>

6. **Wiktionary `Module:ne-IPA`.** This is not an academic source, but it is an
   independent executable pronunciation reference. Its testcases expose useful
   practical judgments, especially `व -> b/w`, rhotics, retroflex flap, and
   gemination. Use it as a diagnostic comparator, not as ground truth.
   <https://en.wiktionary.org/wiki/Module:ne-IPA>

7. **eSpeak NG `ne_rules`.** eSpeak is useful as a negative and capability
   baseline. It supports Nepali, but our earlier audits found it over-retains
   orthographic distinctions, stress, length, and schwas. We should not optimize
   toward eSpeak.
   <https://sources.debian.org/src/espeak-ng/1.49.0%2Bdfsg-11/dictsource/ne_rules>

## 2. Target Definition

The target is **clear mainstream Nepali for TTS**, not a scholarly demo of
maximum phonetic narrowness and not Sanskrit-recitation spelling pronunciation.

That means:

- phonemic distinctions must be represented when they affect intelligibility,
- allophonic details should become model hints only when they improve audio,
- spelling-only distinctions should not be exposed as default phones unless
  native listeners prefer them in the production voice,
- every divergence from Khatiwada/Regmi needs either a corpus reason or a
  listener-test reason.

## 3. Decision Logic

The decision procedure for every segment is:

1. Prefer primary Nepali phonology sources over orthography.
2. Preserve a separate phone only if it is phonemic, needed for TTS acoustics,
   or consistently present in the curated lexicon/audio.
3. If sources and listener perception conflict, keep the source-grounded form as
   baseline and add an experimental profile rather than overwriting the base.
4. Do not import eSpeak behavior unless it is independently supported by Nepali
   sources or native review.
5. Treat Wiktionary as an independent sanity check and a source of candidate
   allophone rules, especially for `व`, `r`, and retroflex flap.

## 4. Vowels

### Oral vowels

Decision: keep six oral vowel labels:

`i e ax aa o u`

Rationale:

- Khatiwada describes six oral vowel qualities and treats the Nepali central
  vowel traditionally written as schwa as closer to `[ʌ]` than `[ə]`.
- Regmi lists six monophthongs and explicitly maps Devanagari `इ/ई` to `i` and
  `उ/ऊ` to `u`.
- Google's Nepali lexicon also uses these six oral vowel labels.

Implementation consequence:

- Keep `ax` for inherent अ.
- Keep `aa` for आ/ा, but do not interpret `aa` as a phonemic length contrast.
  It is a quality/orthographic label inherited from the lexicon and pipeline.

### Vowel length

Decision: **no default phonemic `ii/uu` contrast**.

Rationale:

- Khatiwada says written long/short `i/u` do not form a spoken length
  opposition.
- Regmi says Nepali has no length contrast even though Devanagari uses long and
  short symbols.

Implementation consequence:

- `ई/ी -> i`
- `ऊ/ू -> u`
- Vowel length should only appear as a duration/allophone hint in special
  cases such as /ɦ/-deletion, not as a normal phone.

### Nasalized vowels

Decision: keep nasalized counterparts for all vowels except phonemic `on`.

Current labels:

`in en axn aan un`

Rationale:

- Khatiwada says nasalization is distinctive, but /o/ lacks a phonemic nasal
  counterpart.
- Google's lexicon uses nasalized vowel labels, but rare `ojn/own` appear as
  diphthongal labels. They are engineering labels, not evidence for a simple
  monophthong `on`.

Implementation consequence:

- Keep current `NASALIZE["o"] = "o"` behavior for monophthong /o/.
- Keep `ojn/own` only if they occur in lexicon-derived diphthong contexts.

## 5. Diphthongs

Decision: keep Google's 13-label phonetic diphthong representation for TTS:

`axj axw aaj aaw oj ew ow axjn axwn aajn aawn ojn own`

Rationale:

- Pokharel is cited by Khatiwada as recognizing ten Nepali diphthongs.
- Regmi also lists ten diphthongs and shows that many are written as vowel
  sequences, not single Devanagari letters.
- Google uses a richer practical label set that splits nucleus quality and
  nasalization. This is useful for an acoustic model even if it is not a clean
  phonemic inventory.

Implementation consequence:

- Keep these labels as **TTS phones**, but document them as phonetic/acoustic
  labels rather than independent phonemes.
- Do not create extra Hindi-style `ai/au` labels unless a later tokenizer needs
  orthographic aliases.

## 6. Stops

Decision: keep the four-place, four-laryngeal stop system:

| Place | Phones |
|---|---|
| bilabial | `p ph b bh` |
| dental | `t th d dh` |
| retroflex | `tx txh dx dxh` |
| velar | `k kh g gh` |

Rationale:

- Khatiwada and Regmi both preserve these stop categories.
- Aspiration/breathy voice is contrastive and affects following-vowel phonation.
- Retroflexes are phonological in Khatiwada 2009/2019, even though exact
  articulation varies substantially.

Implementation consequence:

- Keep these as model phones.
- Add future allophone hints for voiced aspirate weakening and retroflex flap
  where useful, but do not collapse the base categories.

## 7. Retroflexes

Decision: keep retroflex stops as distinct phones, but do not force a strongly
sub-apical acoustic target.

Rationale:

- Khatiwada 2009 says Nepali retroflexes have a lesser degree of retroflexion
  than in some other South Asian languages.
- Khatiwada 2019 reports wide articulatory variation; one experiment found many
  productions were cacuminal rather than "real" retroflexion.
- Wiktionary testcases also distinguish initial `ड` from postvocalic retroflex
  flap behavior.

Implementation consequence:

- Base phones remain `tx/txh/dx/dxh`.
- Future acoustic profile should map postvocalic `dx` to a flap hint when the
  model/hifigan path can consume allophone hints.

## 8. Affricates

Decision baseline: keep source-grounded affricate phonemes as:

`ts tsh dz dzh`

Research rationale:

- Khatiwada 2009 explicitly reports Nepali affricates as laminal in the
  alveolar region, while noting that they may sound palato-alveolar to English
  and French listeners.
- Khatiwada 2019's dental/affricate experiment also places most dental and
  affricate productions in the dental-alveolar zone.
- Regmi lists the affricate series as `ʦ ʦʰ ʣ ʣʰ`.

Product hypothesis:

- Our trained voice sounded "Newari" to some listeners. The current evidence
  does not prove that affricate labels are the cause. It may be caused by
  training speakers, acoustic modeling, the synthetic/Barsha mix, duration,
  schwa, `व`, or affricate realization.
- The `real_nepali` code currently rewrites `ts/tsh/dz/dzh` to
  `ch/chh/j/jh` as an **experimental acoustic profile**, not as a new research
  fact.

Validation requirement:

- Before making `ch/chh/j/jh` the main production inventory, run native
  listener A/B on words such as `चार`, `छ`, `आज`, `मान्छे`, `चीन`, `सञ्चार`,
  `रचना`, and `चर्चा`.
- Test both isolated G2P audio and trained TTS samples. If the model improves
  only in neural TTS but not in phoneme-audio rendering, the issue is acoustic
  training rather than phonology.

## 9. Fricatives and Sibilants

Decision: default spoken Nepali has one sibilant `s` plus `h`.

Rationale:

- Khatiwada says Nepali has only two contrastive fricatives, /s/ and /ɦ/.
- Regmi maps `श` and `ष` to `s` in Nepali.
- Google's lexicon also collapses sibilants to `s`.

Implementation consequence:

- Default: `श/ष/स -> s`.
- Keep `sh/sx` only for an explicit careful Sanskritized or spelling-pronunciation
  mode.
- Do not let eSpeak's orthographic `श/ष` preservation drive the default TTS
  voice.

## 10. Nasals

Decision: default spoken Nepali has `m n ng`; `ny/nx` are not default phones.

Rationale:

- Khatiwada says only the first three nasals represented by Nepali orthography
  are phonologically pertinent.
- Regmi maps `ञ` and `ण` to `n`, while noting special contextual behavior for
  `ण`.
- Google has `m/n/ng` and no palatal nasal; retroflex nasal appears only as a
  source label that we collapsed in the original frontend.

Implementation consequence:

- Default: `ञ -> n`, `ण -> n`.
- Contextual anusvara before bilabials/dentals/velars should become `m/n/ng`.
- Keep `ny/nx` only in careful Sanskritized or lexically reviewed exceptions.

## 11. Anusvara and Chandrabindu

Decision:

- Chandrabindu is vowel nasalization.
- Anusvara defaults to nasalization but becomes a homorganic nasal before a
  suitable following consonant.

Rationale:

- Regmi states that chandrabindu represents nasalization, while anusvara can
  also represent a nasal consonant.
- This matches the current `apply_anusvara_context` rule and fixed a real
  lexicon-path bug for words such as `अंग/अंक`.

Implementation consequence:

- Keep the current contextual rule.
- Expand tests for `सञ्चार`, `संस्था`, `अंग्रेजी`, `अंक`, and `संस्कृति`.

## 12. Rhotics and Laterals

Decision: keep `r` and `l` as phonemic phones; add allophone hints later.

Rationale:

- Khatiwada describes /r/ with trill/tap variation: stronger trill in some
  positions, tap/flap intervocalically or word-finally, geminate /r/ fully
  trilled.
- Wiktionary testcases encode tapped `r` intervocalically.

Implementation consequence:

- Base G2P keeps `r`.
- Future acoustic profile can add `r_tap`/`r_trill` or duration hints if the
  model uses allophone tags.
- `ळ` should not be a default separate phone without specific Nepali evidence;
  current fallback to `l` is acceptable.

## 13. Glides and `व`

Decision now: keep `y` and `w` as practical model phones, but make `व` a
priority review area.

Rationale:

- Khatiwada treats `[j w]` as nonsyllabic variants of /i u/ in the consonant
  chart discussion.
- Regmi/Dahal include `j/w` or glides in the inventory, and a TTS frontend needs
  explicit labels for syllable onsets/offglides.
- Wiktionary testcases show `व` can surface as `b` in words such as `विश्वास`
  but as `w` in words such as `वरिपरि`.
- Our own reports already identify `व -> b/w` as a large disagreement bucket.

Implementation consequence:

- Do not hard-code a broad `व -> b` or `व -> w` rule.
- Build a reviewed lexical table for high-frequency `व` words.
- Keep current lexicon entries where they already say `b` or `w`.
- Rule fallback `व -> w` is only a placeholder.

## 14. Loan Phones

Decision: keep `f` and `z` as loan-only phones.

Rationale:

- Khatiwada excludes consonants unique to loans from the core chart.
- TTS still needs to pronounce English and modern loanwords.
- Google folds many loans into native approximations, so lexicon imports are
  not sufficient for modern code-mixed text.

Implementation consequence:

- Nukta spellings `फ़/ज़` may emit `f/z`.
- Latin-script words should go through a code-switch path, not silent Nepali
  G2P.
- Do not turn native `फ/ज` into `f/z` by default.

## 15. Visarga

Decision needed: default clear Nepali should probably drop `ः` except in
careful/Sanskritized mode.

Rationale:

- Regmi states that the visarga symbol occurs in writing in a few cases but is
  not pronounced.
- Current old frontend emits `h` for visarga. That is safe for Sanskritic
  spelling pronunciation but probably wrong for ordinary clear Nepali.

Implementation consequence:

- Add a `real_nepali` rule to drop visarga in default mode.
- Keep `h` in careful recitation mode.
- Add tests before changing this because some proper names or religious terms
  may need careful style.

## 16. Gemination

Decision: keep gemination as a model phone marker (`p:`, `k:`, etc.).

Rationale:

- Khatiwada states consonants except glottal fricative and approximants have
  geminate counterparts, and geminates occur medially.
- Wiktionary testcases also show gemination for words such as `सम्म` and
  `चप्पल`.

Implementation consequence:

- Keep the current `<phone>:` representation for training.
- For `real_nepali`, affricate geminates should rewrite consistently:
  `ts: -> ch:`, `tsh: -> chh:`, etc.

## 17. Schwa

Decision: keep conservative Nepali schwa deletion, not Hindi-style deletion.

Rationale:

- Regmi notes inherent अ is absent in many final positions and some compound
  medial positions.
- The Indo-Aryan schwa-deletion summary notes Nepali-specific verb retention
  behavior and warns that blindly hardcoding inherent schwas gives written form
  rather than pronunciation.
- Our own lexicon xval showed many remaining disagreements are schwa-position
  disagreements, especially compounds.

Implementation consequence:

- Keep final schwa deletion for ordinary non-verb words.
- Keep verb-final retention unless halanta removes it.
- Keep compound schwa deletion conservative; expand with reviewed examples
  rather than importing Hindi VC_CV deletion.
- Add a native-review list: `सुलोचना`, `संविधान`, `नेपालले`, `अगाडि`,
  `राजमार्ग`, `समाचार`, `विद्यालय`.

## 18. Stress and Pitch

Decision: no default stress/pitch phones.

Rationale:

- Khatiwada says stress and pitch are non-distinctive in Nepali.
- eSpeak emits stress-like artifacts; those should not become our target.

Implementation consequence:

- Prosody should be learned from punctuation, syntax, and data, not lexical
  stress tokens.

## 19. Why Not eSpeak

eSpeak is useful because it is executable, broad, and handles code-switching
better than our first frontend. It is not a good target for Nepali phonology.

Observed issues from local reports:

- preserves orthographic length,
- preserves spelling-only Sanskrit distinctions,
- adds stress,
- retains too many schwas,
- gives 100% minimal-pair preservation partly by preserving non-phonemic
  orthographic contrasts.

What to borrow:

- code-switch routing,
- some allophone ideas if independently validated,
- engineering tests, not the actual default pronunciations.

## 20. Current `real_nepali` Code Status

| Area | Status | Notes |
|---|---|---|
| separate folder/package | done | `real_nepali/` exists |
| affricate experimental rewrite | done | `ts/tsh/dz/dzh -> ch/chh/j/jh` |
| source-grounded full policy | this document | still needs review |
| `व` review table | started | `real_nepali/data/review_words.tsv` |
| visarga default drop | not done | research suggests it should be tested |
| allophone hints for `r`/retroflex flap | not done | future acoustic tag work |
| code-switch path | not done | high product priority |
| native listener protocol | not done | required before claiming "proper clear Nepali" |

## 21. Phone-by-Phone Decision Table

This table is deliberately explicit. `Decision` means the default
clear-mainstream G2P target unless marked as experimental or careful style.

| Phone/letter area | Decision | Evidence basis | Implementation status |
|---|---|---|---|
| `i` | keep | Khatiwada/Regmi six-vowel inventory; Google lexicon | done |
| `e` | keep | Khatiwada/Regmi six-vowel inventory; Google lexicon | done |
| `ax` | keep for inherent अ | Khatiwada central/open-mid vowel analysis; Devanagari inherent vowel | done |
| `aa` | keep as आ/ा quality label, not length | no phonemic length contrast; Google label compatibility | done |
| `o` | keep | Khatiwada/Regmi six-vowel inventory | done |
| `u` | keep | Khatiwada/Regmi six-vowel inventory | done |
| `ii`, `uu` | reject default | no spoken length contrast | already absent |
| `in`, `en`, `axn`, `aan`, `un` | keep | contrastive nasalization; Google lexicon | done |
| monophthong `on` | reject default | Khatiwada notes no phonemic nasal /o/ counterpart | done |
| `axj`, `axw`, `aaj`, `aaw`, `oj`, `ew`, `ow` | keep as TTS diphthong labels | Pokharel/Regmi diphthongs plus Google practical labels | done |
| `axjn`, `axwn`, `aajn`, `aawn`, `ojn`, `own` | keep as rare nasal diphthong labels | Google lexicon; useful acoustic labels | done |
| `p ph b bh` | keep | contrastive bilabial stop series | done |
| `t th d dh` | keep dental | contrastive dental stop series | done |
| `tx txh dx dxh` | keep retroflex category | Khatiwada 2009/2019; Regmi | done |
| `k kh g gh` | keep | contrastive velar stop series | done |
| `ts tsh dz dzh` | source-grounded baseline | Khatiwada/Regmi affricate analysis | old frontend done |
| `ch chh j jh` | experimental product labels | listener/acoustic hypothesis, not primary-source correction | `real_nepali` done |
| `m n ng` | keep | three default nasal places | done |
| `ny`, `nx` | careful style only | Khatiwada/Regmi collapse `ञ/ण` in default | old inventory has labels; default does not emit |
| `r` | keep | phonemic rhotic with tap/trill allophones | done |
| tap/trill split | allophone hint only | Khatiwada + Wiktionary tests | not done |
| `l` | keep | phonemic lateral | done |
| `ळ` | map to `l` unless reviewed | rare; insufficient default evidence | done in old base map |
| `s` | keep sole default sibilant | Khatiwada/Regmi; Google lexicon | done |
| `sh`, `sx` | careful style only | spelling/Sanskritized distinction, not default spoken contrast | labels exist; mode not implemented |
| `h` | keep for ह | Khatiwada /ɦ/ with voiceless allophone variation | done |
| voiced-aspirate breathy vowel | allophone hint only | Khatiwada/Pokharel; acoustic not phonemic label | not done |
| `y` | keep practical TTS phone | glide needed for G2P; Regmi/Dahal include glides | done |
| `w` | keep practical TTS phone | glide needed; but `व` needs lexical review | done |
| `व -> b/w` | lexicon/review, not broad rule | Wiktionary and local reports show split behavior | partial via lexicon |
| `f`, `z` | loan-only | Khatiwada excludes loan-only phones from core; modern TTS needs them | done for nukta/loan paths partly |
| `ः` visarga | drop default, keep careful | Regmi says written but not pronounced | not done |
| anusvara before stops | homorganic nasal | Regmi; current rule validated | done |
| chandrabindu | vowel nasalization | Regmi | done |
| gemination | keep `<phone>:` | Khatiwada and Wiktionary examples | done |
| stress/pitch | no phone labels | Khatiwada says non-distinctive | done |
| Latin code-mix | route separately | eSpeak capability gap; product need | not done |

## 22. Validation Plan

Before retraining a final model:

1. **Create a 100-word native-review set** covering all categories above.
   Minimum: affricates, `व`, sibilants, nasals, retroflexes, visarga,
   schwa-sensitive words, loanwords, code-mix.

2. **Generate three G2P variants for each word:**
   - old `nepali_frontend`,
   - `real_nepali` experimental profile,
   - Wiktionary IPA where available.

3. **Ask native listeners for target preference**, not just correctness:
   "Which pronunciation should a clear mainstream Nepali TTS voice use?"

4. **Retrain only after the manifest is rephonemized** with the chosen profile.
   Mixing old and new phone labels in one acoustic model will make listening
   results ambiguous.

5. **Report results by category.**
   Do not claim the whole G2P improved if only affricates improved. Track:
   affricates, `व`, schwa, nasals, sibilants, loans, and prosody separately.

## 23. Immediate Engineering Follow-Up

1. Add `real_nepali` default visarga policy behind a test.
2. Build `tools/compare_real_nepali.py` to output old/new/Wiktionary rows for
   `real_nepali/data/review_words.tsv`.
3. Add a high-frequency `व` review file from `word_frequency.tsv`.
4. Generate A/B audio with a fixed synthesizer before retraining.
5. Only then regenerate training manifests and launch a new model.

## 24. Bottom Line

The core G2P should remain grounded in Khatiwada, Regmi, Pokharel, and the
Google lexicon. The old frontend was not "bad because eSpeak differs"; eSpeak
is worse on several documented phonology points. The real problem is that our
TTS output did not sound like the broad clear Nepali voice we want.

The correct response is not to guess a new inventory. It is to:

- keep source-grounded phonology,
- isolate experimental product profiles,
- validate the disputed categories with native listeners,
- rephonemize training manifests consistently,
- train and evaluate by pronunciation category.
