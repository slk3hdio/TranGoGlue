from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Sequence
import os
import re


# 编译问题模式映射：键为问题类型，值为匹配该类型的正则表达式列表
ISSUE_PATTERNS: list[tuple[str, list[str]]] = [
    ("missing_include", [r"fatal error: '([^']+)' file not found", r"No such file or directory"]),
    ("incomplete_base_class", [r"base class has incomplete type"]),
    ("forward_declare_insufficient", [r"incomplete type", r"invalid use of incomplete type"]),
    ("invalid_override", [r"only virtual member functions can be marked 'override'", r"marked 'override' but does not override"]),
    ("unknown_template", [r"no template named"]),
    ("invalid_inheritance", [r"expected class name", r"expected class-name"]),
    ("duplicate_definition", [r"redefinition of", r"multiple definition of"]),
    ("template_or_syntax", [r"expected ';'", r"declaration does not declare anything"]),
    ("unknown_type", [r"unknown type name", r"does not name a type"]),
]


@dataclass
class IssueLocation:
    """
    编译错误的位置信息。

    职责：
        - 描述单个编译错误出现的文件路径、行号和列号。
        - 作为 Issues 的组成部分，供下游分析与展示错误出现位置。

    使用约定：
        - 字段 file_path、line、column 均为可选，缺省值分别表示
          空路径、第 0 行、第 0 列（表示位置未知）。
        - 通过 to_dict() 可将位置信息转换为可 JSON 序列化的字典。
    """

    file_path: str = ""
    line: int = 0
    column: int = 0

    def to_dict(self) -> dict:
        """
        将位置信息转换为字典。

        返回:
            dict: 包含 file_path、line、column 三个键的字典。
        """
        return {"file_path": self.file_path, "line": self.line, "column": self.column}


@dataclass
class Issue:
    """
    表示一个已识别并规范化的编译问题。

    职责：
        - 聚合某个编译错误的问题类型 (type)、详情 (detail) 与其出现的
          位置 (location)。
        - 供上层模块按类型归类、去重并生成反馈。

    使用约定：
        - type 为规范化后的问题类型，未匹配到已知类型时使用
          "compile_error"。
        - location 默认自动创建为空位置的 IssueLocation。
        - 通过 to_dict() 转换为可序列化字典。
    """

    type: str
    detail: str
    location: IssueLocation = field(default_factory=IssueLocation)

    def to_dict(self) -> dict:
        """
        将编译问题转换为字典。

        返回:
            dict: 包含 type、detail、location 的字典。
        """
        return {
            "type": self.type,
            "detail": self.detail,
            "location": self.location.to_dict(),
        }


@dataclass
class CompileFeedback:
    """
    结构化保存整体编译反馈结果。

    职责：
        - 汇总原始诊断块、当前文件/项目依赖/外部错误块、规范化后的
          问题列表以及最终的小结日志，形成一次编译反馈的完整快照。
        - 提供当前文件错误和依赖阻塞标记，便于下游选择真正的修复目标。

    使用约定：
        - 通常由 analyze_compile_feedback 自动构造并填充，调用方无需
          手动逐项赋值。
        - 通过 to_dict() 可将整个反馈转换为可序列化字典。
    """

    diagnostic_blocks: List[str] = field(default_factory=list)
    local_blocks: List[str] = field(default_factory=list)
    project_dependency_blocks: List[str] = field(default_factory=list)
    external_blocks: List[str] = field(default_factory=list)
    issues: List[Issue] = field(default_factory=list)
    project_dependency_issues: List[Issue] = field(default_factory=list)
    external_issues: List[Issue] = field(default_factory=list)
    has_local_issues: bool = False
    has_project_dependency_issues: bool = False
    blocked_by_dependency: bool = False
    log_output: str = ""
    round: int = 0
    header: str = ""
    success: bool = False

    def to_dict(self) -> dict:
        """
        将编译反馈结果转换为可序列化字典。

        返回:
            dict: 包含反馈各字段的字典，其中三类问题会递归转换为
                  Issue 的字典表示。
        """
        return {
            "diagnostic_blocks": self.diagnostic_blocks,
            "local_blocks": self.local_blocks,
            "project_dependency_blocks": self.project_dependency_blocks,
            "external_blocks": self.external_blocks,
            "issues": [i.to_dict() for i in self.issues],
            "project_dependency_issues": [i.to_dict() for i in self.project_dependency_issues],
            "external_issues": [i.to_dict() for i in self.external_issues],
            "has_local_issues": self.has_local_issues,
            "has_project_dependency_issues": self.has_project_dependency_issues,
            "blocked_by_dependency": self.blocked_by_dependency,
            "log_output": self.log_output,
            "round": self.round,
            "header": self.header,
            "success": self.success,
        }


