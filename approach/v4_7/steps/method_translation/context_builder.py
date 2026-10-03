from __future__ import annotations

import re
from typing import List

from graph import Header, Method


class MethodContextBuilder:
    """方法翻译上下文构建器。

    负责为方法翻译提示词组装跨文件上下文，包括依赖方法签名、
    相关头文件内容以及引用目标头的头文件内容，帮助 LLM 生成更准确的实现。

    用法约定：
        - 通过 build_*_context 系列方法生成字符串形式的上下文片段；
        - 返回的空字符串表示没有可用的上下文。
    """

    _CUSTOM_INCLUDE_RE = re.compile(r'^\s*#include\s+"([^"]+)"', re.MULTILINE)

    def build_dependency_signature_context(self, method: Method) -> str:
        """构建方法的依赖签名上下文。

        遍历当前方法的子节点（被调用的依赖方法），拼接每个依赖的
        Java 签名、映射后的 C++ 定义签名（mapping 阶段产出，可能缺失）、
        头类名与头文件名，用于提示词中的跨引用信息。

        参数:
            method: 需要进行翻译的 Method 节点。

        返回:
            拼接好的依赖签名上下文字符串；无依赖时返回空字符串。
        """
        dependency_lines = []
        for child in method.children:
            lines = [
                f"Java signature: {child.key}",
                f"Header class: {child.header.translated_class_name}",
                f"Header file: {child.header.get_output_header_name()}",
            ]
            # 附上映射阶段确定的 C++ 定义签名，避免调用方猜测被调方参数类型
            cpp_sig = getattr(child, "translated_declaration", "") or getattr(child, "mapped_cpp_definition", "")
            if cpp_sig:
                lines.append(f"C++ definition: {cpp_sig}")
            dependency_lines.append("\n".join(lines))
        return "\n\n".join(dependency_lines)

    def build_related_headers_context(self, method: Method, headers: List[Header]) -> str:
        """构建与目标方法相关的头文件上下文。

        收集目标方法所属头及其依赖的头文件，将每个头的类名、
        文件名与翻译后的代码片段（已截断）拼接为提示词上下文。

        参数:
            method: 需要翻译的 Method 节点。
            headers: 全部头文件列表，用于检索相关头文件。

        返回:
            相关头文件的上下文文本；没有相关头文件时返回空字符串。
        """
        related_headers = self._collect_related_headers(method, headers)
        if not related_headers:
            return ""

        sections = []
        for header in related_headers:
            sections.append(
                "\n".join(
                    [
                        f"Header class: {header.translated_class_name}",
                        f"Header file: {header.get_output_header_name()}",
                        "Header code:",
                        "```cpp",
                        self._truncate_header_context(header.translated_code),
                        "```",
                    ]
                )
            )
        return "\n\n".join(sections)

    def _extract_custom_include_names(self, code: str) -> List[str]:
        """从 C++ 代码中提取自定义头文件（#include "..."）的名称列表。

        参数:
            code: 待分析的 C++ 源码文本。

        返回:
            匹配到的自定义 include 名称列表。
        """
        return self._CUSTOM_INCLUDE_RE.findall(code or "")

    def _truncate_header_context(self, code: str, max_lines: int = 80, max_chars: int = 3500) -> str:
        """截断头文件代码，限制上下文长度。

        参数:
            code: 头文件的翻译代码。
            max_lines: 允许的最大行数。
            max_chars: 允许的最大字符数。

        返回:
            截断后的代码文本；空内容返回 "(empty)"。
        """
        text = (code or "").strip()
        if not text:
            return "(empty)"

        lines = text.splitlines()
        if len(lines) > max_lines:
            text = "\n".join(lines[:max_lines]) + f"\n... ({len(lines)} lines total)"
        if len(text) > max_chars:
            text = text[:max_chars].rstrip() + "\n... [truncated]"
        return text

    def build_includer_context(self, target: Header, headers: List[Header], max_includers: int = 4) -> str:
        """Collect non-external headers that include the target header (usage context)."""
        target_include = target.get_output_header_name()
        includers: List[Header] = []
        for header in headers:
            # 手写桩与外部占位头不作为"引用者上下文"（它们是已知条件）
            if header.key == target.key or header.is_generated_external() or header.is_manual_stub():
                continue
            if not header.translated_code.strip():
                continue
            if target_include in self._extract_custom_include_names(header.translated_code):
                includers.append(header)
            if len(includers) >= max_includers:
                break

        if not includers:
            return ""

        sections = []
        for header in includers:
            sections.append(
                "\n".join(
                    [
                        f"Header class: {header.translated_class_name}",
                        f"Header file: {header.get_output_header_name()}",
                        "Header code:",
                        "```cpp",
                        self._truncate_header_context(header.translated_code),
                        "```",
                    ]
                )
            )
        return "\n\n".join(sections)

    def _collect_related_headers(self, method: Method, headers: List[Header], max_related_headers: int = 4) -> List[Header]:
        """收集与目标方法相关的头文件列表。

        优先收集目标方法所属头文件通过自定义 include 引入的头，
        再收集方法子节点对应的头文件，均去重并限制数量。

        参数:
            method: 需要翻译的 Method 节点。
            headers: 全部头文件列表，用于按 include 名检索。
            max_related_headers: 最多收集的相关头文件数量。

        返回:
            按优先级排列的相关 Header 列表。
        """
        header_by_include_name = {
            header.get_output_header_name(): header
            for header in headers
        }
        selected: List[Header] = []
        selected_keys = {method.header.key}

        def add_header(candidate: Header | None) -> None:
            """将候选头文件加入选择列表（若有效且尚未选中）。"""
            if candidate is None:
                return
            if candidate.key in selected_keys:
                return
            if not candidate.translated_code.strip():
                return
            selected.append(candidate)
            selected_keys.add(candidate.key)

        for include_name in self._extract_custom_include_names(method.header.translated_code):
            add_header(header_by_include_name.get(include_name))
            if len(selected) >= max_related_headers:
                return selected

        for child in method.children:
            add_header(child.header)
            if len(selected) >= max_related_headers:
                return selected

            for include_name in self._extract_custom_include_names(child.header.translated_code):
                add_header(header_by_include_name.get(include_name))
                if len(selected) >= max_related_headers:
                    return selected

        return selected
