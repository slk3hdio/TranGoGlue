from __future__ import annotations

import json
import re
import shutil
import subprocess
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import List, Tuple

from graph import Project


def link_project_dir(work_dir: Path, compile_timeout: int = 60, link_timeout: int = 120) -> Tuple[bool, str]:
    """Compile every .cpp in work_dir and link them into one executable.

    Adds a stub ``int main()`` when no translation unit defines one.
    Returns (success, combined_log). Compile failures of individual files and
    link errors (undefined/duplicate symbols) are both reported in the log.
    """
    # 统一使用绝对路径，避免设置 cwd 后把相对目录前缀重复解析一次。
    work_dir = Path(work_dir).resolve()
    build_dir = work_dir / "__link_build__"
    if build_dir.exists():
        shutil.rmtree(build_dir)
    build_dir.mkdir(parents=True)

    logs: List[str] = []
    try:
        cpp_files = sorted(
            f for f in work_dir.iterdir()
            if f.is_file() and f.suffix == ".cpp" and not f.name.startswith("__compile_header__")
        )
        if not cpp_files:
            return True, ""

        has_main = any(
            re.search(r"\bint\s+main\s*\(", f.read_text(encoding="utf-8", errors="replace"))
            for f in cpp_files
        )
        if not has_main:
            stub = build_dir / "__main_stub.cpp"
            stub.write_text("int main() { return 0; }\n", encoding="utf-8")

        objects: List[Path] = []
        compile_failed = False
        for cpp_file in [*cpp_files, *([] if has_main else [build_dir / "__main_stub.cpp"])]:
            obj_file = build_dir / (cpp_file.stem + ".o")
            try:
                proc = subprocess.run(
                    [
                        "clang++",
                        "-std=c++17",
                        "-c",
                        "-ferror-limit=5",
                        "-ftemplate-backtrace-limit=5",
                        "-fno-caret-diagnostics",
                        "-fmacro-backtrace-limit=5",
                        str(cpp_file),
                        "-o",
                        str(obj_file),
                    ],
                    capture_output=True,
                    text=True, encoding="utf-8", errors="replace",
                    timeout=compile_timeout,
                    cwd=str(work_dir),
                )
            except subprocess.TimeoutExpired:
                compile_failed = True
                logs.append(f"[compile timeout] {cpp_file.name}")
                continue
            if proc.returncode != 0:
                compile_failed = True
                logs.append(f"[compile error] {cpp_file.name}\n{(proc.stdout or '') + (proc.stderr or '')}")
                continue
            objects.append(obj_file)

        if compile_failed:
            return False, "\n".join(logs)

        exe_file = build_dir / "__link_test__.exe"
        try:
            proc = subprocess.run(
                ["clang++", *[str(obj) for obj in objects], "-o", str(exe_file)],
                capture_output=True,
                text=True, encoding="utf-8", errors="replace",
                timeout=link_timeout,
                cwd=str(work_dir),
            )
        except subprocess.TimeoutExpired:
            return False, "[link timeout] linking all object files timed out"

        log_output = (proc.stdout or "") + (proc.stderr or "")
        if proc.returncode != 0:
            return False, f"[link error] whole-project link failed\n{log_output}"
        return True, log_output
    finally:
        shutil.rmtree(build_dir, ignore_errors=True)


@dataclass
class CppFileCompileResult:
    """单个 C++ 文件编译结果的载体。

    封装某个 .cpp/.h 文件的编译结果信息，包括成功与否、日志输出、
    目标 object 文件名与耗时，供上层汇总与诊断使用。

    :ivar file: 被编译的文件名。
    :ivar success: 编译是否成功。
    :ivar log_output: 编译器输出日志。
    :ivar object_file: 生成的目标 object 文件名。
    :ivar elapsed_seconds: 编译耗时（秒）。
    """
    file: str
    success: bool
    log_output: str
    object_file: str
    elapsed_seconds: float


