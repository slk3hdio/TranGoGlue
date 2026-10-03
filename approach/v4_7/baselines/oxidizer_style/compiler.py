from __future__ import annotations

import json
import hashlib
import re
import subprocess
import time
from pathlib import Path

from v4_7.steps.cpp_compile_step import link_project_dir

from .models import CheckResult


class OxidizerCompiler:
    """Run isolated syntax, object, and whole-project checks with clang++."""

    def __init__(self, timeout_seconds: int = 60):
        self.timeout_seconds = timeout_seconds

    def check_syntax(self, source: Path, work_dir: Path) -> CheckResult:
        return self._run(source, work_dir, syntax_only=True)

    def check_object(self, source: Path, work_dir: Path) -> CheckResult:
        return self._run(source, work_dir, syntax_only=False)

    def version(self) -> str:
        try:
            proc = subprocess.run(
                ["clang++", "--version"],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=self.timeout_seconds,
            )
            return ((proc.stdout or "") + (proc.stderr or "")).splitlines()[0].strip()
        except (FileNotFoundError, subprocess.TimeoutExpired, IndexError):
            return "unavailable"

    def evaluate_project(self, result_dir: Path, report_dir: Path, has_stubs: bool) -> dict:
        result_dir = Path(result_dir)
        report_dir.mkdir(parents=True, exist_ok=True)
        headers = sorted(
            path for path in result_dir.iterdir()
            if path.is_file() and path.suffix in {".h", ".hpp"}
        )
        sources = sorted(
            path for path in result_dir.iterdir()
            if path.is_file() and path.suffix == ".cpp" and not path.name.startswith("__")
        )

        header_results = [self._evaluate_file(path, result_dir, is_header=True) for path in headers]
        source_results = [self._evaluate_file(path, result_dir, is_header=False) for path in sources]
        self._write_final_file_logs(report_dir / "headers", header_results)
        self._write_final_file_logs(report_dir / "sources", source_results)
        operational_link, link_log = link_project_dir(
            result_dir,
            compile_timeout=self.timeout_seconds,
            link_timeout=max(120, self.timeout_seconds * 2),
        )
        final = {
            "headers": header_results,
            "sources": source_results,
            "header_syntax_rate": self._rate(header_results, "syntax_success"),
            "header_compile_rate": self._rate(header_results, "compile_success"),
            "cpp_syntax_rate": self._rate(source_results, "syntax_success"),
            "cpp_compile_rate": self._rate(source_results, "compile_success"),
            "operational_link_success": operational_link,
            "strict_link_success": operational_link and not has_stubs,
            "link_log": link_log,
        }
        (report_dir / "final_compile_summary.json").write_text(
            json.dumps(final, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        if link_log:
            (report_dir / "link.log").write_text(link_log, encoding="utf-8")
        return final

    @staticmethod
    def _write_final_file_logs(target_dir: Path, results: list[dict]) -> None:
        target_dir.mkdir(parents=True, exist_ok=True)
        for result in results:
            safe_name = re.sub(r"[^A-Za-z0-9_.-]+", "_", result["file"])
            for check in ("syntax", "compile"):
                success = result[f"{check}_success"]
                log = result[f"{check}_log"] or ("success\n" if success else "failed without diagnostics\n")
                (target_dir / f"{safe_name}.{check}.log").write_text(log, encoding="utf-8")

    def _evaluate_file(self, path: Path, work_dir: Path, is_header: bool) -> dict:
        source = self._header_unit(path, work_dir) if is_header else path
        try:
            syntax = self.check_syntax(source, work_dir)
            compile_result = self.check_object(source, work_dir) if syntax.success else CheckResult(False, syntax.log)
            return {
                "file": path.name,
                "syntax_success": syntax.success,
                "compile_success": compile_result.success,
                "syntax_log": syntax.log,
                "compile_log": compile_result.log,
            }
        finally:
            if is_header and source.exists():
                source.unlink()

    def source_for_fragment(self, header_name: str, cpp_name: str, result_dir: Path, in_header: bool) -> tuple[Path, bool]:
        if in_header:
            header = result_dir / header_name
            return self._header_unit(header, result_dir), True
        cpp = result_dir / cpp_name
        if cpp.exists():
            return cpp, False
        safe_name = re.sub(r"[^A-Za-z0-9_.-]+", "_", Path(cpp_name).stem)
        missing = result_dir / f"__oxidizer_missing_{safe_name}.cpp"
        missing.write_text(
            f'#error "expected generated implementation {cpp_name} is missing"\n',
            encoding="utf-8",
        )
        return missing, True

    def write_fragment_logs(
        self,
        report_dir: Path,
        fragment_id: str,
        attempt: int,
        syntax: CheckResult,
        compile_result: CheckResult,
    ) -> None:
        normalized = re.sub(r"[^A-Za-z0-9_.-]+", "_", fragment_id)
        digest = hashlib.sha256(fragment_id.encode("utf-8")).hexdigest()[:12]
        safe_id = f"{normalized[:48]}_{digest}"
        target = report_dir / "fragment_logs" / safe_id
        target.mkdir(parents=True, exist_ok=True)
        if syntax.log:
            (target / f"attempt_{attempt:02d}.syntax.log").write_text(syntax.log, encoding="utf-8")
        if compile_result.log:
            (target / f"attempt_{attempt:02d}.compile.log").write_text(compile_result.log, encoding="utf-8")

    def _header_unit(self, header: Path, work_dir: Path) -> Path:
        safe_name = re.sub(r"[^A-Za-z0-9_.-]+", "_", header.stem)
        unit = work_dir / f"__oxidizer_header_{safe_name}.cpp"
        unit.write_text(f'#include "{header.name}"\n', encoding="utf-8")
        return unit

    def _run(self, source: Path, work_dir: Path, syntax_only: bool) -> CheckResult:
        start = time.monotonic()
        obj_path = work_dir / f"__oxidizer_{source.stem}.o"
        command = [
            "clang++",
            "-std=c++17",
            "-ferror-limit=10",
            "-ftemplate-backtrace-limit=5",
            "-fno-caret-diagnostics",
        ]
        if syntax_only:
            command.append("-fsyntax-only")
        else:
            command.extend(["-c", source.name, "-o", obj_path.name])
        if syntax_only:
            command.append(source.name)

        try:
            proc = subprocess.run(
                command,
                cwd=str(work_dir),
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=self.timeout_seconds,
            )
            return CheckResult(
                success=proc.returncode == 0,
                log=(proc.stdout or "") + (proc.stderr or ""),
                elapsed_seconds=round(time.monotonic() - start, 4),
            )
        except subprocess.TimeoutExpired as exc:
            output = (exc.stdout or "") + (exc.stderr or "")
            return CheckResult(False, f"{output}\ncheck timed out", round(time.monotonic() - start, 4))
        except FileNotFoundError:
            return CheckResult(False, "Compiler (clang++) not found.", round(time.monotonic() - start, 4))
        finally:
            if obj_path.exists():
                obj_path.unlink()

    @staticmethod
    def _rate(results: list[dict], key: str) -> float:
        return sum(1 for result in results if result[key]) / len(results) if results else 0.0
