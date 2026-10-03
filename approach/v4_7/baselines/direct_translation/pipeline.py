from __future__ import annotations

"""Direct translation + compile-error feedback baseline orchestrator."""

import json
import re
import shutil
from pathlib import Path
from typing import Dict, List

from path_config import cfg_run_result_dir, cfg_source_code_dir_path
from utils.Generator import Generator

from v4_7.steps.cpp_compile_step import CppCompileStep, CppCompileSummary


def _extract_code_pair(output: str) -> tuple[str, str]:
    json_match = re.search(r"\{.*\}", output, re.DOTALL)
    if json_match:
        try:
            data = json.loads(json_match.group(0))
            header = data.get("translated_header", "")
            source = data.get("translated_source", "")
            if isinstance(header, str) and isinstance(source, str):
                return header.strip(), source.strip()
        except json.JSONDecodeError:
            pass
    blocks = re.findall(r"```(?:cpp|C\+\+)?\s*(.*?)```", output, re.DOTALL)
    if len(blocks) >= 2:
        return blocks[0].strip(), blocks[1].strip()
    return "", ""


def build_translation_prompt(
    java_source: str,
    java_name: str,
    header_name: str,
    cpp_name: str,
) -> str:
    return f"""Translate the following Java file to C++.

Translate the WHOLE Java file into a C++17 header/implementation pair:
- `{header_name}` must contain #pragma once, required standard includes, and every class/interface/enum declaration.
- `{cpp_name}` must begin with #include "{header_name}" and contain all non-template method definitions.
- Keep template definitions in the header when C++ requires them there.
- The pair must be self-contained. Do NOT reference project headers from other files; add minimal forward declarations or compile-safe placeholder types for cross-file dependencies.
- Keep class names, method names, and public APIs identical to the Java code.

Java file `{java_name}`:
```java
{java_source}
```

Respond with ONLY a JSON object:
{{"translated_header": "the complete {header_name} content", "translated_source": "the complete {cpp_name} content"}}
"""


def build_feedback_prompt(
    java_source: str,
    java_name: str,
    header_name: str,
    cpp_name: str,
    previous_header: str,
    previous_cpp: str,
    error_log: str,
) -> str:
    return f"""The following C++ translation failed to compile.

Fix both files so the header self-include unit and implementation compile with C++17:
- `{header_name}` must contain #pragma once, required standard includes, and every class/interface/enum declaration.
- `{cpp_name}` must begin with #include "{header_name}" and contain all non-template method definitions.
- Keep template definitions in the header when C++ requires them there.
- The pair must be self-contained. Do NOT reference project headers from other files; add minimal forward declarations or compile-safe placeholder types for cross-file dependencies.
- Keep class names, method names, and public APIs identical to the Java code.

Java file `{java_name}`:
```java
{java_source}
```

Previous header `{header_name}`:
```cpp
{previous_header}
```

Previous implementation `{cpp_name}`:
```cpp
{previous_cpp}
```

Compiler error log:
```
{error_log}
```

Respond with ONLY a JSON object:
{{"translated_header": "the corrected complete {header_name} content", "translated_source": "the corrected complete {cpp_name} content"}}
"""


