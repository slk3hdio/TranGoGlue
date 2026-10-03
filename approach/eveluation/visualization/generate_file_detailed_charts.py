"""
Generate file-level detailed charts for LLM-based code translation evaluation.

This script generates detailed charts showing compilation success rates and
code metrics comparisons at the file level across different translation strategies.

Usage:
    python generate_file_detailed_charts.py
    python generate_file_detailed_charts.py --charts success
    python generate_file_detailed_charts.py --charts error
    python generate_file_detailed_charts.py --charts all
"""
import argparse
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from pathlib import Path
from typing import Optional
import sys
approach_dir = Path(__file__).parent.parent.parent
if approach_dir not in sys.path:
    sys.path.append(str(approach_dir))

from path_config import cfg_statistics_dir_path, cfg_chart_output_dir_path

# Import modular chart generators
from success_rate_charts import (
    generate_all_success_rate_charts,
    setup_matplotlib_fonts,
    STRATEGY_COLORS,
    STRATEGY_NAMES,
    MODEL_NAMES
)
from error_distribution_charts import (
    generate_all_error_distribution_charts,
    ERROR_COLORS,
    ERROR_SHORT_LABELS
)

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


def load_file_details(statistics_dir: Path) -> pd.DataFrame:
    """
    Load file compile details data.

    Args:
        statistics_dir: Path to Statistics directory

    Returns:
        DataFrame with file compile details
    """
    df = pd.read_csv(statistics_dir / 'file_compile_details.csv')
    df['model'] = df['ai_name'].map(MODEL_NAMES)
    df['compile_rate'] = df['success_functions'] / df['total_functions']
    return df


def load_method_details(statistics_dir: Path) -> pd.DataFrame:
    """
    Load method compile details data.

    Args:
        statistics_dir: Path to Statistics directory

    Returns:
        DataFrame with method compile details
    """
    df = pd.read_csv(statistics_dir / 'method_compile_details.csv')
    df['model'] = df['ai_name'].map(MODEL_NAMES)
    return df


def plot_file_comparison_by_project(
    df: pd.DataFrame,
    project_name: str,
    output_dir: Path,
    ai_name: Optional[str] = None,
    figsize: tuple = (16, 8)
) -> None:
    """
    Plot detailed file comparison for a specific project.

    Shows success function count comparison across strategies for each file.

    Args:
        df: DataFrame with file compile details
        project_name: Name of the project to plot
        output_dir: Directory to save output files
        ai_name: Optional AI name filter
        figsize: Figure size tuple
    """
    setup_matplotlib_fonts()

    # Filter data
    filtered_df = df[df['project_name'] == project_name]

    if ai_name is not None:
        filtered_df = filtered_df[filtered_df['ai_name'] == ai_name]

    if len(filtered_df) == 0:
        print(f"Warning: No data found for project '{project_name}'")
        return

    # Get unique files and strategies
    files = filtered_df['file_name'].unique()
    strategies = ['class', 'method', 'method_bottom_up']

    # Prepare data for plotting
    plot_data = []
    for file in files:
        file_df = filtered_df[filtered_df['file_name'] == file]
        for strategy in strategies:
            strategy_df = file_df[file_df['strategy'] == strategy]
            if len(strategy_df) > 0:
                plot_data.append({
                    'file_name': file,
                    'strategy': strategy,
                    'success_functions': strategy_df['success_functions'].values[0],
                    'total_functions': strategy_df['total_functions'].values[0],
                    'compile_rate': strategy_df['compile_rate'].values[0]
                })

    if not plot_data:
        print(f"Warning: No data to plot for project '{project_name}'")
        return

    plot_df = pd.DataFrame(plot_data)

    # Create figure
    fig, ax = plt.subplots(figsize=figsize)

    # Pivot for grouped bar
    pivot_df = plot_df.pivot(index='file_name', columns='strategy', values='compile_rate')

    # Ensure all strategies are present
    for strategy in strategies:
        if strategy not in pivot_df.columns:
            pivot_df[strategy] = np.nan

    # Plot grouped bar chart
    x = np.arange(len(pivot_df.index))
    width = 0.25
    offsets = [-width, 0, width]

    for strategy, offset in zip(strategies, offsets):
        if strategy in pivot_df.columns:
            values = pivot_df[strategy].fillna(0) * 100  # Convert to percentage
            bars = ax.bar(
                x + offset,
                values,
                width,
                label=STRATEGY_NAMES[strategy],
                color=STRATEGY_COLORS[strategy],
                alpha=BAR_ALPHA
            )

    ax.set_xlabel('', fontsize=14, fontweight='bold', fontfamily=FONT)
    ax.set_ylabel(
        'Compile Success Rate (%)',
        fontsize=XY_LABEL_SIZE,
        fontweight='bold',
        fontfamily=FONT
    )
    ax.set_xticks(x)
    ax.set_xticklabels(pivot_df.index, fontsize=XY_TICK_SIZE - 5, fontfamily=FONT, rotation=45, ha='right')
    ax.set_yticks(np.arange(0, 101, 10))
    ax.set_yticklabels(np.arange(0, 101, 10), fontsize=XY_TICK_SIZE, fontfamily=FONT)

    ax.legend(
        loc='upper right',
        fontsize=LEGEND_SIZE,
        prop={'family': FONT, 'size': LEGEND_SIZE}
    )

    ax.grid(axis='y', alpha=0.3)

    # Add title
    title_suffix = f" ({ai_name})" if ai_name else ""
    ax.set_title(
        f'File Compile Rate - {project_name}{title_suffix}',
        fontsize=16,
        fontweight='bold',
        fontfamily=FONT
    )

    plt.tight_layout()

    # Save
    suffix = f"_{ai_name.replace(' ', '_')}" if ai_name else ""
    output_path = output_dir / 'file_comparison' / f'{project_name}{suffix}_comparison.pdf'
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"Generated: {output_path}")
    plt.close()


