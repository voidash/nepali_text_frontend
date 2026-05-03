"""Post-rules applied to base akshara phones.

Each rule is small, named, deterministic, and traceable. The phonemizer
calls them in order; each rule may emit a `decision` event for the
trace.

Rules (all default mode, `spoken_nepali`):

1. `apply_anusvara_context` — anusvara before a homorganic plosive
   becomes the corresponding nasal consonant; otherwise stays as
   vowel nasalization (already applied in akshara base).
2. `apply_gemination` — virama-joined identical consonants emit a
   geminate length marker (and survive lenition rules).
3. `apply_schwa_deletion` — the four documented Nepali schwa-retention
   rules (conjunct retention, verb retention, adverb/postposition
   retention, compound-postposition halanta attachment). Inverse:
   delete the inherent vowel where none of the retention rules fire.
4. `apply_suffix_strip` — when a word missed the lexicon, try
   stripping a known case suffix and re-looking-up the bare root.

The schwa rule operates on a *whole word* parse: it needs to know
whether the final akshara is a conjunct, whether the word is a verb
form, etc. The phonemizer feeds it the full akshara list.
"""

from __future__ import annotations

from typing import Optional

from . import base_map as bm
from .akshara import Akshara

# Phones that act as nasal consonants (used to detect homorganic anusvara)
NASAL_PHONES = {"m", "n", "ng"}

# Place assimilation: anusvara before a plosive at place X becomes
# the nasal at place X.
PLACE_TO_NASAL = {
    # Bilabial
    "p": "m", "ph": "m", "b": "m", "bh": "m",
    # Velar
    "k": "ng", "kh": "ng", "g": "ng", "gh": "ng",
    # Dental, retroflex, alveolar — all assimilate to the alveolar /n/
    # in default mode (palatal /ɲ/ and retroflex /ɳ/ are not phonemic,
    # per Khatiwada 2009).
    "t": "n", "th": "n", "d": "n", "dh": "n",
    "tx": "n", "txh": "n", "dx": "n", "dxh": "n",
    "ts": "n", "tsh": "n", "dz": "n", "dzh": "n",
}

# Nasalized-vowel phone → equivalent nasal consonant for de-nasalization
# when an anusvara turned out to be a contextual nasal consonant.
NASALIZED_TO_ORAL = {
    "axn": "ax", "aan": "aa", "in": "i",
    "un": "u", "en": "e",
    "axjn": "axj", "axwn": "axw",
    "aajn": "aaj", "aawn": "aaw",
    "ojn": "oj", "own": "ow",
}


# ---- Schwa deletion ------------------------------------------------------

# Verb-form heuristic: a word is treated as a verb form if it ends in
# any of these recognisable verbal endings (very rough; lexicon
# overrides supersede). Used to apply Rule 2 (verb retention).
VERB_ENDINGS_DEVA = (
    "्छ", "्छन्", "्छिन्", "्छस्", "्दैन", "्दिन",
    "हुन्छ", "हो", "थियो", "थिए", "थिएन",
    "्न", "्ने", "्दा", "्दै", "्नुस्", "्नुहोस्",
)

# Postpositions that attach to the previous word and trigger halanta-style
# schwa deletion on the last syllable of the host (Rule 4).
ATTACHING_POSTPOSITIONS = ("को", "मा", "ले", "लाई", "बाट", "सँग", "का", "की", "हरू")

# A small inventory of common Nepali adverbs and postpositions that
# retain their final inherent vowel (Rule 3). This is a v0 stopgap;
# proper handling needs lexical tagging in the gold lexicon.
SCHWA_RETAINING_ADVERBS_POSTPOSITIONS = {
    "अब", "आज", "भोलि", "हिजो", "पर्सि", "आज", "अहिले",
    "यहाँ", "त्यहाँ", "जहाँ", "कहाँ",
    "तर", "अनि", "तब", "जब", "किनभने",
    "धेरै", "थोरै", "केही", "कोही",
    "साथ", "बिना", "लागि", "जस्तो",
}


def _is_conjunct_final(aksharas: list[Akshara]) -> bool:
    """Rule 1: did the final phonologically-relevant akshara end in a conjunct?"""
    for a in reversed(aksharas):
        if a.type == "syllable":
            cons = a.components.get("consonants", [])
            return len(cons) > 1
        if a.type == "vowel":
            return False
    return False


def _looks_like_verb(text: str) -> bool:
    return any(text.endswith(end) for end in VERB_ENDINGS_DEVA)


