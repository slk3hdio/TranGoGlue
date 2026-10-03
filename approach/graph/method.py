from pathlib import Path
from typing import Optional, LiteralString
from utils.clean_filename import sanitize_filename  # 导入清洗逻辑
from typing import List, Dict, Any
from utils.clean_filename import sanitize_filename  # 导入清洗逻辑
# from graph.header import Header
import json


class Method:
    """
    表示一个方法的图节点，是整个翻译图的另一个核心数据结构。

    职责：
    - 保存方法的结构信息（key、源代码、调用关系 children/parents、所属 header 等）。
    - 保存翻译过程的状态信息（翻译方案、翻译代码、编译结果、迭代信息等）。
    - 提供序列化（to_dict/save_to_file）与反序列化（_from_dict/_get_from_json）能力，支持持久化为 JSON。

    使用约定：
    - key 为项目内唯一标识，格式为 `类名1$类名2$...$类名n:方法名(参数类型)`。
    - children 为我调用的方法，parents 为调用我的方法，children_external 为调用的外部方法。
    - 反序列化时 header、children、parents 字段先保存为 key，需由 Project.load 还原为对象。
    """
    def __init__(self, key: str, code: str, source_tag: str, header):
        self.key = key # 类名1$类名2$...$类名n:方法名(参数类型)，项目内唯一
        self.id = id(self) # 唯一标识(注意当从文件加载时， self.id不一定和id(self)相等)
        self.file_name = sanitize_filename(key)
        self.code = code # 源代码
        self.children:set[Method] = set[Method]() # 被我调用的方法
        self.children_external:List[Method] = [] # 被我调用的外部方法
        self.parents:set[Method] = set[Method]() # 调用我的方法
        self.source_tag = source_tag # 如 file1.001
        self.header = header  # 头部信息

        self.is_simple_method = False # 是否是简单方法(样板方法、实现简单且不依赖其他方法的方法)
        self.skip_translation = False
        self.skip_translation_reason = ""
        self.is_added_method = False
        self.is_deleted_method = False
        self.is_template_method = False
        self.mapped_java_signature = ""
        self.mapped_cpp_definition = ""
        self.mapping_status = ""
        self.method_body_location = ""
        self.implemented_in_header = False

        # 翻译信息
        self.main_function = "" # 方法的主要功能，规划阶段生成
        self.implementation_detail = "" # 方法的实现详情，翻译阶段生成
        self.temp_header = "" # 临时头

        self.translate_scheme_prompt = ""  # 翻译方案提示
        self.translate_scheme = ""  # 翻译方案

        self.translated_declaration = "" # 翻译后的声明

        self.translate_prompt = ""
        self.translated_code = "" # 翻译后的代码

        self.raw_translated_code = ""  # 未经过处理的翻译后的代码

        # 编译信息
        self.compile_unit = ""
        self.compile_output = ""

        # 标注信息
        self.errors = []

        # 迭代信息
        self.history_iter_suggestions:list[list[str]] = [] # 历史迭代建议
        self.iter_suggestion:list[str] = [] # 当前迭代建议

    def get_name(self)->str:
        """
        获取方法名（不含参数）。

        Returns:
            str，方法名。
        """
        return self.key.split(':')[1].split('(')[0]

    def __repr__(self):
        """
        返回机器可读的表示形式。

        Returns:
            str，形如 Method(key)。
        """
        return f"Method({self.key})"

    def to_dict(self):
        """
        将 Method 序列化为字典结构。

        职责：
        - 输出全部需要在 JSON 中持久化的字段；children/parents/header 以 key 表示。

        Returns:
            dict，包含 Method 全部持久化字段的字典。
        """
        return {
            "key": self.key, # 唯一标识 
            "id": self.id, # 唯一标识 
            "file_name": self.file_name,
            "code": self.code,
            "children": [child.key for child in self.children], # 被我调用的方法
            "children_external": [child.key for child in self.children_external], # 被我调用的外部方法
            "parents": [parent.key for parent in self.parents], # 调用我的方法
            "source_tag": self.source_tag, # 如 file1.001
            "header": self.header.key,  # 头部信息

            "is_simple_method": self.is_simple_method, # 是否是简单方法(样板方法、实现简单且不依赖其他方法的方法)
            "skip_translation": self.skip_translation,
            "skip_translation_reason": self.skip_translation_reason,
            "is_added_method": self.is_added_method,
            "is_deleted_method": self.is_deleted_method,
            "is_template_method": self.is_template_method,
            "mapped_java_signature": self.mapped_java_signature,
            "mapped_cpp_definition": self.mapped_cpp_definition,
            "mapping_status": self.mapping_status,
            "method_body_location": self.method_body_location,
            "implemented_in_header": self.implemented_in_header,

            # 翻译信息
            "main_function": self.main_function, # 方法的主要功能，规划阶段生成
            "implementation_detail": self.implementation_detail, # 方法的实现详情，翻译阶段生成
            "temp_header": self.temp_header, # 临时头

            "translate_scheme_prompt": self.translate_scheme_prompt,  # 翻译方案提示
            "translate_scheme": self.translate_scheme,  # 翻译方案

            "translated_declaration": self.translated_declaration, # 翻译后的声明

            "translate_prompt": self.translate_prompt, # 翻译提示
            "translated_code": self.translated_code, # 翻译后的代码

            "raw_translated_code": self.raw_translated_code,  # 未经过处理的翻译后的代码

            # 编译信息
            "compile_unit": self.compile_unit,
            "compile_output": self.compile_output,

            # 标注信息
            "errors": self.errors,

            # 迭代信息
            "history_iter_suggestions": self.history_iter_suggestions, # 历史迭代建议
            "iter_suggestion": self.iter_suggestion, # 当前迭代建议
        }

    def _from_dict(self, data: Dict[str, Any]):
        """
        从字典中反序列化 Method 的字段。

        职责：
        - 将 data 中保存的字段赋值回当前实例，可选字段使用默认值兜底。

        Args:
            data: 由 to_dict 产生的字典。

        Returns:
            None。
        """
        self.key = data["key"]
        self.id = data["id"] # 唯一标识 
        self.code = data["code"]
        self.source_tag = data["source_tag"]
        self.header = data["header"]
        self.is_simple_method = data["is_simple_method"]
        self.skip_translation = data.get("skip_translation", False)
        self.skip_translation_reason = data.get("skip_translation_reason", "")
        self.is_added_method = data.get("is_added_method", False)
        self.is_deleted_method = data.get("is_deleted_method", False)
        self.is_template_method = data.get("is_template_method", False)
        self.mapped_java_signature = data.get("mapped_java_signature", "")
        self.mapped_cpp_definition = data.get("mapped_cpp_definition", "")
        self.mapping_status = data.get("mapping_status", "")
        self.method_body_location = data.get("method_body_location", "")
        self.implemented_in_header = data.get("implemented_in_header", False)
        self.file_name = sanitize_filename(self.key)
        self.code = data["code"]
        self.children = data["children"] # 被我调用的方法
        self.children_external = data["children_external"] # 被我调用的外部方法

        self.parents = data["parents"] # 调用我的方法
        self.source_tag = data["source_tag"] # 如 file1.001

        self.is_simple_method = data["is_simple_method"] # 是否是简单方法(样板方法、实现简单且不依赖其他方法的方法)
        self.skip_translation = data.get("skip_translation", False)
        self.skip_translation_reason = data.get("skip_translation_reason", "")
        self.is_added_method = data.get("is_added_method", False)
        self.is_deleted_method = data.get("is_deleted_method", False)
        self.is_template_method = data.get("is_template_method", False)
        self.mapped_java_signature = data.get("mapped_java_signature", "")
        self.mapped_cpp_definition = data.get("mapped_cpp_definition", "")
        self.mapping_status = data.get("mapping_status", "")
        self.method_body_location = data.get("method_body_location", "")
        self.implemented_in_header = data.get("implemented_in_header", False)

        # 翻译信息
        self.main_function = data["main_function"] # 方法的主要功能，规划阶段生成
        self.implementation_detail = data["implementation_detail"] # 方法的实现详情，翻译阶段生成
        self.temp_header = data["temp_header"] # 临时头

        self.translate_scheme_prompt = data["translate_scheme_prompt"]  # 翻译方案提示  
        self.translate_scheme = data["translate_scheme"]  # 翻译方案

        self.translated_declaration = data["translated_declaration"] # 翻译后的声明

        self.translate_prompt = data["translate_prompt"] # 翻译提示
        self.translated_code = data["translated_code"] # 翻译后的代码

        self.raw_translated_code = data["raw_translated_code"]  # 未经过处理的翻译后的代码

        # 编译信息
        self.compile_unit = data["compile_unit"]
        self.compile_output = data["compile_output"]

        # 标注信息
        self.errors = data["errors"]

        # 迭代信息
        # self.history_iter_suggestions = data["history_iter_suggestions"] # 历史迭代建议
        # self.iter_suggestion = data["iter_suggestion"] # 当前迭代建议

    @classmethod
    def _get_from_json(cls, file_path:Path):
        """
        从指定 JSON 文件加载 Method。

        职责：
        - 读取并解析 JSON 文件，创建空的 Method 实例并填入字段。

        Args:
            file_path: JSON 文件路径。

        Returns:
            Method，加载得到的方法对象。
        """
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        method = cls("","","", None)
        method._from_dict(data)
        return method

    
    def __str__(self):
        """
        返回方法的可读字符串表示，用于日志输出。

        Returns:
            str，包含 key、source_tag、children、parents 的格式化字符串。
        """
        # 获取 children 和 parents 的 key 值作为字符串
        children_keys = ', '.join([child.key for child in self.children]) if self.children else 'None'
        parents_keys = ', '.join([parent.key for parent in self.parents]) if self.parents else 'None'
    
        # 返回格式化字符串，包含了所需的所有信息
        return (
            f"Key: {self.key}\n"  # 方法的唯一标识
            #f"Code:\n{self.code}\n"  # 方法的源代码
            f"Source Tag: {self.source_tag}\n"  # 源文件标签
            f"Children: {children_keys}\n"  # 被调用的方法
            f"Parents: {parents_keys}\n"  # 调用当前方法的其他方法
            "\n"
        )
    
    def __eq__(self, other):
        """
        判断两个 Method 是否相等，比较依据为 key。

        Args:
            other: 待比较的 Method 对象。

        Returns:
            bool，key 相同则返回 True。
        """
        return self.key == other.key

    def __hash__(self):
        """
        返回基于 key 的哈希值，以支持将 Method 放入集合。

        Returns:
            int，由 key 计算得到的哈希值。
        """
        return hash(self.key)

    def add_iter_suggestion(self, suggestion:str):
        """
        向当前迭代建议列表添加一条建议。

        Args:
            suggestion: 待添加的迭代建议字符串。

        Returns:
            None。
        """
        self.iter_suggestion.append(suggestion)

    def clean(self, store_iter_suggestion:bool=False, del_history_iter_suggestion:bool=False):
        """
        清空方法的翻译与编译状态，还原为待翻译状态。

        职责：
        - 重置翻译方案、翻译代码、编译输出、映射信息、迭代建议等字段。
        - 根据参数决定是否保留/清空历史迭代建议。

        Args:
            store_iter_suggestion: 若为 True，将当前迭代建议存入历史。
            del_history_iter_suggestion: 若为 True 且不存储，则清空历史迭代建议。

        Returns:
            None。
        """
        self.temp_header = "" # 临时头

        self.translate_scheme_prompt = ""  # 翻译方案提示
        self.translate_scheme = ""  # 翻译方案

        self.translated_declaration = "" # 翻译后的声明

        self.translate_prompt = ""
        self.translated_code = "" # 翻译后的代码
        self.raw_translated_code = ""
        self.skip_translation = False
        self.skip_translation_reason = ""
        self.is_added_method = False
        self.is_deleted_method = False
        self.is_template_method = False
        self.mapped_java_signature = ""
        self.mapped_cpp_definition = ""
        self.mapping_status = ""
        self.method_body_location = ""
        self.implemented_in_header = False

        self.compile_unit = ""
        self.compile_output = ""
        self.errors = []

        if store_iter_suggestion:
            self.history_iter_suggestions.append(self.iter_suggestion)
        else:
            if del_history_iter_suggestion:
                self.history_iter_suggestions = []
        self.iter_suggestion = []

    def save_to_file(self, file_path:Path):
        """
        保存方法到指定文件
        """
        file_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(json.dumps(self.to_dict(), ensure_ascii=False, indent=4))
        except FileNotFoundError:
            if file_path.is_absolute():
                long_path = Path("\\\\?\\" + str(file_path))
                with open(long_path, "w", encoding="utf-8") as f:
                    f.write(json.dumps(self.to_dict(), ensure_ascii=False, indent=4))
                return
            raise

    def is_translated(self) -> bool:
        """判断该头文件是否已经翻译完成"""
        # 如果是类/接口，看代码是否生成；如果是枚举，通常直接认为 source_code 存在即可
        # 这里建议以 translated_code 是否有内容为准
        return bool(self.translated_code and self.translated_code.strip())
