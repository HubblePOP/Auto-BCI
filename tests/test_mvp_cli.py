from __future__ import annotations

import io
import json
from contextlib import redirect_stdout
from pathlib import Path

from autobci_harness.cli import build_parser, main


def _run_cli(args: list[str]) -> tuple[int, str]:
    stream = io.StringIO()
    with redirect_stdout(stream):
        code = main(args)
    return int(code), stream.getvalue()


def test_doctor_and_status_are_json_first(tmp_path: Path) -> None:
    code, output = _run_cli(["--repo-root", str(tmp_path), "doctor", "--json"])
    assert code == 0
    doctor = json.loads(output)
    assert doctor["ok"] is True
    assert doctor["checks"]["python"]["ok"] is True
    assert doctor["checks"]["writable_workspace"]["ok"] is True

    code, output = _run_cli(["--repo-root", str(tmp_path), "status", "--json"])
    assert code == 0
    status = json.loads(output)
    assert status["ok"] is True
    assert status["latest_run"] is None
    assert status["artifact_root"].endswith(".autobci")


def test_builtin_classifier_run_writes_verifiable_artifacts(tmp_path: Path) -> None:
    code, output = _run_cli(
        [
            "--repo-root",
            str(tmp_path),
            "run",
            "--task",
            "builtin-classifier",
            "--json",
        ]
    )
    assert code == 0
    payload = json.loads(output)
    assert payload["ok"] is True
    assert payload["task_id"] == "builtin-classifier"
    assert payload["primary_metric"] == "accuracy"
    assert payload["metrics"]["accuracy"] == 1.0

    run_dir = Path(payload["run_dir"])
    assert (run_dir / "events.jsonl").exists()
    assert (run_dir / "ledger.jsonl").exists()
    assert (run_dir / "result.json").exists()
    assert (run_dir / "report.md").exists()

    result = json.loads((run_dir / "result.json").read_text(encoding="utf-8"))
    assert result["selected_result"]["kind"] == "selected"
    assert result["per_run_best_result"]["kind"] == "per_run_best"
    assert result["promotion"]["decision"] == "accepted"

    ledger_rows = [
        json.loads(line)
        for line in (run_dir / "ledger.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert [row["event_type"] for row in ledger_rows] == [
        "program_loaded",
        "runner_completed",
        "evaluation_completed",
        "judgment_completed",
    ]

    dashboard_status = json.loads((tmp_path / ".autobci" / "dashboard" / "status.json").read_text(encoding="utf-8"))
    assert dashboard_status["latest_run"]["run_id"] == payload["run_id"]
    assert dashboard_status["latest_run"]["artifact_refs"]["report"].endswith("report.md")


def test_report_latest_reads_latest_run(tmp_path: Path) -> None:
    _run_cli(["--repo-root", str(tmp_path), "run", "--task", "builtin-classifier", "--json"])

    code, output = _run_cli(["--repo-root", str(tmp_path), "report", "latest"])
    assert code == 0
    assert "# Built-in Classifier Report" in output
    assert "accuracy: 1.000" in output
    assert "ledger.jsonl" in output


def test_dashboard_accepts_host_and_port_after_subcommand() -> None:
    args = build_parser().parse_args(["dashboard", "--host", "127.0.0.1", "--port", "8878"])
    assert args.command == "dashboard"
    assert args.host == "127.0.0.1"
    assert args.port == 8878
