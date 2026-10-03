"""
错误分析模块

调用LLM分析编译错误，将错误分类并保存到JSON文件中。
"""
import json
from pathlib import Path
from typing import Dict, List, Optional
import sys

p_dir = str(Path(__file__).parent)
pp_dir = str(Path(__file__).parent.parent)
if pp_dir not in sys.path:
    sys.path.append(pp_dir)
if p_dir not in sys.path:
    sys.path.append(p_dir)

from path_config import cfg_eval_dir_path, cfg_all_project_names
from utils.Generator import Generator
from analysis_prompt import get_analysis_prompt, json_example


class ErrorAnalyzer:
    """
    基于LLM的编译错误分析器
    """

    def __init__(self, generator: Generator):
        self.generator = generator

    def analyze_log(self, function_code: str, log_output: str) -> List[Dict[str, str]]:
        """
        调用LLM分析编译错误

        Args:
            function_code: 函数代码
            log_output: 编译器的错误输出

        Returns:
            错误列表，每个错误包含 error_type 和 error_detail
        """
        if not log_output or not log_output.strip():
            return []

        prompt = f"""You need to analyze the compilation error of a C++ function.

Here is the function code:
```cpp
{function_code}
```

Here is the compiler error output:
```
{log_output}
```

Please analyze the error and categorize it into one of the following types:
1. Syntax Rule Violation: Syntax and language feature errors
2. Type Error: Errors of type system, e.g., variable/parameter type mismatch; incorrect return value type; type incomplete; illegal type conversion
3. Declaration Mismatch: Mismatched parameter tables, or inconsistent declaration and definition signatures
4. Undefined Symbols: Unknown functions/variables/classes
5. Duplicated Definitions: Redefinition of variables, functions, or classes
6. Header File Error: The header file that should be included is missing, or a header file that does not exist is included
7. Other Errors: Other unexpected errors

Response in JSON format:
```json
{{
    "errors": [
        {{
            "error_type": "Type Error",
            "error_detail": "variable type mismatch: expected int but got std::string"
        }}
    ]
}}
```

Note:
1. Only analyze errors that cause compilation failure, ignore warnings
2. If there are multiple errors, list them all
3. If compilation succeeded (no error), return empty errors array
"""

        try:
            response = self.generator.generate([prompt])
            if not response or not response[0]:
                return []

            # 提取JSON
            content = response[0]
            json_match = self._extract_json(content)
            if not json_match:
                return []

            data = json.loads(json_match)
            return data.get("errors", [])

        except Exception as e:
            print(f"LLM analysis failed: {e}")
            return []

    def _extract_json(self, content: str) -> str:
        """从LLM响应中提取JSON"""
        # 查找```json ... ```格式
        import re
        match = re.search(r'```(?:json)?\s*({[\s\S]*?})\s*```', content)
        if match:
            return match.group(1)

        # 查找纯JSON对象
        match = re.search(r'({[\s\S]*})', content)
        if match:
            return match.group(1)

        return content


