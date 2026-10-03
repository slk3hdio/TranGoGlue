from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, TypedDict

from pydantic import BaseModel


class TranslatedHeader(BaseModel):
    """单个 Header 翻译结果的数据模型。

    职责:
        承载 LLM 翻译输出的单个类的类名与翻译后的 C++ 代码。

    使用约定:
        字段 class_name 为类名，translated_code 为翻译后的 C++ 代码字符串。
    """
    class_name: str
    translated_code: str


class ExternalHeader(BaseModel):
    """外部生成 Header 的数据模型。

    职责:
        承载 LLM 输出的外部依赖 Header 的类名与内容，用于补齐项目缺失依赖。

    使用约定:
        class_name 为外部类名，content 为生成的 C++ 头文件内容。
    """
    class_name: str
    content: str


class HeaderTranslateBatch(BaseModel):
    """一轮翻译输出的批次模型。

    职责:
        封装一次翻译调用的输出，包含多个 TranslatedHeader 以及可选的外部 Header。

    使用约定:
        translated_code 为已翻译 Header 列表，external_headers 为外部 Header 列表。
    """
    translated_code: list[TranslatedHeader]
    external_headers: list[ExternalHeader] = []


class ModifyPatch(BaseModel):
    """修改补丁的数据模型。

    职责:
        描述对既有 Header 代码某一段的精确替换操作。

    使用约定:
        original_str 为待替换的原文，new_str 为替换后的内容，
        modified_part 用于标识修改部位。
    """
    class_name: str
    original_str: str
    new_str: str
    modified_part: str


class AddPatch(BaseModel):
    """新增 Header 补丁的数据模型。

    职责:
        描述需要新增的完整外部 Header 文件及其成员摘要。

    使用约定:
        class_name 为新类名，file_name 为目标文件名，content 为完整内容，
        fields 与 methods 分别记录字段与方法名，便于报告展示。
    """
    class_name: str
    file_name: str
    content: str
    fields: list[str]
    methods: list[str]


class HeaderPatchBatch(BaseModel):
    """修复轮次输出的补丁批次模型。

    职责:
        封装一次修复调用输出的修改补丁与新增补丁列表。

    使用约定:
        modify 为修改补丁列表，add 为新增补丁列表。
    """
    modify: list[ModifyPatch]
    add: list[AddPatch]


@dataclass
class HeaderCompileError:
    """项目内 Header 编译错误及其源码定位。

    职责：
        保存编译器诊断的标准化类型、摘要和实际文件位置，供 batch
        调度判断错误是否指向同一批次中的另一个 Header。

    使用约定：
        file_path 为空表示编译器未提供可解析的项目文件位置；line 和
        column 使用 0 表示未知位置。该模型只承载项目内错误。
    """

    type: str
    detail: str
    file_path: str = ""
    line: int = 0
    column: int = 0


@dataclass
class HeaderCompileResult:
    """单个 Header 编译结果的数据模型。

    职责:
        记录某个 Header 在编译步骤中的成功状态、本地错误和所有项目内错误。

    使用约定:
        header 为编译目标标识，success 表示是否成功，
        local_compile_errors 仅记录当前目标 Header 自身的编译错误；
        project_compile_errors 记录当前 Header 及其依赖 Header 的全部项目内
        错误，并保留每条错误的文件、行、列位置。
    """
    header: str
    success: bool
    local_compile_errors: List[str] = field(default_factory=list)
    project_compile_errors: List[HeaderCompileError] = field(default_factory=list)


class HeaderBatchRecord(TypedDict):
    """一个翻译批次的历史记录模型。

    职责:
        汇总某一个 Header 批次在其轮次中的翻译、补丁、编译结果与反馈信息，
        供迭代报告生成使用。

    使用约定:
        round_idx 为轮次编号，batch_headers 为批次内 Header key 列表，
        add_patches/modify_patches 为新增与修改补丁，
        compile_results 为编译结果列表，feedback_blocks 为发送给 LLM 的反馈。
    """
    round_idx: int
    batch_headers: List[str]
    add_patches: List[AddPatch]
    modify_patches: List[ModifyPatch]
    compile_results: List[HeaderCompileResult]
    feedback_blocks: Dict[str, str]
