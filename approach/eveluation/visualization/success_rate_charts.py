"""
Success rate chart generation module.

Generates charts for compilation success rates at file and method levels.
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
    'method_bottom_up': '#BD4146'
}

# Strategy display names
STRATEGY_NAMES = {
    'class': 'PFT',
    'method': 'PMT',
    'method_bottom_up': 'PMBT'
}

# Model display names
MODEL_NAMES = {
    'deepseek-v3.2': 'DeepSeek-V3.2',
    'qwen-3.5plus': 'Qwen3.5-Plus',
    'ChatGPT-5.1': 'GPT-5.1'
}


def setup_matplotlib_fonts():
    """Configure matplotlib font settings."""
    plt.rcParams['font.family'] = 'serif'
    plt.rcParams['font.serif'] = ['Times New Roman'] + plt.rcParams['font.serif']
    plt.rcParams['font.size'] = 12


def load_data(statistics_dir: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Load file and method compilation summary data.

    Args:
        statistics_dir: Path to Statistics directory

    Returns:
        Tuple of (file_summary_df, method_summary_df)
    """
    file_df = pd.read_csv(statistics_dir / 'file_compile_summary.csv')
    method_df = pd.read_csv(statistics_dir / 'method_compile_summary.csv')

    # Add display names
    file_df['model'] = file_df['ai_name'].map(MODEL_NAMES)
    method_df['model'] = method_df['ai_name'].map(MODEL_NAMES)

    # Calculate success rate percentage
    file_df['success_rate_pct'] = file_df['compile_rate'] * 100
    method_df['success_rate_pct'] = method_df['compile_rate'] * 100

    return file_df, method_df


def plot_overall_success_rate(
    df: pd.DataFrame,
    output_dir: Path,
    level: str = 'file',
    figsize: tuple = (7, 4.1)
) -> None:
    """
    Plot overall success rate by model and strategy.

    Args:
        df: DataFrame with compile summary data
        output_dir: Directory to save output files
        level: 'file' or 'method'
        figsize: Figure size tuple
    """
    setup_matplotlib_fonts()

    fig, ax = plt.subplots(figsize=figsize)

    # Group by model and strategy
    grouped = df.groupby(['model', 'strategy'])['success_rate_pct'].mean().reset_index()
    pivot_data = grouped.pivot(index='model', columns='strategy', values='success_rate_pct')

    # Ensure all strategies are present
    for strategy in ['class', 'method', 'method_bottom_up']:
        if strategy not in pivot_data.columns:
            pivot_data[strategy] = np.nan

    x = np.arange(len(pivot_data.index))
    width = 0.25

    # Plot bars for each strategy
    strategies = ['class', 'method', 'method_bottom_up']
    offsets = [-width, 0, width]

    for strategy, offset in zip(strategies, offsets):
        if strategy in pivot_data.columns:
            values = pivot_data[strategy].fillna(0)
            bars = ax.bar(
                x + offset,
                values,
                width,
                label=STRATEGY_NAMES[strategy],
                color=STRATEGY_COLORS[strategy],
                alpha=BAR_ALPHA
            )

            # Add value labels on bars
            for bar in bars:
                height = bar.get_height()
                if height > 0:
                    ax.text(
                        bar.get_x() + bar.get_width() / 2.,
                        height,
                        f'{height:.1f}',
                        ha='center',
                        va='bottom',
                        fontsize=VAL_LABEL_SIZE,
                        fontfamily=FONT
                    )

    ax.set_xlabel('', fontsize=18, fontweight='bold', fontfamily=FONT)
    # 两行标题:单行 28pt 旋转后超过图高,首字母会被裁掉。
    ax.set_ylabel(
        'Compilation Success\nRate (%)',
        fontsize=18,
        fontweight='bold',
        fontfamily=FONT
    )
    ax.set_xticks(x)
    ax.set_xticks(np.arange(-0.5, len(x), 0.5), minor=True)
    ax.set_xticklabels(pivot_data.index, fontsize=XY_TICK_SIZE, fontfamily=FONT)
    ax.legend(
        loc='upper left',
        fontsize=LEGEND_SIZE,
        prop={'family': FONT, 'size': LEGEND_SIZE}
    )
    ax.grid(True, axis='x', which='minor', alpha=0.3, color='gray')
    ax.set_yticks(np.arange(0, 101, 10))
    ax.set_yticklabels(np.arange(0, 101, 10), fontsize=16, fontfamily=FONT)
    ax.set_ylim(0, 100)

    plt.tight_layout()

    output_path = output_dir / f'overall_success_rate_{level}.pdf'
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=300, bbox_inches='tight', pad_inches=0.12)
    print(f"Generated: {output_path}")
    plt.close()


