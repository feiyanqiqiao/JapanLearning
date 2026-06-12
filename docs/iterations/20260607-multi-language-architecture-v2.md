# 多语种支持架构演进方案 (V2)

LingoTrace 最初作为一个专用的日语学习工作流框架被构建。随着开源社区的演进，我们计划将其打造成一个通用的多语种学习引擎（如英语、法语等）。本方案定义了如何将底层框架与日语特性进行解耦的系统级重构架构。

## 一、 核心架构决策：One Vault Per Language
根据设计讨论，我们确定采用 **“一门语言一个 Vault (One Vault Per Language)”** 的架构理念。
学习不同语种在心智上是高度独立的任务，保持独立的 Vault 可以让个人的知识图谱、关联搜索和 Obsidian 工作区更加纯粹、干净，同时大幅降低系统底层的路由判别复杂度。

---

## 二、 现存的硬编码痛点 (Audit Findings)

在将系统泛化之前，必须清扫以下深层耦合的日语专属逻辑：
1. **Python 工具链写死标签**：`update_next_day_review.py`、`transcribe_listening.py`、`migrate_vault_layout.py` 中写死了 `jp/vocab`、`jp/listening` 等分类标签。
2. **专属属性的刚性校验**：Agent 提示词 (SKILL.md) 强制校验 `reading`（假名读音）、`accent_display`（音调）、`kanji_diff`（汉字辨析）等仅限日语的元数据。
3. **前端仪表板 (Bases) 的逻辑锁死**：`学习系统/总训练.base` 的 `core_text` 与 `support_text` 展示公式完全依赖上述日语字段，甚至硬编码了日语的视图名称（如 `アクセント待练`）。
4. **校验脚本与专属插件**：`validate-survival-speaking-cards.sh` 写死校验 `jp_text` 字段；`setup_offline_dictionary.py` 和 `apply-accent-confirmations.py` 等强依赖日语分词库的脚本未被隔离。
5. **外部转写硬编码**：调用 ListenKit 时直接写死 `--language Japanese`。
6. **Shell 脚本锚点硬编码**：`run-listening-transcribe.sh`、`prepare-source-note-material.sh` 等脚本内包含目录结构的硬编码。
7. **命名空间局限**：根目录 `codex-skills` 固化了 AI 平台，子目录名 `jp-*` 固化了语种，甚至 `openai.yaml` 中也写死了。

---

## 三、 深度重构设计 (Proposed Architecture)

为彻底解决上述痛点，我们提出以下三项核心设计解耦策略：

### 1. 配置文件双轨制 (分离语言身份与路径角色)
将与语言特征相关的配置与传统的路径定义相隔离，避免引入系统性风险。
- **`系统配置/paths.json`**：专职负责 Vault 结构和目录路径的映射，不受语种影响。
- **`系统配置/config.json`**：(新增) 定义该 Vault 的语言灵魂。
  ```json
  {
    "language_profile": {
      "name": "English",
      "tag_namespace": "en",
      "listenkit_locale": "en-US",
      "listenkit_language": "English",
      "pronunciation_system": "ipa",
      "speaking_text_field": "en_text"
    },
    "features": {
      "offline_dictionary": false,
      "accent_audit": false,
      "kanji_diff_support": false
    },
    "template_root": "系统配置/模板"
  }
  ```

### 2. 元数据字段统一化 (Unified Frontmatter)
不再为不同的语言创造特定的字段，而是使用抽象的多态字段名。
所有外语的词汇卡 (vocab) Frontmatter 将严格统一收敛为：

| 字段 | 类型 | 说明 | 日语示例 | 英语示例 |
|---|---|---|---|---|
| `track` | string | 所属轨道 | `class_review` | `class_review` |
| `item_type` | string | 卡片类型 | `vocab` | `vocab` |
| `headword` | string | 词头 | `相撲` | `sumo` |
| `pronunciation` | string | **发音（统一旧的 reading 与 accent）** | `すもう⓪` | `/ˈsuːməʊ/` |
| `meaning_zh` | string | 中文释义 | `摔跤（日本式）` | `相扑` |
| `pos` | string | 词性 | `名词` | `noun` |
| `variants` | list | **变体（统一旧的 kanji_diff）** | `["戸/户"]` | `["sumō"]` |
| `confusable_with` | list | 易混词 | `[]` | `["summon"]` |

