from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


BATCH_SIZES = [1, 2, 3, 5]
COLORS = {
    1: "#0072B2",
    2: "#E69F00",
    3: "#009E73",
    5: "#CC79A7",
}
MARKERS = {1: "o", 2: "s", 3: "D", 5: "^"}
HATCHES = {1: "", 2: "//", 3: "xx", 5: ".."}


# 功能：解析实验汇总文件并生成批大小敏感性分析图。
# 参数：无；命令行参数提供汇总 JSON 与输出目录。
# 返回：成功时返回 0。
def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate publication figures for the header batch-size experiment."
    )
    parser.add_argument("summary_json", type=Path)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()

    data = json.loads(args.summary_json.read_text(encoding="utf-8"))
    aggregate = pd.DataFrame(data["aggregate"])
    rows = pd.DataFrame(data["rows"])
    args.output_dir.mkdir(parents=True, exist_ok=True)

    _configure_style()
    _plot_aggregate(aggregate, args.output_dir)
    _plot_project_heatmap(rows, args.output_dir)
    trajectory = _build_trajectory(data["rows"])
    trajectory.to_csv(args.output_dir / "round_trajectory.csv", index=False, encoding="utf-8")
    _plot_trajectory(trajectory, args.output_dir)
    _plot_key_results(rows, trajectory, args.output_dir)
    _plot_overview(aggregate, rows, trajectory, args.output_dir)
    _write_captions(args.output_dir)
    print(f"Figures written to {args.output_dir}")
    return 0


def _configure_style() -> None:
    sns.set_theme(style="whitegrid")
    plt.rcParams.update({
        "font.family": "serif",
        "font.serif": ["Times New Roman", "Times", "DejaVu Serif"],
        "font.size": 9,
        "axes.labelsize": 10,
        "axes.titlesize": 10,
        "xtick.labelsize": 9,
        "ytick.labelsize": 9,
        "legend.fontsize": 8.5,
        "axes.linewidth": 0.8,
        "grid.linewidth": 0.5,
        "grid.alpha": 0.3,
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
        "svg.fonttype": "none",
    })


def _plot_aggregate(aggregate: pd.DataFrame, output_dir: Path) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(7.15, 2.75))
    _draw_success_bars(axes[0], aggregate)
    _draw_convergence_bars(axes[1], aggregate)
    axes[0].text(-0.17, 1.05, "(a)", transform=axes[0].transAxes, fontweight="bold")
    axes[1].text(-0.17, 1.05, "(b)", transform=axes[1].transAxes, fontweight="bold")
    fig.tight_layout(w_pad=2.0)
    _save(fig, output_dir / "fig_batch_size_aggregate")


def _draw_success_bars(ax: plt.Axes, aggregate: pd.DataFrame) -> None:
    aggregate = aggregate.set_index("batch_size").loc[BATCH_SIZES].reset_index()
    x = np.arange(len(BATCH_SIZES))
    width = 0.36
    micro = aggregate["source_micro_success_rate"].to_numpy() * 100
    macro = aggregate["source_macro_success_rate"].to_numpy() * 100
    bars_micro = ax.bar(
        x - width / 2,
        micro,
        width,
        color=[COLORS[size] for size in BATCH_SIZES],
        edgecolor="black",
        linewidth=0.55,
        label="Micro average",
    )
    bars_macro = ax.bar(
        x + width / 2,
        macro,
        width,
        color="white",
        edgecolor=[COLORS[size] for size in BATCH_SIZES],
        linewidth=1.2,
        hatch="///",
        label="Macro average",
    )
    for bars in (bars_micro, bars_macro):
        for bar in bars:
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + 0.7,
                f"{bar.get_height():.1f}",
                ha="center",
                va="bottom",
                fontsize=7.5,
            )
    ax.set_ylabel("Header compilation success (%)")
    ax.set_xlabel("Header batch size")
    ax.set_xticks(x, BATCH_SIZES)
    ax.set_ylim(75, 101)
    ax.set_yticks([75, 80, 85, 90, 95, 100])
    ax.grid(axis="x", visible=False)
    ax.legend(loc="lower left", frameon=True)


def _draw_convergence_bars(ax: plt.Axes, aggregate: pd.DataFrame) -> None:
    aggregate = aggregate.set_index("batch_size").loc[BATCH_SIZES].reset_index()
    x = np.arange(len(BATCH_SIZES))
    rates = aggregate["project_convergence_rate"].to_numpy() * 100
    bars = ax.bar(
        x,
        rates,
        width=0.58,
        color=[COLORS[size] for size in BATCH_SIZES],
        edgecolor="black",
        linewidth=0.55,
    )
    for bar, count in zip(bars, aggregate["converged_projects"]):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 2,
            f"{int(count)}/9",
            ha="center",
            va="bottom",
            fontsize=8,
        )
    ax.set_ylabel("Fully converged projects (%)")
    ax.set_xlabel("Header batch size")
    ax.set_xticks(x, BATCH_SIZES)
    ax.set_ylim(0, 65)
    ax.set_yticks([0, 20, 40, 60])
    ax.grid(axis="x", visible=False)


