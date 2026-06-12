# 评审报告：多语种支持架构演进方案 (V2)

- **评审对象**：`docs/iterations/20260607-multi-language-architecture-v2.md`
- **评审日期**：2026-06-07
- **评审结论**：⚠️ **有条件通过** — 较 V1 显著进步，审计覆盖从 5 项扩展到 7 项，核心架构决策设计清晰，剩余问题集中在执行细节的完整性上

---

## 一、原评审 13 项修订建议的响应状态

V1 评审报告（`20260607-multi-language-architecture-review.md`）提出了 13 项修订建议。以下逐项核验 V2 的响应情况：

| 编号 | 优先级 | 建议 | V2 响应位置 | 评价 |
|---|---|---|---|---|
| #1 | P0 | `总训练.base` 泛化 | Phase 4（L94-97） | ⚠️ **部分覆盖** — 提到改公式和视图名，但 `jp_text` 字段的处理未提及 |
| #2 | P0 | `validate-survival-speaking-cards.sh` 解耦 | Phase 4 第 1 项（L93） | ✅ 完整 |
| #3 | P0 | `apply-accent-confirmations.py` 归属 | Phase 1（L78） | ✅ 完整 |
| #4 | P0 | `config.json` ∥ `paths.json` 关系 | 第三章第 1 节（L28-49） | ✅ 双轨制设计清晰 |
| #5 | P1 | Shell 脚本审计 | Phase 2（L83） | ✅ 列举了 4 个脚本 |
| #6 | P1 | `sync-to-global.sh` 更新范围 | Phase 2（L83-84） | ✅ 明确提到 |
| #7 | P1 | `config.json` schema 扩展 | 第三章第 1 节（L32-48） | ✅ 完整 schema，含 features 开关 |
| #8 | P1 | 迁移策略 | 隐含在渐进 Phase 中 | ⚠️ 缺显式说明（见下文 2.5） |
| #9 | P1 | 测试策略 | 第五章（L105-109） | ⚠️ 覆盖但不够具体（见下文 2.6） |
| #10 | P2 | SKILL.md 内容泛化 | Phase 5（L101） | ✅ 明确为独立步骤 |
| #11 | P2 | ListenKit 英语验证 | 未显式提及 | ⚠️ 建议补充（见下文 2.7） |
| #12 | P2 | 英语 frontmatter schema | 第三章第 2 节（L55-64） | ✅ 完整表格 |
| #13 | P2 | 文档语言统一 | 全文中文 | ✅ 已修正 |

**总评**：13 项中 9 项完整响应，4 项部分响应。较 V1（0 项覆盖）有质的提升。

---

## 二、V2 新增问题（7 处）

### 2.1 🔴 P0：`总训练.base` 的 `jp_text` 字段未交代

Phase 4（L94-97）描述了 `core_text` / `support_text` 公式改写和视图名称本地化，但**完全未提及 `jp_text` 字段的处理**。

当前 `core_text` 公式是：

```
if(jp_text, jp_text, if(headword, if(accent_display, accent_display, headword), ...))
```

V2 方案将 `accent_display` → `pronunciation`（L95），但 `jp_text` 怎么办？在英语 Vault 中：

- 保留 `jp_text`？→ 语义荒谬
- 改为 `en_text`？→ 需要显式说明
- 统一为 `target_text`？→ 与第三章 `speaking_text_field: "en_text"` 矛盾

此外，`总训练.base` 的 property 声明（`displayName: 日语句子`、`displayName: 重音`）和 `生活口语待练` 视图中的 `jp_text` 列也需更新。

**建议**：在 Phase 4 中补充：

1. `jp_text` → `en_text`（英语 Vault）的公式替换
2. property `displayName` 更新（`日语句子` → `目标语言句子`，或根据 Vault 语言分别设置）
3. 视图表列的字段引用更新

### 2.2 🟡 P1：`openai.yaml` → `skill.yaml` 重命名风险未评估

