from __future__ import annotations

from pathlib import Path
from typing import List
import subprocess
from graph import Header
from utils.compile_feedback import analyze_compile_feedback, CompileFeedback
from .models import HeaderCompileError, HeaderCompileResult
from .third_party_libraries import ThirdPartyLibraryAvailability


class HeaderCompileStep:
    """通过临时空 cpp 包装文件逐个检查生成 Header 的编译状态。

    职责:
        写出当前项目的 Header 快照，调用 clang++ 检查目标 Header，并将
        当前文件错误、项目依赖错误和项目外错误写回编译报告。

    使用约定:
        返回结果中的 local_compile_errors 只表示当前目标 Header 自身错误；
        项目内其他 Header 的错误通过 CompileFeedback 标记为依赖阻塞。
    """

    def __init__(self, third_party_availability: ThirdPartyLibraryAvailability | None = None):
        """初始化编译步骤。

        参数:
            third_party_availability: 第三方库可用性探测对象，用于为缺失头文件补充反馈；可为 None。
        """
        self.third_party_availability = third_party_availability

    def _to_project_compile_errors(self, issues: list) -> List[HeaderCompileError]:
        """将编译反馈中的项目内 Issue 转换为带定位的结果错误。

        参数：
            issues: 当前 Header 或项目内其他 Header 的规范化 Issue 列表。

        返回：
            List[HeaderCompileError]：保留类型、摘要和文件/行/列位置的错误列表。
        """
        errors: List[HeaderCompileError] = []
        for issue in issues:
            location = issue.location
            errors.append(HeaderCompileError(
                type=issue.type,
                detail=issue.detail,
                file_path=location.file_path,
                line=location.line,
                column=location.column,
            ))
        return errors

    def compile_headers(
        self,
        target_headers: List[Header],
        all_headers: List[Header],
        file_dir: Path,
        round_idx: int = 0,
    ) -> List[HeaderCompileResult]:
        """通过临时空 cpp 包装文件编译每个生成的头文件。

        职责:
            将目标 Header 写出到临时目录，为每个 Header 生成一个仅包含
            #include 的 cpp 文件，用 clang++ 做语法检查，并将编译结果写回
            Header 对象及返回结果列表。

        参数:
            target_headers: 需要编译的 Header 列表。
            all_headers: 全部 Header 列表（用于写出依赖头文件）。
            file_dir: 临时编译工作目录。
            round_idx: 当前轮次编号，用于标记编译报告。

        返回:
            每个目标 Header 对应的编译结果 HeaderCompileResult 列表。
        """
        if not target_headers:
            return []

        file_dir = Path(file_dir)
        file_dir.mkdir(parents=True, exist_ok=True)

        for old_file in file_dir.iterdir():
            try:
                old_file.unlink()
            except OSError:
                pass

        for header in all_headers:
            if header.translated_code:
                header_path = file_dir / header.get_output_header_name()
                header_path.write_text(header.translated_code, encoding="utf-8")

        owned_paths = [
            file_dir / h.get_output_header_name()
            for h in all_headers if h.translated_code
        ]

        results: List[HeaderCompileResult] = []
        for header in target_headers:
            if not header.translated_code:
                results.append(HeaderCompileResult(
                    header=header.translated_class_name,
                    success=False,
                    local_compile_errors=["No translated code."],
                ))
                continue

            cpp_file = file_dir / f"_compile_test_{header.translated_class_name.replace('::', '_')}.cpp"
            include_name = header.get_output_header_name()
            cpp_file.write_text(f'#include "{include_name}"\n', encoding="utf-8")

            try:
                proc = subprocess.run(
                    ["clang++", "-std=c++17", "-fsyntax-only", "-c", str(cpp_file)],
                    capture_output=True,
                    text=True, encoding='utf-8', errors='replace',
                    timeout=60,
                    cwd=str(file_dir),
                )
                compile_output = proc.stderr or proc.stdout or ""
                success = proc.returncode == 0

                if not success:
                    analysis = analyze_compile_feedback(
                        compile_output,
                        file_dir / include_name,
                        owned_paths=owned_paths,
                    )
                    analysis.round = round_idx
                    analysis.header = header.key
                    analysis.success = False
                    header.compile_output = compile_output
                    header.compile_reports = [
                        r for r in header.compile_reports
                        if not (hasattr(r, 'round') and r.round == round_idx)
                    ]
                    header.compile_reports.append(analysis)
                    header.latest_compile_status = "failed"

                    local_errors: List[str] = []
                    for issue in analysis.issues:
                        local_errors.append(
                            f"[{issue.type}] {issue.detail}"
                        )
                        if self.third_party_availability is not None:
                            third_party_feedback = self.third_party_availability.feedback_for_issue(
                                issue.type,
                                issue.detail,
                            )
                            if third_party_feedback:
                                local_errors.append(third_party_feedback)
                    results.append(HeaderCompileResult(
                        header=header.translated_class_name,
                        success=False,
                        local_compile_errors=local_errors,
                        project_compile_errors=self._to_project_compile_errors(
                            [*analysis.issues, *analysis.project_dependency_issues]
                        ),
                    ))
                else:
                    analysis = CompileFeedback()
                    analysis.round = round_idx
                    analysis.header = header.key
                    analysis.success = True
                    analysis.has_local_issues = False
                    analysis.log_output = ""
                    header.compile_reports = [
                        r for r in header.compile_reports
                        if not (hasattr(r, 'round') and r.round == round_idx)
                    ]
                    header.compile_reports.append(analysis)
                    header.compile_output = ""
                    header.latest_compile_status = "success"
                    results.append(HeaderCompileResult(
                        header=header.translated_class_name,
                        success=True,
                    ))
            except subprocess.TimeoutExpired:
                header.latest_compile_status = "timeout"
                results.append(HeaderCompileResult(
                    header=header.translated_class_name,
                    success=False,
                    local_compile_errors=["Compilation timed out."],
                ))
            except FileNotFoundError:
                results.append(HeaderCompileResult(
                    header=header.translated_class_name,
                    success=False,
                    local_compile_errors=["Compiler (clang++) not found."],
                ))
            finally:
                if cpp_file.exists():
                    try:
                        cpp_file.unlink()
                    except OSError:
                        pass

        return results
