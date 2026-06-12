#!/usr/bin/env python3
"""Tests for vocab_ops: language-agnostic vocabulary card operations."""
from __future__ import annotations

import unittest
from datetime import date
from pathlib import Path

from tools.vocab_ops import VocabOps


class TestVocabOpsInit(unittest.TestCase):
    """Test VocabOps initialization and properties."""

    def test_default_japanese_config(self) -> None:
        config = {
            "language_profile": {
                "name": "Japanese",
                "tag_namespace": "jp",
                "speaking_text_field": "jp_text",
            },
            "features": {},
        }
        ops = VocabOps(config)
        self.assertEqual(ops.namespace, "jp")
        self.assertEqual(ops.speaking_text_field, "jp_text")

    def test_french_config(self) -> None:
        config = {
            "language_profile": {
                "name": "French",
                "tag_namespace": "fr",
                "speaking_text_field": "fr_text",
            },
            "features": {},
        }
        ops = VocabOps(config)
        self.assertEqual(ops.namespace, "fr")
        self.assertEqual(ops.speaking_text_field, "fr_text")


class TestGetVocabTags(unittest.TestCase):
    """Test get_vocab_tags with different namespaces."""

    def test_japanese_tags(self) -> None:
        config = {
            "language_profile": {
                "name": "Japanese",
                "tag_namespace": "jp",
                "speaking_text_field": "jp_text",
            },
            "features": {},
        }
        ops = VocabOps(config)
        tags = ops.get_vocab_tags()
        self.assertEqual(tags["vocab"], "jp/vocab")
        self.assertEqual(tags["base_vocab"], "jp/base_vocab")
        self.assertEqual(tags["class_review"], "jp/class_review")
        self.assertEqual(tags["promoted"], "jp/promoted")
        self.assertEqual(tags["kanji_diff"], "jp/kanji_diff")

    def test_french_tags(self) -> None:
        config = {
            "language_profile": {
                "name": "French",
                "tag_namespace": "fr",
                "speaking_text_field": "fr_text",
            },
            "features": {},
        }
        ops = VocabOps(config)
        tags = ops.get_vocab_tags()
        self.assertEqual(tags["vocab"], "fr/vocab")
        self.assertEqual(tags["base_vocab"], "fr/base_vocab")


class TestExtractLabel(unittest.TestCase):
    """Test extract_label with various frontmatter."""

    def test_headword_priority(self) -> None:
        config = {
            "language_profile": {
                "name": "Japanese",
                "tag_namespace": "jp",
                "speaking_text_field": "jp_text",
            },
            "features": {},
        }
        ops = VocabOps(config)
        text = "---\nheadword: 荷物\nreading: にもつ\n---\n"
        self.assertEqual(ops.extract_label(text, Path("test.md")), "荷物")

    def test_speaking_text_field_fallback(self) -> None:
        config = {
            "language_profile": {
                "name": "Japanese",
                "tag_namespace": "jp",
                "speaking_text_field": "jp_text",
            },
            "features": {},
        }
        ops = VocabOps(config)
        text = "---\njp_text: こんにちは\n---\n"
        self.assertEqual(ops.extract_label(text, Path("test.md")), "こんにちは")

    def test_filename_stem_fallback(self) -> None:
        config = {
            "language_profile": {
                "name": "Japanese",
                "tag_namespace": "jp",
                "speaking_text_field": "jp_text",
            },
            "features": {},
        }
        ops = VocabOps(config)
        text = "---\nstatus: active\n---\n"
        self.assertEqual(ops.extract_label(text, Path("my_note.md")), "my_note")


