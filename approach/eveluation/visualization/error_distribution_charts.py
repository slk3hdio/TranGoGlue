"""
Error distribution chart generation module.

Generates charts for error type distributions at file and method levels.
Supports three strategies: class (v3), method (v4), method_bottom_up (v4_1).
"""
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from pathlib import Path
from typing import Optional, List, Dict

# Set default style parameters
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")

# Default font and size settings
FONT = 'Times New Roman'
XY_LABEL_SIZE = 28
XY_TICK_SIZE = 20
LEGEND_SIZE = 20
VAL_LABEL_SIZE = 19
BAR_ALPHA = 0.8

# Color scheme for three strategies
STRATEGY_COLORS = {
    'class': '#4A7298',
    'method': '#F3C846',
    'method_bottom_up': '#BD4146',
    'project': '#2E8B57'
}

# Strategy display names
STRATEGY_NAMES = {
    'class': 'PFT',
    'method': 'PMT',
    'method_bottom_up': 'PMBT',
    'project': 'Project-level\n(Graph-based)'
}

# 显示名反查配色键(替代旧的字符串替换,避免标签改名后失效)
STRATEGY_KEY_BY_LABEL = {v: k for k, v in STRATEGY_NAMES.items()}

# Model display names
MODEL_NAMES = {
    'deepseek-v3.2': 'DeepSeek-V3.2',
    'qwen-3.5plus': 'Qwen3.5-Plus',
    'ChatGPT-5.1': 'GPT-5.1'
}

# Error type colors
ERROR_COLORS = {
    'Syntax Rule Violation': '#CF7E9D',
    'Type Error': "#DEA48B",
    'Declaration Mismatch': '#BD4146',
    'Undefined Symbols': '#ECC68C',
    'Duplicated Definitions': '#E4B7BC',
    'Header File Error': '#F5E4C8',
    'Other Errors': '#9B9B9B'
}

# Error type short labels for display
ERROR_SHORT_LABELS = {
    'Syntax Rule Violation': 'Syntax',
    'Type Error': 'Type',
    'Declaration Mismatch': 'Decl Mismatch',
    'Undefined Symbols': 'Undefined',
    'Duplicated Definitions': 'Duplicate',
    'Header File Error': 'Header',
    'Other Errors': 'Other'
}


def setup_matplotlib_fonts():
    """Configure matplotlib font settings."""
    plt.rcParams['font.family'] = 'serif'
    plt.rcParams['font.serif'] = ['Times New Roman'] + plt.rcParams['font.serif']
    plt.rcParams['font.size'] = 12


def load_error_data(statistics_dir: Path) -> pd.DataFrame:
    """
    Load error summary data.

    Args:
        statistics_dir: Path to Statistics directory

    Returns:
        DataFrame with error summary data
    """
    df = pd.read_csv(statistics_dir / 'error_summary.csv')

    # Add display names
    df['model'] = df['ai_name'].map(MODEL_NAMES)

    return df


