from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Dict, List

from graph import Header, Project
from utils.compile_feedback import CompileFeedback
from .models import HeaderBatchRecord


def write_iteration_report(
    project: Project,
    records: List[HeaderBatchRecord],
    result_dir: Path,
    max_header_rounds: int,
    header_batch_size: int,
    mode: str = "batched_iterative",
) -> None:
    """写入 header 翻译轮次、模式和编译结果报告。"""
    def _preview(code: str, max_lines: int = 5, max_chars: int = 200) -> str:
        """生成代码片段预览文本。

        参数:
            code: 待预览的源码字符串。
            max_lines: 最大保留行数，默认为 5。
            max_chars: 最大保留字符数，默认为 200。

        返回:
            截断后的预览字符串；空输入时返回 "(empty)"。
        """
        if not code:
            return "(empty)"
        lines = code.strip().splitlines()
        preview_lines = lines[:max_lines]
        text = "\n".join(preview_lines)
        if len(text) > max_chars:
            text = text[:max_chars].rstrip() + "..."
        if len(lines) > max_lines:
            text += f"\n... ({len(lines)} lines total)"
        return text

    report_path = result_dir / "iteration_report.md"
    lines: List[str] = []

    lines.append(f"# Translation Iteration Report")
    lines.append(f"")
    lines.append(f"| Item | Value |")
    lines.append(f"|------|-------|")
    lines.append(f"| Project | {project.name} |")
    lines.append(f"| Generated | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} |")
    lines.append(f"| Total headers | {len(project.headers)} |")
    lines.append(f"| Original (java) | {sum(1 for h in project.headers if h.source_kind == 'java')} |")
    lines.append(f"| Generated external | {sum(1 for h in project.headers if h.is_generated_external())} |")
    lines.append(f"| Total rounds | {max(r['round_idx'] for r in records) if records else 0} |")
    lines.append(f"| Max rounds | {max_header_rounds} |")
    lines.append(f"| Batch size | {header_batch_size} |")
    lines.append(f"| Translation mode | {mode} |")
    lines.append(f"")

    rounds: Dict[int, List[HeaderBatchRecord]] = {}
    for record in records:
        rounds.setdefault(record["round_idx"], []).append(record)

    header_map = {h.key: h for h in project.headers}

    for round_idx in sorted(rounds):
        round_records = rounds[round_idx]
        is_round1 = round_idx == 1

        total_add = sum(len(r["add_patches"]) for r in round_records)
        total_modify = sum(len(r["modify_patches"]) for r in round_records)
        total_errors = sum(
            sum(1 for cr in r["compile_results"] if not cr.success)
            for r in round_records
        )
        translated_batches = sum(1 for r in round_records if r["add_patches"] or r["modify_patches"])
        skipped_batches = len(round_records) - translated_batches

        lines.append(f"---")
        lines.append(f"")
        lines.append(f"## Round {round_idx}")
        lines.append(f"")
        lines.append(f"| Metric | Value |")
        lines.append(f"|--------|-------|")
        lines.append(f"| Batches | {len(round_records)} |")
        lines.append(f"| Batches translated | {translated_batches} |")
        lines.append(f"| Batches skipped | {skipped_batches} |")
        lines.append(f"| Add patches | {total_add} |")
        lines.append(f"| Modify patches | {total_modify} |")
        if not is_round1:
            lines.append(f"| Pre-compile errors | {total_errors} |")
        lines.append(f"")

        for batch_idx, record in enumerate(round_records):
            batch_num = batch_idx + 1
            lines.append(f"### Batch {batch_num}")
            lines.append(f"")

            batch_key_list = record["batch_headers"]
            lines.append(f"**Headers ({len(batch_key_list)}):** {', '.join(batch_key_list)}")
            lines.append(f"")

            if not is_round1 and record["compile_results"]:
                lines.append(f"#### Pre-existing compile errors")
                lines.append(f"")
                lines.append(f"| Header | Status | Errors |")
                lines.append(f"|--------|--------|--------|")
                for cr in record["compile_results"]:
                    status = "OK" if cr.success else "FAIL"
                    display_errors = list(cr.local_compile_errors)
                    for error in cr.project_compile_errors:
                        location = error.file_path or "unknown"
                        if error.line:
                            location += f":{error.line}"
                            if error.column:
                                location += f":{error.column}"
                        display_errors.append(
                            f"[project:{location}] [{error.type}] {error.detail}"
                        )
                    display_errors = list(dict.fromkeys(display_errors))
                    if display_errors:
                        err_text = "  \n".join(f"  - {e}" for e in display_errors[:5])
                        if len(display_errors) > 5:
                            err_text += f"  \n  - ... (+{len(display_errors) - 5} more)"
                    else:
                        err_text = "-"
                    lines.append(f"| {cr.header} | {status} | {err_text} |")
                lines.append(f"")

            fb_blocks = record.get("feedback_blocks", {})
            if fb_blocks:
                lines.append(f"#### Feedback sent to LLM")
                lines.append(f"")
                for key in batch_key_list:
                    fb = fb_blocks.get(key)
                    if fb:
                        lines.append(f"- **{key}:**")
                        lines.append(f"  ```")
                        for line in fb.split("\n"):
                            lines.append(f"  {line}")
                        lines.append(f"  ```")
                lines.append(f"")

            for key in batch_key_list:
                h = header_map.get(key)
                if h is None:
                    continue
                cpp_preview = _preview(h.translated_code) if h.translated_code else "(not yet translated)"
                lines.append(f"- **{key}** ({h.type or h.source_kind})")
                lines.append(f"")
                lines.append(f"  ```cpp")
                for line in cpp_preview.split("\n"):
                    lines.append(f"  {line}")
                lines.append(f"  ```")
            lines.append(f"")

            if record["add_patches"]:
                lines.append(f"#### Added headers ({len(record['add_patches'])})")
                lines.append(f"")
                for patch in record["add_patches"]:
                    lines.append(f"- **{patch.class_name}** -> `{patch.file_name}`")
                    if patch.fields:
                        lines.append(f"  - Fields: {', '.join(patch.fields)}")
                    if patch.methods:
                        lines.append(f"  - Methods: {', '.join(patch.methods)}")
                    if patch.content:
                        lines.append(f"  - Content preview:")
                        lines.append(f"    ```cpp")
                        lines.append(f"    {_preview(patch.content, max_lines=8, max_chars=300)}")
                        lines.append(f"    ```")
                lines.append(f"")

            if record["modify_patches"]:
                lines.append(f"#### Modified ({len(record['modify_patches'])})")
                lines.append(f"")
                for patch in record["modify_patches"]:
                    lines.append(f"- **{patch.class_name}** `[{patch.modified_part}]`")
                    old_preview = patch.original_str[:200]
                    new_preview = patch.new_str[:200]
                    if len(patch.original_str) > 200:
                        old_preview += "..."
                    if len(patch.new_str) > 200:
                        new_preview += "..."
                    lines.append(f"  ```diff")
                    lines.append(f"  - {old_preview}")
                    lines.append(f"  + {new_preview}")
                    lines.append(f"  ```")
                lines.append(f"")

        lines.append(f"### Round {round_idx} compile results")
        lines.append(f"")
        round_success = sum(1 for h in project.headers if h.latest_compile_status == "success")
        round_failed = sum(1 for h in project.headers if h.latest_compile_status == "failed")
        round_unknown = len(project.headers) - round_success - round_failed
        lines.append(f"| Status | Count |")
        lines.append(f"|--------|-------|")
        lines.append(f"| Success | {round_success} |")
        lines.append(f"| Failed | {round_failed} |")
        if round_unknown:
            lines.append(f"| Unknown | {round_unknown} |")
        lines.append(f"")

        if round_failed > 0:
            lines.append(f"| Header | Errors |")
            lines.append(f"|--------|--------|")
            for h in project.headers:
                if h.latest_compile_status != "failed":
                    continue
                err_parts: List[str] = []
                for report in h.compile_reports:
                    if isinstance(report, CompileFeedback):
                        for issue in report.issues:
                            if issue.detail:
                                err_parts.append(f"[{issue.type}] {issue.detail[:150]}")
                        for issue in report.project_dependency_issues:
                            if issue.detail:
                                err_parts.append(f"[project_dependency:{issue.type}] {issue.detail[:150]}")
                        for issue in report.external_issues:
                            if issue.detail:
                                err_parts.append(f"[external:{issue.type}] {issue.detail[:150]}")
                    elif isinstance(report, dict):
                        issue_groups = [
                            ("", report.get("issues", [])),
                            ("project_dependency:", report.get("project_dependency_issues", [])),
                            ("external:", report.get("external_issues", [])),
                        ]
                        for prefix, issues in issue_groups:
                            for issue in issues:
                                if isinstance(issue, dict):
                                    detail = issue.get("detail", "")
                                    issue_type = issue.get("type", "")
                                else:
                                    detail = issue.detail
                                    issue_type = issue.type
                                if detail:
                                    err_parts.append(f"[{prefix}{issue_type}] {detail[:150]}")
                err_text = "  \n".join(f"  - {e}" for e in err_parts[:5]) if err_parts else h.compile_output[:300] if h.compile_output else "-"
                if len(err_parts) > 5:
                    err_text += f"  \n  - ... (+{len(err_parts) - 5} more)"
                lines.append(f"| {h.key} | {err_text} |")
            lines.append(f"")

        lines.append(f"")
        lines.append(f"---")
        lines.append(f"")

    lines.append(f"## Final Project State")
    lines.append(f"")
    lines.append(f"| # | Header | Type | Status | Source kind | Lines (C++) |")
    lines.append(f"|---|--------|------|--------|-------------|-------------|")
    for i, h in enumerate(project.headers, 1):
        status = h.latest_compile_status or "unknown"
        cpp_lines = len(h.translated_code.splitlines()) if h.translated_code else 0
        lines.append(
            f"| {i} | {h.key} | {h.type or '-'} | {status} | {h.source_kind} | {cpp_lines} |"
        )

    report_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Iteration report written to {report_path}")


def remove_isolated_generated_headers(project: Project) -> None:
    """移除未被任何自定义头文件引用的孤立生成外部 Header。

    职责:
        遍历项目内自定义 Header 的包含关系，收集被引用的外部生成 Header；
        未被任何引用且属于 generated_external 类型的 Header 会从项目中移除。

    参数:
        project: 需要清理孤立生成 Header 的项目对象。
    """
    included_keys: set[str] = set()
    for header in project.headers:
        if header.is_generated_external():
            continue
        _, included_custom = project.get_included(header)
        included_keys.update(h.key for h in included_custom)

    removed = []
    kept = []
    for header in project.headers:
        if header.is_generated_external() and header.key not in included_keys:
            removed.append(header.key)
        else:
            kept.append(header)

    if removed:
        print(f"  Removing {len(removed)} isolated generated headers: {removed}")
        project.headers = kept
