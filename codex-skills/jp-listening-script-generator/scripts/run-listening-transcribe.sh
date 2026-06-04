#!/bin/zsh
set -euo pipefail

SCRIPT_DIR="${0:A:h}"
SKILL_DIR="${SCRIPT_DIR:h}"

find_vault_root() {
  local current="${PWD:A}"
  while [[ "${current}" != "/" ]]; do
    if [[ -f "${current}/tools/listening-transcribe-official/transcribe_listening.py" && -d "${current}/学习系统/听力" ]]; then
      echo "${current}"
      return 0
    fi
    current="${current:h}"
  done
  return 1
}

ROOT="$(find_vault_root || true)"
if [[ -z "${ROOT}" ]]; then
  echo "Unable to locate the vault root from ${PWD}" >&2
  exit 1
fi

PYTHON_BIN="${JP_LISTENING_PYTHON:-}"
if [[ -z "${PYTHON_BIN}" ]]; then
  if [[ -x "/opt/homebrew/bin/python3" ]]; then
    PYTHON_BIN="/opt/homebrew/bin/python3"
  else
    PYTHON_BIN="$(command -v python3)"
  fi
fi

"${PYTHON_BIN}" "${ROOT}/tools/listening-transcribe-official/transcribe_listening.py" "$@"
