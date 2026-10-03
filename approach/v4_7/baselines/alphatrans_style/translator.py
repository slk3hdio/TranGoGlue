from __future__ import annotations

"""AlphaTrans-style compositional translation with compile-feedback reprompting.

Methods are translated in reverse call order (callees before callers). Each
method is prompted with its Java source, the target class skeleton, and the
already-translated callee signatures. After file generation, a clang++ compile
check gates the result; failed methods are reprompted with the compiler error
log (budget-limited), mirroring AlphaTrans's feedback reprompting.
"""

import json
import re
import time
from typing import Dict, List, Optional, Tuple

from graph import Header, Method, Project
from pathlib import Path
from utils.Generator import Generator

from .skeleton_builder import SkeletonBuilder, parse_java_signature

TRANSLATION_SYSTEM_PROMPT = """You are an expert C++ developer translating Java code to C++.
You translate method bodies one at a time. The class skeleton (target header) is provided; match its declarations exactly.
Use only standard library types and the provided class signatures. Do not invent project-specific headers.
"""


def build_method_translation_prompt(method: Method, skeleton: str, translated_callees: str) -> str:
    sig = parse_java_signature(method)
    java_signature = method.key
    cpp_signature_hint = ""
    if sig is not None:
        return_type = str(sig["return_type"])
        name = str(sig["name"])
        params = ", ".join(
            f"{t} {n or 'arg'}" for t, n in sig["params"]  # type: ignore[arg-type]
        )
        owner = method.header.translated_class_name
        cpp_signature_hint = f"{owner}::{name}({params})"
        if sig["name"] == "<init>":
            cpp_signature_hint = f"{owner}::{owner}({params})"

    callee_section = translated_callees.strip() or "(No translated callees yet.)"

    return f"""Translate the following Java method to C++.

Target class skeleton (must match exactly, do not change signatures):
```cpp
{skeleton}
```

Java method to translate:
```java
{method.code}
```

Java signature: {java_signature}
Target C++ signature (hint): {cpp_signature_hint}

Already-translated callee signatures (use them to match calls):
{callee_section}

Respond with ONLY a JSON object:
{{
  "complete_translated_code": "the full C++ method definition, e.g. `int Foo::bar(int x) {{ ... }}`; for a constructor use `Foo::Foo(...)`. Include any `#include <...>` needed at the top of the code string."
}}
"""


