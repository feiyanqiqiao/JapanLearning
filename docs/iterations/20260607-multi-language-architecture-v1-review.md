# 评审报告：多语种支持架构演进方案

- **评审对象**：`docs/iterations/20260607-multi-language-architecture.md`
- **评审日期**：2026-06-07
- **评审结论**：⚠️ **有条件通过** — 方向正确，但存在多处关键遗漏和设计缺陷，需修订后方可进入实施阶段

---

## 一、总体评价

方案抓住了"一门语言一个 Vault"这一核心架构决策，审计发现（Audit Findings）覆盖了主要的硬编码耦合点。但在**完整性、执行安全性、向后兼容性**三个维度上存在显著不足。以下逐一展开。

---

## 二、严重问题（P0 — 阻塞实施）

### 2.1 遗漏：`总训练.base` 的日语硬编码未被审计

方案审计了 Python 脚本、SKILL.md、paths.json、模板，但**完全遗漏了 `学习系统/总训练.base`**。该文件包含：

- 9 个视图名称中 2 个直接使用日语（`アクセント待练`、`音素待练`）
- `core_text` 公式硬编码了 `item_type == "vocab"` 时取 `reading` 字段，`item_type == "grammar"` 时取 `pattern` + `formation` — 这些是日语 frontmatter 的特有字段
- `support_text` 公式硬编码了 `accent_display` 字段

**影响**：即使所有其他文件都解耦完成，Obsidian 仪表板在英语 Vault 中依然会崩溃——`reading` 和 `accent_display` 字段不存在，公式返回空值，视图名称对英语学习者无意义。

**建议**：将 `总训练.base` 的泛化纳入方案第 1 步或第 3 步，明确 `core_text` / `support_text` 公式需根据 `config.json` 中的 `pronunciation_system` 动态选择字段。

### 2.2 遗漏：`validate-survival-speaking-cards.sh` 中的日语硬编码

该脚本内嵌的 Python 校验器硬编码了 `jp_text` 字段检查（第 88 行附近：`duplicate jp_text`）。方案未提及此脚本的解耦。

**影响**：英语 Vault 中的 speaking card 使用 `en_text`（或其他命名），校验器会误报所有卡片缺少 `jp_text`。

**建议**：在方案第 5 节 Python 工具链动态化中补充此脚本，或将字段名校验改为从 `config.json` 读取。

### 2.3 遗漏：`apply-accent-confirmations.py` 的归属与泛化

方案第 5 节提到了 `setup_offline_dictionary.py` 的剥离，但**未提及 `apply-accent-confirmations.py`**。该脚本（149 行）硬编码了：

- `nhk_status` 字段（NHK 日语发音词典特有概念）
- `accent_display` 字段写入逻辑
- CSV 列名 `reading`、`accent_display`

**影响**：该脚本对英语 Vault 完全无用，但如果不明确标记为日语专属插件，新用户可能困惑。

**建议**：与 `setup_offline_dictionary.py` 一同标记为日语专属插件，从核心工具链剥离。英语的音标标注可由 LLM 直接完成（如方案所述），但需在文档中显式说明。

### 2.4 配置文件设计缺陷：`paths.json` → `config.json` 的迁移路径缺失

方案提出将 `paths.json` 升级为 `config.json`，但**未说明**：

1. 现有 `paths.json` 中的 17 个 `roles` 和 7 个 `managed_review_roots` 如何迁移？
2. 所有消费 `paths.json` 的代码（`update_next_day_review.py` 的 `--paths-config` 参数、`transcribe_listening.py` 的路径解析、`validate_vault_structure.py` 的校验逻辑）如何适配？
3. 是保留 `paths.json` + 新增 `config.json`（两个文件并存），还是合并为一个？

**影响**：这是全局性的接口变更，如果设计不清，会导致所有 Python 脚本和 Shell 脚本的路径解析全部失败。

**建议**：明确采用**分离方案**（`config.json` 管语言配置，`paths.json` 管路径角色），还是**合并方案**（`config.json` 包含 `language_profile` + `roles`）。推荐分离方案，因为路径角色与语言无关，合并会引入不必要的耦合。

---

## 三、重要问题（P1 — 影响方案质量）

### 3.1 审计遗漏：Shell 脚本中的路径硬编码

方案审计了 Python 脚本的硬编码，但**遗漏了 Shell 脚本**中的路径耦合：

- `run-listening-transcribe.sh` 硬编码了 `学习系统/听力` 作为 vault root 探测锚点
- `run-next-day-review-update.sh` 硬编码了 `学习系统` 和 `codex-skills` 作为探测锚点
- `prepare-source-note-material.sh` 内部路径引用未被审查
- `check-public-staged-files.sh` 的 allowlist 中硬编码了 `codex-skills/` 目录名

