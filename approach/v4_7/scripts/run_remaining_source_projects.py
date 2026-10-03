from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any


APPROACH_DIR = Path(__file__).resolve().parents[2]
PROJECT_ROOT = APPROACH_DIR.parent
if str(APPROACH_DIR) not in sys.path:
    sys.path.insert(0, str(APPROACH_DIR))

from path_config import cfg_all_project_names, cfg_run_dir  # noqa: E402


VERSION = "v4_7"
DEFAULT_EXISTING_PROJECTS = {
    "BulkheadBuilder",
    "CircuitBreakerExecutor",
    "Cookie",
    "DebugLogExceptionModule",
    "FailurePolicy",
    "JSONParser",
    "OrGroupFilter",
    "PerMessageDeflateExtensionTest",
    "ProgressPrinter",
    "ReadRowHolder",
}


def main() -> int:
    """解析参数并依次运行剩余源项目。

    返回:
        批次执行与摘要写入完成时返回 0。
    """
    parser = argparse.ArgumentParser(description="Run v4_7 full translation/repair experiments for source_projects.")
    parser.add_argument("--ai", default="deepseek")
    parser.add_argument("--projects", default="", help="Comma-separated project names. Defaults to source_projects minus existing v4_7 projects.")
    parser.add_argument("--include-existing", action="store_true", help="Run all source_projects instead of excluding existing v4_7 experiments.")
    parser.add_argument("--run-prefix", default="", help="Shared run id prefix. Defaults to batch timestamp.")
    parser.add_argument("--header-batch-size", type=int, default=3)
    parser.add_argument("--max-repair-attempts", type=int, default=6)
    parser.add_argument("--compile-timeout", type=int, default=60)
    parser.add_argument("--repair-test-suites", default="base", metavar="SUITES", help="repair 测试套件：base 或 base,additional")
    parser.add_argument("--allow-header-failures", action="store_true", help="Continue full pipeline when header translation does not converge.")
    parser.add_argument("--skip-existing-success", action="store_true", help="Skip project if this batch summary already marks it completed.")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    projects = _select_projects(args.projects, include_existing=args.include_existing)
    run_prefix = args.run_prefix or datetime.now().strftime("%Y%m%d_%H%M%S_remaining")
    summary_dir = PROJECT_ROOT / "output" / VERSION / "batch_experiments" / run_prefix
    summary_dir.mkdir(parents=True, exist_ok=True)
    csv_path = summary_dir / "summary.csv"
    json_path = summary_dir / "summary.json"

    existing_summary = _load_existing_summary(json_path) if args.skip_existing_success else {}
    rows: list[dict[str, Any]] = []

    print(f"Projects: {projects}")
    print(f"Run prefix: {run_prefix}")
    print(f"Summary: {summary_dir}")
    if args.dry_run:
        return 0

    for index, project_name in enumerate(projects, start=1):
        if existing_summary.get(project_name, {}).get("status") == "completed":
            print(f"[{index}/{len(projects)}] Skip completed {project_name}")
            rows.append(existing_summary[project_name])
            continue

        run_id = f"{run_prefix}_{index:02d}_{project_name}"
        print(f"[{index}/{len(projects)}] Running {project_name} with run_id={run_id}")
        row = _run_project(
            ai_name=args.ai,
            project_name=project_name,
            run_id=run_id,
            header_batch_size=args.header_batch_size,
            max_repair_attempts=args.max_repair_attempts,
            compile_timeout=args.compile_timeout,
            allow_header_failures=args.allow_header_failures,
            repair_test_suites=args.repair_test_suites,
        )
        rows.append(row)
        _write_outputs(rows, csv_path, json_path)

    _write_outputs(rows, csv_path, json_path)
    print(f"Wrote summary to {csv_path}")
    return 0


def _select_projects(projects_arg: str, include_existing: bool) -> list[str]:
    if projects_arg.strip():
        return [item.strip() for item in projects_arg.split(",") if item.strip()]
    projects = cfg_all_project_names(VERSION)
    if include_existing:
        return projects
    return [project for project in projects if project not in DEFAULT_EXISTING_PROJECTS]