def plot_success_rate_by_project(
    df: pd.DataFrame,
    output_dir: Path,
    strategy: str,
    level: str = 'file',
    figsize: tuple = (12, 7)
) -> None:
    """
    Plot success rate by project for a specific strategy.

    Args:
        df: DataFrame with compile summary data
        output_dir: Directory to save output files
        strategy: Strategy to plot ('class', 'method', or 'method_bottom_up')
        level: 'file' or 'method'
        figsize: Figure size tuple
    """
    setup_matplotlib_fonts()

    fig, ax = plt.subplots(figsize=figsize)

    # Filter by strategy
    strategy_df = df[df['strategy'] == strategy]

    if len(strategy_df) == 0:
        print(f"Warning: No data for strategy '{strategy}'")
        plt.close()
        return

    # Get unique projects and models
    projects = strategy_df['project_name'].unique()
    models = strategy_df['model'].unique()

    # Professional color scheme
    colors = ['#AC2124', '#ECB426', '#416594']

    width = 0.25
    bar_positions = np.arange(len(projects))

    for i, model in enumerate(models):
        model_data = strategy_df[strategy_df['model'] == model]
        rates = [
            model_data[model_data['project_name'] == p]['success_rate_pct'].values[0]
            if p in model_data['project_name'].values else 0
            for p in projects
        ]

        offset = (i - len(models) / 2 + 0.5) * width
        bars = ax.bar(
            bar_positions + offset,
            rates,
            width,
            label=model,
            color=colors[i % len(colors)],
            alpha=BAR_ALPHA
        )

    ax.set_xlabel('', fontsize=18, fontweight='bold', fontfamily=FONT)
    ax.set_ylabel(
        'Compilation Success Rate (%)',
        fontsize=XY_LABEL_SIZE,
        fontweight='bold',
        fontfamily=FONT
    )
    ax.set_xticks(bar_positions)
    ax.set_xticks(np.arange(0.5, len(projects) - 0.5, 0.5), minor=True)

    # Format project names (add line breaks for long names)
    formatted_projects = [
        p.replace('EnableJUnit4MigrationSupport', 'EnableJUnit4-\nMigrationSupport')
        for p in projects
    ]
    ax.set_xticklabels(formatted_projects, fontsize=XY_TICK_SIZE, fontfamily=FONT, rotation=15, ha='right')

    ax.grid(True, axis='x', which='minor', alpha=0.3, color='gray')
    ax.legend(
        loc='upper left',
        fontsize=LEGEND_SIZE,
        prop={'family': FONT, 'size': LEGEND_SIZE}
    )
    ax.set_yticks(np.arange(0, 101, 10))
    ax.set_yticklabels(np.arange(0, 101, 10), fontsize=XY_TICK_SIZE, fontfamily=FONT)
    ax.set_ylim(0, 100)

    # Add value labels on bars
    for bars in ax.containers:
        for bar in bars:
            height = bar.get_height()
            if height > 0:
                ax.text(
                    bar.get_x() + bar.get_width() / 2.,
                    height,
                    f'{height:.1f}',
                    ha='center',
                    va='bottom',
                    fontsize=VAL_LABEL_SIZE,
                    fontfamily=FONT
                )

    # 每组柱子的模型平均值: 标记在组中央, 并用折线跨模块连接
    averages = []
    for p in projects:
        vals = []
        for model in models:
            v = strategy_df[(strategy_df['model'] == model)
                            & (strategy_df['project_name'] == p)][
                'success_rate_pct'].values
            if len(v):
                vals.append(v[0])
        averages.append(sum(vals) / len(vals) if vals else 0.0)
    ax.plot(
        bar_positions,
        averages,
        color='black',
        marker='D',
        markersize=10,
        linewidth=2,
        label='Average',
        zorder=5
    )
    for x_pos, avg in zip(bar_positions, averages):
        ax.text(
            x_pos,
            avg + 2.5,
            f'{avg:.1f}',
            ha='center',
            va='bottom',
            fontsize=VAL_LABEL_SIZE - 5,
            fontfamily=FONT,
            fontweight='bold'
        )
    # 平均线在原 legend 之后添加, 这里重建 legend 以纳入 Average 条目
    ax.legend(
        loc='upper left',
        fontsize=LEGEND_SIZE,
        prop={'family': FONT, 'size': LEGEND_SIZE}
    )

    plt.tight_layout()

    output_path = output_dir / f'success_rate_by_project_{strategy}_{level}.pdf'
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"Generated: {output_path}")
    plt.close()


