from __future__ import annotations

import argparse
import sys
import textwrap
from pathlib import Path
from typing import Iterable, Sequence


APPROACH_DIR = Path(__file__).resolve().parents[1]
if str(APPROACH_DIR) not in sys.path:
    sys.path.append(str(APPROACH_DIR))

from graph import Header, Method, Project
from path_config import cfg_graph_dir_path, cfg_latest_run_id, cfg_run_graph_dir


def _flatten_method_layers(method_layers: Sequence[Sequence[Method]]) -> list[Method]:
    return [method for layer in method_layers for method in layer]


def _resolve_graph_dir(args: argparse.Namespace) -> Path:
    if args.graph_dir:
        return args.graph_dir

    if args.run_id == "latest":
        latest_run_id = cfg_latest_run_id(args.ai, args.project, args.version)
        if latest_run_id:
            return cfg_run_graph_dir(args.ai, args.project, args.version, latest_run_id)
        print("No timestamped run found; falling back to the legacy graph directory.")
        return cfg_graph_dir_path(args.ai, args.project, args.version)

    return cfg_run_graph_dir(args.ai, args.project, args.version, args.run_id)


def _header_edges(project: Project, by: str) -> list[tuple[str, str]]:
    header_by_key = {header.key: header for header in project.headers}
    edges: set[tuple[str, str]] = set()

    for header in project.headers:
        if by == "translated":
            _, included_headers = project.get_included(header)
            for included in included_headers:
                edges.add((included.key, header.key))
        else:
            for imp in header.imports:
                import_key = imp.split(".")[-1]
                if import_key in header_by_key:
                    edges.add((import_key, header.key))

    return sorted(edges)


def _method_edges(methods: Iterable[Method]) -> list[tuple[str, str]]:
    methods = list(methods)
    method_keys = {method.key for method in methods}
    edges: set[tuple[str, str]] = set()
    for method in methods:
        for child in method.children:
            if child.key in method_keys:
                # Dependency -> dependent. This makes dependency flow left to right.
                edges.add((child.key, method.key))
    return sorted(edges)


def _topological_layers(node_keys: Sequence[str], edges: Sequence[tuple[str, str]]) -> list[list[str]]:
    outgoing = {key: set() for key in node_keys}
    incoming = {key: set() for key in node_keys}
    for src, dst in edges:
        if src not in outgoing or dst not in incoming or src == dst:
            continue
        outgoing[src].add(dst)
        incoming[dst].add(src)

    remaining = set(node_keys)
    layers: list[list[str]] = []
    while remaining:
        ready = sorted([key for key in remaining if not (incoming[key] & remaining)])
        if not ready:
            # Cyclic component fallback: keep deterministic output and place the
            # remaining SCC-like nodes in one layer.
            ready = sorted(remaining)
        layers.append(ready)
        remaining.difference_update(ready)
    return layers


def _method_layers(project: Project, methods: Sequence[Method]) -> list[list[str]]:
    allowed = {method.key for method in methods}
    layers: list[list[str]] = []
    for layer in project.methods:
        keys = [method.key for method in layer if method.key in allowed]
        if keys:
            layers.append(keys)
    return layers or _topological_layers([method.key for method in methods], _method_edges(methods))


def _wrap_label(label: str, width: int) -> str:
    return "\n".join(textwrap.wrap(label, width=width, break_long_words=False)) or label


def _draw_layered_graph(
    *,
    title: str,
    nodes: dict[str, str],
    layers: Sequence[Sequence[str]],
    edges: Sequence[tuple[str, str]],
    output: Path,
    node_colors: dict[str, str] | None = None,
    dpi: int = 220,
    label_width: int = 24,
) -> None:
    import matplotlib.pyplot as plt
    from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

    if not nodes:
        raise ValueError(f"No nodes available for {title}")

    node_colors = node_colors or {}
    x_gap = 4.2
    y_gap = 1.05
    box_w = 3.1
    box_h = 0.62
    max_layer_size = max(len(layer) for layer in layers) if layers else 1

    fig_w = max(12.0, len(layers) * 3.4)
    fig_h = max(7.0, max_layer_size * 0.72 + 2.0)
    fig, ax = plt.subplots(figsize=(fig_w, fig_h))
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")
    ax.axis("off")

    positions: dict[str, tuple[float, float]] = {}
    for layer_idx, layer in enumerate(layers):
        layer_height = (len(layer) - 1) * y_gap
        start_y = layer_height / 2
        for row_idx, key in enumerate(layer):
            x = layer_idx * x_gap
            y = start_y - row_idx * y_gap
            positions[key] = (x, y)

    for src, dst in edges:
        if src not in positions or dst not in positions:
            continue
        sx, sy = positions[src]
        dx, dy = positions[dst]
        same_or_backwards = dx <= sx
        rad = 0.24 if same_or_backwards else 0.04
        color = "#8a99a8" if same_or_backwards else "#536878"
        arrow = FancyArrowPatch(
            (sx + box_w / 2, sy),
            (dx - box_w / 2, dy),
            arrowstyle="-|>",
            mutation_scale=10,
            linewidth=0.8,
            color=color,
            alpha=0.42,
            connectionstyle=f"arc3,rad={rad}",
            zorder=1,
        )
        ax.add_patch(arrow)

    for key, (x, y) in positions.items():
        color = node_colors.get(key, "#eaf2f8")
        box = FancyBboxPatch(
            (x - box_w / 2, y - box_h / 2),
            box_w,
            box_h,
            boxstyle="round,pad=0.035,rounding_size=0.06",
            linewidth=1.0,
            edgecolor="#2f3e46",
            facecolor=color,
            zorder=3,
        )
        ax.add_patch(box)
        ax.text(
            x,
            y,
            _wrap_label(nodes[key], label_width),
            ha="center",
            va="center",
            fontsize=7.6,
            color="#1f2d3d",
            zorder=4,
        )

    xs = [pos[0] for pos in positions.values()]
    ys = [pos[1] for pos in positions.values()]
    ax.set_xlim(min(xs) - box_w, max(xs) + box_w)
    ax.set_ylim(min(ys) - 1.25, max(ys) + 1.65)
    ax.text(
        (min(xs) + max(xs)) / 2,
        max(ys) + 1.15,
        title,
        ha="center",
        va="center",
        fontsize=16,
        fontweight="bold",
        color="#17202a",
    )

    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, dpi=dpi, bbox_inches="tight")
    plt.close(fig)


