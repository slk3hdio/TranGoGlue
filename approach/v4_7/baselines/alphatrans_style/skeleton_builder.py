from __future__ import annotations

"""Deterministic (rule-based) Java-to-C++ skeleton construction.

AlphaTrans builds a compilable target-language skeleton by translating types
and emitting class shells with method signatures but no bodies. This module
replicates that step without any LLM planning: a fixed type mapping table plus
simple signature parsing.
"""

import re
from typing import Dict, List, Optional, Tuple

from graph import Header, Method


# Deterministic Java -> C++ type mapping (subset of common types).
SIMPLE_TYPE_MAP: Dict[str, str] = {
    "void": "void",
    "boolean": "bool",
    "byte": "char",
    "short": "short",
    "int": "int",
    "long": "long long",
    "float": "float",
    "double": "double",
    "char": "char",
    "String": "std::string",
    "Object": "void*",
    "Integer": "int",
    "Long": "long long",
    "Short": "short",
    "Byte": "char",
    "Float": "float",
    "Double": "double",
    "Boolean": "bool",
    "Character": "char",
    "Duration": "std::chrono::duration<long long, std::nano>",
    "TimeUnit": "std::chrono::duration<long long, std::nano>",
    "Runnable": "std::function<void()>",
    "Callable": "std::function<void()>",
    "Throwable": "std::exception",
    "Exception": "std::exception",
    "RuntimeException": "std::runtime_error",
    "IllegalStateException": "std::runtime_error",
    "IllegalArgumentException": "std::invalid_argument",
    "NullPointerException": "std::runtime_error",
    "IOException": "std::runtime_error",
    "NoSuchElementException": "std::runtime_error",
    "UnsupportedOperationException": "std::runtime_error",
    "Future": "std::future<void>",
    "Class": "void*",
    "ExecutorService": "void*",
    "ScheduledExecutorService": "void*",
    "Thread": "std::thread",
    "Runnable": "std::function<void()>",
    "Delayed": "void*",
    "ForkJoinPool": "void*",
    "ScheduledThreadPoolExecutor": "void*",
    "ScheduledFuture": "std::future<void>",
    "CompletableFuture": "std::future<void>",
    "Function": "void*",
    "Supplier": "std::function<void()>",
    "Callable": "std::function<void()>",
    "Predicate": "std::function<bool()>",
    "Iterator": "void*",
    "Iterable": "std::vector<void*>",
    "Collection": "std::vector<void*>",
    "Stream": "void*",
    "Optional": "std::optional<void*>",
    "StringBuilder": "std::string",
    "StringBuffer": "std::string",
    "Arrays": "void*",
    "Math": "void*",
    "Objects": "void*",
    "System": "void*",
    "ThreadLocal": "void*",
    "AtomicReference": "void*",
    "AtomicBoolean": "void*",
    "AtomicInteger": "void*",
    "AtomicLong": "void*",
    "Instant": "std::chrono::time_point<std::chrono::system_clock>",
    "LocalDate": "std::string",
    "LocalDateTime": "std::string",
    "ZonedDateTime": "std::string",
    "BigDecimal": "double",
    "BigInteger": "long long",
    "PolicyConfig": "void*",
    "FailsafeFuture": "void*",
    "ExecutionInternal": "void*",
    "AsyncExecutionInternal": "void*",
    "SyncExecutionInternal": "void*",
    "FailurePolicy": "void*",
    "FailurePolicyConfig": "void*",
}

# Generics containers: java name -> cpp template wrapper.
GENERIC_TYPE_MAP: Dict[str, str] = {
    "List": "std::vector",
    "ArrayList": "std::vector",
    "LinkedList": "std::list",
    "Set": "std::set",
    "HashSet": "std::set",
    "TreeSet": "std::set",
    "Map": "std::map",
    "HashMap": "std::map",
    "TreeMap": "std::map",
    "Collection": "std::vector",
    "Iterable": "std::vector",
    "Optional": "std::optional",
    "Queue": "std::deque",
    "Deque": "std::deque",
}

