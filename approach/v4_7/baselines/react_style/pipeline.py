from __future__ import annotations

"""ReAct-style baseline pipeline orchestrator (file-level, one agent per Java class)."""

import json
import shutil
from pathlib import Path
from typing import Dict, List

from graph import Project
from path_config import cfg_run_graph_dir, cfg_run_result_dir
from utils.Generator import Generator

from v4_7.steps.cpp_compile_step import CppCompileStep
from v4_7.steps.step01_graph_build import GraphBuildStep

from .agent import ReactStyleFileAgent


class ReactStylePipeline:
    """End-to-end ReAct-style baseline run.

    Outputs to the same run directory layout as the full pipeline
    (result/*.h, result/*.cpp, result/compile_report/cpp_compile_summary.json)
    so the compile pass rates are directly comparable.
    """

    def __init__(
        self,
        generator: Generator,
        max_compile_attempts: int = 10,
        compile_timeout: int = 60,
    ) -> None:
        self.generator = generator
        self.max_compile_attempts = max_compile_attempts
        self.compile_timeout = compile_timeout
        self.graph_build_step = GraphBuildStep()
        self.cpp_compile_step = CppCompileStep(timeout_seconds=compile_timeout)

    def run(
        self,
        ai_name: str,
        project_name: str,
        force_rebuild: bool = False,
        run_id: str = "",
    ) -> Project:
        project = self.graph_build_step.build_graph(
            ai_name, project_name, force_rebuild=force_rebuild, run_id=run_id
        )
        result_dir = cfg_run_result_dir(ai_name, project_name, "v4_7", run_id)
        result_dir.mkdir(parents=True, exist_ok=True)
        self._clean_result_dir(result_dir)

        headers = [
            header for header in project.headers
            if not header.is_generated_external()
        ]
        print(
            f"========== ReAct-style baseline: translating {len(headers)} files =========="
        )

        per_file: List[Dict] = []
        for header in headers:
            header_name = header.get_output_header_name()
            cpp_name = header.get_output_cpp_name()
            agent = ReactStyleFileAgent(
                ai_name,
                project_name,
                header,
                generator=self.generator,
                work_dir=result_dir,
                target_header_name=header_name,
                target_cpp_name=cpp_name,
                max_compile_attempts=self.max_compile_attempts,
                compile_timeout=self.compile_timeout,
                history_dir=result_dir / "react_history",
            )
            result = agent.run()
            per_file.append({
                "file": cpp_name,
                "header": header_name,
                "status": result.get("status"),
                "attempts": result.get("attempts", 0),
                "interactions": result.get("interactions", 0),
                "error": result.get("error", ""),
                "message": result.get("message", ""),
            })
            print(f"{cpp_name}: {result.get('status')} ({result.get('attempts')} compiles)")

        summary_path = result_dir / "react_baseline_summary.json"
        summary_path.write_text(
            json.dumps({
                "max_compile_attempts": self.max_compile_attempts,
                "total_files": len(per_file),
                "success_files": sum(1 for r in per_file if r["status"] == "success"),
                "per_file": per_file,
            }, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        print("========== ReAct-style baseline: final compile check ==========")
        final_summary = self.cpp_compile_step.compile_cpp_files(result_dir, project)
        print(
            f"ReAct-style baseline final compile: "
            f"{final_summary.success_count}/{final_summary.total_count}"
        )
        return project

    def _clean_result_dir(self, result_dir: Path) -> None:
        for f in result_dir.iterdir():
            if f.is_file() and f.suffix in {".h", ".cpp", ".hpp", ".o"}:
                f.unlink()
        history_dir = result_dir / "react_history"
        if history_dir.exists():
            shutil.rmtree(history_dir)
