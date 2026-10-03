from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from graph import Header, Project
from utils.compile_feedback import compact_issue_detail, CompileFeedback
from .third_party_libraries import ThirdPartyLibraryAvailability


class HeaderRepairContextBuilder:
    """Build compile-feedback blocks and repair context sections for header repair prompts."""

    def __init__(self, third_party_availability: ThirdPartyLibraryAvailability | None = None):
        """初始化修复上下文构建器。

        参数:
            third_party_availability: 第三方库可用性探测对象，可为 None。
        """
        self.third_party_availability = third_party_availability

    def build_repair_feedback_block(self, header: Header) -> str:
        """构建单个 Header 的编译反馈文本块。

        参数:
            header: 需要构建反馈的目标 Header。

        返回:
            格式化后的编译反馈字符串；无问题时返回提示文本。
        """
        if not header.compile_reports and not header.compile_output:
            return "(No compile issues reported.)"

        latest_report = self._get_latest_compile_report(header)
        if latest_report is None:
            return "(No compile issues reported.)"

        lines: List[str] = []
        if header.latest_compile_status:
            lines.append(f"Compile status: {header.latest_compile_status}")

        if latest_report.get("success"):
            return "\n".join(lines) if lines else "(No compile issues reported.)"

        if latest_report.get("blocked_by_dependency") and not latest_report.get("has_local_issues"):
            lines.append("Blocked by dependency-related compile failures outside this header.")
            dependency_issue_groups = [
                ("project_dependency", latest_report.get("project_dependency_issues", [])),
                ("external", latest_report.get("external_issues", [])),
            ]
            for category, issues in dependency_issue_groups:
                for issue in issues:
                    if not isinstance(issue, dict):
                        continue
                    issue_type = issue.get("type", "unknown")
                    detail = compact_issue_detail(str(issue.get("detail", "")))
                    if detail:
                        lines.append(f"[{category}:{issue_type}] {detail}")
            lines.append("Do not modify this header for dependency-only failures.")
            return "\n".join(lines)

        for issue in latest_report.get("issues", []):
            if not isinstance(issue, dict):
                continue
            issue_type = issue.get("type", "unknown")
            detail = issue.get("detail", "")
            compact = compact_issue_detail(str(detail)) if detail else ""
            if compact:
                lines.append(f"[{issue_type}] {compact}")
            else:
                lines.append(f"[{issue_type}]")
            third_party_feedback = self._build_third_party_feedback(issue_type, str(detail))
            if third_party_feedback:
                lines.append(third_party_feedback)

        if not lines and header.compile_output:
            lines.append(header.compile_output.strip())

        return "\n".join(lines) if lines else "(No compile issues reported.)"

    def _build_third_party_feedback(self, issue_type: str, detail: str) -> str:
        """针对编译问题生成第三方库相关的额外反馈。

        参数:
            issue_type: 编译问题类型。
            detail: 编译问题详情。

        返回:
            第三方库反馈字符串；无相关反馈时返回空字符串。
        """
        if self.third_party_availability is None:
            return ""
        return self.third_party_availability.feedback_for_issue(issue_type, detail)

    def _get_latest_compile_report(self, header: Header) -> Dict[str, Any] | None:
        """获取 Header 最新的编译报告（统一为字典形式）。

        参数:
            header: 目标 Header。

        返回:
            最新编译报告字典，无报告时返回 None。
        """
        if not header.compile_reports:
            return None

        latest_report = header.compile_reports[-1]
        if isinstance(latest_report, CompileFeedback):
            return latest_report.to_dict()
        if isinstance(latest_report, dict):
            return latest_report
        return None

    def build_repair_context_sections(
        self,
        project: Project,
        batch_headers: List[Header],
        max_context_headers: int = 4,
    ) -> str:
        """构建用于修复提示的上下文段落。

        职责:
            收集与批次相关且含编译问题的 Header 作为上下文，拼接成
            Markdown 样式文本段供 LLM 修复时参考。

        参数:
            project: 当前项目对象。
            batch_headers: 当前批次的 Header 列表。
            max_context_headers: 上下文 Header 数量上限，默认为 4。

        返回:
            拼接好的上下文文本段；无可用上下文时返回空字符串。
        """
        context_headers = self.collect_repair_context_headers(
            project,
            batch_headers,
            max_context_headers=max_context_headers,
        )
        if not context_headers:
            return ""

        sections: List[str] = []
        for header in context_headers:
            sections.append(
                "\n".join(
                    [
                        f"class name: {header.translated_class_name}",
                        f"File: {header.get_output_header_name()}",
                        f"Latest compile status: {header.latest_compile_status or 'unknown'}",
                        "Current file content:",
                        "```cpp",
                        self._truncate_code_for_context(header.translated_code),
                        "```",
                    ]
                )
            )
        return "\n\n".join(sections)

    def collect_repair_context_headers(
        self,
        project: Project,
        batch_headers: List[Header],
        max_context_headers: int = 4,
    ) -> List[Header]:
        """收集与批次相关的修复上下文 Header。

        职责:
        根据批次内 Header 的编译问题位置、包含关系筛选出可作为
        上下文的外部 Header，用于辅助修复提示。

        参数:
            project: 当前项目对象。
            batch_headers: 当前批次的 Header 列表。
            max_context_headers: 上下文 Header 数量上限，默认为 4。

        返回:
            选中作为上下文的 Header 列表。
        """
        batch_keys = {header.key for header in batch_headers}
        selected: List[Header] = []
        selected_keys: set[str] = set()

        def add_header(candidate: Header | None) -> None:
            """将候选 Header 加入上下文集合（跳过批次内、重复或空翻译的项）。"""
            if candidate is None:
                return
            if candidate.key in batch_keys or candidate.key in selected_keys:
                return
            if not candidate.translated_code.strip():
                return
            selected.append(candidate)
            selected_keys.add(candidate.key)

        for header in batch_headers:
            latest_report = self._get_latest_compile_report(header)
            if not latest_report or latest_report.get("success"):
                continue

            for issue in [
                *latest_report.get("issues", []),
                *latest_report.get("project_dependency_issues", []),
                *latest_report.get("external_issues", []),
            ]:
                if not isinstance(issue, dict):
                    continue
                location = issue.get("location", {}) or {}
                file_path = str(location.get("file_path", "")).strip()
                if file_path:
                    add_header(project.find_header_by_include_name(Path(file_path).name))

            _, included_headers = project.get_included(header)
            for included in included_headers:
                add_header(included)

            if len(selected) >= max_context_headers:
                break

        return selected[:max_context_headers]

    def _truncate_code_for_context(self, code: str, max_lines: int = 120, max_chars: int = 6000) -> str:
        """截断代码文本以适应上下文长度限制。

        参数:
            code: 待截断的源码字符串。
            max_lines: 最大保留行数，默认为 120。
            max_chars: 最大保留字符数，默认为 6000。

        返回:
            截断后的文本；空输入时返回 "(empty)"。
        """
        text = code.strip()
        if not text:
            return "(empty)"

        lines = text.splitlines()
        if len(lines) > max_lines:
            text = "\n".join(lines[:max_lines]) + f"\n... ({len(lines)} lines total)"
        if len(text) > max_chars:
            text = text[:max_chars].rstrip() + "\n... [truncated]"
        return text