class FileLevelErrorAnalyzer:
    """
    文件级别的错误分析器

    使用analysis_prompt原文，直接分析整个文件，将errors放在JSON顶层
    支持批量并行分析多个文件
    """

    def __init__(self, generator: Generator):
        self.generator = generator

    def analyze_files_batch(self, json_files: List[Path]) -> Dict[Path, bool]:
        """
        批量分析多个JSON文件

        Args:
            json_files: JSON文件路径列表

        Returns:
            Dict[文件路径, 是否成功分析]
        """
        if not json_files:
            return {}

        # 首先清除所有文件的旧errors
        print(f"  Clearing old errors from {len(json_files)} files...")
        for json_file in json_files:
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                # 清除顶层errors
                if 'errors' in data:
                    del data['errors']
                    # 立即保存清除后的文件
                    with open(json_file, 'w', encoding='utf-8') as f:
                        json.dump(data, f, indent=4, ensure_ascii=False)

                # 同时清除函数级别的旧errors（如果存在）
                modified = False
                for func in data.get('functions', []):
                    if 'errors' in func:
                        del func['errors']
                        modified = True

                if modified:
                    with open(json_file, 'w', encoding='utf-8') as f:
                        json.dump(data, f, indent=4, ensure_ascii=False)

            except Exception as e:
                print(f"    Warning: Failed to clear errors in {json_file.name}: {e}")
                continue

        # 准备数据
        file_data_map = {}  # json_file -> (original_data, prompt, needs_analysis)
        prompts = []
        prompt_to_file = {}  # prompt_index -> json_file

        for json_file in json_files:
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                # 检查是否需要分析
                functions = data.get('functions', [])
                failed_functions = [f for f in functions if not f.get('success', True)]

                if not failed_functions:
                    # 如果没有失败的函数，清除顶层errors
                    if 'errors' in data:
                        del data['errors']
                        with open(json_file, 'w', encoding='utf-8') as f:
                            json.dump(data, f, indent=4, ensure_ascii=False)
                        print(f"  Cleared errors (no failures): {json_file.name}")
                    file_data_map[json_file] = (data, None, False)
                    continue

                # 构造要分析的JSON数据（只包含必要字段）
                analysis_data = {
                    "file_name": data.get("file_name", ""),
                    "includes": data.get("includes", []),
                    "functions": []
                }

                for func in functions:
                    func_info = {
                        "signature": func.get("signature", ""),
                        "function_code": func.get("function_code", ""),
                        "success": func.get("success", True),
                        "log_output": func.get("log_output", "")
                    }
                    analysis_data["functions"].append(func_info)

                # 生成prompt
                prompt = get_analysis_prompt(json.dumps(analysis_data, indent=2))

                file_data_map[json_file] = (data, prompt, True)
                prompt_to_file[len(prompts)] = json_file
                prompts.append(prompt)

            except json.JSONDecodeError as e:
                print(f"  Error: JSON decode failed in {json_file}: {e}")
                file_data_map[json_file] = (None, None, False)
            except Exception as e:
                print(f"  Error: Failed to prepare {json_file}: {e}")
                file_data_map[json_file] = (None, None, False)

        if not prompts:
            # 没有需要分析的文件
            return {f: file_data_map[f][2] is False for f in json_files}

        print(f"  Batch analyzing {len(prompts)} files with LLM...")

        # 批量调用LLM
        try:
            responses = self.generator.generate(prompts)
        except Exception as e:
            print(f"  LLM batch generation failed: {e}")
            return {f: False for f in json_files if file_data_map.get(f, (None, None, False))[2]}

        # 处理响应
        results = {}
        for idx, response in enumerate(responses):
            json_file = prompt_to_file.get(idx)
            if not json_file:
                continue

            data, _, _ = file_data_map[json_file]

            if not response:
                print(f"  LLM returned empty response: {json_file.name}")
                results[json_file] = False
                continue

            try:
                # 提取JSON
                json_match = self._extract_json(response)
                if not json_match:
                    print(f"  Failed to extract JSON from LLM response: {json_file.name}")
                    results[json_file] = False
                    continue

                result = json.loads(json_match)
                errors = result.get("errors", [])

                # 将errors放在顶层
                if errors:
                    data["errors"] = errors
                    print(f"  Found {len(errors)} errors: {json_file.name}")
                elif "errors" in data:
                    del data["errors"]

                # 保存修改后的文件
                with open(json_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=4, ensure_ascii=False)

                results[json_file] = True

            except Exception as e:
                print(f"  LLM analysis failed for {json_file.name}: {e}")
                results[json_file] = False

        # 添加不需要分析的文件（已成功清除errors）
        for json_file, (data, prompt, needs_analysis) in file_data_map.items():
            if not needs_analysis and data is not None:
                results[json_file] = True

        return results

    def analyze_file(self, json_file: Path) -> bool:
        """
        分析单个JSON文件中的所有错误（使用批量接口）

        Args:
            json_file: JSON文件路径

        Returns:
            是否成功分析
        """
        results = self.analyze_files_batch([json_file])
        return results.get(json_file, False)

    def _extract_json(self, content: str) -> str:
        """从LLM响应中提取JSON"""
        import re
        # 查找```json ... ```格式
        match = re.search(r'```(?:json)?\s*({[\s\S]*?})\s*```', content)
        if match:
            return match.group(1)

        # 查找纯JSON对象
        match = re.search(r'({[\s\S]*})', content)
        if match:
            return match.group(1)

        return content


