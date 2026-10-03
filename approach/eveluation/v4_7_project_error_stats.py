"""
统计 v4_7 项目级编译失败日志的错误分类（论文 RQ4 的 Ours 口径）。

对每个项目的 best run，读取:
- result/compile_report/failed_cpp_compile_logs/*.log
- result/compile_report/failed_header_compile_logs/*.log

每个 .log 文件对应一个失败的翻译单元（.cpp 或 header self-include），
用确定性规则分类（文件级去重 + 级联抑制），与 v3/v4/v4_1 的 eval 口径一致。
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

p_dir = str(Path(__file__).parent)
pp_dir = str(Path(__file__).parent.parent)
if pp_dir not in sys.path:
    sys.path.append(pp_dir)
if p_dir not in sys.path:
    sys.path.append(p_dir)

from path_config import cfg_all_project_names, cfg_best_run_id, cfg_run_result_dir  # noqa: E402
from eveluation.deterministic_error_classifier import (  # noqa: E402
    _is_cascade_error,
    classify_message,
    extract_error_lines,
)

CATS = [
    "Syntax Rule Violation",
    "Type Error",
    "Declaration Mismatch",
    "Undefined Symbols",
    "Duplicated Definitions",
    "Header File Error",
    "Other Errors",
]


def classify_log_file(log_path: Path) -> list[dict[str, str]]:
    """对单个失败日志文件分类（文件级去重 + 级联抑制）。"""
    log_text = log_path.read_text(encoding="utf-8", errors="replace")
    messages = extract_error_lines(log_text)
    has_header_root = any(
        ("file not found" in m.lower()) or ("#include nested too deeply" in m.lower())
        for m in messages
    )
    seen: dict[tuple[str, str], None] = {}
    for msg in messages:
        error_type = classify_message(msg)
        if has_header_root and _is_cascade_error(error_type, msg):
            continue
        key = (error_type, msg[:200])
        if key in seen:
            continue
        seen[key] = None
    return [{"error_type": et, "error_detail": det} for (et, det) in seen]


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="v4_7 project-level error stats from compile_report logs.")
    parser.add_argument("--projects", default="", help="Comma-separated project filter; empty means all v4_7 projects.")
    args = parser.parse_args()

    if args.projects.strip():
        projects = [p.strip() for p in args.projects.split(",") if p.strip()]
    else:
        projects = cfg_all_project_names("v4_7")
    total = Counter()
    per_project: dict[str, Counter] = {}
    for project in projects:
        run_id = cfg_best_run_id("deepseek", project, "v4_7")
        if not run_id:
            print(f"[skip] {project}: no run")
            continue
        result_dir = cfg_run_result_dir("deepseek", project, "v4_7", run_id)
        counter = Counter()
        unit_count = 0
        for summary_name, log_subdir in [
            ("cpp_compile_summary.json", "failed_cpp_compile_logs"),
            ("header_compile_summary.json", "failed_header_compile_logs"),
        ]:
            summary_path = result_dir / "compile_report" / summary_name
            if not summary_path.exists():
                continue
            summary = json.loads(summary_path.read_text(encoding="utf-8"))
            log_dir = result_dir / "compile_report" / log_subdir
            for item in summary.get("results", []):
                if item.get("success", False):
                    continue
                unit_count += 1
                log_file = log_dir / f"{Path(item.get('file', '')).stem}.log"
                if log_file.exists():
                    for err in classify_log_file(log_file):
                        counter[err["error_type"]] += 1
                        total[err["error_type"]] += 1
        per_project[project] = counter
        print(f"[{project}] run={run_id} failed_units={unit_count} errors={dict(counter)}")

    print("\n=== TOTAL v4_7 (project-level compile logs) ===")
    grand = sum(total.values())
    for cat in CATS:
        print(f"  {cat}: {total.get(cat, 0)}")
    print(f"  six-cat total (excl Other): {sum(total.get(c, 0) for c in CATS[:-1])}")
    print(f"  grand total (incl Other): {grand}")

    out_path = Path("statistics") / "v4_7_project_level_error_summary.json"
    out_path.parent.mkdir(exist_ok=True)
    out_path.write_text(
        json.dumps(
            {
                "per_project": {k: dict(v) for k, v in per_project.items()},
                "total": dict(total),
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"Saved to {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
