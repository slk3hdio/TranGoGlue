from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch


def add_box(ax, xy, width, height, title, subtitle, color):
    x, y = xy
    box = FancyBboxPatch(
        (x, y),
        width,
        height,
        boxstyle="round,pad=0.018,rounding_size=0.035",
        linewidth=1.6,
        edgecolor="#233142",
        facecolor=color,
        zorder=2,
    )
    ax.add_patch(box)
    ax.text(
        x + width / 2,
        y + height * 0.62,
        title,
        ha="center",
        va="center",
        fontsize=13,
        fontweight="bold",
        color="#17202a",
        zorder=3,
    )
    ax.text(
        x + width / 2,
        y + height * 0.32,
        subtitle,
        ha="center",
        va="center",
        fontsize=9.5,
        color="#2f3e46",
        linespacing=1.25,
        zorder=3,
    )


def add_arrow(ax, start, end, *, curved=False, label=""):
    style = "arc3,rad=0.18" if curved else "arc3,rad=0.0"
    arrow = FancyArrowPatch(
        start,
        end,
        arrowstyle="-|>",
        mutation_scale=18,
        linewidth=1.5,
        color="#34495e",
        connectionstyle=style,
        zorder=1,
    )
    ax.add_patch(arrow)
    if label:
        lx = (start[0] + end[0]) / 2
        ly = (start[1] + end[1]) / 2 + (0.12 if curved else 0.06)
        ax.text(
            lx,
            ly,
            label,
            ha="center",
            va="center",
            fontsize=9,
            color="#2c3e50",
            bbox={"boxstyle": "round,pad=0.2", "facecolor": "white", "edgecolor": "none", "alpha": 0.9},
            zorder=4,
        )


def draw(output: Path, title: str, dpi: int) -> None:
    fig, ax = plt.subplots(figsize=(13.5, 7.5))
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 7)
    ax.axis("off")

    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")

    ax.text(
        6,
        6.55,
        title,
        ha="center",
        va="center",
        fontsize=18,
        fontweight="bold",
        color="#17202a",
    )
    ax.text(
        6,
        6.18,
        "Compiler-guided iterative synthesis for dependency-aware C++ header generation",
        ha="center",
        va="center",
        fontsize=11,
        color="#536878",
    )

    box_w = 2.35
    box_h = 1.12
    y_top = 4.55
    y_bottom = 2.05

    nodes = {
        "input": (0.65, y_top),
        "context": (3.35, y_top),
        "llm_gen": (6.05, y_top),
        "compiler": (8.75, y_top),
        "feedback": (6.05, y_bottom),
        "repair": (3.35, y_bottom),
        "output": (8.75, y_bottom),
    }

    add_box(
        ax,
        nodes["input"],
        box_w,
        box_h,
        "Java Project",
        "source classes\ninterfaces / enums",
        "#eaf2f8",
    )
    add_box(
        ax,
        nodes["context"],
        box_w,
        box_h,
        "Dependency-aware\nContext",
        "graph order + imports\nincludes + forward decls",
        "#e8f8f5",
    )
    add_box(
        ax,
        nodes["llm_gen"],
        box_w,
        box_h,
        "LLM Header\nSynthesis",
        "Round 1: complete headers\noptional helper headers",
        "#fef5e7",
    )
    add_box(
        ax,
        nodes["compiler"],
        box_w,
        box_h,
        "Local Header\nCompilation",
        "clang++ -fsyntax-only\nper-header status",
        "#f4ecf7",
    )
    add_box(
        ax,
        nodes["feedback"],
        box_w,
        box_h,
        "Structured\nFeedback",
        "local issue extraction\ndependency-block filter",
        "#f9ebea",
    )
    add_box(
        ax,
        nodes["repair"],
        box_w,
        box_h,
        "LLM Patch\nRepair",
        "Round k: modify/add patch\nrollback and retry",
        "#eef7e1",
    )
    add_box(
        ax,
        nodes["output"],
        box_w,
        box_h,
        "Compilable C++\nHeader Set",
        "converged headers\nexternal helper cleanup",
        "#e8daef",
    )

    add_arrow(ax, (3.0, y_top + box_h / 2), (3.35, y_top + box_h / 2))
    add_arrow(ax, (5.7, y_top + box_h / 2), (6.05, y_top + box_h / 2))
    add_arrow(ax, (8.4, y_top + box_h / 2), (8.75, y_top + box_h / 2))
    add_arrow(ax, (9.92, y_top), (9.92, y_bottom + box_h), label="compile result")
    add_arrow(ax, (8.75, y_bottom + box_h / 2), (8.4, y_bottom + box_h / 2))
    add_arrow(ax, (6.05, y_bottom + box_h / 2), (5.7, y_bottom + box_h / 2))
    add_arrow(ax, (4.52, y_bottom + box_h), (6.75, y_top), curved=True, label="localized repair")
    add_arrow(ax, (10.05, y_bottom + box_h), (10.05, y_top), curved=True, label="if not converged")

    ax.text(
        6,
        1.05,
        "Key idea: dependency-aware batching + full initial synthesis + compiler-guided localized patch repair",
        ha="center",
        va="center",
        fontsize=12,
        fontweight="bold",
        color="#1f2d3d",
        bbox={"boxstyle": "round,pad=0.45", "facecolor": "#f8f9f9", "edgecolor": "#ccd1d1"},
    )

    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, dpi=dpi, bbox_inches="tight")
    plt.close(fig)


def main() -> int:
    parser = argparse.ArgumentParser(description="Draw the v4_7 header translation method diagram.")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(__file__).with_name("header_translation_method_diagram.png"),
        help="Output image path. Use .png, .pdf, or any format supported by matplotlib.",
    )
    parser.add_argument("--title", default="v4_7 Header Translation Method", help="Diagram title.")
    parser.add_argument("--dpi", type=int, default=300, help="Output DPI for raster formats.")
    args = parser.parse_args()

    draw(args.output, args.title, args.dpi)
    print(f"Wrote diagram to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
