"""
Header iteration compile visualization utilities.

Generate round-by-round header compile status CSV files and heatmaps from
persisted graph `compile_reports`.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

import matplotlib.pyplot as plt
from matplotlib.colors import BoundaryNorm, ListedColormap
import pandas as pd
import seaborn as sns

from graph import Project


plt.style.use("seaborn-v0_8-whitegrid")
sns.set_palette("husl")

FONT = "Times New Roman"
STATUS_COLUMNS = [
    "version",
    "project_name",
    "ai_name",
    "header_name",
    "round",
    "compile_success",
    "status",
    "has_local_issues",
    "has_project_dependency_issues",
    "blocked_by_dependency",
    "issue_count",
    "project_dependency_issue_count",
    "external_issue_count",
    "primary_issue_type",
    "primary_project_dependency_issue_type",
    "primary_external_issue_type",
]
STATUS_ORDER = ["not_run", "dependency_blocked", "local_failed", "success"]
STATUS_TO_CODE = {
    "not_run": 0,
    "dependency_blocked": 1,
    "local_failed": 2,
    "success": 3,
}
STATUS_TO_MARK = {
    "not_run": "-",
    "dependency_blocked": "D",
    "local_failed": "L",
    "success": "S",
}
STATUS_COLORS = [
    "#D9D9D9",  # not_run
    "#F4A261",  # dependency_blocked
    "#D1495B",  # local_failed
    "#5AA469",  # success
]


def setup_matplotlib_fonts() -> None:
    plt.rcParams["font.family"] = "serif"
    plt.rcParams["font.serif"] = [FONT] + plt.rcParams["font.serif"]
    plt.rcParams["font.size"] = 12


def generate_header_iteration_outputs(
    *,
    version: str,
    project_name: str,
    ai_name: str,
    graph_dir: Path,
    result_dir: Path,
) -> Dict[str, Path]:
    result_dir.mkdir(parents=True, exist_ok=True)
    project = Project.load(graph_dir)

    status_df = build_header_iteration_status_df(project, version, project_name, ai_name)
    summary_df = build_round_summary_df(status_df)

    status_csv_path = result_dir / "header_iteration_status.csv"
    summary_csv_path = result_dir / "header_iteration_round_summary.csv"
    heatmap_png_path = result_dir / "header_iteration_status_heatmap.png"
    heatmap_pdf_path = result_dir / "header_iteration_status_heatmap.pdf"

    status_df.to_csv(status_csv_path, index=False, encoding="utf-8")
    summary_df.to_csv(summary_csv_path, index=False, encoding="utf-8")

    if not status_df.empty:
        render_header_iteration_heatmap(status_df, heatmap_png_path)
        render_header_iteration_heatmap(status_df, heatmap_pdf_path)

    return {
        "status_csv": status_csv_path,
        "summary_csv": summary_csv_path,
        "heatmap_png": heatmap_png_path,
        "heatmap_pdf": heatmap_pdf_path,
    }


def build_header_iteration_status_df(
    project: Project,
    version: str,
    project_name: str,
    ai_name: str,
) -> pd.DataFrame:
    """构建逐 Header、逐轮次的编译状态数据表。

    参数:
        project: 包含 Header 编译历史的项目对象。
        version: 当前框架版本。
        project_name: 项目名称。
        ai_name: 模型名称。

    返回:
        pd.DataFrame: 包含当前文件、项目依赖和项目外错误统计的状态表。
    """
    max_round = max(
        [entry.get("round", 0) for header in project.headers for entry in header.compile_reports] or [0]
    )
    if max_round <= 0:
        return pd.DataFrame(columns=STATUS_COLUMNS)

    rows: List[Dict[str, Any]] = []
    for header in project.headers:
        report_by_round = {
            int(report.get("round", 0)): report
            for report in header.compile_reports
            if int(report.get("round", 0)) > 0
        }
        for round_idx in range(1, max_round + 1):
            report = report_by_round.get(round_idx)
            if report is None:
                rows.append(
                    {
                        "version": version,
                        "project_name": project_name,
                        "ai_name": ai_name,
                        "header_name": header.key,
                        "round": round_idx,
                        "compile_success": False,
                        "status": "not_run",
                        "has_local_issues": False,
                        "has_project_dependency_issues": False,
                        "blocked_by_dependency": False,
                        "issue_count": 0,
                        "project_dependency_issue_count": 0,
                        "external_issue_count": 0,
                        "primary_issue_type": "",
                        "primary_project_dependency_issue_type": "",
                        "primary_external_issue_type": "",
                    }
                )
                continue

            issues = report.get("issues", []) or []
            project_dependency_issues = report.get("project_dependency_issues", []) or []
            external_issues = report.get("external_issues", []) or []
            rows.append(
                {
                    "version": version,
                    "project_name": project_name,
                    "ai_name": ai_name,
                    "header_name": header.key,
                    "round": round_idx,
                    "compile_success": bool(report.get("success", False)),
                    "status": determine_status(report),
                    "has_local_issues": bool(report.get("has_local_issues", False)),
                    "has_project_dependency_issues": bool(
                        report.get("has_project_dependency_issues", project_dependency_issues)
                    ),
                    "blocked_by_dependency": bool(report.get("blocked_by_dependency", False)),
                    "issue_count": len(issues),
                    "project_dependency_issue_count": len(project_dependency_issues),
                    "external_issue_count": len(external_issues),
                    "primary_issue_type": issues[0].get("type", "") if issues else "",
                    "primary_project_dependency_issue_type": (
                        project_dependency_issues[0].get("type", "")
                        if project_dependency_issues else ""
                    ),
                    "primary_external_issue_type": external_issues[0].get("type", "") if external_issues else "",
                }
            )

    df = pd.DataFrame(rows, columns=STATUS_COLUMNS)
    ordered_headers = sort_headers_for_visualization(df)
    df["header_name"] = pd.Categorical(df["header_name"], categories=ordered_headers, ordered=True)
    df = df.sort_values(["header_name", "round"]).reset_index(drop=True)
    return df


def determine_status(report: Dict[str, Any]) -> str:
    """根据单轮编译报告确定可视化状态。

    参数:
        report: 单个 Header 的编译报告字典。

    返回:
        str: success、local_failed、dependency_blocked 或 not_run。
    """
    if report.get("success", False):
        return "success"
    if report.get("has_local_issues", False):
        return "local_failed"
    if report.get("blocked_by_dependency", False):
        return "dependency_blocked"
    return "not_run"


def sort_headers_for_visualization(status_df: pd.DataFrame) -> List[str]:
    summary_rows = []
    for header_name, group in status_df.groupby("header_name", sort=False):
        group = group.sort_values("round")
        final_status = group.iloc[-1]["status"]
        success_rounds = group.loc[group["status"] == "success", "round"].tolist()
        first_success_round = success_rounds[0] if success_rounds else float("inf")
        summary_rows.append(
            {
                "header_name": str(header_name),
                "final_failed": final_status != "success",
                "first_success_round": first_success_round,
            }
        )

    summary_rows.sort(
        key=lambda item: (
            0 if item["final_failed"] else 1,
            item["first_success_round"],
            item["header_name"],
        )
    )
    return [item["header_name"] for item in summary_rows]


def build_round_summary_df(status_df: pd.DataFrame) -> pd.DataFrame:
    summary_columns = [
        "version",
        "project_name",
        "ai_name",
        "round",
        "success_count",
        "local_failed_count",
        "dependency_blocked_count",
        "not_run_count",
    ]
    if status_df.empty:
        return pd.DataFrame(columns=summary_columns)

    rows = []
    for round_idx, group in status_df.groupby("round", sort=True):
        base = group.iloc[0]
        rows.append(
            {
                "version": base["version"],
                "project_name": base["project_name"],
                "ai_name": base["ai_name"],
                "round": round_idx,
                "success_count": int((group["status"] == "success").sum()),
                "local_failed_count": int((group["status"] == "local_failed").sum()),
                "dependency_blocked_count": int((group["status"] == "dependency_blocked").sum()),
                "not_run_count": int((group["status"] == "not_run").sum()),
            }
        )
    return pd.DataFrame(rows, columns=summary_columns)


def render_header_iteration_heatmap(status_df: pd.DataFrame, output_path: Path) -> None:
    setup_matplotlib_fonts()

    pivot = status_df.pivot(index="header_name", columns="round", values="status")
    code_matrix = pivot.apply(lambda column: column.map(lambda value: STATUS_TO_CODE.get(value, 0)))
    annot_matrix = pivot.apply(lambda column: column.map(lambda value: STATUS_TO_MARK.get(value, "-")))

    fig_width = max(6.0, 1.25 * len(pivot.columns) + 2.5)
    fig_height = max(5.0, 0.42 * len(pivot.index) + 2.0)
    fig, ax = plt.subplots(figsize=(fig_width, fig_height))

    cmap = ListedColormap(STATUS_COLORS)
    norm = BoundaryNorm([-0.5, 0.5, 1.5, 2.5, 3.5], cmap.N)

    heatmap = ax.imshow(code_matrix.values, cmap=cmap, norm=norm, aspect="auto")

    for row_idx, header_name in enumerate(pivot.index):
        for col_idx, round_idx in enumerate(pivot.columns):
            ax.text(
                col_idx,
                row_idx,
                annot_matrix.iloc[row_idx, col_idx],
                ha="center",
                va="center",
                color="black",
                fontsize=10,
                fontweight="bold",
            )

    ax.set_xticks(range(len(pivot.columns)))
    ax.set_xticklabels([str(item) for item in pivot.columns])
    ax.set_yticks(range(len(pivot.index)))
    ax.set_yticklabels(list(pivot.index))
    ax.set_xlabel("Round", fontsize=14, fontweight="bold", fontfamily=FONT)
    ax.set_ylabel("Header", fontsize=14, fontweight="bold", fontfamily=FONT)
    ax.set_title(
        f"Header Iteration Compile Status\n{status_df.iloc[0]['version']} / "
        f"{status_df.iloc[0]['project_name']} / {status_df.iloc[0]['ai_name']}",
        fontsize=16,
        fontweight="bold",
        fontfamily=FONT,
    )
    ax.set_xticks([idx - 0.5 for idx in range(1, len(pivot.columns))], minor=True)
    ax.set_yticks([idx - 0.5 for idx in range(1, len(pivot.index))], minor=True)
    ax.grid(which="minor", color="white", linestyle="-", linewidth=0.5)
    ax.tick_params(which="minor", bottom=False, left=False)

    cbar = fig.colorbar(heatmap, ax=ax, ticks=[0, 1, 2, 3])
    cbar.ax.set_yticklabels(STATUS_ORDER)

    plt.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close(fig)
