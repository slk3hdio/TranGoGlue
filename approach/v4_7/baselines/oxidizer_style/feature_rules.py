from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Callable, Literal


FragmentKind = Literal["header", "method"]
Detector = Callable[[str, FragmentKind], bool]
Validator = Callable[[str, str, FragmentKind], str | None]


@dataclass(frozen=True)
class FeatureRule:
    rule_id: str
    description: str
    detector: Detector
    validator: Validator


def _contains(pattern: str) -> Detector:
    regex = re.compile(pattern, re.MULTILINE)
    return lambda source, kind: bool(regex.search(source))


def _target_must_not(pattern: str, message: str) -> Validator:
    regex = re.compile(pattern, re.MULTILINE)

    def validate(source: str, target: str, kind: FragmentKind) -> str | None:
        return message if regex.search(target) else None

    return validate


def _class_validator(source: str, target: str, kind: FragmentKind) -> str | None:
    if kind != "header":
        return None
    match = re.search(r"\b(class|interface|enum)\s+([A-Za-z_]\w*)", source)
    if not match:
        return None
    source_kind, name = match.groups()
    if source_kind == "enum":
        expected = rf"\benum(?:\s+class)?\s+{re.escape(name)}\b"
    else:
        expected = rf"\b(?:class|struct)\s+{re.escape(name)}\b"
    if not re.search(expected, target):
        return f"target must declare the source {source_kind} {name}"
    return None


def _interface_validator(source: str, target: str, kind: FragmentKind) -> str | None:
    if kind != "header" or not re.search(r"\binterface\s+", source):
        return None
    if "virtual" not in target:
        return "Java interface methods must be represented by virtual C++ methods"
    if re.search(r"\([^;{}]*\)\s*;", source) and "= 0" not in target and "=0" not in target:
        return "abstract interface methods must be pure virtual (= 0)"
    return None


def _inheritance_validator(source: str, target: str, kind: FragmentKind) -> str | None:
    if kind != "header":
        return None
    if re.search(r"\b(?:extends|implements)\b", source) and not re.search(
        r"\b(?:class|struct)\s+\w+[^\{;]*:\s*(?:public\s+)?\w+", target
    ):
        return "Java extends/implements relationships must appear as C++ base classes"
    return None


def _string_validator(source: str, target: str, kind: FragmentKind) -> str | None:
    if re.search(r"(?<!:)\bString\b", target):
        return "Java String must not remain in C++; use std::string or an explicit adapter"
    return None


def _array_validator(source: str, target: str, kind: FragmentKind) -> str | None:
    if re.search(r"\b[A-Za-z_]\w*(?:<[^;{}]+>)?\s*\[\s*\]", target):
        return "Java-style Type[] syntax must not remain in C++"
    return None


def _collection_validator(source: str, target: str, kind: FragmentKind) -> str | None:
    pattern = r"(?<!std::)\b(?:List|ArrayList|Map|HashMap|Set|HashSet|Collection|Optional)\s*<"
    if re.search(pattern, target):
        return "Java collection names must be mapped to C++ standard-library types"
    return None


def _static_validator(source: str, target: str, kind: FragmentKind) -> str | None:
    if kind == "header" and re.search(r"\bstatic\b[^;()]*;", source) and "static" not in target:
        return "static source fields require a static or inline static C++ declaration"
    return None


def _constructor_validator(source: str, target: str, kind: FragmentKind) -> str | None:
    if kind != "header":
        return None
    class_match = re.search(r"\bclass\s+([A-Za-z_]\w*)", source)
    if not class_match:
        return None
    name = class_match.group(1)
    if re.search(rf"\b{re.escape(name)}\s*\(", source) and not re.search(
        rf"(?:\b|::){re.escape(name)}\s*\(", target
    ):
        return f"constructor {name}(...) must be preserved"
    return None


def _synchronized_validator(source: str, target: str, kind: FragmentKind) -> str | None:
    if re.search(r"\bsynchronized\b", target):
        return "the Java synchronized keyword must not remain in C++"
    synchronization = ("mutex", "lock_guard", "scoped_lock", "unique_lock", "atomic")
    if not any(token in target for token in synchronization):
        return "synchronized Java code requires an explicit C++ synchronization primitive"
    return None


def _threading_validator(source: str, target: str, kind: FragmentKind) -> str | None:
    if re.search(r"(?<!std::)\b(?:Thread|ExecutorService|Future|CompletableFuture)\b", target):
        return "Java threading types must be mapped to C++ threading/future types or an adapter"
    return None


