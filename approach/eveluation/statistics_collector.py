"""
统一数据收集模块

收集项目编译和错误统计数据，生成统一格式的CSV文件。
支持v3, v4, v4_1版本，使用映射后的AI名称。
"""
import json
import csv
from pathlib import Path
from typing import Dict, List, Optional
import sys

p_dir = str(Path(__file__).parent)
pp_dir = str(Path(__file__).parent.parent)
if pp_dir not in sys.path:
    sys.path.append(pp_dir)
if p_dir not in sys.path:
    sys.path.append(p_dir)

from path_config import cfg_eval_dir_path, cfg_all_project_names, cfg_split_output_dir_path, cfg_statistics_dir_path


class StatisticsCollector:
    """
    统计数据收集器

    统一收集项目、文件、方法级别的编译和错误统计。
    """

    # AI名称映射
    AI_NAME_MAPPING = {
        'qwen': 'qwen-3.5plus',
        'deepseek': 'deepseek-v3.2',
        'gpt': 'ChatGPT-5.1'
    }

    # 版本到策略的映射
    VERSION_STRATEGY = {
        'v3': 'class',
        'v4': 'method',
        'v4_1': 'method_bottom_up',
        'v4_7': 'project',
    }

    # 错误类型
    ERROR_TYPES = [
        "Syntax Rule Violation",
        "Type Error",
        "Declaration Mismatch",
        "Undefined Symbols",
        "Duplicated Definitions",
        "Header File Error",
        "Other Errors"
    ]

    def __init__(self, output_dir: Optional[str] = None):
        if output_dir is None:
            self.output_dir = cfg_statistics_dir_path()
        else:
            self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

    def get_mapped_ai_name(self, ai_name: str) -> str:
        """获取映射后的AI名称"""
        return self.AI_NAME_MAPPING.get(ai_name, ai_name)

    def get_strategy(self, version: str) -> str:
        """获取版本对应的策略"""
        return self.VERSION_STRATEGY.get(version, 'unknown')

    def collect_project_info(self, versions: List[str], ai_names: List[str]) -> None:
        """
        收集项目信息统计

        包括：源文件数、源方法数、翻译后文件数、翻译后方法数、代码长度等
        """
        rows = []

        for version in versions:
            for ai_name in ai_names:
                mapped_ai_name = self.get_mapped_ai_name(ai_name)

                for project_name in cfg_all_project_names(version):
                    try:
                        # 从split目录读取源项目信息
                        split_dir = cfg_split_output_dir_path(project_name, version)
                        source_files = 0
                        source_methods = 0
                        source_text_length = 0

                        if split_dir.exists():
                            for json_file in split_dir.glob('*.json'):
                                try:
                                    with open(json_file, 'r', encoding='utf-8') as f:
                                        data = json.load(f)
                                    source_files += 1
                                    source_methods += len(data.get('methods', []))
                                    source_text_length += len(data.get('classDeclaration', ''))
                                except Exception:
                                    continue

                        # 从eval目录读取翻译后信息
                        eval_dir = cfg_eval_dir_path(ai_name, project_name, version)
                        translated_files = 0
                        translated_methods = 0
                        translated_text_length = 0

                        if eval_dir.exists():
                            for json_file in eval_dir.glob('*.json'):
                                try:
                                    with open(json_file, 'r', encoding='utf-8') as f:
                                        data = json.load(f)
                                    translated_files += 1
                                    functions = data.get('functions', [])
                                    translated_methods += len(functions)
                                    for func in functions:
                                        translated_text_length += len(func.get('function_code', ''))
                                except Exception:
                                    continue

                        rows.append({
                            'project_name': project_name,
                            'ai_name': mapped_ai_name,
                            'version': version,
                            'strategy': self.get_strategy(version),
                            'source_file_count': source_files,
                            'source_method_count': source_methods,
                            'translated_file_count': translated_files,
                            'translated_method_count': translated_methods,
                            'source_text_length': source_text_length,
                            'translated_text_length': translated_text_length
                        })

                    except Exception as e:
                        print(f"Error loading {project_name}/{ai_name}/{version}: {e}")
                        continue

        # 写入CSV
        if rows:
            self._write_csv('project_info.csv', rows)
            print(f"Saved project_info.csv ({len(rows)} rows)")

    def collect_file_compile_stats(self, versions: List[str], ai_names: List[str]) -> None:
        """
        收集文件级别编译统计

        包括：文件编译成功率、每个文件的编译状态
        """
        file_rows = []
        summary_rows = []

        for version in versions:
            for ai_name in ai_names:
                mapped_ai_name = self.get_mapped_ai_name(ai_name)

                for project_name in cfg_all_project_names(version):
                    eval_dir = cfg_eval_dir_path(ai_name, project_name, version)
                    if not eval_dir.exists():
                        continue

                    total_files = 0
                    success_files = 0

                    for json_file in eval_dir.glob('*.json'):
                        try:
                            with open(json_file, 'r', encoding='utf-8') as f:
                                data = json.load(f)

                            # 检查文件是否编译成功（所有函数都成功）
                            functions = data.get('functions', [])
                            if not functions:
                                continue

                            total_files += 1
                            file_success = all(
                                func.get('success', True) for func in functions
                            )

                            if file_success:
                                success_files += 1

                            # 详细记录
                            file_rows.append({
                                'project_name': project_name,
                                'ai_name': mapped_ai_name,
                                'version': version,
                                'strategy': self.get_strategy(version),
                                'file_name': data.get('file_name', json_file.stem + '.cpp'),
                                'total_functions': len(functions),
                                'success_functions': sum(1 for f in functions if f.get('success', True)),
                                'compile_success': file_success
                            })

                        except Exception as e:
                            print(f"Error reading {json_file}: {e}")
                            continue

                    # 汇总记录
                    if total_files > 0:
                        summary_rows.append({
                            'project_name': project_name,
                            'ai_name': mapped_ai_name,
                            'version': version,
                            'strategy': self.get_strategy(version),
                            'total_files': total_files,
                            'success_files': success_files,
                            'compile_rate': success_files / total_files
                        })

        # 写入CSV
        if file_rows:
            self._write_csv('file_compile_details.csv', file_rows)
            print(f"Saved file_compile_details.csv ({len(file_rows)} rows)")

        if summary_rows:
            self._write_csv('file_compile_summary.csv', summary_rows)
            print(f"Saved file_compile_summary.csv ({len(summary_rows)} rows)")

    def collect_method_compile_stats(self, versions: List[str], ai_names: List[str]) -> None:
        """
        收集方法级别编译统计

        包括：方法编译成功率、每个方法的编译状态
        """
        method_rows = []
        summary_rows = []

        for version in versions:
            for ai_name in ai_names:
                mapped_ai_name = self.get_mapped_ai_name(ai_name)

                for project_name in cfg_all_project_names(version):
                    eval_dir = cfg_eval_dir_path(ai_name, project_name, version)
                    if not eval_dir.exists():
                        continue

                    total_methods = 0
                    success_methods = 0

                    for json_file in eval_dir.glob('*.json'):
                        try:
                            with open(json_file, 'r', encoding='utf-8') as f:
                                data = json.load(f)

                            file_name = data.get('file_name', json_file.stem + '.cpp')

                            for func in data.get('functions', []):
                                total_methods += 1
                                success = func.get('success', True)
                                if success:
                                    success_methods += 1

                                # 详细记录
                                method_rows.append({
                                    'project_name': project_name,
                                    'ai_name': mapped_ai_name,
                                    'version': version,
                                    'strategy': self.get_strategy(version),
                                    'file_name': file_name,
                                    'signature': func.get('signature', ''),
                                    'compile_success': success,
                                    'log_output_length': len(func.get('log_output', ''))
                                })

                        except Exception as e:
                            print(f"Error reading {json_file}: {e}")
                            continue

                    # 汇总记录
                    if total_methods > 0:
                        summary_rows.append({
                            'project_name': project_name,
                            'ai_name': mapped_ai_name,
                            'version': version,
                            'strategy': self.get_strategy(version),
                            'total_methods': total_methods,
                            'success_methods': success_methods,
                            'compile_rate': success_methods / total_methods
                        })

        # 写入CSV
        if method_rows:
            self._write_csv('method_compile_details.csv', method_rows)
            print(f"Saved method_compile_details.csv ({len(method_rows)} rows)")

        if summary_rows:
            self._write_csv('method_compile_summary.csv', summary_rows)
            print(f"Saved method_compile_summary.csv ({len(summary_rows)} rows)")

    def collect_error_stats(self, versions: List[str], ai_names: List[str]) -> None:
        """
        收集文件级别错误统计

        只统计顶层errors字段（文件级别分析结果）
        """
        file_rows = []
        summary_rows = []

        for version in versions:
            for ai_name in ai_names:
                mapped_ai_name = self.get_mapped_ai_name(ai_name)

                for project_name in cfg_all_project_names(version):
                    eval_dir = cfg_eval_dir_path(ai_name, project_name, version)
                    if not eval_dir.exists():
                        continue

                    # 初始化错误计数
                    error_counts = {error_type: 0 for error_type in self.ERROR_TYPES}
                    files_with_errors = 0
                    total_errors = 0

                    for json_file in eval_dir.glob('*.json'):
                        try:
                            with open(json_file, 'r', encoding='utf-8') as f:
                                data = json.load(f)

                            file_name = data.get('file_name', json_file.stem + '.cpp')

                            # 只统计顶层errors（文件级别）
                            errors = data.get('errors', [])

                            if errors:
                                files_with_errors += 1

                            for error in errors:
                                error_type = error.get('error_type', 'Other Errors')
                                if error_type not in error_counts:
                                    error_type = 'Other Errors'
                                error_counts[error_type] += 1
                                total_errors += 1

                                # 详细记录
                                file_rows.append({
                                    'project_name': project_name,
                                    'ai_name': mapped_ai_name,
                                    'version': version,
                                    'strategy': self.get_strategy(version),
                                    'file_name': file_name,
                                    'error_type': error_type,
                                    'error_detail': error.get('error_detail', '')[:200]  # 限制长度
                                })

                        except Exception as e:
                            print(f"Error reading {json_file}: {e}")
                            continue

                    # 汇总记录
                    summary_rows.append({
                        'project_name': project_name,
                        'ai_name': mapped_ai_name,
                        'version': version,
                        'strategy': self.get_strategy(version),
                        'files_with_errors': files_with_errors,
                        'total_errors': total_errors,
                        **error_counts
                    })

        # 写入CSV
        if file_rows:
            self._write_csv('error_details.csv', file_rows)
            print(f"Saved error_details.csv ({len(file_rows)} rows)")

        if summary_rows:
            self._write_csv('error_summary.csv', summary_rows)
            print(f"Saved error_summary.csv ({len(summary_rows)} rows)")

    def _write_csv(self, filename: str, rows: List[Dict]) -> None:
        """写入CSV文件"""
        if not rows:
            return

        filepath = self.output_dir / filename
        keys = rows[0].keys()

        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            writer.writerows(rows)

    def collect_all(self, versions: Optional[List[str]] = None, ai_names: Optional[List[str]] = None) -> None:
        """
        收集所有统计信息

        Args:
            versions: 版本列表，默认['v3', 'v4', 'v4_1']
            ai_names: AI名称列表，默认['deepseek', 'qwen', 'gpt']
        """
        if versions is None:
            versions = ['v3', 'v4', 'v4_1']
        if ai_names is None:
            ai_names = ['deepseek', 'qwen', 'gpt']

        print("=" * 60)
        print("Starting statistics collection...")
        print("=" * 60)

        print("\n[1/4] Collecting project info...")
        self.collect_project_info(versions, ai_names)

        print("\n[2/4] Collecting file compile stats...")
        self.collect_file_compile_stats(versions, ai_names)

        print("\n[3/4] Collecting method compile stats...")
        self.collect_method_compile_stats(versions, ai_names)

        print("\n[4/4] Collecting error stats...")
        self.collect_error_stats(versions, ai_names)

        print("\n" + "=" * 60)
        print("Statistics collection completed!")
        print(f"Output directory: {self.output_dir}")
        print("=" * 60)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Collect compile/error statistics')
    parser.add_argument('--versions', nargs='+', default=['v4_7'], help='Versions to collect')
    parser.add_argument('--ai-names', nargs='+', default=['deepseek'], help='AI names to collect')
    args = parser.parse_args()

    collector = StatisticsCollector()
    collector.collect_all(versions=args.versions, ai_names=args.ai_names)
