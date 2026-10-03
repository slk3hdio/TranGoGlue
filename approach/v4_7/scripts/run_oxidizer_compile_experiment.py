from __future__ import annotations

import argparse
import json
import math
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
    """解析实验参数并运行批量翻译。

    返回值：全部项目成功时返回 0，否则返回 1。
    """
    parser = argparse.ArgumentParser(description="Run the compile-first Oxidizer reproduction experiment")
    parser.add_argument("--phase", choices=["pilot", "full"], default="pilot")
    parser.add_argument("--strategy", choices=["sitp", "oxidizer", "both"], default="both")
    parser.add_argument("--ai", default="deepseek")
    parser.add_argument("--temperature", type=float, default=0.2)
    parser.add_argument("--compile-timeout", type=int, default=60)
    parser.add_argument("--experiment-id", default="")
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("--fragment-max-tries", type=int, default=5)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    args.workers = max(1, args.workers)
    args.fragment_max_tries = max(1, args.fragment_max_tries)

    invocation_started = time.monotonic()
    experiment_id = args.experiment_id or datetime.now().strftime("%Y%m%d_%H%M%S")
    projects = PILOT_PROJECTS if args.phase == "pilot" else cfg_all_project_names("v4_7")
    strategies = ["sitp", "oxidizer"] if args.strategy == "both" else [args.strategy]
    output_dir = PROJECT_ROOT / "output" / "v4_7" / "experiments" / experiment_id
    output_dir.mkdir(parents=True, exist_ok=True)
    existing_rows = _load_existing_rows(output_dir)
    rows_by_key = {(row["strategy"], row["project"]): row for row in existing_rows}
    for row in existing_rows:
        if row.get("strategy") == "oxidizer" and row.get("pipeline_exit_code") == 0:
            result_dir = cfg_run_result_dir(args.ai, row["project"], "v4_7", row["run_id"])
            row.update(_oxidizer_fragment_fields(result_dir))

    jobs = []
    for strategy in strategies:
        for project in projects:
            key = (strategy, project)
            completed = rows_by_key.get(key, {}).get("pipeline_exit_code") == 0
            if completed and "evaluation_error" not in rows_by_key[key]:
                continue
            run_id = f"{experiment_id}_{strategy}"
            jobs.append((strategy, project, run_id))
            print(" ".join(_command(args, strategy, project, run_id)))

    if args.dry_run:
        print(f"Pending projects: {len(jobs)}, workers: {args.workers}")
        return 0

    _write_aggregate(
        output_dir,
        args,
        _ordered_rows(rows_by_key, strategies, projects),
        time.monotonic() - invocation_started,
    )
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = {
            executor.submit(_run_project, args, strategy, project, run_id, output_dir):
            (strategy, project)
            for strategy, project, run_id in jobs
        }
        for future in as_completed(futures):
            strategy, project = futures[future]
            try:
                row = future.result()
            except Exception as exc:
                row = {
                    "phase": args.phase,
                    "strategy": strategy,
                    "project": project,
                    "run_id": f"{experiment_id}_{strategy}",
                    "pipeline_exit_code": -1,
                    "runner_error": str(exc),
                    "tuning_project": project in PILOT_PROJECTS,
                }
            rows_by_key[(strategy, project)] = row
            rows = _ordered_rows(rows_by_key, strategies, projects)
            _write_aggregate(output_dir, args, rows, time.monotonic() - invocation_started)
            print(
                f"Completed {strategy}/{project}: exit={row['pipeline_exit_code']} "
                f"({len(rows)}/{len(strategies) * len(projects)} recorded)"
            )

    rows = _ordered_rows(rows_by_key, strategies, projects)
    _write_aggregate(output_dir, args, rows, time.monotonic() - invocation_started)
    print(f"Experiment summary: {output_dir / 'aggregate.json'}")
    return 0 if all(
        row.get("pipeline_exit_code") == 0 and "evaluation_error" not in row
        for row in rows
    ) else 1


