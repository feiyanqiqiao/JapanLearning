# 听力精听稿项目实施梳理

## 当前主线

当前实现已经收敛到一条固定链路：

1. `codex-skills/jp-listening-script-generator/scripts/run-listening-transcribe.sh`
2. `tools/listening-transcribe-official/transcribe_listening.py`
3. `../ListenKit/cli/transcribe-audio.sh`
4. ListenKit backend:
   - ordinary materials: bundled Apple Speech helper
   - Shadowing materials: `faster-whisper small` on CPU with `int8`
5. 回写精听稿 Markdown

当前成品笔记默认只保留这些部分：

- frontmatter
- 标题
- 音频 embed
- `## 脚本`
- `## 可直接背的常用句`
- `## 素材说明`

每个听力素材目录使用固定边界：

- 学习笔记保留在素材目录根部
- 原音频与逐句切片放在 `attach/`
- ListenKit 原始 `.listenkit.md/.json` 产物放在 `artifacts/`

## 已淘汰阶段

这个项目先后试过几条路线，但现在都不再作为主线：

### 1. 纯 Swift Package CLI

- 早期做过 `tools/listening-transcribe/` 这条 Swift Package 方案
- 问题不在转写质量，而在运行形态不适合承接 macOS Speech 授权
- 现在已经退役，不再保留为有效入口

### 2. 旧的本地 Whisper / faster-whisper 实验

- 试过 `faster-whisper tiny`
- 试过 `kotoba-whisper-v2.2-faster`
- 也试过官方 `kotoba-whisper-v2.2`

这些路线的问题已经明确：

- 短音频可以出草稿，但长文稳定性不够
- 解释成本高，参数很多
- 还会留下模型、环境和提示词上的历史包袱

因此当前 vault 不再维护自己的 Whisper/faster-whisper helper。需要通用 ASR 能力时，统一更新 sibling `../ListenKit`。

## 为什么把底层 ASR 迁到 ListenKit

Apple Speech 这条路线已经在 `cz15`、`cz16`、`cz18` 上验证过：

- 本机本地执行
- 不依赖外部云服务
- 长文覆盖率明显好于之前的 Whisper 试验
- 输出可直接接回现有精听稿 Markdown 模板

Shadowing 教材短对话则更适合 `faster-whisper small`。两类 ASR 都属于通用能力，因此迁到 ListenKit；本 vault 只保留日语学习笔记的渲染、排版和后处理。

## 后续维护原则

- 不再新增 vault-local Apple Speech / Whisper / kotoba / faster-whisper helper
- skill 提示词只描述如何调用 ListenKit 和如何生成日语精听稿
- 如果没有现成 `_无文本待补.md`，允许直接新建主题化笔记
- 默认不要把 `## 字幕（带时间）` 写入成品精听稿
- 需要字幕时单独走 helper JSON，而不是污染最终笔记
