from __future__ import annotations

import re
from pathlib import Path
from typing import List

from graph import Header, Method
from graph.file_generator import FileGenerator


class BoundedFileGenerator(FileGenerator):
    """带保护逻辑的文件生成器，避免 method 在 .h/.cpp 间放错位置。"""

    def _generate_header_file(self, header: Header, output_dir: str) -> None:
        """生成头文件（.h）并写入磁盘。

        收集 pragma once、include 与正文行，并将需放入头文件的 method
        代码规范化后追加到头部代码中，最终以 UTF-8 编码写入 output_dir。

        :param header: 待生成头文件的 Header 对象。
        :param output_dir: 输出目录。
        """
        header_path = Path(output_dir) / header.get_output_header_name()
        pragma_lines: List[str] = []
        header_includes: List[str] = []
        body_lines: List[str] = []
        template_method_code_parts: List[str] = []
        route_all_method_code_to_header = self._is_template_header(header)
        self_include = f'"{header.get_output_header_name()}"'

        for line in header.translated_code.split('\n'):
            stripped = line.strip()
            if stripped.startswith('#pragma once'):
                if '#pragma once' not in pragma_lines:
                    pragma_lines.append('#pragma once')
            elif line.startswith('#include'):
                if line.strip() not in header_includes and self_include not in line:
                    header_includes.append(line.strip())
            else:
                body_lines.append(line)

        for method in header.methods:
            if not method.translated_code:
                continue
            if not self._should_emit_method_in_header(method, route_all_method_code_to_header):
                continue

            # method 翻译可能带上 include 或重复 namespace，这里做一次轻量规范化，
            # 保证最终拼到头文件里的内容尽量稳定。
            normalized_method_code = self._normalize_header_method_code(header, method.translated_code)
            for line in normalized_method_code.split('\n'):
                if line.startswith('#include'):
                    if line.strip() not in header_includes and self_include not in line:
                        header_includes.append(line.strip())
                else:
                    template_method_code_parts.append(line)

        body = '\n'.join(body_lines).strip('\n')
        header_code_parts: List[str] = []
        header_code_parts.extend(pragma_lines or ['#pragma once'])
        if header_includes:
            header_code_parts.append("")
            header_code_parts.extend(header_includes)
        if body:
            header_code_parts.append("")
            header_code_parts.append(body)

        header_code = '\n'.join(header_code_parts) + '\n'
        header_code = self._append_header_only_methods_to_header_code(
            header_code,
            '\n'.join(template_method_code_parts).strip(),
        )

        with open(header_path, 'w', encoding='utf-8') as f:
            f.write(header_code)

    def _generate_cpp_file(self, header: Header, output_dir: str) -> None:
        """生成实现文件（.cpp）并写入磁盘。

        依据 method 的位置与模板类型决定哪些方法应落在 cpp 中，收集对应
        的 include 与代码正文，并附加静态成员定义；若最终无任何代码则
        不生成文件。

        :param header: 待生成实现文件的 Header 对象。
        :param output_dir: 输出目录。
        """
        # 手写桩：配套 cpp 实现为人工编写的完整文件，逐字写出，不走方法拼装。
        if header.is_manual_stub():
            if header.stub_cpp_code and header.stub_cpp_code.strip():
                cpp_path = Path(output_dir) / header.get_output_cpp_name()
                with open(cpp_path, 'w', encoding='utf-8') as f:
                    f.write(header.stub_cpp_code.strip() + '\n')
            return

        cpp_path = Path(output_dir) / header.get_output_cpp_name()
        cpp_includes = [f'#include "{header.get_output_header_name()}"']
        cpp_code_parts: List[str] = []
        route_all_method_code_to_header = self._is_template_header(header)

        for method in header.methods:
            if not self._should_emit_method_in_cpp(method, route_all_method_code_to_header):
                continue
            if method.translated_code == "":
                if method.skip_translation:
                    continue
                print(f"warning: {method.file_name} has no translated code")
                continue

            for line in method.translated_code.split('\n'):
                if line.startswith('#include'):
                    if line.strip() not in cpp_includes:
                        cpp_includes.append(line.strip())
                else:
                    cpp_code_parts.append(line)

        existing_cpp_code = '\n'.join(cpp_code_parts)
        static_member_definitions = self._generate_static_member_definitions(header, existing_cpp_code)
        if static_member_definitions:
            if existing_cpp_code.strip():
                cpp_code_parts.append("")
            cpp_code_parts.extend(static_member_definitions)

        cpp_code = '\n'.join(cpp_code_parts).strip()
        if cpp_code == "":
            return

        with open(cpp_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(cpp_includes))
            f.write('\n\n')
            f.write(cpp_code)
            f.write('\n')

    def _extract_static_member_definitions(self, header: Header) -> List[str]:
        """从 header 翻译代码中提取静态成员定义。

        通过静态声明正则匹配类内静态成员声明，跳过函数体与含初始化器的
        声明，生成带类限定名的定义字符串列表。

        :param header: 待提取静态成员定义的 Header 对象。
        :return: 静态成员定义字符串列表。
        """
        static_definitions: List[str] = []
        for raw_line in header.translated_code.splitlines():
            line = raw_line.strip()
            if not line or line.startswith('#'):
                continue

            match = self._STATIC_DECLARATION_RE.match(line)
            if not match:
                continue

            body = match.group('body').strip()
            if '(' in body or ')' in body:
                continue

            name_match = self._STATIC_NAME_RE.search(body)
            if not name_match:
                continue

            member_name = name_match.group('name')
            declaration_prefix = body[:name_match.start('name')].rstrip()
            member_suffix = body[name_match.end('name'):].strip()
            initializer = ''
            if '=' in member_suffix:
                continue

            qualified_name = f'{header.key}::{member_name}{member_suffix}'
            static_definitions.append(f'{declaration_prefix} {qualified_name}{initializer};')

        return static_definitions

    def _should_emit_method_in_header(self, method: Method, route_all_method_code_to_header: bool) -> bool:
        """判断 method 是否应被放入头文件。

        :param method: 待判断的 Method 对象。
        :param route_all_method_code_to_header: 是否将全部方法代码路由到头文件。
        :return: 若 method 应放到头文件返回 True，否则返回 False。
        """
        # 头文件类内已有内联实现的方法不再追加类外定义，避免重复定义；
        # 与 _should_emit_method_in_cpp 中的同款检查保持对称。
        if self._is_defined_in_header(method):
            method.skip_translation = True
            method.skip_translation_reason = "method already has an inline header definition"
            return False
        if method.method_body_location == "header":
            return True
        if method.method_body_location in {"cpp", "none"}:
            return False
        if route_all_method_code_to_header:
            return True
        return self._is_template_method_like(method)

    def _should_emit_method_in_cpp(self, method: Method, route_all_method_code_to_header: bool) -> bool:
        """判断 method 是否应被放入 cpp 实现文件。

        依据方法体位置、模板方法特征及头文件内是否已有定义等条件决定，
        同时对某些被路由到头文件的方法回写 skip 状态以保持一致性。

        :param method: 待判断的 Method 对象。
        :param route_all_method_code_to_header: 是否将全部方法代码路由到头文件。
        :return: 若 method 应放到 cpp 返回 True，否则返回 False。
        """
        if method.method_body_location == "cpp":
            return True
        if method.method_body_location in {"header", "none"}:
            return False
        # 这些分支既决定最终文件落点，也同步回写 skip 状态，保持 graph 和产物一致。
        if route_all_method_code_to_header or self._is_template_method_like(method):
            method.skip_translation = True
            method.skip_translation_reason = "template method emitted in header"
            return False
        if self._is_defined_in_header(method):
            method.skip_translation = True
            method.skip_translation_reason = "method already has an inline header definition"
            return False
        if self._is_defaulted_or_deleted_in_header(method):
            method.skip_translation = True
            method.skip_translation_reason = "declaration is defaulted or deleted in header"
            return False
        return True

    def _is_defaulted_or_deleted_in_header(self, method: Method) -> bool:
        """检查 method 在头文件中是否被声明为 defaulted 或 deleted。

        :param method: 待检查的 Method 对象。
        :return: 若头文件中存在 ``= default`` 或 ``= delete`` 声明返回 True。
        """
        method_name = re.escape(method.get_name())
        pattern = re.compile(rf"\b{method_name}\s*\([^;{{}}]*\)\s*=\s*(default|delete)\s*;")
        return bool(pattern.search(method.header.translated_code or ""))

    def _is_defined_in_header(self, method: Method) -> bool:
        """检查 method 在头文件中是否已有完整的方法体定义。

        同时识别两种形态：类内的内联定义（含构造函数初始化列表）与
        ``ClassName::method`` 形式的类外定义。

        :param method: 待检查的 Method 对象。
        :return: 若头文件中存在对应方法体的定义返回 True。
        """
        header_code = method.header.translated_code or ""
        method_name = re.escape(method.get_name())
        class_names = {
            method.header.key.split("$")[-1],
            method.header.translated_class_name.split("::")[-1],
            method.header.translated_class_name,
        }
        for class_name in sorted(class_names, key=len, reverse=True):
            qualified_name = rf"{re.escape(class_name)}\s*::\s*{method_name}"
            # 类外定义：允许 template/inline 前缀。
            out_of_line = re.compile(
                rf"(?:template\s*<[^>]+>\s*)?(?:inline\s+)?[^;{{}}#]*\b{qualified_name}\s*\([^;{{}}]*\)\s*(?:const\s*)?(?:noexcept\s*)?(?:override\s*)?\{{",
                re.MULTILINE,
            )
            if out_of_line.search(header_code):
                return True
            # 类内内联定义：方法名后紧跟参数表与方法体，允许构造函数的初始化列表。
            in_class = re.compile(
                rf"(?:^|[^:.\w]){method_name}\s*\([^;{{}}]*\)\s*"
                rf"(?:const\s*)?(?:noexcept\s*)?(?:override\s*)?"
                rf"(?::\s*[^{{;]*)?\{{",
                re.MULTILINE,
            )
            if in_class.search(header_code):
                return True
        return False

    def _is_template_header(self, header: Header) -> bool:
        """判断 header 是否为模板头文件。

        在基类判断基础上，额外通过正则匹配 ``template <...> class/struct``
        结构来补全判断。

        :param header: 待判断的 Header 对象。
        :return: 若为模板头文件返回 True。
        """
        if super()._is_template_header(header):
            return True

        code = header.translated_code or ""
        return bool(re.search(r"\btemplate\s*<[^>]+>\s*(?:class|struct)\s+\w+", code))

    def _is_template_method_like(self, method: Method) -> bool:
        """判断 method 是否表现为模板方法。

        依据 method 的 is_template_method 标记或代码中以 template 开头的
        行进行判断。

        :param method: 待判断的 Method 对象。
        :return: 若为模板方法返回 True。
        """
        code = method.translated_code or ""
        return method.is_template_method or bool(re.search(r"^\s*template\s*<", code, re.MULTILINE))

    def _normalize_header_method_code(self, header: Header, code: str) -> str:
        """规范化需写入头文件的 method 代码。

        去除多余的 include 行，并移除包裹的命名空间块，返回清理后的代码。

        :param header: 所属的 Header 对象。
        :param code: 待规范化的 method 代码字符串。
        :return: 规范化后的代码字符串。
        """
        lines: List[str] = []
        namespace_name = self._single_namespace_name(header.translated_code or "")
        in_namespace_block = False
        namespace_depth = 0

        for raw_line in code.splitlines():
            stripped = raw_line.strip()
            if not stripped:
                lines.append(raw_line)
                continue
            if stripped.startswith('#include'):
                continue
            if namespace_name and re.match(rf"namespace\s+{re.escape(namespace_name)}\s*\{{", stripped):
                in_namespace_block = True
                namespace_depth = stripped.count("{") - stripped.count("}")
                continue
            if in_namespace_block:
                namespace_depth += stripped.count("{") - stripped.count("}")
                if (namespace_depth <= 0 and stripped == "}") or stripped.startswith("} // namespace"):
                    in_namespace_block = False
                    namespace_depth = 0
                    continue
            lines.append(raw_line)

        cleaned = "\n".join(lines).strip()
        return self._ensure_template_prefix(header, cleaned)

    def _ensure_template_prefix(self, header: Header, code: str) -> str:
        """为模板类的类外定义补全 ``template<...>`` 前缀。

        模板类的方法以类外定义形式写回头文件时必须携带类模板前缀，
        否则编译报 ``use of undeclared identifier``；方法代码已以
        ``template`` 开头时保持不变，避免重复添加。

        :param header: 所属的 Header 对象。
        :param code: 已清理的 method 代码字符串。
        :return: 必要时补全模板前缀后的代码。
        """
        if not code or not self._is_template_header(header):
            return code
        first_line = next((line.strip() for line in code.splitlines() if line.strip()), "")
        if first_line.startswith("template"):
            return code
        match = re.search(r"(template\s*<[^>]*>)\s*(?:class|struct)\s+\w+", header.translated_code or "")
        if match:
            return match.group(1) + "\n" + code
        return code

    def _append_header_only_methods_to_header_code(self, header_code: str, method_code: str) -> str:
        """将仅头文件方法代码追加到已有头部代码中。

        若头部代码中存在结尾的命名空间闭合标记，则在闭合标记前插入
        方法代码；否则回退到模板方法追加逻辑。

        :param header_code: 已有的头部代码。
        :param method_code: 待追加的方法代码。
        :return: 追加完成后的完整头部代码。
        """
        if not method_code:
            return header_code

        namespace_name = self._single_namespace_name(header_code)
        if namespace_name:
            close_match = list(re.finditer(rf"^\s*}}\s*//\s*namespace\s+{re.escape(namespace_name)}\s*$", header_code, re.MULTILINE))
            if close_match:
                match = close_match[-1]
                before = header_code[:match.start()].rstrip()
                after = header_code[match.start():].lstrip()
                return f"{before}\n\n{method_code}\n\n{after}"

        return self._append_template_methods_to_header_code(header_code, method_code)

    def _single_namespace_name(self, code: str) -> str:
        """提取代码中唯一的命名空间名称。

        :param code: 待分析的代码字符串。
        :return: 若存在唯一命名空间返回其名称，否则返回空字符串。
        """
        names = re.findall(r"^\s*namespace\s+([A-Za-z_]\w*)\s*\{", code or "", re.MULTILINE)
        unique_names: List[str] = []
        for name in names:
            if name not in unique_names:
                unique_names.append(name)
        return unique_names[0] if len(unique_names) == 1 else ""
