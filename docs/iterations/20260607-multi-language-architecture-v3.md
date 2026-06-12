# 多语种支持架构演进方案 (V3 最终版)

LingoTrace 最初作为一个专用的日语学习工作流框架被构建。随着开源社区的演进，我们计划将其打造成一个通用的多语种学习引擎（如英语、法语等）。本方案定义了如何将底层框架与日语特性进行解耦的系统级重构架构。

## 一、 核心架构决策：One Vault Per Language
根据设计讨论，我们确定采用 **“一门语言一个 Vault (One Vault Per Language)”** 的架构理念。
学习不同语种在心智上高度独立，保持独立的 Vault 可以让知识图谱、关联搜索和 Obsidian 工作区更加纯粹、干净，同时大幅降低系统底层的路由判别复杂度。

---

## 二、 现存的硬编码痛点 (Audit Findings)

在将系统泛化之前，必须清扫以下深层耦合的日语专属逻辑：
1. **Python 工具链写死标签**：`update_next_day_review.py`、`transcribe_listening.py`、`migrate_vault_layout.py` 中写死了 `jp/vocab`、`jp/listening` 等分类标签。
2. **专属属性的刚性校验**：Agent 提示词强制校验 `reading`（假名）、`accent_display`（音调）、`kanji_diff`（汉字辨析）等仅限日语的元数据。
3. **前端仪表板 (Bases) 的逻辑锁死**：`总训练.base` 的 `core_text` 公式硬编码了 `reading`、`accent_display`、`jp_text` 及日语视图名。
4. **校验脚本与专属插件**：`validate-survival-speaking-cards.sh` 写死校验 `jp_text`；`setup_offline_dictionary.py` 强依赖日语分词库。
5. **外部转写硬编码**：ListenKit 调用写死 `--language Japanese` 及 Shell 脚本路径写死锚点。
6. **命名空间局限与厂商锁定**：根目录 `codex-skills` 及 Agent 配置 `openai.yaml` 绑定了特定的平台。

---

## 三、 深度重构设计 (Proposed Architecture)

### 1. 配置文件双轨制 (分离语言身份与路径角色)
- **`系统配置/paths.json`**：专职负责 Vault 结构映射，不干涉语种。
- **`系统配置/config.json`**：(新增) 定义该 Vault 的语言身份。
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
      "accent_audit": false
    },
    "template_root": "系统配置/模板"
  }
  ```

### 2. 元数据统一化与 Fallback 兼容 (Unified Frontmatter & Migration)
所有外语的 Frontmatter 字段统一为多态的 `pronunciation`（发音）和 `variants`（变体/差分）。
**存量数据兼容策略 (Fallback)**：为了不破坏现有的上千张日语卡片，Python 脚本在读取发音时将采用软回退机制：优先读取 `pronunciation`，若不存在则回退合并读取 `reading` + `accent_display`。这使得新旧卡片可以无缝共存。

### 3. Agent 技能与平台中立化
- 将 `codex-skills/` 改名为 `agent-skills/`，去除内部的 `jp-` 前缀。
- **向下兼容与通用入口策略**：
  - **对于老旧命令行工具（如 Codex）**：我们将保留开发者编写的 `agents/openai.yaml`，供其继续使用。
  - **对于现代通用 Agent 框架（如 Claude Code, Cursor, Trae）**：它们**不需要**任何繁琐的 `.yaml` 注册文件！它们进入 Vault 的唯一全局入口是根目录下的 `AGENTS.md`。当用户唤起 Claude 时，`AGENTS.md` 会作为全局系统提示词，告诉 Claude 所有的技能路径及运行规则。无论是 `openai.yaml` 还是 `AGENTS.md`，它们都是作为 LingoTrace 框架源码随库分发的，**终端学习者永远不需要去初始化这些配置文件**。

---

## 四、 分阶段执行计划

### Phase 0：前置环境与能力校验
- [ ] 测试 ListenKit 对英语 ASR（`en-US`）的转写效果，确保多语种基建可用。

### Phase 1：配置层注入与专属插件剥离（零破坏）
- [ ] 新建 `系统配置/config.json`。
- [ ] 将 `setup_offline_dictionary.py` 和 `apply-accent-confirmations.py` 在脚本顶部注释中标记为 **[JP-ONLY]** 专属插件，从核心链路解绑。

### Phase 2：目录架构重命名与全局锚点同步
- [ ] 执行 `git mv codex-skills agent-skills` 并去除内部 `jp-` 前缀。
- [ ] 保持现有的 `agents/openai.yaml` 不变（作为向后兼容保留），并在全局说明文档 `AGENTS.md` 中强化通用 Agent 入口指引。
- [ ] 更新 `.gitignore`、`check-public-staged-files.sh`、`run-next-day-review-update.sh` 等 4 个 Shell 脚本中的硬编码探测锚点。

### Phase 3：Python 核心引擎解耦（含 Python 校验器）
- [ ] 新增 `tools/config_loader.py` 用于解析 `config.json`。
- [ ] 改造 `update_next_day_review.py` 及 `transcribe_listening.py`，挂载新的 Unified Frontmatter 字段，并**实装 Fallback 兼容读取逻辑**。
- [ ] 改造 `validate-survival-speaking-cards.sh` 中的 Python 校验器，从配置中动态获取 `speaking_text_field`（如 `en_text`）替代死编码的 `jp_text`。

### Phase 4：前端展现层 (Bases) 适配
- [ ] 改造 `总训练.base`：
  - 更新 `core_text` 公式，使其能够同时兼容 `en_text` 或 `jp_text`（根据 Vault 设定），并将发音展示改为指向 `pronunciation`。
  - 视图名称（如 `アクセント待练`）提供本地化指导策略。

### Phase 5：模板与 Agent 提示词隔离重构
- [ ] 重构 `系统配置/模板/` 树结构：
  - `jp/` 子目录：存放现有的 `单词卡模板.md`、`课堂语法卡模板.md` 等。
  - `en/` 子目录：新建一套采用 `pronunciation`、`variants`、`pos` 等字段的英文标准模板。
- [ ] 修改所有 SKILL.md，注入 `Configuration Awareness` 步骤，消除所有对日语特有属性的校验要求。

---

## 五、 测试与验证策略矩阵 (Verification Plan)
1. **老旧数据兼容性验证 (Unit Test)**：扩展 `test_update_next_day_review.py`，专门传入仅包含 `reading`+`accent_display` 的旧版数据 Mock，确保程序能够正确 Fallback 并完成流转。
2. **多语言配置加载验证**：新增 `test_config_loader.py`，测试配置解析及字段缺失情况。
3. **英语全链路 Dry Run**：向系统输入英文素材，调度 Agent 测试全链路，确保产出的卡片落在正确轨道且模板无误。
4. **CI 拦截防线**：在 `.github/workflows/` 新增 `multi-language-smoke.yml` 自动运行上述所有双语测试用例。
