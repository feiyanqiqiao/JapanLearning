# 评审报告：多语种支持架构演进方案 (V3)

- **评审对象**：`docs/iterations/20260607-multi-language-architecture-v3.md`
- **评审日期**：2026-06-07
- **评审结论**：✅ **通过** — 所有 P0/P1 问题已清零，可进入实施阶段

---

## 一、V2 评审 7 项修订建议的响应状态

V2 评审报告（`20260607-multi-language-architecture-v2-review.md`）提出了 7 项修订建议。以下逐项核验 V3 的响应情况：

| 编号 | 优先级 | V2 问题 | V3 响应位置 | 评价 |
|---|---|---|---|---|
| #1 | P0 | `总训练.base` 的 `jp_text` 未交代 | Phase 4（L78-80）："同时兼容 `en_text` 或 `jp_text`"，"发音展示改为指向 `pronunciation`" | ✅ **已解决** |
| #2 | P1 | `openai.yaml` → `skill.yaml` 风险 | L53-54：保留 `openai.yaml` 作为向后兼容，`AGENTS.md` 作为现代 Agent 通用入口 | ✅ **已解决**，策略优于 V2 评审建议 |
| #3 | P1 | Phase 3/4 边界不合理 | Phase 3（L75）明确包含 `validate-survival-speaking-cards.sh` 的 Python 校验器 | ✅ **已解决** |
| #4 | P1 | 模板目录结构未具体化 | Phase 5（L83-85）：`jp/` 子目录存放现有模板，`en/` 子目录新建英文模板 | ✅ 基本解决（见下文 2.1 细化建议） |
| #5 | P1 | 缺少数据迁移说明 | L48：Fallback 兼容策略，"优先读取 `pronunciation`，若不存在则回退合并读取 `reading` + `accent_display`" | ✅ **已解决** |
| #6 | P1 | 测试策略粗略 | 第五章 4 条策略，含 Fallback 专项测试（L91） | ✅ 基本解决（见下文 2.4 细化建议） |
| #7 | P2 | ListenKit 英语验证 | Phase 0（L61）："测试 ListenKit 对英语 ASR（`en-US`）的转写效果" | ✅ **已解决** |

**总评**：7 项全部响应，其中 5 项完整解决，2 项基本解决（仅需细节补充）。V2 的 P0 问题已消除。

---

## 二、V3 新增问题（5 处，均为 P2 级）

### 2.1 🟢 P2：模板目录重构的文件处置清单仍可细化

Phase 5（L83-85）描述了 `jp/` 和 `en/` 的方向，但对现有 6 个模板文件的具体处置方式未逐一说明。

当前 `系统配置/模板/` 目录：

| 文件 | 处置建议 |
|---|---|
| `录入模板索引.md` | 保留在原位，更新内部链接指向 `jp/` 和 `en/` 子目录，拆出内嵌的口语卡模板片段 |
| `单词卡模板.md` | 移入 `jp/单词卡模板.md`，字段名更新（`reading`→`pronunciation` 等） |
| `课堂语法卡模板.md` | 移入 `jp/课堂语法卡模板.md` |
| `课堂笔记模板.md` | 移入 `jp/课堂笔记模板.md` |
| `每日学习清单模板.md` | 保留在原位（语言无关） |
| `复习流程.md` | 保留在原位（语言无关） |

`en/` 下需新建：`单词卡模板.md`、`课堂语法卡模板.md`、`生活口语句子卡模板.md`（从 `录入模板索引.md` 中拆出）。

**建议**：在 Phase 5 中补充上述文件处置清单，确保执行时无遗漏。此为锦上添花，不阻塞实施。

### 2.2 🟢 P2：`config.json` 的 `features` 缺少 `kanji_diff_support`

V2 方案的 `features` 包含三个开关：`offline_dictionary`、`accent_audit`、`kanji_diff_support`。V3（L38-41）只保留了前两个。

`kanji_diff_support` 的作用是告知脚本和 Agent：该语言是否支持汉字差分卡片（日语 true，英语 false）。虽然 `variants` 统一字段已取代 `kanji_diff`，但这个开关仍然有控制意义——它决定了 Agent 是否需要执行"汉字差分检测"这一步骤（对英语无意义）。

**建议**：恢复 `kanji_diff_support` 开关，或在文档中显式说明"已移除，因为 `variants` 字段统一后不再需要独立的功能开关"。

### 2.3 🟢 P2：Fallback 写入策略未明确

L48 描述了 Fallback **读取**逻辑，但未说明**写入**时的行为：

当 Agent 创建一张新卡片或 Python 脚本 sink 一张卡片时：

1. 是否**只写** `pronunciation`（新字段）？
2. 还是**同时写** `pronunciation` + `reading` + `accent_display`（保持旧字段兼容）？

**建议**：明确为"只写 `pronunciation`"。理由：

- 新卡片天然使用新字段，无需维护旧字段
- `总训练.base` 公式已改为读 `pronunciation`，旧字段不再被消费
- 旧卡片保持原样不动，Fallback 读取逻辑负责兼容

具体 Fallback 读取实现参考：