def _run_project(
    ai_name: str,
    project_name: str,
    run_id: str,
    header_batch_size: int,
    max_repair_attempts: int,
    compile_timeout: int,
    allow_header_failures: bool,
    repair_test_suites: str,
) -> dict[str, Any]:
    """运行一个完整翻译项目并收集阶段结果。

    参数:
        ai_name: 模型名称。
        project_name: 项目名称。
        run_id: 本次运行 ID。
        header_batch_size: Header 批大小。
        max_repair_attempts: 单个 repair 目标的最大编译尝试次数。
        compile_timeout: 单次编译超时秒数。
        allow_header_failures: 是否允许 Header 未收敛后继续。
        repair_test_suites: repair 阶段使用的功能测试套件。

    返回:
        包含进程状态、编译及 repair 指标的项目摘要。
    """
    start = time.monotonic()
    command = [
        sys.executable,
        str(APPROACH_DIR / "main.py"),
        "--ai",
        ai_name,
        "--project",
        project_name,
        "--mode",
        "full",
        "--run-id",
        run_id,
        "--header-batch-size",
        str(header_batch_size),
        "--repair-after-compile",
        "--apply-repair",
        "--max-repair-attempts",
        str(max_repair_attempts),
        "--compile-timeout",
        str(compile_timeout),
        "--repair-test-suites",
        repair_test_suites,
    ]
    if allow_header_failures:
        command.append("--allow-header-failures")

    run_root = cfg_run_dir(ai_name, project_name, VERSION, run_id)
    result_dir = run_root / "result"
    review_dir = run_root / "review"
    proc = subprocess.run(
        command,
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    elapsed = round(time.monotonic() - start, 2)
    log_dir = PROJECT_ROOT / "output" / VERSION / "batch_experiments" / run_id
    log_dir.mkdir(parents=True, exist_ok=True)
    (log_dir / "stdout.log").write_text(proc.stdout or "", encoding="utf-8")
    (log_dir / "stderr.log").write_text(proc.stderr or "", encoding="utf-8")

    result_compile = _load_json(result_dir / "compile_report" / "cpp_compile_summary.json")
    review_repair = _load_json(review_dir / "repair_summary.json")
    review_compile = _load_json(review_dir / "compile_report" / "cpp_compile_summary.json")
    header_failure = _load_json(result_dir / "header_failure_report" / "header_failure_summary.json")

    return {
        "project": project_name,
        "ai": ai_name,
        "run_id": run_id,
        "status": "completed" if proc.returncode == 0 else "failed",
        "returncode": proc.returncode,
        "elapsed_seconds": elapsed,
        "result_cpp_total": _get(result_compile, "total_count"),
        "result_cpp_success": _get(result_compile, "success_count"),
        "result_cpp_failed": _get(result_compile, "failed_count"),
        "result_cpp_success_rate": _get(result_compile, "success_rate"),
        "repair_total_failed_files": _get(review_repair, "total_failed_files"),
        "repair_repaired_count": _get(review_repair, "repaired_count"),
        "repair_failed_count": _get(review_repair, "failed_count"),
        "review_cpp_total": _get(review_compile, "total_count"),
        "review_cpp_success": _get(review_compile, "success_count"),
        "review_cpp_failed": _get(review_compile, "failed_count"),
        "review_cpp_success_rate": _get(review_compile, "success_rate"),
        "failed_files_after_repair": _failed_files(review_compile),
        "header_failed_count": len(header_failure.get("failed_headers", [])) if header_failure else "",
        "failed_headers": _failed_headers_from_header_report(header_failure),
        "header_failure_report": str(result_dir / "header_failure_report" / "header_failure_summary.json") if header_failure else "",
        "stdout_log": str(log_dir / "stdout.log"),
        "stderr_log": str(log_dir / "stderr.log"),
    }


def _load_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _load_existing_summary(path: Path) -> dict[str, dict[str, Any]]:
    data = _load_json(path)
    if not data:
        return {}
    return {row.get("project", ""): row for row in data.get("rows", []) if row.get("project")}


def _get(data: dict[str, Any] | None, key: str) -> Any:
    if data is None:
        return ""
    return data.get(key, "")


def _failed_files(compile_summary: dict[str, Any] | None) -> str:
    if not compile_summary:
        return ""
    files = [item.get("file", "") for item in compile_summary.get("results", []) if not item.get("success")]
    return ";".join(file for file in files if file)


def _failed_headers_from_header_report(header_failure: dict[str, Any] | None) -> str:
    if not header_failure:
        return ""
    headers = [item.get("header", "") for item in header_failure.get("failed_headers", [])]
    return ";".join(header for header in headers if header)


def _write_outputs(rows: list[dict[str, Any]], csv_path: Path, json_path: Path) -> None:
    fields = [
        "project",
        "ai",
        "run_id",
        "status",
        "returncode",
        "elapsed_seconds",
        "result_cpp_total",
        "result_cpp_success",
        "result_cpp_failed",
        "result_cpp_success_rate",
        "repair_total_failed_files",
        "repair_repaired_count",
        "repair_failed_count",
        "review_cpp_total",
        "review_cpp_success",
        "review_cpp_failed",
        "review_cpp_success_rate",
        "failed_files_after_repair",
        "header_failed_count",
        "failed_headers",
        "header_failure_report",
        "stdout_log",
        "stderr_log",
    ]
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump({"rows": rows}, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    raise SystemExit(main())
