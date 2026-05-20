# Auto-BCI

[English](README.md) | [简体中文](README.zh-CN.md)

一个给 coding agent 使用的本地可验证研究闭环 harness。

Auto-BCI 让 coding agent 在有边界的任务里工作，然后用固定评估器、ledger、报告和可复现产物验证结果。当前公开 MVP 刻意保持很小：一个内置分类小基准、JSON-first CLI、本地产物和 dashboard 状态投影。

## 语言切换

GitHub 默认打开 `README.md`，所以英文版是仓库首页。

如果要看中文版，打开 [README.zh-CN.md](README.zh-CN.md)。如果要切回英文版，打开 [README.md](README.md)。

这只是文档语言切换，不表示 MVP 的 CLI 和 dashboard 已经完成完整界面翻译。当前运行界面优先保持最小、稳定、可验证。

## 安装

需要 Python 3.10 或更新版本。

```bash
git clone https://github.com/HubblePOP/Auto-BCI.git
cd Auto-BCI
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
```

## 快速开始

```bash
autobci doctor --json
autobci status --json
autobci run --task builtin-classifier --json
autobci report latest
autobci dashboard --host 127.0.0.1 --port 8878
```

内置任务不需要模型 key，也不需要外部 coding agent。所有本地运行产物都会写到 `.autobci/`，这个目录已被 Git 忽略。

## MVP 验证什么

- 任务有固定契约。
- runner 在固定 train/test 数据划分上执行。
- evaluator 写出确定性指标。
- ledger 记录关键步骤。
- report 和 dashboard 从记录产物里汇总状态。
- 外部 coding agent 后续可以接入，但不会成为任务状态或评估结果的真源。

## 产物目录

```text
.autobci/
  latest_run.json
  dashboard/status.json
  runs/<run_id>/
    events.jsonl
    ledger.jsonl
    result.json
    report.md
```

## Agent 使用方式

Coding agent 应先读取 `AGENTS.md` 和 `.agents/skills/autobci-harness/SKILL.md`。

它可以读文件、改代码、跑命令、检查 diff；但不能绕过 Auto-BCI 的任务契约、固定评估器、ledger、report 和 artifact 证据链。

## 开发检查

```bash
python -m pytest -q
git diff --check
```
