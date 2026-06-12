#!/usr/bin/env python3
"""Tests for tools/config_loader.py."""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import sys

# Allow importing from tools/
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config_loader import (
    ConfigError,
    get_language_name,
    get_listenkit_language,
    get_listenkit_locale,
    get_pronunciation_system,
    get_speaking_text_field,
    get_tag_namespace,
    is_feature_enabled,
    load_config,
)


class TestLoadConfigExisting(unittest.TestCase):
    """Tests with a valid config.json present."""

    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.vault_root = Path(self.tmpdir.name)
        self.config_dir = self.vault_root / "系统配置"
        self.config_dir.mkdir(parents=True)
        self.config_path = self.config_dir / "config.json"
        self.valid_config = {
            "language_profile": {
                "name": "Japanese",
                "tag_namespace": "jp",
                "listenkit_locale": "ja-JP",
                "listenkit_language": "Japanese",
                "pronunciation_system": "pitch_accent",
                "speaking_text_field": "jp_text",
            },
            "features": {
                "offline_dictionary": True,
                "accent_audit": True,
            },
        }
        self.config_path.write_text(json.dumps(self.valid_config, ensure_ascii=False), encoding="utf-8")

    def tearDown(self):
        self.tmpdir.cleanup()

    def test_load_valid_config(self):
        config = load_config(self.vault_root)
        self.assertEqual(config["language_profile"]["name"], "Japanese")
        self.assertEqual(config["language_profile"]["tag_namespace"], "jp")

    def test_get_tag_namespace(self):
        config = load_config(self.vault_root)
        self.assertEqual(get_tag_namespace(config), "jp")

    def test_get_speaking_text_field(self):
        config = load_config(self.vault_root)
        self.assertEqual(get_speaking_text_field(config), "jp_text")

    def test_get_listenkit_locale(self):
        config = load_config(self.vault_root)
        self.assertEqual(get_listenkit_locale(config), "ja-JP")

    def test_get_listenkit_language(self):
        config = load_config(self.vault_root)
        self.assertEqual(get_listenkit_language(config), "Japanese")

    def test_get_pronunciation_system(self):
        config = load_config(self.vault_root)
        self.assertEqual(get_pronunciation_system(config), "pitch_accent")

    def test_get_language_name(self):
        config = load_config(self.vault_root)
        self.assertEqual(get_language_name(config), "Japanese")

    def test_is_feature_enabled_true(self):
        config = load_config(self.vault_root)
        self.assertTrue(is_feature_enabled(config, "offline_dictionary"))
        self.assertTrue(is_feature_enabled(config, "accent_audit"))

    def test_is_feature_enabled_missing(self):
        config = load_config(self.vault_root)
        self.assertFalse(is_feature_enabled(config, "nonexistent_feature"))

    def test_custom_config_path(self):
        alt_path = self.vault_root / "custom" / "my_config.json"
        alt_path.parent.mkdir(parents=True)
        alt_path.write_text(json.dumps(self.valid_config), encoding="utf-8")
        config = load_config(self.vault_root, config_path="custom/my_config.json")
        self.assertEqual(get_tag_namespace(config), "jp")

    def test_absolute_config_path(self):
        config = load_config(self.vault_root, config_path=str(self.config_path))
        self.assertEqual(get_tag_namespace(config), "jp")


class TestLoadConfigFallback(unittest.TestCase):
    """Tests for fallback behavior when config.json is missing."""

    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.vault_root = Path(self.tmpdir.name)

    def tearDown(self):
        self.tmpdir.cleanup()

    def test_missing_config_returns_defaults(self):
        config = load_config(self.vault_root, fallback_to_defaults=True)
        self.assertEqual(get_tag_namespace(config), "jp")
        self.assertEqual(get_language_name(config), "Japanese")
        self.assertEqual(get_speaking_text_field(config), "jp_text")

    def test_missing_config_raises_when_disabled(self):
        with self.assertRaises(ConfigError):
            load_config(self.vault_root, fallback_to_defaults=False)


