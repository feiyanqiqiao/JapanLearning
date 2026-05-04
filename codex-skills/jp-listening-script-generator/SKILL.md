---
name: jp-listening-script-generator
description: Generate Japanese listening practice notes in this Obsidian vault by transcribing one audio file at a time through the sibling ListenKit CLI and rendering the existing 精听稿 Markdown format.
---

# JP Listening Script Generator

Use this skill when the task is to turn one listening audio file in this vault into the existing 精听稿 Markdown note format. Generic ASR is delegated to the sibling `../ListenKit` CLI; this skill keeps only the Obsidian Japanese-learning workflow and note rendering rules.

## Maintenance Source Of Truth

The project copy is the source of truth:

- source: `codex-skills/jp-listening-script-generator/`
- installed copy: `~/.codex/skills/jp-listening-script-generator/`

Edit the project copy first, then sync it to the global skill directory.

Default sync command:

```bash
zsh codex-skills/jp-listening-script-generator/scripts/sync-to-global.sh
```

## Default Workflow

Prefer single-item processing first. The main path is:

1. identify one audio file under `学习系统/听力` or any of its child folders
2. locate the matching note, or create a new note when none exists yet
3. run the transcription pipeline
4. render the Markdown draft note
5. unless the user explicitly asked for `--dry-run`, immediately enter a second editing phase:
   - read the generated `## 脚本`
   - use model judgment to choose `0-5` truly reusable sentences
   - write the final `## 可直接背的常用句`
   - sync frontmatter `daily_use_sentences`
6. only then treat the note as complete

Context-budget rule for this skill:

- do not proactively open multiple existing sample notes just to match style
- first trust the generator's existing Markdown contract and naming heuristics
- only inspect an existing note when the generated result is clearly unstable or ambiguous
- when inspection is needed, prefer one nearest sample note and stop there unless the first sample still leaves the issue unresolved

When rerunning transcription for an existing note, preserve the already curated `## 可直接背的常用句`, `daily_use_sentences`, and any extra manual sections unless the user explicitly asks to reset them.

For short-choice listening materials such as `実力アップ/29番-32番.mp3`, the generator now switches into a short-choice mode automatically:

- it prefers keeping question numbers and `1/2/3` option structure
- it automatically retries with a slow-copy pass when that yields a better structure
- when an existing note already has a clearly better short-choice `## 脚本`, it preserves that script instead of overwriting it with a weaker retranscription

When there is any uncertainty about title quality or recognition stability, use `--dry-run` first.

## Model Route

The generator delegates transcription to `../ListenKit/cli/transcribe-audio.sh` and then applies vault-specific rendering. Set `LISTENKIT_ROOT` only when the sibling repo is not at `../ListenKit`.

- `--engine auto` is the default
- ordinary materials use ListenKit's bundled Apple Speech helper
- `Shadowing_*` path materials currently default to ListenKit's `faster-whisper small` on CPU with `int8` compute because Apple Speech tends to overfit short textbook prompts and misrecognize simple dialogue
- `--engine apple` forces the ListenKit Apple Speech route
- `--engine faster-whisper` forces the ListenKit faster-whisper route

For faster-whisper, use a Python environment with `faster-whisper` installed and set it explicitly when needed:

```bash
FASTER_WHISPER_PYTHON=/tmp/faster-whisper-small-test/bin/python \
zsh codex-skills/jp-listening-script-generator/scripts/run-listening-transcribe.sh "学习系统/听力/Shadowing_初中級/Unit1/04.mp3" --engine faster-whisper --locale ja-JP --dry-run
```

The current local test setup uses:

- model: `small`
- device: `cpu`
- compute type: `int8`
- observed cached run for `Unit1/04.mp3`: about 18 seconds, with peak memory around 1.1 GB footprint

## CLI Entry Point

The skill does not implement generic ASR itself. Always call the local Markdown generator through the wrapper; that generator calls ListenKit for transcription:

```bash
zsh codex-skills/jp-listening-script-generator/scripts/run-listening-transcribe.sh "学习系统/听力/中級を学ぼう/manabo_cz16.mp3"
```

Useful variants:

```bash
zsh codex-skills/jp-listening-script-generator/scripts/run-listening-transcribe.sh "学习系统/听力/中級を学ぼう/manabo_cz16.mp3"
zsh codex-skills/jp-listening-script-generator/scripts/run-listening-transcribe.sh "学习系统/听力/N2/202212/example.mp3" --locale ja-JP
zsh codex-skills/jp-listening-script-generator/scripts/run-listening-transcribe.sh "学习系统/听力/Shadowing_初中級/Unit1/04.mp3" --engine auto --locale ja-JP
```

The Apple Speech helper and generic ASR routing live in ListenKit. Do not reintroduce vault-local Apple Speech or faster-whisper helpers; update `../ListenKit` instead.

## Sandbox And Approval

The Apple Speech route launches ListenKit's local macOS helper app through `/usr/bin/open`. In Codex, that should be treated as a GUI launch, not as a normal sandbox-safe shell command.

- when using Apple Speech, do not probe this route in the sandbox first
- request escalated execution on the first Apple Speech invocation of `zsh codex-skills/jp-listening-script-generator/scripts/run-listening-transcribe.sh ...`
- when the approval UI appears, prefer saving a persistent prefix approval for `["zsh", "codex-skills/jp-listening-script-generator/scripts/run-listening-transcribe.sh"]`

That combination avoids the usual retry pattern of “sandbox run fails first, then ask for approval”.

The faster-whisper route is a normal ListenKit CLI subprocess. It does not launch a GUI helper, but it needs the model files to be present locally or downloadable by the configured Python environment.

## Output Contract

The generated note should follow the existing `manabo_cz15_私の町.md` shape:

- preserve the existing frontmatter as much as possible
- set `transcript_status: full`
- set `transcript_ref: in-note`
- keep the audio embed
- render `## 脚本`
- render `## 可直接背的常用句`
- render `## 素材说明`
- prefer a topic-bearing filename such as `manabo_cz18_土用の丑の日とうなぎ.md`, not a generic `识别稿`
- do not rely on rule-based extraction for `可直接背的常用句`; use model judgment after the script is generated
- for `可直接背的常用句`, prefer quality over quantity: 0-5 items is acceptable, and long sentences are allowed when the pattern is worth memorizing
- overly generic patterns such as `〜は〜です` should usually be rejected
- if nothing is genuinely worth memorizing, leaving the section empty is better than forcing filler content

For dialogue-type listening content, apply a dialogue template layer on top of the normal note contract:

- dialogue-type content is defined by the transcript structure, not by path name, `セクションN`, question numbers, or total length
- when the transcript clearly shows short question/answer or response turn-taking, render `## 脚本` with speaker labels such as `A：` and `B：`
- use a conservative rule: only add `A：/B：` when the alternation is clearly visible from the text
- if the transcript is ambiguous, monologic, list-like, or otherwise unstable, fall back to normal non-speaker formatting
- do not invent `C：` or multi-speaker labels because the current ListenKit transcript payload has no speaker metadata
- in dialogue-type notes, prefer `可直接背的常用句` selections that are reusable question templates, response templates, and social or situational exchanges

## Second-Phase Editing Rules

After the draft note exists, the skill should treat common-sentence curation as a required second phase, not as an optional extra.

- first prefer sentences that have reusable contrast, cause-effect, requirement, trend, evaluation, or question patterns
- for dialogue-type notes, prefer reusable question templates, response templates, social formulas, and scene-specific inquiries before long expository sentences
- avoid sentences that are only useful because of one specific noun unless the structure itself is broadly reusable
- long sentences are acceptable when their pattern is worth memorizing
- if a sentence is selected, keep frontmatter `daily_use_sentences` aligned with the final section
- if no sentence is selected, keep `daily_use_sentences: []`

## Batch Mode

Batch mode is intentionally disabled in the current Apple Speech helper route.