Phase 2（L84）提出将 `agents/openai.yaml` 重命名为 `agents/skill.yaml` 以"消除厂商锁定"。

但 `openai.yaml` 是 **OpenAI Codex 平台的约定格式**——Codex CLI 在加载 skill 时会自动查找 `agents/openai.yaml`。重命名会导致：

- 现有 Codex 用户的 skill 发现机制失效
- `sync-to-global.sh` 复制到 `~/.codex/skills/` 后 Codex 无法识别

如果目标是支持多平台（Codex + Claude + 其他），正确的做法是**保留 `openai.yaml` 同时新增其他平台的 manifest**（如 `agents/claude.yaml`），而非替换。

**建议**：

- 方案 A（推荐）：保留 `openai.yaml`，新增 `agents/claude.yaml` 等平台 manifest，`sync-to-global.sh` 根据目标平台选择性复制
- 方案 B：如果确认不再支持 OpenAI Codex，显式声明并说明对现有用户的影响

### 2.3 🟡 P1：Phase 3 与 Phase 4 的边界划分不合理

`validate-survival-speaking-cards.sh` 是一个**内嵌 Python 校验器的 Shell 脚本**（L93 将其归入 Phase 4"前端交互展现层"），但它的本质是 Python 逻辑，与 Phase 3 的 `config_loader.py` 有直接依赖关系。

同理，`总训练.base` 的公式改写依赖于 Phase 3 确定的字段名（`pronunciation` / `variants`），却放在 Phase 4。

**问题**：Phase 3 完成后系统并不处于一致状态——校验器还在用旧字段名 `jp_text`，Bases 还在用 `accent_display`。如果此时有人运行校验或查看仪表板，会看到错误结果。

**建议**：将 `validate-survival-speaking-cards.sh` 的 Python 内嵌部分移入 Phase 3（与 `update_next_day_review.py` 同批次），Phase 4 专注于纯 Obsidian 层面的变更（`.base` 公式 + property + 视图 + 模板）。

### 2.4 🟡 P1：模板目录重构的具体文件清单缺失

Phase 5（L99）提到"隔离 `jp/` 与 `en/` 双轨制模板"，但未给出具体结构。

当前 `系统配置/模板/` 下有 6 个文件：

| 文件 | 语言相关性 | 处置方式 |
|---|---|---|
| `录入模板索引.md` | 语言无关（但内嵌了日语口语卡模板片段） | 需更新内部链接 + 拆出嵌入模板 |
| `单词卡模板.md` | 日语专属（含 `reading`、`accent_display`、`kanji_diff`） | 移入 `jp/`，字段名更新 |
| `课堂语法卡模板.md` | 日语专属（含日语活用形格式） | 移入 `jp/` |
| `课堂笔记模板.md` | 日语专属（含 `単語`、`漢字差分` 节） | 移入 `jp/` |
| `每日学习清单模板.md` | 语言无关 | 保留在原位 |
| `复习流程.md` | 语言无关 | 保留在原位 |

**需要明确**：

1. `录入模板索引.md` 中嵌入的 `生活口语句子卡模板`（L129-141）如何拆出为独立文件？
2. 英语 `en/` 下需要新建哪些文件？（至少：`单词卡模板.md`、`课堂语法卡模板.md`、`生活口语句子卡模板.md`）
3. `录入模板索引.md` 是否改为按语言分区索引？

**建议**：补充目标目录树结构：

```
系统配置/模板/
  录入模板索引.md          ← 保留（更新内部链接，按语言分区）
  每日学习清单模板.md      ← 保留（语言无关）
  复习流程.md              ← 保留（语言无关）
  jp/
    单词卡模板.md          ← 移动自上层，字段名更新
    课堂语法卡模板.md      ← 移动自上层
    课堂笔记模板.md        ← 移动自上层
    生活口语句子卡模板.md  ← 从录入模板索引中拆出
  en/
    单词卡模板.md          ← 新建
    课堂语法卡模板.md      ← 新建
    生活口语句子卡模板.md  ← 新建
```

### 2.5 🟡 P1：缺少显式的现有数据迁移说明

