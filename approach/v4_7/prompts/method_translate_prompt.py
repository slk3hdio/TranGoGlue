from pydantic import BaseModel


class TranslatedMethod(BaseModel):
    class_name: str
    translated_declaration: str
    implementation: str
    method_detail: str


def method_translate_prompt_direct_with_context(
    source_code: str,
    method_code: str,
    header_code: str,
    all_headers: str,
    dependency_signature_context: str,
    related_headers_context: str,
    translated_declaration: str = "",
) -> str:
    json_example = """```json
{
    \"class_name\": \"ExampleClass\",
    \"method_signature_java\": \"ExampleClass:exampleMethod(Integer,Integer)\",
    \"method_signature_cpp\": \"ExampleClass::exampleMethod(int,int)\",
    \"complete_translated_code\": \"#include <algorithm>\\ndouble ExampleClass::exampleMethod(int a, int b) {\\n    double a_double = a;\\n    double b_double = max(1, b);\\n    return a_double / b_double;\\n}\"
}
```"""
    dependency_section = (
        dependency_signature_context.strip()
        if dependency_signature_context.strip()
        else "(No dependency method signatures are available.)"
    )
    related_headers_section = (
        related_headers_context.strip()
        if related_headers_context.strip()
        else "(No additional related header context is available.)"
    )
    declaration_section = translated_declaration.strip() or "(No mapped C++ definition signature is available; infer the target signature from the header code.)"
    prompt = f"""The following Java code is supposed to be translated into C++ code:
{source_code}

Now we have the translated header code:
{header_code}

We will translate the member methods one by one following the method dependency graph. The current method is:
{method_code}

The target C++ definition signature is:
{declaration_section}

The following dependency method signatures are relevant to the current method. Use them only as high-level dependency hints, not as exact implementation contracts:
{dependency_section}

The following related project headers are available as contract context. When calling project methods, using project constants, or referencing project types, match these declarations exactly:
{related_headers_section}

Please provide the translated C++ method implementation and ensure the code can be compiled. The definition must match the target C++ definition signature exactly. Your response should be in JSON, for example:
{json_example}

Notes:
1. Please strictly adhere to the JSON format for output.
2. The following are the available custom header files, and only these custom headers may be included:
{all_headers}
3. Only the current method needs translation.
4. Do not add new logic that does not exist in the original Java code.
5. Do not invent new custom headers, new project classes, or new project-specific symbols beyond the provided available headers.
6. If Java references an unavailable project-specific implementation type, prefer a compile-safe fallback using only available types instead of introducing a missing header.
7. If dependency hints, prior translations, and related header declarations disagree, follow the provided header declarations.
8. If the current declaration is deleted, defaulted, or already defined inline in the header, do not invent an extra out-of-line definition.
9. Never make the code compile by replacing source behavior with an empty/no-op body, an unconditional default return, `return nullptr`, a fabricated constant, or an unsupported-operation exception. Preserve the complete behavior of the current Java method; repair an inadequate declaration instead of erasing behavior."""
    return prompt


def external_method_implement_prompt(
    header_code: str,
    target_declaration: str,
    all_headers: str,
    related_headers_context: str,
    usage_context: str,
) -> str:
    json_example = """```json
{
    "class_name": "ExampleClass",
    "method_signature_java": "",
    "method_signature_cpp": "ExampleClass::exampleMethod(int)",
    "complete_translated_code": "int ExampleClass::exampleMethod(int value) {\n    return value;\n}"
}
```"""
    related_headers_section = (
        related_headers_context.strip()
        if related_headers_context.strip()
        else "(No additional related header context is available.)"
    )
    usage_section = (
        usage_context.strip()
        if usage_context.strip()
        else "(No usage context from other project files is available.)"
    )
    declaration_section = target_declaration.strip() or "(Infer the target signature from the header code.)"
    prompt = f"""The following C++ header is a project-local placeholder generated for an unavailable external dependency (e.g. a JDK or third-party class). There is no Java source code for it:
{header_code}

One of its member functions is declared but not defined. Implement it now. The target C++ declaration is:
{declaration_section}

The following project headers use this placeholder class. Use them as semantic context so the implementation matches how the project actually uses it:
{usage_section}

Additional related header context:
{related_headers_section}

Please provide a semantically faithful C++ definition and ensure the code can be compiled. The definition must match the target C++ declaration exactly. Your response should be in JSON, for example:
{json_example}

Notes:
1. Please strictly adhere to the JSON format for output. method_signature_java may be left empty because there is no Java source method.
2. The following are the available custom header files, and only these custom headers may be included:
{all_headers}
3. Only the target declaration needs a definition; do not define other members.
4. Implement the behavior required by the usage context with available standard-library and project types. Never use an empty/no-op body, unconditional default return, `return nullptr`, fabricated constant, or unsupported-operation exception merely to satisfy compilation or linking.
5. Do not invent new custom headers, new project classes, or new project-specific symbols beyond the provided available headers.
6. Do not change the class interface in the header; provide only the out-of-line definition."""
    return prompt