STD_INCLUDES_BY_CPP_TYPE = {
    "std::string": "<string>",
    "std::vector": "<vector>",
    "std::list": "<list>",
    "std::set": "<set>",
    "std::map": "<map>",
    "std::optional": "<optional>",
    "std::deque": "<deque>",
    "std::chrono": "<chrono>",
    "std::function": "<functional>",
    "std::exception": "<exception>",
    "std::runtime_error": "<stdexcept>",
    "std::invalid_argument": "<stdexcept>",
    "std::future": "<future>",
    "std::thread": "<thread>",
}

MODIFIER_RE = re.compile(
    r"\b(public|private|protected|static|final|abstract|default|synchronized|native|"
    r"strictfp|transient|volatile|sealed|non-sealed)\b"
)


def _strip_annotations(code: str) -> str:
    code = re.sub(r"@\w+(\([^)]*\))?", "", code)
    code = re.sub(r"/\*.*?\*/", "", code, flags=re.S)
    code = re.sub(r"//.*", "", code)
    return code


def _clean_type_param(name: str) -> str:
    """`T extends Throwable` -> `T`; strip bounds from a Java type variable."""
    return name.strip().split(" ")[0]


def parse_java_signature(method: Method) -> Optional[Dict[str, object]]:
    """Parse return type, name, and params from a Java method body.

    Returns dict with keys: name, return_type, params (list of (type, name)),
    type_params (list of generic type parameter names, e.g. ['T']), and
    is_constructor (bool).
    Returns None if the signature cannot be parsed.
    """
    code = _strip_annotations(method.code)
    # Take the signature up to the first '{' (or the whole line).
    sig_part = code.split("{", 1)[0].strip()
    sig_part = re.sub(r"throws\s+[\w\.,\s]+$", "", sig_part).strip()
    if not sig_part:
        return None

    params_match = re.search(r"\(([^)]*)\)\s*(?:throws.*)?$", sig_part)
    if not params_match:
        return None
    params_str = params_match.group(1).strip()

    before_parens = sig_part[: params_match.start()].strip()
    before_parens = MODIFIER_RE.sub(" ", before_parens)
    before_parens = re.sub(r"\s+", " ", before_parens).strip()

    if not before_parens:
        return None
    tokens = before_parens.split(" ")
    name = tokens[-1]
    return_type = " ".join(tokens[:-1]).strip()
    is_constructor = not return_type

    # Generic method: `<T> T notNull(...)` -> type params ['T'], return type 'T'.
    type_params: List[str] = []
    if return_type.startswith("<") and ">" in return_type:
        type_params = [
            _clean_type_param(p)
            for p in return_type[1 : return_type.index(">")].split(",")
        ]
        return_type = return_type[return_type.index(">") + 1 :].strip()

    params: List[Tuple[str, str]] = []
    if params_str:
        for raw_param in _split_top_level(params_str, ","):
            raw_param = raw_param.strip()
            if not raw_param:
                continue
            if "..." in raw_param:
                raw_param = raw_param.replace("...", "[]")
            if "[]" in raw_param:
                param_type, _, param_name = raw_param.rpartition("[]")
                param_type = param_type.strip() + "[]"
                param_name = param_name.strip()
            else:
                parts = raw_param.rsplit(" ", 1)
                if len(parts) == 2:
                    param_type, param_name = parts[0].strip(), parts[1].strip()
                else:
                    param_type, param_name = raw_param, ""
            params.append((param_type, param_name))

    return {
        "name": name,
        "return_type": return_type,
        "params": params,
        "type_params": type_params,
        "is_constructor": is_constructor,
    }