def analyze_compile_feedback(
    log_output: str,
    header_path: Path | str,
    *,
    owned_paths: Sequence[Path | str] | None = None,
    max_blocks: int = 6,
    max_lines_per_block: int = 14,
    max_chars: int = 12000,
) -> CompileFeedback:
    """
    分析编译反馈日志，提取并分类编译错误。

    参数:
        log_output: 编译输出的日志字符串
        header_path: 要分析的头文件路径
        owned_paths: 属于当前项目的文件路径序列，用于识别项目内依赖错误
        max_blocks: 最大保留的诊断块数量
        max_lines_per_block: 每个诊断块保留的最大行数
        max_chars: 总结日志的最大字符数

    返回:
        CompileFeedback 结构化诊断结果
    """
    header_path = Path(header_path)
    diagnostic_blocks = extract_diagnostic_blocks(log_output)
    local_blocks, project_dependency_blocks, external_blocks = split_blocks_by_header(
        diagnostic_blocks,
        header_path,
        owned_paths=owned_paths,
    )
    issues = normalize_issues(local_blocks, owned_paths=owned_paths)
    project_dependency_issues = normalize_issues(
        project_dependency_blocks,
        owned_paths=owned_paths,
    )
    external_issues = normalize_issues(external_blocks, owned_paths=owned_paths)
    blocked_by_dependency = not bool(issues) and bool(project_dependency_issues or external_issues)
    summarized_blocks = local_blocks or project_dependency_blocks or external_blocks

    return CompileFeedback(
        diagnostic_blocks=diagnostic_blocks,
        local_blocks=local_blocks,
        project_dependency_blocks=project_dependency_blocks,
        external_blocks=external_blocks,
        issues=issues,
        project_dependency_issues=project_dependency_issues,
        external_issues=external_issues,
        has_local_issues=bool(issues),
        has_project_dependency_issues=bool(project_dependency_issues),
        blocked_by_dependency=blocked_by_dependency,
        log_output=summarize_blocks(
            summarized_blocks,
            max_blocks=max_blocks,
            max_lines_per_block=max_lines_per_block,
            max_chars=max_chars,
        ),
    )


def summarize_blocks(
    blocks: Sequence[str],
    *,
    max_blocks: int = 6,
    max_lines_per_block: int = 14,
    max_chars: int = 12000,
) -> str:
    """
    总结诊断块，限制输出的块数量、每个块的行数和总字符数。

    参数:
        blocks: 诊断块序列
        max_blocks: 最大保留的诊断块数量
        max_lines_per_block: 每个诊断块保留的最大行数
        max_chars: 总结结果的最大字符数

    返回:
        总结后的诊断字符串
    """
    if not blocks:
        return ""

    selected_blocks = list(blocks[:max_blocks])
    summarized_blocks = []
    for block in selected_blocks:
        lines = block.splitlines()
        if len(lines) > max_lines_per_block:
            lines = [*lines[:max_lines_per_block], "... [truncated block]"]
        summarized_blocks.append("\n".join(lines))

    summary = "\n\n".join(summarized_blocks)
    if len(summary) > max_chars:
        summary = truncate_text(summary, max_chars)

    omitted_blocks = len(blocks) - len(selected_blocks)
    if omitted_blocks > 0:
        summary += f"\n\n... [{omitted_blocks} additional diagnostic blocks omitted]"
    return summary


