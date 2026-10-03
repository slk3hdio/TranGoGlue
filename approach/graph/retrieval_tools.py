import os
import re
import pickle
import sys
import json
from typing import Any, Dict
from collections import deque
from pathlib import Path

p_dir = str(Path(__file__).parent)
pp_dir = str(Path(__file__).parent.parent)
if pp_dir not in sys.path:
    sys.path.append(pp_dir)
if p_dir not in sys.path:
    sys.path.append(p_dir)
from graph.header import Header
from graph.method import Method
from path_config import *

def generate_split(project_name: str, version: str) -> None:
        """生成图分割"""
        command = f"cd {cfg_parser_tool_path()} && {cfg_gradlew_file_path()} run --args=\"{cfg_source_code_dir_path(project_name)} {cfg_split_output_dir_path(project_name, version)}\""
        print(command)
        os.system(command)


def find_method(split_dir: str, log_file):
    """
    从分割 JSON 文件中提取 Header 与 Method 节点。

    职责：
    - 遍历 split_dir 下的 .json 文件，解析类与方法的声明信息。
    - 为每个类创建 Header，为每个方法创建 Method 并关联到 Header。
    - 将简单方法（语句数 < 3）标记为 is_simple_method。
    - 将提取结果写入 log_file。

    Args:
        split_dir: 分割 JSON 所在目录。
        log_file: 日志文件对象。

    Returns:
        (dict, list)：method_nodes（key->Method）与 headers（Header 列表）。
    """
    method_nodes = {}
    file_id = 1
    headers = []

    for file in os.listdir(split_dir):
        if not file.endswith('.json'):
            continue
        file_path = os.path.join(split_dir, file)
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                raw_content = f.read()
        except UnicodeDecodeError:
            with open(file_path, 'r', encoding='gbk') as f:
                raw_content = f.read()

        json_data = json.loads(raw_content)
        class_type = json_data['type']
        class_name = json_data['className']

        log_file.write(f"{file} 提取{class_type}名为: {class_name}\n")

        header = Header(class_name, json_data['classDeclaration'])
        header.type = class_type
        header.imports = json_data['imports']
        header.fields = json_data['fieldDeclarations']
        header.parent_class = json_data['parentClass']
        header.interfaces = json_data['interfaces']
        headers.append(header)

        file_id += 1

        method_count = 1
        methods = json_data['methods']

        # if class_type == 'interface':
        #     continue

        for method_match in methods:
            method_key = method_match['methodSignature']
            method_body = method_match['methodBody']
            statement_count = method_match['statementCount']

            source_tag = f"file{file_id}.{method_count:03}"

            # 创建并添加方法节点（Method），将其与 Header 正确关联
            node = Method(method_key, method_body, source_tag, header)
            if statement_count < 3:
                node.is_simple_method = True
            method_nodes[method_key] = node
            header.methods.append(node)  # 将方法节点添加到 Header 的 methods 列表
            method_count += 1

    # 输出日志
    log_file.write(f"共识别出 {len(method_nodes)} 个方法：\n")
    for key in sorted(method_nodes.keys()):
        log_file.write(f"  - {key}\n")

    return method_nodes, headers

def get_standard_signature(full_signature: str):
    """
    将完整方法签名转换为标准化签名 `类名:方法名(简化参数类型列表)`。

    职责：
    - 拆分类名与方法名部分，处理 <init> 构造方法。
    - 将参数类型简化为去包名、去嵌套前缀的最简类型。

    Args:
        full_signature: 完整方法签名，形如 `包名.类名:方法名(参数列表)`。

    Returns:
        str，标准化签名；若签名中不含 ':' 则返回 None。
    """
    if ':' not in full_signature:
        return None
    class_part, method_part = full_signature.split(':', 1)
    class_name = class_part.split('.')[-1] # 如果是嵌套类，class_name的格式为类名1$类名2$...$类名n

    method_name_only = method_part.split('(')[0].replace(' ', '')

    if method_name_only == '<init>':
        method_name_only = class_name

    # 参数串
    params = method_part.split('(')[1].split(')')[0]
    param_list = params.split(',') if params else []

    formatted_params = []
    for param in param_list:
        param_type = param.strip().split(' ')[0]
        simplified_type = param_type.split('.')[-1].split('$')[-1].replace(' ','')
        formatted_params.append(simplified_type)

    return f"{class_name}:{method_name_only}({','.join(formatted_params)})"


def find_method_with_erased_types(signature: str, method_nodes: Dict[str, Method]):
    """
    通过去除泛型实参后的签名在方法节点中查找匹配的方法。

    职责：
    - 对 method_nodes 中每个 key 去除泛型实参（<...>），与目标签名比较。

    Args:
        signature: 标准化后的签名。
        method_nodes: key->Method 的字典。

    Returns:
        Method，命中的方法节点；未找到时返回 None。
    """
    for key in method_nodes.keys():
        generics_pattern = re.compile(r'<.*?>')
        erased_signature = generics_pattern.sub('', key)
        if erased_signature == signature:
            return method_nodes[key]
    return None


