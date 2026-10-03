from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

from graph import Header, Method
from utils.Generator import Generator
from utils.str_process import get_json_str
from v4_7.prompts.method_mapping_prompt import method_mapping_prompt

from .cpp_header_scope import scope_header_to_definition_owner
from .models import MethodMappingItem, MethodMappingResult


_CPP_IDENTIFIER_PATTERN = r"[A-Za-z_$][A-Za-z0-9_$]*"
_CPP_SYMBOLIC_OPERATOR_PATTERN = (
    r"operator\s*(?:\[\]|\(\)|<=>|==|!=|<=|>=|<<|>>|\+\+|--|->\*|->|&&|\|\||[+\-*/%<>&|^~!=,])"
)
_MAX_MAPPING_ATTEMPTS = 3


class MethodMappingStep:
    """借助 LLM 建立 Java 方法到 C++ 定义签名的映射并校验其语义。"""

    def __init__(self, generator: Generator):
        """初始化方法映射步骤。

        参数:
            generator: 用于调用 LLM 生成映射结果的 Generator 实例。
        """
        self.generator = generator

    def map_methods(self, headers: List[Header], output_dir: Path | None = None) -> None:
        """调用 LLM 为一批头文件中的 Java 方法生成到 C++ 的映射。

        generated_external 头会被跳过（其方法节点由 external_method_extractor 直接建立）。
        每个头文件的映射结果会被校验并应用到对应的 Method 节点上，
        可选的输出目录会用于保存映射报告。

        参数:
            headers: 待映射的头文件列表。
            output_dir: 可选，报告输出目录。
        """
        # generated_external 头没有 Java 源方法，方法节点由 external_method_extractor
        # 直接建立并标记，不能走 LLM mapping（否则会被当作 unmapped 全部 skip）。
        # manual_stub 同理：方法节点由 manual_stub_loader 直接建立。
        source_headers = [
            header for header in headers
            if not header.is_generated_external() and not header.is_manual_stub()
        ]
        unavailable_headers = [
            header for header in source_headers if not (header.translated_code or "").strip()
        ]
        for header in unavailable_headers:
            self._mark_header_methods_unavailable(header)
        target_headers = [
            header for header in source_headers if (header.translated_code or "").strip()
        ]
        # 记录全量头列表: 匿名类覆盖方法可能归属其它头, 查找时需要跨头索引
        self._all_headers = headers
        self._foreign_method_index = None
        prompts = [self.build_prompt(header, headers) for header in target_headers]
        outputs = self.generator.generate(prompts, require_valid_json=True)

        if len(outputs) != len(target_headers):
            raise RuntimeError(
                "Method mapping output count mismatch: "
                f"expected {len(target_headers)}, received {len(outputs)}"
            )

        for header, output in zip(target_headers, outputs):
            result, warnings = self._parse_and_apply_mapping(header, output)
            attempt = 1
            while self._mapping_requires_retry(warnings) and attempt < _MAX_MAPPING_ATTEMPTS:
                feedback = (
                    "The previous mapping was incomplete or referenced declarations outside the correct "
                    "owner class. Return a corrected complete mapping. Problems to fix:\n"
                    + "\n".join(warnings)
                )
                retry_prompt = self.build_prompt(header, headers, feedback)
                retry_output = self.generator.generate([retry_prompt], require_valid_json=True)[0]
                result, warnings = self._parse_and_apply_mapping(header, retry_output)
                attempt += 1
            if output_dir is not None:
                self.save_mapping_report(header, result, warnings, output_dir)
            self._validate_mapping_completeness(header, warnings)

    def _mark_header_methods_unavailable(self, header: Header) -> None:
        """标记因 header 翻译失败而无法进入方法映射的方法。

        参数:
            header: 未生成有效 C++ 声明的源 header。

        返回:
            None。
        """
        # allow_header_failures 模式必须保留该文件失败，但不应让方法映射门禁
        # 提前终止整个模块；最终编译、链接和测试仍会严格记录该缺失产物。
        for method in header.methods:
            method.mapping_status = "header_unavailable"
            method.method_body_location = "none"
            method.skip_translation = True
            method.skip_translation_reason = "translated header is unavailable"

    def _validate_mapping_completeness(
        self,
        header: Header,
        warnings: Iterable[str],
    ) -> None:
        """对重试后的最终映射执行硬性完整性校验。

        参数:
            header: 当前已应用映射的头文件。
            warnings: 最后一次映射产生的警告。

        返回:
            None。

        抛出:
            RuntimeError: 映射仍不完整或 owner 无效时抛出。
        """
        # 接口/抽象方法天然没有方法体，映射到 C++ 具体定义是合理结果；
        # implemented_in_header 验证对模板/虚函数/=delete 等声明形态误报率高。
        # 两者仅保留警告（仍可触发重试），不作为硬失败条件。
        issues = [
            warning
            for warning in warnings
            if self._mapping_requires_retry([warning])
            and not warning.startswith(
                "declaration-only Java method mapped to concrete C++ definition:"
            )
            and not warning.startswith(
                "implemented_in_header was not verified by header body:"
            )
        ]
        for method in header.methods:
            if not self._has_concrete_java_body(method):
                continue
            if (
                "$" in method.key
                and method.mapping_status in {"", "unmapped", "invalid_cpp_definition"}
            ):
                # 匿名/嵌套类成员: 解析器会把外部类源码中的嵌套类方法归属到
                # 当前头, 而映射模型通常不覆盖它们。降级为警告跳过, 不作硬
                # 失败; 缺失实现会在整文件编译阶段体现为未定义符号。
                print(
                    "warning: unmapped nested/anonymous class member skipped: "
                    f"{method.key}"
                )
                continue
            if method.mapping_status in {"", "unmapped", "invalid_cpp_definition"}:
                issues.append(
                    f"concrete Java method has no valid C++ mapping: {method.key} "
                    f"(status={method.mapping_status or 'empty'})"
                )
                continue
            if (
                method.mapping_status == "deleted_or_merged"
                and not method.skip_translation_reason.startswith("merged into ")
            ):
                # 模型删除具体 Java 方法仅打印警告：样板方法与静态工厂的删除
                # 多数合理，真实缺失由后续编译/repair 阶段兜住。
                print(
                    "warning: concrete Java method was deleted without a verified "
                    f"shared C++ target: {method.key}"
                )

        if issues:
            details = "\n".join(f"- {issue}" for issue in dict.fromkeys(issues))
            raise RuntimeError(
                f"Method mapping completeness validation failed for {header.key}:\n{details}"
            )

    def _parse_and_apply_mapping(
        self,
        header: Header,
        output: str,
    ) -> Tuple[MethodMappingResult, List[str]]:
        """解析一次模型映射输出并应用到方法图。

        参数:
            header: 当前映射所属的头文件。
            output: 模型返回的原始 JSON 文本。

        返回:
            解析后的映射结果及应用时产生的警告列表。
        """
        json_str = get_json_str(output) or output
        result = MethodMappingResult.model_validate_json(json_str)
        return result, self.apply_mapping(header, result)

    def _mapping_requires_retry(self, warnings: Iterable[str]) -> bool:
        """判断映射警告是否表示结果不完整或 owner 匹配无效。

        参数:
            warnings: 本次映射应用产生的警告。

        返回:
            存在遗漏、未知 Java 签名或无效 C++ owner 声明时返回 True。
        """
        retryable_prefixes = (
            "method is not present in LLM mapping result:",
            "mapped Java signature not found in graph:",
            "mapped C++ definition not found in header for",
            "declaration-only Java method competed with concrete implementation:",
            "declaration-only Java method mapped to concrete C++ definition:",
            "implemented_in_header was not verified by header body:",
        )
        return any(warning.startswith(retryable_prefixes) for warning in warnings)

    def build_prompt(
        self,
        header: Header,
        headers: List[Header],
        compatibility_feedback: str = "",
    ) -> str:
        """构建单个头文件的方法映射提示词。

        参数:
            header: 需要映射的头文件。
            headers: 头文件列表（用于上下文）。
            compatibility_feedback: 可选的兼容性反馈信息。

        返回:
            组装好的方法映射提示词字符串。
        """
        java_method_list = self._format_java_method_list(header.methods)
        return method_mapping_prompt(
            header.source_code,
            java_method_list,
            header.translated_code,
            compatibility_feedback,
        )

    def apply_mapping(self, header: Header, result: MethodMappingResult) -> List[str]:
        """将 LLM 返回的映射结果应用到头文件中的方法节点。

        遍历映射项，将每项匹配到图上对应的方法并写入映射状态；
        未出现在映射结果中的方法会被标记为 unmapped。

        参数:
            header: 映射结果所属的头文件。
            result: 解析后的方法映射结果。

        返回:
            映射过程中产生的警告信息列表。
        """
        warnings: List[str] = []
        methods_by_signature = self._index_methods(header.methods)
        mapped_method_ids = set()
        methods_by_cpp_target: Dict[str, Method] = {}

        for item in result.method_mappings:
            java_signature = item.java_signature.strip()
            cpp_definition = item.cpp_definition.strip()

            if not java_signature:
                warnings.append(
                    f"added C++ method has no Java source method: {cpp_definition or '(empty cpp_definition)'}"
                )
                continue

            method = self._find_varargs_disambiguated_method(
                java_signature,
                header.methods,
            )
            if method is None:
                method = self._find_method(java_signature, methods_by_signature)
            resolved_parameter_drift = False
            if method is None:
                method = self._find_unique_method_by_owner_and_name(
                    java_signature,
                    header.methods,
                )
                if method is None:
                    foreign = self._find_foreign_override_method(java_signature, header.key)
                    if foreign is not None:
                        # 匿名类覆盖(如 AdviceListener$1:before)实际归属声明该方法
                        # 的其它头; 跳过该项且不触发重试, 交由被覆盖头正常翻译。
                        warnings.append(
                            "anonymous override mapped to foreign header method "
                            f"(skipped): {java_signature} -> {foreign[1].key}"
                        )
                        continue
                    warnings.append(f"mapped Java signature not found in graph: {java_signature}")
                    continue
                resolved_parameter_drift = True
                warnings.append(
                    "mapped Java signature parameter drift resolved by unique owner/name: "
                    f"{java_signature} -> {method.key}"
                )

            mapped_method_ids.add(id(method))
            cpp_target = self._normalize_cpp_target(cpp_definition)
            merged_into = methods_by_cpp_target.get(cpp_target) if cpp_target else None
            if merged_into is not None and merged_into is not method:
                preferred = self._prefer_duplicate_target_owner(merged_into, method, cpp_definition)
                if preferred is method:
                    self._mark_duplicate_target_as_merged(
                        merged_into,
                        merged_into.mapped_java_signature or merged_into.key,
                        method,
                    )
                    self._apply_item_to_method(method, item)
                    methods_by_cpp_target[cpp_target] = method
                    warnings.extend(self._semantic_mapping_warnings(method, item))
                    warnings.append(
                        "declaration-only Java method competed with concrete implementation: "
                        f"preferred {method.key} over {merged_into.key} for {cpp_definition}"
                    )
                    continue

                self._mark_duplicate_target_as_merged(method, java_signature, merged_into)
                warning_prefix = "multiple Java methods map to one C++ definition"
                if not self._has_concrete_java_body(method) and self._has_concrete_java_body(merged_into):
                    warning_prefix = "declaration-only Java method competed with concrete implementation"
                warnings.append(
                    f"{warning_prefix}; merged {method.key} into {merged_into.key}: "
                    f"{cpp_definition}"
                )
                continue

            self._apply_item_to_method(method, item)
            if resolved_parameter_drift:
                # 后续翻译与报告应引用真实 Java 图签名，而不是模型臆造的参数列表。
                method.mapped_java_signature = method.key

            if cpp_definition and not self._cpp_definition_matches_header(header.translated_code or "", cpp_definition):
                method.mapping_status = "invalid_cpp_definition"
                method.method_body_location = "none"
                method.skip_translation = True
                method.skip_translation_reason = "LLM mapped C++ definition not found in translated header"
                warnings.append(f"mapped C++ definition not found in header for {method.key}: {cpp_definition}")
            elif cpp_target:
                methods_by_cpp_target[cpp_target] = method

            warnings.extend(self._semantic_mapping_warnings(method, item))

        for method in header.methods:
            if id(method) in mapped_method_ids:
                continue
            method.mapping_status = "unmapped"
            method.method_body_location = "none"
            method.skip_translation = True
            method.skip_translation_reason = "method is not present in LLM mapping result"
            warnings.append(f"method is not present in LLM mapping result: {method.key}")

        return warnings

    def _normalize_cpp_target(self, cpp_definition: str) -> str:
        """规范化 C++ 定义签名，用于识别多个 Java 方法合并到同一目标。

        参数:
            cpp_definition: 模型返回的 C++ 定义签名。

        返回:
            去除空白差异后的目标键；空定义返回空字符串。
        """
        return re.sub(r"\s+", "", cpp_definition.strip())

    def _mark_duplicate_target_as_merged(
        self,
        method: Method,
        java_signature: str,
        merged_into: Method,
    ) -> None:
        """将重复指向同一 C++ 定义的后续 Java 方法标记为已合并。

        参数:
            method: 当前重复映射的方法。
            java_signature: 当前方法在映射结果中的 Java 签名。
            merged_into: 首个占用该 C++ 目标、负责生成实现的方法。
        """
        method.mapped_java_signature = java_signature.strip()
        method.mapped_cpp_definition = ""
        method.translated_declaration = ""
        method.is_template_method = False
        method.implemented_in_header = False
        method.mapping_status = "deleted_or_merged"
        method.method_body_location = "none"
        method.is_deleted_method = True
        method.skip_translation = True
        method.skip_translation_reason = f"merged into {merged_into.key} because both map to one C++ definition"

    def _prefer_duplicate_target_owner(
        self,
        existing: Method,
        candidate: Method,
        cpp_definition: str,
    ) -> Method:
        """从共享同一 C++ 目标的 Java 方法中选择更可信的翻译源。

        Java owner 与 C++ 最内层 owner 同名者优先；owner 条件相同时，具体
        方法体优先于接口或抽象声明；仍相同时保持原顺序，以兼容合法重载合并。

        参数:
            existing: 已占用该 C++ 目标的方法。
            candidate: 后续映射到相同目标的方法。
            cpp_definition: 两个方法共享的 C++ 定义签名。

        返回:
            应负责生成目标 C++ 实现的方法。
        """
        existing_rank = self._duplicate_target_rank(existing, cpp_definition)
        candidate_rank = self._duplicate_target_rank(candidate, cpp_definition)
        return candidate if candidate_rank > existing_rank else existing

    def _duplicate_target_rank(self, method: Method, cpp_definition: str) -> Tuple[int, int]:
        """计算重复 C++ 目标候选方法的语义优先级。

        参数:
            method: Java 方法节点。
            cpp_definition: 候选方法共享的 C++ 定义签名。

        返回:
            ``(owner 是否匹配, 是否有具体方法体)`` 排序元组。
        """
        return (
            int(self._java_owner_matches_cpp_owner(method, cpp_definition)),
            int(self._has_concrete_java_body(method)),
        )

    def _has_concrete_java_body(self, method: Method) -> bool:
        """判断 Java 方法节点是否包含可供翻译的具体方法体。

        参数:
            method: Java 方法节点。

        返回:
            方法源码非空且不是解析器生成的无方法体占位符时返回 True。
        """
        code = (method.code or "").strip()
        return bool(code) and "(interface) no body" not in code

    def _java_owner_matches_cpp_owner(self, method: Method, cpp_definition: str) -> bool:
        """判断 Java 最内层 owner 是否与 C++ 最内层 owner 一致。

        参数:
            method: Java 方法节点。
            cpp_definition: C++ 定义签名。

        返回:
            两端最内层类名一致时返回 True。
        """
        java_owner = method.key.rsplit(":", 1)[0].split("$")[-1].split(".")[-1]
        cpp_owner = self._extract_cpp_owner(cpp_definition).split("::")[-1]
        return java_owner == cpp_owner

    def _extract_cpp_owner(self, cpp_definition: str) -> str:
        """提取 C++ 定义签名中的限定 owner。

        参数:
            cpp_definition: C++ 定义签名。

        返回:
            例如 ``Outer::Inner``；无法提取时返回空字符串。
        """
        compact = " ".join(part.strip() for part in cpp_definition.splitlines())
        method_name = self._extract_cpp_method_name(compact)
        if not method_name:
            return ""
        match = re.search(
            rf"((?:{_CPP_IDENTIFIER_PATTERN}::)+){re.escape(method_name)}\s*\(",
            compact,
        )
        return match.group(1).rstrip(":") if match else ""

    def _semantic_mapping_warnings(
        self,
        method: Method,
        item: MethodMappingItem,
    ) -> List[str]:
        """收集单个已应用映射中的语义警告。

        参数:
            method: 已应用映射的 Java 方法节点。
            item: 模型返回的原始映射项。

        返回:
            需要反馈给模型并触发重试的语义警告列表。
        """
        warnings: List[str] = []
        cpp_definition = item.cpp_definition.strip()
        # 无方法体的 Java 方法（接口/抽象）不存在 header 实现可验证，
        # = delete 的定义同样没有函数体；这两类不产 implemented_in_header 警告。
        if (
            item.implemented_in_header
            and not method.implemented_in_header
            and self._has_concrete_java_body(method)
            and "= delete" not in cpp_definition
        ):
            warnings.append(
                "implemented_in_header was not verified by header body: "
                f"{method.key} -> {cpp_definition}"
            )
        if (
            cpp_definition
            and not self._has_concrete_java_body(method)
            and method.mapping_status in {"needs_cpp_body", "needs_header_body"}
        ):
            warnings.append(
                "declaration-only Java method mapped to concrete C++ definition: "
                f"{method.key} -> {cpp_definition}"
            )
        return warnings

    def _cpp_definition_has_header_body(self, header_code: str, cpp_definition: str) -> bool:
        """验证 C++ 目标是否确实在头文件中包含函数体。

        参数:
            header_code: 完整翻译头文件代码。
            cpp_definition: 模型返回的 C++ 定义签名。

        返回:
            owner 类体内或头文件中的限定定义带有函数体时返回 True。
        """
        name = self._extract_cpp_method_name(cpp_definition)
        if not name:
            return False
        suffix_pattern = rf"{re.escape(name)}\s*\([^;{{}}]*\)\s*[^;{{}}]*\{{"
        owner_scope = scope_header_to_definition_owner(header_code, cpp_definition)
        if re.search(suffix_pattern, owner_scope, re.MULTILINE):
            return True

        owner = self._extract_cpp_owner(cpp_definition)
        if not owner:
            return False
        qualified_owner = r"\s*::\s*".join(re.escape(part) for part in owner.split("::"))
        qualified_pattern = rf"{qualified_owner}\s*::\s*{suffix_pattern}"
        return bool(re.search(qualified_pattern, header_code, re.MULTILINE))

    def save_mapping_report(
        self,
        header: Header,
        result: MethodMappingResult,
        warnings: List[str],
        output_dir: Path,
    ) -> None:
        """将映射报告以 JSON 形式保存到输出目录。

        参数:
            header: 映射对应的头文件。
            result: 解析后的映射结果。
            warnings: 映射过程产生的警告信息。
            output_dir: 报告根输出目录，报告写入其 mapping 子目录。
        """
        mapping_dir = output_dir / "mapping"
        mapping_dir.mkdir(parents=True, exist_ok=True)
        report = {
            "header": header.key,
            "method_mappings": [item.model_dump() for item in result.method_mappings],
            "applied_methods": [
                {
                    "java_signature": method.key,
                    "cpp_definition": method.mapped_cpp_definition,
                    "mapping_status": method.mapping_status,
                    "skip_translation": method.skip_translation,
                    "skip_translation_reason": method.skip_translation_reason,
                }
                for method in header.methods
            ],
            "warnings": warnings,
        }
        with open(mapping_dir / f"{header.get_output_header_name()}.method_mapping.json", "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

    def _apply_item_to_method(self, method: Method, item: MethodMappingItem) -> None:
        """将单个映射项应用到方法节点，更新其映射状态与位置信息。

        参数:
            method: 目标方法节点。
            item: 单个方法的映射项。
        """
        java_signature = item.java_signature.strip()
        cpp_definition = item.cpp_definition.strip()

        method.mapped_java_signature = java_signature
        method.mapped_cpp_definition = cpp_definition
        method.translated_declaration = cpp_definition
        method.is_template_method = item.is_template_method
        method.implemented_in_header = bool(
            item.implemented_in_header
            and cpp_definition
            and self._cpp_definition_has_header_body(method.header.translated_code or "", cpp_definition)
        )

        if not cpp_definition:
            method.mapping_status = "deleted_or_merged"
            method.method_body_location = "none"
            method.is_deleted_method = True
            method.skip_translation = True
            method.skip_translation_reason = "deleted or merged according to LLM mapping"
            return

        method.is_deleted_method = False

        if method.implemented_in_header:
            method.mapping_status = "already_implemented"
            method.method_body_location = "none"
            method.skip_translation = True
            method.skip_translation_reason = "method already implemented in translated header after body verification"
            return

        if self._looks_like_std_function_alias(
            method.header.translated_code or "",
            cpp_definition,
        ):
            method.mapping_status = "already_implemented"
            method.method_body_location = "none"
            method.skip_translation = True
            method.skip_translation_reason = "call operator is provided by std::function alias"
            return

        if self._looks_like_pure_virtual(method.header.translated_code or "", cpp_definition):
            method.mapping_status = "pure_virtual"
            method.method_body_location = "none"
            method.skip_translation = True
            method.skip_translation_reason = "pure virtual method does not require implementation"
            return

        if self._looks_like_defaulted_or_deleted(method.header.translated_code or "", cpp_definition):
            method.mapping_status = "defaulted_or_deleted"
            method.method_body_location = "none"
            method.skip_translation = True
            method.skip_translation_reason = "defaulted or deleted method does not require implementation"
            return

        if item.is_template_method:
            method.mapping_status = "needs_header_body"
            method.method_body_location = "header"
        else:
            method.mapping_status = "needs_cpp_body"
            method.method_body_location = "cpp"
        method.skip_translation = False
        method.skip_translation_reason = ""

    def _format_java_method_list(self, methods: Iterable[Method]) -> str:
        """将 Java 方法列表格式化为提示词中使用的文本。

        参数:
            methods: 可迭代的方法集合。

        返回:
            格式化后的方法描述文本；无方法时返回占位说明。
        """
        parts: List[str] = []
        for method in methods:
            parts.append(f"Signature: {method.key}\nSource:\n{method.code}")
        return "\n\n".join(parts) if parts else "(No Java methods are available.)"

    def _index_methods(self, methods: Iterable[Method]) -> Dict[str, Method]:
        """按各签名别名建立方法索引，便于按签名快速查找。

        参数:
            methods: 可迭代的方法集合。

        返回:
            签名键到方法节点的字典映射。
        """
        result: Dict[str, Method] = {}
        for method in methods:
            for key in self._java_signature_keys(method.key):
                result.setdefault(key, method)
        return result

    def _find_method(self, java_signature: str, methods_by_signature: Dict[str, Method]) -> Method | None:
        """按 Java 签名在索引中查找对应方法节点。

        参数:
            java_signature: 待匹配的 Java 方法签名。
            methods_by_signature: 签名索引。

        返回:
            匹配到的方法节点；未匹配时返回 None。
        """
        for key in self._java_signature_keys(java_signature):
            method = methods_by_signature.get(key)
            if method is not None:
                return method
        return None

    def _find_varargs_disambiguated_method(
        self,
        java_signature: str,
        methods: Iterable[Method],
    ) -> Method | None:
        """区分解析器键相同的普通参数与 Java 可变参数重载。

        Java 解析器当前会把 ``T`` 与 ``T...`` 重载折叠成同一个方法键。
        映射模型仍能从源码中返回带省略号的签名，因此在候选键相同且存在
        多个方法时，依据源码声明是否包含 ``...`` 选择唯一候选。

        参数:
            java_signature: 模型返回的 Java 方法签名。
            methods: 当前头文件中的 Java 方法节点。

        返回:
            可唯一判定的普通参数或可变参数方法；否则返回 None。
        """
        normalized = self._normalize_java_signature(java_signature)
        collapsed = normalized.replace("...", "")
        candidates = [
            method
            for method in methods
            if self._normalize_java_signature(method.key).replace("...", "") == collapsed
        ]
        if len(candidates) == 1 and "..." in normalized:
            # 解析器会从方法键中移除省略号；模型保留省略号时，owner、名称和
            # 折叠后的参数完全一致的唯一候选即可安全恢复。
            return candidates[0]
        if len(candidates) < 2:
            return None
        wants_varargs = "..." in normalized
        matching = [
            method
            for method in candidates
            if ("..." in (method.code or "")) == wants_varargs
        ]
        return matching[0] if len(matching) == 1 else None

    def _find_unique_method_by_owner_and_name(
        self,
        java_signature: str,
        methods: Iterable[Method],
    ) -> Method | None:
        """在参数列表漂移时按唯一的 owner 与方法名恢复映射。

        仅当同一 owner 下恰好存在一个同名 Java 方法时才回退，避免把真正的
        重载错误地映射到任意候选。参数差异仍会留作诊断，并由后续编译与
        repair 阶段处理 C++ 声明和调用的一致性。

        参数:
            java_signature: 模型返回、但无法精确匹配的方法签名。
            methods: 当前头文件中的 Java 方法节点。

        返回:
            唯一同 owner 同名的方法；不存在或候选不唯一时返回 None。
        """
        target_identity = self._java_owner_and_method_name(java_signature)
        if target_identity is None:
            return None
        candidates = [
            method
            for method in methods
            if self._java_owner_and_method_name(method.key) == target_identity
        ]
        return candidates[0] if len(candidates) == 1 else None

    def _java_owner_and_method_name(self, signature: str) -> Tuple[str, str] | None:
        """提取规范化 Java 签名的短 owner 与方法名。

        参数:
            signature: Java 方法签名。

        返回:
            ``(短 owner, 方法名)``；格式无法识别时返回 None。
        """
        normalized = self._normalize_java_signature(signature)
        if ":" not in normalized:
            return None
        owner, method_part = normalized.rsplit(":", 1)
        method_name = method_part.split("(", 1)[0]
        if not owner or not method_name:
            return None
        short_owner = owner.split("$")[-1].split(".")[-1]
        return short_owner, method_name

    def _strip_anonymous_qualifier(self, signature: str) -> str:
        """剥离签名 owner 中的匿名类限定符(如 AdviceListener$1 -> AdviceListener)。

        参数:
            signature: 原始 Java 方法签名。

        返回:
            去掉匿名类编号后的规范化签名。
        """
        normalized = self._normalize_java_signature(signature)
        if ":" in normalized:
            owner, method_part = normalized.rsplit(":", 1)
            owner = re.sub(r"\$\d+$", "", owner)
            return f"{owner}:{method_part}"
        return normalized

    def _get_foreign_method_index(self) -> dict:
        """构建/返回跨头方法签名索引(键含匿名限定符剥离后的别名)。"""
        if getattr(self, "_foreign_method_index", None) is None:
            index: dict = {}
            for header in getattr(self, "_all_headers", []) or []:
                for method in header.methods:
                    aliases = self._java_signature_keys(method.key)
                    stripped = self._strip_anonymous_qualifier(method.key)
                    aliases = aliases + self._java_signature_keys(stripped)
                    for key in aliases:
                        index.setdefault(key, (header.key, method))
            self._foreign_method_index = index
        return self._foreign_method_index

    def _find_foreign_override_method(
        self,
        java_signature: str,
        current_header_key: str,
    ) -> tuple[str, object] | None:
        """按匿名限定符剥离后的签名跨头查找方法。

        参数:
            java_signature: 模型返回的 Java 方法签名。
            current_header_key: 当前正在映射的头 key(命中同头不算跨头)。

        返回:
            (归属头 key, 方法节点);未命中返回 None。
        """
        stripped = self._strip_anonymous_qualifier(java_signature)
        index = self._get_foreign_method_index()
        for key in self._java_signature_keys(stripped):
            hit = index.get(key)
            if hit is not None and hit[0] != current_header_key:
                return hit
        return None

    def _java_signature_keys(self, signature: str) -> Tuple[str, ...]:
        """生成一个签名的多种别名键，用于更宽松的匹配。

        参数:
            signature: 原始规范化的 Java 签名。

        返回:
            包含完整签名、短类名前缀签名及纯方法片段签名的元组。
        """
        normalized = self._normalize_java_signature(signature)
        if ":" in normalized:
            owner, method_part = normalized.rsplit(":", 1)
            short_owner = owner.split("$")[-1].split(".")[-1]
            return (normalized, f"{short_owner}:{method_part}", method_part)
        return (normalized,)

    def _normalize_java_signature(self, signature: str) -> str:
        """规范化 Java 签名，统一空白并补齐 owner 与方法的冒号分隔。

        参数:
            signature: 原始 Java 签名。

        返回:
            规范化后的签名文本。
        """
        compact = re.sub(r"\s+", "", signature.strip())
        if ":" not in compact and "." in compact:
            owner, method_part = compact.rsplit(".", 1)
            compact = f"{owner}:{method_part}"
        return compact

    def _cpp_definition_matches_header(self, header_code: str, cpp_definition: str) -> bool:
        """判断映射的 C++ 定义是否在翻译头文件中被提及。

        参数:
            header_code: 翻译后的头文件代码。
            cpp_definition: 映射得到的 C++ 方法定义。

        返回:
            若方法名出现在头文件中则返回 True，否则 False。
        """
        name = self._extract_cpp_method_name(cpp_definition)
        if not name:
            return False
        if self._looks_like_std_function_alias(header_code, cpp_definition):
            return True
        owner_scope = scope_header_to_definition_owner(header_code, cpp_definition)
        return self._header_mentions_cpp_method(owner_scope, name)

    def _looks_like_std_function_alias(
        self,
        header_code: str,
        cpp_definition: str,
    ) -> bool:
        """判断映射目标是否由 ``std::function`` 类型别名提供调用运算符。

        参数:
            header_code: 翻译后的完整头文件代码。
            cpp_definition: 模型映射得到的 C++ 方法签名。

        返回:
            目标为 ``operator()`` 且头文件定义了 ``std::function`` 别名时返回 True。
        """
        if self._extract_cpp_method_name(cpp_definition) != "operator()":
            return False
        return bool(
            re.search(
                r"\busing\s+" + _CPP_IDENTIFIER_PATTERN + r"\s*=\s*std::function\s*<",
                header_code,
            )
        )

    def _looks_like_pure_virtual(self, header_code: str, cpp_definition: str) -> bool:
        """判断 C++ 定义是否对应头文件中的纯虚函数声明。

        参数:
            header_code: 翻译后的头文件代码。
            cpp_definition: 映射得到的 C++ 方法定义。

        返回:
            若头文件中存在对应方法的 "= 0" 纯虚声明则返回 True。
        """
        name = self._extract_cpp_method_name(cpp_definition)
        if not name:
            return False
        owner_scope = scope_header_to_definition_owner(header_code, cpp_definition)
        return bool(re.search(rf"(?:\b|~){re.escape(name.lstrip('~'))}\s*\([^;{{}}]*\)\s*=\s*0\s*;", owner_scope))

    def _looks_like_defaulted_or_deleted(self, header_code: str, cpp_definition: str) -> bool:
        """判断 C++ 定义是否对应头文件中的 =default/=delete 声明。

        参数:
            header_code: 翻译后的头文件代码。
            cpp_definition: 映射得到的 C++ 方法定义。

        返回:
            若头文件中存在对应方法的 "= default" 或 "= delete" 声明则返回 True。
        """
        name = self._extract_cpp_method_name(cpp_definition)
        if not name:
            return False
        owner_scope = scope_header_to_definition_owner(header_code, cpp_definition)
        return bool(re.search(rf"(?:\b|~){re.escape(name.lstrip('~'))}\s*\([^;{{}}]*\)\s*=\s*(default|delete)\s*;", owner_scope))

    def _header_mentions_cpp_method(self, header_code: str, name: str) -> bool:
        """判断头文件中是否出现了指定方法名的调用/定义。

        参数:
            header_code: 翻译后的头文件代码。
            name: 方法名（可能带前导 ~ 表示析构函数）。

        返回:
            若头文件中存在该方法名则返回 True。
        """
        bare_name = name.lstrip("~")
        if name.startswith("~"):
            pattern = rf"~\s*{re.escape(bare_name)}\s*\("
        else:
            pattern = rf"(?:\b|::){re.escape(bare_name)}\s*\("
        return bool(re.search(pattern, header_code))

    def _extract_cpp_method_name(self, cpp_definition: str) -> str:
        """从 C++ 定义文本中提取方法名。

        参数:
            cpp_definition: 映射得到的 C++ 方法定义文本。

        返回:
            提取到的方法名；提取失败时返回空字符串。
        """
        compact = " ".join(part.strip() for part in cpp_definition.splitlines())
        compact = re.sub(r"template\s*<[^>]+>", "", compact).strip()
        operator_match = re.search(
            rf"(?:^|::|\s)({_CPP_SYMBOLIC_OPERATOR_PATTERN})\s*\(",
            compact,
        )
        if operator_match:
            return re.sub(r"\s+", "", operator_match.group(1))
        match = re.search(
            rf"(?:^|::|\s)(~?{_CPP_IDENTIFIER_PATTERN})\s*\(",
            compact,
        )
        return match.group(1) if match else ""
