from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path
from typing import Any


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Consolidate primary and retry header batch-size experiment runs."
    )
    parser.add_argument("primary_summary", type=Path)
    parser.add_argument("--retry-summary", type=Path, action="append", default=[])
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()

    primary_rows = _load_rows(args.primary_summary)
    retry_rows = [row for path in args.retry_summary for row in _load_rows(path)]
    invalid_rows = [row for row in primary_rows if not _valid(row)]

    selected = {
        (row["project"], int(row["batch_size"])): row
        for row in primary_rows
        if _valid(row)
    }
    for row in retry_rows:
        if _valid(row):
            selected[(row["project"], int(row["batch_size"]))] = row

    rows = sorted(selected.values(), key=lambda row: (row["project"], int(row["batch_size"])))
    expected = {
        (row["project"], int(row["batch_size"]))
        for row in primary_rows
    }
    missing = sorted(expected - set(selected))
    aggregate = _aggregate(rows)
    project_summary = _project_summary(rows)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    _write_json(args.output_dir / "final_summary.json", {
        "primary_metric": "source header self-include compilation success",
        "valid_runs": len(rows),
        "invalid_attempts": len(invalid_rows),
        "missing_combinations": [
            {"project": project, "batch_size": batch_size}
            for project, batch_size in missing
        ],
        "aggregate": aggregate,
        "project_summary": project_summary,
        "rows": rows,
        "invalid_rows": invalid_rows,
    })
    _write_csv(args.output_dir / "final_runs.csv", rows)
    _write_csv(args.output_dir / "aggregate.csv", aggregate)
    _write_csv(args.output_dir / "project_summary.csv", project_summary)
    _write_csv(args.output_dir / "invalid_attempts.csv", invalid_rows)
    (args.output_dir / "report.md").write_text(
        _markdown(rows, aggregate, project_summary, invalid_rows, missing),
        encoding="utf-8",
    )

    print(f"Valid runs: {len(rows)}/{len(expected)}")
    print(f"Invalid attempts retained: {len(invalid_rows)}")
    print(f"Missing combinations: {len(missing)}")
    print(f"Report: {args.output_dir / 'report.md'}")
    return 0 if not missing else 1


def _valid(row: dict[str, Any]) -> bool:
    return (
        row.get("returncode") == 0
        and bool(row.get("run_completed"))
        and row.get("source_total") is not None
        and row.get("rounds_used") is not None
    )


def _load_rows(path: Path) -> list[dict[str, Any]]:
    return json.loads(path.read_text(encoding="utf-8")).get("rows", [])


