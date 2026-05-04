# JapanLearning

An Obsidian-based Japanese learning system framework.

This repository publishes the reusable structure, templates, automation, and a small set of curated examples from a personal Japanese learning vault. It is not a full vault backup and does not include private notes, commercial textbook audio, full textbook transcripts, or local Obsidian workspace state.

## What It Contains

- Obsidian-oriented study system structure under `system/`
- reusable Codex skills under `codex-skills/`
- vault-specific listening-note renderer under `tools/`
- documentation under `docs/`
- a small number of sanitized real examples under `examples/`

## What It Does Not Contain

- `.obsidian/` workspace files
- daily private notes
- textbook audio or video files
- commercial listening transcripts
- PDFs, screenshots, course schedules, or temporary files
- the generic ASR/audio import implementation

Generic audio import and ASR are handled by the sibling [ListenKit](https://github.com/feiyanqiqiao/ListenKit) project. This repository keeps only the Japanese-learning system and Obsidian note-generation logic.

## Repository Layout

```text
codex-skills/       Local Codex skills for maintaining the learning system
tools/              Vault-specific automation helpers and tests
docs/               Implementation notes and system boundaries
system/             Public framework structure, templates, and dashboards
examples/           Sanitized example cards and notes
```

## Using The Framework

1. Copy the `system/` structure into an Obsidian vault.
2. Install or adapt the skills in `codex-skills/`.
3. Place `ListenKit` next to this repository if you want the listening transcription workflow.
4. Add your own notes and learning content. Do not reuse copyrighted textbook audio or transcripts unless you have the right to do so.

## ListenKit Dependency

Listening transcription delegates to `../ListenKit/cli/transcribe-audio.sh`. You can override the sibling path with:

```bash
export LISTENKIT_ROOT=/path/to/ListenKit
```

This repository does not vendor `yt-dlp`, `ffmpeg`, Apple Speech helper code, or faster-whisper helpers.

## Privacy And Copyright

The included examples are curated and stripped of private source-note links. They are meant to demonstrate schema and workflow only. Do not commit your private daily notes, course materials, audio files, or commercial textbook transcripts.