def build_call_graph(method_call_path: str, method_nodes: Dict[str, Method], log_file):
    """
    根据方法调用关系文件构建方法调用图。

    职责：
    - 逐行解析调用关系（caller -> callee）。
    - 为存在的方法建立 children/parents 关联。
    - 为调用方存在但被调用方缺失的情况创建外部方法占位节点。
    - 处理各类缺失场景并将日志写入 log_file。

    Args:
        method_call_path: 方法调用关系文件路径。
        method_nodes: key->Method 的字典。
        log_file: 日志文件对象。

    Returns:
        None。
    """
    # 存储被调用方存在但调用方不存在的方法
    missing_called_methods = {}

    with open(method_call_path, 'r', encoding='utf-8') as f:
        count = 0
        for line in f:
            try:
                parts = line.strip().split('\t')
                if len(parts) < 5:
                    log_file.write(f"跳过无效行: {line}\n")
                    continue
                caller = get_standard_signature(parts[2])
                callee = get_standard_signature(parts[3])

                if caller is None or callee is None:
                    log_file.write(f"无效的签名: {parts[2] or parts[3]}\n")
                    continue

                # print(caller, callee)
                caller_node = find_method_with_erased_types(caller, method_nodes)
                callee_node = find_method_with_erased_types(callee, method_nodes)

                # 1. 调用方存在，被调用方不存在
                if caller_node and not callee_node:
                    # 被调用方不存在，创建被调用方的节点并存储在单独的字典中
                    
                    callee_node = Method(callee, "", "", Header(callee.split(':')[0], ""))  # 被调用方的节点
                    missing_called_methods[callee] = callee_node
                    callee_node.parents.add(caller_node)  # 将调用方添加为父节点 # type: ignore

                    log_file.write(f"调用方存在{caller}，被调用方不存在{callee}，已创建被调用方节点: {callee}\n")

                # 2. 调用方不存在，被调用方存在
                elif not caller_node and callee_node:
                    log_file.write(f"调用方不存在，忽略调用方: {caller}\n")

                # 3. 调用方和被调用方都不存在
                elif not caller_node and not callee_node:
                    log_file.write(f"调用方和被调用方都不存在，忽略调用方和被调用方: {caller} -> {callee}\n")
                    continue

                # 4. 调用方和被调用方都存在
                elif caller_node and callee_node and caller_node.key != callee_node.key:
                    caller_node.children.add(callee_node)
                    callee_node.parents.add(caller_node)
                    count += 1
                    log_file.write(f"添加调用关系: {caller_node.key} -> {callee_node.key}\n")
            except Exception as e:
                log_file.write(f"处理行 {line} 时出错: {e}\n")
                print(f"处理行 {line} 时出错: {e}")
                print(f"caller: {caller}")
                print(f"callee: {callee}")
                raise

        log_file.write(f"共添加 {count} 条调用关系\n")

    if missing_called_methods:
        log_file.write("以下是调用方存在，但被调用方不存在的方法：\n")
        for callee, callee_node in missing_called_methods.items():
            parents_keys = [parent.key for parent in callee_node.parents] #type: ignore
            log_file.write(f"  - {callee_node.key}\n")
            log_file.write(f"  Parents: {', '.join(parents_keys)}\n")  # 输出调用当前方法的其他方法

def _find_method_sccs(method_nodes: Dict[str, Method]) -> list[list[str]]:
    """使用迭代式 Kosaraju 算法查找方法图中的强连通分量。

    仅处理 ``method_nodes`` 中的项目内方法；组件及组件内节点均按输入字典
    的顺序稳定排列，避免集合迭代顺序导致实验分组不稳定。

    Args:
        method_nodes: key->Method 的字典。

    Returns:
        list[list[str]]: 强连通分量列表，每个元素是一组方法 key。
    """
    node_order = {key: index for index, key in enumerate(method_nodes)}
    adjacency = {
        key: sorted(
            (child.key for child in node.children if child.key in method_nodes),
            key=node_order.__getitem__,
        )
        for key, node in method_nodes.items()
    }
    reverse_adjacency = {key: [] for key in method_nodes}
    for caller_key, callee_keys in adjacency.items():
        for callee_key in callee_keys:
            reverse_adjacency[callee_key].append(caller_key)

    # 第一遍 DFS 记录完成顺序；显式栈避免大型项目触发 Python 递归深度限制。
    visited = set()
    finish_order = []
    for start_key in method_nodes:
        if start_key in visited:
            continue
        visited.add(start_key)
        stack = [(start_key, 0)]
        while stack:
            current_key, child_index = stack[-1]
            if child_index >= len(adjacency[current_key]):
                stack.pop()
                finish_order.append(current_key)
                continue
            child_key = adjacency[current_key][child_index]
            stack[-1] = (current_key, child_index + 1)
            if child_key not in visited:
                visited.add(child_key)
                stack.append((child_key, 0))

    # 第二遍在反向图上收集 SCC。
    assigned = set()
    components = []
    for start_key in reversed(finish_order):
        if start_key in assigned:
            continue
        assigned.add(start_key)
        component = []
        stack = [start_key]
        while stack:
            current_key = stack.pop()
            component.append(current_key)
            for parent_key in reverse_adjacency[current_key]:
                if parent_key not in assigned:
                    assigned.add(parent_key)
                    stack.append(parent_key)
        component.sort(key=node_order.__getitem__)
        components.append(component)

    components.sort(key=lambda component: node_order[component[0]])
    return components


