from typing import Tuple
from graph import Project, Header
from .models import ModifyPatch, AddPatch


def apply_modify(patch: ModifyPatch, project: Project) -> Tuple[bool, str]:
    """将修改补丁应用到项目中对应 Header 的翻译代码。

    参数:
        patch: 描述原文与替换文的 ModifyPatch。
        project: 目标项目对象。

    返回:
        一个二元组 (success, message)。success 表示是否应用成功，
        message 在失败时给出原因，成功时为空字符串。
    """
    target_header = project.find_header_by_translated_class_name(patch.class_name)
    if target_header is None:
        return False, f"header {patch.class_name} not found"
    if target_header.is_manual_stub():
        # 手写桩为只读已知条件，修复补丁一律拒绝
        return False, f"header {patch.class_name} is a read-only hand-written stub"

    count = target_header.translated_code.count(patch.original_str)
    if count == 0:
        return False, f"original_str not found in {patch.class_name}"
    if count > 1:
        return False, f"original_str matched {count} times in {patch.class_name}, ambiguous"

    target_header.translated_code = target_header.translated_code.replace(
        patch.original_str, patch.new_str
    )
    return True, ""


def apply_add(patch: AddPatch, project: Project) -> Tuple[bool, str]:
    """向项目新增一个外部生成 Header。

    参数:
        patch: 描述新 Header 信息的 AddPatch。
        project: 目标项目对象。

    返回:
        一个二元组 (success, message)。success 表示是否新增成功，
        message 在失败时给出原因，成功时为空字符串。
    """
    if project.find_header_by_translated_class_name(patch.class_name):
        return False, "header already exists"

    new_header = Header(patch.class_name, "")
    new_header.source_kind = "generated_external"
    new_header.translated_code = patch.content
    project.headers.append(new_header)
    return True, ""
