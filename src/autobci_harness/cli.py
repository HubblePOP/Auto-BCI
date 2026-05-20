from __future__ import annotations

import argparse
import csv
import json
import sys
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from importlib import resources
from pathlib import Path
from typing import Any

from . import __version__


TASK_ID = "builtin-classifier"
PRIMARY_METRIC = "accuracy"


@dataclass(frozen=True)
class Row:
    split: str
    feature_a: float
    feature_b: float
    label: int


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def repo_root_from(value: str | None) -> Path:
    return Path(value).expanduser().resolve() if value else Path.cwd().resolve()


def artifact_root(repo_root: Path) -> Path:
    return repo_root / ".autobci"


def runs_root(repo_root: Path) -> Path:
    return artifact_root(repo_root) / "runs"


def latest_run_path(repo_root: Path) -> Path:
    return artifact_root(repo_root) / "latest_run.json"


def dashboard_status_path(repo_root: Path) -> Path:
    return artifact_root(repo_root) / "dashboard" / "status.json"


def read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return default


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp.replace(path)


def append_jsonl(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False) + "\n")


def load_builtin_rows() -> list[Row]:
    with resources.files("autobci_harness").joinpath("fixtures/builtin_classifier.csv").open(
        "r",
        encoding="utf-8",
        newline="",
    ) as handle:
        reader = csv.DictReader(handle)
        return [
            Row(
                split=str(item["split"]),
                feature_a=float(item["feature_a"]),
                feature_b=float(item["feature_b"]),
                label=int(item["label"]),
            )
            for item in reader
        ]


def predict(row: Row) -> int:
    return 1 if row.feature_a >= 0.5 else 0


def confusion_matrix(rows: list[Row]) -> dict[str, int]:
    counts = {"tp": 0, "tn": 0, "fp": 0, "fn": 0}
    for row in rows:
        pred = predict(row)
        if pred == 1 and row.label == 1:
            counts["tp"] += 1
        elif pred == 0 and row.label == 0:
            counts["tn"] += 1
        elif pred == 1 and row.label == 0:
            counts["fp"] += 1
        else:
            counts["fn"] += 1
    return counts


def evaluate(rows: list[Row]) -> dict[str, Any]:
    test_rows = [row for row in rows if row.split == "test"]
    if not test_rows:
        raise ValueError("Built-in fixture has no test rows.")
    correct = sum(1 for row in test_rows if predict(row) == row.label)
    accuracy = correct / len(test_rows)
    return {
        "accuracy": accuracy,
        "correct": correct,
        "total": len(test_rows),
        "confusion_matrix": confusion_matrix(test_rows),
    }


def event(event_type: str, **payload: Any) -> dict[str, Any]:
    return {"created_at": utc_now(), "event_type": event_type, **payload}


def build_report(result: dict[str, Any]) -> str:
    artifacts = result["artifact_refs"]
    metrics = result["metrics"]
    promotion = result["promotion"]
    return "\n".join(
        [
            "# Built-in Classifier Report",
            "",
            f"- run_id: {result['run_id']}",
            f"- task_id: {result['task_id']}",
            f"- primary_metric: {result['primary_metric']}",
            f"- accuracy: {metrics['accuracy']:.3f}",
            f"- decision: {promotion['decision']}",
            f"- reason: {promotion['reason']}",
            "",
            "## Artifacts",
            "",
            f"- events: {artifacts['events']}",
            f"- ledger: {artifacts['ledger']}",
            f"- result: {artifacts['result']}",
            f"- report: {artifacts['report']}",
            "",
        ]
    )


def run_builtin_classifier(repo_root: Path) -> dict[str, Any]:
    rows = load_builtin_rows()
    run_id = f"{TASK_ID}-{int(time.time())}"
    run_dir = runs_root(repo_root) / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    events_path = run_dir / "events.jsonl"
    ledger_path = run_dir / "ledger.jsonl"
    result_path = run_dir / "result.json"
    report_path = run_dir / "report.md"

    artifacts = {
        "events": str(events_path),
        "ledger": str(ledger_path),
        "result": str(result_path),
        "report": str(report_path),
    }
    program = {
        "task_id": TASK_ID,
        "task_type": "classification_binary",
        "primary_metric": PRIMARY_METRIC,
        "split_policy": "fixed packaged train/test split",
        "runner": "feature_a_threshold_baseline",
    }
    metrics = evaluate(rows)
    promotion = {
        "decision": "accepted" if metrics[PRIMARY_METRIC] >= 0.75 else "rejected",
        "reason": "Fixed evaluator completed and passed the acceptance threshold."
        if metrics[PRIMARY_METRIC] >= 0.75
        else "Fixed evaluator completed below the acceptance threshold.",
        "threshold": 0.75,
    }
    trace = [
        event("program_loaded", program=program),
        event("runner_completed", runner=program["runner"], train_rows=sum(1 for row in rows if row.split == "train")),
        event("evaluation_completed", metrics=metrics),
        event("judgment_completed", promotion=promotion),
    ]
    for item in trace:
        append_jsonl(events_path, item)
        append_jsonl(ledger_path, item)

    result = {
        "ok": True,
        "run_id": run_id,
        "run_dir": str(run_dir),
        "task_id": TASK_ID,
        "task_type": "classification_binary",
        "primary_metric": PRIMARY_METRIC,
        "program": program,
        "metrics": metrics,
        "selected_result": {"kind": "selected", "metric": PRIMARY_METRIC, "value": metrics[PRIMARY_METRIC]},
        "per_run_best_result": {"kind": "per_run_best", "metric": PRIMARY_METRIC, "value": metrics[PRIMARY_METRIC]},
        "promotion": promotion,
        "artifact_refs": artifacts,
        "created_at": utc_now(),
    }
    write_json(result_path, result)
    report_path.write_text(build_report(result), encoding="utf-8")

    latest = {
        "ok": True,
        "latest_run": {
            "run_id": run_id,
            "task_id": TASK_ID,
            "primary_metric": PRIMARY_METRIC,
            "metrics": metrics,
            "promotion": promotion,
            "artifact_refs": artifacts,
            "created_at": result["created_at"],
        },
        "artifact_root": str(artifact_root(repo_root)),
    }
    write_json(latest_run_path(repo_root), latest)
    write_json(dashboard_status_path(repo_root), latest)
    return result


