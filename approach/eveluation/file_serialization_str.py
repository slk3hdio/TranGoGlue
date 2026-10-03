"""
基于字符串处理的C++代码序列化器（使用Project graph数据）

不再使用LLM解析.cpp文件，而是直接从Method和Header对象中提取结构化数据。
"""
import json
import re
from pathlib import Path
from typing import List, Dict, Optional, Any
import sys

# 添加项目路径
p_dir = str(Path(__file__).parent)
pp_dir = str(Path(__file__).parent.parent)
if pp_dir not in sys.path:
    sys.path.append(pp_dir)
if p_dir not in sys.path:
    sys.path.append(p_dir)

from graph import Header, Method, Project
from path_config import cfg_graph_dir_path, cfg_eval_dir_path, cfg_all_project_names, cfg_run_graph_dir, cfg_best_run_id


class CPPCodeSerializer:
    """
    基于Method和Header对象的C++代码序列化器

    利用翻译过程中保存的结构化数据，避免重新解析C++代码
    """

    # 正则表达式：匹配函数定义（支持多行）
    # 匹配模式：[返回类型] 类名::方法名(参数列表) [const] [{ 或 换行 + {]
    # 注意：构造函数/析构函数没有返回类型
    _FUNCTION_DEF_RE = re.compile(
        r'(?:^|\n)\s*'  # 行首或换行后
        r'(?P<template>template\s*<[^>]+>\s*)?'  # 可选的模板声明
        r'(?:(?P<return_type>[\w\s:*&<>]+?)\s+)?'  # 可选的返回类型（非贪婪），构造函数没有
        r'(?P<class_name>[\w<>:]+)::(?P<method_name>~?[\w]+)\s*'  # 类名::方法名（支持模板类如 Class<T>::method）
        r'\((?P<params>[^)]*?)\)\s*'  # 参数列表（非贪婪）
        r'(?:const\s*)?'  # 可选的const
        r'(?:noexcept\s*)?'  # 可选的noexcept
        r'(?:override\s*)?'  # 可选的override
        r'(?:final\s*)?'  # 可选的final
        r'(?:->\s*[\w\s:*&<>]+)?'  # 可选的trailing return type
        r'(?:\s*:\s*[^{]+)?'  # 可选的构造函数初始化列表（匹配 : 到 { 之间的内容，但不捕获）
        r'\s*\{',  # 开始大括号
        re.MULTILINE | re.DOTALL
    )

    # 正则：匹配include语句
    _INCLUDE_RE = re.compile(r'^\s*#include\s+["<]([^">]+)[">]\s*$', re.MULTILINE)

    # 正则：匹配静态成员变量声明（从头文件代码中提取）
    _STATIC_DECLARATION_RE = re.compile(
        r'^\s*static\s+(?!inline\b)(?!constexpr\b)(?!consteval\b)(?!constinit\b)(?P<body>[^;]+);',
        re.MULTILINE
    )

    # 正则：匹配构造函数初始化列表
    _CTOR_INIT_LIST_RE = re.compile(
        r'(?:^|\n)\s*'
        r'(template\s*<[^>]+>\s*)?'
        r'(?P<class_name>[\w:]+)::(?P=class_name)\s*'  # 构造函数：ClassName::ClassName
        r'\([^)]*\)\s*'
        r'(?::\s*[^\{]*)?'  # 初始化列表
        r'\{',
        re.MULTILINE | re.DOTALL
    )

    def __init__(self, project: Project):
        """
        初始化序列化器

        Args:
            project: Project对象，包含所有Header和Method
        """
        self.project = project

    def serialize_all(self) -> Dict[str, dict]:
        """
        序列化项目中所有类的.cpp文件

        Returns:
            Dict[file_name, serialized_data]
        """
        result = {}
        for header in self.project.headers:
            if header.type == 'interface':
                continue
            serialized = self._serialize_header(header)
            if serialized:
                result[serialized['file_name']] = serialized
        return result

    def _serialize_header(self, header: Header) -> Optional[dict]:
        """
        序列化单个Header（类）对应的.cpp文件

        Args:
            header: Header对象

        Returns:
            序列化后的字典，或None（如果无方法代码）
        """
        functions = []
        all_includes = set()

        for method in header.methods:
            func_data = self._serialize_method(method, header.key)
            if func_data:
                functions.append(func_data)
                # 从方法代码中提取include
                includes = self._extract_includes(method.translated_code)
                all_includes.update(includes)
                all_includes.add(header.get_output_header_name())  # 默认包含对应的头文件

        if not functions:
            return None

        output_header_name = header.get_output_header_name()

        # 从header代码中提取静态成员变量
        variables = self._extract_static_variables(header)

        return {
            "file_name": Path(output_header_name).stem + '.cpp',
            "includes": sorted(list(all_includes)),
            "variables": variables,
            "functions": functions
        }

    def _serialize_method(self, method: Method, class_name: str) -> Optional[dict]:
        """
        序列化单个Method为函数对象

        Args:
            method: Method对象
            class_name: 所属类名

        Returns:
            函数序列化字典，或None（如果无翻译代码）
        """
        if not method.translated_code or not method.translated_code.strip():
            return None

        # 解析函数签名
        signature = self._parse_function_signature(method.translated_code, class_name)

        # 清理function_code：删除#include语句
        function_code = self._remove_includes(method.translated_code)

        return {
            "signature": signature,
            "function_code": function_code,
            # "success": not method.errors or len(method.errors) == 0,
            "log_output": method.compile_output if method.compile_output else ""
        }

    def _parse_function_signature(self, code: str, class_name: str) -> str:
        """
        从方法代码中解析函数签名

        将完整函数定义转换为简化的签名格式：ClassName::methodName(params)

        Args:
            code: 方法C++代码
            class_name: 类名

        Returns:
            简化的函数签名
        """
        code = code.strip()

        # 处理模板函数
        template_prefix = ""
        template_match = re.match(r'^(template\s*<[^>]+>)\s*', code)
        if template_match:
            template_prefix = template_match.group(1)
            code = code[template_match.end():].strip()

        constructor_signature = self._parse_constructor_signature(code, class_name, template_prefix)
        if constructor_signature:
            return constructor_signature

        # 匹配函数定义
        match = self._FUNCTION_DEF_RE.match('\n' + code)
        if match:
            method_name = match.group('method_name')
            params = match.group('params').strip()
            sig_class_name = match.group('class_name')
            sig_return_type = match.group('return_type')
            sig_template = match.group('template')

            # 构建签名
            # 对于构造函数/析构函数，没有返回类型（类名::类名或类名::~类名）
            # 对于普通函数，需要包含返回类型
            is_ctor_or_dtor = method_name == sig_class_name.split('::')[-1] or method_name.startswith('~')

            if is_ctor_or_dtor:
                signature = f"{sig_class_name}::{method_name}({params})"
            else:
                if sig_return_type:
                    signature = f"{sig_return_type.strip()} {sig_class_name}::{method_name}({params})"
                else:
                    signature = f"{sig_class_name}::{method_name}({params})"

            if sig_template:
                signature = f"{sig_template.strip()} {signature}"

            return signature.strip()

        # 如果正则匹配失败，尝试简单提取
        # 寻找 "类名::方法名("
        simple_pattern = re.search(
            rf'{re.escape(class_name)}(?:<[^>]+>)?::([~\w]+)\s*\(([^)]*)\)',
            code
        )
        if simple_pattern:
            method_name = simple_pattern.group(1)
            params = simple_pattern.group(2).strip()
            class_name_match = re.search(
                rf'({re.escape(class_name)}(?:<[^>]+>)?)::[~\w]+\s*\(',
                code
            )
            qualified_class_name = class_name_match.group(1) if class_name_match else class_name
            return f"{qualified_class_name}::{method_name}({params})"

        # 最后尝试：找到第一个{之前的部分作为签名
        brace_idx = code.find('{')
        if brace_idx > 0:
            sig = code[:brace_idx].strip()
            # 移除返回类型（最后的类型名）
            lines = sig.split('\n')
            last_line = lines[-1].strip()
            # 尝试找到 ::methodName( 模式
            match = re.search(r'([\w:]+::~?[\w]+\s*\([^)]*\))', last_line)
            if match:
                return match.group(1)
            return last_line

        # 无法解析，返回前100字符
        return code[:100].replace('\n', ' ')

    def _parse_constructor_signature(self, code: str, class_name: str, template_prefix: str) -> Optional[str]:
        constructor_pattern = re.compile(
            rf'^(?P<class_name>{re.escape(class_name)}(?:<[^>]+>)?)::(?P<method_name>~?[\w]+)\s*'
            r'\((?P<params>[^)]*)\)\s*'
            r'(?:\:\s*[^\{{]*)?'
            r'\{{',
            re.DOTALL
        )
        match = constructor_pattern.match(code)
        if not match:
            return None

        qualified_class_name = match.group('class_name')
        method_name = match.group('method_name')
        params = match.group('params').strip()
        signature = f"{qualified_class_name}::{method_name}({params})"
        if template_prefix:
            signature = f"{template_prefix} {signature}"
        return signature

    def _extract_includes(self, code: str) -> List[str]:
        """
        从代码中提取#include语句

        Args:
            code: C++代码

        Returns:
            include文件名列表
        """
        if not code:
            return []
        matches = self._INCLUDE_RE.findall(code)
        return list(matches)

    def _remove_includes(self, code: str) -> str:
        """
        从代码中删除#include语句

        Args:
            code: C++代码

        Returns:
            删除#include后的代码
        """
        if not code:
            return ""
        # 按行分割，过滤掉#include行，再重新组合
        lines = code.split('\n')
        filtered_lines = [
            line for line in lines
            if not self._INCLUDE_RE.match(line.strip())
        ]
        return '\n'.join(filtered_lines).strip()

    def _extract_static_variables(self, header: Header) -> List[dict]:
        """
        从头文件代码中提取静态成员变量声明，并转换为变量定义格式

        Args:
            header: Header对象

        Returns:
            变量定义列表
        """
        variables = []

        if not header.translated_code:
            return variables

        # 查找static成员声明
        for match in self._STATIC_DECLARATION_RE.finditer(header.translated_code):
            body = match.group('body').strip()

            # 跳过函数声明（包含括号）
            if '(' in body or ')' in body:
                continue

            # 解析变量名和初始化值
            # 格式如: "static const int MAX_SIZE = 100;" 或 "static std::string name;"
            var_match = re.search(
                r'([\w\s:*&<>]+?)\s+'  # 类型
                r'([\w]+)'  # 变量名
                r'(?:\s*\[[^\]]*\])?'  # 可选数组下标
                r'(?:\s*=\s*(.+))?$',  # 可选初始值
                body
            )

            if var_match:
                var_type = var_match.group(1).strip()
                var_name = var_match.group(2)
                initializer = var_match.group(3) if var_match.group(3) else ""

                # 生成变量定义代码（类名::变量名）
                qualified_name = f"{header.translated_class_name}::{var_name}"
                if initializer:
                    var_code = f"{var_type} {qualified_name} = {initializer};"
                else:
                    var_code = f"{var_type} {qualified_name};"

                variables.append({
                    "name": qualified_name,
                    "variable_code": var_code
                })

        return variables