**建议**：补充 Shell 脚本的审计项。特别是 `codex-skills/` → `agent-skills/` 的重命名会直接导致 `run-next-day-review-update.sh` 的 vault root 探测失败，以及 CI 的 `check-public-staged-files.sh` allowlist 失效。

### 3.2 审计遗漏：`sync-to-global.sh` × 5 的路径影响

每个 skill 目录下的 `sync-to-global.sh` 将文件复制到 `~/.codex/skills/<skill-name>/`。方案提出重命名 `codex-skills/` → `agent-skills/`，但未说明：

1. 目标路径 `~/.codex/skills/` 是否也需要改为 `~/.agent/skills/` 或其他名称？
2. `openai.yaml` 中的 `default_prompt` 引用（如 `$jp-listening-script-generator`）是否需要同步更新？
3. 5 个 `sync-to-global.sh` 脚本是否需要全部重写？

**建议**：明确 `sync-to-global.sh` 的更新范围，并考虑是否将 `~/.codex/` 这一平台绑定路径也泛化。

### 3.3 方案第 2 节 `config.json` 设计过于简略

当前给出的 `config.json` 示例只有 4 个字段：

```json
{
  "language_profile": {
    "name": "English",
    "tag_namespace": "en",
    "listenkit_lang": "English",
    "pronunciation_system": "ipa"
  }
}
```

但实际需要配置的内容远不止这些：

| 缺失的配置项 | 影响 |
|---|---|
| `frontmatter_fields`（语言专属字段列表） | Agent 无法知道英语卡片需要 `ipa`、`pos` 而非 `reading`、`accent_display` |
| `offline_dictionary`（是否需要离线词典及类型） | 无法判断是否调用 `setup_offline_dictionary.py` |
| `template_root`（模板子目录名） | 方案提到 `<template_root>/<tag_namespace>/` 但未定义 `template_root` 的来源 |
| `validation_rules`（语言专属校验规则） | `validate-survival-speaking-cards.sh` 需要知道校验哪些字段 |

**建议**：扩展 `config.json` 的 schema 定义，至少覆盖上述 4 项。可以参考项目已有的 `lingotrace_multilingual_multiagent_design.md` 中的 frontmatter schema 抽象设计。

### 3.4 缺少迁移（Migration）策略

方案描述了"目标状态"，但**完全未提及如何从当前状态迁移到目标状态**：

1. 已有的日语 Vault 用户（即你自己）如何平滑过渡？
2. `codex-skills/` → `agent-skills/` 的重命名是否需要像 `migrate_vault_layout.py` 那样的分阶段迁移脚本？
3. 现有的 `paths.json` 用户配置是否需要自动迁移？
4. 是否需要向后兼容（即新框架能否直接读取旧格式的 Vault）？

**建议**：增加一节"迁移计划"，明确是否需要迁移脚本、是否支持旧格式、迁移的回滚策略。

### 3.5 测试计划缺失

方案未提及任何测试策略。当前项目有 47 个单元测试（5 + 27 + 9 + 6），覆盖了核心 Python 脚本。重构后：

1. 现有测试是否全部需要重写？
2. 是否需要新增"英语 Vault"的集成测试？
3. `config.json` 的解析是否需要单独的单元测试？

**建议**：在方案中增加测试策略节，至少说明：现有测试的适配范围、新增测试的优先级、是否引入 CI 中的多语言 smoke test。

---

## 四、一般问题（P2 — 建议改进）

### 4.1 `jp-survival-speaking-card-generator` 的泛化路径不清晰

方案第 1 节提出将 `jp-*` 前缀抹除，但 `survival-speaking-card-generator` 这个 skill 的 SKILL.md 中深度嵌入了日语场景分类（`日常生活`、`レストラン` 等）、`jp_text` 字段名、日语例句格式。仅改目录名远远不够，SKILL.md 的内容也需要重写。

**建议**：在方案中明确，目录重命名只是第一步，每个 SKILL.md 的内容泛化是独立的工作包，需要逐一评估。

### 4.2 `listenkit_lang` 配置的边界未定义

方案假设 ListenKit 支持 `--language English`，但未验证：

1. ListenKit 当前是否真的支持英语？
2. 如果 ListenKit 不支持，整个英语听力流程是否阻塞？
3. `listenkit_lang` 的可选值列表是什么？

**建议**：在方案中标注 ListenKit 英语支持的验证状态，如果尚未验证，将其列为前置依赖（blocker）。

### 4.3 英语单词卡设计变更过于粗略

方案第 3 节提出的英语单词卡字段变更：

- 移除：`reading`、`accent_display`、`kanji_diff`
- 引入：`ipa`、`pos`、`spelling_diff` / `confusable_with`

但未说明：