def get_ordered_method_groups(method_nodes: Dict[str, Method]):
    """
    根据调用依赖关系对方法进行分层（拓扑级 BFS 分层）。

    职责：
    - 先将互相依赖的方法压缩为强连通分量（SCC）。
    - 在 SCC 构成的有向无环图上，从无依赖组件开始逐层排序。
    - 环内方法进入同一层，确保所有方法都能进入后续翻译流程。

    Args:
        method_nodes: key->Method 的字典。

    Returns:
        list，每层为一个 Method 列表（依赖链由下到上）。
    """
    if not method_nodes:
        return []

    node_order = {key: index for index, key in enumerate(method_nodes)}
    components = _find_method_sccs(method_nodes)
    component_by_method = {
        method_key: component_id
        for component_id, component in enumerate(components)
        for method_key in component
    }
    component_order = {
        component_id: min(node_order[key] for key in component)
        for component_id, component in enumerate(components)
    }

    # 组件依赖数等价于压缩图的出度，反向索引用于依赖完成后唤醒调用方。
    dependencies = {component_id: set() for component_id in range(len(components))}
    callers = {component_id: set() for component_id in range(len(components))}
    for caller_key, caller_node in method_nodes.items():
        caller_component = component_by_method[caller_key]
        for callee_node in caller_node.children:
            if callee_node.key not in component_by_method:
                continue
            callee_component = component_by_method[callee_node.key]
            if caller_component == callee_component:
                continue
            dependencies[caller_component].add(callee_component)
            callers[callee_component].add(caller_component)

    dependency_count = {
        component_id: len(component_dependencies)
        for component_id, component_dependencies in dependencies.items()
    }
    ready = sorted(
        (component_id for component_id, count in dependency_count.items() if count == 0),
        key=component_order.__getitem__,
    )

    ordered_groups = []
    while ready:
        current_group = []
        next_ready = set()
        for component_id in ready:
            current_group.extend(method_nodes[key] for key in components[component_id])
            for caller_component in callers[component_id]:
                dependency_count[caller_component] -= 1
                if dependency_count[caller_component] == 0:
                    next_ready.add(caller_component)
        ordered_groups.append(current_group)
        ready = sorted(next_ready, key=component_order.__getitem__)

    return ordered_groups

def sort_headers(headers: list[Header], key: str = "translated"):
    """
    对header节点按照调用关系进行排序
    key: 排序依据，为"translated"时按照翻译后的头文件包含关系排序，否则按照原始java文件中的import关系排序

    当存在循环依赖时，将无法排序的header节点按原顺序添加到已经排序的节点后
    """
    def find(headers:list[Header], key:str):
        for header in headers:
            if header.key == key:
                return header
        return None

    sorted_headers = []
    header_file_degree = {header.key: 0 for header in headers}
    point_to = {header.key: [] for header in headers}
    external_files = []
    if key == "translated":
        for header in headers:
            for include_file in header.external_header_files:
                include_class_name = include_file.split('.')[0]
                if include_class_name in header_file_degree:
                    header_file_degree[header.key] += 1
                    point_to[include_class_name].append(header)
                else:
                    if include_file not in external_files:
                        external_files.append(include_file)
    else:
        for header in headers:
            for imports_complete in header.imports:
                import_class_name = imports_complete.split('.')[-1]
                if import_class_name in header_file_degree:
                    header_file_degree[header.key] += 1
                    point_to[import_class_name].append(header)
                else:
                    if (import_class_name + '.java') not in external_files:
                        external_files.append(import_class_name + '.java')


    
    queue = deque([header for header in headers if header_file_degree[header.key] == 0])
    while queue:
        current_header = queue.popleft()
        sorted_headers.append(current_header)
        for point in point_to[current_header.key]:
            header_file_degree[point.key] -= 1
            if header_file_degree[point.key] == 0:
                queue.append(point)

    if max(header_file_degree.values()) > 0:
        print("存在循环依赖，无法排序")
        unsorted_headers = []
        for key, degree in header_file_degree.items():
            if degree > 0:
                if key == "translated":
                    print(f"{key}, include {[file for file in find(headers, key).external_header_files if file not in external_files]}") # type: ignore
                else:
                    print(f"{key}, import {[file.split('.')[-1] for file in find(headers, key).imports if (file.split('.')[-1] + ".java") not in external_files]}") # type: ignore
                unsorted_headers.append(find(headers, key))
        # return sorted_headers.extend(unsorted_headers)
        sorted_headers.extend(unsorted_headers) # 先执行扩展操作
        return sorted_headers                   # 然后返回列表对象
    sorted_headers.reverse()
    return sorted_headers
                

