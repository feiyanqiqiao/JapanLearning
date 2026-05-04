#!/bin/zsh
set -euo pipefail

SCRIPT_DIR="${0:A:h}"
SKILL_DIR="${SCRIPT_DIR:h}"
TARGET_DIR="${HOME}/.codex/skills/jp-vocab-maintainer"

mkdir -p "${TARGET_DIR}/agents"
cp "${SKILL_DIR}/SKILL.md" "${TARGET_DIR}/SKILL.md"
cp "${SKILL_DIR}/agents/openai.yaml" "${TARGET_DIR}/agents/openai.yaml"

echo "Synced jp-vocab-maintainer to ${TARGET_DIR}"