class DirectTranslationPipeline:
    """Translation-only baseline with optional compile-error feedback rounds."""

    def __init__(
        self,
        generator: Generator,
        max_feedback_rounds: int = 3,
        compile_timeout: int = 60,
    ) -> None:
        self.generator = generator
        self.max_feedback_rounds = max(0, max_feedback_rounds)
        self.compile_step = CppCompileStep(timeout_seconds=compile_timeout)

    def run(self, ai_name: str, project_name: str, run_id: str = "") -> None:
        src_dir = cfg_source_code_dir_path(project_name)
        java_files = sorted(src_dir.rglob("*.java"))
        if not java_files:
            print(f"No .java files found under {src_dir}")
            return

        result_dir = cfg_run_result_dir(ai_name, project_name, "v4_7", run_id)
        result_dir.mkdir(parents=True, exist_ok=True)
        self._clean_result_dir(result_dir)

        cpp_names = {jf: self._cpp_name(jf, src_dir) for jf in java_files}
        header_names = {jf: Path(cpp_names[jf]).with_suffix(".h").name for jf in java_files}
        print(f"Direct translation: {len(java_files)} Java files -> {result_dir}")

        self._translate_all(java_files, header_names, cpp_names, result_dir, feedback={})

        for round_idx in range(1, self.max_feedback_rounds + 1):
            header_summary = self._compile_headers(result_dir)
            cpp_summary = self._compile_cpp(result_dir)
            failed_stems = {
                Path(r.file).stem
                for r in header_summary.results + cpp_summary.results
                if not r.success
            }
            if not failed_stems:
                print("All files compile. Done.")
                break
            print(f"Feedback round {round_idx}/{self.max_feedback_rounds}: {len(failed_stems)} file pairs failing")
            feedback = self._load_error_logs(result_dir)
            self._translate_all(java_files, header_names, cpp_names, result_dir, feedback=feedback)

        final_headers = self._compile_headers(result_dir)
        final_cpp = self._compile_cpp(result_dir)
        print(
            "Direct translation baseline final compile: "
            f"headers={final_headers.success_count}/{final_headers.total_count}, "
            f"cpp={final_cpp.success_count}/{final_cpp.total_count}"
        )

    # -- internals -----------------------------------------------------------

    def _clean_result_dir(self, result_dir: Path) -> None:
        for f in result_dir.iterdir():
            if f.is_file() and f.suffix in {".cpp", ".h", ".hpp", ".o"}:
                f.unlink()
        compile_report = result_dir / "compile_report"
        if compile_report.exists():
            shutil.rmtree(compile_report, ignore_errors=True)

    def _cpp_name(self, java_file: Path, src_dir: Path) -> str:
        rel = java_file.relative_to(src_dir)
        parts = list(rel.parts)
        parts[-1] = parts[-1].replace(".java", ".cpp")
        return "__".join(parts)

    def _translate_all(
        self,
        java_files: List[Path],
        header_names: Dict[Path, str],
        cpp_names: Dict[Path, str],
        result_dir: Path,
        feedback: Dict[str, str],
    ) -> None:
        targets = [
            jf for jf in java_files
            if not feedback or cpp_names[jf] in feedback
        ]
        prompts = []
        for jf in targets:
            java_source = jf.read_text(encoding="utf-8")
            error_log = feedback.get(cpp_names[jf], "")
            if error_log:
                prompts.append(build_feedback_prompt(
                    java_source,
                    jf.name,
                    header_names[jf],
                    cpp_names[jf],
                    self._read_translated(result_dir, header_names[jf]),
                    self._read_translated(result_dir, cpp_names[jf]),
                    error_log[:6000],
                ))
            else:
                prompts.append(build_translation_prompt(
                    java_source, jf.name, header_names[jf], cpp_names[jf]
                ))
        outputs = self.generator.generate(prompts)
        translated = 0
        for jf, output in zip(targets, outputs):
            header_code, cpp_code = _extract_code_pair(output)
            if not header_code or not cpp_code:
                self._write_translated(
                    result_dir,
                    header_names[jf],
                    '#pragma once\n#error "LLM did not return a complete header/source pair"',
                )
                self._write_translated(
                    result_dir,
                    cpp_names[jf],
                    f'#include "{header_names[jf]}"\n#error "LLM did not return a complete header/source pair"',
                )
                continue
            if "#pragma once" not in header_code:
                header_code = "#pragma once\n" + header_code
            include_line = f'#include "{header_names[jf]}"'
            if include_line not in cpp_code:
                cpp_code = include_line + "\n" + cpp_code
            self._write_translated(result_dir, header_names[jf], header_code)
            self._write_translated(result_dir, cpp_names[jf], cpp_code)
            translated += 1
        print(f"  translated/rewrote {translated}/{len(targets)} header/source pairs")

    def _write_translated(self, result_dir: Path, cpp_name: str, code: str) -> None:
        (result_dir / cpp_name).write_text(code.rstrip() + "\n", encoding="utf-8")

    def _read_translated(self, result_dir: Path, cpp_name: str) -> str:
        path = result_dir / cpp_name
        if not path.exists():
            return "(not translated yet)"
        return path.read_text(encoding="utf-8", errors="replace")

    def _compile_cpp(self, result_dir: Path) -> CppCompileSummary:
        report_dir = result_dir / "compile_report"
        log_dir = report_dir / "failed_cpp_compile_logs"
        report_dir.mkdir(parents=True, exist_ok=True)
        log_dir.mkdir(parents=True, exist_ok=True)
        self.compile_step._clear_failed_logs(log_dir)

        cpp_files = sorted(
            f for f in result_dir.iterdir()
            if f.is_file() and f.suffix == ".cpp" and not f.name.startswith("__compile_header__")
        )
        results = []
        for cpp_file in cpp_files:
            result = self.compile_step._compile_cpp_file(cpp_file, result_dir)
            results.append(result)
            self.compile_step._write_failed_log(result, log_dir)

        success_count = sum(1 for r in results if r.success)
        total_count = len(results)

        summary = CppCompileSummary(
            total_count=total_count,
            success_count=success_count,
            failed_count=total_count - success_count,
            success_rate=success_count / total_count if total_count else 1.0,
            results=results,
        )
        self.compile_step._write_summary(summary, report_dir)
        print(
            f"C++ compile check: total={total_count}, success={success_count}, "
            f"failed={total_count - success_count}, success_rate={summary.success_rate:.4f}"
        )
        return summary

    def _compile_headers(self, result_dir: Path) -> CppCompileSummary:
        report_dir = result_dir / "compile_report"
        log_dir = report_dir / "failed_header_compile_logs"
        report_dir.mkdir(parents=True, exist_ok=True)
        log_dir.mkdir(parents=True, exist_ok=True)
        self.compile_step._clear_failed_logs(log_dir)

        header_files = sorted(
            f for f in result_dir.iterdir()
            if f.is_file() and f.suffix in {".h", ".hpp"}
        )
        results = []
        for header_file in header_files:
            result = self.compile_step._compile_header_file(header_file, result_dir)
            results.append(result)
            self.compile_step._write_failed_log(result, log_dir)

        success_count = sum(1 for r in results if r.success)
        total_count = len(results)
        summary = CppCompileSummary(
            total_count=total_count,
            success_count=success_count,
            failed_count=total_count - success_count,
            success_rate=success_count / total_count if total_count else 1.0,
            results=results,
        )
        self.compile_step._write_summary(
            summary, report_dir, file_name="header_compile_summary.json"
        )
        print(
            f"C++ header compile check: total={total_count}, success={success_count}, "
            f"failed={total_count - success_count}, success_rate={summary.success_rate:.4f}"
        )
        return summary

    def _load_error_logs(self, result_dir: Path) -> Dict[str, str]:
        logs: Dict[str, str] = {}
        report_dir = result_dir / "compile_report"
        for kind, log_dir_name in (
            ("header", "failed_header_compile_logs"),
            ("implementation", "failed_cpp_compile_logs"),
        ):
            log_dir = report_dir / log_dir_name
            if not log_dir.exists():
                continue
            for log_file in log_dir.glob("*.log"):
                cpp_name = log_file.stem + ".cpp"
                if not (result_dir / cpp_name).exists():
                    continue
                log = log_file.read_text(encoding="utf-8", errors="replace")
                logs[cpp_name] = logs.get(cpp_name, "") + f"\n[{kind} compile]\n{log}"
        return logs