1. `pos`（词性）的取值规范是什么？是 Penn Treebank tagset 还是简化标签？
2. `spelling_diff` 与 `confusable_with` 的语义边界？日语中 `kanji_diff` 是一个字段，英语是否需要两个？
3. 英语是否需要 `collocation`（搭配）字段？日语模板中有 `常用搭配与例句` 节，英语是否保留？
4. `track` 字段的取值是否变化？日语的 `class_review`、`survival_speaking`、`listening`、`pronunciation` 是否全部适用于英语？

**建议**：补充完整的英语 frontmatter schema 定义，至少达到日语 `单词卡模板.md` 的详细程度。

### 4.4 文档内部一致性问题

方案标题用中文（"多语种支持架构演进方案"），但第 2-5 节标题突然切换为英文（"Proposed Changes"）。中英文混用降低了可读性。

**建议**：统一为中文，或至少在每个英文标题后附中文翻译。

---

## 五、方案亮点

1. **"一门语言一个 Vault"的架构决策是正确的**。它避免了多语言混合 Vault 带来的标签冲突、模板混乱、Bases 公式爆炸等复杂度，符合 Obsidian 的单库单心智模型。
2. **审计发现覆盖了最关键的耦合点**：Python 脚本、SKILL.md、paths.json、ListenKit 调用。这些确实是重构的核心战场。
3. **`setup_offline_dictionary.py` 的剥离决策合理**。日语离线词典（fugashi/unidic-lite）是重依赖，英语用 LLM 标注音标是更轻量的方案。
4. **以英语为试点的渐进策略**。先做一门新语言验证框架泛化能力，再推广到其他语种，降低了风险。

---

## 六、修订建议清单

| 优先级 | 编号 | 建议 |
|---|---|---|
| P0 | #1 | 将 `总训练.base` 的泛化纳入审计和执行方案 |
| P0 | #2 | 补充 `validate-survival-speaking-cards.sh` 的解耦方案 |
| P0 | #3 | 明确 `apply-accent-confirmations.py` 的归属（日语专属插件） |
| P0 | #4 | 明确 `config.json` 与 `paths.json` 的关系（分离 vs 合并） |
| P1 | #5 | 补充 Shell 脚本的硬编码审计（特别是 `codex-skills/` 探测锚点） |
| P1 | #6 | 明确 `sync-to-global.sh` 的更新范围 |
| P1 | #7 | 扩展 `config.json` 的 schema 定义 |
| P1 | #8 | 增加迁移策略节 |
| P1 | #9 | 增加测试策略节 |
| P2 | #10 | 明确 SKILL.md 内容泛化是独立工作包 |
| P2 | #11 | 验证 ListenKit 英语支持状态 |
| P2 | #12 | 补充完整的英语 frontmatter schema |
| P2 | #13 | 统一文档语言风格 |

---

## 七、结论

方案的架构方向正确，审计发现了真实存在的耦合问题。但在**配置文件迁移路径、Shell 脚本覆盖、测试策略、英语 frontmatter schema 完整性**四个方面存在显著空白。建议按 P0 → P1 → P2 的优先级修订后，再进入实施阶段。

预计修订工作量：**2-3 小时**（主要是补充设计细节，不涉及架构方向调整）。

---

## 八、替代实施方案（评审方补充）

> 以下方案基于对代码库的完整依赖分析（`paths.json` 的 18 个消费点、5 个日语专属字段在 17 个文件中的足迹、ListenKit 的多语言能力验证）设计，旨在填补原方案的所有空白。

### 8.1 核心设计决策

#### 决策 1：双文件分离 — `config.json` ∥ `paths.json`

采用**分离方案**，两个文件职责正交：

| 文件 | 职责 | 变更频率 |
|---|---|---|
| `系统配置/paths.json` | Vault 目录结构的路径角色（17 个 roles + managed_review_roots + base_vocab_root + daily_notes_root） | 低频（目录结构调整时） |
| `系统配置/config.json` | 语言身份、标签体系、模板选择、ListenKit 参数、离线词典配置 | 仅在初始化新语言 Vault 时设置一次 |

**理由**：
- `paths.json` 的 18 个消费点（4 个运行时 Python/Shell、5 个 SKILL.md 策略文件、3 个测试）全部只读取路径角色，与语言无关。改动它们是纯粹的无意义风险。
- `config.json` 是纯新增文件，零破坏性。
- 两个文件的变更生命周期完全不同：路径角色在 Vault 演化时变，语言配置在初始化时定。

#### 决策 2：字段统一化 — 用 `pronunciation` / `variants` 替代日语特有字段名

原方案提出"英语引入 `ipa`、`pos`、`spelling_diff`"，这会导致**字段名随语言分裂**，每新增一门语言就要改一遍所有脚本的字段名映射。

**替代方案**：统一字段名，让内容随语言变化：