V2 方案描述了"目标状态"，但对**现有日语 Vault 中已有的卡片数据**未做任何说明。

核心问题：现有日语卡片使用 `reading` + `accent_display` + `kanji_diff` 字段，重构后脚本期望 `pronunciation` + `variants`。如果直接切换：

- `update_next_day_review.py` 读不到 `pronunciation` → sink 逻辑崩溃
- `transcribe_listening.py` 建立的音调索引找不到 `pronunciation` → 音调候选丢失
- `总训练.base` 的 `core_text` 公式引用 `pronunciation` → 所有卡片显示为空

**需要明确**：

1. 是否需要一次性数据迁移脚本（将现有卡片的 `reading` + `accent_display` → `pronunciation`）？
2. 还是脚本同时兼容新旧字段名（读取时 fallback：先找 `pronunciation`，找不到就拼接 `reading` + `accent_display`）？
3. 迁移的回滚方案是什么？

**建议**：推荐**兼容模式（fallback 读取）**——脚本优先读 `pronunciation`，fallback 到 `reading` + `accent_display` 拼接。这样无需一次性迁移，新旧卡片共存，自然过渡。具体实现：

```python
def get_pronunciation(frontmatter: dict) -> str:
    """优先读 pronunciation，fallback 到 reading + accent_display 拼接。"""
    if "pronunciation" in frontmatter:
        return frontmatter["pronunciation"]
    reading = frontmatter.get("reading", "")
    accent = frontmatter.get("accent_display", "")
    if accent:
        return accent  # accent_display 已包含读音+音调
    return reading
```

### 2.6 🟡 P1：测试策略过于粗略

第五章（L105-109）列了 4 条验证策略，但缺少具体性：

**现有 47 个测试的适配清单**：

| 测试文件 | 测试数 | 是否需要改动 | 改动内容 |
|---|---|---|---|
| `test_update_next_day_review.py` | 5 | ✅ 是 | `reading:` → `pronunciation:`、`kanji_diff:` → `variants:`、新增 `--config` 参数、创建临时 `config.json` fixture |
| `test_transcribe_listening.py` | 27 | ✅ 是 | `accent_display` → `pronunciation`、新增英语 locale 测试用例（`en-US` → `English`）、离线词典条件化测试 |
| `test_migrate_vault_layout.py` | 9 | ❌ 否 | 迁移工具与语言无关 |
| `test_validate_vault_structure.py` | 6 | ❌ 否 | 路径校验与语言无关 |

**新增测试**：

| 新测试 | 覆盖内容 |
|---|---|
| `test_config_loader.py` | config.json 解析、缺失字段默认值、文件不存在异常、JSON 格式错误 |
| `test_update_next_day_review_english.py` | 英语 Vault 的完整 SRS 流程：创建卡片 → sink → merge，使用 `pronunciation` / `variants` 字段 |
| `test_transcribe_listening_english.py` | 英语 locale 的 ListenKit 调用链验证（mock ListenKit），验证 `language_label_for_locale("en-US")` → `"English"` |
| `test_survival_speaking_validation_english.py` | 英语 speaking card 的 `en_text` 字段校验 |

**建议**：将上述矩阵纳入第五章，作为测试策略的具体执行清单。

### 2.7 🟢 P2：ListenKit 英语验证未显式提及

原评审 P2 #11 建议验证 ListenKit 英语支持。V2 方案隐含了这一点（Phase 3 提到"动态读取区域设置"），但未显式声明验证结论。

通过代码审计已确认：

1. `language_label_for_locale()`（`transcribe_listening.py:328-338`）已支持 `en→English` 映射
2. `--locale` 参数（`transcribe_listening.py:276`）默认 `ja-JP` 但可通过 CLI 覆盖
3. `--language` 参数（`prepare-source-note-material.sh:74-77`）默认 `Japanese` 但支持覆盖
4. Whisper 原生支持 ~100 种语言

**结论**：ListenKit 英语支持**在代码层面已就绪**，但**缺少实测验证**。

