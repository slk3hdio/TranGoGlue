from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Any


APPROACH_DIR = Path(__file__).resolve().parents[2]
PROJECT_ROOT = APPROACH_DIR.parent
VERSION = "v4_7"
DEFAULT_PROJECTS = [
    "RateLimiterBuilder",
    "JSONParser",
    "Cookie",
    "Draft_6455Test",
    "FailsafeExecutor",
    "FailurePolicy",
    "ExecutionImpl",
    "TestIssues217",
    "OrGroupFilter",
]


def main() -> int:
    """运行或汇总 RQ6 的 header batch-size 实验。

    参数：
        无；实验配置由命令行参数提供。

    返回：
        所有子任务执行完成时返回 0。
    """
    parser = argparse.ArgumentParser(
        description="Run and summarize the v4_7 header batch-size experiment."
    )
    parser.add_argument("--ai", default="deepseek")
    parser.add_argument("--projects", default=",".join(DEFAULT_PROJECTS))
    parser.add_argument("--batch-sizes", default="1,2,3,5")
    parser.add_argument(
        "--jobs",
        default="",
        help="Optional comma-separated batch_size:project pairs; overrides the full matrix.",
    )
    parser.add_argument("--header-max-rounds", type=int, default=5)
    parser.add_argument(
        "--header-grouping-strategy",
        choices=["dependency", "random"],
        default="dependency",
        help="Header 分组策略；random 随机打散后按 batch size 切分。",
    )
    parser.add_argument(
        "--header-grouping-seed",
        type=int,
        default=None,
        help="random 分组策略的可复现随机种子。",
    )
    parser.add_argument(
        "--mode",
        choices=["header", "full"],
        default="header",
        help="执行仅 header 阶段或完整翻译流水线。",
    )
    parser.add_argument(
        "--repair-after-compile",
        action="store_true",
        help="在 full 模式下执行最终编译修复。",
    )
    parser.add_argument(
        "--apply-repair",
        action="store_true",
        help="将最终修复后的文件回写到运行结果。",
    )
    parser.add_argument("--compile-timeout", type=int, default=60)
    parser.add_argument("--max-repair-attempts", type=int, default=10)
    parser.add_argument("--max-tool-calls", type=int, default=150)
    parser.add_argument("--max-workers", type=int, default=5)
    parser.add_argument("--batch-name", default="")
    parser.add_argument("--skip-completed", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    projects = _comma_list(args.projects)
    batch_sizes = [int(value) for value in _comma_list(args.batch_sizes)]
    if not projects or not batch_sizes:
        parser.error("projects and batch sizes must not be empty")
    if any(size < 1 for size in batch_sizes):
        parser.error("batch sizes must be positive")
    if args.header_max_rounds < 1:
        parser.error("header max rounds must be positive")

    batch_name = args.batch_name or datetime.now().strftime(
        "%Y%m%d_%H%M%S_header_batch_size_r5"
    )
    output_dir = PROJECT_ROOT / "output" / VERSION / "batch_experiments" / batch_name
    log_dir = output_dir / "logs"
    output_dir.mkdir(parents=True, exist_ok=True)
    log_dir.mkdir(parents=True, exist_ok=True)

    job_pairs = _parse_job_pairs(args.jobs) if args.jobs else [
        (batch_size, project)
        for batch_size in batch_sizes
        for project in projects
    ]
    jobs = [
        _make_job(
            ai=args.ai,
            project=project,
            batch_size=batch_size,
            max_rounds=args.header_max_rounds,
            batch_name=batch_name,
            log_dir=log_dir,
            mode=args.mode,
            repair_after_compile=args.repair_after_compile,
            apply_repair=args.apply_repair,
            compile_timeout=args.compile_timeout,
            max_repair_attempts=args.max_repair_attempts,
            max_tool_calls=args.max_tool_calls,
            header_grouping_strategy=args.header_grouping_strategy,
            header_grouping_seed=args.header_grouping_seed,
        )
        for batch_size, project in job_pairs
    ]
    _write_json(output_dir / "manifest.json", {
        "batch_name": batch_name,
        "ai": args.ai,
        "projects": projects,
        "batch_sizes": batch_sizes,
        "header_max_rounds": args.header_max_rounds,
        "header_grouping_strategy": args.header_grouping_strategy,
        "header_grouping_seed": args.header_grouping_seed,
        "mode": args.mode,
        "repair_after_compile": args.repair_after_compile,
        "apply_repair": args.apply_repair,
        "compile_timeout": args.compile_timeout,
        "max_repair_attempts": args.max_repair_attempts,
        "max_tool_calls": args.max_tool_calls,
        "max_workers": args.max_workers,
        "jobs": jobs,
    })

    print(f"Batch: {batch_name}")
    print(f"Projects ({len(projects)}): {projects}")
    print(f"Batch sizes: {batch_sizes}")
    print(f"Jobs: {len(jobs)}, workers: {args.max_workers}")
    print(f"Output: {output_dir}")
    if args.dry_run:
        return 0

    existing = _load_existing_rows(output_dir / "summary.json")
    rows: list[dict[str, Any]] = []
    pending: list[dict[str, Any]] = []
    for job in jobs:
        previous = existing.get(job["run_id"])
        if args.skip_completed and previous and previous.get("run_completed"):
            rows.append(previous)
            print(f"Skip completed: {job['run_id']}")
        else:
            pending.append(job)

    _write_outputs(rows, output_dir)
    with ThreadPoolExecutor(max_workers=max(1, args.max_workers)) as executor:
        futures = {executor.submit(_run_job, job): job for job in pending}
        for completed, future in enumerate(as_completed(futures), start=1):
            job = futures[future]
            try:
                row = future.result()
            except Exception as exc:
                row = _result_row(job, returncode=-1, elapsed_seconds=0)
                row["runner_error"] = repr(exc)
            rows.append(row)
            rows.sort(key=lambda item: (item["batch_size"], item["project"]))
            _write_outputs(rows, output_dir)
            print(
                f"[{completed}/{len(pending)}] {row['project']} bs={row['batch_size']}: "
                f"source={row['source_success']}/{row['source_total']}, "
                f"rounds={row['rounds_used']}, returncode={row['returncode']}"
            )

    _write_outputs(rows, output_dir)
    print(f"Completed. Summary: {output_dir / 'summary.md'}")
    return 0 if all(row.get("returncode") == 0 for row in rows) else 1


def _comma_list(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def _parse_job_pairs(value: str) -> list[tuple[int, str]]:
    pairs = []
    for item in _comma_list(value):
        batch_size_text, separator, project = item.partition(":")
        if not separator or not project.strip():
            raise ValueError(f"invalid job pair {item!r}; expected batch_size:project")
        batch_size = int(batch_size_text)
        if batch_size < 1:
            raise ValueError(f"invalid batch size in job pair {item!r}")
        pairs.append((batch_size, project.strip()))
    return pairs


def _make_job(
    ai: str,
    project: str,
    batch_size: int,
    max_rounds: int,
    batch_name: str,
    log_dir: Path,
    mode: str,
    repair_after_compile: bool,
    apply_repair: bool,
    compile_timeout: int,
    max_repair_attempts: int,
    max_tool_calls: int,
    header_grouping_strategy: str,
    header_grouping_seed: int | None,
) -> dict[str, Any]:
    """构造单个 batch-size 组合的独立运行命令。

    参数：
        ai: 模型标识。
        project: 项目名称。
        batch_size: 当前 header 批大小。
        max_rounds: header 最大反馈轮数。
        batch_name: 批处理名称，同时构成唯一 run ID。
        log_dir: 标准输出和错误日志目录。
        mode: 执行模式（header 或 full）。
        repair_after_compile: 是否执行最终编译修复。
        apply_repair: 是否回写修复产物。
        compile_timeout: 单个 C++ 文件的编译超时秒数。
        max_repair_attempts: 单文件最大修复尝试数。
        max_tool_calls: 单项目修复工具调用预算。

    返回：
        可供子进程执行和结果汇总的任务字典。
    """
    run_id = f"{batch_name}_bs{batch_size}_{project}"
    command = [
        sys.executable,
        str(APPROACH_DIR / "main.py"),
        "--ai",
        ai,
        "--project",
        project,
        "--mode",
        mode,
        "--header-batch-size",
        str(batch_size),
        "--header-max-rounds",
        str(max_rounds),
        "--run-id",
        run_id,
        "--allow-header-failures",
        "--header-grouping-strategy",
        header_grouping_strategy,
    ]
    if header_grouping_seed is not None:
        command.extend(["--header-grouping-seed", str(header_grouping_seed)])
    if mode == "full":
        command.extend(["--compile-timeout", str(compile_timeout)])
        if repair_after_compile:
            command.extend([
                "--repair-after-compile",
                "--max-repair-attempts",
                str(max_repair_attempts),
                "--max-tool-calls",
                str(max_tool_calls),
            ])
        if apply_repair:
            command.append("--apply-repair")
    run_dir = (
        PROJECT_ROOT / "output" / VERSION / project / ai / "runs" / run_id
    )
    return {
        "project": project,
        "ai": ai,
        "batch_size": batch_size,
        "header_max_rounds": max_rounds,
        "mode": mode,
        "header_grouping_strategy": header_grouping_strategy,
        "header_grouping_seed": header_grouping_seed,
        "run_id": run_id,
        "run_dir": str(run_dir),
        "stdout_log": str(log_dir / f"bs{batch_size}_{project}.stdout.log"),
        "stderr_log": str(log_dir / f"bs{batch_size}_{project}.stderr.log"),
        "command": command,
    }


def _run_job(job: dict[str, Any]) -> dict[str, Any]:
    start = time.monotonic()
    stdout_path = Path(job["stdout_log"])
    stderr_path = Path(job["stderr_log"])
    with stdout_path.open("w", encoding="utf-8") as stdout_file, stderr_path.open(
        "w", encoding="utf-8"
    ) as stderr_file:
        process = subprocess.run(
            job["command"],
            cwd=PROJECT_ROOT,
            stdout=stdout_file,
            stderr=stderr_file,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
    elapsed = round(time.monotonic() - start, 2)
    return _result_row(job, process.returncode, elapsed)


def _result_row(
    job: dict[str, Any], returncode: int, elapsed_seconds: float
) -> dict[str, Any]:
    run_dir = Path(job["run_dir"])
    headers = _load_headers(run_dir / "graph")
    source_headers = [header for header in headers if header.get("source_kind") != "generated_external"]
    generated_headers = [header for header in headers if header.get("source_kind") == "generated_external"]
    source_failed = [
        str(header.get("key", ""))
        for header in source_headers
        if header.get("latest_compile_status") != "success"
    ]
    generated_failed = [
        str(header.get("key", ""))
        for header in generated_headers
        if header.get("latest_compile_status") != "success"
    ]
    source_success = len(source_headers) - len(source_failed)
    generated_success = len(generated_headers) - len(generated_failed)
    rounds_used = _rounds_used(
        run_dir / "result" / "header_iteration_round_summary.csv"
    )
    iteration_report = run_dir / "result" / "iteration_report.md"
    return {
        "project": job["project"],
        "ai": job["ai"],
        "batch_size": job["batch_size"],
        "header_max_rounds": job["header_max_rounds"],
        "run_id": job["run_id"],
        "returncode": returncode,
        "run_completed": returncode == 0 and iteration_report.exists(),
        "converged": bool(headers) and not source_failed and not generated_failed,
        "rounds_used": rounds_used,
        "elapsed_seconds": elapsed_seconds,
        "source_success": source_success,
        "source_total": len(source_headers),
        "source_success_rate": source_success / len(source_headers) if source_headers else None,
        "generated_success": generated_success,
        "generated_total": len(generated_headers),
        "generated_success_rate": generated_success / len(generated_headers) if generated_headers else None,
        "all_success": source_success + generated_success,
        "all_total": len(headers),
        "all_success_rate": (
            (source_success + generated_success) / len(headers) if headers else None
        ),
        "failed_source_headers": source_failed,
        "failed_generated_headers": generated_failed,
        "run_dir": job["run_dir"],
        "iteration_report": str(iteration_report),
        "stdout_log": job["stdout_log"],
        "stderr_log": job["stderr_log"],
        "runner_error": "",
    }


def _load_headers(graph_dir: Path) -> list[dict[str, Any]]:
    headers = []
    if not graph_dir.exists():
        return headers
    for path in graph_dir.rglob("*.json"):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if "translated_class_name" in data and "methods" in data:
            headers.append(data)
    return headers


def _rounds_used(path: Path) -> int | None:
    if not path.exists():
        return None
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as file:
            return sum(1 for _ in csv.DictReader(file))
    except OSError:
        return None


def _load_existing_rows(path: Path) -> dict[str, dict[str, Any]]:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return {row["run_id"]: row for row in data.get("rows", [])}


def _write_outputs(rows: list[dict[str, Any]], output_dir: Path) -> None:
    _write_json(output_dir / "summary.json", {"rows": rows, "aggregate": _aggregate(rows)})
    _write_csv(output_dir / "summary.csv", rows)
    _write_csv(output_dir / "aggregate.csv", _aggregate(rows))
    (output_dir / "summary.md").write_text(_markdown(rows), encoding="utf-8")


def _aggregate(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    aggregated = []
    batch_sizes = sorted({row["batch_size"] for row in rows})
    for batch_size in batch_sizes:
        selected = [row for row in rows if row["batch_size"] == batch_size]
        source_success = sum(row.get("source_success") or 0 for row in selected)
        source_total = sum(row.get("source_total") or 0 for row in selected)
        all_success = sum(row.get("all_success") or 0 for row in selected)
        all_total = sum(row.get("all_total") or 0 for row in selected)
        aggregated.append({
            "batch_size": batch_size,
            "completed_projects": sum(bool(row.get("run_completed")) for row in selected),
            "converged_projects": sum(bool(row.get("converged")) for row in selected),
            "projects": len(selected),
            "source_success": source_success,
            "source_total": source_total,
            "source_success_rate": source_success / source_total if source_total else None,
            "all_success": all_success,
            "all_total": all_total,
            "all_success_rate": all_success / all_total if all_total else None,
            "average_rounds": (
                sum(row["rounds_used"] for row in selected if row.get("rounds_used") is not None)
                / sum(row.get("rounds_used") is not None for row in selected)
                if any(row.get("rounds_used") is not None for row in selected)
                else None
            ),
            "elapsed_seconds": sum(row.get("elapsed_seconds") or 0 for row in selected),
        })
    return aggregated


def _write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fields = list(rows[0])
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            encoded = {
                key: ";".join(value) if isinstance(value, list) else value
                for key, value in row.items()
            }
            writer.writerow(encoded)


def _markdown(rows: list[dict[str, Any]]) -> str:
    lines = [
        "# Header Batch-Size Experiment",
        "",
        "## Aggregate",
        "",
        "| Batch size | Projects converged | Source headers | All headers | Avg. rounds |",
        "|---:|---:|---:|---:|---:|",
    ]
    for item in _aggregate(rows):
        lines.append(
            f"| {item['batch_size']} | {item['converged_projects']}/{item['projects']} | "
            f"{item['source_success']}/{item['source_total']} "
            f"({_percent(item['source_success_rate'])}) | {item['all_success']}/{item['all_total']} "
            f"({_percent(item['all_success_rate'])}) | {_number(item['average_rounds'])} |"
        )
    lines.extend([
        "",
        "## Per Project",
        "",
        "| Project | BS | Run ID | Source headers | All headers | Converged | Rounds | Failed source headers |",
        "|---|---:|---|---:|---:|---|---:|---|",
    ])
    for row in sorted(rows, key=lambda item: (item["project"], item["batch_size"])):
        lines.append(
            f"| {row['project']} | {row['batch_size']} | `{row['run_id']}` | "
            f"{row['source_success']}/{row['source_total']} | {row['all_success']}/{row['all_total']} | "
            f"{'yes' if row['converged'] else 'no'} | {row['rounds_used'] or '-'} | "
            f"{', '.join(row['failed_source_headers']) or '-'} |"
        )
    lines.append("")
    return "\n".join(lines)


def _percent(value: float | None) -> str:
    return "-" if value is None else f"{value * 100:.2f}%"


def _number(value: float | None) -> str:
    return "-" if value is None else f"{value:.2f}"


if __name__ == "__main__":
    raise SystemExit(main())
