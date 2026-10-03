"""Summarize time and token cost of v4_7 runs from llm_trace.jsonl.

Trace entries written after usage tracking was added carry real
prompt/completion/total/cached token counts. Older entries are estimated
with a chars-per-token heuristic (marked with the "estimated_" prefix).

Usage (from repo root, conda env sitp):
    python approach/v4_7/scripts/summarize_run_cost.py <result_dir> [<result_dir> ...]
    python approach/v4_7/scripts/summarize_run_cost.py --experiment 20260817_28project_latest
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

CHARS_PER_TOKEN = 4.0  # rough heuristic for deepseek-tokenizer on English/code text


def summarize_result_dir(result_dir: Path) -> dict:
    trace_path = result_dir / "llm_trace.jsonl"
    stats = {
        "calls": 0,
        "calls_with_usage": 0,
        "calls_estimated": 0,
        "prompt_tokens": 0,
        "completion_tokens": 0,
        "total_tokens": 0,
        "cached_tokens": 0,
        "estimated_prompt_tokens": 0,
        "estimated_completion_tokens": 0,
        "llm_elapsed_seconds": 0.0,
    }
    if trace_path.exists():
        for line in trace_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            stats["calls"] += 1
            stats["llm_elapsed_seconds"] += float(entry.get("elapsed_seconds") or 0.0)
            if entry.get("total_tokens") is not None:
                stats["calls_with_usage"] += 1
                stats["prompt_tokens"] += int(entry.get("prompt_tokens") or 0)
                stats["completion_tokens"] += int(entry.get("completion_tokens") or 0)
                stats["total_tokens"] += int(entry.get("total_tokens") or 0)
                stats["cached_tokens"] += int(entry.get("cached_tokens") or 0)
            else:
                stats["calls_estimated"] += 1
                stats["estimated_prompt_tokens"] += int(len(entry.get("prompt") or "") / CHARS_PER_TOKEN)
                stats["estimated_completion_tokens"] += int(len(entry.get("response") or "") / CHARS_PER_TOKEN)
    stats["llm_elapsed_seconds"] = round(stats["llm_elapsed_seconds"], 3)

    report_path = result_dir / "oxidizer_report.json"
    if report_path.exists():
        try:
            report = json.loads(report_path.read_text(encoding="utf-8"))
            stats["run_elapsed_seconds"] = report.get("elapsed_seconds")
        except (OSError, json.JSONDecodeError):
            pass
    stats["grand_total_tokens_approx"] = (
        stats["total_tokens"]
        + stats["estimated_prompt_tokens"]
        + stats["estimated_completion_tokens"]
    )
    return stats


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("result_dirs", nargs="*", type=Path)
    parser.add_argument("--experiment", default="", help="experiment id under output/v4_7/experiments")
    args = parser.parse_args()

    result_dirs: list[Path] = list(args.result_dirs)
    if args.experiment:
        aggregate_path = (
            Path(__file__).resolve().parents[3]
            / "output" / "v4_7" / "experiments" / args.experiment / "aggregate.json"
        )
        aggregate = json.loads(aggregate_path.read_text(encoding="utf-8"))
        for row in aggregate.get("rows", []):
            result_dir = (
                Path(__file__).resolve().parents[3]
                / "output" / "v4_7" / row["project"] / aggregate["experiment"]["ai"]
                / "runs" / row["run_id"] / "result"
            )
            if result_dir.exists():
                result_dirs.append(result_dir)

    if not result_dirs:
        print("no result dirs found")
        return 1

    summaries = {}
    for result_dir in result_dirs:
        stats = summarize_result_dir(result_dir)
        summaries[str(result_dir)] = stats
        print(result_dir)
        print(json.dumps(stats, ensure_ascii=False, indent=2))

    if len(summaries) > 1:
        totals: dict[str, float] = {}
        for stats in summaries.values():
            for key, value in stats.items():
                if isinstance(value, (int, float)):
                    totals[key] = totals.get(key, 0) + value
        print("=== TOTALS ===")
        print(json.dumps(totals, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
