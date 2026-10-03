from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass(frozen=True)
class TypeIR:
    """A small cross-language type shape used before runtime snapshots exist."""

    kind: str
    name: str = ""
    args: tuple["TypeIR", ...] = ()
    nullable: bool = False


@dataclass
class CompatibilityResult:
    compatible: bool
    errors: list[str] = field(default_factory=list)


_JAVA_PRIMITIVES = {
    "boolean": "boolean",
    "byte": "byte",
    "short": "short",
    "int": "int",
    "long": "long",
    "float": "float",
    "double": "double",
    "char": "char",
    "void": "void",
}

_CPP_PRIMITIVES = {
    "bool": "boolean",
    "int8_t": "byte",
    "signed char": "byte",
    "int16_t": "short",
    "int": "int",
    "int32_t": "int",
    "int64_t": "long",
    "long": "long",
    "size_t": "int",
    "long long": "long",
    "float": "float",
    "double": "double",
    "char16_t": "char",
    "void": "void",
}

_JAVA_COLLECTIONS = {
    "List": "sequence",
    "ArrayList": "sequence",
    "LinkedList": "sequence",
    "Collection": "sequence",
    "Iterable": "sequence",
    "Set": "set",
    "HashSet": "set",
    "Map": "map",
    "HashMap": "map",
    "LinkedHashMap": "map",
    "Optional": "optional",
    "CompletableFuture": "future",
    "Future": "future",
}

_CPP_COLLECTIONS = {
    "vector": "sequence",
    "list": "sequence",
    "deque": "sequence",
    "set": "set",
    "unordered_set": "set",
    "map": "map",
    "unordered_map": "map",
    "optional": "optional",
    "future": "future",
    "shared_future": "future",
}


def _split_top_level(text: str) -> list[str]:
    parts: list[str] = []
    start = 0
    angle = paren = bracket = 0
    for index, char in enumerate(text):
        if char == "<":
            angle += 1
        elif char == ">":
            angle = max(0, angle - 1)
        elif char == "(":
            paren += 1
        elif char == ")":
            paren = max(0, paren - 1)
        elif char == "[":
            bracket += 1
        elif char == "]":
            bracket = max(0, bracket - 1)
        elif char == "," and not angle and not paren and not bracket:
            parts.append(text[start:index].strip())
            start = index + 1
    tail = text[start:].strip()
    if tail:
        parts.append(tail)
    return parts


def _strip_java_qualifiers(type_text: str) -> str:
    text = re.sub(r"@\w+(?:\([^)]*\))?\s*", "", type_text)
    text = re.sub(r"^\s*<[^>]+>\s*", "", text)
    text = re.sub(
        r"\b(?:public|protected|private|static|final|abstract|synchronized|native|strictfp|default|volatile|transient)\b",
        "",
        text,
    )
    return re.sub(r"\s+", " ", text).strip()


def java_type_ir(type_text: str) -> TypeIR:
    text = _strip_java_qualifiers(type_text).replace("...", "[]")
    array_depth = 0
    while re.search(r"\[\s*\]$", text):
        text = re.sub(r"\[\s*\]$", "", text).strip()
        array_depth += 1

    generic = re.match(r"^(?P<base>[\w.$]+)\s*<(?P<args>.*)>$", text)
    if generic:
        base = generic.group("base").split(".")[-1]
        args = tuple(java_type_ir(item) for item in _split_top_level(generic.group("args")))
    else:
        base = text.split(".")[-1]
        args = ()

    if base in _JAVA_PRIMITIVES:
        result = TypeIR("primitive", _JAVA_PRIMITIVES[base])
    elif base in {"String", "CharSequence"}:
        result = TypeIR("string", "String")
    elif base in {"Date", "Instant", "LocalDate", "LocalDateTime"}:
        result = TypeIR("date", base)
    elif base == "Object":
        result = TypeIR("object", "Object")
    elif base in _JAVA_COLLECTIONS:
        result = TypeIR(_JAVA_COLLECTIONS[base], base, args)
    elif re.match(r"^[A-Z][A-Za-z0-9_$]*$", base) or "$" in base:
        result = TypeIR("object", base, args)
    else:
        result = TypeIR("unknown", base, args)

    for _ in range(array_depth):
        result = TypeIR("array", args=(result,), nullable=True)
    return result


