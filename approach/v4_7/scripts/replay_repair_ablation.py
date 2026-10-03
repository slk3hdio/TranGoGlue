"""从已有 v4_7 run 回放最终 repair 阶段的文件级消融统计。"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_PROJECTS = [
    "FailurePolicy", "RateLimiterBuilder", "FailsafeExecutor", "ExecutionImpl",
    "TestIssues217", "Draft_6455Test", "OrGroupFilter", "Cookie", "JSONParser",
]


def _read_json(path: Path) -> dict:
    """读取 JSON 文件；文件不存在或格式异常时返回空对象。"""
    try:
        return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    except (OSError, json.JSONDecodeError):
        return {}


def _compile_counts(result_dir: Path) -> dict:
    """统计已有最终编译报告中的文件级成功数。"""
    counts = {"files": 0, "success": 0, "failed": 0}
    for name in ("cpp_compile_summary.json", "header_compile_summary.json"):
        data = _read_json(result_dir / "compile_report" / name)
        for item in data.get("results", []):
            counts["files"] += 1
            if item.get("success"):
                counts["success"] += 1
            else:
                counts["failed"] += 1
    return counts


def replay_project(project: str, ai: str, run_id: str) -> dict:
    """读取一个项目的 repair summary、编译报告和 token 用量。"""
    run_dir = PROJECT_ROOT / "output" / "v4_7" / project / ai / "runs" / run_id
    result_dir = run_dir / "result"
    repair = _read_json(run_dir / "review" / "repair_summary.json")
    usage = _read_json(result_dir / "llm_usage.json")
    compile_counts = _compile_counts(result_dir)
    results = repair.get("results", [])
    attempts = [int(item.get("attempts", 0) or 0) for item in results]
    initial_failed = int(repair.get("total_failed_files", len(results)) or 0)
    repaired = int(repair.get("repaired_count", sum(item.get("status") == "success" for item in results)) or 0)
    return {
        "project": project,
        "run_id": run_id,
        "repair_summary_found": bool(repair),
        "pre_repair_failed_files": initial_failed,
        "repaired_files": repaired,
        "unrepaired_files": max(0, initial_failed - repaired),
        "repair_success_rate": repaired / initial_failed if initial_failed else None,
        "attempts": attempts,
        "post_repair_compile": compile_counts,
        "llm_usage": usage,
        "pre_repair_compile_rate": None,
        "pre_repair_compile_rate_status": "proxy_unavailable_without_snapshot",
    }


def main() -> int:
    """生成项目级和整体 repair 回放 JSON。"""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ai", default="deepseek")
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--experiment-id", default="repair_replay")
    parser.add_argument("--projects", nargs="*", default=DEFAULT_PROJECTS)
    args = parser.parse_args()

    rows = [replay_project(project, args.ai, args.run_id) for project in args.projects]
    total_failed = sum(row["pre_repair_failed_files"] for row in rows)
    total_repaired = sum(row["repaired_files"] for row in rows)
    payload = {
        "ai": args.ai,
        "run_id": args.run_id,
        "proxy": True,
        "proxy_reason": "Existing runs do not retain a complete pre-repair source snapshot.",
        "rows": rows,
        "aggregate": {
            "projects": len(rows),
            "pre_repair_failed_files": total_failed,
            "repaired_files": total_repaired,
            "unrepaired_files": total_failed - total_repaired,
            "repair_success_rate": total_repaired / total_failed if total_failed else None,
        },
    }
    output = PROJECT_ROOT / "output" / "v4_7" / "experiments" / args.experiment_id / "ablation_repair_replay.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