def apply_schwa_deletion(text: str, aksharas: list[Akshara]) -> tuple[list[Akshara], list[dict]]:
    """Apply the four documented Nepali schwa retention/deletion rules.

    The rules are applied to the *final* syllable's inherent vowel (the
    classic site of Nepali schwa variation). Medial schwa deletion is
    NOT applied in v0 — it is rarer in Nepali than in Hindi, and the
    cost of an over-eager rule is high.

    Returns: (mutated aksharas, list of decision events).
    """
    decisions: list[dict] = []

    # Find the final relevant akshara (skip punct, signs, digits)
    final_idx = None
    for k in range(len(aksharas) - 1, -1, -1):
        if aksharas[k].type in ("syllable", "vowel"):
            final_idx = k
            break
    if final_idx is None:
        return aksharas, decisions

    final = aksharas[final_idx]
    if final.type != "syllable":
        return aksharas, decisions

    # Only operates on aksharas that have inherent vowel `ax` at end
    if not final.components.get("inherent_vowel"):
        return aksharas, decisions
    if not final.phones or final.phones[-1] != "ax":
        return aksharas, decisions

    # Rule 1: conjunct retention
    cons = final.components.get("consonants", [])
    if len(cons) > 1:
        decisions.append({
            "type": "post_rule", "rule": "schwa_retention_conjunct",
            "span": final.text, "before": "delete", "after": "retain",
        })
        return aksharas, decisions

    # Rule 2: verb retention
    if _looks_like_verb(text):
        decisions.append({
            "type": "post_rule", "rule": "schwa_retention_verb",
            "span": final.text, "before": "delete", "after": "retain",
        })
        return aksharas, decisions

    # Rule 3: adverb / postposition retention. v0 uses a small hardcoded
    # set; proper handling requires lexical tagging in the gold lexicon.
    if text in SCHWA_RETAINING_ADVERBS_POSTPOSITIONS:
        decisions.append({
            "type": "post_rule", "rule": "schwa_retention_adverb_postposition",
            "span": final.text, "before": "delete", "after": "retain",
        })
        return aksharas, decisions

    # Default for monomorphemic, non-verb, non-conjunct-final words:
    # delete the final inherent vowel.
    deleted = final.phones.pop()
    decisions.append({
        "type": "post_rule", "rule": "schwa_deletion_default",
        "span": final.text, "before": deleted, "after": "<deleted>",
    })
    return aksharas, decisions


# ---- Gemination ----------------------------------------------------------

def apply_gemination(aksharas: list[Akshara]) -> tuple[list[Akshara], list[dict]]:
    """Detect virama-joined identical consonants and mark gemination.

    In any conjunct of the form CC where two adjacent consonants
    share the same phone, replace the doubled phone with a geminate
    marker `<phone>:` (single token, IPA length /ː/). Multiple
    geminations in a single syllable are all collapsed.
    """
    decisions: list[dict] = []
    for a in aksharas:
        if a.type != "syllable":
            continue
        cons = a.components.get("consonants", [])
        # Only act if the conjunct has identical adjacent consonants
        if not any(cons[i]["char"] == cons[i - 1]["char"] for i in range(1, len(cons))):
            continue
        ph = a.phones
        out = []
        i = 0
        while i < len(ph):
            if i + 1 < len(ph) and ph[i] == ph[i + 1]:
                geminate = f"{ph[i]}:"
                decisions.append({
                    "type": "post_rule", "rule": "gemination",
                    "span": a.text, "before": f"{ph[i]} {ph[i + 1]}",
                    "after": geminate,
                })
                out.append(geminate)
                i += 2
            else:
                out.append(ph[i])
                i += 1
        a.phones = out
    return aksharas, decisions


# ---- Anusvara contextual resolution --------------------------------------