def _strip_cpp_qualifiers(type_text: str) -> tuple[str, bool]:
    text = re.sub(r"\b(?:const|volatile|static|inline|virtual|explicit|mutable|constexpr)\b", "", type_text)
    nullable = bool(re.search(r"(?:\*|shared_ptr\s*<|unique_ptr\s*<|weak_ptr\s*<|optional\s*<)", text))
    text = text.replace("&&", " ").replace("&", " ").replace("*", " ")
    return re.sub(r"\s+", " ", text).strip(), nullable


def cpp_type_ir(type_text: str) -> TypeIR:
    text, nullable = _strip_cpp_qualifiers(type_text)
    text = re.sub(r"\b(?:signed|unsigned)\s+char\b", "int8_t", text)
    text = re.sub(r"\bstd::(shared_ptr|unique_ptr|weak_ptr|optional)\s*<", r"std::\1<", text)
    generic = re.match(r"^(?P<base>(?:std::)?[\w:]+)\s*<(?P<args>.*)>$", text)
    if generic:
        base = generic.group("base").split("::")[-1]
        args = tuple(cpp_type_ir(item) for item in _split_top_level(generic.group("args")))
    else:
        base = text.split("::")[-1]
        args = ()

    if base == "char" and nullable:
        result = TypeIR("string", "char_pointer", nullable=True)
    elif base in _CPP_PRIMITIVES:
        result = TypeIR("primitive", _CPP_PRIMITIVES[base], nullable=nullable)
    elif base in {"string", "string_view"}:
        result = TypeIR("string", base, nullable=nullable)
    elif base in {"time_point", "system_clock"}:
        result = TypeIR("date", base, nullable=nullable)
    elif base in _CPP_COLLECTIONS:
        result = TypeIR(_CPP_COLLECTIONS[base], base, args, nullable=nullable)
    elif base in {"shared_ptr", "unique_ptr", "weak_ptr"} and args:
        result = TypeIR("object", args[0].name, args, nullable=True)
    elif base == "optional" and args:
        result = TypeIR("optional", base, args, nullable=True)
    elif base in {"any", "variant"}:
        result = TypeIR("object", base, args, nullable=nullable)
    elif base:
        result = TypeIR("object", base, args, nullable=nullable)
    else:
        result = TypeIR("unknown", text, args, nullable=nullable)
    return result


def _same_type(source: TypeIR, target: TypeIR) -> bool:
    if target.kind == "optional" and target.args and source.kind != "optional":
        return _same_type(source, target.args[0])
    if source.kind == "unknown" or target.kind == "unknown":
        return True
    if source.kind == "primitive":
        return target.kind == "primitive" and source.name == target.name
    if source.kind == "string":
        return target.kind == "string" or target.kind == "optional"
    if source.kind == "date":
        return target.kind == "date" or target.kind == "optional"
    if source.kind == "array":
        if target.kind == "array":
            return bool(source.args and target.args) and _same_type(source.args[0], target.args[0])
        if target.kind == "string" and source.args and source.args[0].name == "char":
            return True
        if target.kind in {"sequence", "object"}:
            return not target.args or not source.args or _same_type(source.args[0], target.args[0])
        return False
    if source.kind in {"sequence", "set", "map", "optional", "future"}:
        if source.kind == "optional":
            return target.kind == "optional" and _same_type(source.args[0], target.args[0]) if source.args and target.args else target.kind == "optional"
        if source.kind != target.kind:
            return False
        if not source.args or not target.args:
            return True
        return len(source.args) == len(target.args) and all(
            _same_type(left, right) for left, right in zip(source.args, target.args)
        )
    if source.kind == "object":
        if target.kind != "object":
            return False
        # A project-local C++ adapter cannot be matched by spelling alone.
        # Snapshot validation is responsible for proving its representation.
        return True
    return source.kind == target.kind


