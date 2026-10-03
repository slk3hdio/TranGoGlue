"""Run 5 extra agent-repair rounds on top of an existing full-pipeline batch run.

For each project this invokes `main.py --mode repair` with the SAME run id, so
the repair agent starts from the already-repaired result/ directory and gets a
fresh budget of `--max-repair-attempts` compilation attempts per still-failing
file (link mode, same as the original batch). llm_usage.json is accumulated
(main.py merges into the existing file), so token/time costs add up.

Usage (from repo root, conda env sitp):
    python approach/v4_7/scripts/run_sitp_extra_repair.py --workers 4
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

APPROACH_DIR = Path(__file__).resolve().parents[2]
PROJECT_ROOT = APPROACH_DIR.parent
if str(APPROACH_DIR) not in sys.path:
    sys.path.insert(0, str(APPROACH_DIR))

from path_config import cfg_all_project_names

DEFAULT_RUN_ID = "20260817_28project_latest_sitp"


def run_project(project: str, args, batch_dir: Path) -> dict:
    """对一个既有运行执行额外 repair 并汇总结果。

    参数:
        project: 项目名称。
        args: 批处理命令行参数。
        batch_dir: 本次额外 repair 的摘要目录。

    返回:
        单项目 repair 执行结果。
    """
    run_dir = PROJECT_ROOT / "output" / "v4_7" / project / args.ai / "runs" / args.run_id
    command = [
        sys.executable,
        str(APPROACH_DIR / "main.py"),
        "--ai", args.ai,
        "--project", project,
        "--run-id", args.run_id,
        "--temperature", str(args.temperature),
        "--compile-timeout", str(args.compile_timeout),
        "--mode", "repair",
        "--apply-repair",
        "--max-repair-attempts", str(args.max_repair_attempts),
        "--max-tool-calls", str(args.max_tool_calls),
        "--repair-test-suites", args.repair_test_suites,
    ]
    log_path = batch_dir / "extra_repair_logs" / f"{project}.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    with open(log_path, "a", encoding="utf-8") as log:
        log.write(f"\n{'='*20} {time.strftime('%F %T')} {'='*20}\n{' '.join(command)}\n")
        log.flush()
        proc = subprocess.run(command, cwd=str(PROJECT_ROOT), stdout=log, stderr=subprocess.STDOUT)
    row = {
        "project": project,
        "run_id": args.run_id,
        "exit_code": proc.returncode,
        "wall_seconds": round(time.monotonic() - started, 3),
        "log": str(log_path),
    }
    repair_summary = run_dir / "review" / "repair_summary.json"
    if repair_summary.exists():
        try:
            data = json.loads(repair_summary.read_text(encoding="utf-8"))
            row["repair_summary"] = {
                "total_failed_files": data.get("total_failed_files"),
                "repaired_count": data.get("repaired_count"),
                "failed_count": data.get("failed_count"),
                "tool_call_count": data.get("tool_call_count"),
            }
        except (OSError, json.JSONDecodeError):
            pass
    return row


def main() -> int:
    """解析参数并并发执行额外 repair。

    返回:
        批处理完成时返回 0。
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ai", default="deepseek")
    parser.add_argument("--run-id", default=DEFAULT_RUN_ID)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--temperature", type=float, default=0.2)
    parser.add_argument("--compile-timeout", type=int, default=60)
    parser.add_argument("--max-repair-attempts", type=int, default=5)
    parser.add_argument("--max-tool-calls", type=int, default=150, help="Maximum repair tool calls per project")
    parser.add_argument("--repair-test-suites", default="base", metavar="SUITES", help="Functional test suites: base or base,additional")
    parser.add_argument("--projects", nargs="*", default=None, help="Subset of projects (default: all 28)")
    args = parser.parse_args()

    projects = args.projects or cfg_all_project_names("v4_7")
    batch_dir = PROJECT_ROOT / "output" / "v4_7" / "experiments" / args.run_id
    batch_dir.mkdir(parents=True, exist_ok=True)

    rows: list[dict] = []
    summary_path = batch_dir / "extra_repair_summary.json"

    def write_summary():
        summary_path.write_text(
            json.dumps({"run_id": args.run_id, "ai": args.ai, "mode": "repair",
                        "max_repair_attempts": args.max_repair_attempts,
                        "max_tool_calls": args.max_tool_calls,
                        "repair_test_suites": args.repair_test_suites,
                        "rows": rows},
                       ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    print(f"projects: {len(projects)}, workers: {args.workers}, extra repair attempts: {args.max_repair_attempts}, tool-call budget: {args.max_tool_calls}")
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {pool.submit(run_project, p, args, batch_dir): p for p in projects}
        for future in as_completed(futures):
            row = future.result()
            rows.append(row)
            write_summary()
            print(f"[{len(rows)}/{len(projects)}] {row['project']}: exit={row.get('exit_code')} "
                  f"wall={row.get('wall_seconds', 0)}s repair={row.get('repair_summary')}")

    write_summary()
    failed = [row["project"] for row in rows if row.get("exit_code") not in (0, None)]
    print(f"extra repair finished: {len(rows) - len(failed)} ok, {len(failed)} failed: {failed}")
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