def analyze_file(json_file: Path, analyzer: ErrorAnalyzer) -> bool:
    """
    分析单个JSON文件中的编译错误
    """
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        modified = False

        for func in data.get('functions', []):
            log_output = func.get('log_output', '')
            success = func.get('success', True)

            # 只分析编译失败的函数
            if success or not log_output or not log_output.strip():
                if 'errors' in func:
                    del func['errors']
                    modified = True
                continue

            # 调用LLM分析错误
            errors = analyzer.analyze_log(func.get('function_code', ''), log_output)

            if errors:
                func['errors'] = errors
                modified = True
                print(f"    Found {len(errors)} errors in {func.get('signature', 'unknown')}")
            elif 'errors' in func:
                del func['errors']
                modified = True

        if modified:
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            print(f"  Updated: {json_file.name}")

        return True

    except Exception as e:
        print(f"  Error: Failed to analyze {json_file}: {e}")
        return False


def analyze_project(project_name: str, ai_name: str, version: str, analyzer: ErrorAnalyzer) -> None:
    """
    分析单个项目的所有JSON文件
    """
    eval_dir = cfg_eval_dir_path(ai_name, project_name, version)

    if not eval_dir.exists():
        print(f"[{version}/{ai_name}/{project_name}] Eval directory not found")
        return

    json_files = list(eval_dir.glob('*.json'))
    if not json_files:
        print(f"[{version}/{ai_name}/{project_name}] No JSON files found")
        return

    print(f"[{version}/{ai_name}/{project_name}] Analyzing {len(json_files)} files...")

    success_count = 0
    for json_file in json_files:
        if analyze_file(json_file, analyzer):
            success_count += 1

    print(f"  -> Analyzed {success_count}/{len(json_files)} files")


def analyze_all_versions(versions: List[str], ai_names: List[str], ai_model: str = "deepseek") -> None:
    """
    分析所有版本的所有项目

    Args:
        versions: 版本列表
        ai_names: AI名称列表
        ai_model: 用于错误分析的AI模型
    """
    print(f"Initializing LLM generator ({ai_model})...")
    generator = Generator(ai_model)
    analyzer = ErrorAnalyzer(generator)

    for version in versions:
        print(f"\n{'='*60}")
        print(f"Processing version: {version}")
        print(f"{'='*60}")

        project_names = cfg_all_project_names(version)

        for ai_name in ai_names:
            print(f"\n--- AI: {ai_name} ---")

            for project_name in project_names:
                try:
                    analyze_project(project_name, ai_name, version, analyzer)
                except Exception as e:
                    print(f"  Error analyzing {project_name}: {e}")
                    continue


def analyze_project_file_level(project_name: str, ai_name: str, version: str, analyzer: FileLevelErrorAnalyzer) -> None:
    """
    使用文件级别分析单个项目的所有JSON文件（批量并行处理）
    """
    eval_dir = cfg_eval_dir_path(ai_name, project_name, version)

    if not eval_dir.exists():
        print(f"[{version}/{ai_name}/{project_name}] Eval directory not found")
        return

    json_files = list(eval_dir.glob('*.json'))
    if not json_files:
        print(f"[{version}/{ai_name}/{project_name}] No JSON files found")
        return

    print(f"[{version}/{ai_name}/{project_name}] Analyzing {len(json_files)} files (file-level, batch)...")

    # 使用批量分析接口
    results = analyzer.analyze_files_batch(json_files)
    success_count = sum(1 for success in results.values() if success)

    print(f"  -> Analyzed {success_count}/{len(json_files)} files")


def analyze_all_versions_file_level(versions: List[str], ai_names: List[str], ai_model: str = "deepseek") -> None:
    """
    使用文件级别分析所有版本的所有项目

    Args:
        versions: 版本列表
        ai_names: AI名称列表
        ai_model: 用于错误分析的AI模型
    """
    print(f"Initializing LLM generator ({ai_model}) for file-level analysis...")
    generator = Generator(ai_model)
    analyzer = FileLevelErrorAnalyzer(generator)

    for version in versions:
        print(f"\n{'='*60}")
        print(f"Processing version: {version}")
        print(f"{'='*60}")

        project_names = cfg_all_project_names(version)

        for ai_name in ai_names:
            print(f"\n--- AI: {ai_name} ---")

            for project_name in project_names:
                try:
                    analyze_project_file_level(project_name, ai_name, version, analyzer)
                except Exception as e:
                    print(f"  Error analyzing {project_name}: {e}")
                    continue


