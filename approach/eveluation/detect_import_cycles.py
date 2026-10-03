from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Set


p_dir = str(Path(__file__).parent)
pp_dir = str(Path(__file__).parent.parent)
if pp_dir not in sys.path:
    sys.path.append(pp_dir)
if p_dir not in sys.path:
    sys.path.append(p_dir)

from path_config import cfg_source_code_dir_path


PACKAGE_PATTERN = re.compile(r"^\s*package\s+([\w.]+)\s*;", re.MULTILINE)
IMPORT_PATTERN = re.compile(r"^\s*import\s+(?:static\s+)?([\w.*]+)\s*;", re.MULTILINE)


@dataclass(frozen=True)
class JavaSourceFile:
    path: Path
    package: str
    type_name: str
    qualified_name: str
    imports: tuple[str, ...]


def remove_java_comments(source: str) -> str:
    result = []
    i = 0
    in_string = False
    in_char = False
    in_line_comment = False
    in_block_comment = False
    escape = False

    while i < len(source):
        ch = source[i]
        nxt = source[i + 1] if i + 1 < len(source) else ""

        if in_line_comment:
            if ch == "\n":
                in_line_comment = False
                result.append(ch)
            i += 1
            continue

        if in_block_comment:
            if ch == "*" and nxt == "/":
                in_block_comment = False
                i += 2
            else:
                if ch == "\n":
                    result.append(ch)
                i += 1
            continue

        if in_string or in_char:
            result.append(ch)
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif in_string and ch == '"':
                in_string = False
            elif in_char and ch == "'":
                in_char = False
            i += 1
            continue

        if ch == "/" and nxt == "/":
            in_line_comment = True
            i += 2
            continue

        if ch == "/" and nxt == "*":
            in_block_comment = True
            i += 2
            continue

        if ch == '"':
            in_string = True
        elif ch == "'":
            in_char = True

        result.append(ch)
        i += 1

    return "".join(result)


def parse_java_file(path: Path, project_dir: Path) -> JavaSourceFile:
    source = path.read_text(encoding="utf-8", errors="replace")
    source_without_comments = remove_java_comments(source)

    package_match = PACKAGE_PATTERN.search(source_without_comments)
    package = package_match.group(1) if package_match else ""
    type_name = path.stem
    qualified_name = f"{package}.{type_name}" if package else type_name
    imports = tuple(IMPORT_PATTERN.findall(source_without_comments))

    return JavaSourceFile(
        path=path.relative_to(project_dir),
        package=package,
        type_name=type_name,
        qualified_name=qualified_name,
        imports=imports,
    )


def collect_java_files(project_dir: Path) -> List[JavaSourceFile]:
    return [
        parse_java_file(path, project_dir)
        for path in sorted(project_dir.rglob("*.java"))
        if path.is_file()
    ]


def build_import_graph(files: Iterable[JavaSourceFile]) -> Dict[str, Set[str]]:
    files = list(files)
    known_types = {file.qualified_name: file for file in files}
    package_to_types: Dict[str, List[str]] = {}
    graph: Dict[str, Set[str]] = {file.qualified_name: set() for file in files}

    for file in files:
        package_to_types.setdefault(file.package, []).append(file.qualified_name)

    for file in files:
        for imported_name in file.imports:
            if imported_name.endswith(".*"):
                imported_package = imported_name[:-2]
                for qualified_name in package_to_types.get(imported_package, []):
                    if qualified_name != file.qualified_name:
                        graph[file.qualified_name].add(qualified_name)
                continue

            target_name = imported_name
            if target_name not in known_types and "." in imported_name:
                maybe_type_import = imported_name.rsplit(".", 1)[0]
                if maybe_type_import in known_types:
                    target_name = maybe_type_import

            if target_name in known_types and target_name != file.qualified_name:
                graph[file.qualified_name].add(target_name)

    return graph


def canonical_cycle(cycle: List[str]) -> tuple[str, ...]:
    body = cycle[:-1] if cycle and cycle[0] == cycle[-1] else cycle
    if not body:
        return tuple()

    rotations = [tuple(body[i:] + body[:i]) for i in range(len(body))]
    reversed_body = list(reversed(body))
    rotations.extend(tuple(reversed_body[i:] + reversed_body[:i]) for i in range(len(body)))
    return min(rotations)


def find_cycles(graph: Dict[str, Set[str]]) -> List[List[str]]:
    cycles: Set[tuple[str, ...]] = set()
    visited: Set[str] = set()
    active: Set[str] = set()
    stack: List[str] = []

    def dfs(node: str) -> None:
        visited.add(node)
        active.add(node)
        stack.append(node)

        for neighbor in sorted(graph.get(node, set())):
            if neighbor not in visited:
                dfs(neighbor)
            elif neighbor in active:
                cycle_start = stack.index(neighbor)
                cycle = stack[cycle_start:] + [neighbor]
                canonical = canonical_cycle(cycle)
                if canonical:
                    cycles.add(canonical)

        stack.pop()
        active.remove(node)

    for node in sorted(graph):
        if node not in visited:
            dfs(node)

    return [list(cycle) + [cycle[0]] for cycle in sorted(cycles)]


def resolve_project_dir(project_name: str, source_root: Path | None) -> Path:
    if source_root is not None:
        project_dir = source_root / project_name
    else:
        project_dir = cfg_source_code_dir_path(project_name)

    if not project_dir.exists():
        raise FileNotFoundError(f"project source directory does not exist: {project_dir}")
    return project_dir


def analyze_project(project_name: str, source_root: Path | None = None) -> dict:
    project_dir = resolve_project_dir(project_name, source_root)
    java_files = collect_java_files(project_dir)
    graph = build_import_graph(java_files)
    cycles = find_cycles(graph)

    return {
        "project_name": project_name,
        "project_dir": str(project_dir),
        "java_file_count": len(java_files),
        "has_import_cycle": bool(cycles),
        "cycles": cycles,
        "graph": {node: sorted(neighbors) for node, neighbors in sorted(graph.items())},
    }


def print_report(result: dict, show_graph: bool = False) -> None:
    print(f"Project: {result['project_name']}")
    print(f"Source directory: {result['project_dir']}")
    print(f"Java files: {result['java_file_count']}")
    print(f"Has import cycle: {result['has_import_cycle']}")

    if result["cycles"]:
        print("\nImport cycles:")
        for index, cycle in enumerate(result["cycles"], start=1):
            print(f"{index}. {' -> '.join(cycle)}")
    else:
        print("\nNo project-internal import cycles found.")

    if show_graph:
        print("\nProject-internal import graph:")
        for node, neighbors in result["graph"].items():
            if neighbors:
                print(f"{node}: {', '.join(neighbors)}")
            else:
                print(f"{node}:")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Detect project-internal cyclic imports among Java source files."
    )
    parser.add_argument("project_name", help="Project name under source_projects by default.")
    parser.add_argument(
        "--source-root",
        type=Path,
        default=None,
        help="Optional source root. Defaults to repository source_projects.",
    )
    parser.add_argument(
        "--show-graph",
        action="store_true",
        help="Print the project-internal import graph.",
    )
    parser.add_argument(
        "--json-output",
        type=Path,
        default=None,
        help="Optional path to write the analysis result as JSON.",
    )
    args = parser.parse_args()

    result = analyze_project(args.project_name, args.source_root)
    print_report(result, show_graph=args.show_graph)

    if args.json_output:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(
            json.dumps(result, ensure_ascii=False, indent=4),
            encoding="utf-8",
        )

    return 1 if result["has_import_cycle"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