def draw_header_topology(project: Project, output: Path, by: str, dpi: int) -> None:
    headers = sorted(project.headers, key=lambda header: header.key)
    nodes = {header.key: header.translated_class_name or header.key for header in headers}
    edges = _header_edges(project, by)
    layers = _topological_layers([header.key for header in headers], edges)
    colors = {}
    for header in headers:
        if header.latest_compile_status == "success":
            colors[header.key] = "#d5f5e3"
        elif header.latest_compile_status in {"failed", "timeout"}:
            colors[header.key] = "#fadbd8"
        elif header.source_kind == "generated_external":
            colors[header.key] = "#fef5e7"
        else:
            colors[header.key] = "#eaf2f8"

    _draw_layered_graph(
        title=f"{project.name} Class/Header Topology ({by})",
        nodes=nodes,
        layers=layers,
        edges=edges,
        output=output,
        node_colors=colors,
        dpi=dpi,
        label_width=22,
    )


def draw_method_topology(project: Project, output: Path, dpi: int, max_methods: int) -> None:
    methods = _flatten_method_layers(project.methods)
    if max_methods > 0 and len(methods) > max_methods:
        methods = sorted(
            methods,
            key=lambda method: len(method.children) + len(method.parents),
            reverse=True,
        )[:max_methods]
        print(f"Method graph truncated to {max_methods} most connected methods.")

    nodes = {
        method.key: f"{method.header.key}.{method.get_name()}"
        for method in methods
    }
    edges = _method_edges(methods)
    layers = _method_layers(project, methods)
    colors = {}
    for method in methods:
        if method.skip_translation:
            colors[method.key] = "#e5e8e8"
        elif method.translated_code:
            colors[method.key] = "#d5f5e3"
        else:
            colors[method.key] = "#fcf3cf"

    _draw_layered_graph(
        title=f"{project.name} Method Dependency Topology",
        nodes=nodes,
        layers=layers,
        edges=edges,
        output=output,
        node_colors=colors,
        dpi=dpi,
        label_width=28,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Visualize project class/header and method topology graphs.")
    parser.add_argument("--ai", default="deepseek", help="AI/model name used in output path lookup.")
    parser.add_argument("--project", required=True, help="Project name, e.g. Cookie.")
    parser.add_argument("--version", default="v4_7", help="Approach version.")
    parser.add_argument(
        "--run-id",
        default="latest",
        help="Timestamp run id, or 'latest'. Ignored when --graph-dir is set.",
    )
    parser.add_argument("--graph-dir", type=Path, help="Explicit Project.save graph directory.")
    parser.add_argument("--output-dir", type=Path, help="Output directory for generated diagrams.")
    parser.add_argument("--header-by", choices=["translated", "original"], default="translated")
    parser.add_argument("--kind", choices=["both", "classes", "methods"], default="both")
    parser.add_argument("--format", default="png", help="Image format supported by matplotlib, e.g. png/pdf/svg.")
    parser.add_argument("--dpi", type=int, default=220)
    parser.add_argument(
        "--max-methods",
        type=int,
        default=0,
        help="Limit method nodes for readability. 0 means no limit.",
    )
    args = parser.parse_args()

    graph_dir = _resolve_graph_dir(args)
    if not graph_dir.exists():
        raise FileNotFoundError(f"Graph directory does not exist: {graph_dir}")

    project = Project.load(graph_dir)
    output_dir = args.output_dir or (graph_dir.parent / "topology")
    suffix = args.format.lstrip(".")

    if args.kind in {"both", "classes"}:
        header_output = output_dir / f"class_topology.{suffix}"
        draw_header_topology(project, header_output, args.header_by, args.dpi)
        print(f"Wrote class topology to {header_output}")

    if args.kind in {"both", "methods"}:
        method_output = output_dir / f"method_topology.{suffix}"
        draw_method_topology(project, method_output, args.dpi, args.max_methods)
        print(f"Wrote method topology to {method_output}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
