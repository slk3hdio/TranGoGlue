from pathlib import Path
from typing import Optional, LiteralString, Tuple, List, Literal
from utils.clean_filename import sanitize_filename  # 导入清洗逻辑
from typing import List, Dict, Any
from graph.method import Method
import json
import re

class Header:
    """
    表示一个头文件（类/接口/枚举）的图节点，是整个翻译图的核心数据结构。

    职责：
    - 保存头文件的结构信息（key、类型、源码、方法列表、字段、父类、接口、依赖等）。
    - 保存翻译过程的状态信息（翻译方案、翻译提示、翻译后的代码、编译结果、迭代信息等）。
    - 提供序列化（to_dict/save_to_file）与反序列化（_from_dict/_get_from_json）能力，支持持久化为 JSON。

    使用约定：
    - key 为头文件的唯一标识（类名，可能包含命名空间分隔符 $）。
    - methods 中保存该方法所属 Method 对象的 key 列表，在反序列化时需与 Method 关联。
    - 本类实例通常由 Project / retrieval_tools 创建并由 FileGenerator 消费。
    """
    def __init__(self, key:str, source_code: str):
        # 结构信息
        self.key = key
        # self.file_name = sanitize_filename(key)
        # self.include_name = self._default_include_name(key)
        self.source_kind = "java"  # java, generated_external, manual_stub
        # 手写桩配套 cpp 实现内容（仅 source_kind == "manual_stub" 时使用，随图持久化）
        self.stub_cpp_code = ""
        self.type = "" # class, interface, enum
        self.source_code = source_code
        self.methods:list[Method] = []
        self.imports = []
        self.fields:str = ""
        self.parent_class:str = ""
        self.interfaces:list[str]|list[LiteralString] = []
        self.generated_external_refs:list[str] = []
        self.generated_from_headers:list[str] = []
        self.include_dependencies:list[str] = []
        # self.external_classes:list[str] = []

        # 翻译信息
        self.translate_scheme_prompt = ""  # 翻译方案提示
        self.translate_scheme = ""  # 翻译方案
        self.scheme_round = 0
        self.scheme_history:list[Dict[str, Any]] = []

        self.translate_prompt = "" # 翻译提示
        self.translated_class_name = key.replace("$", "::")
        self.translated_code = ""  # 翻译后的代码
        self.translated_fields:list[str] = []
        self.header_translation_history:list[Dict[str, Any]] = []  # 翻译后的字段

        self.external_header_files:Dict[str, str] = {} #[file_name: file_content] 包含的其他头文件的文件名列表 (带.h后缀)(在翻译计划中生成file_name, 在正式翻译中生成file_content)
        self.pre_merge_external_classes:list[Dict[str, Any]] = []

        self.raw_translated_code = ""  # 未经过处理的翻译后的代码

        self.compile_output = ""  # 编译输出
        self.compile_reports:list[Dict[str, Any]] = []
        self.latest_compile_status = ""
        # 标注信息
        self.errors = []

        # 迭代信息
        self.iter_suggestion = []  # 迭代建议
        self.history_iter_suggestions:list[list[str]] = []  # 迭代建议历史记录

    def __eq__(self, other):
        """
        判断两个 Header 是否相等。

        比较依据：key 是否相同。

        Args:
            other: 待比较的 Header 对象。

        Returns:
            bool，key 相同则返回 True。
        """
        return self.key == other.key

    def to_dict(self):
        """
        将 Header 序列化为字典结构。

        职责：
        - 输出全部需要在 JSON 中持久化的字段，方法列表以 key 列表形式保存。

        Returns:
            dict，包含 Header 全部持久化字段的字典。
        """
        return {
            # 结构信息
            "key": self.key,
            # "file_name": self.file_name,    
            # "include_name": self.include_name,
            "source_kind": self.source_kind,
            "stub_cpp_code": self.stub_cpp_code,
            "type": self.type,
            "source_code": self.source_code,
            "methods": [method.key for method in self.methods],
            "imports": self.imports,
            "fields": self.fields,
            "parent_class": self.parent_class,
            "interfaces": self.interfaces,
            "generated_external_refs": self.generated_external_refs,
            "generated_from_headers": self.generated_from_headers,
            "include_dependencies": self.include_dependencies,
            # self.external_classes:list[str] = []

            # 翻译信息
            "translate_scheme_prompt": self.translate_scheme_prompt,  # 翻译方案提示
            "translate_scheme": self.translate_scheme,  # 翻译方案
            "scheme_round": self.scheme_round,
            "scheme_history": self.scheme_history,

            "translate_prompt": self.translate_prompt, # 翻译提示
            "translated_class_name": self.translated_class_name,
            "translated_code": self.translated_code,  # 翻译后的代码
            "translated_fields": self.translated_fields,
            "header_translation_history": self.header_translation_history,  # 翻译后的字段

            "external_header_files": self.external_header_files, #[file_name: file_content] 包含的其他头文件的文件名列表 (带.h后缀)(在翻译计划中生成file_name, 在正式翻译中生成file_content)
            "pre_merge_external_classes": self.pre_merge_external_classes,

            "raw_translated_code": self.raw_translated_code,  # 未经过处理的翻译后的代码

            "compile_output": self.compile_output,  # 编译输出
            "compile_reports": self._serialize_compile_reports(),
            "latest_compile_status": self.latest_compile_status,
            # 标注信息
            "errors": self.errors,

            # 迭代信息
            "iter_suggestion": self.iter_suggestion,  # 迭代建议
            "history_iter_suggestions": self.history_iter_suggestions,  # 迭代建议历史记录
        }

    def _from_dict(self, data: Dict[str, Any]):
        """
        从字典中反序列化 Header 的字段。

        职责：
        - 将 data 中保存的字段赋值回当前实例。
        - 对可选字段使用默认值兜底。

        Args:
            data: 由 to_dict 产生的字典。

        Returns:
            None。
        """
        # 结构信息
        self.key = data["key"]
        # self.file_name = sanitize_filename(self.key)
        # self.include_name = data.get("include_name", self._default_include_name(self.key))
        self.source_kind = data.get("source_kind", "java")
        self.stub_cpp_code = data.get("stub_cpp_code", "")
        self.type = data["type"] # class, interface, enum
        self.source_code = data["source_code"]
        self.methods = data["methods"]
        self.imports = data["imports"]
        self.fields = data["fields"]
        self.parent_class = data["parent_class"]
        self.interfaces = data["interfaces"]
        self.generated_external_refs = data.get("generated_external_refs", [])
        self.generated_from_headers = data.get("generated_from_headers", [])
        self.include_dependencies = data.get("include_dependencies", [])
        # self.external_classes:list[str] = []

        # 翻译信息
        self.translate_scheme_prompt = data["translate_scheme_prompt"]  # 翻译方案提示
        self.translate_scheme = data["translate_scheme"]  # 翻译方案
        self.scheme_round = data.get("scheme_round", 0)
        self.scheme_history = data.get("scheme_history", [])

        self.translate_prompt = data["translate_prompt"] # 翻译提示
        self.translated_class_name = data["translated_class_name"]
        self.translated_code = data["translated_code"]  # 翻译后的代码
        self.translated_fields = data["translated_fields"]
        self.header_translation_history = data.get("header_translation_history", [])  # 翻译后的字段

        self.external_header_files = data["external_header_files"]
        self.pre_merge_external_classes = data.get("pre_merge_external_classes", [])

        self.raw_translated_code = data["raw_translated_code"]  # 未经过处理的翻译后的代码

        self.compile_output = data["compile_output"]  # 编译输出
        self.compile_reports = data.get("compile_reports", [])
        self.latest_compile_status = data.get("latest_compile_status", "")
        # 标注信息
        self.errors = data["errors"]

        # 迭代信息
        self.iter_suggestion = data["iter_suggestion"]  # 迭代建议
        self.history_iter_suggestions = data["history_iter_suggestions"]  # 迭代建议历史记录


    def __hash__(self):
        """
        返回基于 key 的哈希值，以支持将 Header 放入集合。

        Returns:
            int，由 key 计算得到的哈希值。
        """
        return hash(self.key)

    @classmethod
    def _get_from_json(cls, file_path:Path):
        """
        从指定 JSON 文件加载 Header。

        职责：
        - 读取并解析 JSON 文件。
        - 根据 key 和 source_code 创建 Header 并填入其余字段。

        Args:
            file_path: JSON 文件路径。

        Returns:
            Header，加载得到的头文件对象。
        """
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        header = cls(data["key"], data["source_code"])
        header._from_dict(data)
        return header

    # @staticmethod
    # def _default_include_name(key: str) -> str:
    #     if key.endswith(".h") or key.endswith(".hpp"):
    #         return key
    #     return f"{sanitize_filename(key)}.h"


    def get_complete_info(self):
        """
        获取头文件的完整信息，按类型输出对应的字典。

        职责：
        - 根据 type 分别构造 class / interface / enum 的信息字典。
        - 对未知类型抛出 ValueError。

        Returns:
            dict，包含类型相关字段的信息字典。
        """
        if self.type == "class":
            return {
                "class_name":self.key,
                "imports":self.imports,
                "class_skeleton":self.source_code,
                # "method_bodies":[method.code for method in self.methods]
            }
        elif self.type == "interface":
            return {
                "interface_name":self.key,
                "imports":self.imports,
                "source_code":self.source_code,
            }
        elif self.type == "enum":
            return {
                "enum_name":self.key,
                "imports":self.imports,
                "source_code":self.source_code,
            }
        else:
            raise ValueError(f"Unknown header type: {self.type}")


    def clean(self, store_iter_suggestion:bool=False, del_history_iter_suggestion:bool=False):
        """
        清空头文件的翻译与编译状态，还原为待翻译状态。

        职责：
        - 重置翻译方案、翻译代码、编译输出、迭代建议等字段。
        - 根据参数决定是否保留/清空历史迭代建议。

        Args:
            store_iter_suggestion: 若为 True，将当前迭代建议存入历史。
            del_history_iter_suggestion: 若为 True 且不存储，则清空历史迭代建议。

        Returns:
            None。
        """
        self.translate_scheme_prompt = ""  # 翻译方案提示
        self.translate_scheme = ""  # 翻译方案
        self.scheme_round = 0
        self.scheme_history = []

        self.translate_prompt = "" # 翻译提示
        self.translated_code = ""  # 翻译后的代码
        self.translated_fields = []
        self.header_translation_history = []  # 翻译后的字段

        self.pre_merge_external_classes = []
        self.raw_translated_code = ""  # 未经过处理的翻译后的代码

        self.compile_output = ""  # 编译输出
        self.compile_reports = []
        self.latest_compile_status = ""
        self.errors = []

        if store_iter_suggestion:
            self.history_iter_suggestions.append(self.iter_suggestion)
        else:
            if del_history_iter_suggestion:
                self.history_iter_suggestions = []
        self.iter_suggestion = []

    def get_all_method_java_signatures(self)->List[str]:
        """
        获取所有方法的java签名
        """
        signatures = []
        for method in self.methods:
            signatures.append(method.key.split(':')[1].replace(' ',''))
        return signatures

    def find_method(self, key:str) :
        """
        根据方法 key 或签名在当前头文件中查找方法节点。

        职责：
        - 生成待匹配的候选签名集合（原始 key、去空格、标准化签名）。
        - 遍历 self.methods，通过集合交集判断是否命中。

        Args:
            key: 方法标识或签名，形如 `类名:方法名(参数类型)`。

        Returns:
            Method，命中的方法节点；未找到时返回 None。
        """
        candidates = {
            key,
            key.replace(' ', '').replace('final', ''),
            self._normalize_method_signature(key),
        }
        candidates = {candidate for candidate in candidates if candidate}

        for method in self.methods:
            method_signature = method.key.split(':', 1)[1] if ':' in method.key else method.key
            method_candidates = {
                method.key,
                method_signature,
                method.key.replace(' ', ''),
                method_signature.replace(' ', ''),
                self._normalize_method_signature(method.key),
                self._normalize_method_signature(method_signature),
            }
            if candidates & {candidate for candidate in method_candidates if candidate}:
                return method
        return None

    @staticmethod
    def _normalize_method_signature(signature: str) -> str:
        """
        标准化方法签名，用于方法匹配。

        职责：
        - 去除 throws 子句、访问修饰符与多余空格。
        - 拆分为方法名与参数表，分别做标准化。

        Args:
            signature: 原始方法签名。

        Returns:
            str，标准化后的方法签名（无空格紧凑形式）。
        """
        if not signature:
            return ""

        signature = signature.strip()
        if ':' in signature:
            signature = signature.split(':', 1)[1].strip()

        signature = re.sub(r"\s+throws\s+.+$", "", signature)
        signature = re.sub(
            r"\b(final|public|protected|private|static|abstract|synchronized|native|default|strictfp)\b",
            "",
            signature,
        )
        signature = signature.strip()

        match = re.match(r"(.+?)\((.*)\)$", signature)
        if not match:
            return Header._normalize_method_name(signature)

        prefix = match.group(1).strip()
        params = match.group(2).strip()
        method_name = Header._normalize_method_name(prefix)
        normalized_params = Header._normalize_param_list(params)
        return f"{method_name}({normalized_params})".replace(" ", "")

    @staticmethod
    def _normalize_param_list(params: str) -> str:
        """
        标准化参数列表。

        职责：
        - 先将参数字符串按顶层逗号拆分。
        - 对每个参数单独标准化后用逗号拼接。

        Args:
            params: 参数表字符串。

        Returns:
            str，标准化后的参数字符串。
        """
        if not params:
            return ""

        return ",".join(
            Header._normalize_param(param)
            for param in Header._split_params(params)
            if param.strip()
        )

    @staticmethod
    def _split_params(params: str) -> List[str]:
        """
        将参数表按照顶层逗号拆分，忽略泛型/括号/下标内部的逗号。

        职责：
        - 维护尖括号、圆括号、方括号的深度计数。
        - 仅在所有深度均为 0 时按逗号切分。

        Args:
            params: 参数表字符串。

        Returns:
            List[str]，拆分后的参数列表。
        """
        result = []
        current = []
        angle_depth = 0
        paren_depth = 0
        bracket_depth = 0

        for ch in params:
            if ch == '<':
                angle_depth += 1
            elif ch == '>':
                angle_depth = max(0, angle_depth - 1)
            elif ch == '(':
                paren_depth += 1
            elif ch == ')':
                paren_depth = max(0, paren_depth - 1)
            elif ch == '[':
                bracket_depth += 1
            elif ch == ']':
                bracket_depth = max(0, bracket_depth - 1)

            if ch == ',' and angle_depth == 0 and paren_depth == 0 and bracket_depth == 0:
                result.append("".join(current).strip())
                current = []
                continue

            current.append(ch)

        if current:
            result.append("".join(current).strip())
        return result

    @classmethod
    def find_by_translated_class_name(cls, headers:List["Header"], name:str)-> Optional["Header"]:
        """
        根据翻译后的类名在头文件列表中查找 Header。

        Args:
            headers: Header 列表。
            name: 翻译后的类名。

        Returns:
            Optional[Header]，命中的头文件；未找到时返回 None。
        """
        for header in headers:
            if header.translated_class_name == name:
                return header
        return None

    def get_include(self)->List[Tuple[str, Literal["standard", "custom"]]]:
        """
        获取所有包含
        返回格式 [(包含文件, 类型(标准库/自定义))]
        """
        if not self.translated_code:
            return []

        result: List[Tuple[str, Literal["standard", "custom"]]] = []
        for match in re.finditer(r'#include\s*[<"]([^>"]+)[>"]', self.translated_code):
            include_file = match.group(1)
            include_type: Literal["standard", "custom"] = "standard" if match.group(0).count('<') > 0 else "custom"
            result.append((include_file, include_type))
        return result

    def get_forward_declare(self)->List[str]:
        """
        获取所有前向声明的类
        """
        if not self.translated_code:
            return []

        result: List[str] = []
        for match in re.finditer(r'(?:class|struct|enum\s+class|enum)\s+(\w[\w:]*(?:::[\w]+)*)\s*;', self.translated_code):
            name = match.group(1)
            if name not in result:
                result.append(name)
        return result
        
    @staticmethod
    def _normalize_param(param: str) -> str:
        """
        标准化单个参数。

        职责：
        - 去除注解、final/volatile/transient 修饰符。
        - 去除顶层类型变量名后的内容（保留类型名）。
        - 去除可变参数标记、泛型实参与包限定名。

        Args:
            param: 单个参数原始字符串。

        Returns:
            str，标准化后的参数类型字符串。
        """
        param = re.sub(r"@\w+(?:\([^)]*\))?\s*", "", param).strip()
        param = re.sub(r"\b(final|volatile|transient)\b", "", param).strip()

        top_level_tokens = []
        current = []
        angle_depth = 0
        bracket_depth = 0

        for ch in param:
            if ch == '<':
                angle_depth += 1
            elif ch == '>':
                angle_depth = max(0, angle_depth - 1)
            elif ch == '[':
                bracket_depth += 1
            elif ch == ']':
                bracket_depth = max(0, bracket_depth - 1)

            if ch.isspace() and angle_depth == 0 and bracket_depth == 0:
                if current:
                    top_level_tokens.append("".join(current))
                    current = []
                continue

            current.append(ch)

        if current:
            top_level_tokens.append("".join(current))

        if len(top_level_tokens) >= 2:
            param = " ".join(top_level_tokens[:-1])

        param = param.replace("...", "").strip()
        param = Header._strip_generic_arguments(param)
        param = Header._strip_package_qualifiers(param)
        return re.sub(r"\s+", "", param)

    @staticmethod
    def _normalize_method_name(name: str) -> str:
        """
        提取并标准化方法名。

        职责：
        - 去除泛型实参。
        - 取最后一个空白分隔的 token，并去掉命名空间/类前缀与嵌套类标记。

        Args:
            name: 方法名前缀字符串。

        Returns:
            str，标准化后的方法名。
        """
        if not name:
            return ""

        name = Header._strip_generic_arguments(name.strip())
        name = name.split()[-1]
        name = re.split(r"::|\.", name)[-1]
        name = name.split("$")[-1]
        return name.replace(" ", "")

    @staticmethod
    def _strip_generic_arguments(text: str) -> str:
        """
        去除文本中顶层的泛型实参（<...> 内容）。

        Args:
            text: 输入文本。

        Returns:
            str，去除泛型实参后的文本。
        """
        if not text:
            return ""

        result = []
        angle_depth = 0
        for ch in text:
            if ch == '<':
                angle_depth += 1
                continue
            if ch == '>':
                angle_depth = max(0, angle_depth - 1)
                continue
            if angle_depth == 0:
                result.append(ch)
        return "".join(result)

    @staticmethod
    def _strip_package_qualifiers(text: str) -> str:
        """
        去除文本中的包限定名，仅保留最简类名。

        职责：
        - 利用正则匹配 `包名.类名` 形式并将其替换为最末的类名。

        Args:
            text: 输入文本。

        Returns:
            str，去除包限定名后的文本。
        """
        if not text:
            return ""

        return re.sub(r"\b(?:[A-Za-z_]\w*\.)+([A-Za-z_]\w*(?:\$[A-Za-z_]\w*)*)\b", r"\1", text)

    def save_to_file(self, file_path:Path):
        """
        将 Header 以 JSON 形式保存到指定文件。

        职责：
        - 以 UTF-8 编码写入 to_dict 的结果，保证中文字符可读。

        Args:
            file_path: 输出文件路径。

        Returns:
            None。
        """
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(json.dumps(self.to_dict(), ensure_ascii=False, indent=4))

    def _serialize_compile_reports(self) -> list:
        """
        序列化编译报告列表。

        职责：
        - 对 CompileFeedback 对象调用其 to_dict，其余对象原样保留。

        Returns:
            list，序列化后的编译报告列表。
        """
        from utils.compile_feedback import CompileFeedback
        result = []
        for report in self.compile_reports:
            if isinstance(report, CompileFeedback):
                result.append(report.to_dict())
            else:
                result.append(report)
        return result

    def get_output_header_name(self) -> str:
        """
        获取输出的头文件名。

        职责：
        - 对翻译后的类名进行文件名清洗，并补上 .h 后缀。

        Returns:
            str，输出头文件名。
        """
        # translated_class_name 可能包含 Windows 非法字符（如命名空间 ::），需清洗
        return f"{sanitize_filename(self.translated_class_name)}.h"

    def get_output_cpp_name(self) -> str:
        """
        获取输出的 cpp 文件名。

        职责：
        - 根据头文件后缀(.h/.hpp)确定对应的 .cpp 文件名。

        Returns:
            str，输出 cpp 文件名。
        """
        if self.get_output_header_name().endswith(".hpp"):
            return self.get_output_header_name()[:-4] + ".cpp"
        if self.get_output_header_name().endswith(".h"):
            return self.get_output_header_name()[:-2] + ".cpp"
        return f"{self.translated_class_name}.cpp"

    def is_generated_external(self) -> bool:
        """
        判断该 Header 是否为外部生成的占位头。

        Returns:
            bool，若 source_kind 或 type 为 generated_external 则返回 True。
        """
        return self.source_kind == "generated_external" or self.type == "generated_external"

    def is_manual_stub(self) -> bool:
        """
        判断该 Header 是否为人工编写的手写桩节点。

        手写桩是已翻译的已知条件：参与上下文构建与编译链接，
        但不参与翻译迭代，repair 阶段只读。

        Returns:
            bool，若 source_kind 为 manual_stub 则返回 True。
        """
        return self.source_kind == "manual_stub"
    
    def is_translated(self) -> bool:
        """判断该头文件是否已经翻译完成"""
        # 如果是类/接口，看代码是否生成；如果是枚举，通常直接认为 source_code 存在即可
        # 这里建议以 translated_code 是否有内容为准
        return bool(self.translated_code and self.translated_code.strip())