def parse_interface_signature(header: Header, method: Method) -> Optional[Dict[str, object]]:
    """Parse an interface method signature from the class declaration source.

    Interface methods have no body in the split JSON, so the signature is
    recovered from header.source_code (the full Java class declaration).
    Overloaded methods are disambiguated by their parameter types from the
    method key (e.g. `AsyncExecution:record(R,Throwable)`).
    """
    method_name = method.get_name()
    if method_name == "<init>":
        return None

    # Expected param types from the method key, e.g. `Class:name(int,String)`.
    key_params: List[str] = []
    key_part = method.key.split(":", 1)[1] if ":" in method.key else ""
    if "(" in key_part:
        inner = key_part.split("(", 1)[1].rsplit(")", 1)[0]
        key_params = [p.strip() for p in inner.split(",") if p.strip()]

    source = _strip_annotations(header.source_code or "")
    pattern = re.compile(
        r"([\w<>,\.\s\[\]\?]*?)\s+" + re.escape(method_name) + r"\s*\(([^)]*)\)\s*;",
        re.MULTILINE,
    )
    best_match = None
    best_score = -1
    for match in pattern.finditer(source):
        params_str = match.group(2).strip()
        param_types = []
        if params_str:
            for raw_param in _split_top_level(params_str, ","):
                raw_param = raw_param.strip()
                if not raw_param:
                    continue
                if "..." in raw_param:
                    raw_param = raw_param.replace("...", "[]")
                parts = raw_param.rsplit(" ", 1)
                param_type = parts[0].strip() if len(parts) == 2 else raw_param
                param_types.append(param_type.split(".")[-1].split("<")[0])
        # Prefer the declaration whose simple param type names match the key.
        if not key_params:
            best_match = match
            break
        score = sum(
            1
            for kp, pt in zip(key_params, param_types)
            if kp.split(".")[-1].split("<")[0].split("$")[-1] == pt
        )
        if score > best_score:
            best_score = score
            best_match = match
    if best_match is None:
        return None

    return_type = best_match.group(1).strip()
    # Drop modifiers from the return type expression before inspecting it.
    return_type = MODIFIER_RE.sub(" ", return_type)
    return_type = re.sub(r"\s+", " ", return_type).strip()
    type_params: List[str] = []
    if return_type.startswith("<") and ">" in return_type:
        type_params = [
            _clean_type_param(p)
            for p in return_type[1 : return_type.index(">")].split(",")
        ]
        return_type = return_type[return_type.index(">") + 1 :].strip()
    if not return_type:
        return_type = "void"

    params_str = best_match.group(2).strip()
    params: List[Tuple[str, str]] = []
    if params_str:
        for raw_param in _split_top_level(params_str, ","):
            raw_param = raw_param.strip()
            if not raw_param:
                continue
            if "..." in raw_param:
                raw_param = raw_param.replace("...", "[]")
            parts = raw_param.rsplit(" ", 1)
            if len(parts) == 2:
                param_type, param_name = parts[0].strip(), parts[1].strip()
            else:
                param_type, param_name = raw_param, ""
            params.append((param_type, param_name))

    return {
        "name": method_name,
        "return_type": return_type,
        "params": params,
        "type_params": type_params,
        "is_constructor": False,
    }


def _split_top_level(text: str, sep: str) -> List[str]:
    """Split by separator at depth 0, ignoring separators inside <...>."""
    parts: List[str] = []
    depth = 0
    current: List[str] = []
    for ch in text:
        if ch == "<":
            depth += 1
        elif ch == ">":
            depth = max(0, depth - 1)
        if ch == sep and depth == 0:
            parts.append("".join(current))
            current = []
        else:
            current.append(ch)
    if current:
        parts.append("".join(current))
    return parts