def _plot_project_heatmap(rows: pd.DataFrame, output_dir: Path) -> None:
    pivot = _project_rate_pivot(rows)
    annotations = _project_annotations(rows, pivot.index)
    fig, ax = plt.subplots(figsize=(5.2, 3.65))
    sns.heatmap(
        pivot,
        annot=annotations,
        fmt="",
        cmap=sns.color_palette("YlGnBu", as_cmap=True),
        vmin=60,
        vmax=100,
        linewidths=0.7,
        linecolor="white",
        cbar_kws={"label": "Compilation success (%)", "pad": 0.02},
        ax=ax,
    )
    ax.set_xlabel("Header batch size")
    ax.set_ylabel("")
    ax.set_xticklabels([f"BS={size}" for size in BATCH_SIZES], rotation=0)
    ax.tick_params(axis="y", labelrotation=0)
    fig.tight_layout()
    _save(fig, output_dir / "fig_batch_size_project_heatmap")


def _project_rate_pivot(rows: pd.DataFrame) -> pd.DataFrame:
    rows = rows.copy()
    rows["rate"] = rows["source_success"] / rows["source_total"] * 100
    pivot = rows.pivot(index="project", columns="batch_size", values="rate")[BATCH_SIZES]
    project_size = rows.groupby("project")["source_total"].first()
    order = project_size.sort_values(ascending=False).index
    return pivot.loc[order]


def _project_annotations(rows: pd.DataFrame, projects: pd.Index) -> np.ndarray:
    lookup = {
        (row.project, int(row.batch_size)): f"{int(row.source_success)}/{int(row.source_total)}"
        for row in rows.itertuples()
    }
    return np.array([
        [lookup[(project, size)] for size in BATCH_SIZES]
        for project in projects
    ])


def _build_trajectory(rows: list[dict[str, Any]]) -> pd.DataFrame:
    records: list[dict[str, Any]] = []
    for row in rows:
        run_dir = Path(row["run_dir"])
        status_path = run_dir / "result" / "header_iteration_status.csv"
        status = pd.read_csv(status_path)
        source_headers = _source_header_names(run_dir / "graph")
        status = status[status["header_name"].isin(source_headers)].copy()
        status["round"] = status["round"].astype(int)
        status["compile_success"] = status["compile_success"].map(_as_bool)
        final_by_header = (
            status.sort_values("round")
            .groupby("header_name", observed=False)
            .tail(1)
            .set_index("header_name")["compile_success"]
        )
        for round_idx in range(1, int(row["header_max_rounds"]) + 1):
            available = status[status["round"] <= round_idx]
            latest = (
                available.sort_values("round")
                .groupby("header_name", observed=False)
                .tail(1)
                .set_index("header_name")["compile_success"]
            )
            if round_idx > int(row["rounds_used"]):
                latest = final_by_header
            for header_name in source_headers:
                records.append({
                    "project": row["project"],
                    "batch_size": int(row["batch_size"]),
                    "round": round_idx,
                    "header": header_name,
                    "success": bool(latest.get(header_name, False)),
                })
    trajectory = pd.DataFrame(records)
    return (
        trajectory.groupby(["batch_size", "round"], as_index=False)
        .agg(success_headers=("success", "sum"), total_headers=("success", "size"))
        .assign(success_rate=lambda frame: frame.success_headers / frame.total_headers)
    )


def _source_header_names(graph_dir: Path) -> set[str]:
    names = set()
    for path in graph_dir.rglob("*.json"):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if (
            "translated_class_name" in data
            and "methods" in data
            and data.get("source_kind") != "generated_external"
        ):
            names.add(str(data["key"]))
    return names


def _as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"true", "1", "yes"}


def _plot_trajectory(trajectory: pd.DataFrame, output_dir: Path) -> None:
    fig, ax = plt.subplots(figsize=(4.7, 3.15))
    _draw_trajectory(ax, trajectory)
    fig.tight_layout()
    _save(fig, output_dir / "fig_batch_size_round_trajectory")


# 功能：按照论文参考风格绘制不同批大小的逐轮收敛曲线。
# 参数：ax 为目标坐标轴，trajectory 为逐轮汇总数据。
# 返回：无；直接修改传入的坐标轴。
def _draw_trajectory(ax: plt.Axes, trajectory: pd.DataFrame) -> None:
    for batch_size in BATCH_SIZES:
        selected = trajectory[trajectory["batch_size"] == batch_size]
        ax.plot(
            selected["round"],
            selected["success_rate"],
            color=COLORS[batch_size],
            marker="o",
            linewidth=1.15,
            markersize=3.8,
            markeredgewidth=0.4,
            label=f"BS={batch_size}",
        )
    ax.set_xlabel("Header translation round")
    ax.set_ylabel("Source-header success")
    ax.set_xticks(range(1, 6))
    ax.set_ylim(0.25, 1.0)
    ax.set_yticks(np.arange(0.3, 1.01, 0.1))
    ax.grid(True, color="#b0b0b0", linewidth=0.65, alpha=0.75)
    ax.legend(ncol=2, loc="lower right", frameon=True)