**建议**：在 Phase 1 前增加一个前置验证步骤："手动用一条英语音频测试 ListenKit 的英语 ASR 输出质量，确认端到端可用。"

---

## 三、V2 亮点

1. **审计发现（第二章）覆盖全面**。V1 遗漏的 `总训练.base`、`validate-survival-speaking-cards.sh`、Shell 脚本锚点、`apply-accent-confirmations.py` 在 V2 中全部补齐（共 7 项 vs V1 的 5 项）。
2. **`openai.yaml` → `skill.yaml` 的思考方向正确**。虽然执行方式需调整（保留旧文件 + 新增多平台 manifest），但"消除厂商锁定"的出发点是有价值的架构思考。
3. **Phase 顺序合理**。从零破坏的配置注入开始（Phase 1），到高风险的目录重命名（Phase 2），再到核心引擎解耦（Phase 3），层层递进，每个 Phase 独立可交付。
4. **字段统一化设计（`pronunciation` / `variants`）是正确的架构决策**。避免了每增一门语言改一遍脚本的困境，是 V1 方案"英语引入 `ipa` / `spelling_diff`"的显著改进。
5. **`config.json` 的 `features` 布尔开关设计优雅**。用 `offline_dictionary`、`accent_audit`、`kanji_diff_support` 三个开关控制可选功能，避免在脚本中硬编码"日语才有的功能"。
6. **文档语言统一为中文**，消除了 V1 中中英文混用的可读性问题。

---

## 四、修订建议汇总

| 优先级 | 编号 | 问题 | 建议 |
|---|---|---|---|
| P0 | #1 | `总训练.base` 的 `jp_text` 字段未交代 | 补充 `jp_text` → `en_text` 的公式替换、property displayName 更新、视图表列更新 |
| P1 | #2 | `openai.yaml` → `skill.yaml` 风险未评估 | 保留 `openai.yaml` + 新增多平台 manifest，或显式声明弃用 Codex 支持 |
| P1 | #3 | Phase 3/4 边界不合理 | 将 `validate-survival-speaking-cards.sh` Python 部分移入 Phase 3 |
| P1 | #4 | 模板目录结构未具体化 | 补充目标目录树 + 每个文件的处置方式 |
| P1 | #5 | 缺少现有数据迁移说明 | 明确是兼容模式（fallback 读取）还是迁移脚本 |
| P1 | #6 | 测试策略粗略 | 补充测试文件清单和具体用例矩阵 |
| P2 | #7 | ListenKit 英语验证未显式提及 | 增加前置验证步骤 |

---

## 五、与 V1 评审的对比

| 维度 | V1 方案 | V2 方案 | 改进幅度 |
|---|---|---|---|
| 审计发现数量 | 5 项 | 7 项 | +40% |
| P0 遗漏 | 4 项 | 1 项 | -75% |
| 配置文件设计 | 含糊（"升级为 config.json"） | 清晰（双轨制 + 完整 schema） | 质的提升 |
| 字段命名策略 | 语言分裂（`ipa`/`spelling_diff`） | 统一化（`pronunciation`/`variants`） | 质的提升 |
| 分阶段计划 | 无 | 5 个 Phase + 明确产出物 | 从无到有 |
| 测试策略 | 无 | 4 条验证策略 | 从无到有 |
| 剩余 P1 问题 | 5 项 | 6 项（均为细节补充） | 问题性质从"架构缺陷"降级为"执行细节" |

---

## 六、结论

V2 方案较 V1 有显著进步：审计覆盖全面，核心架构决策（双轨制配置、字段统一化）设计清晰，分阶段执行计划合理。

剩余问题主要集中在**执行细节的完整性**上：`jp_text` 在 Bases 中的处理、现有数据的兼容策略、模板目录的具体结构、测试用例的粒度。这些都是"补充说明"层面的修订，不涉及架构方向调整。

建议按 P0 → P1 → P2 修订后进入实施。预计修订工作量：**1-2 小时**。
