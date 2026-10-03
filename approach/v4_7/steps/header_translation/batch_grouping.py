import random

from graph import Header
from typing import List
from graph.project import Project


def _name_candidates(name: str) -> set[str]:
    """生成给定名称的各种候选写法集合，用于跨 Java/C++ 命名风格匹配。

    参数:
        name: 原始名称字符串。

    返回:
        一个包含各种候选写法的字符串集合（原始名、包尾、C++ 命名、Java 命名、短名等）。
    """
    if not name:
        return set()

    raw = str(name).strip()
    if not raw:
        return set()

    package_tail = raw.split(".")[-1]
    cpp_name = package_tail.replace("$", "::")
    java_name = package_tail.replace("::", "$")
    short_name = cpp_name.split("::")[-1]

    return {raw, package_tail, cpp_name, java_name, short_name}


def _header_name_candidates(header: Header) -> set[str]:
    """收集一个 Header 对象对应的全部候选名称写法。

    参数:
        header: 待收集候选名的 Header 对象。

    返回:
        该 Header 的 key 与 translated_class_name 的所有候选写法集合。
    """
    candidates = set()
    candidates.update(_name_candidates(header.key))
    candidates.update(_name_candidates(header.translated_class_name))
    return candidates


def _find_header_by_class_name(headers: List[Header], name: str) -> Header | None:
    """在 Header 列表中按类名（或其候选写法）查找对应的 Header。

    参数:
        headers: 待查找的 Header 列表。
        name: 要匹配的类名。

    返回:
        命中的 Header，未找到时返回 None。
    """
    candidates = _name_candidates(name)
    if not candidates:
        return None

    for header in headers:
        if candidates & _header_name_candidates(header):
            return header
    return None


def _collect_inheritance_related_keys(header: Header, all_headers: List[Header]) -> List[str]:
    """收集与给定 Header 存在继承/接口关系的相关 Header 的 key 列表。

    参数:
        header: 待分析的基准 Header。
        all_headers: 全部 Header 列表。

    返回:
        与之相关的 Header key 列表（去重、保持顺序）。
    """
    related: List[str] = []

    def add(candidate: Header | None) -> None:
        """将一个候选 Header 加入相关列表（跳过自身与重复项）。"""
        if candidate is None:
            return
        if candidate.key == header.key:
            return
        if candidate.key not in related:
            related.append(candidate.key)

    add(_find_header_by_class_name(all_headers, header.parent_class))
    for interface_name in header.interfaces:
        add(_find_header_by_class_name(all_headers, interface_name))

    current_names = _header_name_candidates(header)
    for candidate in all_headers:
        if candidate.key == header.key:
            continue
        parent_matches = _name_candidates(candidate.parent_class) & current_names
        interface_matches = any(_name_candidates(interface_name) & current_names for interface_name in candidate.interfaces)
        if parent_matches or interface_matches:
            add(candidate)

    return related


def _dedupe_preserve_order(keys: List[str]) -> List[str]:
    """在保持原有顺序的前提下对 key 列表去重。

    参数:
        keys: 可能包含重复项的 key 列表。

    返回:
        去重后且保持原顺序的 key 列表。
    """
    result: List[str] = []
    seen: set[str] = set()
    for key in keys:
        if key in seen:
            continue
        result.append(key)
        seen.add(key)
    return result


def _can_use_as_fallback(candidate: Header, batch: List[Header], all_headers: List[Header]) -> bool:
    """判断候选 Header 是否可作为当前批次的回退补充成员。

    参数:
        candidate: 待判断的候选 Header。
        batch: 当前已组成的批次 Header 列表。
        all_headers: 全部 Header 列表。

    返回:
        若候选 Header 无关联依赖，或其关联依赖已在批次中，则为 True，否则为 False。
    """
    related_keys = set(_collect_inheritance_related_keys(candidate, all_headers))
    if not related_keys:
        return True

    batch_keys = {header.key for header in batch}
    return bool(related_keys & batch_keys)


def group_headers(
    target_headers: List[Header],
    all_headers: List[Header],
    group_size: int = 3,
    strategy: str = "dependency",
    random_seed: int | None = None,
) -> List[List[Header]]:
    """按指定策略将目标 Header 分组为多个批次。

    职责:
        依据继承/包含/导入/前置声明关系将目标 Header 聚合成大小不超过
        group_size 的批次，尽量保持依赖就近，不足时使用回退成员补齐。

    参数:
        target_headers: 需要分组的 Header 列表。
        all_headers: 全部 Header 列表（用于解析依赖）。
        group_size: 每个批次的期望最大大小，默认为 3。
        strategy: 分组策略；dependency 尽量保持依赖就近，random 则随机切分。
        random_seed: random 策略的可复现随机种子；为空时使用系统随机源。

    返回:
        由若干 Header 批次组成的列表，每个批次为一个 Header 列表。
    """
    if not target_headers:
        return []
    if group_size < 1:
        raise ValueError("group_size must be positive")
    if strategy == "random":
        shuffled_headers = list(target_headers)
        random.Random(random_seed).shuffle(shuffled_headers)
        return [
            shuffled_headers[index:index + group_size]
            for index in range(0, len(shuffled_headers), group_size)
        ]
    if strategy != "dependency":
        raise ValueError(f"unsupported header grouping strategy: {strategy}")

    temp_project = Project("_group_temp", [], all_headers)
    sorted_groups = temp_project.sort_headers(by="translated")

    sorted_headers: List[Header] = []
    for group in sorted_groups:
        sorted_headers.extend(group)

    header_index = {h.key: h for h in all_headers}
    assigned: set[str] = set()
    batches: List[List[Header]] = []

    for base_header in sorted_headers:
        if base_header.key in assigned or base_header not in target_headers:
            continue

        batch: List[Header] = [base_header]
        assigned.add(base_header.key)

        inheritance_keys = [
            k
            for k in _collect_inheritance_related_keys(base_header, all_headers)
            if k not in assigned and header_index.get(k) in target_headers
        ]

        _, included = temp_project.get_included(base_header)
        included_keys = [i.key for i in included if i.key not in assigned and i in target_headers]

        imported_keys: List[str] = []
        for imp in base_header.imports:
            import_class = imp.split(".")[-1]
            h = header_index.get(import_class)
            if h and h.key not in assigned and h in target_headers:
                imported_keys.append(h.key)

        forward_declared_keys: List[str] = []
        for fd_name in base_header.get_forward_declare():
            h = Header.find_by_translated_class_name(all_headers, fd_name)
            if h and h.key not in assigned and h in target_headers:
                forward_declared_keys.append(h.key)

        pool: List[str] = []
        pool.extend(inheritance_keys)
        pool.extend(included_keys)
        pool.extend(imported_keys)
        pool.extend(forward_declared_keys)

        pool = _dedupe_preserve_order(pool)

        remaining = group_size - len(batch)
        if remaining > 0 and pool:
            for k in pool:
                if len(batch) >= group_size:
                    break
                h = header_index.get(k)
                if h and h.key not in assigned:
                    batch.append(h)
                    assigned.add(h.key)

        remaining = group_size - len(batch)
        if remaining > 0:
            for h in sorted_headers:
                if len(batch) >= group_size:
                    break
                if (
                    h in target_headers
                    and h.key not in assigned
                    and _can_use_as_fallback(h, batch, all_headers)
                ):
                    batch.append(h)
                    assigned.add(h.key)

        batches.append(batch)

    return batches
