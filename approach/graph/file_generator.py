import os
import re
import json
from pathlib import Path
from typing import List

from . import Header, Project
# from path_config import cfg_translate_result_dir_path


class FileGenerator:
    """Generate final .h and .cpp files."""

    _STATIC_DECLARATION_RE = re.compile(
        r"^\s*static\s+(?!inline\b)(?!constexpr\b)(?!consteval\b)(?!constinit\b)(?P<body>[^;]+);(?:\s*//.*)?$"
    )
    _STATIC_NAME_RE = re.compile(r"(?P<name>[A-Za-z_]\w*)\s*(?:\[[^\]]*\])?\s*(?:=\s*.+)?$")

    def generate_files(self, ai_name:str, project_name:str, version:str, output_dir:Path, project:Project|None=None) -> None:
        """
        生成指定项目的 C++ 头文件(.h)和源文件(.cpp)。

        职责：
        - 若未显式传入 project，则根据 ai_name/project_name/version 从数据源加载 Project。
        - 先清空并重新生成所有头文件产物（.h/.cpp/.hpp 及临时文件）。
        - 再按需为每个 header 生成对应的 .cpp 文件。
        - 若图中没有任何已翻译头文件，则跳过生成以保护已有产物。

        Args:
            ai_name: AI 名称标识。
            project_name: 项目名称。
            version: 版本标识。
            output_dir: 输出目录路径。
            project: 可选的项目对象；为 None 时自动加载。

        Returns:
            None。
        """
        print("Generating C++ files...")

        if project is None:
            project = Project.load_from_source(ai_name, project_name, version)
        headers: List[Header] = project.headers

        # 防护：图中没有任何已翻译头文件时（如不兼容的 baseline 图），
        # 拒绝重新生成，避免清空 output_dir 里已有的产物。
        if not any(header.translated_code.strip() for header in headers):
            print(f"warning: no translated headers in graph, skip file generation to protect existing files in {output_dir}")
            return

        self.generate_header_artifacts(headers, str(output_dir))

        for header in headers:
            if self._should_generate_cpp_file(header):
                self._generate_cpp_file(header, str(output_dir))

        print(f"Generated C++ files for {len(headers)} classes.")

    def generate_header_artifacts(self, headers: List[Header], output_dir: str) -> None:
        """
        清空并重新生成所有头文件相关的产物。

        职责：
        - 删除 output_dir 中已有的 .h / .cpp / .hpp 文件。
        - 为每个 header 生成对应的头文件。
        - 生成所需的临时文件。

        Args:
            headers: 待生成产物的 Header 列表。
            output_dir: 输出目录路径。

        Returns:
            None。
        """
        for file in Path(output_dir).iterdir():
            if file.is_file():
                suffix = file.suffix
                if suffix == '.h' or suffix == '.cpp' or suffix == '.hpp':
                    file.unlink()
        for header in headers:
            self._generate_header_file(header, output_dir)
        self._generate_temp_files(headers, output_dir)

    def _should_generate_cpp_file(self, header: Header) -> bool:
        """
        判断给定 header 是否需要生成对应的 .cpp 文件。

        规则：
        - 外部占位头：仅当存在需要 cpp 实现且已翻译的方法时生成。
        - 模板头：不生成独立的 .cpp 文件。
        - interface 类型：仅当存在已翻译的非模板方法时生成。
        - 其他类型：默认生成。

        Args:
            header: 待判断的 Header 对象。

        Returns:
            bool，是否应生成 .cpp 文件。
        """
        if header.is_manual_stub():
            # 手写桩：仅当桩定义提供了配套 cpp 实现时才生成对应文件。
            return bool(header.stub_cpp_code and header.stub_cpp_code.strip())
        if header.is_generated_external():
            # 外部占位头只在有方法需要 cpp 实现时才生成对应文件。
            return any(
                method.method_body_location == "cpp" and method.translated_code.strip()
                for method in header.methods
            )
        if self._is_template_header(header):
            return False

        if header.type != 'interface':
            return True

        for method in header.methods:
            if method.is_template_method:
                continue
            if method.translated_code.strip():
                return True
        return False

    def _generate_header_file(self, header: Header, output_dir: str) -> None:
        """
        为单个 header 生成头文件(.h)。

        职责：
        - 从 header.translated_code 中提取 #include 行，并过滤掉对自身的包含。
        - 将模板方法的实现代码合并到对应位置（含模板类时）。
        - 将最终内容以 UTF-8 编码写入 output_dir 下的头文件。

        Args:
            header: 待生成头文件的 Header 对象。
            output_dir: 输出目录路径。

        Returns:
            None。
        """
        header_path = Path(output_dir) / header.get_output_header_name()
        header_includes = []
        header_code = ""
        template_method_code_parts: List[str] = []
        route_all_method_code_to_header = self._is_template_header(header)
        self_include = f'"{header.get_output_header_name()}"'

        for line in header.translated_code.split('\n'):
            if line.startswith('#include'):
                if line.strip() not in header_includes and self_include not in line: # 头文件里不能包含自己
                    header_includes.append(line.strip())
            else:
                header_code += line + '\n'

        for method in header.methods:
            if not method.translated_code:
                continue
            if not route_all_method_code_to_header and not method.is_template_method:
                continue

            for line in method.translated_code.split('\n'):
                if line.startswith('#include'):
                    if line.strip() not in header_includes and self_include not in line: # 头文件里不能包含自己
                        header_includes.append(line.strip())
                else:
                    template_method_code_parts.append(line)

        header_code = self._append_template_methods_to_header_code(
            header_code,
            '\n'.join(template_method_code_parts).strip(),
        )

        with open(header_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(header_includes))
            f.write('\n\n')
            f.write(header_code)

    def _generate_cpp_file(self, header: Header, output_dir: str) -> None:
        """
        为单个 header 生成源文件(.cpp)。

        职责：
        - 收集 header.methods 中需要放入 cpp 的方法实现代码（跳过模板方法）。
        - 合并其中出现的 #include 行，避免重复并确保包含自身头文件。
        - 追加缺失的静态成员定义。
        - 若最终无代码，则跳过写入并给出警告。

        Args:
            header: 待生成 cpp 的 Header 对象。
            output_dir: 输出目录路径。

        Returns:
            None。
        """
        cpp_path = Path(output_dir) / header.get_output_cpp_name()
        cpp_includes = [f'#include "{header.get_output_header_name()}"']
        cpp_code_parts: List[str] = []

        for method in header.methods:
            if method.is_template_method:
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
            print(f"warning: {header.file_name} has no translated code")
            return

        with open(cpp_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(cpp_includes))
            f.write('\n\n')
            f.write(cpp_code)
            f.write('\n')

    def _extract_static_member_definitions(self, header: Header) -> List[str]:
        """
        从 header 的翻译后代码中提取静态成员的定义。

        职责：
        - 扫描 header.translated_code 中形如 `static xxx name;` 的静态成员声明。
        - 忽略包含函数调用括号或位于预处理指令行的内容。
        - 构造 `声明前缀 类名::成员名 后缀;` 形式的类外定义。

        Args:
            header: 待提取静态成员定义的 Header 对象。

        Returns:
            List[str]，静态成员定义的声明行列表。
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
                suffix_before_init, initializer_value = member_suffix.split('=', 1)
                member_suffix = suffix_before_init.strip()
                initializer = ' = ' + initializer_value.strip()

            qualified_name = f'{header.key}::{member_name}{member_suffix}'
            static_definitions.append(f'{declaration_prefix} {qualified_name}{initializer};')

        return static_definitions

    def _has_existing_static_definition(self, cpp_code: str, header: Header, definition: str) -> bool:
        """
        判断给定的静态成员定义是否已经存在于 cpp 代码中。

        职责：
        - 从 definition 中解析出类名和成员名。
        - 在 cpp_code 中匹配 `类名::成员名` 的已有定义（可能带数组下标或初始化）。

        Args:
            cpp_code: 现有的 cpp 代码内容。
            header: 关联的 Header 对象。
            definition: 待检查的静态成员定义字符串。

        Returns:
            bool，若已存在则该返回 True。
        """
        member_match = re.search(rf"{re.escape(header.key)}::([A-Za-z_]\w*)", definition)
        if not member_match:
            return False

        member_name = member_match.group(1)
        pattern = re.compile(
            rf"\b{re.escape(header.key)}::{re.escape(member_name)}\b(?:\s*\[[^\]]*\])?\s*(?:=|;|\()"
        )
        return bool(pattern.search(cpp_code))

    def _generate_static_member_definitions(self, header: Header, cpp_code: str) -> List[str]:
        """
        生成尚未在 cpp 代码中存在的静态成员定义。

        职责：
        - 调用 _extract_static_member_definitions 提取候选定义。
        - 过滤掉已在 cpp_code 中出现的定义，避免重复。

        Args:
            header: 关联的 Header 对象。
            cpp_code: 现有的 cpp 代码内容。

        Returns:
            List[str]，需要补充的静态成员定义列表。
        """
        static_definitions: List[str] = []
        for definition in self._extract_static_member_definitions(header):
            if self._has_existing_static_definition(cpp_code, header, definition):
                continue
            static_definitions.append(definition)
        return static_definitions

    def _generate_temp_files(self, headers: List[Header], temp_dir: str) -> None:
        """
        生成所需的临时头文件。

        职责：
        - 汇总各 header 的 external_header_files 中的外部头文件内容。
        - 跳过与项目内头文件重名的文件。
        - 以 UTF-8 编码将内容写入 temp_dir。

        Args:
            headers: Header 列表。
            temp_dir: 临时文件输出目录。

        Returns:
            None。
        """
        temp_files = {}
        project_header_file_names = {header.get_output_header_name() for header in headers}
        for header in headers:
            for file_name, file_content in header.external_header_files.items():
                if file_content:
                    if file_name in project_header_file_names:
                        continue
                    temp_files[os.path.join(temp_dir, file_name)] = file_content

        for file_path, file_content in temp_files.items():
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(file_content)

        print(f"Generated {len(temp_files)} temporary files.")

    def _is_template_header(self, header: Header) -> bool:
        """
        判断 header 是否为模板头文件。

        职责：
        - 解析 header.translate_scheme 中的 JSON，检查 header_role.is_template 标记。
        - 解析失败或 scheme 为空时返回 False。

        Args:
            header: 待判断的 Header 对象。

        Returns:
            bool，若为模板头则返回 True。
        """
        if not header.translate_scheme.strip():
            return False

        try:
            scheme_dict = json.loads(header.translate_scheme)
        except json.JSONDecodeError:
            return False

        header_role = scheme_dict.get("header_role", {})
        return bool(header_role.get("is_template"))

    def _append_template_methods_to_header_code(self, header_code: str, template_method_code: str) -> str:
        """
        将模板方法的实现代码合并到头文件代码中。

        职责：
        - 若无模板方法代码，直接返回原头文件代码。
        - 若头文件存在 #endif，则将模板方法代码插入到 #endif 之前；否则追加到末尾。

        Args:
            header_code: 现有头文件代码。
            template_method_code: 待合并的模板方法实现代码（可能为空）。

        Returns:
            str，合并后的头文件代码。
        """
        if not template_method_code:
            return header_code

        if header_code and not header_code.endswith('\n'):
            header_code += '\n'

        lines = header_code.splitlines()
        endif_index = None
        for idx, line in enumerate(lines):
            if line.strip().startswith('#endif'):
                endif_index = idx
                break

        block_lines = template_method_code.splitlines()
        if endif_index is None:
            if lines and lines[-1].strip():
                lines.append("")
            lines.extend(block_lines)
            return '\n'.join(lines) + '\n'

        insertion = []
        if endif_index > 0 and lines[endif_index - 1].strip():
            insertion.append("")
        insertion.extend(block_lines)
        if block_lines and (endif_index >= len(lines) or lines[endif_index].strip()):
            insertion.append("")

        updated_lines = lines[:endif_index] + insertion + lines[endif_index:]
        return '\n'.join(updated_lines) + '\n'
