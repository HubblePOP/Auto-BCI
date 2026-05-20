# Auto-BCI

[English](README.md) | [简体中文](README.zh-CN.md)

A local harness for verifiable agent research loops.

Auto-BCI lets coding agents work inside bounded tasks, then verifies the work
with fixed evaluators, ledgers, reports, and reproducible artifacts. The first
public MVP is deliberately small: one built-in classifier task, a JSON-first CLI,
local artifacts, and a dashboard projection.

## Language

GitHub opens `README.md` by default, so the English version is the landing page.
Open [README.zh-CN.md](README.zh-CN.md) for the simplified Chinese version.

This switch is for documentation only. The MVP CLI and dashboard are still kept
minimal and may not translate every runtime label yet.

## Install

Requires Python 3.10 or newer.

```bash
git clone https://github.com/HubblePOP/Auto-BCI.git
cd Auto-BCI
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
```

## Quick Start

```bash
autobci doctor --json
autobci status --json
autobci run --task builtin-classifier --json
autobci report latest
autobci dashboard --host 127.0.0.1 --port 8878
```

The built-in task requires no model key and no external coding agent. It writes
all local run artifacts under `.autobci/`, which is ignored by Git.

## What The MVP Proves

- A task has a fixed contract.
- A runner executes against a fixed train/test split.
- An evaluator writes deterministic metrics.
- A ledger records each important step.
- A report and dashboard summarize recorded artifacts.
- External coding agents can be connected later without becoming the source of
  truth for task state or evaluation.

## Artifact Layout

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

## Agent Usage

Coding agents should read `AGENTS.md` and `.agents/skills/autobci-harness/SKILL.md`.
They may edit project code, run commands, and inspect diffs. They must not bypass
Auto-BCI's task contract, fixed evaluator, ledger, report, or artifact trail.

## Development Checks

```bash
python -m pytest -q
git diff --check
```