### 3. Agent 技能目录泛化
全面剔除原有受限的命名空间，使之完全匹配开源 Agent 框架的定位：
- `codex-skills/` 全面更名为 `agent-skills/`。
- 内部所有 `jp-*` 目录剔除前缀，变为泛用的 `source-note-generator` 等。

---

## 四、 分阶段执行计划

### Phase 1：配置层注入与专属插件剥离（零破坏）
- [ ] 创建 `系统配置/config.json`，定义双语示例（英语与日语）。
- [ ] `paths.json` 保持原样不动。
- [ ] 将 `setup_offline_dictionary.py` 和 `apply-accent-confirmations.py` 在脚本注释中显式标记为 **[JP-ONLY]** 专属插件，从核心链路解绑，并更新 `tools/README.md`。

### Phase 2：目录架构重命名与全局锚点同步
- [ ] 执行 `git mv codex-skills agent-skills` 并去除内部子目录的 `jp-` 前缀。
- [ ] 全局更新关联路径，覆盖 `.gitignore`、`check-public-staged-files.sh` 的 CI 白名单。
- [ ] 更新 Shell 脚本中的硬编码探测锚点：`run-next-day-review-update.sh`、`run-listening-transcribe.sh`、`prepare-source-note-material.sh`、`sync-to-global.sh`。
- [ ] 将 5 个 Agent 下的 `agents/openai.yaml` 重命名为 `agents/skill.yaml` 以消除对特定商业公司的厂商锁定（Vendor Lock-in），并同步修改 `sync-to-global.sh` 的复制路径与 `default_prompt` 中的引用。
- [ ] 更新所有 README 和 AGENTS.md。

### Phase 3：Python 核心引擎解耦
- [ ] 新增 `tools/config_loader.py`，供所有脚本当作统一入口读取 `config.json`。
- [ ] 改造 `update_next_day_review.py`：动态拼接标签前缀（如 `f"{namespace}/vocab"`），并将对 `reading/accent_display/kanji_diff` 的读取改为读 `pronunciation` 和 `variants`。
- [ ] 改造 `transcribe_listening.py`：动态读取区域设置，仅当配置声明需要离线词典时加载 `setup_offline_dictionary.py` 相关逻辑。

### Phase 4：前端交互展现层适配
- [ ] 改造 `validate-survival-speaking-cards.sh` 内嵌脚本，根据配置读取 `{ns}_text` 字段进行判错。
- [ ] 改造 `学习系统/总训练.base`：
  - 将所有合并取值逻辑（`core_text` 和 `support_text`）简化为直接读取 `pronunciation` 字段。
  - 将视图名称本地化或去日语化（如 `アクセント待练` -> `Pronunciation Review`）。

### Phase 5：模板生态泛化与 Agent 提示词清洗
- [ ] 在 `系统配置/模板/` 目录下隔离 `jp/` 与 `en/` 双轨制模板。
- [ ] 采用统一的 `pronunciation` 和 `variants` 字段，设计一份全新、完美的英语单词模板。
- [ ] 清除所有 `SKILL.md` 中关于日语读音与声调的硬要求，增设前置指令：“读取 config.json 判定语种上下文，使用对应的模板进行自动制卡”。

---

## 五、 测试与验证策略 (Verification Plan)
1. **向后兼容性验证**：修改原有的 `test_update_next_day_review.py` 等测试用例，确保 `pronunciation`/`variants` 的映射能跑通原有的卡片流转逻辑。
2. **多语言配置加载测试**：新增 `test_config_loader.py` 专门验证针对不同语言环境 `config.json` 的解析与 fallback。
3. **引入 CI 冒烟测试**：在 `.github/workflows/` 新增 `multi-language-smoke.yml`，执行所有测试，确保无论是日语还是英语逻辑都不会发生退化。
4. **英语端到端 Dry Run**：向系统中输入英语测试素材，调用更新后的 Agent 技能，人工核验产出的 Markdown 笔记是否挂载了 `en/vocab` 且严格遵循了英文 Frontmatter 模板。