class AlphaTransStyleTranslator:
    """Reverse-call-order method translation with compile-feedback repair."""

    def __init__(
        self,
        generator: Generator,
        max_translate_attempts: int = 2,
        max_feedback_rounds: int = 3,
    ) -> None:
        self.generator = generator
        self.max_translate_attempts = max(1, max_translate_attempts)
        self.max_feedback_rounds = max(0, max_feedback_rounds)
        self.skeleton_builder = SkeletonBuilder()
        self._translated_by_key: Dict[str, str] = {}

    def run(self, project: Project) -> None:
        self.skeleton_builder.build_all(project.headers)
        self._translated_by_key = {}

        ordered_layers = self._reverse_call_order_layers(project)
        print(
            f"AlphaTrans-style: translating {sum(len(layer) for layer in ordered_layers)} "
            f"methods in {len(ordered_layers)} reverse-call-order layers"
        )

        for layer_idx, layer in enumerate(ordered_layers):
            pending = [m for m in layer if self._should_translate(m)]
            if not pending:
                print(f"Layer {layer_idx}: no methods to translate")
                continue
            translated = self._translate_batch(pending)
            print(f"Layer {layer_idx}: translated {translated}/{len(pending)} methods")

    # -- public helpers used by the pipeline --------------------------------

    def get_translated_method_code(self, method: Method) -> str:
        return self._translated_by_key.get(method.key, "")

    def translate_single_with_feedback(
        self,
        method: Method,
        error_log: str,
        attempt: int,
    ) -> Tuple[bool, str]:
        """Reprompt a single failed method with the compile error log."""
        prompt = self._build_feedback_prompt(method, error_log)
        try:
            output = self.generator.generate([prompt])[0]
        except Exception as exc:  # pragma: no cover - network/API errors
            print(f"feedback LLM call failed for {method.key}: {exc}")
            return False, ""
        code = self._extract_code(output)
        if code:
            self._translated_by_key[method.key] = code
            return True, code
        return False, ""

    # -- internals -----------------------------------------------------------

    def _reverse_call_order_layers(self, project: Project) -> List[List[Method]]:
        """Group methods into layers: callees before callers (Kahn on call graph)."""
        all_methods: List[Method] = []
        for layer in project.methods:
            all_methods.extend(layer)

        in_degree = {m.key: len(m.children) for m in all_methods}
        queue = [m for m in all_methods if in_degree[m.key] == 0]
        key_to_method = {m.key: m for m in all_methods}
        layers: List[List[Method]] = []

        visited: set = set()
        while queue:
            layer_methods: List[Method] = []
            next_queue: List[Method] = []
            for method in queue:
                if method.key in visited:
                    continue
                visited.add(method.key)
                layer_methods.append(method)
                for parent in method.parents:
                    parent_key = parent.key if isinstance(parent, Method) else parent
                    if parent_key not in in_degree:
                        continue
                    in_degree[parent_key] -= 1
                    if in_degree[parent_key] == 0:
                        next_queue.append(key_to_method.get(parent_key))
            if layer_methods:
                layers.append(layer_methods)
            queue = [m for m in next_queue if m is not None and m.key not in visited]

        # Any remaining (cycles): append in original order.
        remaining = [m for m in all_methods if m.key not in visited]
        if remaining:
            layers.append(remaining)
        return layers

    def _should_translate(self, method: Method) -> bool:
        if method.header.type == "interface":
            return False
        sig = parse_java_signature(method)
        if sig is None:
            return False
        code = method.code or ""
        if not code.strip() or "(interface) no body" in code:
            return False
        if method.key in self._translated_by_key:
            return False
        return True

    def _translate_batch(self, methods: List[Method]) -> int:
        pending = list(methods)
        translated_count = 0
        for attempt in range(1, self.max_translate_attempts + 1):
            if not pending:
                break
            prompts = [self._build_translation_prompt(m) for m in pending]
            try:
                outputs = self.generator.generate(prompts)
            except Exception as exc:  # pragma: no cover
                print(f"batch LLM call failed: {exc}")
                break

            still_pending: List[Method] = []
            for method, output in zip(pending, outputs):
                code = self._extract_code(output)
                if code and self._looks_like_method(method, code):
                    self._translated_by_key[method.key] = code
                    translated_count += 1
                else:
                    still_pending.append(method)
            pending = still_pending

        if pending:
            print(f"warning: {len(pending)} methods failed translation after {self.max_translate_attempts} attempts")
        return translated_count

    def _build_translation_prompt(self, method: Method) -> str:
        skeleton = method.header.translated_code
        translated_callees = self._translated_callee_context(method)
        return build_method_translation_prompt(method, skeleton, translated_callees)

    def _translated_callee_context(self, method: Method) -> str:
        lines: List[str] = []
        for child in method.children:
            child_key = child.key if isinstance(child, Method) else child
            child_code = self._translated_by_key.get(child_key, "")
            if child_code:
                lines.append(f"- {child_key}\n{child_code}")
        return "\n".join(lines)

    def _build_feedback_prompt(self, method: Method, error_log: str) -> str:
        skeleton = method.header.translated_code
        previous_code = self._translated_by_key.get(method.key, "")
        translated_callees = self._translated_callee_context(method)
        return f"""The following C++ method translation failed to compile.

Class skeleton:
```cpp
{skeleton}
```

Previous (failing) translation:
```cpp
{previous_code}
```

Compiler error log:
```
{error_log}
```

Java source of the method:
```java
{method.code}
```

Already-translated callee signatures:
{translated_callees}

Fix the C++ method definition so it compiles. Respond with ONLY a JSON object:
{{"complete_translated_code": "the corrected full C++ method definition"}}
"""

    def _extract_code(self, output: str) -> str:
        """Extract complete_translated_code from the LLM JSON response."""
        json_match = re.search(r"\{.*\}", output, re.DOTALL)
        if not json_match:
            return ""
        try:
            data = json.loads(json_match.group(0))
            code = data.get("complete_translated_code", "")
            if isinstance(code, str):
                return code.strip()
        except json.JSONDecodeError:
            # Try to grab the first code block as a fallback.
            block = re.search(r"```(?:cpp|C\+\+)?\s*(.*?)```", output, re.DOTALL)
            if block:
                return block.group(1).strip()
        return ""

    def _looks_like_method(self, method: Method, code: str) -> bool:
        method_name = method.get_name()
        if method_name == "<init>":
            return method.header.translated_class_name.split("::")[-1] in code
        return method_name in code
