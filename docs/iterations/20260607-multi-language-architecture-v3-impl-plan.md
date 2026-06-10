# V3 多语言架构实施计划

## 背景

LingoTrace 当前是一个深度绑定日语的 Obsidian 学习工作流引擎。V3 设计文档定义了"One Vault Per Language"架构，目标是让系统支持任意语言，同时保持日语 vault 的完全兼容。本计划将 V3 设计转化为可执行的实施步骤。

**核心约束**：所有现有日语笔记必须无需迁移即可继续工作（向后兼容）。

---

## 实施阶段

### Phase 0: 基础设施 — config.json + config_loader.py

**目标**：建立语言身份配置和统一配置加载器，作为所有后续改造的基础。

#### 0.1 创建 `系统配置/config.json`

```json
{
  "language_profile": {
    "name": "Japanese",
    "tag_namespace": "jp",
    "listenkit_locale": "ja-JP",
    "listenkit_language": "Japanese",
    "pronunciation_system": "pitch_accent",
    "speaking_text_field": "jp_text"
  },
  "features": {
    "offline_dictionary": true,
    "accent_audit": true
  }
}
```

**文件**：`系统配置/config.json`（新建）

#### 0.2 创建 `tools/config_loader.py`

统一配置加载模块，所有 Python 脚本通过它读取语言配置。

**核心 API**：

- `load_config(vault_root: Path) -> dict` — 加载并验证 config.json
- `get_tag_namespace(config: dict) -> str` — 获取标签前缀（如 "jp"）
- `get_speaking_text_field(config: dict) -> str` — 获取口语句卡文本字段名
- `get_listenkit_locale(config: dict) -> str` — 获取 ListenKit locale
- `is_feature_enabled(config: dict, feature: str) -> bool` — 检查功能开关

**文件**：`tools/config_loader.py`（新建）

#### 0.3 创建 `tools/tests/test_config_loader.py`

**文件**：`tools/tests/test_config_loader.py`（新建）

---

### Phase 1: 统一 Frontmatter 语义

**目标**：用多态字段名替代日语专属字段名，同时保持向后兼容读取。

#### 1.1 创建 `tools/vocab_note.py`

统一词汇卡 frontmatter 操作模块。

**核心 API**：

- `normalize_reading(frontmatter: dict) -> str` — 读取 `pronunciation`，回退到 `reading`+`accent_display`
- `normalize_variants(frontmatter: dict) -> list` — 读取 `variants`，回退到 `kanji_diff_pairs`
- `build_reading(pronunciation_system: str, ...) -> str` — 根据语言构建 pronunciation 值
- `FIELD_ALIASES` — 定义旧字段到新字段的映射关系

**回退逻辑**（关键）：

```python
def normalize_reading(fm: dict) -> str:
    if "pronunciation" in fm:
        return fm["pronunciation"]
    reading = fm.get("reading", "")
    accent = fm.get("accent_display", "")
    return f"{reading}{accent}" if accent else reading
```

**文件**：`tools/vocab_note.py`（新建）

#### 1.2 更新模板文件

**`系统配置/模板/单词卡模板.md`**：

- 在 frontmatter 中新增 `pronunciation` 和 `variants` 字段
- 保留 `reading`、`accent_display`、`kanji_diff`、`kanji_diff_pairs` 作为兼容字段
- 在使用规则中说明：新卡使用 `pronunciation`/`variants`，旧卡仍可使用旧字段

**`系统配置/模板/录入模板索引.md`**：

- 更新说明，提及新的多态字段名

**文件**：

- `系统配置/模板/单词卡模板.md`（修改）
- `系统配置/模板/录入模板索引.md`（修改）

---

### Phase 2: 通用词汇脚本

**目标**：创建语言无关的词汇卡操作脚本，替代日语硬编码逻辑。

#### 2.1 创建 `tools/vocab_ops.py`

从 `update_next_day_review.py` 中提取词汇相关操作，泛化为语言无关。

**核心功能**：

