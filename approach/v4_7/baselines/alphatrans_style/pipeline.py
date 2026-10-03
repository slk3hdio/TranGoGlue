from __future__ import annotations

"""AlphaTrans-style ablation baseline pipeline orchestrator."""

import shutil
from pathlib import Path
from typing import List, Optional

from graph import Header, Method, Project
from path_config import cfg_run_graph_dir, cfg_run_result_dir
from utils.Generator import Generator

from v4_7.steps.cpp_compile_step import CppCompileStep
from v4_7.steps.step01_graph_build import GraphBuildStep

from .translator import AlphaTransStyleTranslator


class AlphaTransStylePipeline:
    """End-to-end AlphaTrans-style baseline run.

    Outputs to the same run directory layout as the full pipeline
    (result/*.h, result/*.cpp, result/compile_report/cpp_compile_summary.json)
    so the compile pass rates are directly comparable.
    """

    def __init__(
        self,
        generator: Generator,
        max_translate_attempts: int = 2,
        max_feedback_rounds: int = 3,
        compile_timeout: int = 60,
    ) -> None:
        self.generator = generator
        self.graph_build_step = GraphBuildStep()
        self.translator = AlphaTransStyleTranslator(
            generator,
            max_translate_attempts=max_translate_attempts,
            max_feedback_rounds=max_feedback_rounds,
        )
        self.cpp_compile_step = CppCompileStep(timeout_seconds=compile_timeout)

    def run(
        self,
        ai_name: str,
        project_name: str,
        force_rebuild: bool = False,
        run_id: str = "",
        max_feedback_rounds: Optional[int] = None,
    ) -> Project:
        project = self.graph_build_step.build_graph(
            ai_name, project_name, force_rebuild=force_rebuild, run_id=run_id
        )
        result_dir = cfg_run_result_dir(ai_name, project_name, "v4_7", run_id)
        result_dir.mkdir(parents=True, exist_ok=True)

        if max_feedback_rounds is not None:
            self.translator.max_feedback_rounds = max(0, max_feedback_rounds)

        print("========== AlphaTrans-style baseline: skeleton construction ==========")
        self.translator.run(project)

        print("========== AlphaTrans-style baseline: file generation ==========")
        self._generate_files(project, result_dir)

        print("========== AlphaTrans-style baseline: compile + feedback repair ==========")
        for round_idx in range(1, self.translator.max_feedback_rounds + 1):
            summary = self.cpp_compile_step.compile_cpp_files(result_dir, project)
            failed_files = [
                r.file for r in summary.results if not r.success
            ]
            if not failed_files:
                print("All .cpp files compile. Done.")
                break

            print(f"Feedback round {round_idx}/{self.translator.max_feedback_rounds}: {len(failed_files)} files failing")
            repaired_any = False
            for file_name in failed_files:
                repaired_any = self._repair_file(project, result_dir, file_name) or repaired_any
            if not repaired_any:
                print("No method could be repaired in this round; stopping repair.")
                break
            self._generate_files(project, result_dir)

        final_summary = self.cpp_compile_step.compile_cpp_files(result_dir, project)
        print(f"AlphaTrans-style baseline final compile: {final_summary.success_count}/{final_summary.total_count}")
        return project

    # -- internals -----------------------------------------------------------

    def _generate_files(self, project: Project, result_dir: Path) -> None:
        # Clean old generated files.
        for f in result_dir.iterdir():
            if f.is_file() and f.suffix in {".h", ".cpp", ".hpp", ".o"}:
                f.unlink()

        # Write headers from skeletons.
        for header in project.headers:
            if header.is_generated_external():
                continue
            if not header.translated_code.strip():
                continue
            header_path = result_dir / header.get_output_header_name()
            header_path.write_text(header.translated_code, encoding="utf-8")

        # Group translated methods by header and write .cpp files.
        cpp_by_header: dict = {}
        for header in project.headers:
            method_codes: List[str] = []
            for method in header.methods:
                code = self.translator.get_translated_method_code(method)
                if code:
                    method_codes.append(code)
            if method_codes:
                cpp_by_header[header.key] = method_codes

        for header_key, method_codes in cpp_by_header.items():
            header = project.find_header(header_key)
            if header is None:
                continue
            cpp_path = result_dir / header.get_output_cpp_name()
            includes = [f'#include "{header.get_output_header_name()}"']
            for code in method_codes:
                for line in code.splitlines():
                    if line.strip().startswith("#include") and line.strip() not in includes:
                        includes.append(line.strip())
            cpp_path.write_text(
                "\n".join(includes) + "\n\n" + "\n\n".join(method_codes) + "\n",
                encoding="utf-8",
            )

    def _repair_file(self, project: Project, result_dir: Path, file_name: str) -> bool:
        """Reprompt methods of a failing .cpp file with the compile error."""
        header = self._find_header_by_cpp_name(project, file_name)
        if header is None:
            print(f"  no header found for {file_name}; skipping")
            return False

        log_path = result_dir / "compile_report" / "failed_cpp_compile_logs" / f"{file_name}.log"
        error_log = ""
        if log_path.exists():
            error_log = log_path.read_text(encoding="utf-8", errors="replace")[:4000]
        if not error_log:
            error_log = "(no log available)"

        repaired = False
        for method in header.methods:
            if not self.translator.get_translated_method_code(method):
                continue
            attempt = 1
            while attempt <= self.translator.max_translate_attempts:
                ok, _ = self.translator.translate_single_with_feedback(method, error_log, attempt)
                if ok:
                    repaired = True
                    break
                attempt += 1
        return repaired

    def _find_header_by_cpp_name(self, project: Project, cpp_name: str) -> Optional[Header]:
        for header in project.headers:
            if header.get_output_cpp_name() == cpp_name:
                return header
        return None
