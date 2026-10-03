from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any


APPROACH_DIR = Path(__file__).resolve().parents[2]
PROJECT_ROOT = APPROACH_DIR.parent
if str(APPROACH_DIR) not in sys.path:
    sys.path.insert(0, str(APPROACH_DIR))

from path_config import cfg_all_project_names  # noqa: E402


VERSION = "v4_7"


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate paper-ready final C++ compile result tables.")
    parser.add_argument("--ai", default="deepseek")
    parser.add_argument("--output-name", default="paper_compile_results")
    args = parser.parse_args()

    output_root = PROJECT_ROOT / "output" / VERSION
    out_dir = output_root / "batch_experiments" / args.output_name
    out_dir.mkdir(parents=True, exist_ok=True)

    rows = [_best_project_row(output_root, args.ai, project) for project in cfg_all_project_names(VERSION)]
    summary = _summarize(rows)

    _write_csv(rows, out_dir / "full_pipeline_compile_table.csv")
    _write_markdown(rows, summary, out_dir / "full_pipeline_compile_table.md")
    _write_latex(rows, summary, out_dir / "full_pipeline_compile_table.tex")
    _write_json(out_dir / "full_pipeline_compile_table.json", {**summary, "rows": rows})

    print(out_dir)
    print(
        f"cpp_overall={summary['successfully_compiled_cpp_files']}/"
        f"{summary['generated_cpp_files']} ({summary['overall_file_compile_pass_rate'] * 100:.2f}%)"
    )
    print(
        f"translation_unit_overall={summary['successfully_compiled_translation_units']}/"
        f"{summary['generated_translation_units']} ({summary['overall_translation_unit_pass_rate'] * 100:.2f}%)"
    )
    print(
        f"project_full_pass={summary['units_with_all_generated_cpp_files_compiled']}/"
        f"{summary['units_with_generated_cpp_files']}"
    )
    return 0


def _best_project_row(output_root: Path, ai_name: str, project: str) -> dict[str, Any]:
    candidates = []
    for summary_path in (output_root / project / ai_name / "runs").glob("*/result/compile_report/cpp_compile_summary.json"):
        run_id = summary_path.parents[2].name
        if "alphatrans" in run_id:
            continue
        data = _load_json(summary_path)
        if not data:
            continue
        total = int(data.get("total_count") or 0)
        success = int(data.get("success_count") or 0)
        failed = int(data.get("failed_count") or 0)
        rate = float(data.get("success_rate") or (success / total if total else 0.0))
        candidates.append(
            {
                "project": project,
                "run_id": run_id,
                "compiled_cpp_files": success,
                "total_cpp_files": total,
                "failed_cpp_files": failed,
                "compile_pass_rate": rate,
                **_header_compile_fields(summary_path.parents[2]),
                "mtime": summary_path.stat().st_mtime,
            }
        )
    if not candidates:
        return {
            "project": project,
            "run_id": "N/A",
            "compiled_cpp_files": "",
            "total_cpp_files": "",
            "failed_cpp_files": "",
            "compile_pass_rate": "",
            "compiled_header_units": "",
            "total_header_units": "",
            "failed_header_units": "",
            "header_pass_rate": "",
            "status": "No final compile report",
        }

    best = max(
        candidates,
        key=lambda item: (
            item["compiled_cpp_files"],
            item["compile_pass_rate"],
            item["total_cpp_files"],
            item["mtime"],
        ),
    )
    best.pop("mtime", None)
    if best["total_cpp_files"] == 0:
        best["status"] = "No generated .cpp files"
    elif best["failed_cpp_files"] == 0 and best.get("failed_header_units", 0) in {0, ""}:
        best["status"] = "All files compiled"
    else:
        best["status"] = "Partial compile success"
    return best


def _header_compile_fields(run_dir: Path) -> dict[str, Any]:
    data = _load_json(run_dir / "result" / "compile_report" / "header_compile_summary.json")
    if not data:
        return {
            "compiled_header_units": "",
            "total_header_units": "",
            "failed_header_units": "",
            "header_pass_rate": "",
        }
    total = int(data.get("total_count") or 0)
    success = int(data.get("success_count") or 0)
    failed = int(data.get("failed_count") or 0)
    return {
        "compiled_header_units": success,
        "total_header_units": total,
        "failed_header_units": failed,
        "header_pass_rate": float(data.get("success_rate") or (success / total if total else 0.0)),
    }


