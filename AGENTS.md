# AGENTS.md

This repository is a public export of an Obsidian-based Japanese learning system. Treat Markdown notes, frontmatter, wikilinks, Bases, and local Codex skills as part of the user-facing study system.

## Entry Points

- Vocabulary maintenance: `codex-skills/jp-vocab-maintainer/SKILL.md`
- Listening transcription notes: `codex-skills/jp-listening-script-generator/SKILL.md`
- End-of-day review rollover: `codex-skills/jp-next-day-review-updater/SKILL.md`
- Generic audio import and ASR: sibling `../ListenKit`

## Operating Rules

- Keep private vault content out of this public repository.
- Do not add audio, video, PDFs, screenshots, Obsidian workspace files, temp files, or caches.
- Keep examples small, curated, and stripped of private source-note links.
- Do not reintroduce generic ASR helpers or yt-dlp wrappers here; update ListenKit instead.
- Preserve frontmatter and Obsidian links when editing system templates or examples.

## Verification

Before publishing, run the repository safety scans from `README.md` or the release checklist in the final implementation notes. For workflow changes, run the focused Python unit tests under `tools/` and `codex-skills/`.