def plot_strategy_comparison_heatmap(
    df: pd.DataFrame,
    output_dir: Path,
    figsize: tuple = (14, 10)
) -> None:
    """
    Plot heatmap comparing compile rates across strategies for each file.

    Args:
        df: DataFrame with file compile details
        output_dir: Directory to save output files
        figsize: Figure size tuple
    """
    setup_matplotlib_fonts()

    # Group by file and strategy
    grouped = df.groupby(['project_name', 'file_name', 'strategy'])['compile_rate'].mean().reset_index()

    # Pivot for heatmap
    pivot_df = grouped.pivot_table(
        index=['project_name', 'file_name'],
        columns='strategy',
        values='compile_rate'
    ).fillna(0)

    # Ensure all strategies are present
    for strategy in ['class', 'method', 'method_bottom_up']:
        if strategy not in pivot_df.columns:
            pivot_df[strategy] = np.nan

    # Rename columns
    pivot_df.columns = [STRATEGY_NAMES.get(c, c) for c in pivot_df.columns]

    # Create heatmap
    fig, ax = plt.subplots(figsize=figsize)

    sns.heatmap(
        pivot_df,
        annot=True,
        fmt='.2f',
        cmap='RdYlGn',
        cbar_kws={'label': 'Compile Rate'},
        linewidths=0.5,
        ax=ax,
        vmin=0,
        vmax=1
    )

    ax.set_title(
        'File Compile Rate Comparison Across Strategies',
        fontsize=16,
        fontweight='bold',
        fontfamily=FONT
    )
    ax.set_xlabel('Strategy', fontsize=14, fontweight='bold', fontfamily=FONT)
    ax.set_ylabel('File', fontsize=14, fontweight='bold', fontfamily=FONT)

    plt.tight_layout()

    output_path = output_dir / 'file_comparison' / 'strategy_comparison_heatmap.pdf'
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"Generated: {output_path}")
    plt.close()


