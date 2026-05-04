# Listening

The public repository does not include textbook audio, commercial listening transcripts, or generated full scripts.

Use the sibling ListenKit project for generic audio import and ASR:

```bash
../ListenKit/cli/import-audio.sh --url <url> --output-dir work/audio
../ListenKit/cli/transcribe-audio.sh --audio-path <audio> --locale ja-JP
```

The Japanese vault-specific renderer lives in `tools/listening-transcribe-official/` and creates Obsidian-style 精听稿 notes.