def apply_anusvara_context(aksharas: list[Akshara]) -> tuple[list[Akshara], list[dict]]:
    """Resolve anusvara to a homorganic nasal consonant when it precedes
    a plosive at a known place of articulation.

    The akshara parser already turned anusvara into vowel nasalization
    (the safe default). This rule promotes the nasalization to a nasal
    consonant when the next syllable starts with a stop/affricate at
    a known place. Chandrabindu is left alone (always vowel-only).
    """
    decisions: list[dict] = []
    for k in range(len(aksharas) - 1):
        cur = aksharas[k]
        nxt = aksharas[k + 1]
        # Both syllable- and vowel-type aksharas can carry anusvara.
        if cur.type not in ("syllable", "vowel") or nxt.type != "syllable":
            continue
        if bm.ANUSVARA not in cur.components.get("modifiers", []):
            continue
        if not cur.phones:
            continue
        last = cur.phones[-1]
        if last not in NASALIZED_TO_ORAL:
            continue  # already not a nasalized vowel; nothing to do
        # What's the first consonant of the next syllable?
        nxt_cons = nxt.components.get("consonants", [])
        if not nxt_cons:
            continue
        nxt_first_phone = bm.CONSONANT.get(nxt_cons[0]["char"])
        if nxt_first_phone is None:
            continue
        nasal = PLACE_TO_NASAL.get(nxt_first_phone)
        if nasal is None:
            continue
        # Promote: nasalized vowel → oral vowel + nasal consonant
        oral = NASALIZED_TO_ORAL[last]
        cur.phones[-1] = oral
        cur.phones.append(nasal)
        decisions.append({
            "type": "post_rule", "rule": "anusvara_context",
            "span": cur.text, "before": last, "after": f"{oral} {nasal}",
            "context": f"before /{nxt_first_phone}/",
        })
    return aksharas, decisions


# ---- Morphological suffix strip -----------------------------------------

# Ordered longest-first so प्रेषणेहरूको matches before को.
NEPALI_CASE_SUFFIXES = (
    "हरूको", "हरूले", "हरूमा", "हरूका", "हरूलाई", "हरूबाट", "हरूसँग",
    "लाई", "बाट", "सँग",
    "हरू", "मा", "को", "का", "की", "ले",
)


# ---- Diphthong contraction at vowel-sequence boundaries ----------------

# Map (nucleus_phone, glide_vowel_phone) → contracted diphthong label.
# Only the 13 v1.0 diphthong labels are produced.
DIPHTHONG_PAIRS: dict[tuple[str, str], str] = {
    # Oral
    ("ax", "i"): "axj",
    ("ax", "u"): "axw",
    ("aa", "i"): "aaj",
    ("aa", "u"): "aaw",
    ("o", "i"): "oj",
    ("e", "u"): "ew",
    ("o", "u"): "ow",
    # Nasalized counterparts (when nucleus is already nasalized)
    ("axn", "i"): "axjn",
    ("axn", "u"): "axwn",
    ("aan", "i"): "aajn",
    ("aan", "u"): "aawn",
    ("on", "i"): "ojn",
    ("on", "u"): "own",
}


def apply_diphthong_contraction(aksharas: list[Akshara]) -> tuple[list[Akshara], list[dict]]:
    """Contract vowel + independent-vowel pairs into a single diphthong label.

    Patterns:
      [..., consonant + nucleus, independent_vowel(i|u)]
        →  [..., consonant + diphthong]

      [independent_vowel(nucleus), independent_vowel(i|u)]
        →  [diphthong]   (collapses two aksharas into one)

    Only the 13 v1.0 diphthong labels are emitted; combinations not
    in `DIPHTHONG_PAIRS` (e.g. /ei/, /iu/, /ui/) stay as 2-syllable
    sequences per project policy (see Khatiwada 2009: 378 — "It is
    not very easy to determine in many cases whether a given
    sequence is monosyllabic or disyllabic").
    """
    decisions: list[dict] = []
    out: list[Akshara] = []
    i = 0
    while i < len(aksharas):
        cur = aksharas[i]
        # Need a following independent-vowel akshara whose phone is `i` or `u`.
        if i + 1 < len(aksharas):
            nxt = aksharas[i + 1]
            if nxt.type == "vowel" and len(nxt.phones) == 1 and nxt.phones[0] in ("i", "u"):
                if cur.phones:
                    last = cur.phones[-1]
                    diph = DIPHTHONG_PAIRS.get((last, nxt.phones[0]))
                    if diph is not None:
                        # Replace nucleus with diphthong and merge spans.
                        new_phones = cur.phones[:-1] + [diph]
                        merged = Akshara(
                            type=cur.type,
                            text=cur.text + nxt.text,
                            span=(cur.span[0], nxt.span[1]),
                            phones=new_phones,
                            components={**cur.components, "diphthong_merged": True},
                        )
                        decisions.append({
                            "type": "post_rule", "rule": "diphthong_contraction",
                            "span": cur.text + nxt.text,
                            "before": f"{last} {nxt.phones[0]}",
                            "after": diph,
                        })
                        out.append(merged)
                        i += 2
                        continue
        out.append(cur)
        i += 1
    return out, decisions


# ---- Compound-internal schwa deletion (conservative) --------------------