| 统一字段名 | 日语内容 | 英语内容 | 替代的旧字段 |
|---|---|---|---|
| `pronunciation` | `すもう⓪`（假名 + 音调标记） | `/ˈsuːməʊ/`（IPA） | `reading` + `accent_display` 合并 |
| `variants` | `戸/户`（汉字差分） | `color/colour`（拼写差异） | `kanji_diff` + `kanji_diff_pairs` 合并 |

**理由**：
- Python 脚本（`update_next_day_review.py`、`transcribe_listening.py`）只需改一次字段名，之后对所有语言通用。
- `总训练.base` 的 `core_text` / `support_text` 公式只需改一次，不再需要语言条件分支。
- `pos`（词性）、`confusable_with`（易混词）等字段在日语和英语中都有意义，保持原名不变。
- `target_text` 作为 `jp_text` 的统一替代名（用于 speaking cards）。

#### 决策 3：`{tag_namespace}_text` 保留语言前缀

speaking card 的核心文本字段采用 `{ns}_text` 命名（日语 `jp_text`、英语 `en_text`），而非统一为 `target_text`。

**理由**：`总训练.base` 的 `core_text` 公式已用 `if(jp_text, jp_text, ...)` 做分发，保留前缀命名让公式语义清晰，且与标签体系 `jp/vocab` → `en/vocab` 的命名范式一致。校验器从 `config.json` 读取 `tag_namespace` 后动态构造字段名即可。

### 8.2 `config.json` 完整 Schema 定义

```jsonc
{
  "language_profile": {
    "name": "English",                    // 人类可读语言名
    "tag_namespace": "en",                // 标签前缀：en/vocab, en/grammar, ...
    "listenkit_locale": "en-US",          // ListenKit --locale 参数
    "listenkit_language": "English",      // ListenKit --language 参数（Whisper 规范）
    "pronunciation_system": "ipa",        // 发音标注体系：ipa | kana_pitch | pinyin
    "speaking_text_field": "en_text"      // speaking card 核心文本字段名
  },
  "features": {
    "offline_dictionary": false,          // 是否需要离线词典（日语 true，英语 false）
    "accent_audit": false,                // 是否需要 NHK 式音调审计流程
    "kanji_diff_support": false           // 是否支持汉字差分卡片
  },
  "template_root": "系统配置/模板"        // 模板目录根路径（相对于 Vault 根）
}
```

**关键设计说明**：
- `listenkit_locale` 和 `listenkit_language` 分离：前者控制 ASR 语音模型选择（如 `en-US` vs `en-GB`），后者是传给 ListenKit 的语言标签。
- `features` 布尔开关控制可选功能模块的启用，避免在脚本中硬编码"日语才有的功能"。
- `template_root` 指向模板目录根，脚本通过 `<template_root>/<tag_namespace>/` 定位语言专属模板。
- `speaking_text_field` 显式声明 speaking card 的核心文本字段名，校验器直接读取此值。

**日语 Vault 的 `config.json` 示例**：

```jsonc
{
  "language_profile": {
    "name": "日本語",
    "tag_namespace": "jp",
    "listenkit_locale": "ja-JP",
    "listenkit_language": "Japanese",
    "pronunciation_system": "kana_pitch",
    "speaking_text_field": "jp_text"
  },
  "features": {
    "offline_dictionary": true,
    "accent_audit": true,
    "kanji_diff_support": true
  },
  "template_root": "系统配置/模板"
}
```

### 8.3 Frontmatter Schema 统一定义

#### 词汇卡（vocab）— Focus Review + Base Lexicon 通用

| 字段 | 类型 | 必填 | 说明 | 日语示例 | 英语示例 |
|---|---|---|---|---|---|
| `track` | string | ✅ | 固定 `class_review` | `class_review` | `class_review` |
| `item_type` | string | ✅ | 固定 `vocab` | `vocab` | `vocab` |
| `headword` | string | ✅ | 词头（干净书写形式） | `相撲` | `sumo` |
| `pronunciation` | string | ✅ | 发音（体系由 config 决定） | `すもう⓪` | `/ˈsuːməʊ/` |
| `meaning_zh` | string | ✅ | 中文释义 | `摔跤（日本式）` | `相扑（日本式摔跤）` |
| `pos` | string | ✅ | 词性 | `名词` | `noun` |
| `variants` | list | ❌ | 变体/差异信息 | `["戸/户"]` | `["sumō"]` |
| `confusable_with` | list | ❌ | 易混词 | `[]` | `["summon"]` |
| `status` | string | ❌ | Focus 卡状态 | `active` | `active` |
| `next_review` | date | ❌ | 下次复习日期 | `2026-06-10` | `2026-06-10` |
| `done_today` | bool | ❌ | 今日是否完成 | `true` | `true` |
| `source` | string | ❌ | 来源笔记路径 | `笔记/课堂/2026-06-01` | `笔记/课堂/2026-06-01` |

