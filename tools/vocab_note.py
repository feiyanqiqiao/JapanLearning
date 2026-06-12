#!/usr/bin/env python3
"""Unified vocabulary card frontmatter operations for LingoTrace multi-language architecture.

Provides language-agnostic field normalization with backward-compatible fallbacks.
New cards should use `pronunciation` and `variants`; old cards using `reading`+`accent_display`
and `kanji_diff_pairs` continue to work transparently.

Usage:
    from vocab_note import normalize_reading, normalize_variants

    fm = note.frontmatter
    reading = normalize_reading(fm)      # "にもつ①"
    variants = normalize_variants(fm)    # ["複/复"]
"""
from __future__ import annotations

from typing import Any

# Mapping from new canonical field names to legacy aliases.
# When reading, new fields take priority; when the new field is absent,
# the loader falls back to the legacy combination.
FIELD_ALIASES: dict[str, list[str]] = {
    "pronunciation": ["reading", "accent_display"],
    "variants": ["kanji_diff_pairs"],
}


def normalize_reading(frontmatter: dict[str, Any]) -> str:
    """Return the pronunciation string, with fallback to legacy fields.

    Priority:
        1. ``pronunciation`` (new canonical field)
        2. ``reading`` + ``accent_display`` (legacy combination)

    Examples:
        >>> normalize_reading({"pronunciation": "にもつ①"})
        'にもつ①'
        >>> normalize_reading({"reading": "にもつ", "accent_display": "①"})
        'にもつ①'
        >>> normalize_reading({"reading": "にもつ"})
        '也有つ'
        >>> normalize_reading({})
        ''
    """
    if "pronunciation" in frontmatter:
        return str(frontmatter["pronunciation"])

    reading = str(frontmatter.get("reading", ""))
    accent = str(frontmatter.get("accent_display", ""))
    return f"{reading}{accent}" if accent else reading


def normalize_variants(frontmatter: dict[str, Any]) -> list[str]:
    """Return the variant pairs list, with fallback to legacy field.

    Priority:
        1. ``variants`` (new canonical field)
        2. ``kanji_diff_pairs`` (legacy field)

    Examples:
        >>> normalize_variants({"variants": ["複/复"]})
        ['複/复']
        >>> normalize_variants({"kanji_diff_pairs": ["複/复"]})
        ['複/复']
        >>> normalize_variants({})
        []
    """
    if "variants" in frontmatter:
        value = frontmatter["variants"]
        if isinstance(value, list):
            return [str(v) for v in value]
        return [str(value)] if value else []

    legacy = frontmatter.get("kanji_diff_pairs", [])
    if isinstance(legacy, list):
        return [str(v) for v in legacy]
    return [str(legacy)] if legacy else []


def build_reading(
    pronunciation_system: str,
    base_reading: str = "",
    accent_info: str = "",
    raw_pronunciation: str = "",
) -> str:
    """Build a pronunciation value appropriate for the given language system.

    For ``pitch_accent`` systems (Japanese), this concatenates reading + accent_display.
    For other systems, the raw_pronunciation is returned as-is.

    Args:
        pronunciation_system: Identifier from config (e.g. 'pitch_accent', 'ipa').
        base_reading: Clean reading without accent (e.g. 'にもつ').
        accent_info: Accent display string (e.g. '①').
        raw_pronunciation: Pre-built pronunciation string for non-pitch-accent systems.

    Returns:
        Formatted pronunciation string.

    Examples:
        >>> build_reading("pitch_accent", "にもつ", "①")
        'にもつ①'
        >>> build_reading("ipa", raw_pronunciation="nimotsu")
        'nimotsu'
    """
    if pronunciation_system == "pitch_accent":
        return f"{base_reading}{accent_info}" if accent_info else base_reading
    return raw_pronunciation


def get_kanji_diff_status(frontmatter: dict[str, Any]) -> bool:
    """Return whether kanji diff is flagged for this card.

    Checks ``kanji_diff`` boolean field. Defaults to False.
    """
    return bool(frontmatter.get("kanji_diff", False))


def set_pronunciation(frontmatter: dict[str, Any], value: str) -> None:
    """Set the canonical pronunciation field and clear legacy fields.

    This is used when migrating a card from legacy fields to the new schema.
    """
    frontmatter["pronunciation"] = value
    frontmatter.pop("reading", None)
    frontmatter.pop("accent_display", None)


def set_variants(frontmatter: dict[str, Any], value: list[str]) -> None:
    """Set the canonical variants field and clear legacy fields."""
    frontmatter["variants"] = value
    frontmatter.pop("kanji_diff_pairs", None)
