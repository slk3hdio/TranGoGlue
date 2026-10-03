"""
确定性编译错误分类器

从 clang++ 编译日志中按规则提取并分类错误，不依赖 LLM，保证
v3/v4/v4_1 等不同批次数据的分类粒度一致。

错误类型与论文六分类一致：
- Syntax Rule Violation
- Type Error
- Declaration Mismatch
- Undefined Symbols
- Duplicated Definitions
- Header File Error
- Other Errors

用法:
    python approach/eveluation/deterministic_error_classifier.py --versions v3 v4 v4_1 --ai-names deepseek

对每个 eval/*.json 文件，收集其中所有失败函数的 log_output，
提取 error 行并按文件去重，写回顶层 errors 字段（替换原有 LLM 分类结果）。
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

p_dir = str(Path(__file__).parent)
pp_dir = str(Path(__file__).parent.parent)
if pp_dir not in sys.path:
    sys.path.append(pp_dir)
if p_dir not in sys.path:
    sys.path.append(p_dir)

from path_config import cfg_all_project_names  # noqa: E402


ERROR_TYPES = [
    "Syntax Rule Violation",
    "Type Error",
    "Declaration Mismatch",
    "Undefined Symbols",
    "Duplicated Definitions",
    "Header File Error",
    "Other Errors",
]

# 提取 error 行: "path:line:col: error: msg" 或 "fatal error: msg"
_ERROR_LINE_RE = re.compile(r"(?:fatal\s+)?error:\s*(.+?)\s*$")

# 去掉末尾的 [-W...] 等编译选项标记
_WARNING_TAG_RE = re.compile(r"\s*\[-[^\]]+\]\s*$")


def classify_message(message: str) -> str:
    """根据错误消息文本确定性分类。"""
    msg = message.strip()
    lower = msg.lower()

    # Header File Error: 缺失头文件 / include 嵌套过深
    if "file not found" in lower or "no such file or directory" in lower:
        return "Header File Error"
    if "#include nested too deeply" in lower:
        return "Header File Error"

    # Duplicated Definitions: 重复定义 / 重复初始化
    if "redefinition of" in lower:
        return "Duplicated Definitions"
    if "already has an initializer" in lower:
        return "Duplicated Definitions"
    if "multiple definition" in lower:
        return "Duplicated Definitions"
    if "redeclared as different kind of symbol" in lower:
        return "Duplicated Definitions"

    # Undefined Symbols: 未声明标识符 / 未知类型 / 无此成员
    if "use of undeclared identifier" in lower:
        return "Undefined Symbols"
    if "unknown type name" in lower:
        return "Undefined Symbols"
    if "unknown class name" in lower:
        return "Undefined Symbols"
    if "no member named" in lower:
        return "Undefined Symbols"
    if "no template named" in lower:
        return "Undefined Symbols"
    if "unknown template name" in lower:
        return "Undefined Symbols"
    if "requires template arguments" in lower:
        return "Undefined Symbols"
    if "field has incomplete type" in lower:
        return "Undefined Symbols"
    if "incomplete type" in lower and "used in" in lower:
        return "Undefined Symbols"

    # Declaration Mismatch: 声明/定义签名不一致
    if "no matching function for call to" in lower:
        return "Declaration Mismatch"
    if "no matching constructor for initialization" in lower:
        return "Declaration Mismatch"
    if "is ambiguous" in lower:
        return "Declaration Mismatch"
    if "marked 'override' but does not override" in lower:
        return "Declaration Mismatch"
    if "does not override any member" in lower:
        return "Declaration Mismatch"
    if "does not match any declaration" in lower:
        return "Declaration Mismatch"
    if "different exception specification" in lower:
        return "Declaration Mismatch"

    # Type Error: 类型不匹配 / 非法转换
    if "no viable conversion" in lower:
        return "Type Error"
    if "no viable overloaded" in lower:
        return "Type Error"
    if "could not bind" in lower:
        return "Type Error"
    if "is not polymorphic" in lower:
        return "Type Error"
    if "invalid operands" in lower:
        return "Type Error"
    if "from incompatible type" in lower:
        return "Type Error"
    if "incompatible type" in lower:
        return "Type Error"
    if "cannot convert" in lower:
        return "Type Error"
    if "conversion from" in lower:
        return "Type Error"
    if "mismatched types" in lower:
        return "Type Error"
    if "initializing argument of type" in lower:
        return "Type Error"
    if "return type" in lower and "must match" in lower:
        return "Type Error"
    if "does not provide a call operator" in lower:
        return "Type Error"
    if "implicitly-deleted" in lower and "constructor" in lower:
        return "Type Error"
    if "is an abstract class" in lower:
        return "Type Error"
    if "abstract class type" in lower:
        return "Type Error"
    if "cannot initialize a variable of type" in lower:
        return "Type Error"
    if "comparison of distinct pointer types" in lower:
        return "Type Error"

    # Undefined Symbols: 模板未实例化/未定义
    if "implicit instantiation of undefined template" in lower:
        return "Undefined Symbols"
    if "explicit instantiation of" in lower and "undefined template" in lower:
        return "Undefined Symbols"

    # Undefined Symbols: 不完整类型(仅前向声明/未包含定义)与缺失声明
    if "incomplete type" in lower:
        return "Undefined Symbols"
    if "incomplete element type" in lower:
        return "Undefined Symbols"
    if "no type named" in lower:
        return "Undefined Symbols"

    # Declaration Mismatch: 声明与继承/成员初始化不一致
    if "is not a direct or virtual base of" in lower:
        return "Declaration Mismatch"
    if "does not name a non-static data member" in lower:
        return "Declaration Mismatch"
    if "tag type that does not match previous declaration" in lower:
        return "Declaration Mismatch"
    if "no matching member function" in lower:
        return "Declaration Mismatch"
    if "too few arguments to function call" in lower:
        return "Declaration Mismatch"
    if "too many arguments to function call" in lower:
        return "Declaration Mismatch"
    if "missing exception specification" in lower:
        return "Declaration Mismatch"
    if "does not have a default constructor" in lower:
        return "Declaration Mismatch"

    # Duplicated Definitions: 成员/构造函数重复声明
    if "cannot be redeclared" in lower:
        return "Duplicated Definitions"
    if "duplicate member" in lower:
        return "Duplicated Definitions"

    # Type Error: 类型转换/初始化不合法
    if "static_cast from" in lower:
        return "Type Error"
    if "cannot initialize a member subobject of type" in lower:
        return "Type Error"
    if "cannot initialize object parameter of type" in lower:
        return "Type Error"
    if "default initialization of an object of const type" in lower:
        return "Type Error"
    if "indirection requires pointer operand" in lower:
        return "Type Error"
    if "cannot form a reference to" in lower:
        return "Type Error"
    if "is not a constant expression" in lower:
        return "Type Error"
    if "no matching conversion" in lower:
        return "Type Error"
    if "cannot initialize a parameter of type" in lower:
        return "Type Error"
    if "cannot initialize return object" in lower:
        return "Type Error"
    if "cast from pointer to smaller type" in lower:
        return "Type Error"
    if "taking the address of a temporary" in lower:
        return "Type Error"
    if "member reference type" in lower and "is not a pointer" in lower:
        return "Type Error"
    if "dynamic_cast" in lower:
        return "Type Error"
    if "template argument for template type parameter must be a type" in lower:
        return "Type Error"

    # Syntax Rule Violation: 关键字误用/函数初始化器/非法嵌套与字符
    if "cannot be specified on member function templates" in lower:
        return "Syntax Rule Violation"
    if "illegal initializer" in lower:
        return "Syntax Rule Violation"
    if "does not look like a pure-specifier" in lower:
        return "Syntax Rule Violation"
    if "function definition is not allowed here" in lower:
        return "Syntax Rule Violation"
    if "not allowed inside a function" in lower:
        return "Syntax Rule Violation"
    if "extraneous closing brace" in lower:
        return "Syntax Rule Violation"
    if "unexpected character" in lower:
        return "Syntax Rule Violation"
    if "does not contain any unexpanded parameter packs" in lower:
        return "Syntax Rule Violation"
    if "definition of explicitly defaulted" in lower:
        return "Syntax Rule Violation"
    if "needs an explicit size or an initializer" in lower:
        return "Syntax Rule Violation"
    if "does not enclose namespace" in lower:
        return "Syntax Rule Violation"

    # Declaration Mismatch: override 签名不一致
    if "marked 'override' hides virtual member function" in lower:
        return "Declaration Mismatch"
    if "has a different return type" in lower and "override" in lower:
        return "Declaration Mismatch"

    # Syntax Rule Violation: 语法/语言特性
    if "only virtual member functions can be marked" in lower:
        return "Syntax Rule Violation"
    if "does not allow dynamic exception specifications" in lower:
        return "Syntax Rule Violation"
    if lower.startswith("expected"):
        return "Syntax Rule Violation"
    if "expected class name" in lower:
        return "Syntax Rule Violation"
    if "unexpected" in lower and ("token" in lower or "end of file" in lower):
        return "Syntax Rule Violation"

    # Undefined Symbols: 不完整类型 / std 命名空间缺失类型 / 不可达成员
    if "has incomplete type" in lower or "incomplete type" in lower:
        return "Undefined Symbols"
    if "incomplete result type" in lower:
        return "Undefined Symbols"
    if "no type named" in lower:
        return "Undefined Symbols"
    if "does not refer to a value" in lower:
        return "Undefined Symbols"
    if "cannot be implicitly captured" in lower:
        return "Undefined Symbols"
    if "is a private member of" in lower or "is a protected member of" in lower:
        return "Undefined Symbols"

    # Declaration Mismatch: 构造初始化列表与类声明不符 / 类外定义签名不一致 /
    # 异常规格更宽 / 调用被删除的构造或转换函数
    if "does not name a non-static data member" in lower:
        return "Declaration Mismatch"
    if "return type of" in lower and ("differs from" in lower
                                      or "not covariant" in lower):
        return "Declaration Mismatch"
    if "more lax than base version" in lower:
        return "Declaration Mismatch"
    if "call to deleted" in lower:
        return "Declaration Mismatch"
    if "functions that differ only in their return type" in lower:
        return "Declaration Mismatch"

    # Duplicated Definitions: 类成员重复声明 / typedef 重定义 / 重复实例化
    if "cannot be redeclared" in lower or "duplicate member" in lower:
        return "Duplicated Definitions"
    if "redeclared with" in lower or "typedef redefinition" in lower:
        return "Duplicated Definitions"
    if "duplicate explicit instantiation" in lower:
        return "Duplicated Definitions"

    # Type Error: const 调用不匹配 / void 误用 / 无效转换与绑定 /
    # 模板参数个数错误 / const 成员缺初始化
    if "'this' argument to member function" in lower:
        return "Type Error"
    if ("reference to 'void'" in lower or "may not have 'void'" in lower
            or "indirection not permitted" in lower
            or "address of an rvalue of type 'void'" in lower
            or "member reference base type 'void'" in lower):
        return "Type Error"
    if "static_cast" in lower or "reinterpret_cast" in lower:
        return "Type Error"
    if ("cannot bind" in lower or "cannot initialize object parameter" in lower
            or "unrelated type" in lower):
        return "Type Error"
    if "_atomic cannot be applied" in lower or "static assertion failed" in lower:
        return "Type Error"
    if ("template arguments" in lower
            and ("too many" in lower or "too few" in lower
                 or "cannot have" in lower)):
        return "Type Error"
    if "default initialization of an object of const type" in lower:
        return "Type Error"
    if "must explicitly initialize the const member" in lower:
        return "Type Error"

    # Syntax Rule Violation: Java 风格初始化器 / 关键字位置非法 / 非法字符 /
    # 声明语法杂项
    if "pure-specifier" in lower or "illegal initializer" in lower:
        return "Syntax Rule Violation"
    if "'virtual' " in lower and ("cannot be" in lower or "can only" in lower):
        return "Syntax Rule Violation"
    if "'static' can only" in lower:
        return "Syntax Rule Violation"
    if "'override' specifier is not allowed" in lower:
        return "Syntax Rule Violation"
    if "unexpected character" in lower or "not allowed in an identifier" in lower:
        return "Syntax Rule Violation"
    if ("type specifier is required" in lower or "anonymous class" in lower
            or "forbids forward references" in lower
            or "templates can only be declared" in lower
            or "function definition is not allowed" in lower
            or "extraneous closing brace" in lower
            or "out-of-line declaration of a member" in lower
            or "range-based 'for'" in lower
            or "delegating constructor" in lower
            or "type-id cannot have a name" in lower
            or "parameter name cannot have template arguments" in lower
            or "brackets are not allowed" in lower
            or "type name requires a specifier" in lower):
        return "Syntax Rule Violation"

    return "Other Errors"


def extract_error_lines(log_output: str) -> list[str]:
    """从编译日志中提取所有 error 行的消息文本（去重，忽略 note/warning）。"""
    messages: list[str] = []
    for line in log_output.splitlines():
        match = _ERROR_LINE_RE.search(line.strip())
        if not match:
            continue
        msg = match.group(1).strip()
        msg = _WARNING_TAG_RE.sub("", msg).strip()
        if not msg:
            continue
        if "too many errors emitted" in msg:
            continue
        if msg not in messages:
            messages.append(msg)
    return messages


def classify_file(json_path: Path) -> list[dict[str, str]]:
    """对一个 eval JSON 文件做确定性分类（文件级去重）。

    级联抑制：如果日志中出现了 header 级别的错误（`file not found` 或
    `#include nested too deeply`），编译器要么终止（fatal）要么继续暴露由
    同一个包含失败引起的级联错误（unknown type name / incomplete type /
    override 不匹配等）。这些级联错误与 header 错误是同一个根因，按
    "一个错误只记一次" 的原则，抑制它们，避免不同编译器行为（fatal vs
    非 fatal）造成计数粒度不一致。
    """
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # 先收集全部错误消息（按出现顺序）
    all_messages: list[str] = []
    for func in data.get("functions", []):
        if func.get("success", True):
            continue
        log_output = func.get("log_output", "") or ""
        all_messages.extend(extract_error_lines(log_output))

    # 判断是否存在 header 级错误
    has_header_root = any(
        ("file not found" in msg.lower()) or ("#include nested too deeply" in msg.lower())
        for msg in all_messages
    )

    seen: dict[tuple[str, str], None] = {}
    for msg in all_messages:
        error_type = classify_message(msg)
        detail = msg[:200]

        if has_header_root and _is_cascade_error(error_type, msg):
            continue

        key = (error_type, detail)
        if key in seen:
            continue
        seen[key] = None

    return [{"error_type": et, "error_detail": det} for (et, det) in seen]


def _is_cascade_error(error_type: str, msg: str) -> bool:
    """判断错误是否由 header 包含失败引起的级联错误。"""
    if error_type == "Header File Error":
        return False
    lower = msg.lower()
    # 类型解析失败：未知类型 / 不完整类型 / 成员不存在 / override 不匹配
    if "unknown type name" in lower:
        return True
    if "unknown class name" in lower:
        return True
    if "unknown template name" in lower:
        return True
    if "field has incomplete type" in lower:
        return True
    if "incomplete type" in lower and "used in" in lower:
        return True
    if "incomplete type" in lower:
        return True
    if "no member named" in lower:
        return True
    if "marked 'override' but does not override" in lower:
        return True
    if "does not override any member" in lower:
        return True
    if "use of undeclared identifier" in lower:
        return True
    if "requires template arguments" in lower:
        return True
    if "no template named" in lower:
        return True
    return False


def process_project(version: str, ai_name: str, project_name: str) -> int:
    eval_dir = Path("output") / version / project_name / ai_name / "eval"
    if not eval_dir.exists():
        return 0

    updated = 0
    for json_file in sorted(eval_dir.glob("*.json")):
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as exc:
            print(f"  [skip] {json_file.name}: {exc}")
            continue

        errors = classify_file(json_file)
        if errors:
            data["errors"] = errors
        else:
            data.pop("errors", None)

        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        updated += 1

    return updated


def main() -> int:
    parser = argparse.ArgumentParser(description="Deterministic compile error classification for eval JSONs.")
    parser.add_argument("--versions", nargs="+", default=["v3", "v4", "v4_1"])
    parser.add_argument("--ai-names", nargs="+", default=["deepseek"])
    args = parser.parse_args()

    total_files = 0
    for version in args.versions:
        for ai_name in args.ai_names:
            for project_name in cfg_all_project_names(version):
                updated = process_project(version, ai_name, project_name)
                total_files += updated
                if updated:
                    print(f"[{version}/{ai_name}/{project_name}] classified {updated} files")
    print(f"Total classified eval files: {total_files}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
