from __future__ import annotations

import json
from typing import Any, Dict, List

from ...prompts.header_prompts import (
    header_patch_batch_prompt,
    header_translate_batch_prompt,
)
from .models import HeaderTranslateBatch, HeaderPatchBatch
from utils.str_process import get_cpp_code, get_json_str
from graph import Header, Project
from .models import AddPatch, ModifyPatch
from pydantic import ValidationError
from utils.Generator import Generator
from utils.compile_feedback import CompileFeedback
from .patch_applier import apply_modify, apply_add
from .feedback_context import HeaderRepairContextBuilder
from .third_party_libraries import ThirdPartyLibraryAvailability
from utils.exceptions import UnexpectedOutputError


class HeaderTranslationStep:
    """负责按批次或按文件生成 C++ 头文件，并记录可重放的翻译历史。"""

    def __init__(
        self,
        generator: Generator,
        header_batch_size: int = 1,
        third_party_availability: ThirdPartyLibraryAvailability | None = None,
    ):
        """初始化 Header 翻译步骤。

        参数:
            generator: 用于调用 LLM 生成翻译结果的生成器。
            header_batch_size: 批处理大小，至少为 1。
            third_party_availability: 第三方库可用性对象，可为 None。
        """
        self.generator = generator
        self.header_batch_size = max(1, header_batch_size)
        self._current_round = 0
        self.third_party_availability = third_party_availability
        self._context_builder = HeaderRepairContextBuilder(third_party_availability)

    def translate_per_file_one_shot(
        self,
        project: Project,
        headers: List[Header],
        max_retries: int = 3,
    ) -> List[tuple[Header, List[AddPatch], List[ModifyPatch]]]:
        """为每个 Java header 独立生成一次完整文件，返回成功处理的文件记录。"""
        targets = [header for header in headers if header.source_kind == "java"]
        pending = list(targets)
        results: List[tuple[Header, List[AddPatch], List[ModifyPatch]]] = []
        for attempt in range(1, max_retries + 1):
            if not pending:
                break
            prompts = [self._build_round1_prompt([header], headers) for header in pending]
            outputs = self.generator.generate(prompts, require_valid_json=True)
            next_pending: List[Header] = []
            for header, raw_output in zip(pending, outputs):
                try:
                    add_patches, modify_patches = self._apply_round1_batch(
                        project, [header], raw_output, targets.index(header)
                    )
                    results.append((header, add_patches, modify_patches))
                except Exception as exc:
                    header.raw_translated_code = raw_output
                    header.translated_code = ""
                    print(f"warning: one-shot header {header.key} attempt {attempt} failed: {exc}")
                    next_pending.append(header)
            pending = next_pending
        for header in pending:
            print(f"warning: one-shot header {header.key} exhausted retries")
        return results

    def translate_batch(
        self,
        project: Project,
        batch_headers: List[Header],
        round_idx: int,
        batch_index: int,
        max_retries: int = 3,
    ) -> tuple[List[AddPatch], List[ModifyPatch], Dict[str, str]]:
        """按批次翻译 Header 并应用补丁，支持失败重试与状态回滚。

        职责:
            根据轮次选择首轮翻译或修复提示，调用生成器并应用补丁；
            解析失败时回滚项目状态并重试，最终返回新增补丁、修改补丁与反馈块。

        参数:
            project: 当前项目对象。
            batch_headers: 当前批次 Header 列表。
            round_idx: 当前轮次编号（大于 1 时进入修复模式）。
            batch_index: 批次序号，用于日志。
            max_retries: 最大重试次数，默认为 3。

        返回:
            三元组 (add_patches, modify_patches, feedback_blocks)。
        """
        self._current_round = round_idx

        feedback_blocks: Dict[str, str] = {}
        if round_idx > 1:
            for header in batch_headers:
                feedback_blocks[header.key] = self._context_builder.build_repair_feedback_block(header)

        last_error: Exception | None = None
        for attempt in range(1, max_retries + 1):
            snapshot = self._snapshot(project, batch_headers)
            try:
                if round_idx == 1:
                    prompt = self._build_round1_prompt(batch_headers, project.headers)
                    raw_output = self.generator.generate([prompt], require_valid_json=True)[0]
                    result = self._apply_round1_batch(
                        project,
                        batch_headers,
                        raw_output,
                        batch_index,
                    )
                else:
                    prompt = self._build_repair_prompt(project, batch_headers, project.headers, feedback_blocks)
                    raw_output = self.generator.generate([prompt], require_valid_json=True)[0]
                    result = self._apply_repair_batch(
                        batch_headers,
                        project,
                        prompt,
                        feedback_blocks,
                        raw_output,
                        batch_index,
                    )
                return (*result, feedback_blocks)
            except UnexpectedOutputError as e:
                last_error = e
                self._restore(project, batch_headers, snapshot)
                print(f"  Batch {batch_index} attempt {attempt}/{max_retries} failed: {e}")
                if attempt < max_retries:
                    print(f"  Retrying...")

        print(f"  Batch {batch_index} exhausted all {max_retries} retries: {last_error}")
        return [], [], feedback_blocks

    def _snapshot(
        self, project: Project, batch_headers: List[Header]
    ) -> Dict[str, Any]:
        """记录项目当前状态快照，用于失败时回滚。

        参数:
            project: 当前项目对象。
            batch_headers: 批次 Header 列表（本方法用于记录上下文）。

        返回:
            包含 header_count 与各 header 翻译代码的字典快照。
        """
        header_snapshots = {}
        for h in project.headers:
            header_snapshots[h.key] = {
                "translated_code": h.translated_code,
                "raw_translated_code": h.raw_translated_code,
            }
        return {
            "header_count": len(project.headers),
            "headers": header_snapshots,
        }

    def _restore(
        self, project: Project, batch_headers: List[Header], snapshot: Dict[str, Any]
    ) -> None:
        """根据快照恢复项目状态以回滚失败的尝试。

        参数:
            project: 需要恢复状态的项目对象。
            batch_headers: 批次 Header 列表（保留用于上下文）。
            snapshot: 由 _snapshot 生成的状态快照。
        """
        for h in project.headers:
            saved = snapshot["headers"].get(h.key)
            if saved:
                h.translated_code = saved["translated_code"]
                h.raw_translated_code = saved["raw_translated_code"]

        while len(project.headers) > snapshot["header_count"]:
            project.headers.pop()

    def _build_round1_prompt(self, batch_headers: List[Header], all_headers: List[Header]) -> str:
        """构建首轮翻译的提示文本。

        参数:
            batch_headers: 当前批次 Header 列表。
            all_headers: 全部 Header 列表（用于提供可用头文件清单）。

        返回:
            生成的首轮翻译提示字符串，并写入各 Header 的 translate_prompt。
        """
        batch_sections = []
        for index, header in enumerate(batch_headers, start=1):
            batch_sections.append(
                "\n".join(
                    [
                        f"Unit {index}",
                        "Java code:",
                        "```java",
                        header.source_code.strip() or "(empty)",
                        "```",
                        f"Target header file name: {header.get_output_header_name()}",
                        f"Target class name: {header.translated_class_name}",
                    ]
                )
            )

        all_headers_info = [
            f"- file: {header.get_output_header_name()}, class_name: {header.translated_class_name}"
            for header in all_headers
        ]

        prompt = header_translate_batch_prompt(
            batch_sections="\n\n".join(batch_sections),
            available_headers="\n".join(all_headers_info),
            batch_header_names=", ".join(header.key for header in batch_headers),
        )
        for header in batch_headers:
            header.translate_prompt = prompt
        return prompt

    def _build_repair_prompt(
        self,
        project: Project,
        batch_headers: List[Header],
        all_headers: List[Header],
        feedback_blocks: Dict[str, str] | None = None,
    ) -> str:
        """构建修复轮次的提示文本（含反馈与上下文）。

        参数:
            project: 当前项目对象。
            batch_headers: 当前批次 Header 列表。
            all_headers: 全部 Header 列表（提供可用头文件清单）。
            feedback_blocks: 各 Header 的编译反馈块；为 None 时自动构建。

        返回:
            生成的修复提示字符串，并写入各 Header 的 translate_prompt。
        """
        batch_sections = []
        for header in batch_headers:
            fb = (feedback_blocks or {}).get(header.key, self._context_builder.build_repair_feedback_block(header))
            batch_sections.append(
                "\n".join(
                    [
                        f"class name: {header.translated_class_name}",
                        f"Batch file: {header.get_output_header_name()}",
                        f"Source kind: {header.source_kind}",
                        "Current file content:",
                        "```cpp",
                        header.translated_code.strip() or "(empty)",
                        "```",
                        "Local compile issues to fix:",
                        fb,
                    ]
                )
            )

        all_headers_info = [
            f"- file: {header.get_output_header_name()}, class_name: {header.translated_class_name}"
            for header in all_headers
        ]
        context_sections = self._context_builder.build_repair_context_sections(project, batch_headers)

        prompt = header_patch_batch_prompt(
            target_sections="\n\n".join(batch_sections),
            context_sections=context_sections,
            available_headers="\n".join(all_headers_info),
            batch_header_names=", ".join(header.key for header in batch_headers),
        )
        for header in batch_headers:
            header.translate_prompt = prompt
        return prompt

    def _apply_round1_batch(
        self,
        project: Project,
        batch_headers: List[Header],
        raw_output: str,
        batch_index: int,
    ) -> tuple[List[AddPatch], List[ModifyPatch]]:
        """解析首轮翻译输出并应用到项目。

        职责:
            解析 HeaderTranslateBatch JSON，写入各 Header 的翻译代码与历史，
            并为外部 Header 创建项目内新 Header 及对应新增补丁。

        参数:
            project: 当前项目对象。
            batch_headers: 当前批次 Header 列表。
            raw_output: LLM 原始输出字符串。
            batch_index: 批次序号，用于错误信息。

        返回:
            二元组 (add_patches, modify_patches)，首轮修改补丁为空列表。
        """
        try:
            output = HeaderTranslateBatch.model_validate_json(get_json_str(raw_output))
            translated_headers = output.translated_code
            external_headers = output.external_headers
        except ValidationError as e:
            print(f"error: round1: can not parse json from translate output: {raw_output if len(raw_output) < 200 else raw_output[:200] + '...'}")
            raise UnexpectedOutputError(f"round 1, batch {batch_index}: can not parse json from translate output. {e}")

        add_patches: List[AddPatch] = []

        for translated in translated_headers:
            target_header = Header.find_by_translated_class_name(batch_headers, translated.class_name)
            if target_header is None:
                raise UnexpectedOutputError(f"round 1, batch {batch_index}: Header {translated.class_name} not found in batch headers. Headers in batch headers: {','.join(header.translated_class_name for header in batch_headers)}")
            target_header.raw_translated_code = str(translated)
            target_header.translated_code = get_cpp_code(translated.translated_code)
            target_header.header_translation_history.append(
                {
                    "round": self._current_round,
                    "mode": "round1_translate",
                    "prompt": target_header.translate_prompt,
                    "raw_output": raw_output,
                    "parsed_output": str(translated),
                    "translated_code": target_header.translated_code,
                }
            )

        for header in batch_headers:
            if not header.translated_code:
                raise UnexpectedOutputError(f"Header {header.translated_class_name} has no translated code.")

        for external_header in external_headers:
            if Header.find_by_translated_class_name(project.headers, external_header.class_name):
                raise UnexpectedOutputError(f"round 1, batch {batch_index}: external header {external_header.class_name} already exists in project.")
            class_cpp_name = external_header.class_name
            content = external_header.content
            new_header = Header(class_cpp_name.replace("::", "$"), "")
            new_header.source_kind = 'generated_external'
            new_header.translated_code = content
            project.headers.append(new_header)

            add_patches.append(AddPatch(
                class_name=external_header.class_name,
                file_name=external_header.class_name + ".h",
                content=content,
                fields=[],
                methods=[],
            ))

        return add_patches, []

    def _apply_repair_batch(
        self,
        batch_headers: List[Header],
        project: Project,
        prompt: str,
        feedback_blocks: Dict[str, str],
        raw_output: str,
        batch_index: int,
    ) -> tuple[List[AddPatch], List[ModifyPatch]]:
        """解析修复轮次输出并应用补丁。

        职责:
            解析 HeaderPatchBatch JSON，逐一应用修改与新增补丁，
            若失败则抛出 UnexpectedOutputError，成功后记录修复历史。

        参数:
            batch_headers: 当前批次 Header 列表。
            project: 当前项目对象。
            prompt: 发送给 LLM 的提示文本。
            feedback_blocks: 各 Header 的编译反馈块。
            raw_output: LLM 原始输出字符串。
            batch_index: 批次序号，用于错误信息。

        返回:
            二元组 (add_patches, modify_patches)。
        """
        try:
            output = HeaderPatchBatch.model_validate_json(get_json_str(raw_output))
            modify_patches = output.modify
            add_patches = output.add
        except ValidationError as e:
            print(f"error: round2: can not parse json from translate output: {raw_output if len(raw_output) < 200 else raw_output[:200] + '...'}")
            raise UnexpectedOutputError(f"round 2, batch {batch_index}: can not parse json from translate output. {e}")

        for patch in modify_patches:
            if not Header.find_by_translated_class_name(batch_headers, patch.class_name):
                print(f"warning: round 2, batch {batch_index} header {patch.class_name} not found in batch headers. Headers in batch headers: {','.join(header.translated_class_name for header in batch_headers)}")
            success, message = apply_modify(patch, project)
            if not success:
                raise UnexpectedOutputError(f"round 2, batch {batch_index}: apply modify patch {patch} failed. {message}")

        for patch in add_patches:
            success, message = apply_add(patch, project)
            if not success:
                raise UnexpectedOutputError(f"round 2, batch {batch_index}: apply add patch {patch} failed. {message}")

        self._record_repair_history(
            batch_headers,
            prompt,
            feedback_blocks,
            raw_output,
            modify_patches,
            add_patches,
        )
        return add_patches, modify_patches

    def _record_repair_history(
        self,
        batch_headers: List[Header],
        prompt: str,
        feedback_blocks: Dict[str, str],
        raw_output: str,
        modify_patches: List[ModifyPatch],
        add_patches: List[AddPatch],
    ) -> None:
        """为批次内各 Header 记录修复轮次的翻译历史。

        参数:
            batch_headers: 当前批次 Header 列表。
            prompt: 发送给 LLM 的提示文本。
            feedback_blocks: 各 Header 的编译反馈块。
            raw_output: LLM 原始输出字符串。
            modify_patches: 修改补丁列表。
            add_patches: 新增补丁列表。
        """
        serialized_output = {
            "modify": [patch.model_dump() for patch in modify_patches],
            "add": [patch.model_dump() for patch in add_patches],
        }

        for header in batch_headers:
            header.raw_translated_code = raw_output
            header.header_translation_history.append(
                {
                    "round": self._current_round,
                    "mode": "repair_batch",
                    "prompt": prompt,
                    "feedback_block": feedback_blocks.get(header.key, ""),
                    "raw_output": raw_output,
                    "parsed_output": json.dumps(serialized_output, ensure_ascii=False, indent=4),
                    "related_modify_patches": [
                        patch.model_dump()
                        for patch in modify_patches
                        if patch.class_name == header.translated_class_name
                    ],
                    "translated_code": header.translated_code,
                }
            )
