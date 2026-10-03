from ast import Tuple
from pathlib import Path
import hashlib
import sys

p_dir = str(Path(__file__).parent)
pp_dir = str(Path(__file__).parent.parent)
if pp_dir not in sys.path:
    sys.path.append(pp_dir)
if p_dir not in sys.path:
    sys.path.append(p_dir)

from graph.method import Method
from graph.header import Header
from typing import List, Dict, Optional, Literal
from utils.clean_filename import sanitize_filename

from graph.retrieval_tools import *
import json
import shutil


def _short_graph_filename(name: str, suffix: str = ".json") -> str:
    """
    生成图的持久化文件名。

    职责：
    - 对名称做文件名清洗。
    - 若清洗后长度不超过 80，直接拼接后缀；否则截断并以哈希摘要保证唯一性。

    Args:
        name: 原始名称（类名或方法标识等）。
        suffix: 文件后缀，默认 .json。

    Returns:
        str，生成的图文件名。
    """
    safe = sanitize_filename(name)
    if len(safe) <= 80:
        return f"{safe}{suffix}" if not safe.endswith(suffix) else safe
    digest = hashlib.sha1(safe.encode("utf-8")).hexdigest()[:12]
    return f"{safe[:60]}_{digest}{suffix}"


def _read_graph_json(path: Path) -> dict:
    """
    读取图 JSON 文件并解析为字典。

    职责：
    - 优先直接读取；若遇到 FileNotFoundError，则通过 \\\\?\\ 长路径前缀重试。

    Args:
        path: JSON 文件路径。

    Returns:
        dict，解析得到的字典数据。
    """
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        absolute_path = path if path.is_absolute() else path.resolve()
        long_path = Path("\\\\?\\" + str(absolute_path))
        return json.loads(long_path.read_text(encoding="utf-8"))


