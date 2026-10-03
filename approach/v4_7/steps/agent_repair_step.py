from __future__ import annotations

import csv
import json
import re
import shutil
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import List

from v4_7.agent.Agent import CppCompilationAgent
from v4_7.agent.tools import validate_project_after_link
from .cpp_compile_step import CppCompileStep, CppFileCompileResult


@dataclass
class AgentRepairFileResult:
    """单个文件智能体修复结果的数据载体。

    记录某个失败文件在修复过程中的最终状态、尝试次数及相关信息。

    :ivar file: 被修复的文件名。
    :ivar status: 修复状态（如 success/error/unknown）。
    :ivar attempts: 尝试修复的次数。
    :ivar history_file: 修复历史文件的相对路径。
    :ivar error: 修复过程中的错误信息。
    """
    file: str
    status: str
    attempts: int
    history_file: str
    error: str = ""


@dataclass
class AgentRepairSummary:
    """一批文件智能体修复结果的汇总。

    记录失败文件总数、已修复与仍失败的数量以及每个文件的修复结果明细。

    :ivar total_failed_files: 参与修复的失败文件总数。
    :ivar repaired_count: 修复成功的文件数。
    :ivar failed_count: 修复失败的文件数。
    :ivar results: 各文件修复结果列表。
    :ivar tool_call_count: 当前项目 repair 阶段实际执行的工具调用总数。
    """
    total_failed_files: int
    repaired_count: int
    failed_count: int
    results: List[AgentRepairFileResult]
    tool_call_count: int = 0


