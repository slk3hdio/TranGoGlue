from __future__ import annotations

import re
from typing import Iterable, List

from graph import Header, Method

from .cpp_header_scope import scope_header_to_definition_owner


_CPP_IDENTIFIER_PATTERN = r"[A-Za-z_$][A-Za-z0-9_$]*"


class MethodStateManager:
    """Infer the current method translation state from translated headers."""

    _HEADER_ONLY_PREFIX_RE = re.compile(r"^\s*(?:template\s*<[^>]+>\s*)?(?:inline\s+)?")

    def refresh_headers(self, headers: Iterable[Header]) -> None:
        """刷新一批头文件中所有方法的翻译状态。

        参数:
            headers: 可迭代的头文件集合。
        """
        for header in headers:
            self.refresh_header(header)

    def refresh_header(self, header: Header) -> None:
        """刷新单个头文件中所有方法的翻译状态。

        参数:
            header: 需要刷新的头文件。
        """
        for method in header.methods:
            self.refresh_method(method)

    def refresh_method(self, method: Method) -> None:
        """根据翻译头文件推断并更新单个方法的翻译状态。

        依次判断方法是否已有 LLM 映射、所属类是否实现、
        是否为删除/纯虚/defaulted 声明以及是否已在头文件中内联实现，
        据此设置 skip_translation 与原因。

        参数:
            method: 需要刷新状态的方法节点。
        """
        # 手写桩（manual_stub）方法的状态由 manual_stub_loader 设定，刷新不得改动
        header = getattr(method, "header", None)
        if header is not None and getattr(header, "is_manual_stub", None) and header.is_manual_stub():
            return
        if self._has_llm_mapping(method):
            self._refresh_from_mapping(method)
            return

        declaration = self._extract_declaration(method)
        method.translated_declaration = declaration
        method.is_template_method = self._is_template_method(method, declaration)

        if not self._owner_is_implemented_in_header(method):
            method.skip_translation = True
            method.skip_translation_reason = "所属类未在翻译头文件中定义，仅有前向声明或缺少类体"
            method.is_deleted_method = False
            return

        if self._is_deleted_declaration(declaration):
            method.is_deleted_method = True
            method.skip_translation = True
            method.skip_translation_reason = "deleted function declaration does not require implementation"
            return

        method.is_deleted_method = False

        if self._is_pure_virtual_declaration(declaration):
            method.skip_translation = True
            method.skip_translation_reason = "纯虚函数声明不需要直接生成实现"
            return

        if self._is_defaulted_declaration(declaration):
            method.skip_translation = True
            method.skip_translation_reason = "defaulted function declaration does not require implementation"
            return

        if self._declaration_has_body(declaration):
            method.skip_translation = True
            method.skip_translation_reason = "方法声明自身已经包含函数体"
            return

        if self._is_defined_in_header(method):
            method.skip_translation = True
            method.skip_translation_reason = "method already has an inline header definition"
            return

        if not declaration and not self._header_mentions_method(method):
            method.skip_translation = True
            method.skip_translation_reason = "method is not declared in translated header"
            return

        method.skip_translation = False
        method.skip_translation_reason = ""

    def _has_llm_mapping(self, method: Method) -> bool:
        """判断方法是否已具有 LLM 生成的映射信息。

        参数:
            method: 目标方法节点。

        返回:
            若存在任意映射相关字段则返回 True。
        """
        return bool(
            method.mapping_status
            or method.mapped_java_signature
            or method.mapped_cpp_definition
            or method.method_body_location
        )

    def _refresh_from_mapping(self, method: Method) -> None:
        """根据已有的 LLM 映射信息刷新方法的翻译状态。

        依据映射的 C++ 定义及标记（是否已实现、是否为模板、纯虚等）
        设置方法的状态与实现位置。

        参数:
            method: 已具有 LLM 映射的方法节点。
        """
        declaration = method.mapped_cpp_definition.strip()
        if declaration:
            method.translated_declaration = declaration
        method.is_template_method = bool(method.is_template_method)

        if not declaration:
            method.mapping_status = method.mapping_status or "deleted_or_merged"
            method.method_body_location = "none"
            method.is_deleted_method = True
            method.skip_translation = True
            method.skip_translation_reason = method.skip_translation_reason or "deleted or merged according to LLM mapping"
            return

        method.is_deleted_method = False

        if method.implemented_in_header:
            if self._is_defined_in_header(method):
                method.mapping_status = "already_implemented"
                method.method_body_location = "none"
                method.skip_translation = True
                method.skip_translation_reason = "method already implemented in translated header after body verification"
                return
            method.implemented_in_header = False

        if self._mapped_method_is_pure_virtual(method, declaration):
            method.mapping_status = "pure_virtual"
            method.method_body_location = "none"
            method.skip_translation = True
            method.skip_translation_reason = "pure virtual method does not require implementation"
            return

        if self._mapped_method_is_defaulted_or_deleted(method, declaration):
            method.mapping_status = "defaulted_or_deleted"
            method.method_body_location = "none"
            method.skip_translation = True
            method.skip_translation_reason = "defaulted or deleted method does not require implementation"
            return

        if method.mapping_status in {"invalid_cpp_definition", "unmapped"}:
            method.method_body_location = "none"
            method.skip_translation = True
            method.skip_translation_reason = method.skip_translation_reason or method.mapping_status
            return

        if method.method_body_location not in {"header", "cpp"}:
            method.method_body_location = "header" if method.is_template_method else "cpp"
        method.mapping_status = "needs_header_body" if method.method_body_location == "header" else "needs_cpp_body"
        method.skip_translation = False
        method.skip_translation_reason = ""

    def _mapped_method_is_pure_virtual(self, method: Method, declaration: str) -> bool:
        """判断映射声明对应头文件中的纯虚函数。

        参数:
            method: 目标方法节点。
            declaration: 映射得到的 C++ 声明。

        返回:
            若头文件中存在对应方法的 "= 0" 声明则返回 True。
        """
        name = self._extract_cpp_method_name(declaration) or method.get_name()
        owner_scope = scope_header_to_definition_owner(method.header.translated_code or "", declaration)
        return bool(re.search(rf"(?:\b|~){re.escape(name.lstrip('~'))}\s*\([^;{{}}]*\)\s*=\s*0\s*;", owner_scope))

    def _mapped_method_is_defaulted_or_deleted(self, method: Method, declaration: str) -> bool:
        """判断映射声明对应头文件中的 =default/=delete 函数。

        参数:
            method: 目标方法节点。
            declaration: 映射得到的 C++ 声明。

        返回:
            若头文件中存在对应方法的 "= default" 或 "= delete" 声明则返回 True。
        """
        name = self._extract_cpp_method_name(declaration) or method.get_name()
        # 声明文本本身即来自头文件，先做直接判断；owner 作用域提取对嵌套类
        # 可能失败，作为兜底再搜一次头文件。
        if self._is_defaulted_declaration(declaration) or self._is_deleted_declaration(declaration):
            return True
        owner_scope = scope_header_to_definition_owner(method.header.translated_code or "", declaration)
        return bool(re.search(rf"(?:\b|~){re.escape(name.lstrip('~'))}\s*\([^;{{}}]*\)\s*=\s*(default|delete)\s*;", owner_scope))

    def _extract_declaration(self, method: Method) -> str:
        """从翻译头文件中提取方法对应的声明文本。

        根据方法名与参数个数匹配候选声明；候选不唯一时优先参数数一致的声明。

        参数:
            method: 目标方法节点。

        返回:
            提取到的声明文本；无法提取时返回空字符串。
        """
        header_code = method.header.translated_code or ""
        if not header_code.strip():
            return ""

        candidates = self._candidate_declarations(header_code, method)
        candidates = [
            candidate for candidate in candidates
            if self._declaration_matches_method(candidate, method)
        ]
        if not candidates:
            return ""

        param_count = self._java_param_count(method.key)
        matched = [candidate for candidate in candidates if self._cpp_param_count(candidate) == param_count]
        if len(matched) == 1:
            return matched[0]
        if len(candidates) == 1:
            return candidates[0]
        return matched[0] if matched else ""

    def _candidate_declarations(self, header_code: str, method: Method) -> List[str]:
        """在头文件代码中收集与目标方法名匹配的候选声明。

        参数:
            header_code: 翻译后的头文件代码。
            method: 目标方法节点。

        返回:
            候选声明文本列表（可能包含多行拼接的声明）。
        """
        candidates: List[str] = []
        lines = header_code.splitlines()
        method_pattern = self._method_signature_hint_pattern(method)
        for idx, raw_line in enumerate(lines):
            line = raw_line.strip()
            if "(" not in line:
                continue
            if line.startswith("//") or line.startswith("#"):
                continue
            if not method_pattern.search(line):
                continue
            block_lines = [line]
            prefix_lines = []
            back_idx = idx - 1
            while back_idx >= 0:
                prev = lines[back_idx].strip()
                if not prev:
                    back_idx -= 1
                    continue
                if prev.startswith("template<") or prev.startswith("template <"):
                    prefix_lines.insert(0, prev)
                    back_idx -= 1
                    continue
                break
            if "{" not in line and ";" not in line and "= default" not in line and "= delete" not in line:
                forward_idx = idx + 1
                while forward_idx < len(lines):
                    next_line = lines[forward_idx].strip()
                    if not next_line:
                        forward_idx += 1
                        continue
                    block_lines.append(next_line)
                    if "{" in next_line or ";" in next_line or "= default" in next_line or "= delete" in next_line:
                        break
                    forward_idx += 1
            candidate = "\n".join(prefix_lines + block_lines).strip()
            if candidate and candidate not in candidates:
                candidates.append(candidate)
        return candidates

    def _method_signature_hint_pattern(self, method: Method) -> re.Pattern[str]:
        """构造用于在头文件中定位方法名的正则提示模式。

        参数:
            method: 目标方法节点。

        返回:
            匹配方法名后紧跟左括号的正则对象。
        """
        method_name = re.escape(method.get_name())
        return re.compile(rf"(?:^|[\s:*&<>,~]){method_name}\s*\(")

    def _declaration_matches_method(self, declaration: str, method: Method) -> bool:
        """判断提取出的声明是否与目标方法同名。

        参数:
            declaration: 候选声明文本。
            method: 目标方法节点。

        返回:
            若声明的函数名与目标方法名一致则返回 True。
        """
        extracted_name = self._extract_cpp_method_name(declaration)
        if not extracted_name:
            return False
        return extracted_name == method.get_name()

    def _extract_cpp_method_name(self, declaration: str) -> str:
        """从声明文本中提取方法名。

        参数:
            declaration: C++ 方法声明文本。

        返回:
            提取到的方法名；提取失败时返回空字符串。
        """
        compact = " ".join(part.strip() for part in declaration.splitlines())
        compact = compact.replace("{", " { ").replace("(", " ( ")
        match = re.search(rf"(~?{_CPP_IDENTIFIER_PATTERN})\s*\(", compact)
        return match.group(1) if match else ""

    def _is_template_method(self, method: Method, declaration: str) -> bool:
        """判断方法是否为模板方法。

        参数:
            method: 目标方法节点。
            declaration: 提取或映射得到的声明文本。

        返回:
            若方法已标记为模板或声明以模板开头则返回 True。
        """
        if method.is_template_method:
            return True
        return declaration.strip().startswith("template <") or declaration.strip().startswith("template<")

    def _is_pure_virtual_declaration(self, declaration: str) -> bool:
        """判断声明是否为纯虚函数（含 "= 0;"）。

        参数:
            declaration: 方法声明文本。

        返回:
            若为纯虚声明则返回 True。
        """
        return "= 0;" in declaration.replace("\n", " ")

    def _is_defaulted_declaration(self, declaration: str) -> bool:
        """判断声明是否为 =default 函数。

        参数:
            declaration: 方法声明文本。

        返回:
            若为 =default 声明则返回 True。
        """
        return "= default" in declaration

    def _is_deleted_declaration(self, declaration: str) -> bool:
        """判断声明是否为 =delete 函数。

        参数:
            declaration: 方法声明文本。

        返回:
            若为 =delete 声明则返回 True。
        """
        return "= delete" in declaration

    def _declaration_has_body(self, declaration: str) -> bool:
        """判断声明文本是否已包含函数体（同时含 { 与 }）。

        参数:
            declaration: 方法声明文本。

        返回:
            若声明中包含函数体则返回 True。
        """
        compact = " ".join(part.strip() for part in declaration.splitlines())
        return "{" in compact and "}" in compact

    def _header_mentions_method(self, method: Method) -> bool:
        """判断头文件中是否出现了目标方法名。

        参数:
            method: 目标方法节点。

        返回:
            若头文件中出现方法名加左括号的模式则返回 True。
        """
        name = method.get_name()
        return bool(re.search(rf"\b{re.escape(name)}\s*\(", method.header.translated_code or ""))

    def _is_defined_in_header(self, method: Method) -> bool:
        """判断目标方法是否已在翻译头文件中给出内联定义。

        通过匹配"类名::方法名("的带函数体定义，或匹配规范化后的声明加函数体。

        参数:
            method: 目标方法节点。

        返回:
            若头文件中已存在内联定义则返回 True。
        """
        header_code = method.header.translated_code or ""
        if not header_code.strip():
            return False

        method_name = re.escape(method.get_name())
        class_names = {
            method.header.key.split("$")[-1],
            method.header.translated_class_name.split("::")[-1],
            method.header.translated_class_name,
        }

        for class_name in sorted(class_names, key=len, reverse=True):
            qualified_name = rf"{re.escape(class_name)}\s*::\s*{method_name}"
            qualified_pattern = re.compile(
                rf"(?:template\s*<[^>]+>\s*)?(?:inline\s+)?[^;{{}}#]*\b{qualified_name}\s*\([^;{{}}]*\)\s*(?:const\s*)?(?:noexcept\s*)?(?:override\s*)?\{{",
                re.MULTILINE,
            )
            if qualified_pattern.search(header_code):
                return True

        declaration = self._extract_declaration(method)
        if not declaration:
            return False

        condensed = " ".join(part.strip() for part in declaration.splitlines())
        condensed = condensed.replace("= default", "").replace("= delete", "")
        condensed = condensed.rstrip(";").strip()
        condensed = self._HEADER_ONLY_PREFIX_RE.sub("", condensed)
        condensed_pattern = re.escape(condensed)
        inline_pattern = re.compile(rf"{condensed_pattern}\s*(?::[^\{{]+)?\{{", re.MULTILINE)
        return bool(inline_pattern.search(header_code))

    def _owner_is_implemented_in_header(self, method: Method) -> bool:
        """判断方法所属类是否已在翻译头文件中定义（含类体）。

        若方法属于头文件自身则必然已实现；否则在头代码中查找类定义。

        参数:
            method: 目标方法节点。

        返回:
            若所属类已在头文件中定义则返回 True。
        """
        owner_key = method.key.split(":", 1)[0]
        if owner_key == method.header.key:
            return True

        header_code = method.header.translated_code or ""
        owner_names = self._owner_class_names(method)
        for owner_name in owner_names:
            short_name = owner_name.split("::")[-1]
            if re.search(rf"\b(class|struct)\s+{re.escape(short_name)}\b[^;]*\{{", header_code):
                return True
        return False

    def _owner_class_names(self, method: Method) -> List[str]:
        """返回方法所属类的候选类名（含命名空间展开后的简称）。

        参数:
            method: 目标方法节点。

        返回:
            所属类的类名列表。
        """
        owner_key = method.key.split(":", 1)[0]
        names: List[str] = []
        translated = owner_key.replace("$", "::")
        if translated not in names:
            names.append(translated)
        short_name = translated.split("::")[-1]
        if short_name not in names:
            names.append(short_name)
        return names

    def _java_param_count(self, method_key: str) -> int:
        """统计 Java 方法签名中的参数个数（按顶层逗号计数）。

        参数:
            method_key: 方法节点的 key，含方法名与参数部分。

        返回:
            参数个数；无参数时返回 0。
        """
        if "(" not in method_key or ")" not in method_key:
            return 0
        params = method_key.split("(", 1)[1].rsplit(")", 1)[0].strip()
        if not params:
            return 0
        return len(self._split_params(params))

    def _cpp_param_count(self, declaration: str) -> int:
        """统计 C++ 声明中括号内的参数个数。

        参数:
            declaration: C++ 方法声明文本。

        返回:
            参数个数；无参数时返回 0，无法解析括号时返回 -1。
        """
        condensed = " ".join(part.strip() for part in declaration.splitlines())
        match = re.search(r"\((.*)\)", condensed)
        if not match:
            return -1
        params = match.group(1).strip()
        if not params:
            return 0
        return len(self._split_params(params))

    def _split_params(self, params: str) -> List[str]:
        """按顶层逗号拆分参数列表，忽略模板、括号、方括号内部的逗号。

        参数:
            params: 参数列表文本。

        返回:
            拆分后的参数片段列表（空片段被过滤）。
        """
        result: List[str] = []
        current: List[str] = []
        angle_depth = 0
        paren_depth = 0
        bracket_depth = 0
        for ch in params:
            if ch == "<":
                angle_depth += 1
            elif ch == ">":
                angle_depth = max(0, angle_depth - 1)
            elif ch == "(":
                paren_depth += 1
            elif ch == ")":
                paren_depth = max(0, paren_depth - 1)
            elif ch == "[":
                bracket_depth += 1
            elif ch == "]":
                bracket_depth = max(0, bracket_depth - 1)
            elif ch == "," and angle_depth == 0 and paren_depth == 0 and bracket_depth == 0:
                result.append("".join(current).strip())
                current = []
                continue
            current.append(ch)
        if current:
            result.append("".join(current).strip())
        return [item for item in result if item]
