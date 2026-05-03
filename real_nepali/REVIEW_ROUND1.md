# Listening Review Round 1

Date: 2026-05-03

Source: browser localStorage for the local review UI at `localhost:5173`.

Review set:

- 149 items in `review-ui/public/review-data.json`
- 148 saved judgments
- 1 missing judgment: `123_महासचिव`

Vote summary:

| vote | count |
|---|---:|
| `real` | 130 |
| `tie` | 15 |
| `old` | 2 |
| `bad` | 1 |
| missing | 1 |

Rows needing follow-up:

| id | text | vote | old phones | real phones | note |
|---|---|---|---|---|---|
| `30_जिल्ला` | जिल्ला | `old` | `dz i l . l aa` | `j i l . l aa` | possible exception or eSpeak artifact |
| `42_सूचना` | सूचना | `old` | `s u . ts ax . n aa` | `s u . ch ax . n aa` | possible exception or eSpeak artifact |
| `134_छोरा` | छोरा | `bad` | `tsh o . r aa` | `chh o . r aa` | both eSpeak samples bad |
| `123_महासचिव` | महासचिव | missing | `m ax . h aa . s ax . ts i b` | `m ax . h aa . s ax . ch i b` | no saved vote |

Interpretation:

The first-pass result strongly supports the `real_nepali` affricate profile for
the review set, but `छोरा` shows that the fixed eSpeak A/B is not a reliable
final judge for every aspirated-affricate token. Wiktionary gives `छोरा` as
`t͡sʰoɾä`; the old phones match that broad form and the `real_nepali` phones
match it when the affricate-place choice is neutralized. The likely issue is the
review renderer's bracket payload (`ts h` / `tS h`) behaving like affricate plus
separate `h`, not a clean aspirated affricate.

Next action:

Do not turn the `छोरा` bad sample into a G2P rule change yet. Use it as a
round-2 audio-rendering probe for aspirated affricates before deciding whether
any lexicon override is needed.