def normalize_issues(
    diagnostic_blocks: Sequence[str],
    *,
    owned_paths: Sequence[Path | str] | None = None,
) -> List[Issue]:
    """
    规范化诊断块，提取问题类型、详情和位置信息，并去重。

    参数:
        diagnostic_blocks: 诊断块序列。
        owned_paths: 项目内 Header 路径；用于从标准库诊断栈回溯实际项目位置。

    返回:
        规范化后的问题列表
    """
    if not diagnostic_blocks:
        return []

    issues: List[Issue] = []
    for block in diagnostic_blocks:
        metadata = extract_issue_metadata(block, owned_paths=owned_paths)
        matched_issue_types = detect_issue_types(block)
        location = IssueLocation(**metadata.location) if metadata.location else IssueLocation()
        if matched_issue_types:
            for issue_type in matched_issue_types:
                issues.append(Issue(
                    type=issue_type,
                    detail=metadata.detail,
                    location=location,
                ))
            continue

        detail = metadata.detail
        if detail:
            issues.append(Issue(
                type="compile_error",
                detail=detail,
                location=location,
            ))

    deduped = []
    seen = set()
    for issue in issues:
        key = (issue.type, issue.detail)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(issue)
    return deduped


def detect_issue_types(block: str) -> List[str]:
    """
    根据诊断块内容检测问题类型。

    参数:
        block: 单个诊断块字符串

    返回:
        匹配到的问题类型列表
    """
    matched_issue_types = []
    lowered = block.lower()
    for issue_type, regexes in ISSUE_PATTERNS:
        matched = any(re.search(pattern, block, re.IGNORECASE) for pattern in regexes)
        if not matched and issue_type == "missing_include":
            matched = "no such file or directory" in lowered or "file not found" in lowered
        if matched:
            matched_issue_types.append(issue_type)
    return matched_issue_types


def compact_issue_detail(detail: str, max_chars: int = 240) -> str:
    """
    压缩问题详情，保留关键信息并限制长度。

    参数:
        detail: 原始问题详情字符串
        max_chars: 压缩后的最大字符数

    返回:
        压缩后的问题详情
    """
    lines = [line.rstrip() for line in detail.splitlines() if line.strip()]
    if not lines:
        return ""

    primary = ""
    source_line = ""
    marker_line = ""
    note_line = ""

    for index, line in enumerate(lines):
        stripped = line.strip()
        if not primary and (" error:" in stripped or " fatal error:" in stripped or stripped.startswith("error:")):
            primary = stripped
            for follow in lines[index + 1 :]:
                follow_stripped = follow.strip()
                if not follow_stripped:
                    continue
                if not source_line and not _looks_like_diagnostic_metadata(follow_stripped):
                    source_line = follow_stripped
                    continue
                if source_line and not marker_line and re.fullmatch(r"[\^~ ]+", follow_stripped):
                    marker_line = follow_stripped
                    continue
                if " note:" in follow_stripped or follow_stripped.startswith("note:"):
                    note_line = follow_stripped
                    break
            break

    compact_parts = [primary or lines[0].strip()]
    if source_line:
        compact_parts.append(f"source: {source_line}")
    if marker_line:
        compact_parts.append(f"marker: {marker_line}")
    if note_line:
        compact_parts.append(note_line)

    compact = " | ".join(" ".join(part.split()) for part in compact_parts if part)
    if len(compact) > max_chars:
        compact = compact[:max_chars].rstrip() + "..."
    return compact


def extract_diagnostic_blocks(log_output: str) -> List[str]:
    """
    从编译日志中提取诊断块，每个块包含一个错误及其上下文。

    参数:
        log_output: 编译输出的日志字符串

    返回:
         诊断块列表
    """
    lines = log_output.splitlines()
    if not lines:
        return []

    blocks: List[List[str]] = []
    current_block: List[str] = []
    recent_include_context: List[str] = []

    for line in lines:
        stripped = line.strip()
        if not stripped:
            if current_block:
                current_block.append(line)
            continue

        if stripped.startswith("In file included from"):
            recent_include_context.append(line)
            if len(recent_include_context) > 3:
                recent_include_context = recent_include_context[-3:]
            if current_block:
                current_block.append(line)
            continue

        if " error:" in line or stripped.startswith("error:") or " fatal error:" in line:
            if current_block:
                blocks.append(current_block)
            current_block = [*recent_include_context, line]
            continue

        if current_block:
            current_block.append(line)

    if current_block:
        blocks.append(current_block)

    if not blocks:
        return [log_output]

    return [clean_block_lines(block) for block in blocks]


