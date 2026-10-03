from __future__ import annotations


def header_translate_batch_prompt(
    batch_sections: str,
    available_headers: str,
    batch_header_names: str,
) -> str:
    json_example = """```json
{
    "translated_code": [
        {
            "class_name": "HeaderA",
            "translated_code": "#pragma once\\n#include <string>\\nclass HeaderA {\\npublic:\\n    void run();\\n};"
        },
        {
            "class_name": "HeaderB",
            "translated_code": "#pragma once\\nclass HeaderB {\\npublic:\\n    int size() const;\\n};"
        }
    ],
    "external_headers": [
        {
            "class_name": "Helper",
            "content": "#pragma once\\nclass Helper {\\npublic:\\n    int value() const;\\n};"
        }
    ]
}
```"""

    return f"""You are generating the initial C++ header set for a Java-to-C++ migration project.

This is round 1. In this round, you must produce complete header files for the target Java headers.
Any helper file that does not already exist in the project must be emitted through `external_headers`.
Every helper file you create will become a real project header after this batch.

Target headers in this batch:
{batch_header_names}

Batch details:
{batch_sections}

Available project headers that may be included directly:
{available_headers}

Requirements:
1. Return one valid JSON object only.
2. The top-level keys must be:
   - required key `translated_code`
   - optional key `external_headers`
3. `translated_code` must be a list.
4. Each item in `translated_code` must be an object with:
   - `class_name`
   - `translated_code`
5. The `translated_code` list must contain exactly one item for each target header in this batch, and no extra items.
6. Each item `translated_code` value must be a complete compilable header file.
7. `external_headers`, if present, must be a top-level list of brand-new helper headers required by this batch.
8. Do not put `external_headers` inside a single translated header entry.
9. Do not emit a helper header if an equivalent project header already exists in the available header list.
10. Non-template methods should be declared but not implemented in the header.
11. Use only:
   - the available project headers listed above,
   - helper headers emitted in this same answer,
   - or C++ standard library headers.
12. Do not output any header outside this batch.
13. Do not add custom namespaces unless absolutely necessary.
14. Preserve every concrete method declared by every Java nested/inner class. For each such method, emit a corresponding C++ declaration in the concrete nested class; do not omit the concrete nested class, replace it with only an interface or forward declaration, or assume that its methods are covered by similarly named interface methods.
15. Forward declarations of concrete nested classes are not sufficient. Emit the complete concrete nested-class declarations, including the fields and method declarations needed to translate all of their Java methods in the later method-translation stage.

Return valid JSON only in the following format:
{json_example}
"""


def header_patch_batch_prompt(
    target_sections: str,
    context_sections: str,
    available_headers: str,
    batch_header_names: str,
) -> str:
    json_example = """```json
{
    "modify": [
        {
            "class_name": "HeaderA",
            "original_str": "#include \\"OldHelper.h\\"",
            "new_str": "#include \\"NewHelper.h\\"",
            "modified_part": "includes"
        }
    ],
    "add": [
        {
            "class_name": "NewHelper",
            "file_name": "NewHelper.h",
            "content": "#pragma once\\nclass NewHelper {\\npublic:\\n    int value() const;\\n};",
            "fields": [],
            "methods": [
                "int value() const;"
            ]
        }
    ]
}
```"""

    context_block = context_sections.strip() or "(No additional context headers.)"
    return f"""You are repairing an existing C++ header set for a Java-to-C++ migration project.

This is round 2 or later. Do not regenerate whole headers by logical unit. The current project already has
real header files. You must describe the next repair as one unified batch patch.

Available project headers:
{available_headers}

Current target headers in this batch:
{batch_header_names}

Target header states and local compile issues:
{target_sections}

Related context headers:
{context_block}

Output protocol:
1. Return one valid JSON object only.
2. The top level must contain exactly two keys: `modify` and `add`.
3. `modify` patches existing header files only.
4. `add` creates brand-new header files only.
5. If no change is needed, return `{{"modify": [], "add": []}}`.

Rules for `modify`:
1. `class_name` is the C++ class name being patched.
2. `original_str` MUST be copy-pasted exactly from the current file content, character for character.
3. `new_str` is the replacement text.
4. `modified_part` must be one of: `includes`, `fields`, `methods`, `others`.
5. Use the smallest patch set that fixes the reported local issues.

Rules for `add`:
1. `file_name` must be a brand-new `.h` file.
2. `content` must be a complete compilable header file.
3. `fields` and `methods` are concise summaries for reporting only.
4. Only create a new helper header when patching existing files is not enough.

Hard constraints:
1. Do not output full translated headers grouped by logical header name.
2. Do not add any top-level key other than `modify` and `add`.
3. Do not reference custom project headers that are not already available or newly added in this batch.
4. Prefer fixing the concrete compile errors instead of redesigning unrelated parts.
5. Prefer leaving headers whose compile status is already `success` unchanged unless a successful header must change to fix a failed header in the same batch.
6. When override, inheritance, or signature-mismatch issues are reported, compare them against the related context headers before writing patches.
7. Preserve every concrete method declared by every Java nested/inner class. If a concrete nested class or any of its methods is missing from the current C++ header, add its complete declaration; an interface declaration or a forward declaration alone does not cover the concrete Java methods.
8. Do not solve a missing nested-class declaration by deleting or merging its source methods, and do not introduce placeholder method bodies such as empty bodies, unconditional default returns, or `return nullptr`.

Return valid JSON only in the following format:
{json_example}
"""