class AgentRepairStep:
    """Run the C++ compilation repair agent against failed .cpp files and source headers."""

    def __init__(
        self,
        compile_step: CppCompileStep,
        link_mode: bool = True,
        test_suites: tuple[str, ...] = ("base",),
    ):
        """初始化修复步骤。

        :param compile_step: 用于编译检查的 CppCompileStep 实例。
        :param link_mode: 是否启用链接级检查与修复。
        :param test_suites: 链接成功后按顺序执行的功能测试套件。
        """
        self.compile_step = compile_step
        self.link_mode = link_mode
        if not test_suites:
            raise ValueError("At least one repair test suite is required")
        unsupported = set(test_suites) - {"base", "additional"}
        if unsupported:
            raise ValueError(f"Unsupported repair test suites: {sorted(unsupported)}")
        self.test_suites = tuple(dict.fromkeys(test_suites))

    def run_repair(
        self,
        ai_name: str,
        project_name: str,
        result_dir: Path,
        review_dir: Path,
        max_attempts: int = 10,
        apply_repair: bool = False,
        compile_rounds: int | None = None,
        link_rounds: int = 2,
        max_tool_calls: int | None = None,
    ) -> AgentRepairSummary:
        """驱动 C++ 编译修复智能体对失败文件进行修复。

        准备回顾目录、加载失败文件与初始错误信息；在链接模式下执行整体
        链接检查判定是否增加链接修复目标；随后对每个失败文件运行智能体
        修复并做最终编译校验，可选的以两阶段模式先 -c 修复再统一链接修复。
        最后汇总结果并写入报告与 CSV，若 apply_repair 为真则将修复结果
        回写至结果目录。

        :param ai_name: AI 名称。
        :param project_name: 项目名称。
        :param result_dir: 包含失败产物的结果目录。
        :param review_dir: 用于修复的回顾目录。
        :param max_attempts: 每个文件的最大修复尝试次数。
        :param apply_repair: 是否将修复结果应用回结果目录。
        :param compile_rounds: 两阶段模式下 -c 修复的轮数；为 None 时不启用两阶段。
        :param link_rounds: 两阶段模式下链接修复的轮数。
        :return: 修复汇总结果 AgentRepairSummary。
        """
        result_dir = Path(result_dir)
        review_dir = Path(review_dir)
        # manual_stub readonly: stub files are never repair targets and must not be edited.
        # Convention: stub header is <class_name>.h, optional impl is <class_name>.cpp.
        from path_config import cfg_cpp_stub_dirs
        from .manual_stub_loader import load_stub_definitions
        stub_names = load_stub_definitions(cfg_cpp_stub_dirs(project_name))
        self.readonly_files: set[str] = set()
        for stub_class_name, stub_def in stub_names.items():
            self.readonly_files.add(f"{stub_class_name}.h")
            if stub_def.cpp_code.strip():
                self.readonly_files.add(f"{stub_class_name}.cpp")

        self._prepare_review_dir(result_dir, review_dir)

        initial_errors = self._load_initial_errors(result_dir)
        two_phase = self.link_mode and compile_rounds is not None

        history_dir = review_dir / "repair_history"
        history_dir.mkdir(parents=True, exist_ok=True)

        results: List[AgentRepairFileResult] = []
        tool_call_counter = {"count": 0}
        attempted_files: set[str] = set()

        # 每修复一个根因后重新扫描当前产物，避免继续处理已经被连带修复的
        # 陈旧失败项。Header 及诊断明确指向的依赖文件始终排在 CPP 前面。
        while True:
            failed_files, current_errors = self._scan_current_compile_failures(review_dir)
            if not failed_files and self.link_mode and not two_phase:
                validation_ok, validation_log = validate_project_after_link(
                    project_name,
                    review_dir,
                    compile_timeout=self.compile_step.timeout_seconds,
                    test_suites=getattr(self, "test_suites", ("base",)),
                )
                if validation_ok:
                    break
                validation_target = self._pick_validation_repair_target(
                    review_dir,
                    project_name,
                    validation_log,
                    list(attempted_files),
                )
                if validation_target is None:
                    print("Project validation still fails but no untried repair target remains.")
                    break
                failed_files = [validation_target]
                current_errors[validation_target] = validation_log

            pending_files = [
                file_name for file_name in failed_files
                if file_name not in attempted_files
            ]
            if not pending_files:
                break

            if max_tool_calls is not None and tool_call_counter["count"] >= max_tool_calls:
                print(f"Repair tool-call budget exhausted at {max_tool_calls}; remaining files skipped.")
                for skipped_file in pending_files:
                    results.append(AgentRepairFileResult(
                        file=skipped_file,
                        status="max_tool_calls_reached",
                        attempts=0,
                        history_file="",
                        error=f"Project tool-call budget exhausted at {max_tool_calls}",
                    ))
                break

            file_name = pending_files[0]
            attempted_files.add(file_name)
            print(f"========== Agent repair: {file_name} ==========")
            history_file = history_dir / f"{Path(file_name).stem}.history.json"
            current_error = current_errors.get(file_name, "").strip()
            original_error = initial_errors.get(file_name, "").strip()
            initial_error_log = "\n\n".join(
                part for part in (original_error, current_error) if part
            )
            try:
                agent = CppCompilationAgent(
                    ai_name=ai_name,
                    project_name=project_name,
                    file_path=review_dir / file_name,
                    work_dir=review_dir,
                    initial_error_log=initial_error_log,
                    readonly_files=self.readonly_files,
                    trace_path=result_dir / "llm_trace.jsonl",
                    history_path=history_file,
                    compile_timeout=self.compile_step.timeout_seconds,
                    link_mode=False if two_phase else self.link_mode,
                    test_suites=getattr(self, "test_suites", ("base",)),
                )
                result = agent.run(
                    max_attempts=compile_rounds if two_phase else max_attempts,
                    max_tool_calls=max_tool_calls,
                    tool_call_counter=tool_call_counter,
                )
                status = result.get("status", "unknown")
                attempts = int(result.get("attempts", 0))
                error = str(result.get("error", ""))
                refreshed_failures, refreshed_errors = self._scan_current_compile_failures(review_dir)
                target_resolved = file_name not in refreshed_failures
                if target_resolved and self.link_mode and not two_phase and not refreshed_failures:
                    validation_ok, validation_log = validate_project_after_link(
                        project_name,
                        review_dir,
                        compile_timeout=self.compile_step.timeout_seconds,
                        test_suites=getattr(self, "test_suites", ("base",)),
                    )
                    if not validation_ok:
                        next_target = self._pick_validation_repair_target(
                            review_dir,
                            project_name,
                            validation_log,
                            [],
                        )
                        if next_target == file_name:
                            target_resolved = False
                            refreshed_errors[file_name] = validation_log

                if target_resolved:
                    status = "success"
                    error = ""
                else:
                    if status == "success":
                        status = "validation_failed"
                    if not error:
                        error = refreshed_errors.get(file_name, current_error)
            except Exception as exc:
                status = "error"
                attempts = 0
                error = str(exc)

            results.append(AgentRepairFileResult(
                file=file_name,
                status=status,
                attempts=attempts,
                history_file=str(history_file.relative_to(review_dir)),
                error=error,
            ))

        if not results and not two_phase:
            print("No failed C++/header files found for repair.")

        if two_phase and link_rounds > 0:
            link_entry = self._run_link_phase(
                ai_name,
                project_name,
                result_dir,
                review_dir,
                history_dir,
                link_rounds,
                max_tool_calls,
                tool_call_counter,
            )
            if link_entry is not None:
                results.append(link_entry)

        repaired_count = sum(1 for result in results if result.status == "success")
        failed_count = len(results) - repaired_count
        summary = AgentRepairSummary(
            len(results),
            repaired_count,
            failed_count,
            results,
            tool_call_count=tool_call_counter["count"],
        )
        self._write_summary(summary, review_dir)
        self._write_stats_csv(summary, review_dir)

        if apply_repair:
            self._apply_review_to_result(review_dir, result_dir)

        return summary

    def _prepare_review_dir(self, result_dir: Path, review_dir: Path) -> None:
        """准备回顾目录，将结果目录内容复制过去。

        若回顾目录已存在则先删除，复制时忽略编译报告、映射及 object 文件。

        :param result_dir: 结果目录。
        :param review_dir: 回顾目录。
        """
        if review_dir.exists():
            shutil.rmtree(review_dir)
        ignore = shutil.ignore_patterns("compile_report", "mapping", "*.o")
        shutil.copytree(result_dir, review_dir, ignore=ignore)

    def _scan_current_compile_failures(
        self,
        review_dir: Path,
    ) -> tuple[List[str], dict[str, str]]:
        """重新编译当前评审目录并返回按根因优先排列的失败文件。

        参数:
            review_dir: 当前 repair 工作目录。

        返回:
            ``(失败文件列表, 文件到诊断日志的映射)``。诊断明确指向的
            Header 优先，其次为其他 Header、明确指向的 CPP 和其他 CPP。
        """
        review_dir = Path(review_dir)
        readonly = getattr(self, "readonly_files", set())
        source_files = [
            file_path
            for file_path in review_dir.iterdir()
            if file_path.is_file()
            and file_path.suffix in {".h", ".hpp", ".cpp"}
            and not file_path.name.startswith("__compile_header__")
            and file_path.name not in readonly
        ]
        source_files.sort(
            key=lambda path: (
                0 if path.suffix in {".h", ".hpp"} else 1,
                path.name.casefold(),
            )
        )

        failures: List[str] = []
        errors: dict[str, str] = {}
        for file_path in source_files:
            result = self._compile_file_c_only(file_path, review_dir)
            if result.success:
                continue
            failures.append(file_path.name)
            errors[file_path.name] = result.log_output

        prioritized = self._prioritize_compile_failures(review_dir, failures, errors)
        for candidate in prioritized:
            if candidate in errors:
                continue
            related_logs = [
                log_output
                for log_output in errors.values()
                if candidate in log_output
            ]
            if related_logs:
                errors[candidate] = "\n\n".join(related_logs)
        return prioritized, errors

    def _prioritize_compile_failures(
        self,
        review_dir: Path,
        failures: List[str],
        errors: dict[str, str],
    ) -> List[str]:
        """依据编译器首个错误位置和文件类型排列 repair 候选。

        参数:
            review_dir: repair 工作目录。
            failures: 直接编译失败的文件名。
            errors: 各失败文件的诊断日志。

        返回:
            去重后的候选文件列表，依赖根因 Header 优先。
        """
        location_pattern = re.compile(
            r"(?P<file>[A-Za-z0-9_.$-]+\.(?:cpp|cc|cxx|h|hpp))"
            r":\d+(?::\d+)?[^\n]*error:"
        )
        referenced: List[str] = []
        for failed_file in failures:
            for match in location_pattern.finditer(errors.get(failed_file, "")):
                candidate = match.group("file")
                if (review_dir / candidate).is_file() and candidate not in referenced:
                    referenced.append(candidate)
                break

        def ordered(candidates: List[str], header: bool) -> List[str]:
            """筛选并稳定排列指定类型的候选文件。

            参数:
                candidates: 保持原顺序的候选文件名。
                header: 为 True 时保留头文件，否则保留实现文件。

            返回:
                类型匹配的候选文件名列表。
            """
            return [
                candidate
                for candidate in candidates
                if (Path(candidate).suffix in {".h", ".hpp"}) == header
            ]

        priority = [
            *ordered(referenced, True),
            *ordered(failures, True),
            *ordered(referenced, False),
            *ordered(failures, False),
        ]
        return list(dict.fromkeys(priority))

    def _load_failed_files(self, result_dir: Path) -> List[str]:
        """加载所有编译失败的文件名列表。

        :param result_dir: 结果目录。
        :return: 失败文件名（.cpp/.h/.hpp）列表。
        """
        failed_files = self._load_failed_header_files(result_dir)
        failed_files.extend(self._load_failed_cpp_files(result_dir))
        return failed_files

    def _load_failed_cpp_files(self, result_dir: Path) -> List[str]:
        """从编译报告中加载失败的 .cpp 文件列表。

        :param result_dir: 结果目录。
        :return: 失败 .cpp 文件名列表。
        """
        summary_path = result_dir / "compile_report" / "cpp_compile_summary.json"
        if not summary_path.exists():
            return []
        data = json.loads(summary_path.read_text(encoding="utf-8"))
        return [
            item["file"] for item in data.get("results", [])
            if item.get("file", "").endswith(".cpp") and not item.get("success", False)
        ]

    def _load_failed_header_files(self, result_dir: Path) -> List[str]:
        """从编译报告中加载失败的头文件列表。

        :param result_dir: 结果目录。
        :return: 失败 .h/.hpp 文件名列表。
        """
        summary_path = result_dir / "compile_report" / "header_compile_summary.json"
        if not summary_path.exists():
            return []
        data = json.loads(summary_path.read_text(encoding="utf-8"))
        return [
            item["file"] for item in data.get("results", [])
            if item.get("file", "").endswith((".h", ".hpp")) and not item.get("success", False)
        ]

    def _load_initial_errors(self, result_dir: Path) -> dict[str, str]:
        """加载各失败文件的初始编译错误信息。

        :param result_dir: 结果目录。
        :return: 文件名为键、初始错误日志为值的字典。
        """
        errors: dict[str, str] = {}
        for summary_name in ("cpp_compile_summary.json", "header_compile_summary.json"):
            summary_path = result_dir / "compile_report" / summary_name
            if not summary_path.exists():
                continue
            data = json.loads(summary_path.read_text(encoding="utf-8"))
            errors.update({
                item.get("file", ""): item.get("log_output", "")
                for item in data.get("results", [])
                if item.get("file")
            })
        return errors

    def _run_link_phase(
        self,
        ai_name: str,
        project_name: str,
        result_dir: Path,
        review_dir: Path,
        history_dir: Path,
        link_rounds: int,
        max_tool_calls: int | None,
        tool_call_counter: dict[str, int],
    ) -> AgentRepairFileResult | None:
        """在共享项目预算内对整工程执行指定轮数的链接及测试修复。"""
        validation_ok, validation_log = validate_project_after_link(
            project_name,
            review_dir,
            compile_timeout=self.compile_step.timeout_seconds,
            test_suites=getattr(self, "test_suites", ("base",)),
        )
        if validation_ok:
            print("Project validation phase: link and available tests already succeed, skipping.")
            return None

        target = self._pick_validation_repair_target(
            review_dir,
            project_name,
            validation_log,
            [],
        )
        if target is None:
            return None

        if max_tool_calls is not None and tool_call_counter["count"] >= max_tool_calls:
            print(f"Link repair skipped: tool-call budget exhausted at {max_tool_calls}.")
            return AgentRepairFileResult(
                file=target,
                status="max_tool_calls_reached",
                attempts=0,
                history_file="",
                error=f"Project tool-call budget exhausted at {max_tool_calls}",
            )

        print(f"========== Link repair ({link_rounds} rounds): {target} ==========")
        history_file = history_dir / f"{Path(target).stem}.link.history.json"
        try:
            agent = CppCompilationAgent(
                ai_name=ai_name,
                project_name=project_name,
                file_path=review_dir / target,
                work_dir=review_dir,
                initial_error_log=validation_log,
                readonly_files=self.readonly_files,
                trace_path=result_dir / "llm_trace.jsonl",
                history_path=history_file,
                compile_timeout=self.compile_step.timeout_seconds,
                link_mode=True,
                test_suites=getattr(self, "test_suites", ("base",)),
            )
            result = agent.run(
                max_attempts=link_rounds,
                max_tool_calls=max_tool_calls,
                tool_call_counter=tool_call_counter,
            )
            status = result.get("status", "unknown")
            attempts = int(result.get("attempts", 0))
            error = str(result.get("error", ""))
            validation_ok, validation_log = validate_project_after_link(
                project_name,
                review_dir,
                compile_timeout=self.compile_step.timeout_seconds,
                test_suites=getattr(self, "test_suites", ("base",)),
            )
            if validation_ok:
                status = "success"
                error = ""
            else:
                if status == "success":
                    status = "validation_failed"
                if not error:
                    error = validation_log
        except Exception as exc:
            status = "error"
            attempts = 0
            error = str(exc)

        return AgentRepairFileResult(
            file=target,
            status=status,
            attempts=attempts,
            history_file=str(history_file.relative_to(review_dir)),
            error=error,
        )

    def _compile_file_c_only(self, file_path: Path, work_dir: Path):
        """始终以 -c 单文件方式检查（头文件用自包含单元）。"""
        if file_path.suffix in {".h", ".hpp"}:
            return self.compile_step._compile_header_file(file_path, work_dir)
        return self.compile_step._compile_cpp_file(file_path, work_dir)

    def _compile_target_file(self, file_path: Path, work_dir: Path, project_name: str):
        """按目标文件类型执行最终编译校验。

        链接模式下无论目标是实现还是头文件，都执行整体链接和功能测试；
        非链接模式下，头文件走自包含单元编译，其余文件做单文件 -c 编译。

        :param file_path: 待校验的目标文件路径。
        :param work_dir: 编译工作目录。
        :param project_name: 当前翻译项目名称。
        :return: 编译结果 CppFileCompileResult。
        """
        if self.link_mode:
            success, log_output = validate_project_after_link(
                project_name,
                work_dir,
                compile_timeout=self.compile_step.timeout_seconds,
                test_suites=getattr(self, "test_suites", ("base",)),
            )
            return CppFileCompileResult(
                file=file_path.name,
                success=success,
                log_output=log_output,
                object_file="",
                elapsed_seconds=0.0,
            )
        if file_path.suffix in {".h", ".hpp"}:
            return self.compile_step._compile_header_file(file_path, work_dir)
        return self.compile_step._compile_cpp_file(file_path, work_dir)

    def _pick_validation_repair_target(
        self,
        review_dir: Path,
        project_name: str,
        validation_log: str,
        failed_files: List[str],
    ) -> str | None:
        """为链接或功能测试失败选择 repair Agent 的入口文件。

        功能测试优先选择诊断区 ``error:`` 行明确带源码行号的实现或头文件，
        再考虑 warning 和其他源码位置，以免前置警告或断言所在的测试入口
        掩盖真正的失败文件；没有明确位置时回退到项目同名实现。链接错误
        仍沿用符号提及频次策略。

        :param review_dir: 修复工作目录。
        :param project_name: 当前翻译项目名称。
        :param validation_log: 链接或功能测试反馈。
        :param failed_files: 已进入修复队列的文件名。
        :return: 入口文件名；没有实现文件时返回 None。
        """
        project_entry = review_dir / f"{project_name}.cpp"
        if "[functional test" in validation_log:
            # 只扫描附加只读测试源码之前的诊断，避免源码中的类型名干扰入口选择。
            diagnostic_log = validation_log.split(
                "--- functional test source", 1
            )[0]
            location_pattern = re.compile(
                r"(?P<file>[A-Za-z0-9_.$-]+\.(?:cpp|cc|cxx|h|hpp))"
                r":\d+(?::\d+)?"
            )
            diagnostic_lines = diagnostic_log.splitlines()
            # 编译器可能先打印无关 warning，必须优先跟随真正的 error 位置。
            for severity in ("error:", "warning:", None):
                for line in diagnostic_lines:
                    if severity is not None and severity not in line:
                        continue
                    match = location_pattern.search(line)
                    if match is None:
                        continue
                    candidate = match.group("file")
                    if candidate not in failed_files and (review_dir / candidate).is_file():
                        return candidate
            if project_entry.is_file() and project_entry.name not in failed_files:
                return project_entry.name
        return self._pick_link_repair_target(review_dir, validation_log, failed_files)

    def _pick_link_repair_target(self, review_dir: Path, link_log: str, failed_files: List[str]) -> str | None:
        """选择一个 .cpp 作为链接修复的入口文件：优先选链接日志中提及最多的文件。"""
        cpp_files = sorted(
            f.name for f in review_dir.iterdir()
            if f.is_file() and f.suffix == ".cpp" and not f.name.startswith("__compile_header__")
        )
        available_files = [name for name in cpp_files if name not in failed_files]
        if not available_files:
            return None

        best: str | None = None
        best_count = 0
        for name in available_files:
            stem = Path(name).stem
            count = link_log.count(stem)
            if count > best_count:
                best = name
                best_count = count
        return best or available_files[0]

    def _write_summary(self, summary: AgentRepairSummary, review_dir: Path) -> None:
        """将修复汇总结果写为 JSON 报告文件。

        :param summary: 修复汇总对象。
        :param review_dir: 回顾目录。
        """
        data = {
            "total_failed_files": summary.total_failed_files,
            "repaired_count": summary.repaired_count,
            "failed_count": summary.failed_count,
            "tool_call_count": summary.tool_call_count,
            "repair_order": [result.file for result in summary.results],
            "results": [asdict(result) for result in summary.results],
        }
        with open(review_dir / "repair_summary.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _write_stats_csv(self, summary: AgentRepairSummary, review_dir: Path) -> None:
        """将修复统计信息写为 CSV 文件。

        :param summary: 修复汇总对象。
        :param review_dir: 回顾目录。
        """
        with open(review_dir / "compilation_stats.csv", "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["File Name", "Compilation Attempts", "Status"])
            for result in summary.results:
                writer.writerow([result.file, result.attempts, result.status])

    def _apply_review_to_result(self, review_dir: Path, result_dir: Path) -> None:
        """将回顾目录中的修复结果回写至结果目录。

        :param review_dir: 回顾目录。
        :param result_dir: 结果目录。
        """
        for file in review_dir.iterdir():
            if file.is_file() and file.suffix in {".h", ".hpp", ".cpp"}:
                shutil.copy2(file, result_dir / file.name)