**关键变更说明**：
- `reading` + `accent_display` → 合并为 `pronunciation`。日语中音调标记已内嵌在假名中（`すもう⓪`），无需两个字段。
- `kanji_diff` + `kanji_diff_pairs` → 合并为 `variants`（YAML list）。布尔标志不再单独存在，list 非空即表示有变体。
- `pos` 从隐式（日语靠 `formation` 推断）变为显式必填，提升跨语言一致性。
- 以下字段**保持不变**：`track`、`item_type`、`headword`、`meaning_zh`、`status`、`next_review`、`done_today`、`source`。

#### 口语卡（survival_speaking）

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `track` | string | ✅ | 固定 `survival_speaking` |
| `item_type` | string | ✅ | 固定 `sentence` |
| `{ns}_text` | string | ✅ | 目标语言句子（`jp_text` / `en_text`） |
| `meaning_zh` | string | ✅ | 中文翻译 |
| `reply_hint` | string | ✅ | 回复提示 |
| `scene_category` | string | ✅ | 场景分类 |
| `speaker_role` | string | ❌ | 说话人角色 |

`{ns}_text` 的字段名由 `config.json` 的 `speaking_text_field` 决定。校验器、Bases 公式、SKILL.md 均从配置读取。

#### 语法卡（grammar）— 无变更

| 字段 | 说明 |
|---|---|
| `track` | `class_review` |
| `item_type` | `grammar` |
| `pattern` | 语法句型 |
| `meaning_zh` | 中文释义 |
| `formation` | 活用形（YAML list） |
| `contrast_with` | 对比语法 |

语法卡结构在日语和英语中高度相似，无需语言分化。

### 8.4 `总训练.base` 泛化方案

#### 字段名替换

| 旧引用 | 新引用 | 位置 |
|---|---|---|
| `accent_display` | `pronunciation` | `core_text` 公式 + property 声明 |
| `jp_text` | `{ns}_text`（动态） | `core_text` 公式 + property 声明 |
| `reading` | 已被 `pronunciation` 吸收 | 无需单独引用 |

#### `core_text` 公式改写

**旧公式**（日语硬编码）：
```
if(jp_text, jp_text, if(headword, if(accent_display, accent_display, headword), ...))
```

**新公式**（使用统一字段名）：
```
if(en_text, en_text, if(headword, if(pronunciation, pronunciation, headword), ...))
```

> 注：`en_text` 在日语 Vault 中替换为 `jp_text`。由于采用"一门语言一个 Vault"，每个 Vault 只需写死自己的 `{ns}_text` 字段名，不存在多语言混合问题。

#### `support_text` 公式改写

**旧**：`if(accent_display, accent_display + " · " + meaning_zh, meaning_zh)`
**新**：`if(pronunciation, pronunciation + " · " + meaning_zh, meaning_zh)`

#### 视图名称本地化

| 旧名称 | 日语 Vault | 英语 Vault |
|---|---|---|
| `アクセント待练` | 保持不变 | `Pronunciation Review` |
| `音素待练` | 保持不变 | `Phoneme Review` |

视图名是纯展示文本，每个 Vault 的 `.base` 文件独立维护，不影响框架逻辑。

### 8.5 ListenKit 多语言能力验证结论

通过代码审计确认：

1. **`language_label_for_locale()`**（`transcribe_listening.py:328-338`）已显式支持 4 种语言映射：`ja→Japanese`、`en→English`、`zh→Chinese`、`ko→Korean`。
2. **`--locale` 参数**（`transcribe_listening.py:276`）默认 `ja-JP` 但可通过 CLI 覆盖。
3. **`--language` 参数**（`prepare-source-note-material.sh:74-77`）默认 `Japanese` 但支持 `--language <label>` 覆盖。
4. **`HOWTO_ADD_NEW_LANGUAGE.md`** 明确声明 `listenkit_lang` "must comply with the underlying Whisper/engine language naming convention"，Whisper 原生支持 ~100 种语言。

**结论**：ListenKit 英语支持**已就绪**，无需额外开发。只需将 `config.json` 中的 `listenkit_locale` 设为 `en-US`、`listenkit_language` 设为 `English`，现有代码路径即可正确传递参数。

**唯一的测试缺口**：`test_transcribe_listening.py` 仅测试 `locale="ja-JP"` 场景。需补充英语 locale 的测试用例验证 `language_label_for_locale("en-US")` → `"English"` 的端到端传递。

### 8.6 分阶段执行计划

#### Phase 0：前置准备（无代码变更）

- [ ] 验证 ListenKit 英语 ASR 端到端可用性（手动测试一条英语音频）
- [ ] 在 `docs/HOWTO_ADD_NEW_LANGUAGE.md` 中补全 `config.json` 完整 schema
- [ ] 确认英语 frontmatter schema 细节（`pos` 取值规范、`variants` 格式）

