---
name: autobci-harness
description: Use Auto-BCI as a local harness for verifiable agent research loops.
---

# Auto-BCI Harness Skill

Auto-BCI is a harness, not a replacement for your coding agent.

## First Checks

1. Read `AGENTS.md`.
2. Run `autobci doctor --json` when setup or runtime health matters.
3. Run `autobci status --json` before making claims about current state.
4. Prefer JSON output when available.

## Working Model

Use the coding agent for:

- reading files
- editing code
- running commands
- comparing diffs
- explaining changes

Use Auto-BCI for:

- task contracts
- fixed evaluation
- ledger and report artifacts
- dashboard projection
- reproducible run records

## Boundaries

Never bypass Auto-BCI's verification boundary:

- do not edit generated `.autobci/` artifacts by hand
- do not change the primary metric silently
- do not change the fixed split silently
- do not claim progress from chat memory when artifacts exist

## Result Reporting

When summarizing a result, state:

- what command ran
- what artifact proves it
- whether the result is selected, a candidate, or only a smoke result
- what risks remain
- the next action
