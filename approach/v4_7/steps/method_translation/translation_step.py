from __future__ import annotations

from typing import List

from graph import Header, Method
from utils.Generator import Generator
from v4_7.prompts.method_translate_prompt import (
    external_method_implement_prompt,
    method_translate_prompt_direct_with_context,
)

from .context_builder import MethodContextBuilder
from .output_parser import looks_like_expected_method, process_method_output
from .state_manager import MethodStateManager


class MethodTranslationStep:
    """按方法生成 C++ 实现，并根据模式选择是否提供跨文件上下文。"""

    def __init__(self, generator: Generator, max_translate_attempts: int = 2, translation_mode: str = "contextual"):
        """初始化方法翻译器；translation_mode 支持 contextual 或 no_context。"""
        if translation_mode not in {"contextual", "no_context"}:
            raise ValueError(f"Unsupported method translation mode: {translation_mode}")
        self.generator = generator
        self.state_manager = MethodStateManager()
        self.context_builder = MethodContextBuilder()
        self.max_translate_attempts = max(1, max_translate_attempts)
        self.translation_mode = translation_mode

    def get_prompt(self, method: Method, headers: List[Header]) -> str:
        """构造单个方法的翻译提示词。

        no_context 模式只保留方法自身信息；对于外部占位类会使用
        专门的 prompt 根据声明与使用方上下文生成最小实现。

        参数:
            method: 需要翻译的方法节点。
            headers: 全部头文件列表，用于汇总头文件名称与上下文。

        返回:
            组装好的翻译提示词字符串。

        抛出:
            ValueError: 方法缺少翻译头代码时抛出。
        """
        all_headers = [header.get_output_header_name() for header in headers]
        if not method.header.translated_code:
            raise ValueError(f"Method {method.key} has no translated header code.")

        if method.header.is_generated_external():
            # 外部占位类没有 Java 源码，用专用 prompt 根据声明 + 使用方上下文生成最小实现。
            usage_context = (
                self.context_builder.build_includer_context(method.header, headers)
                if self.translation_mode == "contextual" else ""
            )
            prompt = external_method_implement_prompt(
                method.header.translated_code,
                method.translated_declaration or method.mapped_cpp_definition,
                ",".join(all_headers),
                self.context_builder.build_related_headers_context(method, headers)
                if self.translation_mode == "contextual" else "",
                usage_context,
            )
            method.translate_prompt = prompt
            return prompt

        dependency_signature_context = self.context_builder.build_dependency_signature_context(method) if self.translation_mode == "contextual" else ""
        related_headers_context = self.context_builder.build_related_headers_context(method, headers) if self.translation_mode == "contextual" else ""
        prompt = method_translate_prompt_direct_with_context(
            method.header.source_code,
            method.code,
            method.header.translated_code,
            ",".join(all_headers),
            dependency_signature_context,
            related_headers_context,
            method.translated_declaration,
        )
        method.translate_prompt = prompt
        return prompt

    def process_output(self, method: Method, output: str) -> None:
        """解析并写入方法的翻译输出（委托给 process_method_output）。

        参数:
            method: 待处理的方法节点。
            output: LLM 返回的原始输出文本。
        """
        process_method_output(method, output)

    def get_method_to_translate(self, method_nodes: List[Method]) -> List[Method]:
        """筛选出当前层中需要实际翻译的方法节点。

        跳过接口、已标记跳过、已删除、映射位置无效以及已有翻译代码的方法。

        参数:
            method_nodes: 一层的方法节点列表。

        返回:
            需要翻译的方法节点列表。
        """
        result = []
        for node in method_nodes:
            if node.header.type == "interface":
                continue
            if node.skip_translation or node.is_deleted_method:
                continue
            if node.mapping_status and node.method_body_location not in {"header", "cpp"}:
                continue
            if node.translated_code:
                continue
            result.append(node)
        return result

    def _translate_pending_methods(self, methods: List[Method], headers: List[Header]) -> int:
        """循环翻译待处理的方法，支持多次重试失败的节点。

        每次生成一批提示词交由 LLM，校验输出并统计成功翻译数量；
        失败的节点进入下一轮，直到达到最大尝试次数。

        参数:
            methods: 待翻译的方法节点列表。
            headers: 全部头文件列表。

        返回:
            成功翻译的方法数量。
        """
        translated_count = 0
        pending = list(methods)
        for attempt in range(1, self.max_translate_attempts + 1):
            if not pending:
                break

            prompts = [self.get_prompt(node, headers) for node in pending]
            outputs = self.generator.generate(prompts, require_valid_json=True)

            next_pending: List[Method] = []
            for index, node in enumerate(pending):
                if index >= len(outputs):
                    print(
                        f"warning: method {node.key} translate attempt {attempt} "
                        "returned no corresponding model output"
                    )
                    next_pending.append(node)
                    continue
                code = outputs[index]
                try:
                    self.process_output(node, code)
                    if not looks_like_expected_method(node):
                        raise ValueError("translated code does not appear to match the target method")
                    translated_count += 1
                except Exception as exc:
                    node.raw_translated_code = code
                    node.translated_code = ""
                    print(f"warning: method {node.key} translate attempt {attempt} failed: {exc}")
                    next_pending.append(node)

            pending = next_pending

        if pending:
            for node in pending:
                print(f"warning: method {node.key} still has no valid translated implementation after retries")

        return translated_count

    def _validate_translation_completeness(self, headers: List[Header]) -> None:
        """验证所有需要方法体的节点都具有有效且匹配的翻译结果。

        参数:
            headers: 项目全部头文件及其方法节点。

        返回:
            None。

        抛出:
            RuntimeError: 任一需要落入 Header 或 CPP 的方法缺失实现，或已有
                实现与映射目标不匹配时抛出。
        """
        issues: List[str] = []
        for header in headers:
            # 手写桩方法实现由桩提供，不纳入完整性校验
            if header.is_manual_stub():
                continue
            for method in header.methods:
                if method.skip_translation or method.is_deleted_method:
                    continue
                # 与 get_method_to_translate 对齐：接口方法不参与翻译，
                # 其 C++ 实现由实现类负责，不纳入完整性校验。
                if header.type == "interface":
                    continue
                if method.method_body_location not in {"header", "cpp"}:
                    continue
                if not (method.translated_code or "").strip():
                    issues.append(f"{method.key}: missing translated implementation")
                    continue
                if not looks_like_expected_method(method):
                    issues.append(f"{method.key}: translated implementation targets another method")

        if issues:
            details = "\n".join(f"- {issue}" for issue in issues)
            raise RuntimeError(
                "Method translation completeness validation failed; final files were not generated:\n"
                + details
            )

    def translate_methods(self, method_nodes: List[List[Method]], headers: List[Header]) -> None:
        """按层翻译所有方法节点。

        先刷新全部头文件的状态，再逐层筛选待翻译方法并执行翻译，
        每层结束后重新刷新状态；最后重放一遍原始翻译代码写入节点。

        参数:
            method_nodes: 按依赖层分组的待翻译方法节点列表。
            headers: 全部头文件列表。
        """
        print("generate translated methods...")
        self.state_manager.refresh_headers(headers)

        total_methods_translated = 0
        for layer_idx, layer in enumerate(method_nodes):
            nodes_to_translate = self.get_method_to_translate(layer)

            if not nodes_to_translate:
                print(f"Layer {layer_idx}: No methods to translate.")
                continue

            translated_in_layer = self._translate_pending_methods(nodes_to_translate, headers)
            total_methods_translated += translated_in_layer
            print(f"Layer {layer_idx}: Translated {translated_in_layer}/{len(nodes_to_translate)} methods.")
            self.state_manager.refresh_headers(headers)

        # 失败输出仅作为诊断历史保留在 raw_translated_code 中，不能在绕过
        # 目标方法校验的情况下重新写回 translated_code。
        self._validate_translation_completeness(headers)

        print(f"Total methods translated: {total_methods_translated}")