def _summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    measured = [row for row in rows if isinstance(row["total_cpp_files"], int) and row["total_cpp_files"] > 0]
    zero_cpp = [row for row in rows if row["total_cpp_files"] == 0]
    missing = [row for row in rows if row["total_cpp_files"] == ""]
    full_pass = [row for row in measured if row["failed_cpp_files"] == 0]

    total_success = sum(row["compiled_cpp_files"] for row in measured)
    total_files = sum(row["total_cpp_files"] for row in measured)
    total_failed = sum(row["failed_cpp_files"] for row in measured)
    header_measured = [row for row in rows if isinstance(row.get("total_header_units"), int) and row["total_header_units"] > 0]
    header_success = sum(row["compiled_header_units"] for row in header_measured)
    header_total = sum(row["total_header_units"] for row in header_measured)
    header_failed = sum(row["failed_header_units"] for row in header_measured)
    overall_rate = total_success / total_files if total_files else 0.0
    translation_unit_success = total_success + header_success
    translation_unit_total = total_files + header_total
    translation_unit_failed = total_failed + header_failed
    return {
        "benchmark_units": len(rows),
        "units_with_final_compile_report": len(measured) + len(zero_cpp),
        "units_with_generated_cpp_files": len(measured),
        "units_with_all_generated_cpp_files_compiled": len(full_pass),
        "generated_cpp_files": total_files,
        "successfully_compiled_cpp_files": total_success,
        "failed_cpp_files": total_failed,
        "overall_file_compile_pass_rate": overall_rate,
        "generated_header_units": header_total,
        "successfully_compiled_header_units": header_success,
        "failed_header_units": header_failed,
        "overall_header_unit_pass_rate": header_success / header_total if header_total else 0.0,
        "generated_translation_units": translation_unit_total,
        "successfully_compiled_translation_units": translation_unit_success,
        "failed_translation_units": translation_unit_failed,
        "overall_translation_unit_pass_rate": translation_unit_success / translation_unit_total if translation_unit_total else 0.0,
        "missing_final_compile_report_projects": [row["project"] for row in missing],
        "zero_cpp_projects": [row["project"] for row in zero_cpp],
    }


def _write_csv(rows: list[dict[str, Any]], path: Path) -> None:
    fields = [
        "project",
        "run_id",
        "compiled_cpp_files",
        "total_cpp_files",
        "failed_cpp_files",
        "compile_pass_rate_percent",
        "compiled_header_units",
        "total_header_units",
        "failed_header_units",
        "header_pass_rate_percent",
        "compiled_translation_units",
        "total_translation_units",
        "failed_translation_units",
        "translation_unit_pass_rate_percent",
        "status",
    ]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    "project": row["project"],
                    "run_id": row["run_id"],
                    "compiled_cpp_files": row["compiled_cpp_files"],
                    "total_cpp_files": row["total_cpp_files"],
                    "failed_cpp_files": row["failed_cpp_files"],
                    "compile_pass_rate_percent": _rate_percent(row),
                    "compiled_header_units": row.get("compiled_header_units", ""),
                    "total_header_units": row.get("total_header_units", ""),
                    "failed_header_units": row.get("failed_header_units", ""),
                    "header_pass_rate_percent": _header_rate_percent(row),
                    "compiled_translation_units": _translation_unit_success(row),
                    "total_translation_units": _translation_unit_total(row),
                    "failed_translation_units": _translation_unit_failed(row),
                    "translation_unit_pass_rate_percent": _translation_unit_rate_percent(row),
                    "status": row["status"],
                }
            )


