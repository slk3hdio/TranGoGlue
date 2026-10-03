"""手写 C++ 桩（manual_stub）的序列化定义加载与图注入。

桩以 JSON 形式存放在共享库 ``<source_root>/_cpp_stubs/`` 与模块级
``<source_root>/<module>/cpp_stubs/`` 中（模块覆盖共享库）。每个 JSON 描述一个
C++ 类，并声明其方法对应的 Java 签名；注入图时据此创建 Header/Method 节点，
并重跑调用边构建，使 Java 调用方到桩方法的边正常建立。

桩节点是"已翻译的已知条件"：参与上下文构建与编译链接，不参与翻译迭代，
repair 阶段只读。同名冲突时 Java 优先（闭包中已有同名 Java 类则桩不生效），
但手写桩优先于 LLM 生成的 generated_external 占位（替换之）。
"""

from __future__ import annotations

import io
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List

# 兼容从 approach/ 根目录直接运行的场景
_approach_dir = str(Path(__file__).resolve().parents[2])
if _approach_dir not in sys.path:
    sys.path.insert(0, _approach_dir)

from graph import Header, Method, Project
from graph.retrieval_tools import (
    build_call_graph,
    get_ordered_method_groups,
    get_standard_signature,
)

MANUAL_STUB_KIND = "manual_stub"
MANUAL_STUB_SOURCE_TAG = "manual_stub"


@dataclass
class StubMethodDef:
    """桩方法的序列化定义。

    :ivar java_signature: 标准化后的 Java 签名（`类名:方法名(参数类型,...)`），用于接调用边。
    :ivar cpp_declaration: 对应的 C++ 声明，作为上下文中的已知签名。
    :ivar body_location: 实现位置（"cpp" 或 "header"），仅作节点标记，不触发翻译。
    """

    java_signature: str
    cpp_declaration: str
    body_location: str = "cpp"


@dataclass
class StubDef:
    """一个手写桩类的序列化定义。

    :ivar class_name: C++ 类名（即图节点 key）。
    :ivar java_class: 对应的 Java 全限定类名（仅作文档与日志用途）。
    :ivar header_code: 完整 C++ 头文件内容。
    :ivar cpp_code: 配套实现文件内容（纯头文件类为空串）。
    :ivar methods: 方法定义列表。
    """

    class_name: str
    java_class: str
    header_code: str
    cpp_code: str
    methods: List[StubMethodDef] = field(default_factory=list)


def load_stub_definitions(stub_dirs: List[Path]) -> Dict[str, StubDef]:
    """扫描并解析桩定义目录，按覆盖优先级合并。

    同名类按目录顺序先占先得（调用方应把模块级目录放在共享库之前）。
    缺字段或 JSON 损坏的桩打警告并跳过，不阻断构建。

    :param stub_dirs: 桩搜索目录列表，高优先级在前。
    :return: 类名 -> StubDef 的字典。
    """
    stubs: Dict[str, StubDef] = {}
    for stub_dir in stub_dirs:
        stub_dir = Path(stub_dir)
        if not stub_dir.is_dir():
            continue
        for json_path in sorted(stub_dir.glob("*.json")):
            try:
                data = json.loads(json_path.read_text(encoding="utf-8"))
                stub = _parse_stub(data)
            except (ValueError, KeyError, json.JSONDecodeError) as exc:
                print(f"[manual_stub] 跳过无效桩定义 {json_path}: {exc}")
                continue
            # 高优先级目录先占位，低优先级同名直接跳过
            if stub.class_name in stubs:
                continue
            stubs[stub.class_name] = stub
    return stubs


def _parse_stub(data: dict) -> StubDef:
    """解析单个桩 JSON，校验必填字段并标准化 Java 签名。

    :param data: 桩 JSON 反序列化后的字典。
    :return: 解析得到的 StubDef。
    :raises ValueError: 必填字段缺失或类型错误。
    """
    class_name = data.get("class_name")
    if not class_name or not isinstance(class_name, str):
        raise ValueError("缺少必填字段 class_name")
    header_code = data.get("header_code")
    if not header_code or not isinstance(header_code, str):
        raise ValueError(f"桩 {class_name} 缺少必填字段 header_code")

    methods: List[StubMethodDef] = []
    for index, raw_method in enumerate(data.get("methods", [])):
        java_signature = raw_method.get("java_signature")
        cpp_declaration = raw_method.get("cpp_declaration")
        if not java_signature or not cpp_declaration:
            raise ValueError(f"桩 {class_name} 第 {index} 个方法缺少 java_signature/cpp_declaration")
        # 允许写全限定签名，统一标准化为图内 key 形式
        standard = get_standard_signature(java_signature) or java_signature
        methods.append(
            StubMethodDef(
                java_signature=standard,
                cpp_declaration=cpp_declaration,
                body_location=raw_method.get("body_location", "cpp"),
            )
        )

    return StubDef(
        class_name=class_name,
        java_class=data.get("java_class", ""),
        header_code=header_code,
        cpp_code=data.get("cpp_code", ""),
        methods=methods,
    )