@dataclass
class CppCompileSummary:
    """一批 C++ 文件编译结果的汇总。

    记录总数量、成功/失败数量、成功率以及每个文件的编译结果明细。

    :ivar total_count: 总文件数。
    :ivar success_count: 成功编译的文件数。
    :ivar failed_count: 编译失败的文件数。
    :ivar success_rate: 成功率（0~1）。
    :ivar results: 各文件编译结果列表。
    """
    total_count: int
    success_count: int
    failed_count: int
    success_rate: float
    results: List[CppFileCompileResult]


class CppCompileStep:
    """Compile generated C++ implementation files and header self-include units."""

    _MAX_LOG_CHARS = 12000

    def __init__(self, timeout_seconds: int = 60):
        """初始化编译步骤。

        :param timeout_seconds: 单个文件编译的超时时间（秒）。
        """
        self.timeout_seconds = timeout_seconds

    def compile_cpp_files(self, result_dir: Path, project: Project) -> CppCompileSummary:
        """编译结果目录中的所有实现文件（.cpp）。

        逐个编译 .cpp 文件，收集失败日志、回写编译结果到 method，并生成
        汇总 JSON 报告与统计信息。

        :param result_dir: 包含待编译 .cpp 文件的结果目录。
        :param project: 对应的 Project 对象，用于回写编译结果。
        :return: 编译汇总结果 CppCompileSummary。
        """
        result_dir = Path(result_dir)
        report_dir = result_dir / "compile_report"
        log_dir = report_dir / "failed_cpp_compile_logs"
        report_dir.mkdir(parents=True, exist_ok=True)
        log_dir.mkdir(parents=True, exist_ok=True)
        self._clear_failed_logs(log_dir)

        cpp_files = [
            file for file in sorted(result_dir.iterdir())
            if file.is_file() and file.suffix == ".cpp" and not file.name.startswith("__compile_header__")
        ]

        results: List[CppFileCompileResult] = []
        for cpp_file in cpp_files:
            result = self._compile_cpp_file(cpp_file, result_dir)
            results.append(result)
            self._write_failed_log(result, log_dir)
            self._write_result_to_methods(project, result)

            if result.success:
                print(f"Compiled {result.file} successfully.")
            else:
                print(f"Failed to compile {result.file}.")

        success_count = sum(1 for result in results if result.success)
        total_count = len(results)
        failed_count = total_count - success_count
        success_rate = success_count / total_count if total_count else 1.0
        summary = CppCompileSummary(
            total_count=total_count,
            success_count=success_count,
            failed_count=failed_count,
            success_rate=success_rate,
            results=results,
        )
        self._write_summary(summary, report_dir)
        print(
            f"C++ compile check: total={total_count}, success={success_count}, "
            f"failed={failed_count}, success_rate={success_rate:.4f}"
        )
        return summary

    def compile_header_files(self, result_dir: Path, project: Project) -> CppCompileSummary:
        """编译结果目录中的所有源头文件（.h/.hpp）。

        为每个头文件构造自包含编译单元并逐个编译，收集失败日志与回写
        编译结果，最终生成头文件编译汇总报告。

        :param result_dir: 包含待编译头文件的结果目录。
        :param project: 对应的 Project 对象，用于回写编译结果。
        :return: 编译汇总结果 CppCompileSummary。
        """
        result_dir = Path(result_dir)
        report_dir = result_dir / "compile_report"
        log_dir = report_dir / "failed_header_compile_logs"
        report_dir.mkdir(parents=True, exist_ok=True)
        log_dir.mkdir(parents=True, exist_ok=True)
        self._clear_failed_logs(log_dir)

        header_files = self._source_header_files(result_dir, project)

        results: List[CppFileCompileResult] = []
        for header_file in header_files:
            result = self._compile_header_file(header_file, result_dir)
            results.append(result)
            self._write_failed_log(result, log_dir)
            self._write_header_result_to_methods(project, result)

            if result.success:
                print(f"Compiled header {result.file} successfully.")
            else:
                print(f"Failed to compile header {result.file}.")

        success_count = sum(1 for result in results if result.success)
        total_count = len(results)
        failed_count = total_count - success_count
        success_rate = success_count / total_count if total_count else 1.0
        summary = CppCompileSummary(
            total_count=total_count,
            success_count=success_count,
            failed_count=failed_count,
            success_rate=success_rate,
            results=results,
        )
        self._write_summary(summary, report_dir, file_name="header_compile_summary.json")
        print(
            f"C++ header compile check: total={total_count}, success={success_count}, "
            f"failed={failed_count}, success_rate={success_rate:.4f}"
        )
        return summary

    def _source_header_files(self, result_dir: Path, project: Project) -> list[Path]:
        """获取结果目录中需要编译的源头文件路径列表。

        仅收集 project 中非生成外部的 header 所对应的、且实际存在于
        结果目录里的 .h/.hpp 文件。

        :param result_dir: 结果目录。
        :param project: 对应的 Project 对象。
        :return: 待编译头文件路径列表。
        """
        header_names = sorted({
            header.get_output_header_name()
            for header in project.headers
            if not header.is_generated_external() and not header.is_manual_stub()
        })
        return [
            result_dir / header_name for header_name in header_names
            if (result_dir / header_name).is_file() and (result_dir / header_name).suffix in {".h", ".hpp"}
        ]

    def _compile_cpp_file(self, cpp_file: Path, result_dir: Path) -> CppFileCompileResult:
        """编译单个 .cpp 文件。

        使用 clang++ 以 -c 方式编译目标文件，捕获输出并处理超时、找不到
        编译器及异常等情况，编译结束后清理临时 object 文件。

        :param cpp_file: 待编译的 .cpp 文件路径。
        :param result_dir: 编译工作目录。
        :return: 该文件的编译结果 CppFileCompileResult。
        """
        obj_file = cpp_file.with_suffix(".o")
        start_time = time.monotonic()
        try:
            proc = subprocess.run(
                [
                    "clang++",
                    "-std=c++17",
                    "-c",
                    "-ferror-limit=5",
                    "-ftemplate-backtrace-limit=5",
                    "-fno-caret-diagnostics",
                    "-fmacro-backtrace-limit=5",
                    cpp_file.name,
                    "-o",
                    obj_file.name,
                ],
                cwd=str(result_dir),
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=self.timeout_seconds,
            )
            success = proc.returncode == 0
            log_output = self._compact_log((proc.stdout or "") + (proc.stderr or ""))
        except subprocess.TimeoutExpired as exc:
            success = False
            log_output = self._compact_log((exc.stdout or "") + (exc.stderr or "") + "\nCompilation timed out.")
        except FileNotFoundError:
            success = False
            log_output = "Compiler (clang++) not found."
        except Exception as exc:
            success = False
            log_output = str(exc)
        finally:
            elapsed_seconds = time.monotonic() - start_time
            if obj_file.exists():
                try:
                    obj_file.unlink()
                except OSError:
                    pass

        return CppFileCompileResult(
            file=cpp_file.name,
            success=success,
            log_output=log_output,
            object_file=obj_file.name,
            elapsed_seconds=round(elapsed_seconds, 4),
        )

    def _compile_header_file(self, header_file: Path, result_dir: Path) -> CppFileCompileResult:
        """通过自包含编译单元编译单个头文件。

        为头文件生成一个仅包含 ``#include`` 该头文件的 .cpp 单元并以 -c
        方式编译，从而验证头文件能否独立编译，最后清理临时文件。

        :param header_file: 待编译的头文件路径。
        :param result_dir: 编译工作目录。
        :return: 该头文件的编译结果 CppFileCompileResult。
        """
        unit_file = result_dir / f"__compile_header__{header_file.stem}.cpp"
        obj_file = result_dir / f"__compile_header__{header_file.stem}.o"
        start_time = time.monotonic()
        try:
            unit_file.write_text(f'#include "{header_file.name}"\n', encoding="utf-8")
            proc = subprocess.run(
                [
                    "clang++",
                    "-std=c++17",
                    "-c",
                    "-ferror-limit=5",
                    "-ftemplate-backtrace-limit=5",
                    "-fno-caret-diagnostics",
                    "-fmacro-backtrace-limit=5",
                    unit_file.name,
                    "-o",
                    obj_file.name,
                ],
                cwd=str(result_dir),
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=self.timeout_seconds,
            )
            success = proc.returncode == 0
            log_output = self._compact_log((proc.stdout or "") + (proc.stderr or ""))
        except subprocess.TimeoutExpired as exc:
            success = False
            log_output = self._compact_log((exc.stdout or "") + (exc.stderr or "") + "\nCompilation timed out.")
        except FileNotFoundError:
            success = False
            log_output = "Compiler (clang++) not found."
        except Exception as exc:
            success = False
            log_output = str(exc)
        finally:
            elapsed_seconds = time.monotonic() - start_time
            for temp_file in (unit_file, obj_file):
                if temp_file.exists():
                    try:
                        temp_file.unlink()
                    except OSError:
                        pass

        return CppFileCompileResult(
            file=header_file.name,
            success=success,
            log_output=log_output,
            object_file=obj_file.name,
            elapsed_seconds=round(elapsed_seconds, 4),
        )

    def _compact_log(self, log_output: str) -> str:
        """压缩编译器日志，限制其长度。

        对超过最大长度的日志，过滤掉非错误的 \"In file included from\" 行，
        若仍超限则截断并追加截断标记。

        :param log_output: 原始编译器日志。
        :return: 压缩后的日志字符串。
        """
        if len(log_output) <= self._MAX_LOG_CHARS:
            return log_output

        lines: List[str] = []
        for line in log_output.splitlines():
            if "In file included from" in line and "error:" not in line:
                continue
            lines.append(line)

        compact = "\n".join(lines)
        if len(compact) > self._MAX_LOG_CHARS:
            compact = compact[: self._MAX_LOG_CHARS] + "\n...[truncated]"
        return compact

    def _clear_failed_logs(self, log_dir: Path) -> None:
        """编译前清理旧的失败日志，避免修复后残留陈旧日志。"""
        for log_file in log_dir.glob("*.log"):
            try:
                log_file.unlink()
            except OSError:
                pass

    def _write_failed_log(self, result: CppFileCompileResult, log_dir: Path) -> None:
        """将编译失败文件的日志写入指定目录。

        :param result: 编译结果对象。
        :param log_dir: 失败日志输出目录。
        """
        if result.success:
            return
        log_path = log_dir / f"{Path(result.file).stem}.log"
        log_path.write_text(result.log_output, encoding="utf-8")

    def _write_summary(self, summary: CppCompileSummary, report_dir: Path, file_name: str = "cpp_compile_summary.json") -> None:
        """将编译汇总结果写为 JSON 报告文件。

        :param summary: 编译汇总对象。
        :param report_dir: 报告输出目录。
        :param file_name: 报告文件名。
        """
        data = {
            "total_count": summary.total_count,
            "success_count": summary.success_count,
            "failed_count": summary.failed_count,
            "success_rate": summary.success_rate,
            "results": [asdict(result) for result in summary.results],
        }
        with open(report_dir / file_name, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _write_result_to_methods(self, project: Project, result: CppFileCompileResult) -> None:
        """将单文件编译结果回写至对应 header 下的 method。

        :param project: 对应的 Project 对象。
        :param result: 编译结果对象。
        """
        header_name = Path(result.file).stem
        for header in project.headers:
            if header.get_output_cpp_name() != result.file and header.key != header_name:
                continue
            for method in header.methods:
                if method.method_body_location != "cpp" and not method.translated_code:
                    continue
                method.compile_unit = result.file
                method.compile_output = "" if result.success else result.log_output
            return

    def _write_header_result_to_methods(self, project: Project, result: CppFileCompileResult) -> None:
        """将头文件编译结果回写至对应 header 下的 method。

        :param project: 对应的 Project 对象。
        :param result: 编译结果对象。
        """
        for header in project.headers:
            if header.get_output_header_name() != result.file:
                continue
            for method in header.methods:
                if method.method_body_location != "header" and not method.implemented_in_header:
                    continue
                method.compile_unit = result.file
                method.compile_output = "" if result.success else result.log_output
            return