def _run_project(args, strategy: str, project: str, run_id: str, output_dir: Path) -> dict:
    started = time.monotonic()
    log_dir = output_dir / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / f"{strategy}_{project}.log"
    command = _command(args, strategy, project, run_id)
    with open(log_path, "a", encoding="utf-8") as log:
        proc = subprocess.run(
            command,
            cwd=str(PROJECT_ROOT),
            stdout=log,
            stderr=subprocess.STDOUT,
        )
    row = {
        "phase": args.phase,
        "strategy": strategy,
        "project": project,
        "run_id": run_id,
        "pipeline_exit_code": proc.returncode,
        "tuning_project": project in PILOT_PROJECTS,
        "runner_wall_seconds": round(time.monotonic() - started, 3),
        "runner_log": str(log_path.relative_to(PROJECT_ROOT)),
    }
    if proc.returncode == 0:
        result_dir = cfg_run_result_dir(args.ai, project, "v4_7", run_id)
        graph_dir = cfg_run_graph_dir(args.ai, project, "v4_7", run_id)
        try:
            evaluation = evaluate_run(result_dir, graph_dir, args.compile_timeout)
            row.update(_summary_fields(evaluation))
            if strategy == "oxidizer":
                row.update(_oxidizer_fragment_fields(result_dir))
        except Exception as exc:
            row["evaluation_error"] = str(exc)
    return row


def _load_existing_rows(output_dir: Path) -> list[dict]:
    aggregate_path = output_dir / "aggregate.json"
    if not aggregate_path.exists():
        return []
    return list(json.loads(aggregate_path.read_text(encoding="utf-8")).get("rows", []))


def _ordered_rows(rows: dict, strategies: list[str], projects: list[str]) -> list[dict]:
    return [
        rows[(strategy, project)]
        for strategy in strategies
        for project in projects
        if (strategy, project) in rows
    ]


def _command(args, strategy: str, project: str, run_id: str) -> list[str]:
    """构造单项目实验命令。

    参数：args 为批处理参数，strategy 为实验策略，project 为项目名，
    run_id 为运行标识。返回可直接传给子进程的命令参数列表。
    """
    command = [
        sys.executable,
        str(APPROACH_DIR / "main.py"),
        "--ai", args.ai,
        "--project", project,
        "--run-id", run_id,
        "--temperature", str(args.temperature),
        "--compile-timeout", str(args.compile_timeout),
    ]
    if strategy == "oxidizer":
        command.extend(
            [
                "--mode", "oxidizer-baseline",
                "--feature-requery-budget", "10",
                "--fragment-max-tries", str(args.fragment_max_tries),
            ]
        )
    else:
        command.extend(
            [
                "--mode", "full",
                "--header-batch-size", "3",
                "--header-max-rounds", "10",
                "--repair-after-compile",
                "--apply-repair",
                "--max-repair-attempts", "15",
            ]
        )
    return command


def _summary_fields(evaluation: dict) -> dict:
    coarse = evaluation["coarse_methods"]
    return {
        "header_syntax_rate": evaluation["header_syntax_rate"],
        "header_compile_rate": evaluation["header_compile_rate"],
        "cpp_syntax_rate": evaluation["cpp_syntax_rate"],
        "cpp_compile_rate": evaluation["cpp_compile_rate"],
        "operational_link_success": evaluation["operational_link_success"],
        "strict_link_success": evaluation["strict_link_success"],
        "coarse_method_compile_rate": coarse["compile_rate"],
        "source_loc_compile_rate": coarse["source_loc_compile_rate"],
        "header_count": len(evaluation["headers"]),
        "header_syntax_success": sum(item["syntax_success"] for item in evaluation["headers"]),
        "header_compile_success": sum(item["compile_success"] for item in evaluation["headers"]),
        "cpp_count": len(evaluation["sources"]),
        "cpp_syntax_success": sum(item["syntax_success"] for item in evaluation["sources"]),
        "cpp_compile_success": sum(item["compile_success"] for item in evaluation["sources"]),
        "method_count": coarse["total"],
        "method_compile_success": coarse["success"],
        "method_source_loc": coarse["source_loc"],
        "method_successful_source_loc": coarse["successful_source_loc"],
    }