**产出物**：确认文档 + ListenKit 验证报告
**预计耗时**：1 小时

#### Phase 1：配置层（纯新增，零破坏）

- [ ] 创建 `系统配置/config.json`（英语 Vault 示例 + 日语 Vault 示例）
- [ ] `paths.json` 完全不动
- [ ] 在 `AGENTS.md` 中新增策略声明："语言身份配置位于 `系统配置/config.json`"

**产出物**：2 个 config.json 文件 + AGENTS.md 更新
**变更文件**：3 个（新增 2 + 修改 1）
**预计耗时**：30 分钟

#### Phase 2：目录重命名 + 引用同步

- [ ] `codex-skills/` → `agent-skills/`（git mv）
- [ ] 子目录 `jp-*` 前缀抹除（git mv × 5）
- [ ] 同步更新以下文件中的旧路径引用：

| 文件 | 变更内容 |
|---|---|
| `.gitignore` | `codex-skills/` → `agent-skills/` |
| `tools/git/check-public-staged-files.sh` | allowlist 中的 `codex-skills/` → `agent-skills/` |
| `codex-skills/jp-next-day-review-updater/scripts/run-next-day-review-update.sh` | vault root 探测锚点 `codex-skills` → `agent-skills` |
| `README.md` | 目录结构说明 |
| `AGENTS.md` | skill 路径引用 |
| `docs/USER_GUIDE.md` | 目录结构说明 |
| `tools/README.md` | 脚本路径引用 |
| 5× `sync-to-global.sh` | 更新源路径（目标路径 `~/.codex/skills/` 暂不改，避免影响现有安装） |
| 5× `agents/openai.yaml` | `default_prompt` 中的路径引用（如有） |

**产出物**：重命名后的目录结构 + 全部引用同步
**变更文件**：约 15 个
**预计耗时**：1 小时

#### Phase 3：Python 脚本解耦（核心重构）

**3a. 新增 `config_loader.py` 共享模块**

在 `tools/` 下创建共享的配置加载模块：

```python
# tools/config_loader.py
"""Load language identity from 系统配置/config.json."""
import json
from pathlib import Path
from dataclasses import dataclass

@dataclass(frozen=True)
class LanguageConfig:
    name: str
    tag_namespace: str
    listenkit_locale: str
    listenkit_language: str
    pronunciation_system: str
    speaking_text_field: str
    offline_dictionary: bool
    accent_audit: bool
    kanji_diff_support: bool
    template_root: str

def load_language_config(vault_root: Path, config_path: str = "系统配置/config.json") -> LanguageConfig:
    path = vault_root / config_path
    if not path.is_file():
        raise RuntimeError(f"config.json not found at {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    profile = data["language_profile"]
    features = data.get("features", {})
    return LanguageConfig(
        name=profile["name"],
        tag_namespace=profile["tag_namespace"],
        listenkit_locale=profile.get("listenkit_locale", "ja-JP"),
        listenkit_language=profile.get("listenkit_language", "Japanese"),
        pronunciation_system=profile.get("pronunciation_system", "kana_pitch"),
        speaking_text_field=profile.get("speaking_text_field", "jp_text"),
        offline_dictionary=features.get("offline_dictionary", False),
        accent_audit=features.get("accent_audit", False),
        kanji_diff_support=features.get("kanji_diff_support", False),
        template_root=data.get("template_root", "系统配置/模板"),
    )
```

**3b. 修改 `update_next_day_review.py`**

| 变更点 | 旧代码 | 新代码 |
|---|---|---|
| 新增 CLI 参数 | — | `--config`（默认 `系统配置/config.json`） |
| `render_base_note()` 参数 | `reading`, `accent_display`, `kanji_diff` | `pronunciation`, `variants` |
| 前缀标签 | `jp/vocab` 硬编码 | `f"{config.tag_namespace}/vocab"` |
| `kanji_diff` 标签 | `jp/kanji_diff` 硬编码 | `f"{config.tag_namespace}/variant"`（当 variants 非空时） |
| `extract_label()` | `("headword", "pattern", "jp_text", "target_text")` | `("headword", "pattern", config.speaking_text_field, "target_text")` |
| Sink 逻辑 | 读 `reading` + `accent_display` + `kanji_diff` | 读 `pronunciation` + `variants` |

**3c. 修改 `transcribe_listening.py`**

| 变更点 | 旧代码 | 新代码 |
|---|---|---|
| `--locale` 默认值 | `ja-JP` 硬编码 | 从 `config.json` 读取 `listenkit_locale` |
| `language_label_for_locale()` | 保留（已有 4 语言映射），但默认值从配置取 | |
| `accent_display` 写入 | 写入 frontmatter `accent_display` | 写入 `pronunciation` |
| `reading` 读取 | 构建确认音调索引时读 `reading` | 读 `pronunciation`（解析音调标记部分） |
| 标签注入 | `jp/vocab`、`jp/listening` | `{ns}/vocab`、`{ns}/listening` |
| 离线词典 | 无条件加载 | 仅当 `config.offline_dictionary == true` 时加载 |

