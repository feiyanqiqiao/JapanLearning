#!/bin/zsh
set -euo pipefail

find_vault_root() {
  local current="${PWD:A}"
  while [[ "${current}" != "/" ]]; do
    if [[ -f "${current}/tools/listening-transcribe-official/requirements-listening.txt" ]]; then
      echo "${current}"
      return 0
    fi
    current="${current:h}"
  done
  return 1
}

ROOT="$(find_vault_root || true)"
if [[ -z "${ROOT}" ]]; then
  echo "Unable to locate the LingoTrace vault root from ${PWD}" >&2
  exit 1
fi

BOOTSTRAP_PYTHON="${LINGOTRACE_LISTENING_BOOTSTRAP_PYTHON:-/opt/homebrew/bin/python3.14}"
VENV_DIR="${LINGOTRACE_LISTENING_VENV_DIR:-${HOME}/Library/Caches/LingoTrace/venvs/cpython-314}"
VENV_PYTHON="${VENV_DIR}/bin/python"
SETUP_SCRIPT="${ROOT}/tools/listening-transcribe-official/setup_offline_dictionary.py"

if [[ ! -x "${BOOTSTRAP_PYTHON}" ]]; then
  echo "Python 3.14 bootstrap is missing: ${BOOTSTRAP_PYTHON}" >&2
  exit 1
fi

if [[ "$("${BOOTSTRAP_PYTHON}" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')" != "3.14" ]]; then
  echo "LingoTrace requires a Python 3.14 bootstrap: ${BOOTSTRAP_PYTHON}" >&2
  exit 1
fi

if [[ -e "${VENV_DIR}" && ! -x "${VENV_PYTHON}" ]]; then
  echo "Existing LingoTrace virtual environment is incomplete: ${VENV_DIR}" >&2
  echo "Remove it intentionally, then rerun this script." >&2
  exit 1
fi

if [[ ! -x "${VENV_PYTHON}" ]]; then
  mkdir -p "${VENV_DIR:h}"
  "${BOOTSTRAP_PYTHON}" -m venv "${VENV_DIR}"
fi

if [[ "$("${VENV_PYTHON}" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')" != "3.14" ]]; then
  echo "Existing LingoTrace virtual environment is not Python 3.14: ${VENV_DIR}" >&2
  echo "Remove it intentionally, then rerun this script." >&2
  exit 1
fi

"${VENV_PYTHON}" "${SETUP_SCRIPT}" --python "${VENV_PYTHON}" --install
echo "LingoTrace listening runtime is ready: ${VENV_PYTHON}"