@dataclass
class IssueMetadata:
    """
    保存从单个诊断块中提取的元数据。

    职责：
        - 记录问题详情 (detail) 与可选的定位信息 (location)。
        - 供 extract_issue_metadata 的调用方直接消费，无需关心底层
          正则/行的解析细节。

    使用约定：
        - location 默认为空字典，仅在成功解析出位置时填充。
        - detail 为提炼后的错误描述文本。
    """

    detail: str
    location: dict = field(default_factory=dict)


def extract_issue_metadata(
    block: str,
    *,
    owned_paths: Sequence[Path | str] | None = None,
) -> IssueMetadata:
    """
    从诊断块中提取问题元数据，包括详情和位置信息。

    参数:
        block: 单个诊断块字符串。
        owned_paths: 项目内 Header 路径；主错误位于项目外时用于回溯归因位置。

    返回:
        IssueMetadata 包含详情和位置
    """
    lines = [line.rstrip("\n") for line in block.splitlines()]
    error_line = first_error_line(block) or (lines[0].strip() if lines else "")
    location = resolve_diagnostic_location(block, owned_paths=owned_paths)

    source_line = ""
    marker_line = ""
    note_line = ""

    for index, line in enumerate(lines):
        stripped = line.strip()
        if stripped != error_line.strip():
            continue
        for follow in lines[index + 1 :]:
            follow_stripped = follow.strip()
            if not follow_stripped:
                continue
            if not source_line and not _looks_like_diagnostic_metadata(follow_stripped):
                source_line = _normalize_source_excerpt_line(follow.rstrip())
                continue
            if source_line and not marker_line and re.fullmatch(r"[\^~ ]+", follow_stripped):
                marker_line = _normalize_marker_excerpt_line(follow.rstrip())
                continue
            if " note:" in follow_stripped or follow_stripped.startswith("note:"):
                note_line = follow.rstrip()
                break
        break

    if not source_line and location.get("file_path") and location.get("line"):
        source_line = read_source_line(location["file_path"], int(location["line"]))

    detail_lines = [error_line] if error_line else []
    if source_line:
        detail_lines.append(source_line)
    if marker_line:
        detail_lines.append(marker_line)
    if note_line:
        detail_lines.append(note_line)
    if not detail_lines:
        detail_lines = [block.strip()]

    return IssueMetadata(
        detail="\n".join(line for line in detail_lines if line).strip(),
        location=location,
    )


def split_blocks_by_header(
    blocks: Sequence[str],
    header_path: Path | str,
    *,
    owned_paths: Sequence[Path | str] | None = None,
) -> tuple[List[str], List[str], List[str]]:
    """
    将诊断块分割为当前文件、项目内依赖和项目外依赖三类。

    参数:
        blocks: 诊断块序列
        header_path: 要分析的头文件路径
        owned_paths: 属于当前项目的文件路径序列。

    返回:
        tuple: 当前文件块、项目内依赖块和项目外依赖块。
    """
    header_path = Path(header_path)
    owned_paths = list(owned_paths or [])
    normalized_header_path = normalize_path_for_compare(str(header_path))
    normalized_owned_paths = {
        normalize_path_for_compare(str(path))
        for path in owned_paths
    }
    normalized_owned_paths.discard(normalized_header_path)
    header_name = header_path.name.lower()
    project_dependency_names = {
        Path(path).name.lower()
        for path in owned_paths
        if normalize_path_for_compare(str(path)) != normalized_header_path
    }
    local_blocks: List[str] = []
    project_dependency_blocks: List[str] = []
    external_blocks: List[str] = []

    for block in blocks:
        resolved_location = resolve_diagnostic_location(block, owned_paths=owned_paths)
        error_path = resolved_location.get("file_path", "")
        if error_path:
            normalized_error_path = normalize_path_for_compare(error_path)
            if normalized_error_path == normalized_header_path:
                local_blocks.append(block)
            elif normalized_error_path in normalized_owned_paths:
                project_dependency_blocks.append(block)
            elif _is_relative_diagnostic_path(error_path):
                error_name = Path(error_path).name.lower()
                if error_name == header_name:
                    local_blocks.append(block)
                elif error_name in project_dependency_names:
                    project_dependency_blocks.append(block)
                else:
                    external_blocks.append(block)
            else:
                external_blocks.append(block)
            continue

        error_line = first_error_line(block).lower()
        if header_name and header_name in error_line:
            local_blocks.append(block)
        elif any(owned_name in error_line for owned_name in project_dependency_names):
            project_dependency_blocks.append(block)
        else:
            external_blocks.append(block)

    return local_blocks, project_dependency_blocks, external_blocks