**3d. 修改 `validate-survival-speaking-cards.sh`**

内嵌 Python 校验器：
- 新增 `--config` 参数，读取 `config.json`
- `required_fields` 中的 `jp_text` → `config.speaking_text_field`
- 标签校验中的 `jp/survival_speaking` → `{ns}/survival_speaking`

**3e. 标记日语专属脚本**

- `setup_offline_dictionary.py`：文件头添加注释 `"""日语专属：离线词典（fugashi/unidic-lite）安装与验证。"""`
- `apply-accent-confirmations.py`：文件头添加注释 `"""日语专属：NHK 音调审计数据写入。"""`
- 两个脚本**不删除、不移动**，仅通过文档和注释明确其日语专属属性。
- `tools/README.md` 中为这两个脚本添加 `[JP-ONLY]` 标记。

**产出物**：config_loader.py + 4 个脚本修改 + 2 个脚本标注
**变更文件**：7 个（新增 1 + 修改 4 + 标注 2）
**预计耗时**：3 小时

#### Phase 4：SKILL.md + 模板 + Bases

**4a. SKILL.md 泛化**

为每个 SKILL.md 增加"配置感知"前置步骤：

```markdown
## Configuration Awareness
Before executing any action, read `系统配置/config.json` to obtain:
- `tag_namespace` — used for tag injection (e.g., `{ns}/vocab`)
- `speaking_text_field` — used for speaking card core text field name
- `template_root` — used to locate language-specific templates
```

逐个 SKILL.md 清理日语硬编码：

| SKILL.md | 需清理的硬编码 |
|---|---|
| `review-material-maintainer` | `reading`→`pronunciation`、`accent_display`→`pronunciation`、`kanji_diff`→`variants`、`jp/vocab`→`{ns}/vocab`、模板路径 |
| `next-day-review-updater` | `jp/vocab`→`{ns}/vocab`、`jp/kanji_diff`→`{ns}/variant` |
| `listening-script-generator` | `--locale ja-JP`→从配置读、`jp/listening`→`{ns}/listening`、离线词典条件化 |
| `source-note-generator` | `--language Japanese`→从配置读、模板路径 |
| `survival-speaking-card-generator` | `jp_text`→从配置读、`jp/survival_speaking`→`{ns}/survival_speaking` |

**4b. 模板目录重构**

```
系统配置/模板/
  录入模板索引.md          ← 保留（更新链接）
  每日学习清单模板.md      ← 保留（语言无关）
  复习流程.md              ← 保留（语言无关）
  jp/
    单词卡模板.md          ← 移动自上层，字段名更新（reading→pronunciation 等）
    课堂语法卡模板.md      ← 移动自上层
    课堂笔记模板.md        ← 移动自上层
    生活口语句子卡模板.md  ← 新增（从录入模板索引中拆出）
  en/
    单词卡模板.md          ← 新建（英语完整模板）
    课堂语法卡模板.md      ← 新建
    生活口语句子卡模板.md  ← 新建
```

**英语单词卡模板**（`系统配置/模板/en/单词卡模板.md`）关键内容：

```yaml
# 课堂重点词卡
track: class_review
item_type: vocab
headword: ""
pronunciation: ""        # IPA, e.g., /ˈwɔːtər/
pos: ""                  # noun, verb, adj, adv, ...
meaning_zh: ""
variants: []             # e.g., ["color/colour"]
confusable_with: []      # e.g., ["affect/effect"]
status: active
next_review: ""
done_today: false
source: ""
```

**4c. `总训练.base` 更新**

- `accent_display` → `pronunciation`（property 声明 + `core_text` 公式 + `support_text` 公式）
- `jp_text` → `en_text`（英语 Vault）/ 保持 `jp_text`（日语 Vault）
- property `displayName` 更新：`重音` → `发音`（日语 Vault 保持 `重音` 亦可）
- 日语视图名 `アクセント待练` → 英语 Vault 改为 `Pronunciation Review`

**产出物**：5 个 SKILL.md 更新 + 模板目录重构 + 总训练.base 更新
**变更文件**：约 12 个
**预计耗时**：2 小时

#### Phase 5：测试策略

**5a. 现有测试适配**

