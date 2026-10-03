from __future__ import annotations

import re
from typing import List, Optional, Tuple

from graph import Header, Method, Project

from .state_manager import MethodStateManager


_CPP_IDENTIFIER_PATTERN = r"[A-Za-z_$][A-Za-z0-9_$]*"
_CLASS_BODY_START_RE = re.compile(
    rf"\b(?:class|struct)\s+{_CPP_IDENTIFIER_PATTERN}[^;{{}}]*\{{"
)
_BLOCK_COMMENT_RE = re.compile(r"/\*.*?\*/", re.DOTALL)
_LINE_COMMENT_RE = re.compile(r"//[^\n]*")
_ACCESS_SPECIFIER_RE = re.compile(r"^(?:public|private|protected)\s*:\s*")
_SKIP_PREFIXES = ("using ", "typedef ", "friend ", "static_assert", "return ", "operator")
_TEMPLATE_PREFIX_RE = re.compile(r"^\s*template\s*<")


def extract_external_methods(project: Project) -> int:
    """Extract member function declarations from generated external headers
    and register them as Method nodes so they enter the method graph.

    Idempotent: methods whose key already exists in the header are skipped.
    Returns the number of newly created method nodes.
    """
    state_manager = MethodStateManager()
    created = 0

    for header in project.headers:
        if not header.is_generated_external():
            continue
        if not (header.translated_code or "").strip():
            continue

        existing_keys = {method.key for method in header.methods}
        for declaration, has_body in _iter_member_declarations(header.translated_code):
            parsed = _parse_declaration(declaration)
            if parsed is None:
                continue
            name, params = parsed

            key = f"{header.key}:{name}({params})"
            if key in existing_keys:
                continue
            existing_keys.add(key)

            if has_body:
                # 已有内联实现，无需生成 cpp 实现，不建节点。
                continue

            method = Method(key, declaration, "generated_external", header)
            method.mapped_cpp_definition = declaration
            method.translated_declaration = declaration
            method.implemented_in_header = False
            method.is_template_method = bool(_TEMPLATE_PREFIX_RE.match(declaration))
            if method.is_template_method:
                method.mapping_status = "needs_header_body"
                method.method_body_location = "header"
            else:
                method.mapping_status = "needs_cpp_body"
                method.method_body_location = "cpp"

            # 复用状态判定：纯虚 / =default / = delete 的声明会被标记 skip。
            state_manager.refresh_method(method)

            header.methods.append(method)
            created += 1

    if created:
        # project.methods 在 load 时已分层，需要把新节点并入分层结果，
        # 否则方法翻译步骤看不到它们。
        from graph.retrieval_tools import get_ordered_method_groups

        all_methods = {method.key: method for header in project.headers for method in header.methods}
        project.methods = get_ordered_method_groups(all_methods)

    return created


def _strip_comments(code: str) -> str:
    """移除源代码中的块注释与行注释。

    参数:
        code: 原始 C++ 头文件代码。

    返回:
        去掉注释后的代码文本。
    """
    code = _BLOCK_COMMENT_RE.sub("", code)
    return _LINE_COMMENT_RE.sub("", code)


def _iter_member_declarations(header_code: str) -> List[Tuple[str, bool]]:
    """Yield (declaration, has_body) for each member function found in class bodies.

    declaration 是压缩成单行的声明文本（以 ; 结尾）；has_body 为 True 表示
    类内已带函数体。
    """
    code = _strip_comments(header_code)
    declarations: List[Tuple[str, bool]] = []

    for class_match in _CLASS_BODY_START_RE.finditer(code):
        body_start = class_match.end() - 1  # 指向 '{'
        body_end = _match_bracket(code, body_start, "{", "}")
        if body_end is None:
            continue
        body = code[body_start + 1:body_end]
        declarations.extend(_split_class_body_statements(body))

    return declarations


