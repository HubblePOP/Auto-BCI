# Built-in Classifier Program

## Goal

Verify that Auto-BCI can run a bounded task and produce auditable artifacts.

## Fixed Contract

- Task: binary classification on a tiny packaged table.
- Split: fixed train/test rows.
- Primary metric: accuracy.
- Runner: deterministic threshold baseline.
- Output: events, ledger, result, report, dashboard status.

## Promotion Rule

The run is accepted only when the fixed evaluator completes and accuracy is at
least `0.75`.