| 测试文件 | 适配内容 |
|---|---|
| `test_update_next_day_review.py` | 所有 `reading:` → `pronunciation:`、`kanji_diff:` → `variants:`、新增 `--config` 参数、创建临时 `config.json` fixture |
| `test_transcribe_listening.py` | `accent_display` → `pronunciation`、新增英语 locale 测试用例（`en-US` → `English`）、离线词典条件化测试 |
| `test_migrate_vault_layout.py` | 无变更（迁移工具与语言无关） |
| `test_validate_vault_structure.py` | 无变更（路径校验与语言无关） |

**5b. 新增测试**

| 新测试 | 覆盖内容 |
|---|---|
| `test_config_loader.py` | config.json 解析、缺失字段默认值、文件不存在异常 |
| `test_update_next_day_review_english.py` | 英语 Vault 的完整 SRS 流程：创建卡片 → sink → merge，使用 `pronunciation` / `variants` 字段 |
| `test_transcribe_listening_english.py` | 英语 locale 的 ListenKit 调用链验证（mock ListenKit） |
| `test_survival_speaking_validation_english.py` | 英语 speaking card 的 `en_text` 字段校验 |

**5c. CI 增强**

在 `.github/workflows/` 中新增 `multi-language-smoke.yml`：
- 触发条件：PR to main
- 内容：运行全部测试（`python -m pytest`），确保日语和英语场景均通过

**产出物**：3 个测试文件适配 + 4 个新测试 + 1 个 CI workflow
**变更文件**：约 8 个
**预计耗时**：2 小时

#### Phase 6：文档更新

- [ ] `docs/HOWTO_ADD_NEW_LANGUAGE.md`：更新为完整 config.json schema + 模板创建步骤 + 测试验证步骤
- [ ] `docs/USER_GUIDE.md`：更新目录结构说明、新增多语言 Vault 初始化指南
- [ ] `tools/README.md`：更新脚本路径、标注 `[JP-ONLY]` 脚本
- [ ] `CHANGELOG.md`：记录多语言架构重构
- [ ] `docs/lingotrace_multilingual_multiagent_design.md`：更新为已实现状态

**产出物**：5 个文档更新
**变更文件**：5 个
**预计耗时**：1 小时

### 8.7 变更影响矩阵

| Phase | 新增文件 | 修改文件 | 删除/移动文件 | 预计耗时 |
|---|---|---|---|---|
| 0 - 前置准备 | 0 | 1 | 0 | 1h |
| 1 - 配置层 | 2 | 1 | 0 | 0.5h |
| 2 - 目录重命名 | 0 | ~15 | 5 (git mv) | 1h |
| 3 - Python 解耦 | 1 | 4 | 0 | 3h |
| 4 - SKILL/模板/Bases | ~5 | ~12 | ~3 (模板移动) | 2h |
| 5 - 测试 | ~4 | ~3 | 0 | 2h |
| 6 - 文档 | 0 | 5 | 0 | 1h |
| **合计** | **~12** | **~41** | **~8** | **10.5h** |

### 8.8 回滚策略

由于采用"纯新增 + 渐进修改"策略，每个 Phase 独立可回滚：

- **Phase 1**（config.json）：删除新增文件即可回滚，零影响。
- **Phase 2**（目录重命名）：`git revert` 该 commit 即可恢复目录名和所有引用。
- **Phase 3**（Python 解耦）：每个脚本的修改独立 commit，可逐一 revert。
- **Phase 4**（SKILL/模板）：模板移动可用 `git revert`，SKILL.md 修改可逐一 revert。
- **Phase 5**（测试）：纯新增测试，revert 无副作用。

**关键原则**：每个 Phase 合并为一个独立 PR，确保 `main` 分支在任何时刻都处于可工作状态。

### 8.9 与原方案的差异对照

| 维度 | 原方案 | 本方案 | 选择理由 |
|---|---|---|---|
| config.json 与 paths.json | "升级为 config.json"（含义模糊） | 双文件分离，职责正交 | paths.json 的 18 个消费点无需改动 |
| 字段命名策略 | 英语引入 `ipa`/`pos`/`spelling_diff` | 统一为 `pronunciation`/`variants` | 避免每增一门语言改一遍脚本 |
| 总训练.base | 未提及 | 独立 Phase 处理 | 遗漏会导致仪表板崩溃 |
| Shell 脚本 | 未审计 | Phase 2 完整覆盖 | `codex-skills` 探测锚点会断裂 |
| 日语专属脚本 | 提到 setup_offline_dictionary | 补充 apply-accent-confirmations | 两个脚本都只对日语有意义 |
| 迁移策略 | 无 | Phase 独立 + git revert | 保证 main 始终可工作 |
| 测试策略 | 无 | 4 个新测试 + 3 个适配 + CI | 47 个现有测试不能白跑 |
| ListenKit 验证 | 未验证 | Phase 0 前置验证 | 代码已有 4 语言映射，但缺实测 |
| 执行耗时估算 | 无 | 10.5 小时 / 7 个 Phase | 每个 Phase 独立可交付 |