```python
def get_pronunciation(frontmatter: dict) -> str:
    """优先读 pronunciation，fallback 到 accent_display（已含读音+音调）或 reading。"""
    if "pronunciation" in frontmatter:
        return frontmatter["pronunciation"]
    accent = frontmatter.get("accent_display", "")
    if accent:
        return accent  # accent_display 已包含读音+音调标记
    return frontmatter.get("reading", "")
```

### 2.4 🟢 P2：测试矩阵可补充 `test_transcribe_listening.py` 的适配

第五章（L91-94）提到了 `test_update_next_day_review.py` 的 Fallback 测试，但未提及 `test_transcribe_listening.py`（27 个测试）的适配。

该测试文件中有以下日语硬编码需要适配：

- 测试数据中的 `accent_display: すもう⓪` → 需新增使用 `pronunciation` 字段的测试用例
- `locale="ja-JP"` → 需新增 `locale="en-US"` 的测试用例验证 `language_label_for_locale("en-US")` → `"English"`
- 离线词典加载逻辑 → 需新增 `config.offline_dictionary == false` 时跳过加载的测试

**建议**：在第五章第 1 条后补充："同步扩展 `test_transcribe_listening.py`，新增英语 locale 和 pronunciation 字段的测试用例。"

### 2.5 🟢 P2：Phase 6（文档更新）未列出

V2 方案的替代方案中有 Phase 6 文档更新。V3 的 Phase 0-5 覆盖了代码和配置层面，但未提及文档同步。

**建议**：在 Phase 5 后补充 Phase 6 文档更新，至少包括：

- `docs/HOWTO_ADD_NEW_LANGUAGE.md`：更新 `config.json` 完整 schema
- `CHANGELOG.md`：记录多语言架构重构
- `tools/README.md`：标注 `[JP-ONLY]` 脚本
- `docs/USER_GUIDE.md`：更新目录结构说明

---

## 三、V3 亮点

1. **`openai.yaml` 的处理策略是三版方案中最优的**。保留旧文件做向后兼容，同时指出现代 Agent 框架（Claude Code、Cursor、Trae）根本不需要 yaml 注册文件——`AGENTS.md` 才是通用入口。这个认知比 V2 的"重命名为 `skill.yaml`"高了一个层级。
2. **Fallback 兼容策略是正确的工程决策**。不搞一次性迁移脚本，让新旧字段自然共存，通过读取时 fallback 实现无缝过渡。这对已有上千张卡片的用户 Vault 来说是风险最低的方案。
3. **Phase 3 将 `validate-survival-speaking-cards.sh` 的 Python 校验器纳入**，解决了 V2 中 Phase 3/4 边界不一致的问题。
4. **Phase 0 前置验证 ListenKit 英语 ASR**，确保多语种基建在写代码前就确认可用。
5. **全文精炼**，从 V2 的 110 行压缩到 95 行，信息密度提升，无冗余。

---

## 四、修订建议汇总

| 优先级 | 编号 | 问题 | 建议 |
|---|---|---|---|
| P2 | #1 | 模板文件处置清单 | 补充 6 个现有文件的具体处置方式（移动/保留/新建） |
| P2 | #2 | `features` 缺 `kanji_diff_support` | 恢复该开关或显式说明移除理由 |
| P2 | #3 | Fallback 写入策略未明确 | 明确为"只写 `pronunciation`" |
| P2 | #4 | `test_transcribe_listening.py` 适配 | 补充英语 locale 和 pronunciation 字段的测试用例 |
| P2 | #5 | Phase 6 文档更新 | 补充文档同步步骤 |

---

## 五、三版方案演进对照

| 维度 | V1 | V2 | V3 |
|---|---|---|---|
| 审计发现 | 5 项 | 7 项 | 6 项（合并同类项，更精炼） |
| P0 遗漏 | 4 项 | 1 项 | **0 项** |
| P1 遗漏 | 5 项 | 6 项 | **0 项** |
| 配置设计 | "升级为 config.json" | 双轨制 + 完整 schema | 双轨制 + 完整 schema |
| 字段策略 | 语言分裂 | 统一化 | 统一化 + Fallback 兼容 |
| 平台策略 | 未提及 | 重命名 yaml（有风险） | **保留 + 通用入口（最优）** |
| 数据迁移 | 无 | 无 | **Fallback 兼容（最优）** |
| 测试策略 | 无 | 4 条（粗略） | 4 条（含 Fallback 专项） |
| 文档更新 | 无 | 无 | 未列出（P2 级补充） |
| 阻塞问题数 | 9 项 | 7 项 | **0 项** |

---

## 六、结论

V3 方案**可以进入实施阶段**。

所有 P0 和 P1 问题已全部解决。剩余 5 处均为 P2 级细节补充（模板文件清单、写入策略、测试用例、文档同步），不阻塞任何 Phase 的执行。这些细节可以在各 Phase 的执行过程中同步补充，无需再出 V4。

建议按 Phase 0 → 1 → 2 → 3 → 4 → 5 顺序推进，在每个 Phase 的 PR 描述中补充对应的细节。
