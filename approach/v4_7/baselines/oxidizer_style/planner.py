from __future__ import annotations

from collections import deque
from typing import Callable, Hashable, Iterable, TypeVar

from graph import Header, Method


NodeT = TypeVar("NodeT")
KeyT = TypeVar("KeyT", bound=Hashable)


def dependency_scc_order(
    nodes: Iterable[NodeT],
    key_of: Callable[[NodeT], KeyT],
    dependencies_of: Callable[[NodeT], Iterable[KeyT]],
) -> list[list[NodeT]]:
    """Return SCC groups in dependency-first order."""
    node_list = list(nodes)
    by_key = {key_of(node): node for node in node_list}
    graph = {
        key: {dep for dep in dependencies_of(node) if dep in by_key and dep != key}
        for key, node in by_key.items()
    }

    index = 0
    indices: dict[KeyT, int] = {}
    lowlinks: dict[KeyT, int] = {}
    stack: list[KeyT] = []
    on_stack: set[KeyT] = set()
    components: list[list[KeyT]] = []

    def strong_connect(key: KeyT) -> None:
        nonlocal index
        indices[key] = index
        lowlinks[key] = index
        index += 1
        stack.append(key)
        on_stack.add(key)

        for dep in sorted(graph[key], key=str):
            if dep not in indices:
                strong_connect(dep)
                lowlinks[key] = min(lowlinks[key], lowlinks[dep])
            elif dep in on_stack:
                lowlinks[key] = min(lowlinks[key], indices[dep])

        if lowlinks[key] != indices[key]:
            return
        component: list[KeyT] = []
        while stack:
            member = stack.pop()
            on_stack.remove(member)
            component.append(member)
            if member == key:
                break
        components.append(component)

    for key in graph:
        if key not in indices:
            strong_connect(key)

    component_of = {
        key: component_idx
        for component_idx, component in enumerate(components)
        for key in component
    }
    component_dependencies: dict[int, set[int]] = {
        idx: set() for idx in range(len(components))
    }
    dependents: dict[int, set[int]] = {idx: set() for idx in range(len(components))}
    for key, deps in graph.items():
        src = component_of[key]
        for dep in deps:
            dst = component_of[dep]
            if src == dst:
                continue
            component_dependencies[src].add(dst)
            dependents[dst].add(src)

    pending = {idx: len(deps) for idx, deps in component_dependencies.items()}
    queue = deque(sorted(idx for idx, count in pending.items() if count == 0))
    ordered: list[list[NodeT]] = []
    while queue:
        idx = queue.popleft()
        ordered.append([by_key[key] for key in sorted(components[idx], key=str)])
        for dependent in sorted(dependents[idx]):
            pending[dependent] -= 1
            if pending[dependent] == 0:
                queue.append(dependent)

    if len(ordered) != len(components):
        raise RuntimeError("failed to produce a complete SCC dependency order")
    return ordered


def header_dependency_groups(headers: list[Header]) -> list[list[Header]]:
    names: dict[str, str] = {}
    for header in headers:
        names[header.key] = header.key
        names[header.key.split(".")[-1]] = header.key
        names[header.key.split("$")[-1]] = header.key

    def dependencies(header: Header) -> set[str]:
        result: set[str] = set()
        candidates = [header.parent_class, *header.interfaces]
        candidates.extend(imp.split(".")[-1] for imp in header.imports)
        for candidate in candidates:
            if not candidate:
                continue
            normalized = candidate.split("<", 1)[0].split(".")[-1].split("$")[-1]
            matched = names.get(normalized)
            if matched:
                result.add(matched)
        return result

    return dependency_scc_order(headers, lambda header: header.key, dependencies)


def method_dependency_groups(methods: list[Method]) -> list[list[Method]]:
    method_keys = {method.key for method in methods}
    return dependency_scc_order(
        methods,
        lambda method: method.key,
        lambda method: (child.key for child in method.children if child.key in method_keys),
    )