def _oxidizer_fragment_fields(result_dir: Path) -> dict:
    report = json.loads((result_dir / "oxidizer_report.json").read_text(encoding="utf-8"))
    budget = int(report.get("fragment_budget", report["config"].get("fragment_max_tries", 5)))
    syntax_at_budget = report["syntax_at_budget"]
    compile_at_budget = report["compile_at_budget"]
    token_usage = report.get("token_usage") or {}
    trace_usage = _trace_token_usage(result_dir / "llm_trace.jsonl")
    return {
        "fragment_count": report["fragment_count"],
        "fragment_source_loc": report["source_loc"],
        "fragment_syntax_at_1": report["syntax_at_1"]["rate"],
        "fragment_compile_at_1": report["compile_at_1"]["rate"],
        "fragment_syntax_at_1_loc": report["syntax_at_1"]["source_loc_rate"],
        "fragment_compile_at_1_loc": report["compile_at_1"]["source_loc_rate"],
        "fragment_budget": budget,
        "fragment_syntax_at_budget": syntax_at_budget["rate"],
        "fragment_compile_at_budget": compile_at_budget["rate"],
        "fragment_syntax_at_budget_loc": syntax_at_budget["source_loc_rate"],
        "fragment_compile_at_budget_loc": compile_at_budget["source_loc_rate"],
        f"fragment_syntax_at_{budget}": syntax_at_budget["rate"],
        f"fragment_compile_at_{budget}": compile_at_budget["rate"],
        f"fragment_syntax_at_{budget}_loc": syntax_at_budget["source_loc_rate"],
        f"fragment_compile_at_{budget}_loc": compile_at_budget["source_loc_rate"],
        "stub_rate": report["stub_rate"],
        "average_queries_per_fragment": report["average_queries_per_fragment"],
        "total_llm_queries": report["query_count"],
        "oxidizer_elapsed_seconds": report["elapsed_seconds"],
        "llm_elapsed_seconds": token_usage.get("llm_elapsed_seconds"),
        "prompt_tokens": token_usage.get("prompt_tokens"),
        "completion_tokens": token_usage.get("completion_tokens"),
        "total_tokens": token_usage.get("total_tokens"),
        "cached_tokens": token_usage.get("cached_tokens"),
        "calls_without_usage": trace_usage["calls_without_usage"],
        "calls_with_usage": trace_usage["calls_with_usage"],
        "estimated_prompt_tokens_without_usage": trace_usage["estimated_prompt_tokens_without_usage"],
        "estimated_completion_tokens_without_usage": trace_usage["estimated_completion_tokens_without_usage"],
        "estimated_total_tokens_without_usage": trace_usage["estimated_total_tokens_without_usage"],
        "accounted_total_tokens": trace_usage["accounted_total_tokens"],
    }


def _trace_token_usage(trace_path: Path) -> dict:
    stats = {
        "calls_with_usage": 0,
        "calls_without_usage": 0,
        "actual_total_tokens": 0,
        "estimated_prompt_tokens_without_usage": 0,
        "estimated_completion_tokens_without_usage": 0,
    }
    if not trace_path.exists():
        stats["estimated_total_tokens_without_usage"] = 0
        stats["accounted_total_tokens"] = 0
        return stats
    for line in trace_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue
        if entry.get("total_tokens") is not None:
            stats["calls_with_usage"] += 1
            stats["actual_total_tokens"] += int(entry.get("total_tokens") or 0)
            continue
        stats["calls_without_usage"] += 1
        stats["estimated_prompt_tokens_without_usage"] += math.ceil(
            len(entry.get("prompt") or "") / 4
        )
        stats["estimated_completion_tokens_without_usage"] += math.ceil(
            len(entry.get("response") or "") / 4
        )
    stats["estimated_total_tokens_without_usage"] = (
        stats["estimated_prompt_tokens_without_usage"]
        + stats["estimated_completion_tokens_without_usage"]
    )
    stats["accounted_total_tokens"] = (
        stats["actual_total_tokens"] + stats["estimated_total_tokens_without_usage"]
    )
    return stats