def plot_file_level_comparison(
    df: pd.DataFrame,
    output_dir: Path,
    figsize: tuple = (14, 8)
) -> None:
    """
    Plot file-level detailed comparison showing success/failure per file.

    Args:
        df: DataFrame with file compile details
        output_dir: Directory to save output files
        figsize: Figure size tuple
    """
    setup_matplotlib_fonts()

    # Get unique projects and strategies
    projects = df['project_name'].unique()

    for project in projects:
        project_df = df[df['project_name'] == project]

        fig, ax = plt.subplots(figsize=figsize)

        # Group by file and strategy
        grouped = project_df.groupby(['file_name', 'strategy']).agg({
            'compile_success': 'first',
            'success_functions': 'first',
            'total_functions': 'first'
        }).reset_index()

        # Pivot for visualization
        pivot_success = grouped.pivot(
            index='file_name',
            columns='strategy',
            values='compile_success'
        ).fillna(False)

        # Create heatmap data (1 for success, 0 for failure)
        strategies = ['class', 'method', 'method_bottom_up']
        heatmap_data = pd.DataFrame(index=pivot_success.index)

        for strategy in strategies:
            if strategy in pivot_success.columns:
                heatmap_data[STRATEGY_NAMES[strategy]] = pivot_success[strategy].astype(int)
            else:
                heatmap_data[STRATEGY_NAMES[strategy]] = np.nan

        # Plot heatmap
        sns.heatmap(
            heatmap_data,
            annot=True,
            fmt='.0f',
            cmap='RdYlGn',
            cbar_kws={'label': 'Success (1) / Failure (0)'},
            linewidths=0.5,
            ax=ax,
            vmin=0,
            vmax=1
        )

        ax.set_title(
            f'File Compilation Status - {project}',
            fontsize=16,
            fontweight='bold',
            fontfamily=FONT
        )
        ax.set_xlabel('Strategy', fontsize=14, fontweight='bold', fontfamily=FONT)
        ax.set_ylabel('File Name', fontsize=14, fontweight='bold', fontfamily=FONT)

        plt.tight_layout()

        output_path = output_dir / 'file_comparison' / f'{project}_file_status.pdf'
        output_path.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"Generated: {output_path}")
        plt.close()


def generate_all_success_rate_charts(
    statistics_dir: Path,
    output_dir: Path
) -> None:
    """
    Generate all success rate charts.

    Args:
        statistics_dir: Path to Statistics directory
        output_dir: Path to save output figures
    """
    print("=" * 60)
    print("Generating Success Rate Charts")
    print("=" * 60)

    file_df, method_df = load_data(statistics_dir)

    # Overall success rates
    print("\n[1/4] Overall success rate (file-level)...")
    plot_overall_success_rate(file_df, output_dir, level='file')

    # print("\n[2/4] Overall success rate (method-level)...")
    # plot_overall_success_rate(method_df, output_dir, level='method')

    # Success rate by project for each strategy
    for i, strategy in enumerate(['class', 'method', 'method_bottom_up'], 3):
        print(f"\n[{i}/7] Success rate by project ({strategy})...")
        plot_success_rate_by_project(file_df, output_dir, strategy, level='file')

    print("\n[7/7] File-level detailed comparison...")
    file_details = pd.read_csv(statistics_dir / 'file_compile_details.csv')
    file_details['model'] = file_details['ai_name'].map(MODEL_NAMES)
    plot_file_level_comparison(file_details, output_dir)

    print("\n" + "=" * 60)
    print("Success rate charts generated!")
    print("=" * 60)


if __name__ == '__main__':
    statistics_dir = Path('../../../Statistics')
    output_dir = Path('../../../figures/detailed')
    generate_all_success_rate_charts(statistics_dir, output_dir)