class TestIsFocusVocab(unittest.TestCase):
    """Test is_focus_vocab."""

    def test_true(self) -> None:
        config = {
            "language_profile": {
                "name": "Japanese",
                "tag_namespace": "jp",
                "speaking_text_field": "jp_text",
            },
            "features": {},
        }
        ops = VocabOps(config)
        self.assertTrue(ops.is_focus_vocab("class_review", "vocab"))

    def test_false_wrong_track(self) -> None:
        config = {
            "language_profile": {
                "name": "Japanese",
                "tag_namespace": "jp",
                "speaking_text_field": "jp_text",
            },
            "features": {},
        }
        ops = VocabOps(config)
        self.assertFalse(ops.is_focus_vocab("listening", "vocab"))

    def test_false_wrong_type(self) -> None:
        config = {
            "language_profile": {
                "name": "Japanese",
                "tag_namespace": "jp",
                "speaking_text_field": "jp_text",
            },
            "features": {},
        }
        ops = VocabOps(config)
        self.assertFalse(ops.is_focus_vocab("class_review", "error"))


class TestRenderBaseNote(unittest.TestCase):
    """Test render_base_note with language-agnostic tags."""

    def test_basic_render(self) -> None:
        config = {
            "language_profile": {
                "name": "Japanese",
                "tag_namespace": "jp",
                "speaking_text_field": "jp_text",
            },
            "features": {},
        }
        ops = VocabOps(config)
        result = ops.render_base_note(
            note_title="荷物",
            headword="荷物",
            reading="にもつ",
            accent_display="①",
            meaning_zh="行李",
            source_notes=['"[[笔记/2026.6/2026.6.1]]"'],
            first_seen=date(2026, 6, 1),
            last_seen=date(2026, 6, 10),
            seen_count=5,
            kanji_diff="false",
            kanji_diff_pairs=[],
        )
        self.assertIn("headword: 荷物", result)
        self.assertIn("reading: にもつ", result)
        self.assertIn("accent_display: ①", result)
        self.assertIn("jp/vocab", result)
        self.assertIn("jp/base_vocab", result)
        self.assertIn("jp/promoted", result)

    def test_with_kanji_diff(self) -> None:
        config = {
            "language_profile": {
                "name": "Japanese",
                "tag_namespace": "jp",
                "speaking_text_field": "jp_text",
            },
            "features": {},
        }
        ops = VocabOps(config)
        result = ops.render_base_note(
            note_title="複雑",
            headword="複雑",
            reading="ふくざつ",
            accent_display="⓪",
            meaning_zh="复杂",
            source_notes=[],
            first_seen=date(2026, 6, 1),
            last_seen=date(2026, 6, 10),
            seen_count=3,
            kanji_diff="true",
            kanji_diff_pairs=["複/复"],
        )
        self.assertIn("jp/kanji_diff", result)
        self.assertIn("- 複/复", result)

    def test_with_pronunciation_and_variants(self) -> None:
        config = {
            "language_profile": {
                "name": "Japanese",
                "tag_namespace": "jp",
                "speaking_text_field": "jp_text",
            },
            "features": {},
        }
        ops = VocabOps(config)
        result = ops.render_base_note(
            note_title="複雑",
            headword="複雑",
            reading="ふくざつ",
            accent_display="⓪",
            meaning_zh="复杂",
            source_notes=[],
            first_seen=date(2026, 6, 1),
            last_seen=date(2026, 6, 10),
            seen_count=3,
            kanji_diff="true",
            kanji_diff_pairs=["複/复"],
            pronunciation="ふくざつ⓪",
            variants=["複/复"],
        )
        self.assertIn("pronunciation: ふくざつ⓪", result)
        self.assertIn("- 複/复", result)

    def test_french_namespace(self) -> None:
        config = {
            "language_profile": {
                "name": "French",
                "tag_namespace": "fr",
                "speaking_text_field": "fr_text",
            },
            "features": {},
        }
        ops = VocabOps(config)
        result = ops.render_base_note(
            note_title="bonjour",
            headword="bonjour",
            reading="",
            accent_display="",
            meaning_zh="你好",
            source_notes=[],
            first_seen=date(2026, 6, 1),
            last_seen=date(2026, 6, 10),
            seen_count=1,
            kanji_diff="false",
            kanji_diff_pairs=[],
        )
        self.assertIn("fr/vocab", result)
        self.assertIn("fr/base_vocab", result)
        self.assertIn("fr/promoted", result)
        self.assertNotIn("jp/", result)


if __name__ == "__main__":
    unittest.main()
