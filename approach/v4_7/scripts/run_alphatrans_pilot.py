"""运行 AlphaTrans baseline 的四项目试点。"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

APPROACH_DIR = Path(__file__).resolve().parents[2]
PROJECT_ROOT = APPROACH_DIR.parent
if str(APPROACH_DIR) not in sys.path:
    sys.path.insert(0, str(APPROACH_DIR))

from path_config import cfg_all_project_names, cfg_run_graph_dir, cfg_run_result_dir
from v4_7.baselines.oxidizer_style.evaluator import evaluate_run


PILOT_PROJECTS = [
    "JSONParser",
    "Cookie",
    "DebugLogExceptionModule",
    "RateLimiterBuilder",
]


def main() -> int:
    """按 pilot 或 full 阶段运行 AlphaTrans 项目并写入聚合结果。

    返回值：所有项目成功时返回 0，否则返回 1。
    """
    parser = argparse.ArgumentParser(description="Run the AlphaTrans baseline experiment")
    parser.add_argument("--phase", choices=["pilot", "full"], default="pilot")
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("--ai", default="deepseek")
    parser.add_argument("--temperature", type=float, default=0.2)
    parser.add_argument("--compile-timeout", type=int, default=60)
    parser.add_argument("--max-repair-attempts", type=int, default=10)
    parser.add_argument("--experiment-id", default="")
    parser.add_argument("--force-project", action="append", default=[])
    args = parser.parse_args()
    args.workers = max(1, args.workers)

    experiment_id = args.experiment_id or datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = PROJECT_ROOT / "output" / "v4_7" / "experiments" / experiment_id
    output_dir.mkdir(parents=True, exist_ok=True)
    projects = PILOT_PROJECTS if args.phase == "pilot" else cfg_all_project_names("v4_7")
    force_projects = set(args.force_project)
    unknown_forced = sorted(force_projects.difference(projects))
    if unknown_forced:
        parser.error(f"Unknown --force-project values: {', '.join(unknown_forced)}")

    # 仅复用配置一致、产物完整且日志中没有供应商错误的成功项目。
    rows = _load_valid_rows(output_dir, args, experiment_id, projects, force_projects)
    row_by_project = {row["project"]: row for row in rows}
    pending_projects = [project for project in projects if project not in row_by_project]
    started = time.monotonic()
    _write_aggregate(output_dir, args, experiment_id, projects, rows, time.monotonic() - started)
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = {
            executor.submit(_run_project, args, project, experiment_id, output_dir): project
            for project in pending_projects
        }
        for future in as_completed(futures):
            project = futures[future]
            try:
                row = future.result()
            except Exception as exc:
                row = {
                    "project": project,
                    "strategy": "alphatrans",
                    "run_id": f"{experiment_id}_alphatrans",
                    "pipeline_exit_code": -1,
                    "runner_error": str(exc),
                }
            # 重跑项目以最新结果替换旧行，防止失败记录与成功记录重复累计。
            row_by_project[project] = row
            rows = [row_by_project[name] for name in projects if name in row_by_project]
            _write_aggregate(output_dir, args, experiment_id, projects, rows, time.monotonic() - started)
    return 0 if len(rows) == len(projects) and all(row["pipeline_exit_code"] == 0 for row in rows) else 1


def _load_valid_rows(
    output_dir: Path,
    args,
    experiment_id: str,
    projects: list[str],
    force_projects: set[str],
) -> list[dict]:
    """读取可安全续跑的既有 AlphaTrans 结果。

    参数：output_dir 为实验目录，args 为本次配置，experiment_id 为实验标识，
    projects 为目标项目顺序，force_projects 为必须重跑的项目。返回有效结果行。
    """
    aggregate_path = output_dir / "aggregate.json"
    if not aggregate_path.exists():
        return []
    try:
        payload = json.loads(aggregate_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []

    experiment = payload.get("experiment", {})
    expected = {
        "id": experiment_id,
        "phase": args.phase,
        "strategy": "alphatrans",
        "ai": args.ai,
        "temperature": args.temperature,
        "max_repair_attempts": max(1, args.max_repair_attempts),
    }
    if any(experiment.get(key) != value for key, value in expected.items()):
        return []

    # 后出现的同名行覆盖旧行，再按论文基准项目顺序输出。
    latest: dict[str, dict] = {}
    for row in payload.get("rows", []):
        project = row.get("project")
        if project in projects:
            latest[project] = row
    return [
        latest[project]
        for project in projects
        if project not in force_projects
        and project in latest
        and _row_is_valid(latest[project], args, experiment_id, output_dir)
    ]


def _row_is_valid(row: dict, args, experiment_id: str, output_dir: Path) -> bool:
    """判断既有项目结果是否足以作为续跑完成证据。

    参数：row 为聚合结果行，args 为本次配置，experiment_id 为实验标识，
    output_dir 为实验目录。返回产物、指标和日志均有效时的布尔值。
    """
    project = row.get("project")
    run_id = f"{experiment_id}_alphatrans"
    required_metrics = {
        "header_compile_rate",
        "cpp_compile_rate",
        "operational_link_success",
        "strict_link_success",
    }
    if (
        not isinstance(project, str)
        or row.get("run_id") != run_id
        or row.get("pipeline_exit_code") != 0
        or row.get("evaluation_error")
        or not required_metrics.issubset(row)
    ):
        return False

    result_dir = cfg_run_result_dir(args.ai, project, "v4_7", run_id)
    graph_dir = cfg_run_graph_dir(args.ai, project, "v4_7", run_id)
    if not result_dir.is_dir() or not graph_dir.is_dir():
        return False
    if not any(result_dir.glob("*.h")) or not any(graph_dir.iterdir()):
        return False

    log_path = output_dir / f"{project}.log"
    try:
        log_text = log_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return False
    provider_error_markers = (
        "in_flight_budget_exhausted",
        "Arrearage",
        "402 Payment Required",
        "Insufficient Balance",
        "overdue-payment",
    )
    return not any(marker in log_text for marker in provider_error_markers)


def _run_project(args, project: str, experiment_id: str, output_dir: Path) -> dict:
    """运行一个 AlphaTrans 项目并提取最终评估指标。

    参数：args 为命令行配置，project 为项目名，experiment_id 为实验标识，
    output_dir 为日志和聚合报告目录。返回该项目的结果记录。
    """
    run_id = f"{experiment_id}_alphatrans"
    log_path = output_dir / f"{project}.log"
    command = [
        sys.executable,
        str(APPROACH_DIR / "main.py"),
        "--ai", args.ai,
        "--project", project,
        "--run-id", run_id,
        "--temperature", str(args.temperature),
        "--compile-timeout", str(args.compile_timeout),
        "--mode", "alphatrans-baseline",
        "--max-repair-attempts", str(max(1, args.max_repair_attempts)),
    ]
    started = time.monotonic()
    with log_path.open("w", encoding="utf-8") as log:
        process = subprocess.run(command, cwd=str(PROJECT_ROOT), stdout=log, stderr=subprocess.STDOUT)
    row = {
        "project": project,
        "strategy": "alphatrans",
        "run_id": run_id,
        "pipeline_exit_code": process.returncode,
        "runner_wall_seconds": round(time.monotonic() - started, 3),
        "runner_log": str(log_path.relative_to(PROJECT_ROOT)),
    }
    if process.returncode == 0:
        result_dir = cfg_run_result_dir(args.ai, project, "v4_7", run_id)
        graph_dir = cfg_run_graph_dir(args.ai, project, "v4_7", run_id)
        try:
            evaluation = evaluate_run(result_dir, graph_dir, args.compile_timeout)
            row.update({
                "header_syntax_rate": evaluation["header_syntax_rate"],
                "header_compile_rate": evaluation["header_compile_rate"],
                "cpp_syntax_rate": evaluation["cpp_syntax_rate"],
                "cpp_compile_rate": evaluation["cpp_compile_rate"],
                "operational_link_success": evaluation["operational_link_success"],
                "strict_link_success": evaluation["strict_link_success"],
                "coarse_method_compile_rate": evaluation["coarse_methods"]["compile_rate"],
                "source_loc_compile_rate": evaluation["coarse_methods"]["source_loc_compile_rate"],
            })
        except Exception as exc:
            row["evaluation_error"] = str(exc)
    return row


def _write_aggregate(
    output_dir: Path,
    args,
    experiment_id: str,
    projects: list[str],
    rows: list[dict],
    elapsed: float,
) -> None:
    """写入 AlphaTrans 实验的配置、项目结果和运行时间。

    参数：output_dir 为实验目录，args 为配置，experiment_id 为实验标识，
    rows 为已完成项目结果，elapsed 为累计运行秒数。无返回值。
    """
    payload = {
        "experiment": {
            "id": experiment_id,
            "phase": args.phase,
            "strategy": "alphatrans",
            "ai": args.ai,
            "temperature": args.temperature,
            "compile_timeout": args.compile_timeout,
            "max_repair_attempts": max(1, args.max_repair_attempts),
            "workers": args.workers,
            "projects": projects,
        },
        "elapsed_seconds": round(elapsed, 3),
        "rows": rows,
    }
    (output_dir / "aggregate.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )


if __name__ == "__main__":
    raise SystemExit(main())
