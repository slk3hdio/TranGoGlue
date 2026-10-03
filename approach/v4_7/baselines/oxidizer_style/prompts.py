from __future__ import annotations

from .feature_rules import FeatureRule


def _rules_text(rules: list[FeatureRule]) -> str:
    if not rules:
        return "(No special feature mapping rules apply.)"
    return "\n".join(f"- [{rule.rule_id}] {rule.description}" for rule in rules)


def header_prompt(
    source: str,
    header_name: str,
    dependency_summary: str,
    peer_summary: str,
    rules: list[FeatureRule],
    feedback: str,
) -> str:
    return f"""Translate one Java declaration fragment to a complete C++17 header.

Source Java declaration fragment:
```java
{source}
```

Already accepted dependency declarations:
{dependency_summary or "(None)"}

Declarations in the same dependency cycle (their C++ definitions may not exist yet):
{peer_summary or "(None)"}

Apply these Java-to-C++ feature mapping rules:
{_rules_text(rules)}

Compiler or mapping feedback from the previous candidate:
{feedback or "(None)"}

Requirements:
1. Return the complete `{header_name}` content, including #pragma once and all required standard includes.
2. Preserve source class/interface/enum names and public method names.
3. Include only already accepted project headers. Use forward declarations for cycle peers.
4. Keep method bodies out of this header except templates, inline trivial members, defaulted members, or enum definitions.
5. Do not emit Java syntax, package names, imports, annotations, or throws clauses.
6. Do not modify any accepted dependency.

Respond with ONLY one JSON object:
{{"translated_header": "complete C++17 header text"}}
"""


def method_prompt(
    source_method: str,
    owning_declaration: str,
    target_declaration: str,
    dependency_summary: str,
    peer_summary: str,
    rules: list[FeatureRule],
    feedback: str,
) -> str:
    return f"""Translate one Java method fragment to one C++17 method definition.

Current Java source fragment:
```java
{source_method}
```

Already accepted owning C++ declaration:
```cpp
{owning_declaration}
```

The definition signature is frozen and must be matched exactly:
```cpp
{target_declaration}
```

Already accepted callee declarations:
{dependency_summary or "(None)"}

Methods in the same recursive dependency group:
{peer_summary or "(None)"}

Apply these Java-to-C++ feature mapping rules:
{_rules_text(rules)}

Compiler or mapping feedback from the previous candidate:
{feedback or "(None)"}

Requirements:
1. Return only the current complete method definition plus required standard #include lines.
2. Do not change the fixed signature, target header, or any accepted method.
3. Use only declarations available in the target header and dependency summaries.
4. Do not add behavior absent from the Java method merely to make compilation pass.

Respond with ONLY one JSON object:
{{"complete_translated_code": "complete C++17 method definition"}}
"""
