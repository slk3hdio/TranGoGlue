"""Evaluate all SITP runs of a batch and aggregate metrics + cost.

Runs the common evaluator (header/cpp syntax+compile, link, coarse methods)
on each project's result dir and joins llm_usage.json cost data.

Usage (from repo root, conda env sitp):
    python approach/v4_7/scripts/evaluate_sitp_batch.py --run-id 20260817_28project_latest_sitp
"""

from __future__ import annotations

import argparse
import json
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

APPROACH_DIR = Path(__file__).resolve().parents[2]
PROJECT_ROOT = APPROACH_DIR.parent
if str(APPROACH_DIR) not in sys.path:
    sys.path.insert(0, str(APPROACH_DIR))

from path_config import cfg_all_project_names, cfg_run_graph_dir, cfg_run_result_dir
from v4_7.baselines.oxidizer_style.evaluator import evaluate_run


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-id", default="20260817_28project_latest_sitp")
    parser.add_argument("--ai", default="deepseek")
    parser.add_argument("--compile-timeout", type=int, default=60)
    parser.add_argument("--no-cache", action="store_true", help="Recompile instead of reusing cached common_evaluation.json")
    parser.add_argument("--workers", type=int, default=1, help="并行评测的项目数量")
    args = parser.parse_args()

    projects = cfg_all_project_names("v4_7")

    def evaluate_project(project: str) -> dict:
        """评测单个项目并返回主表聚合所需的原始计数。"""
        result_dir = cfg_run_result_dir(args.ai, project, "v4_7", args.run_id)
        graph_dir = cfg_run_graph_dir(args.ai, project, "v4_7", args.run_id)
        row = {"project": project, "run_id": args.run_id}
        usage_path = result_dir / "llm_usage.json"
        if usage_path.exists():
            row["llm_usage"] = json.loads(usage_path.read_text(encoding="utf-8"))
        try:
            cache_path = result_dir / "compile_report" / "common" / "common_evaluation.json"
            if cache_path.exists() and not args.no_cache:
                evaluation = json.loads(cache_path.read_text(encoding="utf-8"))
            else:
                evaluation = evaluate_run(result_dir, graph_dir, args.compile_timeout)
            _filter_to_java_backed_files(evaluation, graph_dir)
            coarse = evaluation["coarse_methods"]
            row.update({
                "header_syntax_rate": evaluation["header_syntax_rate"],
                "header_compile_rate": evaluation["header_compile_rate"],
                "cpp_syntax_rate": evaluation["cpp_syntax_rate"],
                "cpp_compile_rate": evaluation["cpp_compile_rate"],
                "operational_link_success": evaluation["operational_link_success"],
                "strict_link_success": evaluation["strict_link_success"],
                "coarse_method_compile_rate": coarse["compile_rate"],
                "header_count": len(evaluation["headers"]),
                "header_syntax_success": sum(i["syntax_success"] for i in evaluation["headers"]),
                "header_compile_success": sum(i["compile_success"] for i in evaluation["headers"]),
                "cpp_count": len(evaluation["sources"]),
                "cpp_syntax_success": sum(i["syntax_success"] for i in evaluation["sources"]),
                "cpp_compile_success": sum(i["compile_success"] for i in evaluation["sources"]),
                "method_count": coarse["total"],
                "method_compile_success": coarse["success"],
            })
        except Exception as exc:
            row["evaluation_error"] = str(exc)
        return row

    with ThreadPoolExecutor(max_workers=max(1, args.workers)) as executor:
        rows = list(executor.map(evaluate_project, projects))
    for row in rows:
        print(f"{row['project']}: {row.get('evaluation_error', 'ok')}")

    def micro(num_key: str, den_key: str) -> float | None:
        avail = [r for r in rows if num_key in r and den_key in r]
        total = sum(r[den_key] for r in avail)
        return sum(r[num_key] for r in avail) / total if total else None

    def macro(key: str) -> float | None:
        vals = [r[key] for r in rows if key in r]
        return sum(vals) / len(vals) if vals else None

    link_rows = [r for r in rows if "operational_link_success" in r]
    payload = {
        "run_id": args.run_id,
        "ai": args.ai,
        "rows": rows,
        "micro": {
            "header_syntax_rate": micro("header_syntax_success", "header_count"),
            "header_compile_rate": micro("header_compile_success", "header_count"),
            "cpp_syntax_rate": micro("cpp_syntax_success", "cpp_count"),
            "cpp_compile_rate": micro("cpp_compile_success", "cpp_count"),
            "method_compile_rate": micro("method_compile_success", "method_count"),
        },
        "macro": {
            "header_syntax_rate": macro("header_syntax_rate"),
            "header_compile_rate": macro("header_compile_rate"),
            "cpp_syntax_rate": macro("cpp_syntax_rate"),
            "cpp_compile_rate": macro("cpp_compile_rate"),
            "method_compile_rate": macro("coarse_method_compile_rate"),
        },
        "operational_link_projects": sum(1 for r in link_rows if r["operational_link_success"]),
        "strict_link_projects": sum(1 for r in link_rows if r["strict_link_success"]),
        "link_denominator": len(link_rows),
        "total_tokens": sum((r.get("llm_usage") or {}).get("total_tokens", 0) for r in rows),
        "total_wall_seconds": sum((r.get("llm_usage") or {}).get("wall_seconds", 0) for r in rows),
    }
    out_path = PROJECT_ROOT / "output" / "v4_7" / "experiments" / args.run_id / "aggregate_sitp.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nwritten: {out_path}")
    print(json.dumps({k: v for k, v in payload.items() if k != "rows"}, ensure_ascii=False, indent=2))
    return 0


def _filter_to_java_backed_files(evaluation: dict, graph_dir: Path) -> None:
    """Keep only header/.cpp entries backed by a Java source class.

    The pipeline emits extra generated_external/helper files that baselines
    do not produce; drop them so file counts are comparable across methods.
    Link results are project-level and left untouched.
    """
    from graph import Project

    project = Project.load(graph_dir)
    java_headers = [h for h in project.headers if not h.is_generated_external()]
    header_names = {h.get_output_header_name() for h in java_headers}
    cpp_names = {h.get_output_cpp_name() for h in java_headers}

    evaluation["headers"] = [i for i in evaluation["headers"] if i["file"] in header_names]
    evaluation["sources"] = [i for i in evaluation["sources"] if i["file"] in cpp_names]

    def rate(items: list, key: str) -> float:
        return sum(1 for i in items if i[key]) / len(items) if items else 0.0

    evaluation["header_syntax_rate"] = rate(evaluation["headers"], "syntax_success")
    evaluation["header_compile_rate"] = rate(evaluation["headers"], "compile_success")
    evaluation["cpp_syntax_rate"] = rate(evaluation["sources"], "syntax_success")
    evaluation["cpp_compile_rate"] = rate(evaluation["sources"], "compile_success")


if __name__ == "__main__":
    raise SystemExit(main())