def save_nodes(data, file_path: str):
    """
    将图数据以 pickle 二进制形式保存到文件。

    Args:
        data: 待保存的数据对象。
        file_path: 输出文件路径。

    Returns:
        None。
    """
    with open(file_path, 'wb') as f:
        pickle.dump(data, f)
    print(f"方法节点已保存到 {file_path}")

def load_nodes(file_path):
    """
    从 pickle 文件加载图数据。

    Args:
        file_path: 输入文件路径。

    Returns:
        反序列化得到的数据对象。
    """
    with open(file_path, 'rb') as f:
        return pickle.load(f)

def retrieve(split_dir:str, method_call_path:str, output_dir_path:str):
    """
    从分割数据与调用关系构建完整翻译图。

    职责：
    - 调用 find_method 提取 Header 与 Method。
    - 调用 build_call_graph 构建方法调用关系。
    - 调用 get_ordered_method_groups 对方法分层。
    - 将方法与头文件信息分别写入输出文件，并组装最终数据。

    Args:
        split_dir: 分割 JSON 目录。
        method_call_path: 方法调用关系文件路径。
        output_dir_path: 输出目录路径。

    Returns:
        dict，包含 "method_nodes"（分层方法）与 "headers" 的数据。
    """
    log_path = os.path.join(output_dir_path, "log.txt")
    method_output_path = os.path.join(output_dir_path, "method_output.txt")
    header_output_path = os.path.join(output_dir_path, "header_output.txt")

    with open(log_path, "w", encoding="utf-8") as log_file:
        method_nodes, headers = find_method(split_dir, log_file)
        # for method_key, method in method_nodes.items():
        #     print(method_key)
        # break
        build_call_graph(method_call_path, method_nodes, log_file)
        sorted_methods = get_ordered_method_groups(method_nodes)
        

    with open(method_output_path, "w", encoding="utf-8") as f:
        for index, layer in enumerate[Any](sorted_methods):
            f.write(f"layer{index}==============================================\n")
            for node in layer:
                f.write(str(node))

    with open(header_output_path, "w", encoding="utf-8") as f:
        for header in headers:
            f.write(f"header==========\n")
            f.write(header.source_code)

    data = {"method_nodes": sorted_methods, "headers": headers}
    

    return data

def retrieve_project(ai_name, project_name, version):
    """
    供上层流水线调用的入口，按项目配置检索并构建翻译图。

    职责：
    - 根据路径配置获取分割目录、输出目录与方法调用文件。
    - 调用 retrieve 构建图数据。
    - 输出图摘要与按依赖排序后的头文件顺序日志。

    Args:
        ai_name: AI 名称标识。
        project_name: 项目名称。
        version: 版本标识。

    Returns:
        dict，包含 "method_nodes" 与 "headers" 的数据。
    """
    split_dir_path = cfg_split_output_dir_path(project_name, version)
    output_dir_path = cfg_binary_graph_dir_path(ai_name, project_name, version)
    method_call_path = cfg_method_call_file_path(project_name)
    data = retrieve(str(split_dir_path), str(method_call_path), str(output_dir_path))
    # return
    headers = data["headers"]
    methods = data["method_nodes"]

    with open(output_dir_path/'output.txt', 'w', encoding='utf-8') as f:
        for header in headers:
            f.write("===============================================\n")
            f.write(header.key+'\n')
            for method in header.methods:
                f.write('    '+method.key+'\n')
                parents = [parent.key for parent in method.parents]
                f.write('      Parents: '+','.join(parents)+'\n')
                children = [child.key for child in method.children]
                f.write('      Children: '+','.join(children)+'\n')

    print(len(headers), sum([len(layer) for layer in methods]))

    sorted_headers = sort_headers(headers)
    for header in sorted_headers: #type: ignore
        print(header.key)

    return data


if __name__ == '__main__':
    ai_name = 'deepseek'
    version = 'v4_1'
    # project_names = cfg_all_project_names(version)
    project_names = ['ClassStructureByChildClassTestCase']
    for project_name in project_names:
        data = retrieve_project(ai_name, project_name, version)
                # print(erased_signature)
                


    
