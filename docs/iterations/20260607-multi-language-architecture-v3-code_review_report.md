# V3 代码审查报告 (Code Review Report)

- **审查对象**：Commit `19ca166` (基于 `20260607-multi-language-architecture-v3-impl-plan.md`)
- **审查基准**：`20260607-multi-language-architecture-v3.md` (V3 架构白皮书)
- **审查结论**：🔴 **打回重做 (需要修复 P0 缺陷)** — 核心的 Python 引擎解耦做得非常漂亮，但前端交互层 (Bases) 和模板结构层出现了严重的“偷工减料”，直接违背了 V3 架构的两个核心设计。

---

## 🟢 值得赞赏的优秀实现 (Strengths)

1. **优雅的 Fallback 降级机制**：`tools/vocab_note.py` 的实现非常精妙。通过 `normalize_reading` 等函数，优先读取新字段 `pronunciation`，为空时自动回退读取旧字段 `reading` + `accent_display`。这完美且安全地保障了历史存量数据的兼容。
2. **健壮的配置加载器**：`tools/config_loader.py` 实现了带有 `_JAPANESE_DEFAULTS` 的容错机制。这意味着即便老用户的 Vault 里忘了加 `config.json`，系统依然能按日语模式兜底运行，零破坏。
3. **彻底的命名空间清理**：干净利落地完成了 `codex-skills` 向 `agent-skills` 的重命名，并且将所有的 `jp-` 前缀移除，关联的十几处 Shell 脚本和 `sync-to-global.sh` 均成功更新，未留死角。
4. **内嵌 Python 解决 Shell 痛点**：在 `validate-survival-speaking-cards.sh` 中使用了一段内嵌的 Python 脚本动态读取 `config.json` 里的 `speaking_text_field`，成功干掉了原先死磕 `jp_text` 的硬编码。

---

## 🔴 P0 级严重架构违背 (Blockers)

### 1. 前端 Bases 公式遗漏了 `pronunciation` 字段
在 V3 白皮书中，Phase 4 明确要求：*“更新 core_text 公式... 并将发音展示改为指向 pronunciation”*。

**当前实现**：
```text
if(jp_text, jp_text, if(fr_text, fr_text, if(headword, if(accent_display, accent_display, headword), ...)))
```
**缺陷分析**：
Agent 仅仅是盲目地加了一个 `fr_text`，但**完全忘记了加入最重要的 `pronunciation` 字段**！这意味着如果用户现在新建了一张英语单词卡，填写了全新的 `pronunciation` 字段，前端面板上将无法显示发音（因为公式依然只认旧时代的 `accent_display`），最终只会退化显示干瘪的词头（headword）。
**修复要求**：
公式必须将 `pronunciation` 纳入优先读取链，例如：
`if(pronunciation, pronunciation, if(accent_display, accent_display, headword))`。同时需要补上 `en_text`。

### 2. 模板目录未实施“双轨制”隔离
在 V3 白皮书中，Phase 5 明确要求：*“重构 `系统配置/模板/` 树结构：`jp/` 子目录存放现有模板，`en/` 子目录新建英文标准模板”*。

**当前实现**：
Agent 完全没有新建任何子目录！它“偷懒”地直接把 `pronunciation` 和 `variants` 加到了原有的 `系统配置/模板/单词卡模板.md` 里。
**缺陷分析**：
这严重破坏了“One Vault Per Language”的纯净体验原则。现在一个学习英语的用户，打开单词卡模板，依然会看到带有 `reading`、`accent_display`、`kanji_diff` 的冗杂废代码，甚至还有“如 にもつ①”的日语指导。这与泛化设计的初衷背道而驰。
**修复要求**：
必须严格执行物理隔离。把现有的带有 `reading` 的模板全部移入 `系统配置/模板/jp/`，并在 `系统配置/模板/en/` 下为英语建立一套干净的、只有 `pronunciation` 和 `variants` 等字段的新模板。

---

## 🟡 P1 级执行遗漏 (Warnings)

### 1. 遗漏了 CI 拦截防线工作流
**缺陷分析**：
V3 白皮书第五章明确要求：*“引入 CI 冒烟测试：在 `.github/workflows/` 新增 `multi-language-smoke.yml`”*。目前的 commit 记录中并未包含任何 `.github/` 目录的新增文件。
**修复要求**：
补齐 GitHub Actions 的 YAML 配置文件，利用已有的 unittest 跑通自动化测试。

---

## 📝 审查总结与下一步行动

另一位 Agent 在执行 **Python 核心引擎解耦** 这个最难的任务上表现出色，但在处理**前端展示逻辑**和**用户可见的模板结构**时出现了偷工减料，没有严格遵照 V3 的设计白皮书。

建议直接根据这份报告开启一轮 **Bugfix / 补丁阶段**，修复上述两个 P0 级缺陷即可顺利推进到主线。