def _is_relative_diagnostic_path(path_str: str) -> bool:
    """判断诊断路径是否为相对路径，可安全使用文件名降级匹配。

    参数:
        path_str: 编译器诊断中的原始路径。

    返回:
        bool: 路径不是 POSIX 或 Windows 绝对路径时返回 True。
    """
    normalized = str(path_str).strip().replace("\\", "/")
    if not normalized:
        return False
    return not normalized.startswith("/") and not re.match(r"^[A-Za-z]:/", normalized)


def clean_block_lines(block_lines: Sequence[str]) -> str:
    """
    清理诊断块的行，保留最多2层包含上下文。

    参数:
        block_lines: 诊断块的行序列

    返回:
         清理后的诊断块字符串
    """
    cleaned_lines = []
    include_prefix_kept = 0
    for line in block_lines:
        if "In file included from" in line and include_prefix_kept >= 2:
            continue
        if "In file included from" in line:
            include_prefix_kept += 1
        cleaned_lines.append(line.rstrip())
    return "\n".join(cleaned_lines).strip()


def extract_error_location(error_line: str) -> dict:
    """
    从错误行中提取错误位置信息（文件路径、行号、列号）。

    参数:
        error_line: 包含错误的行字符串

    返回:
         包含位置信息的字典，若无则返回空字典
    """
    match = re.match(
        r"^(?P<path>.+?):(?P<line>\d+):(?P<column>\d+):\s+(?:fatal\s+)?error:",
        error_line.strip(),
    )
    if not match:
        return {}

    return {
        "file_path": match.group("path").strip(),
        "line": int(match.group("line")),
        "column": int(match.group("column")),
    }


def first_error_line(text: str) -> str:
    """
    从文本中找到第一个包含错误的行。

    参数:
        text: 要搜索的文本字符串

    返回:
         第一个错误行，若无则返回空字符串
    """
    for line in text.splitlines():
        stripped = line.strip()
        if " error:" in stripped or stripped.startswith("error:") or " fatal error:" in stripped:
            return stripped
    return ""


def extract_error_file_path(block: str) -> str:
    """
    从诊断块中提取错误所在的文件路径。

    参数:
        block: 单个诊断块字符串

    返回:
         错误文件路径，若无则返回空字符串
    """
    error_line = first_error_line(block)
    if not error_line:
        return ""

    return extract_error_location(error_line).get("file_path", "")


def resolve_diagnostic_location(
    block: str,
    *,
    owned_paths: Sequence[Path | str] | None = None,
) -> dict:
    """解析诊断位置，并从项目外错误沿诊断栈回溯到项目 Header。

    参数:
        block: 单个 clang 诊断块，可能包含 include 栈、主错误和 note 栈。
        owned_paths: 项目内 Header 路径集合；为空时只返回主错误位置。

    返回:
        dict: 优先返回主错误位置；当主错误位于项目外时，先从错误后的
        note/模板实例化栈查找第一个项目 Header，再从错误前的 include 栈
        逆序查找最近项目 Header。完全无法回溯时仍返回原始错误位置。
    """
    lines = block.splitlines()
    error_index = -1
    primary_location: dict = {}
    for index, line in enumerate(lines):
        if not first_error_line(line):
            continue
        error_index = index
        primary_location = extract_error_location(line.strip())
        break

    if not primary_location or not owned_paths:
        return primary_location

    normalized_owned_paths = {
        normalize_path_for_compare(str(path)) for path in owned_paths
    }
    primary_path = primary_location.get("file_path", "")
    if normalize_path_for_compare(primary_path) in normalized_owned_paths:
        return primary_location

    # clang 的 note/模板实例化链位于主错误之后，顺序即从底层实现回到调用点。
    for line in lines[error_index + 1 :]:
        candidate = extract_any_diagnostic_location(line)
        if _is_owned_diagnostic_location(candidate, normalized_owned_paths):
            return candidate

    # include 栈位于主错误之前，逆序查找可得到离底层错误最近的项目 Header。
    for line in reversed(lines[:error_index]):
        candidate = extract_any_diagnostic_location(line)
        if _is_owned_diagnostic_location(candidate, normalized_owned_paths):
            return candidate

    return primary_location


