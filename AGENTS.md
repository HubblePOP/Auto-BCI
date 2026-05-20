# Agent Instructions

Auto-BCI is a local harness for verifiable agent research loops.

Use your coding-agent abilities for reading files, editing code, running commands,
and explaining diffs. Use Auto-BCI for task contracts, fixed evaluation, ledger
events, reports, dashboard projection, and reproducible artifacts.

Rules:

1. Run `autobci doctor --json` before setup claims.
2. Run `autobci status --json` before current-state claims.
3. Do not edit generated run artifacts under `.autobci/` by hand.
4. Do not change a task contract, primary metric, or split silently.
5. Summarize results from `result.json`, `ledger.jsonl`, and `report.md`, not
   from chat memory.
6. Treat external coding agents as execution surfaces. Auto-BCI owns the fixed
   evaluator and audit trail.