def _format_type(type_ir: TypeIR) -> str:
    if type_ir.args:
        return f"{type_ir.name or type_ir.kind}<{', '.join(_format_type(arg) for arg in type_ir.args)}>"
    return type_ir.name or type_ir.kind


def _parse_java_method(method_key: str, source: str) -> tuple[str, list[TypeIR], TypeIR | None, str]:
    owner, signature = method_key.rsplit(":", 1) if ":" in method_key else ("", method_key)
    match = re.match(r"(?P<name>[\w$<>]+)\((?P<params>.*)\)$", signature.strip())
    if not match:
        return "", [], None, owner
    name = match.group("name")
    params = [java_type_ir(item) for item in _split_top_level(match.group("params"))]
    owner_name = owner.split("$")[-1].split(".")[-1]
    if name == owner_name:
        return name, params, None, owner_name

    clean = re.sub(r"/\*.*?\*/|//[^\n]*", " ", source, flags=re.S)
    pattern = re.compile(
        rf"(?P<return>[\w.$<>\[\], ?]+?)\s+{re.escape(name)}\s*\((?P<params>[^()]*)\)",
        re.S,
    )
    source_matches = list(pattern.finditer(clean))
    source_match = next(
        (item for item in source_matches if len(_split_top_level(item.group("params"))) == len(params)),
        source_matches[0] if source_matches else None,
    )
    if source_match:
        source_params = _split_top_level(source_match.group("params"))
        parsed_params = [java_type_ir(_java_parameter_type(item)) for item in source_params]
        if len(parsed_params) == len(params):
            params = parsed_params
    return_type = java_type_ir(source_match.group("return")) if source_match else None
    return name, params, return_type, owner_name


def _java_parameter_type(parameter: str) -> str:
    text = _strip_java_qualifiers(parameter)
    match = re.match(r"^(?P<type>.+(?:\s|\.\.\.))(?P<name>[A-Za-z_$]\w*)$", text)
    return match.group("type").strip() if match else text


def _cpp_parameter_type(parameter: str) -> str:
    text = parameter.strip()
    text = re.sub(r"\s*=.*$", "", text).strip()
    if text == "...":
        return text
    # Remove the parameter identifier while retaining pointer/reference syntax.
    match = re.match(r"^(?P<type>.*(?:\s|[*&]))(?P<name>[A-Za-z_]\w*)$", text)
    if match:
        text = match.group("type").strip()
    return text


def _parse_cpp_signature(definition: str, expected_name: str) -> tuple[str, list[TypeIR], TypeIR | None]:
    compact = re.sub(r"template\s*<[^>]*>", "", definition, flags=re.S)
    name_match = re.search(rf"(?P<name>~?{re.escape(expected_name.lstrip('~'))})\s*\(", compact)
    if not name_match:
        # Java names can be renamed when they are C++ keywords (for example,
        # delete -> deleteWatcher). The mapping itself establishes identity;
        # compatibility compares the mapped signature's types.
        candidates = list(re.finditer(r"(?P<name>~?[A-Za-z_]\w*)\s*\(", compact))
        name_match = candidates[-1] if candidates else None
    if not name_match:
        return "", [], None
    depth = 1
    end = name_match.end()
    while end < len(compact) and depth:
        if compact[end] == "(":
            depth += 1
        elif compact[end] == ")":
            depth -= 1
        end += 1
    if depth:
        return "", [], None
    params_text = compact[name_match.end():end - 1]
    params = [cpp_type_ir(_cpp_parameter_type(item)) for item in _split_top_level(params_text)]
    before = compact[:name_match.start()].strip()
    owner_name = expected_name.lstrip("~")
    return_text = re.sub(r"(?:[A-Za-z_]\w*(?:<[^>]*>)?::)+$", "", before).strip()
    constructor = not return_text or before == owner_name or expected_name.startswith("~")
    return_type = None if constructor else cpp_type_ir(return_text)
    return name_match.group("name"), params, return_type


