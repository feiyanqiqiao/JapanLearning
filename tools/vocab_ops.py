#!/usr/bin/env python3
"""Language-agnostic vocabulary card operations for LingoTrace.

Extracts and generalizes vocabulary-related logic from update_next_day_review.py.
All tag prefixes and field names are driven by config.json instead of hardcoded.

Usage:
    from config_loader import load_config
    from vocab_ops import VocabOps

    config = load_config(vault_root)
    ops = VocabOps(config)
    label = ops.extract_label(text, path)
    tags = ops.get_vocab_tags()
"""
from __future__ import annotations

import re
from datetime import date
from pathlib import Path
from typing import Any

from tools.config_loader import get_tag_namespace, get_speaking_text_field
from tools.vocab_note import normalize_reading, normalize_variants


class VocabOpsError(RuntimeError):
    """Raised when a vocabulary operation fails."""


class VocabOps:
    """Language-agnostic vocabulary card operations."""

    def __init__(self, config: dict[str, Any]) -> None:
        self._config = config
        self._namespace = get_tag_namespace(config)
        self._speaking_text_field = get_speaking_text_field(config)

    @property
    def namespace(self) -> str:
        """Return the tag namespace (e.g. 'jp', 'fr')."""
        return self._namespace

    @property
    def speaking_text_field(self) -> str:
        """Return the frontmatter field name for speaking card text."""
        return self._speaking_text_field

    def get_vocab_tags(self) -> dict[str, str]:
        """Return vocabulary tag mappings using the configured namespace.

        Returns:
            Dict with keys: 'vocab', 'base_vocab', 'class_review', 'promoted', 'kanji_diff'
        """
        ns = self._namespace
        return {
            "vocab": f"{ns}/vocab",
            "base_vocab": f"{ns}/base_vocab",
            "class_review": f"{ns}/class_review",
            "promoted": f"{ns}/promoted",
            "kanji_diff": f"{ns}/kanji_diff",
        }

    def get_track_labels(self) -> dict[str, str]:
        """Return track label mappings. Currently language-agnostic."""
        return {
            "class_review": "重点复习",
            "survival_speaking": "生活口语",
            "listening": "听力",
            "pronunciation": "发音",
        }

    def extract_label(self, text: str, path: Path) -> str:
        """Extract a display label from the note's frontmatter.

        Priority: headword > pattern > speaking_text_field > target_text > filename stem

        Args:
            text: Full note text with frontmatter.
            path: Path to the note file.

        Returns:
            Extracted label string.
        """
        # Standard fields in priority order
        candidates = ["headword", "pattern", self._speaking_text_field, "target_text"]
        for key in candidates:
            value = self._get_field(text, key, path, required=False).strip().strip('"')
            if value:
                return value
        return path.stem

    def is_focus_vocab(self, track: str, item_type: str) -> bool:
        """Check if an item is a focus vocabulary card."""
        return track == "class_review" and item_type == "vocab"

    def render_base_note(
        self,
        note_title: str,
        headword: str,
        reading: str,
        accent_display: str,
        meaning_zh: str,
        source_notes: list[str],
        first_seen: date,
        last_seen: date,
        seen_count: int,
        kanji_diff: str,
        kanji_diff_pairs: list[str],
        pronunciation: str = "",
        variants: list[str] | None = None,
    ) -> str:
        """Render a base vocabulary note with language-agnostic tags.

        This is the generalized version of render_base_note from update_next_day_review.py.
        Tags are generated from the configured namespace instead of hardcoded 'jp/'.

        Args:
            note_title: Note title (usually headword).
            headword: The word's headword.
            reading: Clean reading without accent.
            accent_display: Accent display string.
            meaning_zh: Chinese meaning.
            source_notes: List of source note wikilinks.
            first_seen: First seen date.
            last_seen: Last seen date.
            seen_count: Number of times seen.
            kanji_diff: "true" or "false" for kanji diff flag.
            kanji_diff_pairs: List of kanji diff pairs.
            pronunciation: New canonical pronunciation field (optional).
            variants: New canonical variants field (optional).

        Returns:
            Complete note text with frontmatter and body.
        """
        tags = self.get_vocab_tags()
        source_lines = "\n".join(f'- "{source}"' for source in source_notes)
        body_lines = "\n".join(f"- {source}" for source in source_notes)

        tag_list = [tags["vocab"], tags["base_vocab"], tags["class_review"], tags["promoted"]]
        if kanji_diff == "true":
            tag_list.append(tags["kanji_diff"])
        tag_lines = "\n".join(f"- {tag}" for tag in tag_list)

        kanji_diff_pair_lines = "\n".join(self._format_frontmatter_list("kanji_diff_pairs", kanji_diff_pairs))
        accent_line = f"accent_display: {accent_display}\n" if accent_display else ""

        # New canonical fields
        pronunciation_line = f"pronunciation: {pronunciation}\n" if pronunciation else ""
        variants_lines = "\n".join(self._format_frontmatter_list("variants", variants or []))

        return (
            "---\n"
            f"headword: {headword}\n"
            "aliases:\n"
            f"- {self._yaml_quote(headword)}\n"
            f"reading: {reading}\n"
            f"{accent_line}"
            f"{pronunciation_line}"
            f"{variants_lines}\n"
            f"meaning_zh: {meaning_zh}\n"
            "source_notes:\n"
            f"{source_lines}\n"
            f"first_seen: {first_seen.isoformat()}\n"
            f"last_seen: {last_seen.isoformat()}\n"
            f"seen_count: {seen_count}\n"
            "status: promoted\n"
            "promote_candidate: false\n"
            f"kanji_diff: {kanji_diff}\n"
            f"{kanji_diff_pair_lines}\n"
            "tags:\n"
            f"{tag_lines}\n"
            "---\n\n"
            f"# {note_title}\n\n"
            "## 来源\n\n"
            f"{body_lines}\n"
        )

    def _get_field(self, text: str, key: str, path: Path, required: bool = True) -> str:
        """Extract a frontmatter field value."""
        match = re.search(rf"^{re.escape(key)}:\s*(.*)$", text, flags=re.MULTILINE)
        if match:
            return match.group(1).strip()
        if required:
            raise VocabOpsError(f"{path}: missing frontmatter field {key!r}")
        return ""

    @staticmethod
    def _format_frontmatter_list(key: str, items: list[str]) -> list[str]:
        """Format a frontmatter list field."""
        if not items:
            return [f"{key}: []"]
        return [f"{key}:"] + [f"- {item}" for item in items]

    @staticmethod
    def _yaml_quote(value: str) -> str:
        """Quote a YAML string value."""
        return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'