def build_doctor_report(repo_root: Path) -> dict[str, Any]:
    root = artifact_root(repo_root)
    writable = True
    message = "ok"
    try:
        root.mkdir(parents=True, exist_ok=True)
        probe = root / ".write_probe"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink()
    except OSError as exc:
        writable = False
        message = str(exc)
    return {
        "ok": writable,
        "version": __version__,
        "repo_root": str(repo_root),
        "artifact_root": str(root),
        "checks": {
            "python": {"ok": sys.version_info >= (3, 10), "version": sys.version.split()[0]},
            "writable_workspace": {"ok": writable, "message": message},
            "builtin_task": {"ok": True, "task_id": TASK_ID},
        },
    }


def build_status(repo_root: Path) -> dict[str, Any]:
    latest = read_json(latest_run_path(repo_root), {})
    latest_run = latest.get("latest_run") if isinstance(latest, dict) else None
    return {
        "ok": True,
        "version": __version__,
        "repo_root": str(repo_root),
        "artifact_root": str(artifact_root(repo_root)),
        "latest_run": latest_run if isinstance(latest_run, dict) else None,
    }


def print_json(payload: Any) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def latest_report(repo_root: Path) -> tuple[int, str]:
    status = build_status(repo_root)
    latest_run = status.get("latest_run")
    if not isinstance(latest_run, dict):
        return 1, "No latest run found. Run `autobci run --task builtin-classifier --json` first."
    refs = latest_run.get("artifact_refs") if isinstance(latest_run.get("artifact_refs"), dict) else {}
    report = Path(str(refs.get("report") or ""))
    if not report.exists():
        return 1, f"Latest report is missing: {report}"
    return 0, report.read_text(encoding="utf-8")


class DashboardHandler(SimpleHTTPRequestHandler):
    repo_root: Path
    dashboard_root: Path

    def translate_path(self, path: str) -> str:
        clean = path.split("?", 1)[0].split("#", 1)[0]
        if clean in {"", "/", "/index.html"}:
            return str(self.dashboard_root / "index.html")
        return str(self.dashboard_root / clean.lstrip("/"))

    def do_GET(self) -> None:  # noqa: N802
        clean = self.path.split("?", 1)[0].split("#", 1)[0]
        if clean == "/status.json":
            payload = read_json(dashboard_status_path(self.repo_root), build_status(self.repo_root))
            body = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        super().do_GET()


def serve_dashboard(repo_root: Path, host: str, port: int) -> int:
    dashboard_root = Path(__file__).resolve().parents[2] / "dashboard"
    if not dashboard_status_path(repo_root).exists():
        write_json(dashboard_status_path(repo_root), build_status(repo_root))

    handler = type(
        "BoundDashboardHandler",
        (DashboardHandler,),
        {"repo_root": repo_root, "dashboard_root": dashboard_root},
    )
    server = ThreadingHTTPServer((host, port), handler)
    url = f"http://{host}:{port}/"
    print(f"Auto-BCI dashboard running at {url}")
    print("Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nDashboard stopped.")
    finally:
        server.server_close()
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="autobci")
    parser.add_argument("--repo-root", default=None)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8878)
    subparsers = parser.add_subparsers(dest="command")

    doctor = subparsers.add_parser("doctor")
    doctor.add_argument("--json", action="store_true")

    status = subparsers.add_parser("status")
    status.add_argument("--json", action="store_true")

    run = subparsers.add_parser("run")
    run.add_argument("--task", default=TASK_ID)
    run.add_argument("--json", action="store_true")

    report = subparsers.add_parser("report")
    report_sub = report.add_subparsers(dest="report_action", required=True)
    report_sub.add_parser("latest")

    dashboard = subparsers.add_parser("dashboard")
    dashboard.add_argument("--host", default=None)
    dashboard.add_argument("--port", type=int, default=None)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    repo_root = repo_root_from(args.repo_root)

    if args.command == "doctor":
        payload = build_doctor_report(repo_root)
        if args.json:
            print_json(payload)
        else:
            print(f"Auto-BCI doctor: {'ok' if payload['ok'] else 'failed'}")
        return 0 if payload["ok"] else 1

    if args.command == "status":
        payload = build_status(repo_root)
        if args.json:
            print_json(payload)
        else:
            latest = payload.get("latest_run")
            print(f"Auto-BCI status: latest_run={latest.get('run_id') if isinstance(latest, dict) else '-'}")
        return 0

    if args.command == "run":
        if args.task != TASK_ID:
            print(f"Unknown task: {args.task}")
            return 2
        payload = run_builtin_classifier(repo_root)
        if args.json:
            print_json(payload)
        else:
            print(f"Run complete: {payload['run_id']} accuracy={payload['metrics']['accuracy']:.3f}")
        return 0

    if args.command == "report" and args.report_action == "latest":
        code, text = latest_report(repo_root)
        print(text)
        return code

    if args.command == "dashboard":
        host = args.host or "127.0.0.1"
        port = args.port or 8878
        return serve_dashboard(repo_root, host, port)

    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