def map_type(java_type: str, class_type_params: Optional[List[str]] = None) -> str:
    """Deterministically translate a Java type string to a C++ type string."""
    class_type_params = class_type_params or []
    java_type = java_type.strip()
    if not java_type:
        return "void"

    # Array suffix
    array_suffix = ""
    while java_type.endswith("[]"):
        array_suffix += "[]"
        java_type = java_type[:-2].strip()
    if array_suffix:
        inner = map_type(java_type, class_type_params)
        return f"std::vector<{inner}>"

    # Type variable of the enclosing class.
    if java_type in class_type_params:
        return java_type

    # Generic container: List<T> -> std::vector<T>
    generic_match = re.match(r"^([A-Za-z_]\w*)<(.+)>$", java_type)
    if generic_match:
        base_name, inner = generic_match.group(1), generic_match.group(2)
        # Java wildcards: `? extends X` / `? super X` -> X.
        inner = re.sub(r"\?\s*(?:extends|super)\s+", "", inner)
        if base_name in SIMPLE_TYPE_MAP:
            return SIMPLE_TYPE_MAP[base_name]
        cpp_wrapper = GENERIC_TYPE_MAP.get(base_name)
        if cpp_wrapper:
            inner_parts = _split_top_level(inner, ",")
            mapped_inner = ", ".join(map_type(p, class_type_params) for p in inner_parts)
            return f"{cpp_wrapper}<{mapped_inner}>"
        # Custom generic class: keep the parameterized name, e.g. Foo<T> -> Foo<T>.
        inner_parts = _split_top_level(inner, ",")
        mapped_inner = ", ".join(map_type(p, class_type_params) for p in inner_parts)
        if base_name == "Class":
            return "void*"
        return f"{base_name}<{mapped_inner}>"

    # Package-qualified name: take the simple class name.
    simple = java_type.split(".")[-1]

    if simple == "?":
        return "void*"
    if simple.startswith("?") or simple == "":
        return "void*"
    if simple in SIMPLE_TYPE_MAP:
        return SIMPLE_TYPE_MAP[simple]
    # Unknown custom type: keep the simple name (assume it maps to a project header).
    return simple


def collect_std_includes(cpp_type: str) -> List[str]:
    includes: List[str] = []
    for key in STD_INCLUDES_BY_CPP_TYPE:
        if key in cpp_type:
            inc = STD_INCLUDES_BY_CPP_TYPE[key]
            if inc not in includes:
                includes.append(inc)
    return includes


def parse_inheritance(source_code: str) -> Tuple[str, List[str]]:
    """Extract (parent_class, interfaces) from a Java class/interface declaration."""
    cleaned = _strip_annotations(source_code or "")
    match = re.search(r"\bclass\s+[\w<>,\.\s]+\s+(?:extends\s+([\w<>,\.\s]+))?\s*(?:implements\s+([\w<>,\.\s]+))?\s*\{", cleaned)
    if not match:
        match = re.search(
            r"\binterface\s+[\w<>,\.\s]+\s*(?:extends\s+([\w<>,\.\s]+))?\s*\{", cleaned
        )
        if not match:
            return "", []
        parent = match.group(1).strip() if match.group(1) else ""
        return parent, []
    parent = match.group(1).strip() if match.group(1) else ""
    interfaces = []
    if match.group(2):
        interfaces = [i.strip() for i in _split_top_level(match.group(2), ",") if i.strip()]
    return parent, interfaces


