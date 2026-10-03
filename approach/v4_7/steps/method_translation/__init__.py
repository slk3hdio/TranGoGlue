"""method_translation 包：方法翻译步骤相关组件。

该包提供 Java 方法到 C++ 方法实现的翻译链路中的各个模块，
包括方法映射（MethodMappingStep）、翻译（MethodTranslationStep）、
状态管理（MethodStateManager）以及外部方法提取（extract_external_methods）。

包内模块通过 __all__ 对外暴露统一的公共 API，供上层 pipeline 直接引用。
"""
from .external_method_extractor import extract_external_methods
from .mapping_step import MethodMappingStep
from .state_manager import MethodStateManager
from .translation_step import MethodTranslationStep

__all__ = [
    "MethodMappingStep",
    "MethodStateManager",
    "MethodTranslationStep",
    "extract_external_methods",
]
