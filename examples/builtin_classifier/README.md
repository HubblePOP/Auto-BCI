# Built-in Classifier Example

This example is intentionally tiny. It exists to verify the public MVP loop:

```text
task contract -> deterministic runner -> fixed evaluator -> ledger -> report
```

Run it with:

```bash
autobci run --task builtin-classifier --json
autobci report latest
```
