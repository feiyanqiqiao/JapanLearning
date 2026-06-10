# 如何为 LingoTrace 添加新语种支持

LingoTrace 采用 **”一门语言一个 Vault (One Vault Per Language)”** 的底层架构。

这就意味着，框架内部的流转机制（如间隔重复衰减、知识图谱构建、关联防重等）是完全跨语种通用的。但由于每门外语在发音体系、词汇特有属性上存在巨大差异，如果你希望在 LingoTrace 的骨架上开展一门全新外语（例如法语、西班牙语、德语）的学习，你需要针对性地完成以下”换壳”配置工作。

你**不需要**去修改底层的 Python 调度代码或 Agent 的主线任务逻辑，只需要在你的 Vault 中完成以下配置维度的定义：

**核心模块**（必须）：
- `tools/config_loader.py` — 统一配置加载器
- `tools/vocab_note.py` — 统一词汇卡 frontmatter 操作
- `tools/vocab_ops.py` — 语言无关的词汇卡操作

---

## 1. 定义语言档案 (config.json)

你需要在目标 Vault 的 `系统配置/config.json` 中，按需修改并确立该语言的专属元数据上下文：

```json
{
  "language_profile": {
    "name": "French",
    "tag_namespace": "fr",
    "listenkit_locale": "fr-FR",
    "listenkit_language": "French",
    "pronunciation_system": "ipa",
    "speaking_text_field": "fr_text"
  },
  "features": {
    "offline_dictionary": false,
    "accent_audit": false
  },
  "template_root": "系统配置/模板"
}
```

- `tag_namespace`：系统的灵魂标识。底层的脚本会自动抓取该字段，将所有的复习网络打上 `fr/vocab`、`fr/grammar` 的标签。
- `listenkit_locale` & `listenkit_language`：传递给底层语音识别组件的参数（需符合 Whisper / API 引擎的语种名拼写规范）。
- `speaking_text_field`：口语练习卡片中，代表目标语言句子文本的专属字段名。
- `features`：决定是否启用特定的扩展行为（例如是否依赖本地离线词典处理复杂发音）。

---

## 2. 建立统一元数据 (Unified Frontmatter) 的骨架

LingoTrace 采用**元数据字段统一化**的设计。这意味着你不需要（也不应该）为了特定的语言去创造新的专属字段名（例如不应该为了法语去新增 `gender` 或 `ipa` 字段）。所有的语言特性都会被抽象收敛到核心的通用多态字段中：

- `pronunciation`：存储这门语言的发音信息（如法语的 `/bɔ̃.ʒuʁ/`，日语的 `すもう⓪`，英语的 `/ˈsuːməʊ/`）。
- `variants`：存储这门语言的书写变体或查缺补漏信息（如英美的拼写差异 `color/colour`，日语的汉字差分 `戸/户`）。

请在 `系统配置/模板/<tag_namespace>/` 目录下（例如 `系统配置/模板/fr/`），准备好对应的学习卡片模板。以**法语**单词卡为例：

```markdown
---
track: class_review
item_type: vocab
headword: {{word}}
pronunciation: ""    # 法语国际音标
meaning_zh: ""
pos: ""              # 词性 (及阴阳性标记)
variants: []         # 书写变体信息
confusable_with: []
status: active
next_review: ""
done_today: false
source: ""
tags:
  - fr/vocab
---
```
将这份结构命名为 `单词卡模板.md`，Agent 启动后就会自动加载这一套专属骨架，填入符合特性的大语言模型生成内容。

---

## 3. 定制化 Agent 提示词 (可选)

LingoTrace 核心的 `agent-skills` 已经高度泛化，能够通过模板指引自动进行属性填充。

但如果你发现由于大语言模型（LLM）的固有特性，导致在处理某种特定语言时频繁出现某种“语病”或者“归类错误”（比如未能准确处理法语特有的连诵 liaison 规则），你可以打开对应的技能目录（例如 `agent-skills/source-note-generator/SKILL.md`），在提示词的最下方追加该语言专属的 **Language Specific Constraints**，约束大模型的输出行为。

---

## 4. 本地辅助工具与离线词典 (可选)

你可能会注意到原始框架的 `tools/` 下包含 `setup_offline_dictionary.py` 这样的脚本，这是为了解决**日语独有的分词与声调（Pitch Accent）标注**问题，而引入了 `fugashi` 和 `unidic-lite` 等本地 NLP 依赖。

这种本地依赖**并不是 LingoTrace 核心运转的必选项**。
- 如果你新增的语言（如英语、西班牙语）可以直接依靠大模型准确生成音标和发音特性，你只需在 `config.json` 中配置 `"offline_dictionary": false`，系统完全**不需要**配置离线词典。
- 如果你觉得大语言模型经常搞错某些单词的重音，或者你需要极高精度的离线发音库（比如英语的 `cmudict`），你可以仿照原始的日语词典脚本，在 `tools/` 目录下编写特定语言的辅助脚本提供给 Agent 使用。

**总结**：在 LingoTrace 中添加新语种支持，本质就是 **配置定属性，模板定骨架**，如果大模型不够聪明，再辅以 **本地脚本挂词典**。完成这些配置，LingoTrace 将瞬间转变为你专属的最强外语学习引擎。