def _aggregate(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[int(row["batch_size"])].append(row)

    aggregate = []
    for batch_size, selected in sorted(grouped.items()):
        source_success = sum(int(row["source_success"]) for row in selected)
        source_total = sum(int(row["source_total"]) for row in selected)
        generated_success = sum(int(row["generated_success"]) for row in selected)
        generated_total = sum(int(row["generated_total"]) for row in selected)
        project_rates = [
            int(row["source_success"]) / int(row["source_total"])
            for row in selected
            if int(row["source_total"])
        ]
        aggregate.append({
            "batch_size": batch_size,
            "projects": len(selected),
            "converged_projects": sum(bool(row["converged"]) for row in selected),
            "project_convergence_rate": sum(bool(row["converged"]) for row in selected) / len(selected),
            "source_success": source_success,
            "source_total": source_total,
            "source_micro_success_rate": source_success / source_total,
            "source_macro_success_rate": sum(project_rates) / len(project_rates),
            "generated_success": generated_success,
            "generated_total": generated_total,
            "average_rounds": sum(int(row["rounds_used"]) for row in selected) / len(selected),
            "max_round_runs": sum(
                int(row["rounds_used"]) >= int(row["header_max_rounds"])
                for row in selected
            ),
            "elapsed_seconds": sum(float(row["elapsed_seconds"]) for row in selected),
        })
    return aggregate


def _project_summary(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[row["project"]].append(row)

    summary = []
    for project, selected in sorted(grouped.items()):
        best_success = max(int(row["source_success"]) for row in selected)
        best_batch_sizes = sorted(
            int(row["batch_size"])
            for row in selected
            if int(row["source_success"]) == best_success
        )
        summary.append({
            "project": project,
            "source_total": int(selected[0]["source_total"]),
            "best_source_success": best_success,
            "best_batch_sizes": ";".join(map(str, best_batch_sizes)),
            "bs1_success": _success_for(selected, 1),
            "bs2_success": _success_for(selected, 2),
            "bs3_success": _success_for(selected, 3),
            "bs5_success": _success_for(selected, 5),
        })
    return summary


def _success_for(rows: list[dict[str, Any]], batch_size: int) -> int | None:
    return next(
        (int(row["source_success"]) for row in rows if int(row["batch_size"]) == batch_size),
        None,
    )


def _markdown(
    rows: list[dict[str, Any]],
    aggregate: list[dict[str, Any]],
    project_summary: list[dict[str, Any]],
    invalid_rows: list[dict[str, Any]],
    missing: list[tuple[str, int]],
) -> str:
    lines = [
        "# Header Batch-Size Experiment (Maximum 5 Rounds)",
        "",
        "Primary metric: source-mapped header self-include compilation success. Generated external headers are recorded but excluded from the primary rate because their count varies by run.",
        "",
        f"Valid matrix: {len(rows)} runs. Invalid infrastructure attempts retained separately: {len(invalid_rows)}. Missing combinations: {len(missing)}.",
        "",
        "## Aggregate Results",
        "",
        "| Batch size | Source headers (micro) | Project mean (macro) | Converged projects | Avg. rounds | Runs at round limit |",
        "|---:|---:|---:|---:|---:|---:|",
    ]
    for item in aggregate:
        lines.append(
            f"| {item['batch_size']} | {item['source_success']}/{item['source_total']} "
            f"({_percent(item['source_micro_success_rate'])}) | "
            f"{_percent(item['source_macro_success_rate'])} | "
            f"{item['converged_projects']}/{item['projects']} "
            f"({_percent(item['project_convergence_rate'])}) | "
            f"{item['average_rounds']:.2f} | {item['max_round_runs']}/{item['projects']} |"
        )

    lines.extend([
        "",
        "## Per-Project Comparison",
        "",
        "| Project | Source total | BS=1 | BS=2 | BS=3 | BS=5 | Best batch size |",
        "|---|---:|---:|---:|---:|---:|---|",
    ])
    for item in project_summary:
        lines.append(
            f"| {item['project']} | {item['source_total']} | {item['bs1_success']} | "
            f"{item['bs2_success']} | {item['bs3_success']} | {item['bs5_success']} | "
            f"{item['best_batch_sizes']} |"
        )

    lines.extend([
        "",
        "## Valid Runs",
        "",
        "| Project | BS | Run ID | Source headers | Generated headers | Converged | Rounds | Failed source headers |",
        "|---|---:|---|---:|---:|---|---:|---|",
    ])
    for row in rows:
        lines.append(
            f"| {row['project']} | {row['batch_size']} | `{row['run_id']}` | "
            f"{row['source_success']}/{row['source_total']} | "
            f"{row['generated_success']}/{row['generated_total']} | "
            f"{'yes' if row['converged'] else 'no'} | {row['rounds_used']} | "
            f"{', '.join(row['failed_source_headers']) or '-'} |"
        )

    lines.extend([
        "",
        "## Invalid Infrastructure Attempts",
        "",
        "These attempts are excluded from all aggregate results; their run directories and logs remain preserved.",
        "",
        "| Project | BS | Run ID | Return code |",
        "|---|---:|---|---:|",
    ])
    for row in invalid_rows:
        lines.append(
            f"| {row['project']} | {row['batch_size']} | `{row['run_id']}` | {row['returncode']} |"
        )
    lines.append("")
    return "\n".join(lines)


def _percent(value: float) -> str:
    return f"{value * 100:.2f}%"


def _write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]), extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({
                key: ";".join(value) if isinstance(value, list) else value
                for key, value in row.items()
            })


if __name__ == "__main__":
    raise SystemExit(main())
