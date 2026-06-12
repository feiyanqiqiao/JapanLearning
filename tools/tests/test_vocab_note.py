#!/usr/bin/env python3
"""Tests for vocab_note: unified vocabulary card frontmatter operations."""
from __future__ import annotations

import unittest

from tools.vocab_note import (
    build_reading,
    get_kanji_diff_status,
    normalize_reading,
    normalize_variants,
    set_pronunciation,
    set_variants,
)


class TestNormalizeReading(unittest.TestCase):
    """Test normalize_reading with various frontmatter combinations."""

    def test_new_pronunciation_field_takes_priority(self) -> None:
        fm = {"pronunciation": "にもつ①", "reading": "にもつ", "accent_display": "①"}
        self.assertEqual(normalize_reading(fm), "にもつ①")

    def test_legacy_reading_and_accent_display(self) -> None:
        fm = {"reading": "にもつ", "accent_display": "①"}
        self.assertEqual(normalize_reading(fm), "にもつ①")

    def test_legacy_reading_only(self) -> None:
        fm = {"reading": "にもつ"}
        self.assertEqual(normalize_reading(fm), "にもつ")

    def test_legacy_accent_display_only(self) -> None:
        fm = {"accent_display": "①"}
        self.assertEqual(normalize_reading(fm), "①")

    def test_empty_frontmatter(self) -> None:
        self.assertEqual(normalize_reading({}), "")

    def test_new_field_without_legacy(self) -> None:
        fm = {"pronunciation": "じてんしゃ②／⓪"}
        self.assertEqual(normalize_reading(fm), "じてんしゃ②／⓪")


class TestNormalizeVariants(unittest.TestCase):
    """Test normalize_variants with various frontmatter combinations."""

    def test_new_variants_field_takes_priority(self) -> None:
        fm = {"variants": ["複/复", "辺/边"], "kanji_diff_pairs": ["旧/旧"]}
        self.assertEqual(normalize_variants(fm), ["複/复", "辺/边"])

    def test_legacy_kanji_diff_pairs(self) -> None:
        fm = {"kanji_diff_pairs": ["複/复"]}
        self.assertEqual(normalize_variants(fm), ["複/复"])

    def test_empty_frontmatter(self) -> None:
        self.assertEqual(normalize_variants({}), [])

    def test_new_field_single_string(self) -> None:
        fm = {"variants": "複/复"}
        self.assertEqual(normalize_variants(fm), ["複/复"])

    def test_legacy_field_single_string(self) -> None:
        fm = {"kanji_diff_pairs": "複/复"}
        self.assertEqual(normalize_variants(fm), ["複/复"])


class TestBuildReading(unittest.TestCase):
    """Test build_reading for different pronunciation systems."""

    def test_pitch_accent_with_accent(self) -> None:
        result = build_reading("pitch_accent", "にもつ", "①")
        self.assertEqual(result, "にもつ①")

    def test_pitch_accent_without_accent(self) -> None:
        result = build_reading("pitch_accent", "にもつ")
        self.assertEqual(result, "にもつ")

    def test_ipa_system(self) -> None:
        result = build_reading("ipa", raw_pronunciation="nimotsu")
        self.assertEqual(result, "nimotsu")

    def test_other_system(self) -> None:
        result = build_reading("pinyin", raw_pronunciation="mǎi")
        self.assertEqual(result, "mǎi")


class TestGetKanjiDiffStatus(unittest.TestCase):
    """Test get_kanji_diff_status."""

    def test_true(self) -> None:
        self.assertTrue(get_kanji_diff_status({"kanji_diff": True}))

    def test_false(self) -> None:
        self.assertFalse(get_kanji_diff_status({"kanji_diff": False}))

    def test_missing(self) -> None:
        self.assertFalse(get_kanji_diff_status({}))


class TestSetPronunciation(unittest.TestCase):
    """Test set_pronunciation migration helper."""

    def test_sets_new_field_and_clears_legacy(self) -> None:
        fm = {"reading": "にもつ", "accent_display": "①", "headword": "荷物"}
        set_pronunciation(fm, "にもつ①")
        self.assertEqual(fm["pronunciation"], "にもつ①")
        self.assertNotIn("reading", fm)
        self.assertNotIn("accent_display", fm)
        self.assertEqual(fm["headword"], "荷物")  # other fields preserved


class TestSetVariants(unittest.TestCase):
    """Test set_variants migration helper."""

    def test_sets_new_field_and_clears_legacy(self) -> None:
        fm = {"kanji_diff_pairs": ["複/复"], "headword": "複雑"}
        set_variants(fm, ["複/复"])
        self.assertEqual(fm["variants"], ["複/复"])
        self.assertNotIn("kanji_diff_pairs", fm)
        self.assertEqual(fm["headword"], "複雑")  # other fields preserved


if __name__ == "__main__":
    unittest.main()
