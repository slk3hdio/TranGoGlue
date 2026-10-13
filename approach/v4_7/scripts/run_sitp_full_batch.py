"""Run the SITP v4_7 full pipeline over all 28 projects in parallel.

Each project runs as a separate `main.py --mode <experiment>` subprocess with a
fixed run id, so re-running this script resumes unfinished projects. The
experiment (standard pipeline or one of the ablation groups) is selected with
`--experiment`; all paper hyperparameters are fixed inside main.py. Per-project
stdout/stderr goes to a log file under the batch output directory. When a
project finishes, its exit code, wall time and llm_usage.json (token cost)
are collected into batch_summary.json.

Usage (from repo root, conda env sitp):
    python approach/v4_7/scripts/run_sitp_full_batch.py --workers 4
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
    """运行单个项目并返回可写入批次摘要的结果。

    参数:
        project: 项目名称。
        args: 批处理命令行参数。
        batch_dir: 批次输出目录。

    返回:
        包含退出码、耗时和用量信息的结果字典。
    """
    run_dir = PROJECT_ROOT / "output" / "v4_7" / project / args.ai / "runs" / args.run_id
    result_dir = run_dir / "result"
    usage_path = result_dir / "llm_usage.json"
    if usage_path.exists() and not args.force:
        return {"project": project, "run_id": args.run_id, "skipped": "already complete"}

    command = [
        sys.executable,
        str(APPROACH_DIR / "main.py"),
        "--ai", args.ai,
        "--project", project,
        "--run-id", args.run_id,
        "--mode", args.experiment,
    ]
    log_path = batch_dir / "logs" / f"{project}.log"
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
    if usage_path.exists():
        try:
            row["llm_usage"] = json.loads(usage_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            pass
    return row


def main() -> int:
    """解析批处理参数，并发执行选定项目。

    返回:
        全部任务调度完成时返回 0。
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ai", default="deepseek")
    parser.add_argument("--run-id", default=DEFAULT_RUN_ID)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument(
        "--experiment",
        choices=["full", "ablation-header-oneshot", "ablation-wo-grouping", "ablation-wo-context", "ablation-wo-repair"],
        default="full",
        help="Experiment entry forwarded to main.py --mode; hyperparameters are fixed in main.py",
    )
    parser.add_argument("--force", action="store_true", help="Re-run projects even if llm_usage.json exists")
    parser.add_argument("--projects", nargs="*", default=None, help="Subset of projects (default: all 28)")
    args = parser.parse_args()

    projects = args.projects or cfg_all_project_names("v4_7")
    batch_dir = PROJECT_ROOT / "output" / "v4_7" / "experiments" / args.run_id
    batch_dir.mkdir(parents=True, exist_ok=True)

    rows: list[dict] = []
    summary_path = batch_dir / "batch_summary.json"
    if summary_path.exists() and not args.force:
        try:
            rows = json.loads(summary_path.read_text(encoding="utf-8")).get("rows", [])
        except (OSError, json.JSONDecodeError):
            rows = []
    # 断点续跑时同一项目只保留最后一次记录，避免旧失败行污染最终统计。
    rows_by_project = {row["project"]: row for row in rows}
    rows = list(rows_by_project.values())
    done_projects = {row["project"] for row in rows if row.get("exit_code") == 0 or row.get("skipped")}

    pending = [p for p in projects if p not in done_projects]
    print(f"projects: {len(projects)}, done: {len(done_projects)}, pending: {len(pending)}, workers: {args.workers}")

    def write_summary():
        summary_path.write_text(
            json.dumps(
                {
                    "run_id": args.run_id,
                    "ai": args.ai,
                    "experiment": args.experiment,
                    "rows": rows,
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {pool.submit(run_project, p, args, batch_dir): p for p in pending}
        for future in as_completed(futures):
            row = future.result()
            rows = [item for item in rows if item["project"] != row["project"]]
            rows.append(row)
            # 断点续跑单个项目时，汇总中仍包含此前完成的其它项目，
            # 因此使用完整项目顺序排序，避免在子集列表中查找失败。
            project_order = cfg_all_project_names("v4_7")
            order_index = {name: index for index, name in enumerate(project_order)}
            rows.sort(key=lambda item: order_index.get(item["project"], len(order_index)))
            write_summary()
            print(f"[{len(rows)}/{len(projects)}] {row['project']}: exit={row.get('exit_code', 'skip')} "
                  f"wall={row.get('wall_seconds', 0)}s")

    write_summary()
    failed = [row["project"] for row in rows if row.get("exit_code") not in (0, None)]
    print(f"batch finished: {len(rows) - len(failed)} ok, {len(failed)} failed: {failed}")
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