FEATURE_RULES: tuple[FeatureRule, ...] = (
    FeatureRule(
        "declaration-kind",
        "Map Java class/interface/enum declarations to C++ class/struct/enum declarations with the same source name.",
        _contains(r"\b(?:class|interface|enum)\s+"),
        _class_validator,
    ),
    FeatureRule(
        "interface-virtual-dispatch",
        "Map Java interfaces to abstract C++ base classes with a virtual destructor and pure virtual methods.",
        _contains(r"\binterface\s+"),
        _interface_validator,
    ),
    FeatureRule(
        "inheritance",
        "Preserve extends/implements using public C++ base classes and override where applicable.",
        _contains(r"\b(?:extends|implements)\b"),
        _inheritance_validator,
    ),
    FeatureRule(
        "primitive-types",
        "Map Java boolean/byte/short/int/long/float/double/char to explicit C++ types; never emit Java type names.",
        _contains(r"\b(?:boolean|byte|short|int|long|float|double|char)\b"),
        _target_must_not(r"\bboolean\b", "Java boolean must be translated to bool"),
    ),
    FeatureRule(
        "string",
        "Map java.lang.String to std::string and include <string>.",
        _contains(r"\bString\b"),
        _string_validator,
    ),
    FeatureRule(
        "arrays",
        "Map Java arrays to std::vector/std::array or an explicit pointer/span representation; do not retain Type[] syntax.",
        _contains(r"\[\s*\]"),
        _array_validator,
    ),
    FeatureRule(
        "collections-generics",
        "Map Java collections and Optional to corresponding C++ standard-library templates and add their standard includes.",
        _contains(r"\b(?:List|ArrayList|Map|HashMap|Set|HashSet|Collection|Optional)\s*<"),
        _collection_validator,
    ),
    FeatureRule(
        "nullability",
        "Map Java null to nullptr, std::optional, or an explicit nullable smart-pointer policy.",
        _contains(r"\bnull\b"),
        _target_must_not(r"\bnull\b", "Java null must be translated to nullptr or std::nullopt"),
    ),
    FeatureRule(
        "static-initialization",
        "Preserve Java static members using C++ static/inline static declarations and legal C++ initialization.",
        _contains(r"\bstatic\b"),
        _static_validator,
    ),
    FeatureRule(
        "exceptions",
        "Map Java throw/throws and checked exceptions to C++ exceptions; remove throws clauses and Java exception type names.",
        _contains(r"\b(?:throw|throws|Exception|Throwable)\b"),
        _target_must_not(r"\bthrows\b", "Java throws clauses must not remain in C++"),
    ),
    FeatureRule(
        "constructors-overloads",
        "Preserve constructors, overloads, and overriding declarations with legal C++ signatures.",
        _contains(r"\b(?:public|protected|private)\s+[A-Za-z_]\w*\s*\("),
        _constructor_validator,
    ),
    FeatureRule(
        "override",
        "Preserve Java dynamic dispatch using virtual/override in C++ declarations.",
        _contains(r"@Override|\boverride\b"),
        lambda source, target, kind: (
            "overridden Java methods should use C++ override in the class declaration"
            if kind == "header" and "override" not in target
            else None
        ),
    ),
    FeatureRule(
        "synchronization",
        "Map synchronized and atomic behavior to std::mutex locks, std::atomic, and other explicit C++ concurrency primitives.",
        _contains(r"\bsynchronized\b|\bAtomic[A-Za-z]+\b"),
        _synchronized_validator,
    ),
    FeatureRule(
        "threading",
        "Map Java Thread, ExecutorService, Future, and CompletableFuture to C++ threads/futures or an explicit adapter.",
        _contains(r"\b(?:Thread|ExecutorService|Future|CompletableFuture)\b"),
        _threading_validator,
    ),
    FeatureRule(
        "java-standard-library",
        "Replace java.* APIs with C++ standard-library APIs or a compile-safe project-local adapter; no java.* names may remain.",
        _contains(r"\bjava\.[A-Za-z_]"),
        _target_must_not(r"\bjava\s*(?:::|\.)", "java.* names must not remain in target C++"),
    ),
)


def applicable_rules(source: str, kind: FragmentKind) -> list[FeatureRule]:
    return [rule for rule in FEATURE_RULES if rule.detector(source, kind)]


def validate_rules(
    rules: list[FeatureRule], source: str, target: str, kind: FragmentKind
) -> list[str]:
    failures: list[str] = []
    for rule in rules:
        failure = rule.validator(source, target, kind)
        if failure:
            failures.append(f"{rule.rule_id}: {failure}")
    return failures