def _split_class_body_statements(body: str) -> List[Tuple[str, bool]]:
    """Split a class body into top-level member statements.

    只保留包含 '(' 的语句（候选成员函数），返回 (单行声明, 是否带函数体)。
    """
    results: List[Tuple[str, bool]] = []
    current: List[str] = []
    paren_depth = 0
    i = 0
    n = len(body)

    def flush(has_body: bool) -> None:
        """将累积的当前语句压平为一个候选成员声明，并加入结果列表。"""
        statement = " ".join("".join(current).split())
        current.clear()
        statement = _ACCESS_SPECIFIER_RE.sub("", statement).strip()
        if not statement or "(" not in statement:
            return
        if statement.startswith("#"):
            return
        if any(statement.startswith(prefix) for prefix in _SKIP_PREFIXES):
            return
        if has_body:
            # 截掉函数体，只保留声明部分。
            brace_idx = statement.find("{")
            declarator = statement[:brace_idx].strip()
            if declarator:
                results.append((declarator, True))
            return
        if not statement.endswith(";"):
            statement += ";"
        results.append((statement, False))

    while i < n:
        ch = body[i]
        if ch == "(":
            paren_depth += 1
        elif ch == ")":
            paren_depth = max(0, paren_depth - 1)
        elif ch == "{" and paren_depth == 0:
            end = _match_bracket(body, i, "{", "}")
            if end is None:
                current.append(body[i:])
                i = n
                flush(True)
                break
            current.append(body[i:end + 1])
            i = end + 1
            flush(True)
            continue
        elif ch == ";" and paren_depth == 0:
            flush(False)
            i += 1
            continue
        current.append(ch)
        i += 1

    if current:
        flush(False)

    return results


def _match_bracket(text: str, open_idx: int, open_ch: str, close_ch: str) -> Optional[int]:
    """在文本中查找与起始括号配对的结束括号下标。

    参数:
        text: 待扫描的文本。
        open_idx: 起始括号所在下标。
        open_ch: 起始括号字符（如 "{" 或 "("）。
        close_ch: 结束括号字符（如 "}" 或 ")"）。

    返回:
        配对结束括号的下标；未找到配对时返回 None。
    """
    depth = 0
    for idx in range(open_idx, len(text)):
        if text[idx] == open_ch:
            depth += 1
        elif text[idx] == close_ch:
            depth -= 1
            if depth == 0:
                return idx
    return None


def _parse_declaration(declaration: str) -> Optional[Tuple[str, str]]:
    """Parse a member declaration into (method_name, normalized_param_types).

    返回的参数类型串用于 Method.key，只需保证同类内签名唯一、逗号结构与
    原声明一致（MethodStateManager._java_param_count 按顶层逗号计数）。
    """
    text = _TEMPLATE_PREFIX_RE.sub("", declaration).strip()
    open_idx = text.find("(")
    if open_idx < 0:
        return None
    # 首个 "(" 位于模板参数内部时，该语句是 std::function 类型的字段声明
    # （如 std::function<R()> supplier;），不是成员函数，拒绝解析。
    angle_depth = 0
    for ch in text[:open_idx]:
        if ch == "<":
            angle_depth += 1
        elif ch == ">":
            angle_depth = max(0, angle_depth - 1)
    if angle_depth > 0:
        return None
    close_idx = _match_bracket(text, open_idx, "(", ")")
    if close_idx is None:
        return None

    prefix = text[:open_idx].rstrip()
    name_match = re.search(rf"(~?{_CPP_IDENTIFIER_PATTERN})$", prefix)
    if not name_match:
        return None
    name = name_match.group(1)

    params_text = text[open_idx + 1:close_idx].strip()
    param_types = ",".join(
        _normalize_param_type(param)
        for param in _split_top_level_params(params_text)
    )
    return name, param_types


def _split_top_level_params(params: str) -> List[str]:
    """按顶层逗号拆分参数列表，忽略模板、括号内部的逗号。

    参数:
        params: 括号内的参数字符串；空串或 "void" 表示无参数。

    返回:
        拆分后的参数片段列表。
    """
    if not params or params == "void":
        return []
    result: List[str] = []
    current: List[str] = []
    angle_depth = 0
    paren_depth = 0
    for ch in params:
        if ch == "<":
            angle_depth += 1
        elif ch == ">":
            angle_depth = max(0, angle_depth - 1)
        elif ch == "(":
            paren_depth += 1
        elif ch == ")":
            paren_depth = max(0, paren_depth - 1)
        if ch == "," and angle_depth == 0 and paren_depth == 0:
            result.append("".join(current).strip())
            current.clear()
            continue
        current.append(ch)
    if current:
        result.append("".join(current).strip())
    return [item for item in result if item]


def _normalize_param_type(param: str) -> str:
    """去掉默认值和形参名，只保留类型部分。"""
    param = param.split("=", 1)[0].strip()
    if not param:
        return param
    tokens = param.rsplit(None, 1)
    if len(tokens) == 2 and re.fullmatch(_CPP_IDENTIFIER_PATTERN, tokens[1]):
        # 最后一个词是形参名（类型部分以标识符、*、& 等结尾）
        candidate = tokens[0].strip()
        if candidate and not candidate.endswith(("...", ".")):
            return re.sub(r"\s+", "", candidate)
    return re.sub(r"\s+", "", param)
