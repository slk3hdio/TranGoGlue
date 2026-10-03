"""按论文定义汇总 RQ6 的分阶段编译指标。

读取 continuation 批次的 summary.json，分别计算 header translation、repair 前和
repair 后的 source-mapped 编译指标，并执行模块整体链接检查。链接产物只会写入并
自动清理 result/__link_build__ 临时目录。
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import lru_cache
from pathlib import Path
from typing import Any


APPROACH_DIR = Path(__file__).resolve().parents[2]
PROJECT_ROOT = APPROACH_DIR.parent
if str(APPROACH_DIR) not in sys.path:
    sys.path.insert(0, str(APPROACH_DIR))

from utils.clean_filename import sanitize_filename
from v4_7.steps.cpp_compile_step import link_project_dir


DEFAULT_DEPENDENCY_BATCH = (
    "output/v4_7/batch_experiments/20260903_rq6_existing_headers_full"
)
DEFAULT_RANDOM_BATCH = (
    "output/v4_7/batch_experiments/20260904_rq6_random_grouping_bs3_full"
)


def main() -> int:
    """解析批次参数、执行分阶段统计，并写入 JSON 和 Markdown。"""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dependency-batch",
        action="append",
        dest="dependency_batches",
        help="可重复指定需要合并统计的 dependency continuation 批次。",
    )
    parser.add_argument(
        "--random-batch",
        default=DEFAULT_RANDOM_BATCH,
        help="随机分组 continuation 批次；传空字符串可跳过。",
    )
    parser.add_argument(
        "--output",
        default="output/v4_7/batch_experiments/rq6_paper_four_metrics.json",
    )
    parser.add_argument(
        "--markdown-output",
        default="",
        help="Markdown 输出路径；默认与 JSON 同名。",
    )
    parser.add_argument(
        "--replacement-experiment",
        action="append",
        default=[],
        metavar="BS=PATH",
        help="用完整 full 实验替换同 BS 的 dependency 数据，可重复指定。",
    )
    parser.add_argument("--workers", type=int, default=5)
    args = parser.parse_args()

    dependency_batches = args.dependency_batches or [DEFAULT_DEPENDENCY_BATCH]
    specs = [("dependency", PROJECT_ROOT / path) for path in dependency_batches]
    if args.random_batch:
        specs.append(("random", PROJECT_ROOT / args.random_batch))

    rows: list[dict[str, Any]] = []
    for strategy, batch_dir in specs:
        rows.extend(_evaluate_batch(strategy, batch_dir, args.workers))
    for specification in args.replacement_experiment:
        batch_size, experiment_dir = _parse_replacement(specification)
        rows = [
            row
            for row in rows
            if not (row["strategy"] == "dependency" and row["batch_size"] == batch_size)
        ]
        rows.extend(
            _evaluate_experiment(
                "dependency", PROJECT_ROOT / experiment_dir, batch_size, args.workers
            )
        )
    rows.sort(key=lambda row: (row["strategy"], int(row["batch_size"])))

    output_path = PROJECT_ROOT / args.output
    markdown_path = (
        PROJECT_ROOT / args.markdown_output
        if args.markdown_output
        else output_path.with_suffix(".md")
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    markdown_path.write_text(_render_markdown(rows), encoding="utf-8")
    print(output_path)
    print(markdown_path)
    print(json.dumps(rows, ensure_ascii=False, indent=2))
    return 0


def _evaluate_batch(strategy: str, batch_dir: Path, workers: int) -> list[dict[str, Any]]:
    """对一个 continuation 批次按 batch size 汇总分阶段指标。"""
    payload = _load_json(batch_dir / "summary.json")
    return _evaluate_rows(strategy, batch_dir, payload.get("rows", []), workers)


def _evaluate_experiment(
    strategy: str, experiment_dir: Path, batch_size: int, workers: int
) -> list[dict[str, Any]]:
    """将直接 full 实验目录转换为统一项目记录后执行统计。"""
    payload = _load_json(experiment_dir / "batch_summary.json")
    ai_name = str(payload["ai"])
    run_id = str(payload["run_id"])
    rows = []
    for item in payload.get("rows", []):
        project = str(item["project"])
        run_dir = PROJECT_ROOT / "output" / "v4_7" / project / ai_name / "runs" / run_id
        completed = (
            (run_dir / "result" / "compile_report" / "cpp_compile_summary.json").exists()
            and (run_dir / "result" / "compile_report" / "header_compile_summary.json").exists()
            and (run_dir / "review" / "repair_summary.json").exists()
        )
        rows.append({
            "project": project,
            "run_id": run_id,
            "run_key": f"{run_id}:{project}",
            "run_dir": str(run_dir),
            "batch_size": batch_size,
            "completed": completed,
            "log": item.get("log") or str(experiment_dir / "logs" / f"{project}.log"),
        })
    return _evaluate_rows(strategy, experiment_dir, rows, workers)


def _evaluate_rows(
    strategy: str, source_dir: Path, rows: list[dict[str, Any]], workers: int
) -> list[dict[str, Any]]:
    """对统一格式的项目记录按 batch size 汇总分阶段指标。"""
    link_results = _check_links(rows, workers)
    metrics = []
    for batch_size in sorted({int(row["batch_size"]) for row in rows}):
        selected = [row for row in rows if int(row["batch_size"]) == batch_size]
        pre_header = _sum_compile_stage(
            selected, "stage_metrics/method_header_compile_summary.json", "header"
        )
        pre_cpp = _sum_compile_stage(
            selected, "stage_metrics/method_cpp_compile_summary.json", "cpp"
        )
        post_header = _sum_compile_stage(
            selected, "compile_report/header_compile_summary.json", "header"
        )
        post_cpp = _sum_compile_stage(
            selected, "compile_report/cpp_compile_summary.json", "cpp"
        )
        trajectory = _header_round_progression(selected)
        linked = sum(bool(link_results[_row_key(row)]) for row in selected)
        completed = sum(bool(row.get("completed")) for row in selected)
        project_total = len(selected)

        pre_header_success, pre_header_total = pre_header["success"], pre_header["total"]
        pre_cpp_success, pre_cpp_total = pre_cpp["success"], pre_cpp["total"]
        post_header_success, post_header_total = post_header["success"], post_header["total"]
        post_cpp_success, post_cpp_total = post_cpp["success"], post_cpp["total"]
        metrics.append({
            "strategy": strategy,
            "batch_size": batch_size,
            "source_batch": str(source_dir),
            "completed_projects": completed,
            "project_total": project_total,
            "valid_full_pipeline": completed == project_total,
            "header_translation_success": trajectory[-1]["success"] if trajectory else 0,
            "header_translation_total": trajectory[-1]["total"] if trajectory else 0,
            "header_translation_percent": trajectory[-1]["percent"] if trajectory else 0.0,
            "header_round_progression": trajectory,
            "pre_repair_available_projects": min(
                pre_header["available_projects"], pre_cpp["available_projects"]
            ),
            "pre_repair_header_available_projects": pre_header["available_projects"],
            "pre_repair_cpp_available_projects": pre_cpp["available_projects"],
            "pre_repair_syn_h_success": pre_header_success,
            "pre_repair_syn_h_total": pre_header_total,
            "pre_repair_syn_h_percent": _percent(pre_header_success, pre_header_total),
            "pre_repair_syn_cpp_success": pre_cpp_success,
            "pre_repair_syn_cpp_total": pre_cpp_total,
            "pre_repair_syn_cpp_percent": _percent(pre_cpp_success, pre_cpp_total),
            "pre_repair_tu_success": pre_header_success + pre_cpp_success,
            "pre_repair_tu_total": pre_header_total + pre_cpp_total,
            "pre_repair_tu_percent": _percent(
                pre_header_success + pre_cpp_success,
                pre_header_total + pre_cpp_total,
            ),
            "post_repair_available_projects": min(
                post_header["available_projects"], post_cpp["available_projects"]
            ),
            "post_repair_header_available_projects": post_header["available_projects"],
            "post_repair_cpp_available_projects": post_cpp["available_projects"],
            # 保留旧字段名，使已有论文表格脚本继续读取 repair 后四指标。
            "syn_h_success": post_header_success,
            "syn_h_total": post_header_total,
            "syn_h_percent": _percent(post_header_success, post_header_total),
            "syn_cpp_success": post_cpp_success,
            "syn_cpp_total": post_cpp_total,
            "syn_cpp_percent": _percent(post_cpp_success, post_cpp_total),
            "tu_success": post_header_success + post_cpp_success,
            "tu_total": post_header_total + post_cpp_total,
            "tu_percent": _percent(
                post_header_success + post_cpp_success,
                post_header_total + post_cpp_total,
            ),
            "link_success": linked,
            "link_total": project_total,
            "link_percent": _percent(linked, project_total),
            "link_failed_projects": [
                row["project"] for row in selected if not link_results[_row_key(row)]
            ],
        })
    return metrics


def _sum_compile_stage(
    rows: list[dict[str, Any]], relative_path: str, artifact_kind: str
) -> dict[str, int]:
    """汇总一个编译阶段，并过滤掉 generated_external 生成的辅助文件。

    参数：
        rows: continuation 汇总中的项目记录。
        relative_path: 相对于 result 目录的编译摘要路径。
        artifact_kind: ``header`` 或 ``cpp``。

    返回：
        成功数、总数以及存在该阶段快照的项目数。
    """
    success = 0
    total = 0
    available_projects = 0
    for row in rows:
        run_dir = Path(row["run_dir"])
        summary_path = run_dir / "result" / Path(relative_path)
        if summary_path.exists():
            summary = _load_json(summary_path)
        elif relative_path.startswith("stage_metrics/") and row.get("log"):
            summary = _load_pre_repair_log(Path(row["log"]), artifact_kind)
        else:
            continue
        source_artifacts = _source_artifacts(run_dir / "graph")
        allowed_files = (
            source_artifacts["headers"]
            if artifact_kind == "header"
            else source_artifacts["cpp"]
        )
        results = [
            item for item in summary.get("results", []) if item.get("file") in allowed_files
        ]
        success += sum(bool(item.get("success")) for item in results)
        total += len(results)
        available_projects += 1
    return {"success": success, "total": total, "available_projects": available_projects}


def _load_pre_repair_log(log_path: Path, artifact_kind: str) -> dict[str, Any]:
    """从最终一次运行日志恢复 repair 开始前的逐文件编译结果。"""
    text = log_path.read_text(encoding="utf-8", errors="replace")
    attempts = re.split(r"(?m)^==================== .+ ====================\s*$", text)
    attempt = next((part for part in reversed(attempts) if "========== Agent repair" in part), "")
    pre_repair = attempt.split("========== Agent repair", 1)[0]
    suffix = ".h" if artifact_kind == "header" else ".cpp"
    results: list[dict[str, Any]] = []
    for line in pre_repair.splitlines():
        stripped = line.strip()
        success_match = re.fullmatch(r"Compiled (?:header )?(.+\.(?:h|cpp)) successfully\.", stripped)
        failed_match = re.fullmatch(r"Failed to compile (?:header )?(.+\.(?:h|cpp))\.", stripped)
        match = success_match or failed_match
        if match and match.group(1).endswith(suffix):
            results.append({"file": match.group(1), "success": success_match is not None})
    return {"results": results}


def _parse_replacement(specification: str) -> tuple[int, str]:
    """解析 ``BS=PATH`` 形式的替换实验参数。"""
    batch_text, separator, path = specification.partition("=")
    if not separator or not batch_text.isdigit() or not path:
        raise ValueError(f"无效 replacement experiment：{specification}")
    return int(batch_text), path


@lru_cache(maxsize=None)
def _source_artifacts(graph_dir: Path) -> dict[str, Any]:
    """从图快照提取 source-mapped Header、CPP 文件名和状态候选名。"""
    headers: set[str] = set()
    cpp_files: set[str] = set()
    status_candidates: list[list[str]] = []
    seen_header_files: set[str] = set()
    # 每个一级目录中与目录同名的 JSON 才是 Header 根节点，其他 JSON 均为 Method。
    header_paths = [
        directory / f"{directory.name}.json"
        for directory in graph_dir.iterdir()
        if directory.is_dir()
    ]
    for path in header_paths:
        try:
            data = _load_json(path)
        except (OSError, json.JSONDecodeError):
            continue
        if not _is_source_header(data):
            continue
        translated_name = str(data.get("translated_class_name") or data.get("key") or "")
        header_file = f"{sanitize_filename(translated_name)}.h"
        if header_file in seen_header_files:
            continue
        seen_header_files.add(header_file)
        headers.add(header_file)
        cpp_files.add(f"{sanitize_filename(translated_name)}.cpp")
        candidates = [str(data.get("key") or ""), translated_name, path.parent.name]
        status_candidates.append(list(dict.fromkeys(name for name in candidates if name)))
    return {"headers": headers, "cpp": cpp_files, "status_candidates": status_candidates}


def _is_source_header(data: dict[str, Any]) -> bool:
    """判断 JSON 对象是否为源 Java 类对应的 Header 节点。"""
    return (
        "translated_class_name" in data
        and "methods" in data
        and data.get("source_kind") != "generated_external"
    )


def _header_round_progression(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """按轮汇总 source-mapped Header 成功数，并延续提前收敛状态。"""
    run_data: list[tuple[list[list[str]], dict[str, list[tuple[int, bool]]]]] = []
    max_round = 0
    for row in rows:
        run_dir = Path(row["run_dir"])
        status_path = run_dir / "result" / "header_iteration_status.csv"
        if not status_path.exists():
            continue
        status_by_name: dict[str, list[tuple[int, bool]]] = {}
        with status_path.open("r", encoding="utf-8", newline="") as handle:
            for item in csv.DictReader(handle):
                round_index = int(item["round"])
                max_round = max(max_round, round_index)
                status_by_name.setdefault(str(item["header_name"]), []).append(
                    (round_index, _as_bool(item.get("compile_success")))
                )
        candidates = _source_artifacts(run_dir / "graph")["status_candidates"]
        run_data.append((candidates, status_by_name))

    progression = []
    for round_index in range(1, max_round + 1):
        success = 0
        total = 0
        for candidates, status_by_name in run_data:
            for names in candidates:
                status_name = next((name for name in names if name in status_by_name), None)
                history = status_by_name.get(status_name, []) if status_name else []
                latest = [value for seen_round, value in history if seen_round <= round_index]
                success += bool(latest[-1]) if latest else False
                total += 1
        progression.append({
            "round": round_index,
            "success": success,
            "total": total,
            "percent": _percent(success, total),
        })
    return progression


def _check_links(rows: list[dict[str, Any]], workers: int) -> dict[str, bool]:
    """并行执行模块整体链接；未完成 run 直接计为链接失败。"""
    result = {_row_key(row): False for row in rows}

    def check(row: dict[str, Any]) -> tuple[str, bool]:
        """对单个完成 run 执行临时链接验证并返回结果。"""
        if not row.get("completed"):
            return _row_key(row), False
        success, _ = link_project_dir(Path(row["run_dir"]) / "result")
        return _row_key(row), success

    with ThreadPoolExecutor(max_workers=max(1, workers)) as executor:
        futures = [executor.submit(check, row) for row in rows]
        for future in as_completed(futures):
            run_id, success = future.result()
            result[run_id] = success
    return result


def _row_key(row: dict[str, Any]) -> str:
    """返回项目记录的唯一键，兼容每项目 run id 和共享 full run id。"""
    return str(row.get("run_key") or row["run_id"])


def _render_markdown(rows: list[dict[str, Any]]) -> str:
    """将扩展指标渲染为便于核对和引用的 Markdown 表格。"""
    lines = [
        "# RQ6 batch size 分阶段指标",
        "",
        "口径：Header 与 CPP 均只统计源 Java 类映射出的文件；TU 为两者合计。",
        "repair 前数据优先来自 method 阶段结束时保存的 `stage_metrics` 快照；缺失时从运行日志中的首次编译段恢复。",
        "",
        "## 数据完整性",
        "",
        "| 策略 | BS | 全流程完成 | repair 前快照 | repair 后报告 | 有效 |",
        "|---|---:|---:|---:|---:|---|",
    ]
    for row in rows:
        valid = "是" if row["valid_full_pipeline"] else "否"
        lines.append(
            f"| {row['strategy']} | {row['batch_size']} | "
            f"{row['completed_projects']}/{row['project_total']} | "
            f"{row['pre_repair_available_projects']}/{row['project_total']} | "
            f"{row['post_repair_available_projects']}/{row['project_total']} | {valid} |"
        )

    max_round = max(
        (len(row.get("header_round_progression", [])) for row in rows), default=0
    )
    lines.extend(["", "## Header translation 成功文件数变化", ""])
    round_headers = " | ".join(f"R{index}" for index in range(1, max_round + 1))
    lines.append(f"| 策略 | BS | {round_headers} |")
    lines.append("|---|---:|" + "---:|" * max_round)
    for row in rows:
        cells = {
            item["round"]: f"{item['success']}/{item['total']} ({item['percent']:.2f}%)"
            for item in row.get("header_round_progression", [])
        }
        values = " | ".join(cells.get(index, "-") for index in range(1, max_round + 1))
        lines.append(f"| {row['strategy']} | {row['batch_size']} | {values} |")

    lines.extend([
        "",
        "## Repair 前（method 阶段结束）",
        "",
        "| 策略 | BS | %Syn(h) | %Syn(cpp) | %TU |",
        "|---|---:|---:|---:|---:|",
    ])
    for row in rows:
        lines.append(
            f"| {row['strategy']} | {row['batch_size']} | "
            f"{_metric_cell(row, 'pre_repair_syn_h')} | "
            f"{_metric_cell(row, 'pre_repair_syn_cpp')} | "
            f"{_metric_cell(row, 'pre_repair_tu')} |"
        )

    lines.extend([
        "",
        "## Repair 后（论文四指标）",
        "",
        "| 策略 | BS | %Syn(h) | %Syn(cpp) | %TU | %Link |",
        "|---|---:|---:|---:|---:|---:|",
    ])
    for row in rows:
        lines.append(
            f"| {row['strategy']} | {row['batch_size']} | "
            f"{_metric_cell(row, 'syn_h')} | {_metric_cell(row, 'syn_cpp')} | "
            f"{_metric_cell(row, 'tu')} | {_metric_cell(row, 'link')} |"
        )
    lines.append("")
    return "\n".join(lines)


def _metric_cell(row: dict[str, Any], prefix: str) -> str:
    """格式化单项指标为成功数/总数和百分比。"""
    return (
        f"{row[f'{prefix}_success']}/{row[f'{prefix}_total']} "
        f"({row[f'{prefix}_percent']:.2f}%)"
    )


def _load_json(path: Path) -> dict[str, Any]:
    """以 UTF-8 读取 JSON 对象。"""
    return json.loads(path.read_text(encoding="utf-8"))


def _as_bool(value: Any) -> bool:
    """兼容 CSV 中的布尔字符串和原生布尔值。"""
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes"}


def _percent(success: int, total: int) -> float:
    """将成功计数转换为百分比；空分母固定为 0。"""
    return round(success / total * 100, 2) if total else 0.0


if __name__ == "__main__":
    raise SystemExit(main())