def get_error_statistics(versions: Optional[List[str]] = None):
    """
    生成错误统计信息
    """
    import csv

    statistics_dir = Path("Statistics")
    statistics_dir.mkdir(exist_ok=True)

    error_types = [
        "Syntax Rule Violation",
        "Type Error",
        "Declaration Mismatch",
        "Undefined Symbols",
        "Duplicated Definitions",
        "Header File Error",
        "Other Errors"
    ]

    file_rows = []
    method_rows = []

    if versions is None:
        versions = ['v3', 'v4', 'v4_1']

    for version in versions:
        strategy = 'class' if version == 'v3' else 'method'

        for ai_name in ['deepseek', 'qwen', 'gpt']:
            for project_name in cfg_all_project_names(version):
                eval_dir = cfg_eval_dir_path(ai_name, project_name, version)
                if not eval_dir.exists():
                    continue

                file_count = 0
                method_count = 0
                error_counts = {error_type: 0 for error_type in error_types}

                for json_file in eval_dir.glob('*.json'):
                    try:
                        with open(json_file, 'r', encoding='utf-8') as f:
                            data = json.load(f)

                        has_errors = False

                        # 首先检查顶层 errors 字段（文件级别分析）
                        top_level_errors = data.get('errors', [])
                        if top_level_errors:
                            has_errors = True
                            for error in top_level_errors:
                                error_type = error.get('error_type', 'Other Errors')
                                if error_type not in error_counts:
                                    error_type = 'Other Errors'
                                error_counts[error_type] += 1

                        # 然后检查函数级别的 errors 字段（方法级别分析）
                        for func in data.get('functions', []):
                            method_count += 1
                            errors = func.get('errors', [])
                            if errors:
                                has_errors = True
                                for error in errors:
                                    error_type = error.get('error_type', 'Other Errors')
                                    if error_type not in error_counts:
                                        error_type = 'Other Errors'
                                    error_counts[error_type] += 1

                        if has_errors:
                            file_count += 1

                    except Exception as e:
                        print(f"Error reading {json_file}: {e}")
                        continue

                row = {
                    'project_name': project_name,
                    'ai_name': ai_name,
                    'strategy': strategy,
                    'file_count': file_count,
                    **error_counts,
                    'all': sum(error_counts.values())
                }
                file_rows.append(row)

                method_row = {
                    'project_name': project_name,
                    'ai_name': ai_name,
                    'strategy': strategy,
                    'method_count': method_count,
                    **error_counts,
                    'all': sum(error_counts.values())
                }
                method_rows.append(method_row)

    if file_rows:
        keys = file_rows[0].keys()
        with open(statistics_dir / 'error_statistics_class.csv', 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            writer.writerows(file_rows)
        print(f"Saved error_statistics_class.csv")

    if method_rows:
        keys = method_rows[0].keys()
        with open(statistics_dir / 'error_statistics_method.csv', 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            writer.writerows(method_rows)
        print(f"Saved error_statistics_method.csv")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Analyze compilation errors')
    parser.add_argument('--mode', choices=['method', 'file'], default='file',
                        help='Analysis mode: method (per-function) or file (whole file)')
    parser.add_argument('--ai', default='deepseek-v4',
                        help='AI model to use for analysis')
    parser.add_argument('--versions', nargs='+', default=['v4_3'],
                        help='Versions to analyze')
    parser.add_argument('--ai-names', nargs='+', default=['deepseek'],
                        help='AI names to analyze')

    args = parser.parse_args()

    if args.mode == 'method':
        # 使用LLM逐方法分析所有版本的错误
        print("Using method-level analysis...")
        analyze_all_versions(
            versions=args.versions,
            ai_names=args.ai_names,
            ai_model=args.ai
        )
    else:
        # 使用文件级别分析
        print("Using file-level analysis...")
        analyze_all_versions_file_level(
            versions=args.versions,
            ai_names=args.ai_names,
            ai_model=args.ai
        )

    # 生成统计信息
    print("\nGenerating statistics...")
    get_error_statistics(['v4_3'])

    print("\nDone!")