def check_method_signature(method_key: str, source: str, cpp_definition: str) -> CompatibilityResult:
    name, source_params, source_return, owner = _parse_java_method(method_key, source)
    if not name:
        return CompatibilityResult(False, ["unable to parse Java method signature"])
    target_name, target_params, target_return = _parse_cpp_signature(cpp_definition, name)
    if not target_name:
        return CompatibilityResult(False, [f"unable to parse C++ signature for {name}"])

    errors: list[str] = []
    if len(source_params) != len(target_params):
        errors.append(f"parameter count: Java has {len(source_params)}, C++ has {len(target_params)}")
    for index, (source_type, target_type) in enumerate(zip(source_params, target_params)):
        if not _same_type(source_type, target_type):
            errors.append(
                f"parameter {index + 1}: Java {_format_type(source_type)} is not compatible with C++ {_format_type(target_type)}"
            )
    if source_return is None and target_return is not None:
        errors.append("constructor must not have a C++ return type")
    elif source_return is not None and target_return is None:
        errors.append("non-constructor Java method is missing a C++ return type")
    elif source_return is not None and target_return is not None and not _same_type(source_return, target_return):
        errors.append(
            f"return type: Java {_format_type(source_return)} is not compatible with C++ {_format_type(target_return)}"
        )
    return CompatibilityResult(not errors, errors)


def check_method_mappings(methods: list, *, include_skipped: bool = False) -> list[str]:
    errors: list[str] = []
    for method in methods:
        if not method.mapped_cpp_definition or (method.skip_translation and not include_skipped):
            continue
        source = method.code
        if not re.search(rf"\b{re.escape(method.get_name())}\s*\(", source):
            source = f"{source}\n{method.header.source_code}"
        result = check_method_signature(method.key, source, method.mapped_cpp_definition)
        if not result.compatible:
            errors.extend(f"{method.key}: {error}" for error in result.errors)
    return errors


def _header_fields(source: str) -> list[tuple[str, TypeIR]]:
    fields: list[tuple[str, TypeIR]] = []
    for line in source.splitlines():
        if "(" in line or ";" not in line:
            continue
        match = re.search(
            r"\b(?P<type>[A-Za-z_$][\w.$]*(?:\s*<[^;=]+>)?(?:\s*\[\])?)\s+(?P<name>[A-Za-z_$]\w*)\s*(?:=.*)?;",
            line,
        )
        if match:
            fields.append((match.group("name"), java_type_ir(match.group("type"))))
    return fields


def check_header_compatibility(source: str, target: str) -> CompatibilityResult:
    errors: list[str] = []
    source_without_comments = re.sub(r"/\*.*?\*/|//[^\n]*", " ", source, flags=re.S)
    class_match = re.search(r"\b(?:class|interface|enum)\s+([A-Za-z_$][\w$]*)", source_without_comments)
    if class_match and not re.search(rf"\b(?:class|struct|enum(?:\s+class)?)\s+{re.escape(class_match.group(1))}\b", target):
        errors.append(f"missing translated type declaration: {class_match.group(1)}")

    for field_name, source_type in _header_fields(source):
        field_match = None
        for line in target.splitlines():
            if re.search(rf"\b{re.escape(field_name)}\b", line) and "(" not in line and "return" not in line:
                field_match = re.search(
                    rf"(?P<type>[A-Za-z_:][\w:<> ,*&]+?)\s+{re.escape(field_name)}\s*(?:[=;])",
                    line,
                )
                if field_match:
                    break
        if not field_match:
            # Java fields may be renamed, inherited, or represented by an
            # adapter in C++; schema-level checks belong to snapshot validation.
            continue
        target_type = cpp_type_ir(field_match.group("type"))
        if not _same_type(source_type, target_type):
            errors.append(
                f"field {field_name}: Java {_format_type(source_type)} is not compatible with C++ {_format_type(target_type)}"
            )
    return CompatibilityResult(not errors, errors)