def _write_markdown(rows: list[dict[str, Any]], summary: dict[str, Any], path: Path) -> None:
    lines = [
        "# Full-Pipeline C++ File Compilation Results",
        "",
        "Table reports final per-project `.cpp` file compilation results after the full translation pipeline and agent repair. The overall file-level pass rate is computed over projects with a final compile report and at least one generated `.cpp` file.",
        "",
        "| Metric | Value |",
        "|---|---:|",
        f"| Benchmark units | {summary['benchmark_units']} |",
        f"| Units with final compile report | {summary['units_with_final_compile_report']} |",
        f"| Units with generated `.cpp` files | {summary['units_with_generated_cpp_files']} |",
        f"| Units with all generated `.cpp` files compiled | {summary['units_with_all_generated_cpp_files_compiled']} |",
        f"| Generated `.cpp` files | {summary['generated_cpp_files']} |",
        f"| Successfully compiled `.cpp` files | {summary['successfully_compiled_cpp_files']} |",
        f"| Failed `.cpp` files | {summary['failed_cpp_files']} |",
        f"| Overall file compilation pass rate | {summary['overall_file_compile_pass_rate'] * 100:.2f}% |",
        f"| Header self-compile units | {summary['generated_header_units']} |",
        f"| Successfully compiled header units | {summary['successfully_compiled_header_units']} |",
        f"| Header self-compile pass rate | {summary['overall_header_unit_pass_rate'] * 100:.2f}% |",
        f"| Overall translation-unit pass rate (`.cpp` + header self-compile) | {summary['overall_translation_unit_pass_rate'] * 100:.2f}% |",
        "",
        "| Project | `.cpp` Compiled / Total | Header Units Compiled / Total | Overall TU Pass Rate | Status |",
        "|---|---:|---:|---:|---|",
    ]
    for row in rows:
        lines.append(
            f"| {row['project']} | {_compiled_total(row)} | {_header_compiled_total(row)} | {_translation_unit_rate_percent(row)} | {row['status']} |"
        )
    lines.extend(
        [
            "",
            "Notes: header units are synthetic translation units that include one generated header at a time. They account for template and header-only implementations that are not represented by standalone `.cpp` files. `N/A` denotes missing compile reports; `0 / 0` cases are excluded from the corresponding denominator.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_latex(rows: list[dict[str, Any]], summary: dict[str, Any], path: Path) -> None:
    lines = [
        r"\begin{table}[t]",
        r"\centering",
        r"\caption{Full-pipeline C++ file compilation results after agent repair.}",
        r"\label{tab:full_pipeline_compile}",
        r"\begin{tabular}{lrrrr}",
        r"\toprule",
        r"Project & Compiled & Total & Failed & Pass rate \\",
        r"\midrule",
    ]
    for row in rows:
        project = row["project"].replace("_", r"\_")
        if not isinstance(row["total_cpp_files"], int):
            lines.append(f"{project} & N/A & N/A & N/A & N/A \\\\")
        elif row["total_cpp_files"] == 0:
            lines.append(f"{project} & 0 & 0 & 0 & N/A \\\\")
        else:
            lines.append(
                f"{project} & {row['compiled_cpp_files']} & {row['total_cpp_files']} & "
                f"{row['failed_cpp_files']} & {row['compile_pass_rate'] * 100:.2f}\\% \\\\")
    lines.extend(
        [
            r"\midrule",
            f"Overall & {summary['successfully_compiled_cpp_files']} & {summary['generated_cpp_files']} & {summary['failed_cpp_files']} & {summary['overall_file_compile_pass_rate'] * 100:.2f}\\% \\\\",
            r"\bottomrule",
            r"\end{tabular}",
            r"\end{table}",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _compiled_total(row: dict[str, Any]) -> str:
    if not isinstance(row["total_cpp_files"], int):
        return "N/A"
    return f"{row['compiled_cpp_files']} / {row['total_cpp_files']}"


def _rate_percent(row: dict[str, Any]) -> str:
    if not isinstance(row["total_cpp_files"], int) or row["total_cpp_files"] == 0:
        return "N/A"
    return f"{row['compile_pass_rate'] * 100:.2f}%"


def _header_compiled_total(row: dict[str, Any]) -> str:
    if not isinstance(row.get("total_header_units"), int):
        return "N/A"
    return f"{row['compiled_header_units']} / {row['total_header_units']}"


def _header_rate_percent(row: dict[str, Any]) -> str:
    if not isinstance(row.get("total_header_units"), int) or row["total_header_units"] == 0:
        return "N/A"
    return f"{row['header_pass_rate'] * 100:.2f}%"


def _translation_unit_success(row: dict[str, Any]) -> int | str:
    if not isinstance(row.get("total_cpp_files"), int):
        return ""
    header_success = row.get("compiled_header_units", 0)
    if not isinstance(header_success, int):
        header_success = 0
    return row["compiled_cpp_files"] + header_success


def _translation_unit_total(row: dict[str, Any]) -> int | str:
    if not isinstance(row.get("total_cpp_files"), int):
        return ""
    header_total = row.get("total_header_units", 0)
    if not isinstance(header_total, int):
        header_total = 0
    return row["total_cpp_files"] + header_total


def _translation_unit_failed(row: dict[str, Any]) -> int | str:
    if not isinstance(row.get("total_cpp_files"), int):
        return ""
    header_failed = row.get("failed_header_units", 0)
    if not isinstance(header_failed, int):
        header_failed = 0
    return row["failed_cpp_files"] + header_failed


def _translation_unit_rate_percent(row: dict[str, Any]) -> str:
    total = _translation_unit_total(row)
    success = _translation_unit_success(row)
    if not isinstance(total, int) or total == 0 or not isinstance(success, int):
        return "N/A"
    return f"{success / total * 100:.2f}%"


def _load_json(path: Path) -> dict[str, Any] | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _write_json(path: Path, data: dict[str, Any]) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
