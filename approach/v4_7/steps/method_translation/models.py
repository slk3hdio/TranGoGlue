from __future__ import annotations

from typing import List

from pydantic import BaseModel


class MethodTranslateResult(BaseModel):
    """单个方法翻译结果的 Pydantic 模型。

    用于校验 LLM 返回的方法翻译 JSON，保存完整的翻译后 C++ 代码。
    """
    complete_translated_code: str


class MethodMappingItem(BaseModel):
    """单个方法的映射项 Pydantic 模型。

    描述一个 Java 方法到 C++ 定义的映射关系，包含签名、定义文本
    以及是否为模板方法、是否已在头文件中实现等信息。
    """
    java_signature: str
    cpp_definition: str
    is_template_method: bool = False
    implemented_in_header: bool = False


class MethodMappingResult(BaseModel):
    """方法映射结果的 Pydantic 模型。

    包含一批 MethodMappingItem 项，对应 LLM 为某个头文件返回的完整映射结果。
    """
    method_mappings: List[MethodMappingItem]
