from __future__ import annotations

import re

from graph import Method
from pydantic import ValidationError
from utils.str_process import get_json_str

from .models import MethodTranslateResult


_CPP_IDENTIFIER_PATTERN = r"[A-Za-z_$][A-Za-z0-9_$]*"


def process_method_output(method: Method, output: str) -> None:
    """解析并写入某个方法的 LLM 翻译输出。

    从输出中提取 JSON，校验结构，并将翻译后的 C++ 代码写回方法节点。

    参数:
        method: 待处理的方法节点，其翻译结果会被就地更新。
        output: LLM 返回的原始输出文本。

    抛出:
        ValueError: 输出中没有有效 JSON、JSON 结构无效或翻译代码为空时抛出。
    """
    method.raw_translated_code = output
    json_str = get_json_str(output)
    if not json_str:
        raise ValueError(f"method {method.key} has no valid json code")

    try:
        result = MethodTranslateResult.model_validate_json(json_str)
    except ValidationError as exc:
        raise ValueError(f"method {method.key} has invalid json schema: {exc}") from exc

    translated_code = result.complete_translated_code.strip()
    if not translated_code:
        raise ValueError(f"method {method.key} translated to empty code")
    method.translated_code = translated_code


def looks_like_expected_method(method: Method) -> bool:
    """检查翻译结果是否确实对应目标方法。

    通过比对翻译代码中包含的方法名与所属类名（或映射声明中的限定名），
    判断 LLM 输出是否与期望的方法一致。

    参数:
        method: 已写入翻译代码的方法节点。

    返回:
        若翻译代码看起来匹配目标方法则返回 True，否则 False。
    """
    code = method.translated_code or ""
    if not code.strip():
        return False

    mapped_name, mapped_owners = _mapped_cpp_name_and_owners(method.translated_declaration or method.mapped_cpp_definition)
    if mapped_name:
        if mapped_name not in code:
            return False
        return not mapped_owners or any(owner and owner in code for owner in mapped_owners)

    method_name = method.get_name()
    owner_names = {
        method.header.translated_class_name,
        method.header.translated_class_name.split("::")[-1],
        method.key.split(":", 1)[0].replace("$", "::"),
        method.key.split(":", 1)[0].split("$")[-1],
    }
    if method_name not in code:
        return False
    return any(owner_name and owner_name in code for owner_name in owner_names)


def _mapped_cpp_name_and_owners(cpp_definition: str) -> tuple[str, set[str]]:
    """从 C++ 定义中提取方法名及其限定名的所有类名。

    参数:
        cpp_definition: 映射得到的 C++ 方法定义文本。

    返回:
        (方法名, 类名集合)；提取失败时返回 ("", set())。
    """
    compact = " ".join(part.strip() for part in cpp_definition.splitlines())
    compact = re.sub(r"template\s*<[^>]+>", "", compact).strip()
    # 方法名除普通标识符外, 还需兼容 C++ 运算符重载(如 operator==、operator<);
    # 限定名前缀中的模板实参(如 ExecutionResult<R>::)不是合法标识符字符, 允许其出现;
    # 但模板实参内不允许空白, 避免跨空格吞掉返回类型
    # (如 "Timeout<R> TimeoutBuilder<R>::build()" 中的 "Timeout<R> " 是返回类型而非限定名)。
    _owner_prefix = rf"(?:{_CPP_IDENTIFIER_PATTERN}(?:<[^;()\s]*>)?::)*"
    match = re.search(
        rf"({_owner_prefix}(~?(?:{_CPP_IDENTIFIER_PATTERN}|operator[^()\s]*)))\s*\(",
        compact,
    )
    if not match:
        return "", set()
    qualified_name = match.group(1)
    method_name = match.group(2)
    if "::" not in qualified_name:
        return method_name, set()
    owner = qualified_name.rsplit("::", 1)[0]
    # 类名集合同时保留带模板实参与去除模板实参两种形态, 便于在代码中做包含匹配
    owner_no_tpl = re.sub(r"<[^>]*>", "", owner)
    owners = {owner, owner.split("::")[-1], owner_no_tpl, owner_no_tpl.split("::")[-1]}
    return method_name, owners