- 从 frontmatter 中读取 `speaking_text_field`（由 config.json 驱动）
- 使用 `vocab_note.normalize_reading()` 替代直接读取 `reading`/`accent_display`
- 使用 `vocab_note.normalize_variants()` 替代直接读取 `kanji_diff_pairs`

**文件**：`tools/vocab_ops.py`（新建）

---

### Phase 3: 配置驱动的复习脚本

**目标**：让 `update_next_day_review.py` 从 config.json 读取标签前缀，不再硬编码 `jp/`。

#### 3.1 修改 `update_next_day_review.py`

**改动点**：

1. 引入 `config_loader.load_config()`
2. 将 `TRACK_LABELS` 改为从 config 动态生成标签
3. 将硬编码的 `jp/` 标签前缀替换为 `config["language_profile"]["tag_namespace"] + "/"`
4. 保持 `STAGE_DAYS`、`STAGE_RULES` 不变（它们是语言无关的）
5. 添加命令行参数 `--config` 允许指定配置文件路径

**向后兼容**：

- 如果 vault 中没有 config.json，回退到默认的 `jp` 命名空间
- 现有的 `reading`+`accent_display` 字段继续被正确读取

**文件**：`codex-skills/jp-next-day-review-updater/scripts/update_next_day_review.py`（修改）

---

### Phase 4: Agent Skills 重构

**目标**：将 `codex-skills/` 重命名为 `agent-skills/`，移除 `jp-` 前缀，更新所有 SKILL.md 和脚本。

#### 4.1 目录重命名

```
codex-skills/jp-listening-script-generator/      → agent-skills/listening-script-generator/
codex-skills/jp-next-day-review-updater/          → agent-skills/next-day-review-updater/
codex-skills/jp-review-material-maintainer/       → agent-skills/review-material-maintainer/
codex-skills/jp-source-note-generator/            → agent-skills/source-note-generator/
codex-skills/jp-survival-speaking-card-generator/  → agent-skills/survival-speaking-card-generator/
```

使用 `git mv` 执行重命名，保留 git 历史。

#### 4.2 更新每个 SKILL.md

所有 5 个 SKILL.md 文件需要：

- 更新 `name:` frontmatter（移除 `jp-` 前缀）
- 更新 `description:` 中的日语特定描述为语言无关描述
- 更新文件路径引用（`codex-skills/` → `agent-skills/`）
- 更新 `sync-to-global.sh` 路径

#### 4.3 更新 `validate-survival-speaking-cards.sh`

将硬编码的 `jp_text` 字段名改为从 config.json 读取 `speaking_text_field`。

**文件**：

- 所有 5 个 SKILL.md（修改）
- 所有 5 个 `sync-to-global.sh`（修改）
- `validate-survival-speaking-cards.sh`（修改）
- `AGENTS.md`（修改，更新入口点路径）

---

### Phase 5: 工具链更新

**目标**：更新辅助脚本和配置，完成多语言改造。

#### 5.1 更新 `apply-accent-confirmations.py`

当前完全绑定日语音调系统。改造为：

- 从 config.json 读取 `pronunciation_system`
- 如果不是 `pitch_accent`，跳过或给出提示
- 保留日语音调逻辑不变

#### 5.2 更新 `总训练.base`

将 `core_text` 公式中的 `jp_text` 改为兼容写法：

- 在 formula 中同时检查 `jp_text` 和通用字段名（如 `text`），确保兼容
- Bases 公式不支持动态字段名引用，因此采用多字段回退策略

#### 5.3 更新文档

- `docs/HOWTO_ADD_NEW_LANGUAGE.md` — 与实际实现对齐
- `README.md` — 更新项目结构说明，反映 `agent-skills/` 目录重命名
- `CHANGELOG.md` — 记录本次架构变更

**文件**：

- `codex-skills/jp-review-material-maintainer/scripts/apply-accent-confirmations.py`（修改）
- `学习系统/总训练.base`（修改）
- `docs/HOWTO_ADD_NEW_LANGUAGE.md`（修改）
- `README.md`（修改）
- `CHANGELOG.md`（修改）

