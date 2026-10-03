from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


APPROACH_DIR = Path(__file__).resolve().parents[2]
PROJECT_ROOT = APPROACH_DIR.parent
if str(APPROACH_DIR) not in sys.path:
    sys.path.insert(0, str(APPROACH_DIR))

from path_config import cfg_run_dir  # noqa: E402


VERSION = "v4_7"


@dataclass(frozen=True)
class RepairRun:
    project: str
    ai: str
    run_id: str
    run_dir: Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Rerun v4_7 agent repair for existing runs in parallel.")
    parser.add_argument("--ai", default="deepseek")
    parser.add_argument("--projects", default="", help="Comma-separated project filter. Defaults to every project with repair_summary.json.")
    parser.add_argument("--run-ids", default="", help="Comma-separated run id filter.")
    parser.add_argument("--batch-name", default="", help="Output folder name under output/v4_7/batch_experiments.")
    parser.add_argument("--max-workers", type=int, default=6, help="Maximum concurrent repair processes.")
    parser.add_argument("--max-repair-attempts", type=int, default=6)
    parser.add_argument("--compile-timeout", type=int, default=60)
    parser.add_argument("--skip-compiled", action="store_true", help="Skip runs whose result compile summary has zero failed .cpp files.")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if args.max_workers < 1:
        parser.error("--max-workers must be >= 1")

    runs = _discover_runs(
        ai_name=args.ai,
        project_filter=_split_filter(args.projects),
        run_id_filter=_split_filter(args.run_ids),
        skip_compiled=args.skip_compiled,
    )
    batch_name = args.batch_name or datetime.now().strftime("%Y%m%d_%H%M%S_parallel_repair")
    batch_dir = PROJECT_ROOT / "output" / VERSION / "batch_experiments" / batch_name
    log_dir = batch_dir / "logs"
    batch_dir.mkdir(parents=True, exist_ok=True)
    log_dir.mkdir(parents=True, exist_ok=True)

    print(f"Runs: {len(runs)}")
    print(f"Max workers: {args.max_workers}")
    print(f"Batch dir: {batch_dir}")
    for run in runs:
        print(f"  {run.project} {run.run_id}")

    manifest_path = batch_dir / "manifest.json"
    _write_json(manifest_path, {"runs": [_run_manifest(run) for run in runs]})

    if args.dry_run:
        return 0

    rows = _run_parallel(
        runs=runs,
        log_dir=log_dir,
        max_workers=args.max_workers,
        max_repair_attempts=args.max_repair_attempts,
        compile_timeout=args.compile_timeout,
    )
    _write_outputs(rows, batch_dir / "summary.csv", batch_dir / "summary.json")
    print(f"Wrote summary to {batch_dir / 'summary.csv'}")
    return 0 if all(row.get("returncode") == 0 for row in rows) else 1


def _discover_runs(
    ai_name: str,
    project_filter: set[str],
    run_id_filter: set[str],
    skip_compiled: bool,
) -> list[RepairRun]:
    output_root = PROJECT_ROOT / "output" / VERSION
    runs: list[RepairRun] = []
    for summary_path in sorted(output_root.glob(f"*/{ai_name}/runs/*/review/repair_summary.json")):
        run_dir = summary_path.parents[1]
        run_id = run_dir.name
        project = run_dir.parents[2].name
        if project_filter and project not in project_filter:
            continue
        if run_id_filter and run_id not in run_id_filter:
            continue
        if skip_compiled and _compile_failed_count(run_dir) == 0:
            continue
        expected_run_dir = cfg_run_dir(ai_name, project, VERSION, run_id)
        if expected_run_dir.resolve() != run_dir.resolve():
            raise ValueError(f"Unexpected run path parse: {summary_path}")
        runs.append(RepairRun(project=project, ai=ai_name, run_id=run_id, run_dir=run_dir))
    return runs


def _run_parallel(
    runs: list[RepairRun],
    log_dir: Path,
    max_workers: int,
    max_repair_attempts: int,
    compile_timeout: int,
) -> list[dict[str, Any]]:
    pending = list(runs)
    active: list[dict[str, Any]] = []
    rows: list[dict[str, Any]] = []
    total = len(runs)

    while pending or active:
        while pending and len(active) < max_workers:
            run = pending.pop(0)
            active.append(_start_process(run, log_dir, max_repair_attempts, compile_timeout))
            print(f"Started [{len(rows) + len(active)}/{total}] {run.project} {run.run_id}")

        for item in list(active):
            proc: subprocess.Popen[str] = item["proc"]
            if proc.poll() is None:
                continue
            active.remove(item)
            row = _finish_process(item)
            rows.append(row)
            status = "ok" if row.get("returncode") == 0 else "failed"
            print(f"Finished [{len(rows)}/{total}] {row['project']} {row['run_id']} {status}")

        if active:
            time.sleep(1)

    return rows