def serialize_project_from_graph(
    ai_name: str,
    project_name: str,
    version: str,
    run_id: str = "",
) -> Dict[str, dict]:
    """
    从Project graph加载并序列化整个项目

    Args:
        ai_name: AI名称
        project_name: 项目名称
        version: 版本
        run_id: 可选。v4_7+ 结构下指定 run id；为空时自动使用最新 run。

    Returns:
        所有.cpp文件的序列化数据
    """
    graph_dir = _resolve_graph_dir(ai_name, project_name, version, run_id)

    if not graph_dir.exists():
        raise FileNotFoundError(f"Graph directory not found: {graph_dir}")

    # 加载Project
    project = Project.load(graph_dir)

    # 创建序列化器并执行
    serializer = CPPCodeSerializer(project)
    return serializer.serialize_all()


def _resolve_graph_dir(ai_name: str, project_name: str, version: str, run_id: str = "") -> Path:
    """v4_7+ 使用 run 目录下的 graph；旧版本使用扁平 graph 目录。"""
    latest_run = _resolve_run_id(ai_name, project_name, version, run_id)
    if latest_run:
        return cfg_run_graph_dir(ai_name, project_name, version, latest_run)
    return cfg_graph_dir_path(ai_name, project_name, version)


def _resolve_run_id(ai_name: str, project_name: str, version: str, run_id: str = "") -> str:
    """返回实际使用的 run id；v4_7+ 且未指定时取编译成功率最高的 run，旧版本返回空字符串。"""
    if run_id:
        return run_id
    best = cfg_best_run_id(ai_name, project_name, version)
    return best or ""