def inject_manual_stubs(project: Project, stub_dirs: List[Path], method_call_path: Path) -> int:
    """把手写桩注入项目图：创建/刷新桩节点、接调用边、重分层。

    幂等：重复注入时刷新已有桩节点内容并重建其方法节点，不产生重复节点。
    冲突规则：java 节点优先（跳过）；generated_external 被手写桩替换；
    已有 manual_stub 节点刷新内容（桩文件修改后自动生效）。

    :param project: 目标项目图对象（就地修改）。
    :param stub_dirs: 桩搜索目录列表，高优先级在前。
    :param method_call_path: 方法调用关系文件路径，用于接边。
    :return: 本次注入（新建或替换）的桩数量；无桩库或全部跳过时为 0。
    """
    stubs = load_stub_definitions(stub_dirs)
    if not stubs:
        return 0

    injected = 0
    for stub in stubs.values():
        existing = project.find_header(stub.class_name)
        if existing is not None and not existing.is_manual_stub() and not existing.is_generated_external():
            # Java 优先：闭包中已有同名 Java 类时桩不生效
            print(f"[manual_stub] {stub.class_name} 已有 Java 节点，跳过手写桩")
            continue
        if existing is not None and existing.is_generated_external():
            print(f"[manual_stub] {stub.class_name} 替换 generated_external 占位为手写桩")
        if existing is None:
            existing = Header(stub.class_name, "")
            project.headers.append(existing)
            injected += 1
        elif existing.is_generated_external():
            injected += 1
        _apply_stub(existing, stub)

    # 接边 + 重分层（含新建与刷新的桩方法）
    _rewire_and_relayer(project, method_call_path)
    return injected


def _apply_stub(header: Header, stub: StubDef) -> None:
    """把桩定义写入 Header 节点并重建其 Method 子节点。

    :param header: 目标图节点（新建或被替换/刷新的节点）。
    :param stub: 桩定义。
    """
    # 替换 generated_external 时，其旧方法节点（LLM 占位解析产物）整体作废
    drop_all_methods = header.is_generated_external()
    header.source_kind = MANUAL_STUB_KIND
    header.translated_code = stub.header_code
    header.translated_class_name = stub.class_name.replace("$", "::")
    header.latest_compile_status = "success"
    header.stub_cpp_code = stub.cpp_code

    # 重建方法节点：摘除旧桩方法（刷新时）或全部旧方法（替换 generated_external 时）
    if drop_all_methods:
        header.methods = []
    else:
        header.methods = [m for m in header.methods if m.source_tag != MANUAL_STUB_SOURCE_TAG]
    existing_keys = {m.key for m in header.methods}
    for method_def in stub.methods:
        if method_def.java_signature in existing_keys:
            continue
        method = Method(method_def.java_signature, "", MANUAL_STUB_SOURCE_TAG, header)
        method.translated_declaration = method_def.cpp_declaration
        method.mapped_cpp_definition = method_def.cpp_declaration
        method.mapping_status = "already_implemented"
        method.skip_translation = True
        method.skip_translation_reason = "manual_stub: 手写桩，实现由模块提供"
        method.method_body_location = method_def.body_location
        method.implemented_in_header = method_def.body_location == "header"
        header.methods.append(method)
        existing_keys.add(method.key)


def _rewire_and_relayer(project: Project, method_call_path: Path) -> None:
    """重跑调用边构建并按最新节点集合重分层。

    build_call_graph 基于集合语义，重跑幂等；桩方法进入 method_nodes 后，
    Java 调用方到桩方法的 children/parents 边才能建立（callee 缺失时不建边）。

    :param project: 目标项目图对象（就地修改）。
    :param method_call_path: 方法调用关系文件路径。
    """
    # 同 key 重载取首个实例参与接边（与 Project.load 的口径一致）
    all_methods: Dict[str, List[Method]] = {}
    for header in project.headers:
        for method in header.methods:
            all_methods.setdefault(method.key, []).append(method)
    methods_by_key = {key: methods[0] for key, methods in all_methods.items()}

    method_call_path = Path(method_call_path)
    if method_call_path.is_file():
        build_call_graph(str(method_call_path), methods_by_key, io.StringIO())
    else:
        print(f"[manual_stub] 警告: 未找到 method_call 文件 {method_call_path}，跳过接边")

    # 分层输入用伪 key 补充同 key 重载实例，与 Project.load 保持一致
    ordered_input: dict = dict(methods_by_key)
    for key, methods in all_methods.items():
        for dup_index, dup_method in enumerate(methods[1:], start=1):
            ordered_input[f"{key}#dup{dup_index}"] = dup_method
    project.methods = get_ordered_method_groups(ordered_input)