class TestLoadConfigValidation(unittest.TestCase):
    """Tests for config validation errors."""

    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.vault_root = Path(self.tmpdir.name)
        self.config_dir = self.vault_root / "系统配置"
        self.config_dir.mkdir(parents=True)
        self.config_path = self.config_dir / "config.json"

    def tearDown(self):
        self.tmpdir.cleanup()

    def test_invalid_json(self):
        self.config_path.write_text("{bad json", encoding="utf-8")
        with self.assertRaises(ConfigError):
            load_config(self.vault_root, fallback_to_defaults=False)

    def test_not_an_object(self):
        self.config_path.write_text('"just a string"', encoding="utf-8")
        with self.assertRaises(ConfigError):
            load_config(self.vault_root, fallback_to_defaults=False)

    def test_missing_language_profile(self):
        self.config_path.write_text(json.dumps({"features": {}}), encoding="utf-8")
        with self.assertRaises(ConfigError):
            load_config(self.vault_root, fallback_to_defaults=False)

    def test_missing_tag_namespace(self):
        bad = {
            "language_profile": {
                "name": "Test",
                "speaking_text_field": "text",
            }
        }
        self.config_path.write_text(json.dumps(bad), encoding="utf-8")
        with self.assertRaises(ConfigError):
            load_config(self.vault_root, fallback_to_defaults=False)

    def test_missing_name(self):
        bad = {
            "language_profile": {
                "tag_namespace": "fr",
                "speaking_text_field": "fr_text",
            }
        }
        self.config_path.write_text(json.dumps(bad), encoding="utf-8")
        with self.assertRaises(ConfigError):
            load_config(self.vault_root, fallback_to_defaults=False)

    def test_missing_speaking_text_field(self):
        bad = {
            "language_profile": {
                "name": "French",
                "tag_namespace": "fr",
            }
        }
        self.config_path.write_text(json.dumps(bad), encoding="utf-8")
        with self.assertRaises(ConfigError):
            load_config(self.vault_root, fallback_to_defaults=False)

    def test_missing_features_gets_default(self):
        minimal = {
            "language_profile": {
                "name": "Test",
                "tag_namespace": "t",
                "speaking_text_field": "t_text",
            }
        }
        self.config_path.write_text(json.dumps(minimal), encoding="utf-8")
        config = load_config(self.vault_root, fallback_to_defaults=False)
        self.assertEqual(config["features"], {})
        self.assertFalse(is_feature_enabled(config, "offline_dictionary"))


class TestLoadConfigFrench(unittest.TestCase):
    """Tests with a non-Japanese language config."""

    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.vault_root = Path(self.tmpdir.name)
        self.config_dir = self.vault_root / "系统配置"
        self.config_dir.mkdir(parents=True)
        self.config_path = self.config_dir / "config.json"
        self.french_config = {
            "language_profile": {
                "name": "French",
                "tag_namespace": "fr",
                "listenkit_locale": "fr-FR",
                "listenkit_language": "French",
                "pronunciation_system": "ipa",
                "speaking_text_field": "fr_text",
            },
            "features": {
                "offline_dictionary": False,
                "accent_audit": False,
            },
        }
        self.config_path.write_text(json.dumps(self.french_config, ensure_ascii=False), encoding="utf-8")

    def tearDown(self):
        self.tmpdir.cleanup()

    def test_french_config_loads(self):
        config = load_config(self.vault_root)
        self.assertEqual(get_tag_namespace(config), "fr")
        self.assertEqual(get_language_name(config), "French")
        self.assertEqual(get_speaking_text_field(config), "fr_text")
        self.assertEqual(get_pronunciation_system(config), "ipa")
        self.assertFalse(is_feature_enabled(config, "offline_dictionary"))


if __name__ == "__main__":
    unittest.main()
