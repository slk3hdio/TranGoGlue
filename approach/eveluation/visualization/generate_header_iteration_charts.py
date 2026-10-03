"""
Backfill header iteration compile visualizations from persisted graph state.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

approach_dir = Path(__file__).parent.parent.parent
if str(approach_dir) not in sys.path:
    sys.path.append(str(approach_dir))

from eveluation.visualization.header_iteration_charts import generate_header_iteration_outputs
from path_config import cfg_graph_dir_path, cfg_translate_result_dir_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate header iteration charts from graph state.")
    parser.add_argument("--version", required=True, help="Approach version, for example v4_4 or v4_5.")
    parser.add_argument("--project", required=True, help="Project name.")
    parser.add_argument("--ai", required=True, help="Model name, for example deepseek.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    graph_dir = cfg_graph_dir_path(args.ai, args.project, args.version)
    result_dir = cfg_translate_result_dir_path(args.ai, args.project, args.version)

    if not graph_dir.exists():
        raise FileNotFoundError(f"Graph directory does not exist: {graph_dir}")

    outputs = generate_header_iteration_outputs(
        version=args.version,
        project_name=args.project,
        ai_name=args.ai,
        graph_dir=graph_dir,
        result_dir=result_dir,
    )

    print("Generated header iteration visualization artifacts:")
    for key, path in outputs.items():
        print(f"- {key}: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