def _start_process(
    run: RepairRun,
    log_dir: Path,
    max_repair_attempts: int,
    compile_timeout: int,
) -> dict[str, Any]:
    safe_name = _safe_name(f"{run.project}__{run.run_id}")
    stdout_path = log_dir / f"{safe_name}.stdout.log"
    stderr_path = log_dir / f"{safe_name}.stderr.log"
    stdout_file = stdout_path.open("w", encoding="utf-8", errors="replace")
    stderr_file = stderr_path.open("w", encoding="utf-8", errors="replace")
    command = [
        sys.executable,
        str(APPROACH_DIR / "main.py"),
        "--ai",
        run.ai,
        "--project",
        run.project,
        "--mode",
        "repair",
        "--run-id",
        run.run_id,
        "--apply-repair",
        "--max-repair-attempts",
        str(max_repair_attempts),
        "--compile-timeout",
        str(compile_timeout),
    ]
    start = time.monotonic()
    proc = subprocess.Popen(
        command,
        cwd=str(PROJECT_ROOT),
        stdout=stdout_file,
        stderr=stderr_file,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return {
        "run": run,
        "proc": proc,
        "start": start,
        "stdout_file": stdout_file,
        "stderr_file": stderr_file,
        "stdout_path": stdout_path,
        "stderr_path": stderr_path,
        "command": command,
    }


def _finish_process(item: dict[str, Any]) -> dict[str, Any]:
    item["stdout_file"].close()
    item["stderr_file"].close()
    proc: subprocess.Popen[str] = item["proc"]
    run: RepairRun = item["run"]
    elapsed = round(time.monotonic() - item["start"], 2)
    return {
        "project": run.project,
        "ai": run.ai,
        "run_id": run.run_id,
        "returncode": proc.returncode,
        "elapsed_seconds": elapsed,
        "result_cpp_total": _compile_field(run.run_dir, "total_count"),
        "result_cpp_success": _compile_field(run.run_dir, "success_count"),
        "result_cpp_failed": _compile_field(run.run_dir, "failed_count"),
        "result_cpp_success_rate": _compile_field(run.run_dir, "success_rate"),
        "repair_total_failed_files": _repair_field(run.run_dir, "total_failed_files"),
        "repair_repaired_count": _repair_field(run.run_dir, "repaired_count"),
        "repair_failed_count": _repair_field(run.run_dir, "failed_count"),
        "repair_order": ";".join(_repair_field(run.run_dir, "repair_order") or []),
        "failed_files_after_repair": ";".join(_failed_files(run.run_dir)),
        "stdout_log": str(item["stdout_path"]),
        "stderr_log": str(item["stderr_path"]),
        "command": " ".join(item["command"]),
    }


def _compile_failed_count(run_dir: Path) -> int:
    cpp_failed = int(_compile_field(run_dir, "failed_count") or 0)
    header_data = _load_json(run_dir / "result" / "compile_report" / "header_compile_summary.json")
    header_failed = int(header_data.get("failed_count", 0)) if header_data else 0
    return cpp_failed + header_failed


def _compile_field(run_dir: Path, field: str) -> Any:
    data = _load_json(run_dir / "result" / "compile_report" / "cpp_compile_summary.json")
    if not data:
        return ""
    return data.get(field, "")


def _repair_field(run_dir: Path, field: str) -> Any:
    data = _load_json(run_dir / "review" / "repair_summary.json")
    if not data:
        return ""
    return data.get(field, "")


def _failed_files(run_dir: Path) -> list[str]:
    data = _load_json(run_dir / "result" / "compile_report" / "cpp_compile_summary.json")
    if not data:
        return []
    return [item.get("file", "") for item in data.get("results", []) if not item.get("success") and item.get("file")]


def _load_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _write_outputs(rows: list[dict[str, Any]], csv_path: Path, json_path: Path) -> None:
    fields = [
        "project",
        "ai",
        "run_id",
        "returncode",
        "elapsed_seconds",
        "result_cpp_total",
        "result_cpp_success",
        "result_cpp_failed",
        "result_cpp_success_rate",
        "repair_total_failed_files",
        "repair_repaired_count",
        "repair_failed_count",
        "repair_order",
        "failed_files_after_repair",
        "stdout_log",
        "stderr_log",
        "command",
    ]
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})
    _write_json(json_path, {"rows": rows})


def _write_json(path: Path, data: dict[str, Any]) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _split_filter(value: str) -> set[str]:
    return {item.strip() for item in value.split(",") if item.strip()}


def _safe_name(value: str) -> str:
    return "".join(ch if ch.isalnum() or ch in "._-" else "_" for ch in value)


def _run_manifest(run: RepairRun) -> dict[str, str]:
    return {
        "project": run.project,
        "ai": run.ai,
        "run_id": run.run_id,
        "run_dir": str(run.run_dir),
    }


if __name__ == "__main__":
    raise SystemExit(main())
