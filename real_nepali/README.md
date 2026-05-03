# real_nepali

This folder is the new clear-standard Nepali G2P research track. It is separate
from `nepali_frontend` because we need to test a broader listener target without
destroying the existing reproducible frontend.

Read [RESEARCH.md](RESEARCH.md) first. The important correction is that the
published literature does **not** support a casual equation of
`ts/tsh/dz/dzh` with "Newari Nepali"; Khatiwada 2009 describes the mass-media
standard and still analyzes the affricates that way. The current affricate
rewrite is therefore an experimental TTS profile for listener tests, not a
proven phonological fix.

The first experimental change is narrow: keep the working lexicon, schwa rules,
anusvara rules, and text normalization, but rewrite the affricate labels:

| Old policy | New clear-standard label |
|---|---|
| `ts` च | `ch` |
| `tsh` छ | `chh` |
| `dz` ज | `j` |
| `dzh` झ | `jh` |

This is a product/acoustic target decision. It must be judged by native
listening and TTS quality, not by blindly optimizing the old Wiktionary number.

## Try it

```bash
python3 -m real_nepali.g2p "चार छ आज मान्छे चीन"
```

## Rebuild a training manifest

Use this when preparing new training data so the `phones` column comes from the
clear-standard profile:

```bash
python3 -m real_nepali.manifest \
  --in /home/ubuntu/data/manifests/train.tsv \
  --out /home/ubuntu/data/manifests/train.real_nepali.tsv
```

## Current boundaries

- Sibilants (`श`, `ष`, `स`) still collapse to `s` by default. That is kept
  because Khatiwada/Regmi support the collapse for ordinary spoken Nepali.
- ञ/ण still collapse to `n` by default for the same reason.
- `व` remains lexicon-led (`b` or `w` where the lexicon says so; rule fallback
  still uses `w`). This needs a review pass because it is one of the largest
  remaining pronunciation-error sources.
