#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path


CIRCLED_ACCENT_MARKS = "⓪①②③④⑤⑥⑦⑧⑨"
ACCENT_TYPE_TO_MARK = {str(index): mark for index, mark in enumerate(CIRCLED_ACCENT_MARKS)}


def accent_marks_from_type(value: str) -> str | None:
    marks = [
        ACCENT_TYPE_TO_MARK[item]
        for item in re.findall(r"\d+", value or "")
        if item in ACCENT_TYPE_TO_MARK
    ]
    if not marks:
        return None
    return "/".join(dict.fromkeys(marks))


def default_cache_dir() -> Path:
    override = os.environ.get("JP_LISTENING_DICT_DIR")
    if override:
        return Path(override).expanduser()
    return Path.home() / "Library" / "Caches" / "jp-listening-dicts"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="setup-offline-dictionary",
        description="Prepare the offline Japanese dictionary cache for listening learning packages.",
    )
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--check", action="store_true", help="Check whether an offline dictionary cache is usable.")
    action.add_argument("--install", action="store_true", help="Install fugashi and unidic-lite into the cache.")
    action.add_argument("--dry-run", action="store_true", help="Print the install command without running it.")
    parser.add_argument("--cache-dir", type=Path, default=None)
    parser.add_argument("--python", default=sys.executable)
    return parser.parse_args()


def cache_dir_from_args(args: argparse.Namespace) -> Path:
    return args.cache_dir.expanduser() if args.cache_dir else default_cache_dir()


def static_accent_map_path(cache_dir: Path) -> Path:
    return cache_dir / "accent_map.json"


def python_runtime_info(python_executable: str) -> dict[str, str]:
    code = (
        "import json, sys; "
        "print(json.dumps({'executable': sys.executable, 'version': sys.version.split()[0], "
        "'cache_tag': sys.implementation.cache_tag}))"
    )
    try:
        result = subprocess.run(
            [python_executable, "-I", "-c", code],
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=15,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise RuntimeError(f"Unable to inspect Python runtime {python_executable}: {exc}") from exc
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip() or f"exit code {result.returncode}"
        raise RuntimeError(f"Unable to inspect Python runtime {python_executable}: {detail}")
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Python runtime returned invalid metadata: {result.stdout.strip()}") from exc
    if not payload.get("cache_tag"):
        raise RuntimeError(f"Python runtime did not report an ABI cache tag: {python_executable}")
    return {key: str(value) for key, value in payload.items()}


def python_target(cache_dir: Path, cache_tag: str) -> Path:
    return cache_dir / "python" / cache_tag


def import_from_cache(cache_dir: Path, runtime: dict[str, str]) -> tuple[bool, str]:
    target = python_target(cache_dir, runtime["cache_tag"])
    code = r'''
import json
import re
import sys

sys.path.insert(0, sys.argv[1])
import fugashi
import unidic_lite

tagger = fugashi.Tagger(f"-d {unidic_lite.DICDIR}")
words = list(tagger("公園を散歩します。"))
tokens = [str(word.surface) for word in words]
marks = "⓪①②③④⑤⑥⑦⑧⑨"
accents = []
for word in words:
    values = re.findall(r"\d+", str(getattr(word.feature, "aType", "") or ""))
    rendered = "/".join(dict.fromkeys(marks[int(value)] for value in values if int(value) < len(marks)))
    if rendered:
        accents.append(f"{word.surface}{rendered}")
print(json.dumps({"tokens": tokens, "accents": accents}, ensure_ascii=False))
'''
    try:
        result = subprocess.run(
            [runtime["executable"], "-I", "-c", code, str(target)],
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=60,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return False, f"Python dictionary health check failed: {exc}"
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip() or f"exit code {result.returncode}"
        return False, f"Python dictionary packages are not ready: {detail}"
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError:
        return False, f"Python dictionary health check returned invalid output: {result.stdout.strip()}"
    tokens = [str(item) for item in payload.get("tokens", [])]
    accents = [str(item) for item in payload.get("accents", [])]
    if not tokens:
        return False, "fugashi loaded but did not parse the sample sentence."
    if not accents:
        return False, "fugashi loaded but returned no sample accent candidates."
    return True, f"fugashi + unidic-lite ready; sample tokens: {' / '.join(tokens)}; sample accents: {' / '.join(accents)}"


def check_cache(cache_dir: Path, python_executable: str) -> tuple[bool, list[str]]:
    messages = [f"cache_dir: {cache_dir}"]
    try:
        runtime = python_runtime_info(python_executable)
    except RuntimeError as exc:
        return False, messages + [str(exc)]
    target = python_target(cache_dir, runtime["cache_tag"])
    messages.extend(
        [
            f"python: {runtime['executable']}",
            f"version: {runtime['version']}",
            f"abi_tag: {runtime['cache_tag']}",
            f"python_target: {target}",
        ]
    )
    accent_map = static_accent_map_path(cache_dir)
    if accent_map.exists():
        try:
            payload = json.loads(accent_map.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            return False, messages + [f"accent_map.json invalid: {exc}"]
        if isinstance(payload, dict):
            messages.append(f"accent_map.json entries: {len(payload)}")
        else:
            return False, messages + ["accent_map.json must contain a JSON object."]

    package_ready, package_message = import_from_cache(cache_dir, runtime)
    messages.append(package_message)
    if package_ready:
        return True, messages
    return False, messages + ["No usable offline dictionary found."]


def install_command(args: argparse.Namespace, cache_dir: Path, runtime: dict[str, str]) -> list[str]:
    return [
        args.python,
        "-m",
        "pip",
        "install",
        "--upgrade",
        "--target",
        str(python_target(cache_dir, runtime["cache_tag"])),
        "fugashi",
        "unidic-lite",
    ]


def main() -> int:
    args = parse_args()
    cache_dir = cache_dir_from_args(args)

    if args.check:
        ok, messages = check_cache(cache_dir, args.python)
        print("\n".join(messages))
        return 0 if ok else 1

    try:
        runtime = python_runtime_info(args.python)
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    command = install_command(args, cache_dir, runtime)
    if args.dry_run:
        print(" ".join(command))
        return 0

    cache_dir.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(command, check=False)
    if result.returncode != 0:
        return result.returncode
    ok, messages = check_cache(cache_dir, args.python)
    print("\n".join(messages))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