def calculate_error_percentages(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate error type percentages for each row.

    Args:
        df: DataFrame with error counts

    Returns:
        DataFrame with error percentages added
    """
    error_types = [
        'Syntax Rule Violation',
        'Type Error',
        'Declaration Mismatch',
        'Undefined Symbols',
        'Duplicated Definitions',
        'Header File Error',
        'Other Errors'
    ]

    df_pct = df.copy()

    # Calculate percentage for each error type
    for error_type in error_types:
        if error_type in df.columns:
            df_pct[f'{error_type}_pct'] = (
                df_pct[error_type] / df_pct['total_errors'] * 100
            ).fillna(0)

    return df_pct


def plot_error_distribution_by_strategy(
    df: pd.DataFrame,
    output_dir: Path,
    figsize: tuple = (6.5, 4.3)
) -> None:
    """
    Plot error type distribution by strategy (aggregated across models and projects).

    Args:
        df: DataFrame with error summary data
        output_dir: Directory to save output files
        figsize: Figure size tuple
    """
    setup_matplotlib_fonts()

    error_types = [
        'Syntax Rule Violation',
        'Type Error',
        'Declaration Mismatch',
        'Undefined Symbols',
        'Duplicated Definitions',
        'Header File Error',
        'Other Errors'
    ]

    # 先按策略聚合错误计数再计算百分比,与论文表2的计数汇总同口径,
    # 避免逐行宏平均导致图文数字不一致。
    count_cols = [et for et in error_types if et in df.columns]
    if not count_cols:
        print("Warning: No error count columns found")
        return

    grouped_counts = df.groupby('strategy')[count_cols].sum()
    grouped_pct = grouped_counts.div(grouped_counts.sum(axis=1), axis=0) * 100

    # Prepare data for plotting
    plot_data = []
    for strategy, row in grouped_pct.iterrows():
        for error_type in error_types:
            if error_type in row.index:
                plot_data.append({
                    'strategy': STRATEGY_NAMES.get(strategy, strategy),
                    'error_type': ERROR_SHORT_LABELS.get(error_type, error_type),
                    'percentage': row[error_type]
                })

    plot_df = pd.DataFrame(plot_data)

    # Create grouped bar chart
    fig, ax = plt.subplots(figsize=figsize)

    # Pivot for grouped bar
    pivot_df = plot_df.pivot(index='error_type', columns='strategy', values='percentage')

    # Ensure correct column order
    strategy_order = ['PFT', 'PMT', 'PMBT', 'Project-level\n(Graph-based)']
    pivot_df = pivot_df[[c for c in strategy_order if c in pivot_df.columns]]

    # Plot
    pivot_df.plot(
        kind='bar',
        ax=ax,
        color=[STRATEGY_COLORS.get(STRATEGY_KEY_BY_LABEL.get(s, ''), '#999999')
               for s in pivot_df.columns],
        alpha=BAR_ALPHA,
        width=0.7
    )

    ax.set_xlabel('', fontsize=14, fontweight='bold', fontfamily=FONT)
    ax.set_ylabel(
        'Error Percentage (%)',
        fontsize=18,
        fontweight='bold',
        fontfamily=FONT
    )
    ax.set_xticklabels(pivot_df.index, fontsize=XY_TICK_SIZE, fontfamily=FONT, rotation=45, ha='right')
    ax.set_yticks(np.arange(0, 101, 20))
    ax.set_yticklabels(np.arange(0, 101, 20), fontsize=16, fontfamily=FONT)

    ax.legend(
        loc='upper right',
        fontsize=LEGEND_SIZE,
        prop={'family': FONT, 'size': LEGEND_SIZE}
    )

    ax.grid(axis='y', alpha=0.3)

    # 图例置于坐标区上方,避免遮挡最高组的柱形与标签。
    ax.legend(
        loc='lower center',
        bbox_to_anchor=(0.5, 1.02),
        ncol=3,
        fontsize=LEGEND_SIZE,
        prop={'family': FONT, 'size': LEGEND_SIZE},
        frameon=False
    )

    plt.tight_layout()

    output_path = output_dir / 'error_distribution_by_strategy.pdf'
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=300, bbox_inches='tight', pad_inches=0.12)
    print(f"Generated: {output_path}")
    plt.close()


def plot_stacked_error_by_strategy(
    df: pd.DataFrame,
    output_dir: Path,
    figsize: tuple = (6.5, 4.8)
) -> None:
    """
    Plot stacked error distribution by strategy and model.
    Shows absolute error counts with labeled values.

    Args:
        df: DataFrame with error summary data
        output_dir: Directory to save output files
        figsize: Figure size tuple
    """
    setup_matplotlib_fonts()

    error_types = [
        'Syntax Rule Violation',
        'Type Error',
        'Declaration Mismatch',
        'Undefined Symbols',
        'Duplicated Definitions',
        'Header File Error',
        'Other Errors'
    ]

    # Aggregate by model and strategy (using absolute counts)
    grouped = df.groupby(['model', 'strategy'])[error_types].sum().reset_index()

    # 按策略为主分组(PFT/PMT/PMBT 各三根柱,模型次序固定),
    # 一级 x 标签为策略名,二级斜排标签为模型名,避免两行斜排标签相互碰撞。
    MODEL_ORDER = ['DeepSeek-V3.2', 'GPT-5.1', 'Qwen3.5-Plus']
    STRAT_ORDER = ['class', 'method', 'method_bottom_up']
    grouped = grouped.set_index(['strategy', 'model']).reindex(
        [(s, m) for s in STRAT_ORDER for m in MODEL_ORDER]).reset_index()

    # 单行模型名作为二级 x 标签
    xlabels = grouped['model'].tolist()
    n_bars = len(grouped)

    # Calculate total errors
    grouped['total'] = grouped[error_types].sum(axis=1)

    # Create stacked bar chart
    fig, ax = plt.subplots(figsize=figsize)

    # Prepare data for stacked bar
    bottom = np.zeros(n_bars)
    bar_patches = []

    for error_type in error_types:
        if error_type in grouped.columns:
            values = grouped[error_type].values
            bars = ax.bar(
                np.arange(n_bars),
                values,
                bottom=bottom,
                label=ERROR_SHORT_LABELS.get(error_type, error_type),
                color=ERROR_COLORS.get(error_type, '#999999'),
                alpha=BAR_ALPHA
            )
            bar_patches.append((bars, values, bottom.copy()))
            bottom += values

    # Add total count labels on top of each bar
    # 相邻柱总数接近时会左右相碰,隔根抬高错开。
    total_max = max(grouped['total'])
    for i, total in enumerate(grouped['total']):
        extra = total_max * 0.055 if i % 2 == 1 else 0.0
        ax.text(
            i, total + total_max * 0.02 + extra,
            f'{int(total)}',
            ha='center',
            va='bottom',
            fontsize=VAL_LABEL_SIZE - 4,
            fontfamily=FONT,
            fontweight='bold',
            color='black'
        )

    ax.set_xlabel('', fontsize=14, fontweight='bold', fontfamily=FONT)
    ax.set_ylabel(
        'Error Count',
        fontsize=16,
        fontweight='bold',
        fontfamily=FONT
    )
    ax.set_xticks(np.arange(n_bars))
    ax.set_xticklabels(xlabels, fontsize=14, fontfamily=FONT, rotation=45, ha='right')

    # 一级策略标签:居中于每组三根柱的下方深处(低于斜排标签扇形);竖线辅助分组。
    for gi, (strategy, label) in enumerate(zip(STRAT_ORDER, ['PFT', 'PMT', 'PMBT'])):
        center = gi * 3 + 1
        ax.text(center, -0.56, label, transform=ax.get_xaxis_transform(),
                ha='center', va='center', fontsize=16, fontfamily=FONT, fontweight='bold')
    for sep in (2.5, 5.5):
        ax.axvline(sep, color='#9CA3AF', linewidth=0.8, alpha=0.5)

    # 纵轴:留出柱顶总数的头部空间,刻度统一为 100 间隔。
    max_total = max(grouped['total'])
    y_max = int((max_total * 1.18 + 99) // 100 * 100)
    ax.set_ylim(0, y_max)
    ax.set_yticks(np.arange(0, y_max + 1, 100))
    ax.set_yticklabels(np.arange(0, y_max + 1, 100), fontsize=12, fontfamily=FONT)

    ax.grid(axis='y', alpha=0.3)

    # 图例固定在画布内部顶带。若放在画布外,bbox_inches='tight' 会把画布撑大,
    # 论文里按固定宽度缩放后绘图区就会被挤小,与并排的 (a) 比例失衡。
    fig.legend(
        loc='upper center',
        bbox_to_anchor=(0.545, 0.99),
        ncol=3,
        frameon=False,
        handlelength=1.4,
        columnspacing=1.0,
        prop={'family': FONT, 'size': 13}
    )

    # 显式布局:图例、斜排模型标签、策略标签全部收在画布内。
    fig.subplots_adjust(top=0.80, bottom=0.34, left=0.105, right=0.985)

    output_path = output_dir / 'stacked_error_distribution.pdf'
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=300)
    print(f"Generated: {output_path}")
    plt.close()


def plot_error_heatmap(
    df: pd.DataFrame,
    output_dir: Path,
    figsize: tuple = (12, 8)
) -> None:
    """
    Plot heatmap of error types by model and strategy.
    Shows absolute error counts.

    Args:
        df: DataFrame with error summary data
        output_dir: Directory to save output files
        figsize: Figure size tuple
    """
    setup_matplotlib_fonts()

    error_types = [
        'Syntax Rule Violation',
        'Type Error',
        'Undefined Symbols',
        'Duplicated Definitions',
        'Header File Error',
        'Declaration Mismatch',
        'Other Errors'
    ]

    # Aggregate by model and strategy (using absolute counts)
    grouped = df.groupby(['model', 'strategy'])[error_types].sum().reset_index()

    # Create combined label
    grouped['config'] = (
        grouped['model'] + '\n(' +
        grouped['strategy'].map(STRATEGY_NAMES) + ')'
    )

    # Prepare heatmap matrix
    heatmap_matrix = grouped.set_index('config')[error_types].T

    # Shorten error type names
    heatmap_matrix.index = [ERROR_SHORT_LABELS.get(et, et) for et in heatmap_matrix.index]

    # Create heatmap
    fig, ax = plt.subplots(figsize=figsize)

    # Calculate dynamic vmax based on data
    vmax = heatmap_matrix.values.max()
    vmax_rounded = int((vmax + 9) / 10) * 10  # Round up to nearest 10

    sns.heatmap(
        heatmap_matrix,
        annot=True,
        fmt='.0f',
        cmap='YlOrRd',
        cbar_kws={'label': 'Error Count'},
        linewidths=0.5,
        ax=ax,
        vmin=0,
        vmax=vmax_rounded
    )

    ax.set_title(
        'Error Type Count by Model and Strategy',
        fontsize=16,
        fontweight='bold',
        fontfamily=FONT
    )
    ax.set_xlabel('Configuration', fontsize=14, fontweight='bold', fontfamily=FONT)
    ax.set_ylabel('Error Type', fontsize=14, fontweight='bold', fontfamily=FONT)

    plt.tight_layout()

    output_path = output_dir / 'error_heatmap.pdf'
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"Generated: {output_path}")
    plt.close()


def plot_error_by_project(
    df: pd.DataFrame,
    output_dir: Path,
    figsize: tuple = (14, 8)
) -> None:
    """
    Plot error counts by project and strategy.

    Args:
        df: DataFrame with error summary data
        output_dir: Directory to save output files
        figsize: Figure size tuple
    """
    setup_matplotlib_fonts()

    # Aggregate by project and strategy
    grouped = df.groupby(['project_name', 'strategy'])['total_errors'].sum().reset_index()

    # Pivot for plotting
    pivot_df = grouped.pivot(index='project_name', columns='strategy', values='total_errors').fillna(0)

    # Ensure all strategies are present
    for strategy in ['class', 'method', 'method_bottom_up', 'project']:
        if strategy not in pivot_df.columns:
            pivot_df[strategy] = 0

    # Create grouped bar chart
    fig, ax = plt.subplots(figsize=figsize)

    strategies = ['class', 'method', 'method_bottom_up', 'project']
    x = np.arange(len(pivot_df.index))
    width = 0.2
    offsets = [-1.5 * width, -0.5 * width, 0.5 * width, 1.5 * width]

    for strategy, offset in zip(strategies, offsets):
        if strategy in pivot_df.columns:
            values = pivot_df[strategy].values
            ax.bar(
                x + offset,
                values,
                width,
                label=STRATEGY_NAMES[strategy],
                color=STRATEGY_COLORS[strategy],
                alpha=BAR_ALPHA
            )

    # add value labels on top of bars
    for i, project in enumerate(pivot_df.index):
        for strategy, offset in zip(strategies, offsets):
            if strategy in pivot_df.columns:
                value = pivot_df.loc[project, strategy]
                if value > 3:  # Only show label if value is significant
                    ax.text(
                        i + offset, value + max(pivot_df.max()) * 0.02,
                        f'{int(value)}',
                        ha='center',
                        va='bottom',
                        fontsize=VAL_LABEL_SIZE - 5,
                        fontfamily=FONT,
                        fontweight='bold',
                        color='black'
                    )

    ax.set_xlabel('', fontsize=14, fontweight='bold', fontfamily=FONT)
    ax.set_ylabel(
        'Total Error Count',
        fontsize=XY_LABEL_SIZE,
        fontweight='bold',
        fontfamily=FONT
    )
    ax.set_xticks(x)
    ax.set_xticklabels(pivot_df.index, fontsize=XY_TICK_SIZE, fontfamily=FONT, rotation=45, ha='right')

    ax.set_yticks(np.arange(0, 141, 20))
    ax.set_yticklabels(np.arange(0, 141, 20), fontsize=XY_TICK_SIZE, fontfamily=FONT)

    ax.legend(
        loc='upper left',
        fontsize=LEGEND_SIZE,
        prop={'family': FONT, 'size': LEGEND_SIZE}
    )

    ax.grid(axis='y', alpha=0.3)

    plt.tight_layout()

    output_path = output_dir / 'error_count_by_project.pdf'
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"Generated: {output_path}")
    plt.close()


def generate_all_error_distribution_charts(
    statistics_dir: Path,
    output_dir: Path
) -> None:
    """
    Generate all error distribution charts.

    Args:
        statistics_dir: Path to Statistics directory
        output_dir: Path to save output figures
    """
    print("=" * 60)
    print("Generating Error Distribution Charts")
    print("=" * 60)

    df = load_error_data(statistics_dir)

    print("\n[1/4] Error distribution by strategy...")
    plot_error_distribution_by_strategy(df, output_dir)

    print("\n[2/4] Stacked error distribution...")
    plot_stacked_error_by_strategy(df, output_dir)

    print("\n[3/4] Error heatmap...")
    plot_error_heatmap(df, output_dir)

    print("\n[4/4] Error count by project...")
    plot_error_by_project(df, output_dir)

    print("\n" + "=" * 60)
    print("Error distribution charts generated!")
    print("=" * 60)


if __name__ == '__main__':
    statistics_dir = Path('../../../Statistics')
    output_dir = Path('../../../figures/detailed')
    generate_all_error_distribution_charts(statistics_dir, output_dir)