def extract_any_diagnostic_location(line: str) -> dict:
    """从普通诊断、note 或 include 栈行中提取文件位置。

    参数:
        line: clang 输出中的单行文本。

    返回:
        dict: 包含 file_path、line、column；无法解析时返回空字典。
    """
    stripped = line.strip()
    include_prefix = "In file included from "
    if stripped.startswith(include_prefix):
        stripped = stripped[len(include_prefix):]
    elif stripped.startswith("from "):
        stripped = stripped[len("from "):]

    match = re.match(
        r"^(?P<path>.+?):(?P<line>\d+)(?::(?P<column>\d+))?(?::|,)",
        stripped,
    )
    if not match:
        return {}
    return {
        "file_path": match.group("path").strip(),
        "line": int(match.group("line")),
        "column": int(match.group("column") or 0),
    }


def _is_owned_diagnostic_location(
    location: dict,
    normalized_owned_paths: set[str],
) -> bool:
    """判断解析出的诊断位置是否属于项目 Header。

    参数:
        location: extract_any_diagnostic_location 返回的位置字典。
        normalized_owned_paths: 已规范化的项目 Header 路径集合。

    返回:
        bool: 位置具有文件路径且该路径属于项目时返回 True。
    """
    file_path = location.get("file_path", "")
    return bool(
        file_path
        and normalize_path_for_compare(file_path) in normalized_owned_paths
    )


def normalize_path_for_compare(path_str: str) -> str:
    """
    规范化路径字符串，用于比较（不区分大小写、统一路径分隔符）。

    参数:
        path_str: 原始路径字符串

    返回:
         规范化后的路径字符串
    """
    normalized = os.path.normcase(
        os.path.normpath(
            os.path.abspath(path_str)
        )
    )
    return normalized.rstrip()


def truncate_text(text: str, max_chars: int) -> str:
    """
    截断文本到指定的最大字符数，末尾添加截断标记。

    参数:
        text: 原始文本字符串
        max_chars: 最大字符数

    返回:
         截断后的文本
    """
    if len(text) <= max_chars:
        return text
    return text[:max_chars].rstrip() + "\n... [truncated]"


def read_source_line(file_path: str, line_number: int) -> str:
    """
    读取指定文件的指定行内容。

    参数:
        file_path: 文件路径
        line_number: 行号（从1开始）

    返回:
         指定行的内容，若无法读取则返回空字符串
    """
    if not file_path or line_number <= 0:
        return ""

    try:
        with open(file_path, "r", encoding="utf-8") as file:
            for current_index, line in enumerate(file, start=1):
                if current_index == line_number:
                    return line.rstrip("\n\r")
    except OSError:
        return ""
    return ""


def _looks_like_diagnostic_metadata(line: str) -> bool:
    """
    判断一行文本是否属于编译器输出的元数据信息（而非源代码摘录）。

    参数:
        line: 待判断的行字符串

    返回:
        bool: 若是包含文件追踪、error/note 等元数据行则返回 True，
              否则返回 False
    """
    stripped = line.strip()
    if not stripped:
        return True
    if stripped.startswith("In file included from"):
        return True
    if " error:" in stripped or " fatal error:" in stripped or stripped.startswith("error:"):
        return True
    if " note:" in stripped or stripped.startswith("note:"):
        return True
    return False


def _normalize_source_excerpt_line(line: str) -> str:
    """
    规范化源代码摘录行，去除行号与竖线前缀。

    参数:
        line: 原始的源代码摘录行（可能带行号与 "|" 分隔符）

    返回:
        str: 去除前缀后的源代码内容
    """
    return re.sub(r"^\s*\d+\s*\|\s?", "", line.rstrip())


def _normalize_marker_excerpt_line(line: str) -> str:
    """
    规范化错误标记行，去除开头的竖线分隔符。

    参数:
        line: 原始的错误标记行（可能以 "|" 开头）

    返回:
        str: 去除前缀后的标记内容
    """
    return re.sub(r"^\s*\|\s?", "", line.rstrip())


if __name__ == '__main__':
    pass
