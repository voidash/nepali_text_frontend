"""Dialect profile definitions for the real_nepali frontend."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class DialectProfile:
    """A small output profile layered on top of the base Nepali frontend.

    The base frontend already handles lexicon lookup, schwa deletion,
    anusvara, gemination, syllable boundaries, and number normalization. The
    profile owns the dialect/acoustic target labels that should differ.
    """

    name: str
    description: str
    phone_rewrites: dict[str, str] = field(default_factory=dict)

    def rewrite_phone(self, phone: str) -> str:
        """Return the profile-specific phone label for ``phone``."""
        return self.phone_rewrites.get(phone, phone)


STANDARD_CLEAR_NEPALI = DialectProfile(
    name="standard_clear_nepali",
    description=(
        "Mainstream clear Nepali speech target. Keeps the current lexicon and "
        "schwa/anusvara rules, but exposes a separate affricate-label profile "
        "for broad-listener TTS tests. The literature treats alveolar affricates "
        "as standard Nepali, so this is an experimental product profile, not a "
        "settled phonological correction."
    ),
    phone_rewrites={
        # Old Kathmandu-policy labels -> clear-standard labels.
        "ts": "ch",
        "tsh": "chh",
        "dz": "j",
        "dzh": "jh",
        # Geminated variants, emitted as single ``phone:`` tokens.
        "ts:": "ch:",
        "tsh:": "chh:",
        "dz:": "j:",
        "dzh:": "jh:",
    },
)

PROFILES = {
    STANDARD_CLEAR_NEPALI.name: STANDARD_CLEAR_NEPALI,
    "real_nepali": STANDARD_CLEAR_NEPALI,
}


def get_profile(name: str = STANDARD_CLEAR_NEPALI.name) -> DialectProfile:
    try:
        return PROFILES[name]
    except KeyError as exc:
        valid = ", ".join(sorted(PROFILES))
        raise ValueError(f"unknown real_nepali profile {name!r}; valid: {valid}") from exc
