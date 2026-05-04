import importlib.util
import json
import sys
import tempfile
import unittest
from io import StringIO
from pathlib import Path
from unittest import mock


MODULE_PATH = Path(__file__).resolve().parents[1] / "transcribe_listening.py"
SPEC = importlib.util.spec_from_file_location("transcribe_listening", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class TranscribeListeningTests(unittest.TestCase):
    def test_process_one_preserves_existing_second_phase_edits(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            audio_path = root / "manabo_cz20.mp3"
            audio_path.write_bytes(b"")
            note_path = root / "manabo_cz20_1日の摂取カロリー.md"
            note_path.write_text(
                "\n".join(
                    [
                        "---",
                        "track: listening",
                        "daily_use_sentences:",
                        "  - 既存の例文です。",
                        "transcript_status: full",
                        "transcript_ref: in-note",
                        "---",
                        "",
                        "# manabo_cz20 1日の摂取カロリー",
                        "",
                        "![[manabo_cz20.mp3]]",
                        "",
                        "## 脚本",
                        "",
                        "旧脚本です。",
                        "",
                        "## 可直接背的常用句",
                        "",
                        "原句：既存の例文です。",
                        "句式：既存の句式説明。",
                        "可替换骨架：AはBです。",
                        "",
                        "## 素材说明",
                        "",
                        "人工で補った説明です。",
                        "",
                        "## 我的备注",
                        "",
                        "ここは残したいメモです。",
                        "",
                    ]
                ),
                encoding="utf-8",
            )

            payload = {
                "full_text": "新しい文です。次の文です。",
                "segments": [
                    {"start": 0.0, "end": 1.0, "text": "新しい文です。"},
                    {"start": 1.2, "end": 2.1, "text": "次の文です。"},
                ],
            }

            with mock.patch.object(MODULE, "invoke_helper", return_value=payload):
                result = MODULE.process_one(audio_path, None, "ja-JP", None, False)

            self.assertIn("Updated", result)
            rendered = note_path.read_text(encoding="utf-8")
            self.assertIn("新しい文です。", rendered)
            self.assertIn("次の文です。", rendered)
            self.assertIn("原句：既存の例文です。", rendered)
            self.assertIn("人工で補った説明です。", rendered)
            self.assertIn("## 我的备注", rendered)
            self.assertIn("ここは残したいメモです。", rendered)
            self.assertIn("  - 既存の例文です。", rendered)

    def test_process_one_creates_placeholder_when_note_is_new(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            audio_path = root / "manabo_cz99.mp3"
            audio_path.write_bytes(b"")
            payload = {
                "full_text": "これは新しい素材です。",
                "segments": [
                    {"start": 0.0, "end": 1.0, "text": "これは新しい素材です。"},
                ],
            }

            with mock.patch.object(MODULE, "invoke_helper", return_value=payload):
                result = MODULE.process_one(audio_path, None, "ja-JP", None, False)

            self.assertIn("Created", result)
            created_notes = list(root.glob("manabo_cz99_*.md"))
            self.assertEqual(len(created_notes), 1)
            rendered = created_notes[0].read_text(encoding="utf-8")
            self.assertIn("daily_use_sentences: []", rendered)
            self.assertIn(MODULE.COMMON_SECTION_PLACEHOLDER, rendered)

    def test_process_one_preserves_intentionally_empty_common_section(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            audio_path = root / "manabo_cz21.mp3"
            audio_path.write_bytes(b"")
            note_path = root / "manabo_cz21_恵方巻きとうなぎとお菓子.md"
            note_path.write_text(
                "\n".join(
                    [
                        "---",
                        "track: listening",
                        "daily_use_sentences: []",
                        "transcript_status: full",
                        "transcript_ref: in-note",
                        "---",
                        "",
                        "# manabo_cz21 恵方巻きとうなぎとお菓子",
                        "",
                        "![[manabo_cz21.mp3]]",
                        "",
                        "## 脚本",
                        "",
                        "旧脚本です。",
                        "",
                        "## 可直接背的常用句",
                        "",
                        "",
                        "## 素材说明",
                        "",
                        "",
                    ]
                ),
                encoding="utf-8",
            )

            payload = {
                "full_text": "新しい脚本です。",
                "segments": [
                    {"start": 0.0, "end": 1.0, "text": "新しい脚本です。"},
                ],
            }

            with mock.patch.object(MODULE, "invoke_helper", return_value=payload):
                MODULE.process_one(audio_path, None, "ja-JP", None, False)

            rendered = note_path.read_text(encoding="utf-8")
            self.assertNotIn(MODULE.COMMON_SECTION_PLACEHOLDER, rendered)
            common_block = rendered.split("## 可直接背的常用句", 1)[1].split("## 素材说明", 1)[0]
            self.assertEqual(common_block.strip(), "")

    def test_dry_run_does_not_rename_generated_note(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            audio_path = root / "manabo_cz20.mp3"
            audio_path.write_bytes(b"")
            placeholder_path = root / "manabo_cz20_识别稿.md"
            target_path = root / "manabo_cz20_1日の摂取カロリー.md"
            placeholder_path.write_text(
                "\n".join(
                    [
                        "---",
                        "track: listening",
                        "daily_use_sentences: []",
                        "transcript_status: partial",
                        "transcript_ref: in-note",
                        "---",
                        "",
                        "# manabo_cz20 识别稿",
                        "",
                        "![[manabo_cz20.mp3]]",
                        "",
                        "## 脚本",
                        "",
                        "旧脚本です。",
                        "",
                        "## 我的备注",
                        "",
                        "ここは残したいメモです。",
                        "",
                    ]
                ),
                encoding="utf-8",
            )
            payload = {
                "full_text": "摂取カロリーについて話しています。摂取カロリーは大切です。",
                "segments": [
                    {"start": 0.0, "end": 1.0, "text": "摂取カロリーについて話しています。"},
                    {"start": 1.2, "end": 2.1, "text": "摂取カロリーは大切です。"},
                ],
            }

            with mock.patch.object(MODULE, "invoke_helper", return_value=payload):
                result = MODULE.process_one(audio_path, None, "ja-JP", None, True)

            self.assertTrue(placeholder_path.exists())
            self.assertFalse(target_path.exists())
            self.assertIn(str(target_path), result)
            self.assertIn("## 我的备注", result)
            self.assertIn("ここは残したいメモです。", result)

    def test_new_notes_infer_source_tag_from_audio_path(self) -> None:
        cases = [
            ("中級を学ぼう/manabo_cz99.mp3", "source/manabo"),
            ("ドリル＆ドリル　日本語能力試験Ｎ3/N3 A-5.mp3", "source/drill_n3"),
            ("実力アップ/29番-32番.mp3", "source/jitsuryoku_up"),
        ]

        for relative_path, expected_tag in cases:
            with self.subTest(relative_path=relative_path):
                frontmatter = MODULE.build_default_frontmatter(Path(relative_path), 1, False)
                self.assertIn(f"  - {expected_tag}", frontmatter)

    def test_dialogue_frontmatter_uses_dialogue_defaults(self) -> None:
        frontmatter = MODULE.build_default_frontmatter(Path("Shadowing_初中級/Unit1/04.mp3"), 4, False, True)
        self.assertIn("  - 对话轮替时容易把发言人和应答关系听反", frontmatter)
        self.assertIn("practice_focus: 先确认每轮是谁在问、谁在答，再抓场景里的高频问句和应答模板。", frontmatter)

    def test_conservative_dialogue_detection_marks_clear_qa(self) -> None:
        rendered = MODULE.render_conservative_ab_dialogue(
            ["駅までどのくらいですか？", "歩いて5分ぐらいです。"]
        )
        self.assertEqual(rendered, ["A：駅までどのくらいですか？", "B：歩いて5分ぐらいです。"])

    def test_conservative_dialogue_detection_rejects_monologue(self) -> None:
        rendered = MODULE.render_conservative_ab_dialogue(
            ["今日は良い天気ですね。", "朝から公園を散歩して、とても静かなたたずまいを楽しみました。"]
        )
        self.assertIsNone(rendered)

    def test_non_dialogue_script_keeps_plain_paragraphs(self) -> None:
        chunks = [
            MODULE.Chunk(start=0.0, end=1.0, text="今日は良い天気ですね。"),
            MODULE.Chunk(start=1.0, end=2.0, text="朝から公園を散歩して、とても静かなたたずまいを楽しみました。"),
        ]
        rendered, dialogue_mode = MODULE.render_dialogue_script_section(
            ["今日は良い天気ですね。", "朝から公園を散歩して、とても静かなたたずまいを楽しみました。"],
            chunks,
            False,
        )
        self.assertFalse(dialogue_mode)
        self.assertNotIn("A：", rendered)

    def test_main_rejects_scan_dir_for_apple_helper_route(self) -> None:
        stderr = StringIO()
        with mock.patch.object(sys, "argv", ["transcribe-listening", "--scan-dir", "学习系统/听力"]):
            with mock.patch("sys.stderr", stderr):
                exit_code = MODULE.main()

        self.assertEqual(exit_code, 1)
        self.assertIn("Batch scan mode is not supported", stderr.getvalue())

    def test_auto_engine_uses_faster_whisper_for_shadowing(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            audio_dir = root / "Shadowing_初中級" / "Unit1"
            audio_dir.mkdir(parents=True)
            audio_path = audio_dir / "04.mp3"
            audio_path.write_bytes(b"")
            payload = {
                "full_text": "",
                "segments": [
                    {"start": 0.0, "end": 3.0, "text": "セクション4"},
                    {"start": 3.0, "end": 5.0, "text": "1"},
                    {"start": 5.0, "end": 8.0, "text": "はじめまして、わたなべです。"},
                    {"start": 8.0, "end": 14.0, "text": "たなかです。どうぞよろしく。"},
                    {"start": 54.8, "end": 55.3, "text": "2"},
                    {"start": 55.4, "end": 59.4, "text": "山田さんの部屋は何回ですか?"},
                    {"start": 59.4, "end": 63.4, "text": "3回です。"},
                    {"start": 70.0, "end": 70.3, "text": "3"},
                    {"start": 70.4, "end": 72.4, "text": "奥には?"},
                ],
            }

            with mock.patch.object(MODULE, "invoke_faster_whisper", return_value=payload) as faster_mock:
                with mock.patch.object(MODULE, "invoke_helper") as apple_mock:
                    result = MODULE.process_one(audio_path, None, "ja-JP", "田中です", True)

            faster_mock.assert_called_once()
            apple_mock.assert_not_called()
            self.assertIn("セクション4", result)
            self.assertIn("1\nA：はじめまして、渡辺です。\nB：田中です。どうぞよろしく。", result)
            self.assertIn("2\nA：山田さんの部屋は何階ですか？\nB：三階です。", result)
            self.assertIn("3\nお国は？", result)
            self.assertIn(MODULE.FASTER_WHISPER_MATERIAL_NOTE, result)
            self.assertIn(MODULE.DIALOGUE_MATERIAL_NOTE_SUFFIX, result)

    def test_shadowing_normalization_handles_context_homophones(self) -> None:
        self.assertEqual(MODULE.normalize_shadowing_text("山田さんの部屋は何回ですか?"), "山田さんの部屋は何階ですか？")
        self.assertEqual(MODULE.normalize_shadowing_text("3回です。"), "三階です。")
        self.assertEqual(MODULE.normalize_shadowing_text("奥には?"), "お国は？")

    def test_faster_whisper_invocation_uses_listenkit_cli(self) -> None:
        result = mock.Mock(
            returncode=0,
            stdout=json.dumps(
                {
                    "engine": "faster-whisper",
                    "locale": "ja-JP",
                    "language": "ja",
                    "full_text": "ok",
                    "segments": [],
                    "timing_complete": True,
                },
                ensure_ascii=False,
            ),
            stderr="",
        )

        with mock.patch.object(MODULE.subprocess, "run", return_value=result) as run_mock:
            payload = MODULE.invoke_faster_whisper(Path("/tmp/audio.mp3"), "ja-JP", "/tmp/fw/bin/python")

        command = run_mock.call_args.args[0]
        env = run_mock.call_args.kwargs["env"]
        self.assertIn("ListenKit/cli/transcribe-audio.sh", command[1])
        self.assertIn("--engine", command)
        self.assertIn("faster-whisper", command)
        self.assertEqual(env["FASTER_WHISPER_PYTHON"], "/tmp/fw/bin/python")
        self.assertEqual(payload["engine"], "faster-whisper")

    def test_apple_invocation_uses_listenkit_builtin_helper(self) -> None:
        result = mock.Mock(
            returncode=0,
            stdout=json.dumps(
                {
                    "engine": "apple",
                    "locale": "ja-JP",
                    "full_text": "ok",
                    "segments": [],
                    "timing_complete": True,
                },
                ensure_ascii=False,
            ),
            stderr="",
        )

        with mock.patch.dict(MODULE.os.environ, {"LISTENKIT_ROOT": "/tmp/listenkit"}, clear=True):
            with mock.patch.object(MODULE.subprocess, "run", return_value=result) as run_mock:
                payload = MODULE.invoke_helper(Path("/tmp/audio.mp3"), "ja-JP")

        command = run_mock.call_args.args[0]
        env = run_mock.call_args.kwargs["env"]
        self.assertEqual(command[1], "/tmp/listenkit/cli/transcribe-audio.sh")
        self.assertIn("--engine", command)
        self.assertIn("apple", command)
        self.assertNotIn("APPLE_SPEECH_HELPER", env)
        self.assertEqual(payload["engine"], "apple")

    def test_existing_note_title_is_preserved_for_shadowing_rerun(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            audio_dir = root / "Shadowing_初中級" / "Unit1"
            audio_dir.mkdir(parents=True)
            audio_path = audio_dir / "04.mp3"
            audio_path.write_bytes(b"")
            note_path = audio_dir / "04_田中です.md"
            note_path.write_text(
                "\n".join(
                    [
                        "---",
                        "track: listening",
                        "daily_use_sentences: []",
                        "transcript_status: full",
                        "transcript_ref: in-note",
                        "---",
                        "",
                        "# 04 田中です",
                        "",
                        "![[04.mp3]]",
                        "",
                        "## 脚本",
                        "",
                        "旧脚本です。",
                        "",
                    ]
                ),
                encoding="utf-8",
            )
            payload = {
                "full_text": "",
                "segments": [
                    {"start": 0.0, "end": 3.0, "text": "セクション4"},
                    {"start": 3.0, "end": 5.0, "text": "1"},
                    {"start": 5.0, "end": 8.0, "text": "ホットコーヒーのMひとつください。"},
                ],
            }

            with mock.patch.object(MODULE, "invoke_faster_whisper", return_value=payload):
                result = MODULE.process_one(audio_path, None, "ja-JP", None, True)

            self.assertIn("# 04 田中です", result)
            self.assertNotIn("# 04 ホットコーヒー", result)

    def test_shadowing_four_turn_exchange_is_rendered_as_abab(self) -> None:
        chunks = [
            MODULE.Chunk(start=0.0, end=1.0, text="セクション7"),
            MODULE.Chunk(start=1.0, end=2.0, text="7"),
            MODULE.Chunk(start=2.0, end=3.0, text="お名前は？"),
            MODULE.Chunk(start=3.0, end=4.0, text="ペドロです。"),
            MODULE.Chunk(start=4.0, end=5.0, text="お国は？"),
            MODULE.Chunk(start=5.0, end=6.0, text="スペインです。"),
        ]
        rendered, dialogue_mode = MODULE.render_dialogue_script_section([], chunks, True)
        self.assertTrue(dialogue_mode)
        self.assertIn("7\nA：お名前は？\nB：ペドロです。\nA：お国は？\nB：スペインです。", rendered)


if __name__ == "__main__":
    unittest.main()