class Project:
    """
    表示一个翻译项目，聚合项目内的头文件与方法分组。

    职责：
    - 保存项目名、头文件列表 headers 与按依赖层级分组的方法列表 methods。
    - 提供按 key / 头文件名 / 翻译类名查找头文件的能力。
    - 提供依赖头文件的拓扑排序（含强连通分量处理）。
    - 提供整个项目的保存（save）与加载（load / load_from_source）能力。

    使用约定：
    - methods 的每个元素是同一依赖层级的一组 Method 对象（分层顺序由调用图推导）。
    - headers 中每个 Header 通过其 methods 关联对应方法。
    """
    def __init__(self, name: str, methods: List[List[Method]], headers: List[Header]):
        """
        初始化 Project。

        Args:
            name: 项目名称。
            methods: 按依赖层级分组的 Method 列表。
            headers: 项目内的 Header 列表。
        """
        self.name = name
        self.methods = methods
        self.headers = headers

    def find_header(self, key:str) -> Optional[Header]:
        """
        根据 header 的 key 查找对应的 Header。

        Args:
            key: 头文件 key。

        Returns:
            Optional[Header]，命中的头文件；未找到时返回 None。
        """
        for header in self.headers:
            if header.key == key:
                return header
        return None

    def find_header_by_include_name(self, include_name: str) -> Optional[Header]:
        """
        根据输出头文件名查找对应的 Header。

        Args:
            include_name: 输出头文件名（如 xxx.h）。

        Returns:
            Optional[Header]，命中的头文件；未找到时返回 None。
        """
        for header in self.headers:
            if header.get_output_header_name() == include_name:
                return header
        return None

    def find_header_by_translated_class_name(self, class_name):
        """
        根据翻译后的类名查找对应的 Header。

        Args:
            class_name: 翻译后的类名。

        Returns:
            Optional[Header]，命中的头文件；未找到时返回 None。
        """
        return Header.find_by_translated_class_name(self.headers, class_name)

    def get_included(self, header:Header)-> tuple[List[str], List[Header]]:
        """
        获取指定头文件的所有包含文件
        """
        if header not in self.headers:
            print(f"warning: header {header.key} not in project headers.")

        included_standard: List[str] = []
        included_custom: List[Header] = []
        for include_name, include_type in header.get_include():
            if include_type == "standard":
                included_standard.append(include_name)
            else:
                matched = self.find_header_by_include_name(include_name)
                if matched:
                    included_custom.append(matched)
                else:
                    included_standard.append(include_name)

        return included_standard, included_custom

    def sort_headers(self, by:Literal["original", "translated"])->List[List[Header]]:
        """
        对头文件按照依赖关系进行拓扑排序
        by: 按照原始java代码中的import依赖关系排序, 还是按照翻译后的include依赖关系排序
        返回的列表中每一项要么是单个节点的列表, 要么是一个SCC中所有节点的列表

        顺序:
        [依赖链低层->高层]
        """
        if not self.headers:
            return []

        n = len(self.headers)
        key_to_idx = {header.key: i for i, header in enumerate(self.headers)}

        adj: List[List[int]] = [[] for _ in range(n)]
        for i, header in enumerate(self.headers):
            if by == "translated":
                _, included = self.get_included(header)
                for inc in included:
                    j = key_to_idx.get(inc.key)
                    if j is not None:
                        adj[j].append(i)
            else:
                for imp in header.imports:
                    import_class = imp.split(".")[-1]
                    for j, other in enumerate(self.headers):
                        if other.key == import_class:
                            adj[j].append(i)
                            break

        in_degree: List[int] = [0] * n
        for u in range(n):
            for v in adj[u]:
                in_degree[v] += 1

        zero_queue = [i for i in range(n) if in_degree[i] == 0]
        topo_order: List[int] = []
        while zero_queue:
            u = zero_queue.pop(0)
            topo_order.append(u)
            for v in adj[u]:
                in_degree[v] -= 1
                if in_degree[v] == 0:
                    zero_queue.append(v)

        if len(topo_order) == n:
            result: List[List[Header]] = [[self.headers[i]] for i in reversed(topo_order)]
            return result

        remaining = [i for i in range(n) if i not in set(topo_order)]
        scc_groups: List[List[int]] = self._find_sccs(adj, remaining)

        for group in scc_groups:
            for u in group:
                if u not in topo_order:
                    topo_order.append(u)

        result = []
        for group in scc_groups:
            if len(group) > 1:
                result.append([self.headers[i] for i in group])
        for i in reversed(topo_order):
            already_added = any(i in group for group in scc_groups if len(group) > 1)
            if not already_added:
                result.append([self.headers[i]])
        return result

    def _find_sccs(self, adj: List[List[int]], vertices: List[int]) -> List[List[int]]:
        """
        在指定子图（vertices）上寻找强连通分量。

        职责：
        - 基于 Kosaraju 算法：先对子图做正向 DFS 得到完成顺序栈，再在反向图上按栈序做第二次 DFS 划分分量。

        Args:
            adj: 邻接表。
            vertices: 参与计算的顶点编号列表。

        Returns:
            List[List[int]]，强连通分量的顶点分组列表。
        """
        n = len(self.headers)
        visited = [False] * n
        stack: List[int] = []

        def dfs(u: int):
            visited[u] = True
            for v in adj[u]:
                if v in set(vertices) and not visited[v]:
                    dfs(v)
            stack.append(u)

        for u in vertices:
            if not visited[u]:
                dfs(u)

        rev_adj: List[List[int]] = [[] for _ in range(n)]
        for u in range(n):
            for v in adj[u]:
                rev_adj[v].append(u)

        comp: List[int] = [-1] * n

        def rdfs(u: int, label: int):
            comp[u] = label
            for v in rev_adj[u]:
                if v in set(vertices) and comp[v] == -1:
                    rdfs(v, label)

        label = 0
        while stack:
            u = stack.pop()
            if comp[u] == -1:
                rdfs(u, label)
                label += 1

        sccs: List[List[int]] = []
        for lbl in range(label):
            group = [u for u, c in enumerate(comp) if c == lbl]
            if group:
                sccs.append(group)
        return sccs



    @classmethod
    def save(cls, project: "Project", dir_path: Path):
        """
        保存项目到指定目录
        """
        dir_path.mkdir(parents=True, exist_ok=True)
        for header in project.headers:
            header_dir = dir_path / _short_graph_filename(header.key, suffix="")
            header_dir.mkdir(parents=True, exist_ok=True)

            header.save_to_file(header_dir / _short_graph_filename(header.key))
            for method in header.methods:
                save_path = header_dir / _short_graph_filename(method.get_name() + str(method.id))
                method.save_to_file(save_path)

    @classmethod
    def load(cls, dir_path: Path):
        """
        从指定目录加载项目
        """
        # self.name = dir_path.name
        # self.headers = []
        project = cls(dir_path.name, [], [])
        # key -> Method 列表：Java 可变参数重载（T 与 T...）会被解析器折叠成
        # 相同的方法 key，但磁盘上仍是按 id 命名的不同文件，必须全部保留。
        all_methods: dict[str, list] = {}
        for header_dir in dir_path.iterdir():
            if not header_dir.is_dir():
                continue
            for file in header_dir.iterdir():
                data = _read_graph_json(file)
                if "translated_class_name" in data and "methods" in data:
                    header = Header(data["key"], data["source_code"])
                    header._from_dict(data)
                    project.headers.append(header)
                    continue

                method = Method("", "", "", None)
                method._from_dict(data)
                all_methods.setdefault(method.key, []).append(method)

        for header in project.headers:
            methods_str_list = header.methods
            # 同 key 的重复方法按出现顺序依次分配不同实例，避免多个重载
            # 共享同一 Method 对象（否则变参消歧和后续翻译会丢方法）。
            key_usage: dict[str, int] = {}
            resolved_methods = []
            for key in methods_str_list:
                candidates = all_methods[key]
                index = key_usage.get(key, 0)
                resolved_methods.append(candidates[min(index, len(candidates) - 1)])
                key_usage[key] = index + 1
            header.methods = resolved_methods

        # 调用边按 key 索引时同 key 重载取第一个实例，保持原有分层行为。
        methods_by_key = {key: methods[0] for key, methods in all_methods.items()}

        for method in (m for ms in all_methods.values() for m in ms):
            method.header = project.find_header(method.header)
            if method.header is None:
                raise ValueError(f"Can not find header {method.header} for method {method.key}")
            children_str_list = method.children
            method.children = set([methods_by_key[key] for key in children_str_list])
            parent_str_list = method.parents
            method.parents = set([methods_by_key[key] for key in parent_str_list])

            children_external_str_list = method.children_external
            method.children_external = [Method(key, "", "", Header(key.split(':')[0], "")) for key in children_external_str_list]

        # 分层输入：同 key 的重载实例（如 T 与 T... 变参重载）用伪 key 补充进
        # 分层图，保证每个重载都会进入方法翻译流程；调用边仍按真实 key 解析。
        ordered_input: dict = dict(methods_by_key)
        for key, methods in all_methods.items():
            for dup_index, dup_method in enumerate(methods[1:], start=1):
                ordered_input[f"{key}#dup{dup_index}"] = dup_method

        project.methods = get_ordered_method_groups(ordered_input)
        return project

    @classmethod
    def load_from_source(cls, ai_name:str, project_name:str, version:str):
        """
        从数据源加载项目
        """
        split_dir = cfg_split_output_dir_path(project_name, version)
        split_list = list(split_dir.iterdir())
        if not split_list:
            print(f"Split files not exist in {split_dir}, generate split.")
            generate_split(project_name, version)
        data = retrieve_project(ai_name, project_name, version)
        return cls(project_name, data["method_nodes"], data["headers"])

    def get_method_layers_as_str(self):
        """
        以字符串形式获取方法分层信息，便于日志输出。

        Returns:
            str，每层方法名称的摘要字符串。
        """
        return '\n'.join([f"Layer {i}, {len(layer)} methods: {[method.get_name() for method in layer]} " for i, layer in enumerate(self.methods)])

    def print_method_layers(self):
        """
        在控制台打印方法分层信息。

        Returns:
            None。
        """
        for i, layer in enumerate(self.methods):
            print(f"Layer {i}, {len(layer)} methods: {[method.get_name() for method in layer]}")

    def print_layer_info(self):
        """
        在控制台打印每个层的方法数量。

        Returns:
            None。
        """
        for layer_idx, layer in enumerate(self.methods):
            print(f"Layer {layer_idx}: {len(layer)} methods")


if __name__ == "__main__":
    from retrieval_tools import *
    data = retrieve_project('deepseek', 'Cookie', 'v4_1')
    project = Project('Cookie', data["method_nodes"], data["headers"])

    Project.save(project, Path("test/Cookie"))


            
            

                



