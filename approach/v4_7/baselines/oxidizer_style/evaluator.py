from __future__ import annotations

import json
from pathlib import Path

from graph import Project

from .compiler import OxidizerCompiler


def evaluate_run(
    result_dir: Path,
    graph_dir: Path,
    compile_timeout: int = 60,
) -> dict:
    """Evaluate any SITP-compatible run using one common compile-first protocol."""
    result_dir = Path(result_dir)
    graph_dir = Path(graph_dir)
    report_dir = result_dir / "compile_report" / "common"
    has_stubs = _run_has_stubs(result_dir)
    compiler = OxidizerCompiler(timeout_seconds=compile_timeout)
    evaluation = compiler.evaluate_project(result_dir, report_dir, has_stubs=has_stubs)

    project = Project.load(graph_dir)
    add_coarse_method_metrics(evaluation, project, _stubbed_fragment_ids(result_dir))
    (report_dir / "common_evaluation.json").write_text(
        json.dumps(evaluation, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return evaluation


def add_coarse_method_metrics(
    evaluation: dict,
    project: Project,
    stubbed_fragment_ids: set[str] | None = None,
) -> dict:
    """Attach source-method compilation metrics to an existing file evaluation."""
    stubbed_fragment_ids = stubbed_fragment_ids or set()
    header_results = {item["file"]: item for item in evaluation["headers"]}
    source_results = {item["file"]: item for item in evaluation["sources"]}
    method_rows = []
    for header in project.headers:
        # 手写桩仅提供外部依赖，不计入模型翻译方法的覆盖与编译统计。
        if header.is_generated_external() or header.is_manual_stub():
            continue
        for method in header.methods:
            if method.is_added_method:
                continue
            artifact_name, artifact_result = _method_artifact_result(
                header, method, header_results, source_results
            )
            represented = bool(
                method.translated_code.strip()
                or method.mapping_status
                in {"already_implemented", "pure_virtual", "defaulted_or_deleted"}
            )
            stubbed = f"method:{method.key}" in stubbed_fragment_ids
            success = (
                represented
                and not stubbed
                and bool(artifact_result and artifact_result["compile_success"])
            )
            method_rows.append(
                {
                    "method": method.key,
                    "artifact": artifact_name,
                    "represented": represented,
                    "stubbed": stubbed,
                    "compile_success": success,
                    "source_loc": _source_loc(method.code),
                }
            )

    method_count = len(method_rows)
    method_success = sum(1 for row in method_rows if row["compile_success"])
    total_loc = sum(row["source_loc"] for row in method_rows)
    success_loc = sum(row["source_loc"] for row in method_rows if row["compile_success"])
    evaluation["coarse_methods"] = {
        "total": method_count,
        "success": method_success,
        "compile_rate": method_success / method_count if method_count else 0.0,
        "source_loc": total_loc,
        "successful_source_loc": success_loc,
        "source_loc_compile_rate": success_loc / total_loc if total_loc else 0.0,
        "details": method_rows,
    }
    return evaluation


def _method_artifact_result(header, method, header_results: dict, source_results: dict):
    in_header = method.method_body_location == "header" or method.mapping_status in {
        "already_implemented",
        "pure_virtual",
        "defaulted_or_deleted",
    }
    if in_header:
        name = header.get_output_header_name()
        return name, header_results.get(name)
    name = header.get_output_cpp_name()
    return name, source_results.get(name)


def _run_has_stubs(result_dir: Path) -> bool:
    report_path = result_dir / "oxidizer_report.json"
    if not report_path.exists():
        return False
    try:
        return int(json.loads(report_path.read_text(encoding="utf-8")).get("stub_count", 0)) > 0
    except Exception:
        return False


def _stubbed_fragment_ids(result_dir: Path) -> set[str]:
    fragments_path = result_dir / "fragments.jsonl"
    if not fragments_path.exists():
        return set()
    result = set()
    try:
        for line in fragments_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            record = json.loads(line)
            if record.get("stubbed"):
                result.add(record["fragment_id"])
    except (OSError, KeyError, json.JSONDecodeError):
        return set()
    return result


def _source_loc(source: str) -> int:
    return sum(1 for line in source.splitlines() if line.strip())
