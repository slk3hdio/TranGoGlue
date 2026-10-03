from __future__ import annotations

import re


_CPP_IDENTIFIER_PATTERN = r"[A-Za-z_$][A-Za-z0-9_$]*"


def scope_header_to_definition_owner(header_code: str, cpp_definition: str) -> str:
    """将头文件文本缩小到 C++ 限定方法所属类的类体。

    参数:
        header_code: 完整的 C++ 头文件代码。
        cpp_definition: 可能带 ``Outer::Inner::method`` 限定名的方法定义。

    返回:
        找到 owner 时返回对应类体；无 owner 时返回完整头文件；owner 已给出但
        类体不存在时返回空字符串。
    """
    owner = _extract_definition_owner(cpp_definition)
    if not owner:
        return header_code
    return _extract_class_body(header_code, owner.split("::")[-1])


def _extract_definition_owner(cpp_definition: str) -> str:
    """提取 C++ 方法定义限定名中的 owner。

    参数:
        cpp_definition: C++ 方法定义签名。

    返回:
        例如 ``Outer::Inner``；没有限定 owner 时返回空字符串。
    """
    compact = " ".join(part.strip() for part in cpp_definition.splitlines())
    compact = re.sub(r"template\s*<[^>]+>", "", compact).strip()
    method_name = _extract_definition_method_name(compact)
    if not method_name:
        return ""
    match = re.search(
        rf"((?:{_CPP_IDENTIFIER_PATTERN}::)+){re.escape(method_name)}\s*\(",
        compact,
    )
    return match.group(1).rstrip(":") if match else ""


def _extract_definition_method_name(cpp_definition: str) -> str:
    """提取 C++ 定义中实际被声明的方法名。

    参数:
        cpp_definition: 已压缩为单行的 C++ 定义签名。

    返回:
        参数列表前的方法名；无法识别时返回空字符串。
    """
    matches = list(
        re.finditer(
            rf"(?:^|::|\s)(~?{_CPP_IDENTIFIER_PATTERN})\s*\(",
            cpp_definition,
        )
    )
    return matches[0].group(1) if matches else ""


def _extract_class_body(header_code: str, class_name: str) -> str:
    """按花括号配对提取指定类或结构体的完整类体。

    参数:
        header_code: 完整头文件文本。
        class_name: 不带外层限定名的类名。

    返回:
        包含外层花括号的类体文本；未找到完整定义时返回空字符串。
    """
    declaration = re.search(
        rf"\b(?:class|struct)\s+{re.escape(class_name)}\b[^;{{]*\{{",
        header_code,
    )
    if declaration is None:
        return ""

    opening = header_code.find("{", declaration.start())
    depth = 0
    for index in range(opening, len(header_code)):
        char = header_code[index]
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return header_code[opening : index + 1]
    return ""
