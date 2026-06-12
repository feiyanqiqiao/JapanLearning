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

PYTHON_BIN="${LINGOTRACE_LISTENING_PYTHON:-${JP_LISTENING_PYTHON:-${HOME}/Library/Caches/LingoTrace/venvs/cpython-314/bin/python}}"
INIT_SCRIPT="${ROOT}/codex-skills/jp-listening-script-generator/scripts/init-listening-runtime.sh"
SETUP_SCRIPT="${ROOT}/tools/listening-transcribe-official/setup_offline_dictionary.py"

if [[ ! -x "${PYTHON_BIN}" ]]; then
  echo "LingoTrace listening runtime is missing or not executable: ${PYTHON_BIN}" >&2
  echo "Repair: ${INIT_SCRIPT}" >&2
  exit 1
fi

if ! CHECK_OUTPUT="$("${PYTHON_BIN}" "${SETUP_SCRIPT}" --python "${PYTHON_BIN}" --check 2>&1)"; then
  print -r -- "${CHECK_OUTPUT}" >&2
  echo "LingoTrace listening runtime is unhealthy." >&2
  echo "Repair: ${INIT_SCRIPT}" >&2
  exit 1
fi

"${PYTHON_BIN}" "${ROOT}/tools/listening-transcribe-official/transcribe_listening.py" "$@"
