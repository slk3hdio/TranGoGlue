"""续跑被中断的 AlphaTrans 全量实验（仅重跑未完成项目）。

用途说明：
    当 run_alphatrans_pilot.py 发起的 full 阶段实验因挂死被中断时，
    本脚本读取已有 aggregate.json 中的"已完成项目"，跳过它们，
    只针对"未完成项目"用相同的 run_id 重新跑 alphatrans-baseline，
    并把新结果合并回同一份 aggregate.json，从而续跑而非全量重跑。

    它直接复用 run_alphatrans_pilot 里的 _run_project 命令构造逻辑，
    保证与原始实验的调用方式（--mode alphatrans-baseline、run-id、
    temperature、compile-timeout、max-repair-attempts）完全一致。

参数：
    --experiment-id：原始实验 ID（默认 20260818_alphatrans_r10_full）
    --workers：并发 worker 数量（默认 4）
    --projects：可选，若提供则只跑这些项目；否则自动跳过已完成的

返回值：
    所有需运行项目均成功时返回 0，否则返回 1。
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

APPROACH_DIR = Path(__file__).resolve().parents[2]
PROJECT_ROOT = APPROACH_DIR.parent
if str(APPROACH_DIR) not in sys.path:
    sys.path.insert(0, str(APPROACH_DIR))

# 需要续跑的原始实验 ID（对应 output/v4_7/experiments/<ID> 目录）
EXPERIMENT_ID = "20260818_alphatrans_r10_full"
# 并发 worker 数量（与原始实验一致）
WORKERS = 4

# 复用原始运行器的单项目运行逻辑，保证命令构造一致
from v4_7.scripts.run_alphatrans_pilot import _run_project


def main() -> int:
    """执行续跑：跳过已完成项目，只跑未完成项目并合并回 aggregate.json。

    返回值：所有需运行项目成功时返回 0，否则返回 1。
    """
    parser = argparse.ArgumentParser(description="Resume an interrupted AlphaTrans full run")
    parser.add_argument("--experiment-id", default=EXPERIMENT_ID)
    parser.add_argument("--workers", type=int, default=WORKERS)
    parser.add_argument("--ai", default="deepseek")
    parser.add_argument("--temperature", type=float, default=0.2)
    parser.add_argument("--compile-timeout", type=int, default=60)
    parser.add_argument("--max-repair-attempts", type=int, default=10)
    parser.add_argument("--projects", nargs="*", default=[], help="若提供则只跑这些项目")
    args = parser.parse_args()

    output_dir = PROJECT_ROOT / "output" / "v4_7" / "experiments" / args.experiment_id
    agg_path = output_dir / "aggregate.json"
    if not agg_path.exists():
        print(f"aggregate.json not found under {output_dir}")
        return 1
    agg = json.loads(agg_path.read_text(encoding="utf-8"))

    all_projects = list(agg.get("experiment", {}).get("projects", []))
    if not all_projects:
        print(f"No projects listed in {agg_path}")
        return 1

    # 已完成：pipeline_exit_code == 0。其余（未完成或中断）则续跑。
    done = {r.get("project") for r in agg.get("rows", []) if r.get("pipeline_exit_code") == 0}
    if args.projects:
        todo = [p for p in args.projects if p in all_projects]
    else:
        todo = [p for p in all_projects if p not in done]
        print(f"Skipping {len(done)} already-completed projects: {sorted(done)}")

    if not todo:
        print("No unfinished projects to resume. Nothing to do.")
        return 0

    print(f"Resuming {len(todo)} unfinished projects under experiment {args.experiment_id} (workers={args.workers})")
    print("Projects to run:", todo)

    # 保留原有已完成项目的结果行，续跑期间按项目合并
    new_rows = {r.get("project"): r for r in agg.get("rows", []) if r.get("pipeline_exit_code") == 0}
    started = time.monotonic()

    def _write() -> None:
        """按项目顺序写回合并后的 aggregate.json（含累计 elapsed）。"""
        rows = [new_rows[p] for p in all_projects if p in new_rows]
        payload = {
            "experiment": agg["experiment"],
            "elapsed_seconds": round(time.monotonic() - started, 3),
            "rows": rows,
        }
        agg_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def _run_store(project: str) -> tuple:
        """运行单个项目，返回 (project, result_row)。"""
        row = _run_project(args, project, args.experiment_id, output_dir)
        return project, row

    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = {executor.submit(_run_store, p): p for p in todo}
        for future in as_completed(futures):
            project, row = future.result()
            new_rows[project] = row
            _write()
            print(f"Done {project}: exit={row.get('pipeline_exit_code')} ({time.monotonic() - started:.1f}s elapsed)")

    final_rows = [new_rows[p] for p in all_projects if p in new_rows]
    ok = all(r.get("pipeline_exit_code") == 0 for r in final_rows)
    print(f"Resume completed: {len(final_rows)}/{len(all_projects)} projects have results. All OK={ok}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
