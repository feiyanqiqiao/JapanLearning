#!/usr/bin/env python3
"""Unified configuration loader for LingoTrace multi-language architecture.

Loads language identity and feature flags from 系统配置/config.json.
All Python scripts should use this module instead of hardcoding language-specific values.

Usage:
    from config_loader import load_config, get_tag_namespace

    config = load_config(vault_root)
    namespace = get_tag_namespace(config)  # e.g. "jp"
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

DEFAULT_CONFIG_PATH = Path("系统配置/config.json")

# Fallback defaults for existing Japanese vaults without config.json.
# This ensures backward compatibility during the migration period.
_JAPANESE_DEFAULTS: dict[str, Any] = {
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


class ConfigError(RuntimeError):
    """Raised when config.json is present but structurally invalid."""


def load_config(
    vault_root: Path,
    config_path: Path | str | None = None,
    *,
    fallback_to_defaults: bool = True,
) -> dict[str, Any]:
    """Load and validate the language configuration.

    Args:
        vault_root: Absolute path to the vault root directory.
        config_path: Override path to config.json. If relative, resolved against vault_root.
                     Defaults to 系统配置/config.json.
        fallback_to_defaults: If True and config.json is missing, return Japanese defaults.
                              If False, raise ConfigError on missing file.

    Returns:
        Parsed config dict with at least ``language_profile`` and ``features`` keys.

    Raises:
        ConfigError: If config.json is missing (and fallback disabled) or structurally invalid.
    """
    if config_path is None:
        resolved = vault_root / DEFAULT_CONFIG_PATH
    else:
        p = Path(config_path)
        resolved = p if p.is_absolute() else vault_root / p

    if not resolved.exists():
        if fallback_to_defaults:
            return dict(_JAPANESE_DEFAULTS)
        raise ConfigError(f"config file not found: {resolved}")

    try:
        raw = json.loads(resolved.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ConfigError(f"invalid JSON in {resolved}: {exc}") from exc

    if not isinstance(raw, dict):
        raise ConfigError(f"config must be a JSON object, got {type(raw).__name__}")

    # Validate required top-level keys
    if "language_profile" not in raw:
        raise ConfigError(f"config {resolved} is missing required key 'language_profile'")

    profile = raw["language_profile"]
    if not isinstance(profile, dict):
        raise ConfigError("'language_profile' must be a JSON object")

    # Validate required language_profile fields
    _required_field(profile, "name", resolved)
    _required_field(profile, "tag_namespace", resolved)
    _required_field(profile, "speaking_text_field", resolved)

    # Ensure features exists (default to empty)
    if "features" not in raw:
        raw["features"] = {}

    return raw


def get_tag_namespace(config: dict[str, Any]) -> str:
    """Return the tag namespace prefix (e.g. 'jp', 'fr')."""
    return config["language_profile"]["tag_namespace"]


def get_speaking_text_field(config: dict[str, Any]) -> str:
    """Return the frontmatter field name for speaking card text (e.g. 'jp_text')."""
    return config["language_profile"]["speaking_text_field"]


def get_listenkit_locale(config: dict[str, Any]) -> str:
    """Return the ListenKit locale string (e.g. 'ja-JP')."""
    return config["language_profile"].get("listenkit_locale", "")


def get_listenkit_language(config: dict[str, Any]) -> str:
    """Return the ListenKit language name (e.g. 'Japanese')."""
    return config["language_profile"].get("listenkit_language", "")


def get_pronunciation_system(config: dict[str, Any]) -> str:
    """Return the pronunciation system identifier (e.g. 'pitch_accent')."""
    return config["language_profile"].get("pronunciation_system", "")


def get_language_name(config: dict[str, Any]) -> str:
    """Return the human-readable language name (e.g. 'Japanese')."""
    return config["language_profile"]["name"]


def is_feature_enabled(config: dict[str, Any], feature: str) -> bool:
    """Check whether a feature flag is enabled.

    Args:
        config: Parsed config dict.
        feature: Feature name (e.g. 'offline_dictionary', 'accent_audit').

    Returns:
        True if the feature is explicitly set to True; False otherwise.
    """
    return bool(config.get("features", {}).get(feature, False))


def _required_field(profile: dict, key: str, config_path: Path) -> None:
    if key not in profile:
        raise ConfigError(f"config {config_path}: language_profile is missing required key '{key}'")