def _write_aggregate(
    output_dir: Path, args, rows: list[dict], invocation_wall_seconds: float = 0.0
) -> None:
    """写入实验聚合报告。

    参数：output_dir 为实验目录，args 为运行配置，rows 为项目结果，
    invocation_wall_seconds 为批处理累计墙钟时间。无返回值。
    """
    held_out = [row for row in rows if not row.get("tuning_project")]
    payload = {
        "experiment": {
            "phase": args.phase,
            "ai": args.ai,
            "temperature": args.temperature,
            "repetitions": 1,
            "workers": args.workers,
            "fragment_max_tries": args.fragment_max_tries,
            "tuning_projects": PILOT_PROJECTS,
        },
        "timing": {
            "invocation_wall_seconds": round(invocation_wall_seconds, 3),
            "sum_project_pipeline_seconds": round(
                sum(float(row.get("oxidizer_elapsed_seconds") or 0.0) for row in rows), 3
            ),
            "sum_runner_wall_seconds": round(
                sum(float(row.get("runner_wall_seconds") or 0.0) for row in rows), 3
            ),
        },
        "token_usage": _aggregate_token_usage(rows),
        "rows": rows,
        "all_projects_macro": _macro(rows),
        "all_projects_micro": _micro(rows),
        "held_out_24_macro": _macro(held_out),
        "held_out_24_micro": _micro(held_out),
    }
    (output_dir / "aggregate.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def _aggregate_token_usage(rows: list[dict]) -> dict:
    keys = (
        "prompt_tokens",
        "completion_tokens",
        "total_tokens",
        "cached_tokens",
        "calls_with_usage",
        "calls_without_usage",
        "estimated_prompt_tokens_without_usage",
        "estimated_completion_tokens_without_usage",
        "estimated_total_tokens_without_usage",
        "accounted_total_tokens",
    )
    return {
        key: sum(int(row.get(key) or 0) for row in rows)
        for key in keys
    }


def _macro(rows: list[dict]) -> dict:
    metrics = [
        "header_syntax_rate",
        "header_compile_rate",
        "cpp_syntax_rate",
        "cpp_compile_rate",
        "coarse_method_compile_rate",
        "source_loc_compile_rate",
        "operational_link_success",
        "strict_link_success",
    ]
    result = {}
    for strategy in ("sitp", "oxidizer"):
        selected = [row for row in rows if row.get("strategy") == strategy]
        result[strategy] = {
            metric: (
                sum(row[metric] for row in selected if metric in row)
                / sum(1 for row in selected if metric in row)
                if any(metric in row for row in selected)
                else None
            )
            for metric in metrics
        }
    return result


def _micro(rows: list[dict]) -> dict:
    pairs = {
        "header_syntax_rate": ("header_syntax_success", "header_count"),
        "header_compile_rate": ("header_compile_success", "header_count"),
        "cpp_syntax_rate": ("cpp_syntax_success", "cpp_count"),
        "cpp_compile_rate": ("cpp_compile_success", "cpp_count"),
        "coarse_method_compile_rate": ("method_compile_success", "method_count"),
        "source_loc_compile_rate": ("method_successful_source_loc", "method_source_loc"),
    }
    result = {}
    for strategy in ("sitp", "oxidizer"):
        selected = [row for row in rows if row.get("strategy") == strategy]
        metrics = {}
        for metric, (numerator, denominator) in pairs.items():
            available = [row for row in selected if numerator in row and denominator in row]
            total = sum(row[denominator] for row in available)
            metrics[metric] = sum(row[numerator] for row in available) / total if total else None
        result[strategy] = metrics
    return result


if __name__ == "__main__":
    raise SystemExit(main())
