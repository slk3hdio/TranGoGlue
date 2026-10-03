from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import List

from eveluation.visualization.header_iteration_charts import generate_header_iteration_outputs
from graph import Header, Project
from path_config import cfg_graph_dir_path, cfg_translate_result_dir_path, cfg_run_graph_dir, cfg_run_result_dir
from utils.Generator import Generator

from . import version
from .agent_repair_step import AgentRepairStep
from .bounded_file_generator import BoundedFileGenerator
from .cpp_compile_step import CppCompileStep
from .step01_graph_build import GraphBuildStep
from .method_translation import MethodMappingStep, MethodStateManager, MethodTranslationStep, extract_external_methods
from .header_translation.models import HeaderBatchRecord, HeaderCompileResult
from .header_translation.batch_grouping import group_headers
from .header_translation.translation_step import HeaderTranslationStep
from .header_translation.compile_step import HeaderCompileStep
from .header_translation.iteration_report import write_iteration_report, remove_isolated_generated_headers
from .header_translation.third_party_libraries import ThirdPartyLibraryAvailability


class TranslationPipeline:
    """v4_7 Java-to-C++ 翻译流水线。

    职责：
        编排图构建、Header 迭代翻译、方法翻译、文件生成和修复步骤，
        并根据带文件定位的编译错误决定 Header batch 是否需要继续处理。

    使用约定：
        通过 run_header_translation 等公开方法执行对应阶段；Header batch
        只有在存在本文件错误或错误指向同 batch 其他 Header 时才继续翻译。
    """

    def __init__(
        self,
        generator: Generator,
        max_header_rounds: int = 10,
        header_batch_size: int = 1,
        cpp_compile_timeout: int = 60,
        header_translation_mode: str = "batched_iterative",
        method_translation_mode: str = "contextual",
        header_grouping_strategy: str = "dependency",
        header_grouping_seed: int | None = None,
        repair_test_suites: tuple[str, ...] = ("base",),
        mapping_generator: Generator | None = None,
    ):
        """初始化流水线，并配置翻译消融模式与 repair 测试套件。

        参数:
            generator: 全流程共享的模型生成器。
            max_header_rounds: Header 最大迭代轮数。
            header_batch_size: Header 批大小。
            cpp_compile_timeout: C++ 单次编译超时秒数。
            header_translation_mode: Header 翻译模式。
            method_translation_mode: 方法翻译模式。
            header_grouping_strategy: Header 分组策略。
            header_grouping_seed: 随机分组种子。
            repair_test_suites: repair 链接成功后按顺序执行的测试套件。
            mapping_generator: 方法映射专用的模型生成器；为 None 时与主流程
                共用 generator。方法映射属于工程辅助环节而非评测内容，
                可用更强模型独立调用。
        """
        if header_translation_mode not in {"batched_iterative", "per_file_one_shot"}:
            raise ValueError(f"Unsupported header translation mode: {header_translation_mode}")
        if header_grouping_strategy not in {"dependency", "random"}:
            raise ValueError(f"Unsupported header grouping strategy: {header_grouping_strategy}")
        self.generator = generator
        self.max_header_rounds = max_header_rounds
        self.header_batch_size = max(1, header_batch_size)
        self.header_translation_mode = header_translation_mode
        self.method_translation_mode = method_translation_mode
        self.header_grouping_strategy = header_grouping_strategy
        self.header_grouping_seed = header_grouping_seed
        self.third_party_availability = ThirdPartyLibraryAvailability()
        self.graph_build_step = GraphBuildStep()
        self.header_translation_step = HeaderTranslationStep(
            generator,
            self.header_batch_size,
            third_party_availability=self.third_party_availability,
        )
        self.header_compile_step = HeaderCompileStep(self.third_party_availability)
        self.method_mapping_step = MethodMappingStep(mapping_generator or generator)
        self.method_translation_step = MethodTranslationStep(generator, translation_mode=method_translation_mode)
        self.method_state_manager = MethodStateManager()
        self.cpp_file_generation_step = BoundedFileGenerator()
        self.cpp_compile_step = CppCompileStep(timeout_seconds=cpp_compile_timeout)
        self.agent_repair_step = AgentRepairStep(
            self.cpp_compile_step,
            test_suites=repair_test_suites,
        )

    @staticmethod
    def _diagnostic_file_name(file_path: str) -> str:
        """提取编译诊断路径中的文件名并统一大小写。

        参数：
            file_path: 编译器报告的绝对路径、相对路径或裸文件名。

        返回：
            str：统一分隔符并 casefold 后的文件名；空路径返回空字符串。
        """
        normalized = str(file_path or "").replace("\\", "/").rstrip("/")
        return normalized.rsplit("/", 1)[-1].casefold() if normalized else ""

    def _batch_has_cross_header_errors(
        self,
        compile_results: List[HeaderCompileResult],
        batch: List[Header],
        compile_dir: Path | None = None,
    ) -> bool:
        """判断项目内错误是否定位到同 batch 的另一个 Header。

        参数：
            compile_results: 当前 batch 各 Header 的预编译结果。
            batch: 当前准备遍历的 Header 列表。
            compile_dir: Header 实际写出目录；用于解析相对诊断路径，可为 None。

        返回：
            bool：任一错误定位到同 batch 的其他 Header 时返回 True。
        """
        output_path_by_header = {
            header.translated_class_name.casefold(): self._normalize_diagnostic_path(
                (Path(compile_dir) / header.get_output_header_name())
                if compile_dir is not None else header.get_output_header_name()
            )
            for header in batch
        }
        batch_output_paths = set(output_path_by_header.values())
        batch_output_names = {
            self._diagnostic_file_name(header.get_output_header_name())
            for header in batch
        }

        def matches_batch_header(file_path: str, current_path: str) -> bool:
            """判断诊断路径是否精确指向 batch 内另一个 Header。"""
            raw_path = str(file_path or "")
            if not raw_path:
                return False
            normalized_path = self._normalize_diagnostic_path(raw_path, compile_dir)
            if normalized_path in batch_output_paths:
                return normalized_path != current_path
            # clang 在部分诊断中只输出文件名，此时只能按文件名兼容降级匹配。
            if len(raw_path.replace("\\", "/").split("/")) == 1:
                error_name = self._diagnostic_file_name(raw_path)
                current_name = self._diagnostic_file_name(current_path)
                return error_name in batch_output_names and error_name != current_name
            return False

        for result in compile_results:
            current_output_path = output_path_by_header.get(result.header.casefold(), "")
            for error in result.project_compile_errors:
                if matches_batch_header(error.file_path, current_output_path):
                    return True
        return False

    @staticmethod
    def _failed_headers_from_compile_results(
        headers: List[Header],
        compile_results: List[HeaderCompileResult],
    ) -> List[Header]:
        """从一轮全量编译结果中筛选下一轮仍需处理的 Header。

        参数：
            headers: 项目内全部 Header，保持项目原有顺序。
            compile_results: 本轮对全部 Header 的编译结果。

        返回：
            List[Header]：编译失败或未成功的 Header；成功 Header 不会进入下一轮
            target_headers，但仍保留在 all_headers 中供依赖解析和编译使用。
        """
        result_by_header = {result.header: result for result in compile_results}
        failed_headers: List[Header] = []
        for header in headers:
            # 手写桩是已知条件，无论编译结果如何都不进入翻译迭代
            if header.is_manual_stub():
                continue
            result = result_by_header.get(header.translated_class_name)
            if result is None or not result.success:
                failed_headers.append(header)
        return failed_headers

    @staticmethod
    def _normalize_diagnostic_path(file_path: str | Path, base_dir: Path | None = None) -> str:
        """规范化诊断文件路径，统一分隔符、大小写和相对目录。

        参数：
            file_path: 编译器报告路径或项目输出文件路径。
            base_dir: 相对路径的解析基准目录，可为 None。

        返回：
            str：用于路径比较的 casefold 规范化路径。
        """
        path = Path(str(file_path).replace("\\", "/"))
        if base_dir is not None and not path.is_absolute():
            path = Path(base_dir) / path
        try:
            path = path.resolve()
        except OSError:
            pass
        return str(path).replace("\\", "/").casefold().rstrip("/")

    def run_header_translation(
        self,
        ai_name: str,
        project_name: str,
        force_rebuild: bool = False,
        run_id: str = "",
        allow_failures: bool = False,
    ) -> List[HeaderBatchRecord]:
        """执行 header 翻译；one-shot 模式只生成一次并跳过反馈修复轮次。"""
        self.generator.set_trace_stage("header_translation")
        project = self.graph_build_step.build_graph(ai_name, project_name, force_rebuild=force_rebuild, run_id=run_id)
        graph_dir = cfg_graph_dir_path(ai_name, project_name, version) if not run_id else cfg_run_graph_dir(ai_name, project_name, version, run_id)
        result_dir = cfg_translate_result_dir_path(ai_name, project_name, version) if not run_id else cfg_run_result_dir(ai_name, project_name, version, run_id)
        result_dir.mkdir(parents=True, exist_ok=True)

        compile_dir = result_dir / "compile"
        compile_dir.mkdir(parents=True, exist_ok=True)

        self.third_party_availability.probe(compile_dir)
        self.third_party_availability.print_summary()

        if self.header_translation_mode == "per_file_one_shot":
            print("========== Header per-file one-shot translation ==========")
            translated = self.header_translation_step.translate_per_file_one_shot(project, project.headers)
            records = [
                {
                    "round_idx": 1,
                    "batch_headers": [header.key],
                    "add_patches": add_patches,
                    "modify_patches": modify_patches,
                    "compile_results": [],
                    "feedback_blocks": {},
                }
                for header, add_patches, modify_patches in translated
            ]
            compile_results = self.header_compile_step.compile_headers(
                project.headers, project.headers, compile_dir, round_idx=1
            )
            compile_by_header = {result.header: result for result in compile_results}
            for record in records:
                record["compile_results"] = [compile_by_header[record["batch_headers"][0]]]
            remove_isolated_generated_headers(project)
            Project.save(project, graph_dir)
            write_iteration_report(
                project, records, result_dir, 1, 1,
                mode="per_file_one_shot",
            )
            self._refresh_header_iteration_visualization(ai_name, project_name, graph_dir, result_dir)
            if not all(result.success for result in compile_results):
                failed_headers = [result.header for result in compile_results if not result.success]
                self._write_header_failure_summary(project, result_dir, failed_headers)
                if not allow_failures:
                    raise RuntimeError(f"One-shot header compilation failed: {failed_headers}")
            print(f"Header one-shot translation completed: {len(translated)} files")
            return records

        all_batch_records: List[HeaderBatchRecord] = []
        # 手写桩不参与翻译迭代
        target_headers = [h for h in project.headers if not h.is_manual_stub()]
        for round_idx in range(1, self.max_header_rounds + 1):
            print(f"========== Header iteration round {round_idx}/{self.max_header_rounds} ==========")

            # 每轮使用不同但可复现的种子，避免失败 Header 在后续轮次保持固定排列。
            round_seed = (
                self.header_grouping_seed + round_idx
                if self.header_grouping_seed is not None else None
            )
            batches = group_headers(
                target_headers,
                project.headers,
                self.header_batch_size,
                strategy=self.header_grouping_strategy,
                random_seed=round_seed,
            )

            round_records: List[HeaderBatchRecord] = []
            any_batch_translated = False
            for batch_idx, batch in enumerate(batches):
                batch_header_names = [h.key for h in batch]

                pre_compile_results: List[HeaderCompileResult] = []
                if round_idx > 1:
                    pre_compile_results = self.header_compile_step.compile_headers(
                        batch, project.headers, compile_dir, round_idx=round_idx
                    )
                    has_local_errors = any(cr.local_compile_errors for cr in pre_compile_results)
                    has_cross_header_errors = self._batch_has_cross_header_errors(
                        pre_compile_results,
                        batch,
                        compile_dir,
                    )
                    if not has_local_errors and not has_cross_header_errors:
                        print(
                            f"  Batch {batch_idx}: no local errors or errors pointing "
                            "to another header in this batch, skipped."
                        )
                        continue

                    failed_in_batch = [cr.header for cr in pre_compile_results if not cr.success]
                    if has_cross_header_errors and not has_local_errors:
                        print(
                            f"  Batch {batch_idx}: project errors point to another header "
                            "in this batch, translating..."
                        )
                    else:
                        print(
                            f"  Batch {batch_idx}: {len(failed_in_batch)}/{len(batch)} "
                            "headers failed with actionable batch errors, translating..."
                        )

                add_patches, modify_patches, feedback_blocks = self.header_translation_step.translate_batch(
                    project, batch, round_idx, batch_idx
                )
                any_batch_translated = True

                record: HeaderBatchRecord = {
                    "round_idx": round_idx,
                    "batch_headers": batch_header_names,
                    "add_patches": add_patches,
                    "modify_patches": modify_patches,
                    "compile_results": pre_compile_results,
                    "feedback_blocks": feedback_blocks,
                }
                round_records.append(record)

            if round_idx > 1 and not any_batch_translated:
                print("  No batches had actionable local or cross-header errors. Complete.")
                all_batch_records.extend(round_records)
                break

            round_compile_results = self.header_compile_step.compile_headers(
                project.headers, project.headers, compile_dir, round_idx=round_idx
            )
            remove_isolated_generated_headers(project)
            active_header_names = {
                header.translated_class_name for header in project.headers
                if not header.is_manual_stub()
            }
            active_compile_results = [
                result for result in round_compile_results
                if result.header in active_header_names
            ]
            target_headers = self._failed_headers_from_compile_results(
                project.headers,
                active_compile_results,
            )

            all_batch_records.extend(round_records)
            Project.save(project, graph_dir)
            print(f"  Saved graph to {graph_dir}")
            write_iteration_report(project, all_batch_records, result_dir, self.max_header_rounds, self.header_batch_size)
            self._refresh_header_iteration_visualization(ai_name, project_name, graph_dir, result_dir)

            if all(cr.success for cr in active_compile_results):
                print("  All headers compile OK, translation complete.")
                break

            succeeded = sum(1 for cr in active_compile_results if cr.success)
            failed = len(active_compile_results) - succeeded
            print(f"  Round {round_idx} summary: {succeeded} succeeded, {failed} failed")

        write_iteration_report(project, all_batch_records, result_dir, self.max_header_rounds, self.header_batch_size)
        self._refresh_header_iteration_visualization(ai_name, project_name, graph_dir, result_dir)

        # 收敛判定只看非桩节点（桩状态恒为 success，但显式排除更清晰）
        non_stub_headers = [h for h in project.headers if not h.is_manual_stub()]
        if not all(header.latest_compile_status == "success" for header in non_stub_headers):
            failed_headers = [header.key for header in non_stub_headers if header.latest_compile_status != "success"]
            self._write_header_failure_summary(project, result_dir, failed_headers)
            Project.save(project, graph_dir)
            if allow_failures:
                print(
                    "warning: header compilation did not converge; "
                    f"continuing with failed headers: {failed_headers}"
                )
                return all_batch_records
            raise RuntimeError(
                f"Header compilation did not converge within {self.max_header_rounds} rounds. "
                f"Failed headers: {failed_headers}"
            )

        Project.save(project, graph_dir)
        print(f"Header translation completed. Graph saved to {graph_dir}")
        return all_batch_records

    def run_method_mapping(
        self,
        ai_name: str,
        project_name: str,
        force_rebuild: bool = False,
        run_id: str = "",
        clear_method_progress: bool = False,
    ) -> None:
        """执行 method 映射阶段：为每个方法标注其 Java↔C++ 映射关系。

        映射结果会持久化到 graph 中；可选地先清空之前的 method 进度，
        并抽取外部方法补充到 method 图中。

        参数：
            ai_name: 模型名。
            project_name: 源项目名。
            force_rebuild: 是否强制重建图结构。
            run_id: 运行 ID（空表示使用旧式平铺路径）。
            clear_method_progress: 是否在映射前清空已有 method 翻译进度。
        """
        self.generator.set_trace_stage("method_mapping")
        project = self.graph_build_step.build_graph(ai_name, project_name, force_rebuild=force_rebuild, run_id=run_id)
        graph_dir = cfg_graph_dir_path(ai_name, project_name, version) if not run_id else cfg_run_graph_dir(ai_name, project_name, version, run_id)
        result_dir = cfg_translate_result_dir_path(ai_name, project_name, version) if not run_id else cfg_run_result_dir(ai_name, project_name, version, run_id)
        result_dir.mkdir(parents=True, exist_ok=True)

        if clear_method_progress:
            self._clear_method_progress(project, result_dir)
            Project.save(project, graph_dir)
            print(f"  Cleared method translation progress in graph {graph_dir}")

        self._extract_external_methods(project, graph_dir)

        print("========== Method mapping ==========")
        self.method_mapping_step.map_methods(project.headers, result_dir)
        self.method_state_manager.refresh_headers(project.headers)
        Project.save(project, graph_dir)
        print(f"  Saved graph with method mappings to {graph_dir}")

    def run_method_translation(
        self,
        ai_name: str,
        project_name: str,
        force_rebuild: bool = False,
        run_id: str = "",
        clear_method_progress: bool = False,
        skip_mapping: bool = False,
        skip_cpp_compile: bool = False,
        repair_after_compile: bool = False,
        max_repair_attempts: int = 10,
        apply_repair: bool = False,
        max_tool_calls: int | None = None,
    ) -> None:
        """执行 method 翻译、文件生成与可选的 C++ 编译检查和 agent 修复。

        流程：清空进度(可选) → 映射(除非 skip_mapping) → 翻译方法体 →
        生成最终 .h/.cpp 文件 → 编译检查 → (可选)agent 修复后重新编译。

        参数：
            ai_name: 模型名。
            project_name: 源项目名。
            force_rebuild: 是否强制重建图结构。
            run_id: 运行 ID。
            clear_method_progress: 是否先清空已有 method 进度。
            skip_mapping: 是否跳过 LLM 方法映射步骤（消融）。
            skip_cpp_compile: 是否跳过最终 C++ 编译检查。
            repair_after_compile: 编译检查后是否执行 agent 修复。
            max_repair_attempts: 每个失败文件的最大修复尝试次数。
            apply_repair: 是否将修复结果回写到 result 目录。
        """
        project = self.graph_build_step.build_graph(ai_name, project_name, force_rebuild=force_rebuild, run_id=run_id)
        graph_dir = cfg_graph_dir_path(ai_name, project_name, version) if not run_id else cfg_run_graph_dir(ai_name, project_name, version, run_id)
        result_dir = cfg_translate_result_dir_path(ai_name, project_name, version) if not run_id else cfg_run_result_dir(ai_name, project_name, version, run_id)
        result_dir.mkdir(parents=True, exist_ok=True)

        if clear_method_progress:
            self._clear_method_progress(project, result_dir)
            Project.save(project, graph_dir)
            print(f"  Cleared method translation progress in graph {graph_dir}")

        if not skip_mapping:
            self._extract_external_methods(project, graph_dir)
            print("========== Method mapping ==========")
            self.generator.set_trace_stage("method_mapping")
            self.method_mapping_step.map_methods(project.headers, result_dir)
            self.method_state_manager.refresh_headers(project.headers)
            Project.save(project, graph_dir)
            print(f"  Saved graph with method mappings to {graph_dir}")
        else:
            self._extract_external_methods(project, graph_dir)

        print("========== Method state refresh ==========")
        self.method_state_manager.refresh_headers(project.headers)
        Project.save(project, graph_dir)

        print("========== Method translation ==========")
        self.generator.set_trace_stage("method_translation")
        # 方法翻译若因完整性校验失败而中断，也要先保存已翻译的进度，
        # 保证 --resume 续跑只补缺口而不是全量重来。
        try:
            self.method_translation_step.translate_methods(project.methods, project.headers)
        finally:
            self.method_state_manager.refresh_headers(project.headers)
            Project.save(project, graph_dir)
            print(f"  Saved graph with translated methods to {graph_dir}")

        print("========== Final file generation ==========")
        self.cpp_file_generation_step.generate_files(
            ai_name,
            project_name,
            version,
            result_dir,
            project,
        )
        Project.save(project, graph_dir)

        if not skip_cpp_compile:
            print("========== C++ compile check ==========")
            self.cpp_compile_step.compile_cpp_files(result_dir, project)
            self.cpp_compile_step.compile_header_files(result_dir, project)
            Project.save(project, graph_dir)
            if repair_after_compile:
                self._run_agent_repair_on_project(
                    ai_name,
                    project_name,
                    result_dir,
                    project,
                    max_repair_attempts=max_repair_attempts,
                    apply_repair=apply_repair,
                    max_tool_calls=max_tool_calls,
                )
                compile_dir = result_dir if apply_repair else result_dir.parent / "review"
                self.cpp_compile_step.compile_cpp_files(compile_dir, project)
                self.cpp_compile_step.compile_header_files(compile_dir, project)
                Project.save(project, graph_dir)
        print("Method translation completed!")

    def run_cpp_compile_check(self, ai_name: str, project_name: str, force_rebuild: bool = False, run_id: str = "") -> None:
        """仅执行 C++ 编译检查阶段并持久化结果。

        对已生成的结果目录中的 .cpp 与 .h 文件分别调用 clang++ 编译检查，
        将编译结果写回 graph 后再保存。

        参数：
            ai_name: 模型名。
            project_name: 源项目名。
            force_rebuild: 是否强制重建图结构。
            run_id: 运行 ID。
        """
        project = self.graph_build_step.build_graph(ai_name, project_name, force_rebuild=force_rebuild, run_id=run_id)
        graph_dir = cfg_graph_dir_path(ai_name, project_name, version) if not run_id else cfg_run_graph_dir(ai_name, project_name, version, run_id)
        result_dir = cfg_translate_result_dir_path(ai_name, project_name, version) if not run_id else cfg_run_result_dir(ai_name, project_name, version, run_id)
        result_dir.mkdir(parents=True, exist_ok=True)

        print("========== C++ compile check ==========")
        self.cpp_compile_step.compile_cpp_files(result_dir, project)
        self.cpp_compile_step.compile_header_files(result_dir, project)
        Project.save(project, graph_dir)
        print(f"  Saved graph with C++ compile results to {graph_dir}")

    def run_agent_repair(
        self,
        ai_name: str,
        project_name: str,
        force_rebuild: bool = False,
        run_id: str = "",
        max_repair_attempts: int = 10,
        apply_repair: bool = False,
        max_tool_calls: int | None = None,
    ) -> None:
        """执行 agent 修复阶段：针对编译失败的文件进行迭代修复。

        若尚未生成编译摘要则先执行一次编译检查；随后调用 agent 修复失败
        文件，修复后对（回写后的）目录再次执行编译检查并保存结果。

        参数：
            ai_name: 模型名。
            project_name: 源项目名。
            force_rebuild: 是否强制重建图结构。
            run_id: 运行 ID。
            max_repair_attempts: 每个失败文件的最大修复尝试次数。
            apply_repair: 是否将修复结果回写到 result 目录。
        """
        project = self.graph_build_step.build_graph(ai_name, project_name, force_rebuild=force_rebuild, run_id=run_id)
        graph_dir = cfg_graph_dir_path(ai_name, project_name, version) if not run_id else cfg_run_graph_dir(ai_name, project_name, version, run_id)
        result_dir = cfg_translate_result_dir_path(ai_name, project_name, version) if not run_id else cfg_run_result_dir(ai_name, project_name, version, run_id)
        result_dir.mkdir(parents=True, exist_ok=True)

        if not (result_dir / "compile_report" / "cpp_compile_summary.json").exists():
            print("========== C++ compile check ==========")
            self.cpp_compile_step.compile_cpp_files(result_dir, project)
            self.cpp_compile_step.compile_header_files(result_dir, project)
            Project.save(project, graph_dir)

        self._run_agent_repair_on_project(
            ai_name,
            project_name,
            result_dir,
            project,
            max_repair_attempts=max_repair_attempts,
            apply_repair=apply_repair,
            max_tool_calls=max_tool_calls,
        )

        print("========== Post-repair C++ compile check ==========")
        compile_dir = result_dir if apply_repair else result_dir.parent / "review"
        self.cpp_compile_step.compile_cpp_files(compile_dir, project)
        self.cpp_compile_step.compile_header_files(compile_dir, project)
        Project.save(project, graph_dir)
        print(f"  Saved graph with repair results to {graph_dir}")

    def run_full_translation(
        self,
        ai_name: str,
        project_name: str,
        force_rebuild: bool = False,
        run_id: str = "",
        clear_method_progress: bool = False,
        skip_mapping: bool = False,
        skip_cpp_compile: bool = False,
        repair_after_compile: bool = False,
        max_repair_attempts: int = 10,
        apply_repair: bool = False,
        max_tool_calls: int | None = None,
        allow_header_failures: bool = False,
    ) -> List[HeaderBatchRecord]:
        """运行完整翻译流水线：先 header 翻译，再 method 翻译与文件生成。

        参数：
            ai_name: 模型名。
            project_name: 源项目名。
            force_rebuild: 是否强制重建图结构。
            run_id: 运行 ID。
            clear_method_progress: 是否先清空 method 进度。
            skip_mapping: 是否跳过方法映射（消融）。
            skip_cpp_compile: 是否跳过最终 C++ 编译检查。
            repair_after_compile: 编译后是否执行 agent 修复。
            max_repair_attempts: 每个失败文件的最大修复尝试次数。
            apply_repair: 是否回写修复结果。
            max_tool_calls: 单项目 repair 阶段的最大 LLM 工具调用次数。
            allow_header_failures: header 未收敛时是否仍继续。

        返回：
            List[HeaderBatchRecord]: header 翻译各批次/轮次的记录。
        """
        all_batch_records = self.run_header_translation(
            ai_name,
            project_name,
            force_rebuild=force_rebuild,
            run_id=run_id,
            allow_failures=allow_header_failures,
        )
        self.run_method_translation(
            ai_name,
            project_name,
            force_rebuild=False,
            run_id=run_id,
            clear_method_progress=clear_method_progress,
            skip_mapping=skip_mapping,
            skip_cpp_compile=skip_cpp_compile,
            repair_after_compile=repair_after_compile,
            max_repair_attempts=max_repair_attempts,
            apply_repair=apply_repair,
            max_tool_calls=max_tool_calls,
        )
        print("Full translation pipeline completed successfully!")
        return all_batch_records

    def _extract_external_methods(self, project: Project, graph_dir: Path) -> None:
        """抽取在头文件中被引用但未定义的外部方法，补充到 method 图中。

        参数：
            project: 当前项目图对象（会就地修改）。
            graph_dir: graph 目录，若有新增方法则更新保存。
        """
        extracted_count = extract_external_methods(project)
        if extracted_count:
            print(f"========== External method extraction: {extracted_count} method(s) added to the method graph ==========")
            Project.save(project, graph_dir)

    def _clear_method_progress(self, project: Project, result_dir: Path) -> None:
        """清空所有方法的翻译进度历史，并删除已生成的映射目录。

        参数：
            project: 当前项目图对象（会就地清空各 method 的进度）。
            result_dir: 结果目录（用于删除 mapping 子目录）。
        """
        cleared_count = 0
        for layer in project.methods:
            for method in layer:
                method.clean(del_history_iter_suggestion=True)
                cleared_count += 1

        mapping_dir = result_dir / "mapping"
        if mapping_dir.exists():
            shutil.rmtree(mapping_dir)

        print(f"  Cleared method progress for {cleared_count} methods.")

    def _write_header_failure_summary(self, project: Project, result_dir: Path, failed_headers: List[str]) -> None:
        """把编译失败的 header 相关信息写入 JSON 摘要报告。

        记录每个失败 header 的类名、状态、来源类型、解析出的 issue 列表
        与编译输出，供后续人工或脚本分析。

        参数：
            project: 当前项目图对象。
            result_dir: 结果目录（摘要写入其 header_failure_report 子目录）。
            failed_headers: 需要汇总的失败 header key 列表。
        """
        summary_dir = result_dir / "header_failure_report"
        summary_dir.mkdir(parents=True, exist_ok=True)
        rows = []
        for header in project.headers:
            if header.key not in failed_headers:
                continue
            issues = []
            for report in header.compile_reports:
                report_issues = getattr(report, "issues", None)
                if report_issues is None and isinstance(report, dict):
                    report_issues = report.get("issues", [])
                for issue in report_issues or []:
                    if isinstance(issue, dict):
                        issues.append({
                            "type": issue.get("type", ""),
                            "detail": issue.get("detail", ""),
                        })
                    else:
                        issues.append({
                            "type": getattr(issue, "type", ""),
                            "detail": getattr(issue, "detail", ""),
                        })
            rows.append({
                "header": header.key,
                "translated_class_name": header.translated_class_name,
                "status": header.latest_compile_status,
                "source_kind": header.source_kind,
                "issues": issues,
                "compile_output": header.compile_output,
            })

        summary_path = summary_dir / "header_failure_summary.json"
        summary_path.write_text(
            json.dumps({"failed_headers": rows}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"Header failure summary written to {summary_path}")

    def _run_agent_repair_on_project(
        self,
        ai_name: str,
        project_name: str,
        result_dir: Path,
        project: Project,
        max_repair_attempts: int,
        apply_repair: bool,
        max_tool_calls: int | None = None,
    ) -> None:
        """对当前项目运行 agent 修复，并打印修复汇总。

        参数：
            ai_name: 模型名。
            project_name: 源项目名。
            result_dir: 结果目录。
            project: 当前项目图对象。
            max_repair_attempts: 每个失败文件的最大尝试次数。
            apply_repair: 是否将修复结果回写到 result 目录。
            max_tool_calls: 最大工具调用次数；为 None 时按模块规模自适应
                （max(150, 10 × 头文件数)）。
        """
        # 按模块规模自适应 repair 预算：小模块保底 150，大模块按头文件数放大
        if max_tool_calls is None:
            max_tool_calls = max(150, 10 * len(project.headers))
            print(f"Adaptive repair tool-call budget: {max_tool_calls} (headers={len(project.headers)})")
        print("========== Agent repair ==========")
        review_dir = result_dir.parent / "review"
        summary = self.agent_repair_step.run_repair(
            ai_name=ai_name,
            project_name=project_name,
            result_dir=result_dir,
            review_dir=review_dir,
            max_attempts=max_repair_attempts,
            apply_repair=apply_repair,
            max_tool_calls=max_tool_calls,
        )
        print(
            f"Agent repair summary: total_failed={summary.total_failed_files}, "
            f"repaired={summary.repaired_count}, failed={summary.failed_count}, "
            f"tool_calls={summary.tool_call_count}/{max_tool_calls if max_tool_calls is not None else 'unlimited'}"
        )

    def _refresh_header_iteration_visualization(
        self, ai_name: str, project_name: str, graph_dir: Path, result_dir: Path
    ) -> None:
        """刷新 header 迭代过程的图表输出（失败时不阻断主流程）。

        参数：
            ai_name: 模型名。
            project_name: 源项目名。
            graph_dir: graph 目录。
            result_dir: 结果目录。
        """
        try:
            generate_header_iteration_outputs(
                version=version,
                project_name=project_name,
                ai_name=ai_name,
                graph_dir=graph_dir,
                result_dir=result_dir,
            )
        except Exception as exc:
            print(f"warning: failed to generate header iteration visualization: {exc}")