class SkeletonBuilder:
    """Build deterministic C++ class skeletons from the project graph."""

    def __init__(self) -> None:
        self._header_by_class_name: Dict[str, Header] = {}
        self._cycle_pairs: set = set()

    def _pointerize_cycle_type(self, cpp_type: str, cycle_deps: set) -> str:
        """Append `*` if the base of cpp_type is a cycle participant."""
        base = cpp_type.split("<")[0].split("::")[-1].strip()
        if base in cycle_deps and not cpp_type.endswith("*") and not cpp_type.endswith("&"):
            return cpp_type + "*"
        return cpp_type

    def _cycle_dep_simple_names(self, header: Header) -> set:
        """Simple class names that must be referenced via pointer/forward decl
        because they participate in an include cycle with this header."""
        names = set()
        for (a_key, b_key) in self._cycle_pairs:
            if a_key == header.key:
                for other in [None]:
                    pass
                # Find the simple name of b_key
                for h in self._header_by_class_name.values():
                    if h.key == b_key:
                        names.add(h.translated_class_name.split("::")[-1])
        return names

    def build_all(self, headers: List[Header]) -> None:
        self._header_by_class_name = {
            header.key: header for header in headers if not header.is_generated_external()
        }
        for header in headers:
            if not header.is_generated_external():
                header.translated_code = self.build_skeleton(header, headers)
        self._add_project_includes(headers)

    def _add_project_includes(self, headers: List[Header]) -> None:
        """Mechanically add `#include "X.h"` for referenced project classes.

        This mirrors AlphaTrans's skeleton construction, which resolves imports
        and circular dependencies statically (no LLM). Each generated header
        includes the project headers of every custom type it references.
        Includes that would form an include cycle are replaced by forward
        declarations of the referenced class.
        """
        header_by_simple_name: Dict[str, Header] = {}
        for header in headers:
            if header.is_generated_external():
                continue
            header_by_simple_name[header.key.split("$")[-1]] = header
            header_by_simple_name.setdefault(header.translated_class_name.split("::")[-1], header)

        include_map: Dict[str, List[str]] = {}
        for header in headers:
            if header.is_generated_external():
                continue
            code = header.translated_code or ""
            if not code.strip():
                continue
            self_name = header.translated_class_name.split("::")[-1]
            referenced: List[str] = []
            for token in re.findall(r"\b[A-Za-z_]\w*\b", code):
                if token == self_name:
                    continue
                if token in {"class", "template", "public", "private", "virtual", "std", "int",
                             "void", "bool", "char", "long", "short", "float", "double"}:
                    continue
                dep = header_by_simple_name.get(token)
                if dep is None or dep.key == header.key:
                    continue
                dep_include = f'#include "{dep.get_output_header_name()}"'
                if dep_include not in referenced:
                    referenced.append(dep_include)
            include_map[header.key] = referenced

        # Break include cycles: if A would include B and B includes A, replace
        # one direction with a forward declaration of the referenced class.
        def has_cycle_path(src_key: str, dst_key: str, visited: set) -> bool:
            for inc in include_map.get(src_key, []):
                dep_key = None
                inc_file = inc.split('"')[1]
                for other in headers:
                    if other.get_output_header_name() == inc_file:
                        dep_key = other.key
                        break
                if dep_key is None:
                    continue
                if dep_key == dst_key:
                    return True
                if dep_key in visited:
                    continue
                if has_cycle_path(dep_key, dst_key, visited | {dep_key}):
                    return True
            return False

        # Compute set of (A, B) pairs where B is on an include cycle back to A.
        cycle_pairs: set = set()
        for header in headers:
            if header.is_generated_external():
                continue
            for inc in include_map.get(header.key, []):
                inc_file = inc.split('"')[1]
                dep = None
                for other in headers:
                    if other.get_output_header_name() == inc_file:
                        dep = other
                        break
                if dep is not None and has_cycle_path(dep.key, header.key, {dep.key}):
                    cycle_pairs.add((header.key, dep.key))
        self._cycle_pairs = cycle_pairs

        for header in headers:
            if header.is_generated_external():
                continue
            if header.key not in include_map:
                continue
            referenced = include_map[header.key]
            final_refs: List[str] = []
            forward_decls: List[str] = []
            for inc in referenced:
                inc_file = inc.split('"')[1]
                dep = None
                for other in headers:
                    if other.get_output_header_name() == inc_file:
                        dep = other
                        break
                if dep is not None and has_cycle_path(dep.key, header.key, {dep.key}):
                    dep_type_params = self._class_type_params(dep)
                    simple = dep.translated_class_name.split("::")[-1]
                    if dep_type_params:
                        forward_decls.append(
                            "template <" + ", ".join("class " + p for p in dep_type_params) + ">\nclass " + simple + ";"
                        )
                    else:
                        forward_decls.append(f"class {simple};")
                    continue
                final_refs.append(inc)

            lines = header.translated_code.splitlines()
            insert_at = 1
            while insert_at < len(lines) and (lines[insert_at].startswith("#include") or not lines[insert_at].strip()):
                insert_at += 1
            new_parts = list(lines[:1])
            if final_refs:
                new_parts.append("")
                new_parts.extend(final_refs)
            if forward_decls:
                new_parts.append("")
                new_parts.extend(forward_decls)
            new_parts.append("")
            new_parts.extend(lines[1:insert_at])
            new_parts.extend(lines[insert_at:])
            header.translated_code = "\n".join(new_parts).rstrip() + "\n"

    def _class_type_params(self, header: Header) -> List[str]:
        cleaned = _strip_annotations(header.source_code or "").strip()
        cleaned = re.sub(r"\b(public|private|protected|abstract|final|static|sealed|non-sealed)\b", " ", cleaned)
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        match = re.match(r"^(?:class|interface|enum)\s+([A-Za-z_]\w*)<([^>]*)>", cleaned)
        if not match:
            return []
        return [_clean_type_param(p) for p in _split_top_level(match.group(2), ",")]

    def build_skeleton(self, header: Header, all_headers: List[Header]) -> str:
        """根据 Java header 构建确定性的 C++ 类骨架。

        参数：header 为当前 Java 类型，all_headers 为项目内全部类型。
        返回值：包含声明、字段、继承关系和必要 include 的 C++ header 文本。
        """
        type_params = self._class_type_params(header)
        class_name = header.translated_class_name
        # 字段和构造器检查都需要当前类的简单名称，必须在各分支前统一初始化。
        simple_class_name = class_name.split("::")[-1]
        is_interface = header.type == "interface"
        is_enum = header.type == "enum"

        if is_enum:
            lines = ["#pragma once", "", f"class {class_name} {{}};"]
            return "\n".join(lines)

        if type_params:
            header_open = f"template <{', '.join('class ' + p for p in type_params)}>"
        else:
            header_open = None

        used_std_includes: List[str] = []
        declared_methods: List[str] = []

        # Method declarations
        cycle_deps = self._cycle_dep_simple_names(header)
        for method in header.methods:
            sig = (
                parse_interface_signature(header, method)
                if is_interface
                else parse_java_signature(method)
            )
            if sig is None:
                continue
            name = str(sig["name"])
            method_type_params = [p for p in sig["type_params"] if p not in type_params]  # type: ignore[arg-type]
            if name == "<init>" or sig["is_constructor"]:
                continue
            return_type = map_type(str(sig["return_type"]), type_params + method_type_params)
            return_type = self._pointerize_cycle_type(return_type, cycle_deps)
            params = ", ".join(
                f"{self._pointerize_cycle_type(map_type(t, type_params + method_type_params), cycle_deps)} {n or 'arg'}"
                for t, n in sig["params"]  # type: ignore[arg-type]
            )
            template_prefix = ""
            if method_type_params:
                if is_interface:
                    # C++ forbids virtual member function templates; drop the
                    # method from the interface skeleton (naive baseline choice).
                    continue
                template_prefix = (
                    f"    template <{', '.join('class ' + p for p in method_type_params)}>\n"
                )
            if is_interface:
                decl = f"{template_prefix}    virtual {return_type} {name}({params}) = 0;"
            else:
                decl = f"{template_prefix}    {return_type} {name}({params});"
            # Drop exact duplicate declarations (e.g. overloads erased to the
            # same signature after naive type mapping), ignoring param names.
            normalized = re.sub(r"\s+", " ", decl)
            # Normalize the parameter list only: drop each param name (the
            # last identifier before `,` or `)` inside the parens), without
            # touching generic arguments outside the parens.
            def _drop_param_names(match: re.Match) -> str:
                inner = match.group(1)
                parts = inner.split(",")
                cleaned = []
                for part in parts:
                    part = part.strip()
                    tokens = part.split(" ")
                    if len(tokens) >= 2 and re.fullmatch(r"[a-zA-Z_]\w*", tokens[-1]):
                        part = " ".join(tokens[:-1]).strip()
                    cleaned.append(part)
                return "(" + ", ".join(cleaned) + ")"

            normalized = re.sub(r"\((.*?)\)", _drop_param_names, normalized)
            if normalized in declared_methods:
                continue
            declared_methods.append(normalized)
            for t, _ in sig["params"]:  # type: ignore[union-attr]
                used_std_includes.extend(
                    collect_std_includes(map_type(t, type_params + method_type_params))
                )
            used_std_includes.extend(collect_std_includes(return_type))

        # Constructors: methods with the same name as the class.
        for method in header.methods:
            sig = parse_java_signature(method)
            if sig is None:
                continue
            name = str(sig["name"])
            simple_class_name = header.key.split("$")[-1]
            if sig["is_constructor"] or name == "<init>" or name == simple_class_name:
                param_parts = []
                for t, n in sig["params"]:  # type: ignore[arg-type]
                    mapped_t = map_type(t, type_params)
                    base_t = t.strip().split(".")[-1].split("<")[0]
                    is_self_param = (
                        base_t == simple_class_name
                        or base_t == class_name.split("::")[-1]
                    )
                    if is_self_param and not mapped_t.endswith("&") and not mapped_t.endswith("*"):
                        mapped_t = mapped_t + "&"
                    param_parts.append((mapped_t, n or "arg"))
                if len(param_parts) == 1 and param_parts[0][0] == class_name:
                    param_parts[0] = (class_name + "&", param_parts[0][1])
                params = ", ".join(f"{t} {n}" for t, n in param_parts)
                declared_methods.insert(0, f"    {class_name}({params});")
                for t, _ in sig["params"]:  # type: ignore[union-attr]
                    used_std_includes.extend(collect_std_includes(map_type(t, type_params)))

        # Field declarations (simple name-only; skip complex initializers).
        # Interfaces have no data members in C++; also skip fields whose name
        # collides with a method name (Java allows it, C++ does not).
        method_names = set()
        for method in header.methods:
            sig = (
                parse_interface_signature(header, method)
                if is_interface
                else parse_java_signature(method)
            )
            if sig is not None:
                method_names.add(str(sig["name"]))
        field_lines: List[str] = []
        for field_str in header.fields:
            cleaned = _strip_annotations(field_str).strip()
            cleaned = re.sub(r"=.*$", "", cleaned).strip().rstrip(";").strip()
            parts = cleaned.split(" ")
            parts = [p for p in parts if p not in {
                "public", "private", "protected", "static", "final", "volatile", "transient",
            }]
            if len(parts) < 2:
                continue
            field_type = " ".join(parts[:-1])
            field_name = parts[-1]
            if is_interface:
                continue
            if field_name in method_names:
                continue
            # Skip self-typed static singleton fields (incomplete type at the
            # point of declaration inside the class body).
            base_field_type = field_type.split(".")[-1].split("<")[0]
            if base_field_type == simple_class_name or base_field_type == class_name.split("::")[-1]:
                continue
            mapped = map_type(field_type, type_params)
            mapped = self._pointerize_cycle_type(mapped, cycle_deps)
            base_field_simple = mapped.split("<")[0].split("::")[-1].strip()
            base_header = self._header_by_class_name.get(base_field_simple)
            if base_header is not None and base_header.type == "interface" and not mapped.endswith("*") and not mapped.endswith("&"):
                mapped = mapped + "*"
            field_lines.append(f"    {mapped} {field_name};")
            used_std_includes.extend(collect_std_includes(mapped))

        # Inheritance
        inheritance = ""
        parent, interfaces = parse_inheritance(header.source_code or "")
        bases: List[str] = []
        if parent:
            bases.append(f"public {map_type(parent, type_params)}")
        for iface in interfaces:
            bases.append(f"public {map_type(iface, type_params)}")
        if bases:
            inheritance = " : " + ", ".join(bases)

        lines = []
        lines.append("#pragma once")
        for inc in sorted(set(used_std_includes)):
            lines.append(f"#include {inc}")
        if used_std_includes:
            lines.append("")
        if header_open:
            lines.append(header_open)
        lines.append(f"class {class_name}{inheritance} {{")
        lines.append("public:")
        lines.extend(declared_methods)
        if field_lines:
            lines.append("private:")
            lines.extend(field_lines)
        lines.append("};")
        return "\n".join(lines)
