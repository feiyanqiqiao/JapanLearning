# LingoTrace 更新日志 (Changelog)

版本号规则：`年月日-时分秒`（如 `20260606-065513`）。
后续开始迭代本项目时，所有的功能演进、修复与架构变动都会记录于此。

---

## [20260610-V3-Multi-Language-Architecture-Code-Review-Fix]

### 修复 (Fixed)

#### P0 级架构违背修复
- **Bases 公式遗漏 `pronunciation` 字段**：更新 `学习系统/总训练.base` 的 `core_text` 公式，添加 `pronunciation`、`en_text` 字段支持
- **模板目录未实施双轨制隔离**：
  - 将现有模板移入 `系统配置/模板/jp/` 目录
  - 创建 `系统配置/模板/en/` 目录及英语专属模板
  - 英语模板包含：单词卡、课堂笔记、语法卡、录入模板索引、每日学习清单

#### P1 级执行遗漏修复
- **遗漏 CI 拦截防线工作流**：新增 `.github/workflows/multi-language-smoke.yml`
  - 支持 Python 3.10/3.11/3.12 矩阵测试
  - 运行所有单元测试
  - 验证 config.json schema
  - 验证模板目录结构
  - 验证 agent-skills 目录结构

---

## [20260610-V3-Multi-Language-Architecture]

### 新增 (Added)

#### Phase 0: 基础设施 — config.json + config_loader.py
- 新增 `系统配置/config.json` — 语言身份配置文件
- 新增 `tools/config_loader.py` — 统一配置加载模块
- 新增 `tools/tests/test_config_loader.py` — 配置加载器单元测试（21 个测试）

#### Phase 1: 统一 Frontmatter 语义
- 新增 `tools/vocab_note.py` — 统一词汇卡 frontmatter 操作模块
  - `normalize_reading()` — 读取 pronunciation，回退到 reading+accent_display
  - `normalize_variants()` — 读取 variants，回退到 kanji_diff_pairs
  - `build_reading()` — 根据语言构建 pronunciation 值
- 新增 `tools/tests/test_vocab_note.py` — vocab_note 单元测试（20 个测试）
- 更新 `系统配置/模板/单词卡模板.md` — 添加 `pronunciation` 和 `variants` 字段
- 更新 `系统配置/模板/录入模板索引.md` — 添加多语言兼容说明

#### Phase 2: 通用词汇脚本
- 新增 `tools/vocab_ops.py` — 语言无关的词汇卡操作模块
  - `VocabOps` 类 — 封装配置驱动的词汇操作
  - `get_vocab_tags()` — 生成语言无关的标签映射
  - `extract_label()` — 从 frontmatter 提取显示标签
  - `render_base_note()` — 渲染基础词汇卡
- 新增 `tools/__init__.py` — tools 包初始化文件
- 新增 `tools/tests/test_vocab_ops.py` — vocab_ops 单元测试（14 个测试）

### 变更 (Changed)

#### Phase 3: 配置驱动的复习脚本
- 更新 `agent-skills/next-day-review-updater/scripts/update_next_day_review.py`
  - 添加 `--config` 命令行参数
  - 使用 `config_loader` 加载语言配置
  - 标签前缀改为配置驱动（不再硬编码 `jp/`）
  - `extract_label()` 使用配置驱动的 `speaking_text_field`
  - `render_base_note()` 使用配置驱动的 `namespace`

#### Phase 4: Agent Skills 重构
- 目录重命名：
  - `codex-skills/` → `agent-skills/`
  - `jp-listening-script-generator/` → `listening-script-generator/`
  - `jp-next-day-review-updater/` → `next-day-review-updater/`
  - `jp-review-material-maintainer/` → `review-material-maintainer/`
  - `jp-source-note-generator/` → `source-note-generator/`
  - `jp-survival-speaking-card-generator/` → `survival-speaking-card-generator/`
- 更新所有 SKILL.md 文件（5 个）
- 更新所有 `sync-to-global.sh` 文件（5 个）
- 更新 `validate-survival-speaking-cards.sh`
- 更新 `AGENTS.md`

#### Phase 5: 工具链更新
- 更新 `agent-skills/review-material-maintainer/scripts/apply-accent-confirmations.py`
  - 从 config.json 读取 `pronunciation_system`
  - 非 `pitch_accent` 系统时跳过处理
- 更新 `学习系统/总训练.base`
  - `core_text` 公式添加 `fr_text` 回退支持
- 更新 `docs/HOWTO_ADD_NEW_LANGUAGE.md` — 与实际实现对齐
- 更新 `README.md` — 更新项目结构说明

---

## [20260606-065513]
### 新增 (Added)
- 创建了统一的版本更新文档（CHANGELOG.md）。
- 增加了产品与系统的详细白皮书文档（包含于 `docs/` 目录中）：
  - 功能模块与用户旅程审计报告
  - 产品需求与架构白皮书
  - 早期用户画像与自查问卷
  - 多语种与多 Agent 终端演进架构设计方案
- 更新了项目 README.md 简介与使用指南。