---

### Phase 6: 验证

#### 6.1 运行所有现有测试

```bash
python3 -m unittest tools/listening-transcribe-official/tests/test_transcribe_listening.py
python3 -m unittest codex-skills/jp-next-day-review-updater/tests/test_update_next_day_review.py
python3 -m unittest discover -s tools/vault-structure/tests -p 'test_*.py'
python3 -m unittest discover -s tools/tests -p 'test_*.py'
```

#### 6.2 手动验证

- 用现有日语 vault 运行 `update_next_day_review.py --dry-run`，确认输出不变
- 检查所有 SKILL.md 路径引用是否正确
- 检查 AGENTS.md 入口点是否正确指向新路径

---

## 关键文件清单

### 新建文件（6 个）

| 文件 | 用途 |
|------|------|
| `系统配置/config.json` | 语言身份配置 |
| `tools/config_loader.py` | 统一配置加载器 |
| `tools/vocab_note.py` | 统一词汇卡 frontmatter 操作 |
| `tools/vocab_ops.py` | 语言无关的词汇操作 |
| `tools/tests/__init__.py` | 测试包 |
| `tools/tests/test_config_loader.py` | config_loader 单元测试 |

### 修改文件（~15 个）

| 文件 | 改动类型 |
|------|----------|
| `update_next_day_review.py` | 标签配置驱动化 |
| `apply-accent-confirmations.py` | 语言条件化 |
| `validate-survival-speaking-cards.sh` | 字段名配置化 |
| 5 × `SKILL.md` | 路径更新 + 语言泛化描述 |
| 5 × `sync-to-global.sh` | 路径更新 |
| `系统配置/模板/单词卡模板.md` | 新增多态字段 |
| `系统配置/模板/录入模板索引.md` | 更新说明 |
| `学习系统/总训练.base` | formula 兼容化 |
| `AGENTS.md` | 入口点路径更新 |
| `README.md` | 结构说明更新 |
| `docs/HOWTO_ADD_NEW_LANGUAGE.md` | 与实现对齐 |

### 重命名目录

| 原路径 | 新路径 |
|--------|--------|
| `codex-skills/` | `agent-skills/` |
| `codex-skills/jp-listening-script-generator/` | `agent-skills/listening-script-generator/` |
| `codex-skills/jp-next-day-review-updater/` | `agent-skills/next-day-review-updater/` |
| `codex-skills/jp-review-material-maintainer/` | `agent-skills/review-material-maintainer/` |
| `codex-skills/jp-source-note-generator/` | `agent-skills/source-note-generator/` |
| `codex-skills/jp-survival-speaking-card-generator/` | `agent-skills/survival-speaking-card-generator/` |

---

## 执行顺序与依赖

```
Phase 0 (基础设施)
    │
    ├──→ Phase 1 (Frontmatter 语义)
    ├──→ Phase 2 (通用词汇脚本)
    ├──→ Phase 3 (配置驱动复习脚本)
    │
    └──→ Phase 4 (Agent Skills 重构)
              │
              └──→ Phase 5 (工具链更新)
                        │
                        └──→ Phase 6 (验证)
```

**关键依赖**：

- Phase 0 是所有后续阶段的前置条件
- Phase 1-3 可以在 Phase 0 完成后并行推进
- Phase 4 依赖 Phase 0（需要 config.json 驱动标签）
- Phase 5 依赖 Phase 0 + Phase 4
- Phase 6 是最后的验证阶段

---

## 验证方案

1. **单元测试**：运行所有现有测试，确保向后兼容
2. **config_loader 测试**：验证配置加载、默认值、错误处理
3. **vocab_note 测试**：验证字段回退逻辑（新字段优先，旧字段兼容）
4. **手动验证**：
   - 用现有日语 vault 运行 `update_next_day_review.py --dry-run`，确认输出不变
   - 检查所有 SKILL.md 路径引用是否正确
   - 检查 AGENTS.md 入口点是否正确指向新路径