def plot_strategy_delta_heatmap(
    df: pd.DataFrame,
    output_dir: Path,
    baseline: str = 'class',
    compare: str = 'method_bottom_up',
    figsize: tuple = (14, 10)
) -> None:
    """
    Plot heatmap showing delta (improvement/degradation) between two strategies.

    Args:
        df: DataFrame with file compile details
        output_dir: Directory to save output files
        baseline: Baseline strategy for comparison
        compare: Strategy to compare against baseline
        figsize: Figure size tuple
    """
    setup_matplotlib_fonts()

    # Group by file and strategy
    grouped = df.groupby(['project_name', 'file_name', 'strategy'])['compile_rate'].mean().reset_index()

    # Pivot for comparison
    pivot_df = grouped.pivot_table(
        index=['project_name', 'file_name'],
        columns='strategy',
        values='compile_rate'
    ).fillna(0)

    if baseline not in pivot_df.columns or compare not in pivot_df.columns:
        print(f"Warning: Cannot create delta heatmap - missing '{baseline}' or '{compare}' strategy")
        return

    # Calculate delta
    delta = pivot_df[compare] - pivot_df[baseline]
    delta_df = pd.DataFrame(delta, columns=['improvement'])

    # Create heatmap
    fig, ax = plt.subplots(figsize=figsize)

    # Center colormap at 0
    vmax = abs(delta).max()
    vmin = -vmax

    sns.heatmap(
        delta_df,
        annot=True,
        fmt='+.2f',
        cmap='RdYlGn_r',
        center=0,
        cbar_kws={'label': f'Improvement ({compare} - {baseline})'},
        linewidths=0.5,
        ax=ax,
        vmin=vmin,
        vmax=vmax
    )

    ax.set_title(
        f'Compile Rate Improvement: {STRATEGY_NAMES[compare]} vs {STRATEGY_NAMES[baseline]}',
        fontsize=16,
        fontweight='bold',
        fontfamily=FONT
    )
    ax.set_xlabel('', fontsize=14, fontweight='bold', fontfamily=FONT)
    ax.set_ylabel('File', fontsize=14, fontweight='bold', fontfamily=FONT)
    ax.set_xticks([])

    plt.tight_layout()

    output_path = output_dir / 'file_comparison' / f'delta_{baseline}_vs_{compare}.pdf'
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"Generated: {output_path}")
    plt.close()


def generate_all_file_detailed_charts(
    statistics_dir: Path,
    output_dir: Path
) -> None:
    """
    Generate all file-level detailed charts.

    Args:
        statistics_dir: Path to Statistics directory
        output_dir: Path to save output figures
    """
    print("=" * 60)
    print("Generating File-Level Detailed Charts")
    print("=" * 60)

    df = load_file_details(statistics_dir)

    # Get unique projects
    projects = df['project_name'].unique()

    print(f"\n[1/{len(projects) + 2}] Strategy comparison heatmap...")
    plot_strategy_comparison_heatmap(df, output_dir)

    print(f"\n[2/{len(projects) + 2}] Strategy delta heatmap (class vs method_bottom_up)...")
    plot_strategy_delta_heatmap(df, output_dir, baseline='class', compare='method_bottom_up')

    # Generate per-project comparisons
    for i, project in enumerate(projects, 3):
        print(f"\n[{i}/{len(projects) + 2}] File comparison for {project}...")
        plot_file_comparison_by_project(df, project, output_dir)

    print("\n" + "=" * 60)
    print("File-level detailed charts generated!")
    print("=" * 60)


def main():
    statistics_dir = cfg_statistics_dir_path()
    output_dir = cfg_chart_output_dir_path() / 'empirical'
    charts = 'all'

    # Generate requested charts
    # if charts in ['success', 'all']:
    #     print("\n>>> Generating Success Rate Charts <<<")
    #     generate_all_success_rate_charts(statistics_dir, output_dir/'success_rate')

    if charts in ['error', 'all']:
        print("\n>>> Generating Error Distribution Charts <<<")
        generate_all_error_distribution_charts(statistics_dir, output_dir/'error_analysis')

    # if charts in ['detailed', 'all']:
    #     print("\n>>> Generating File-Level Detailed Charts <<<")
    #     generate_all_file_detailed_charts(statistics_dir, output_dir)

    print("\n" + "=" * 60)
    print("All requested charts generated successfully!")
    print(f"Output directory: {output_dir}")
    print("=" * 60)


if __name__ == '__main__':
    main()