def apply_compound_schwa(text: str, aksharas: list[Akshara],
                          lexicon: Optional[dict[str, list[str]]] = None
                          ) -> tuple[list[Akshara], list[dict]]:
    """Delete medial inherent schwa at detected compound boundaries.

    Detection is *conservative*: a schwa is medial-deleted only when
    a known sub-word boundary is identified by a lexicon-prefix
    lookup.  For each medial syllable carrying an inherent `ax`,
    we check whether the Devanagari prefix up through that syllable
    is itself a complete word in the lexicon (a sub-word). If yes,
    that schwa is at a compound boundary and we delete it.

    This avoids false positives on simple multi-syllable words
    (where Hindi-style VC_CV would over-delete). Requires the
    candidate lexicon — falls back to no-op if not provided.

    Empirically this targets the largest residual disagreement
    category against the Google lexicon.
    """
    if lexicon is None:
        return aksharas, []
    decisions: list[dict] = []

    # We need to track Devanagari character offsets per akshara.
    # Each akshara already has .span = (start, end) in the input text.
    if not aksharas:
        return aksharas, decisions

    # A genuine compound boundary requires BOTH halves to be in the
    # lexicon AND to be at least 2 aksharas each — otherwise we are
    # most likely dealing with a single morpheme whose prefix happens
    # to coincide with a short word in the lexicon.
    syl_count_to = []
    cnt = 0
    for a in aksharas:
        if a.type in ("syllable", "vowel"):
            cnt += 1
        syl_count_to.append(cnt)
    total_syll = cnt

    n = len(aksharas)
    for k in range(n):
        a = aksharas[k]
        if a.type != "syllable":
            continue
        if not a.components.get("inherent_vowel"):
            continue
        if not a.phones or a.phones[-1] != "ax":
            continue
        prefix_syll = syl_count_to[k]
        suffix_syll = total_syll - prefix_syll
        if prefix_syll < 2 or suffix_syll < 2:
            continue
        prefix = text[: a.span[1]]
        suffix = text[a.span[1]:]
        if prefix not in lexicon or suffix not in lexicon:
            continue
        deleted = a.phones.pop()
        decisions.append({
            "type": "post_rule", "rule": "compound_schwa_deletion",
            "span": a.text,
            "before": deleted,
            "after": "<deleted>",
            "context": f"compound: {prefix!r} + {suffix!r} (both in lex, both ≥2 aksharas)",
        })
    return aksharas, decisions


def apply_anusvara_to_phone_list(phones: list[str]) -> tuple[list[str], list[dict]]:
    """Apply the anusvara contextual rule to a flat phone list.

    Pattern: a nasalized-vowel phone immediately followed by a
    syllable boundary `.` followed by a stop/affricate at a known
    place of articulation gets promoted to oral-vowel + homorganic
    nasal consonant + syllable boundary + onset.

    Used by the phonemizer's *lexicon* path so that lexicon-encoded
    anusvara entries (e.g., Google's `axn . g ax` for अंग) are
    rendered consistently with our rule G2P (`ax ng . g ax`),
    matching the documented Khatiwada/Regmi anusvara contextual
    rule.

    Idempotent — running it twice on the same input is a no-op.
    """
    out: list[str] = []
    decisions: list[dict] = []
    i = 0
    n = len(phones)
    while i < n:
        if (
            phones[i] in NASALIZED_TO_ORAL
            and i + 2 < n
            and phones[i + 1] == "."
            and phones[i + 2] in PLACE_TO_NASAL
        ):
            oral = NASALIZED_TO_ORAL[phones[i]]
            nasal = PLACE_TO_NASAL[phones[i + 2]]
            out.extend([oral, nasal, ".", phones[i + 2]])
            decisions.append({
                "type": "post_rule",
                "rule": "anusvara_context_lexicon",
                "before": f"{phones[i]} . {phones[i + 2]}",
                "after": f"{oral} {nasal} . {phones[i + 2]}",
            })
            i += 3
        else:
            out.append(phones[i])
            i += 1
    return out, decisions


def try_suffix_strip(spelling: str, lexicon: dict[str, list[str]]) -> Optional[tuple[str, str, list[str]]]:
    """If `spelling` is not in the lexicon but `<root> + <suffix>` matches
    a known case suffix and `<root>` is in the lexicon, return
    (root, suffix, root_phones). Otherwise None.

    Suffix phones are NOT computed here — the caller phonemizes the
    suffix via the akshara parser and concatenates.
    """
    if spelling in lexicon:
        return None
    for suf in NEPALI_CASE_SUFFIXES:
        if len(spelling) <= len(suf):
            continue
        if spelling.endswith(suf):
            root = spelling[: -len(suf)]
            if root in lexicon:
                return root, suf, lexicon[root]
    return None
