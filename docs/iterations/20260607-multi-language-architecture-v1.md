# 多语种支持架构演进方案（归档）

根据讨论决策，我们采用 **“一门语言一个 Vault (One Vault Per Language)”** 的架构理念。学习不同语种在心智上是高度独立的任务，保持独立的 Vault 可以让个人的知识图谱和 Obsidian 工作区更加纯粹、干净，同时大幅降低系统的路由复杂度。

本方案以**引入英语支持**作为试点，规划如何将底层框架与特定的日语特性进行解耦。

---

## 现存的硬编码痛点 (Audit Findings)

通过梳理代码，目前框架在以下维度与日语强耦合：
1. **Python 脚本硬编码**：`update_next_day_review.py`、`transcribe_listening.py`、`migrate_vault_layout.py` 中写死了 `jp/vocab`、`jp/listening` 等标签。
2. **Agent 提示词 (SKILL.md) 强关联**：强制校验 `reading`（假名读音）、`accent_display`（音调）、`kanji_diff`（汉字辨析）等日语专属的前端元数据。
3. **路径角色特异性**：`paths.json` 中定义的 `pronunciation_accent_root`（发音/アクセント）是日语特有的 Pitch Accent 概念。
4. **命名空间局限**：目录名 `codex-skills` 固化了 AI 平台，子目录名 `jp-*` 固化了语种。
5. **外部转写硬编码**：调用 ListenKit 时直接写死了 `--language Japanese`。

---

## Proposed Changes (重构执行方案)

### 1. 目录架构全面泛化 (打破认知局限)
- **[RENAME]** 根目录 `codex-skills/` 重命名为 `agent-skills/`，标志本项目向通用 Agent 框架转型。
- **[RENAME]** 将内部子目录的 `jp-` 前缀抹除，例如 `jp-review-material-maintainer` 改为通用名称 `review-material-maintainer`。
- **[MODIFY]** 同步全局替换 `README.md`、`AGENTS.md`、`.gitignore` 和 `check-public-staged-files.sh` 中对旧路径的引用。

### 2. 引入 Vault 级语言配置文件
由于每个 Vault 只专心学一门语言，我们只需要在现有的 `系统配置/paths.json` 外壳基础上，将它升级为全局的 `config.json`，并注入该 Vault 的语言灵魂：

```json
{
  "language_profile": {
    "name": "English",
    "tag_namespace": "en",
    "listenkit_lang": "English",
    "pronunciation_system": "ipa"
  },
  "roles": {
    "focus_vocab_root": "学习系统/词库/重点词汇",
    ...
  }
}
```
*注：Vault 的目录结构（如 `学习系统/词库/`）完全保持不变，纯粹靠配置切换底层业务逻辑。*

### 3. Frontmatter 与模板 (Templates) 的语种分化
因为不同语言的词汇属性（骨架）不同，我们在系统的模板目录下建立分化：
- `系统配置/模板/en/单词卡模板.md`
- `系统配置/模板/jp/单词卡模板.md`

**英语单词卡设计变更**：
- 移除：`reading`（读音）、`accent_display`（声调）、`kanji_diff`（汉字辨析）。
- 引入：`ipa`（国际音标）、`pos`（词性）、`spelling_diff` / `confusable_with`（易混词辨析）。
- 标签变更为 `- en/vocab`。

### 4. 彻底解耦 Agent SKILL.md
- **[MODIFY]** 清除所有 `SKILL.md` 中写死的日语要求。
- 引入配置感知：Agent 在执行动作前，必须先读取当前 Vault 的 `config.json` 获取 `tag_namespace`。
- 指令变为：`When creating a card, strictly use the template located at <template_root>/<tag_namespace>/ and append tags using <tag_namespace>/vocab.`

### 5. Python 工具链动态化与词典剥离
- **[MODIFY]** 修改 `update_next_day_review.py` 和对应的单元测试 `test_update_next_day_review.py`，不再写死 `jp/`，而是从 `config.json` 中读取 `tag_namespace`，动态生成 `tags = [f"{namespace}/vocab"]`。
- **[MODIFY]** `transcribe_listening.py` 动态读取 `listenkit_lang` 和 `tag_namespace`。
- **[MODIFY]** `migrate_vault_layout.py` 同样将原本硬编码的分类标签替换为动态读取。
- **[DECOUPLE]** 针对原项目硬编码的日语离线词典脚本 `setup_offline_dictionary.py`（依赖 `fugashi`），将其标记为特定语种（日语）的专属插件，从系统的核心启动链路中剥离。英语等新语种可直接通过 LLM 标注音标，无需强依赖本地词典。