def save_serialized_files(
    ai_name: str,
    project_name: str,
    version: str,
    serialized_data: Dict[str, dict]
) -> None:
    """
    将序列化数据保存到eval目录

    Args:
        ai_name: AI名称
        project_name: 项目名称
        version: 版本
        serialized_data: 序列化数据
    """
    eval_dir = cfg_eval_dir_path(ai_name, project_name, version)
    eval_dir.mkdir(parents=True, exist_ok=True)

    for file_name, data in serialized_data.items():
        json_file = eval_dir / file_name.replace('.cpp', '.json')
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        print(f"Serialized {file_name} -> {json_file}")


def serialize_all_projects(ai_name: str, version: str, force: bool = False) -> None:
    """
    序列化指定AI和版本的所有项目

    Args:
        ai_name: AI名称
        version: 版本
        force: 是否强制重新序列化（即使已有结果）
    """
    for project_name in cfg_all_project_names(version):
        eval_dir = cfg_eval_dir_path(ai_name, project_name, version)

        # 检查是否已有结果
        if not force and eval_dir.exists() and any(eval_dir.iterdir()):
            print(f"Skipping {ai_name}/{project_name}/{version} (already serialized)")
            continue

        try:
            print(f"Serializing {ai_name}/{project_name}/{version}...")
            serialized = serialize_project_from_graph(ai_name, project_name, version)
            save_serialized_files(ai_name, project_name, version, serialized)
            print(f"  -> Serialized {len(serialized)} files")
        except FileNotFoundError as e:
            print(f"  -> Skipped: {e}")
        except Exception as e:
            print(f"  -> Error: {e}")


if __name__ == "__main__":
    # 示例：序列化单个项目
    # result = serialize_project_from_graph("deepseek", "Cookie", "v4_1")
    # print(json.dumps(list(result.values())[0], indent=2))

    # 序列化所有项目
    for version in ['v4_1']:
        for ai_name in ['deepseek', 'qwen', 'gpt']:
            serialize_all_projects(ai_name, version)