# 功能：将逐模块结果与轮次轨迹合并为论文正文使用的精简双联图。
# 参数：rows 为逐模块实验结果，trajectory 为逐轮汇总数据，output_dir 为输出目录。
# 返回：无；在输出目录中写入 PDF、SVG 和 PNG 三种格式。
def _plot_key_results(
    rows: pd.DataFrame,
    trajectory: pd.DataFrame,
    output_dir: Path,
) -> None:
    fig, (ax_heatmap, ax_trajectory) = plt.subplots(
        1,
        2,
        figsize=(7.15, 3.25),
        gridspec_kw={"width_ratios": [1.42, 1.0]},
    )

    pivot = _project_rate_pivot(rows)
    annotations = _project_annotations(rows, pivot.index)
    sns.heatmap(
        pivot,
        annot=annotations,
        fmt="",
        annot_kws={"fontsize": 6.7},
        cmap=sns.color_palette("YlGnBu", as_cmap=True),
        vmin=60,
        vmax=100,
        linewidths=0.55,
        linecolor="white",
        cbar_kws={"label": "Compilation success", "pad": 0.02, "shrink": 0.92},
        ax=ax_heatmap,
    )
    ax_heatmap.set_xlabel("Header batch size")
    ax_heatmap.set_ylabel("")
    ax_heatmap.set_xticklabels([str(size) for size in BATCH_SIZES], rotation=0)
    ax_heatmap.tick_params(axis="y", labelrotation=0, labelsize=7.0)

    _draw_trajectory(ax_trajectory, trajectory)
    ax_heatmap.set_title("(a) Per-module outcomes", pad=5)
    ax_trajectory.set_title("(b) Round-wise convergence", pad=5)
    fig.tight_layout(w_pad=1.5)
    _save(fig, output_dir / "fig_batch_size_key_results")


def _plot_overview(
    aggregate: pd.DataFrame,
    rows: pd.DataFrame,
    trajectory: pd.DataFrame,
    output_dir: Path,
) -> None:
    fig = plt.figure(figsize=(7.15, 6.1))
    grid = fig.add_gridspec(2, 2, height_ratios=[0.92, 1.2], hspace=0.42, wspace=0.34)
    ax_success = fig.add_subplot(grid[0, 0])
    ax_convergence = fig.add_subplot(grid[0, 1])
    ax_heatmap = fig.add_subplot(grid[1, 0])
    ax_trajectory = fig.add_subplot(grid[1, 1])

    _draw_success_bars(ax_success, aggregate)
    _draw_convergence_bars(ax_convergence, aggregate)

    pivot = _project_rate_pivot(rows)
    annotations = _project_annotations(rows, pivot.index)
    sns.heatmap(
        pivot,
        annot=annotations,
        fmt="",
        annot_kws={"fontsize": 6.5},
        cmap=sns.color_palette("YlGnBu", as_cmap=True),
        vmin=60,
        vmax=100,
        linewidths=0.55,
        linecolor="white",
        cbar=False,
        ax=ax_heatmap,
    )
    ax_heatmap.set_xlabel("Header batch size")
    ax_heatmap.set_ylabel("")
    ax_heatmap.set_xticklabels([f"BS={size}" for size in BATCH_SIZES], rotation=0)
    ax_heatmap.tick_params(axis="y", labelrotation=0, labelsize=6.7)

    _draw_trajectory(ax_trajectory, trajectory)
    for label, ax in zip("abcd", [ax_success, ax_convergence, ax_heatmap, ax_trajectory]):
        ax.text(-0.18, 1.06, f"({label})", transform=ax.transAxes, fontweight="bold")
    _save(fig, output_dir / "fig_batch_size_overview")


def _save(fig: plt.Figure, base_path: Path) -> None:
    for suffix in ("pdf", "svg", "png"):
        kwargs = {"dpi": 300} if suffix == "png" else {}
        fig.savefig(base_path.with_suffix(f".{suffix}"), bbox_inches="tight", **kwargs)
    plt.close(fig)


def _write_captions(output_dir: Path) -> None:
    text = """# Suggested Figure Captions

## Aggregate

**Effect of header batch size on translation quality.** (a) Micro- and macro-averaged source-header compilation success rates across nine projects. (b) Fraction of projects in which all source and generated headers compile within five rounds. Batch size 3 achieves the highest success and convergence rates.

## Project Heatmap

**Per-project source-header compilation success under different batch sizes.** Each cell reports compiled source headers over all source headers after at most five translation rounds. Batch size 3 provides the strongest overall performance, while a few projects favor batch size 1, indicating sensitivity to dependency structure.

## Round Trajectory

**Source-header compilation success over header translation rounds.** Rates are micro-averaged over the same 164 source headers. Runs that converge before round five retain their final status in later rounds. Batch size 3 converges to the highest final success rate.

## Overview

**Header batch-size ablation over nine Java-to-C++ translation projects.** The panels show (a) source-header success, (b) project-level convergence, (c) per-project outcomes, and (d) round-wise convergence. All experiments use DeepSeek and a maximum of five header translation rounds.
"""
    (output_dir / "figure_captions.md").write_text(text, encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
