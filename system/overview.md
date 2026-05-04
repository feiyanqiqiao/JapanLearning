---
title: 总训练入口
tags:
  - jp/system
  - jp/dashboard
---

# 总训练入口

> [!note]
> 每天先打开这一页，再进入各条训练线。默认顺序：
> 1. 课堂复习
> 2. 生活口语
> 3. 听力精听
> 4. 发音录音与回听
> 5. 当天复盘

## 今日节奏

- 15 分钟：课堂复习
- 15 分钟：生活口语句库
- 20 分钟：听力精听
- 15 分钟：发音录音与回听
- 5 分钟：当天标记与复盘

## 录入与维护

- 新课笔记继续放在 `daily-notes/`
- 新条目优先从 [[学习系统/模板/录入模板索引]] 复制
- 每天收口可直接复制 [[学习系统/模板/每日学习清单模板]] 到当天笔记
- 总面板文件在 [[学习系统/面板/总训练.base]]
- 词汇双层规则见 [[学习系统/词库/词汇双层说明]]
- 基础词库浏览面板见 [[学习系统/词库/基础词汇.base]]
- アクセント独立训练区见 [[学习系统/发音/アクセント/アクセント训练入口]]
- 音素独立训练区见 [[学习系统/发音/音素/音素训练入口]]
- `done_today` 可以临时勾选，帮助你在当天训练时做手工标记
- 每天收口时运行 `zsh codex-skills/jp-next-day-review-updater/scripts/run-next-day-review-update.sh --date YYYY-MM-DD --dry-run` 先检查；确认无误后去掉 `--dry-run` 推进已完成条目
- 收口脚本只处理 `status: active` 且 `done_today: true` 的条目，并把 `last_reviewed / review_stage / next_review` 往前推进，把 `done_today` 清回 `false`
- `今日总训练` 现在按 `last_reviewed / next_review` 判断今天是否还需要出现；`done_today` 只负责临时勾选

## 复习曲线

统一曲线：

`day0 -> day1 -> day3 -> day7 -> day14 -> day30 -> day90 -> day180 -> mastered`

正常推进：

- `day0` 完成后：`next_review = 完成日 + 1`
- `day1` 完成后：`next_review = 完成日 + 3`
- `day3` 完成后：`next_review = 完成日 + 7`
- `day7` 完成后：`next_review = 完成日 + 14`
- `day14` 完成后：`next_review = 完成日 + 30`
- `day30` 完成后：`next_review = 完成日 + 90`
- `day90` 完成后：`next_review = 完成日 + 180`
- `day180` 完成后：`status = mastered`，`next_review = ""`

延迟规则：

- `overdue_days = 完成日 - 原 next_review`
- `allowed_delay = max(1, 当前阶段天数)`
- 如果 `overdue_days <= allowed_delay`，升到下一阶段
- 如果 `overdue_days > allowed_delay`，不升阶，保持原 `review_stage`，并重新排到 `完成日 + allowed_delay`

> [!warning]
> Obsidian 官方帮助确认 `Bases` 支持多字段排序，但公开的 `.base` 语法没有写出排序键名。
> 请在 [[学习系统/面板/总训练.base]] 的 `Sort` 菜单里按下面顺序保存一次：
> `first_seen` 新到旧 → `formula.priority_rank` 升序 → `next_review` 旧到新 → `error_count` 大到小 → `seen_count` 大到小

## 今日总训练

![[学习系统/面板/总训练.base#今日总训练]]

## 课堂高风险

![[学习系统/面板/总训练.base#课堂高风险]]

## 生活口语待练

![[学习系统/面板/总训练.base#生活口语待练]]

## 听力待精听

![[学习系统/面板/总训练.base#听力待精听]]

## 发音待录音

![[学习系统/面板/总训练.base#发音待录音]]

## アクセント待练

![[学习系统/面板/总训练.base#アクセント待练]]

## 音素待练

![[学习系统/面板/总训练.base#音素待练]]

## 最近新增

![[学习系统/面板/总训练.base#最近新增]]

## 重复出现 / 反复出错

![[学习系统/面板/总训练.base#重复出现 / 反复出错]]
