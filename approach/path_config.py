from pathlib import Path
from typing import Optional
from datetime import datetime
import sys
import json
import os
def make_dir(func):
    """装饰器：在函数返回目录路径后，自动创建该目录（含父目录）。

    适用于返回 Path 的配置函数，确保返回的目录已实际存在。

    Args:
        func: 被装饰的、返回目录 Path 的函数。

    Returns:
        wrapper: 包装函数，返回已确保存在的目录 Path。
    """
    def wrapper(*args, **kwargs):
        dir_path = func(*args, **kwargs)
        if not dir_path.exists():
            dir_path.mkdir(parents=True)
        return dir_path
    return wrapper

# 本项目根目录
project_root_dir_path = Path(__file__).parent.parent


# 要翻译的原始项目目录
def cfg_source_project_dir_path() -> Path:
    """返回存放待翻译原始项目的根目录。

    默认返回项目根目录下的 source_projects；可通过环境变量
    SITP_SOURCE_PROJECTS_DIR 指向其他模块目录（如 source_projects_min50）。

    Returns:
        Path: 原始项目根目录。
    """
    override = os.environ.get("SITP_SOURCE_PROJECTS_DIR")
    if override:
        return Path(override)
    return project_root_dir_path / "source_projects"
        

def cfg_source_code_dir_path(project_name:str) -> Path:
    """返回指定项目的源码目录路径。

    Args:
        project_name: 项目名称。

    Returns:
        Path: source_projects 下对应项目的目录。
    """
    return cfg_source_project_dir_path() / project_name


# 输出总目录
@make_dir
def output_root_dir_path(version) -> Path:
    """返回指定版本的输出根目录，并确保其存在。

    Args:
        version: 版本标识（如 "v4_7"）。

    Returns:
        Path: 输出根目录路径。
    """
    return project_root_dir_path / "output" / version


# 解析工具目录
@make_dir
def cfg_parser_tool_path() -> Path:
    """返回 Java 解析工具（Gradle 工程）的路径，并确保目录存在。

    Returns:
        Path: approach/parser_tool 目录路径。
    """
    return project_root_dir_path / "approach" / "parser_tool"
# 判断是windows还是Linux
def cfg_gradlew_file_path()-> Path:
    """根据当前操作系统返回对应的 Gradle 脚本路径。

    在 Windows 系统上返回 gradlew.bat，否则返回 gradlew。

    Returns:
        Path: 可用的 Gradle 启动脚本路径。
    """
    is_windows = sys.platform.startswith("win")
    if is_windows:
        return cfg_parser_tool_path() / "gradlew.bat"
    else:
        return cfg_parser_tool_path() / "gradlew"

@make_dir
def cfg_split_output_dir_path(project_name:str, version:str) -> Path:
    """本目录存放分割后的原始代码"""
    return output_root_dir_path(version) / project_name / "split"

def cfg_method_call_file_path(project_name:str) -> Path:
    """储存方法调用信息的文件"""
    return cfg_source_project_dir_path() / project_name / "method_call.txt"


def cfg_cpp_stub_dirs(project_name: str) -> list[Path]:
    """返回手写 C++ 桩（manual_stub）JSON 定义的搜索目录。

    按覆盖优先级从高到低排列：模块级 cpp_stubs/ 在前，共享库 _cpp_stubs/ 在后。
    加载时同名类名按此顺序先占先得，实现"模块覆盖共享库"。
    目录不存在时对应项会被跳过（由调用方判断 is_dir）。

    Args:
        project_name: 当前翻译项目名称。

    Returns:
        list[Path]: 桩定义搜索目录列表（高优先级在前）。
    """
    source_root = cfg_source_project_dir_path()
    return [
        source_root / project_name / "cpp_stubs",
        source_root / "_cpp_stubs",
    ]


@make_dir
def cfg_translated_project_dir_path(ai_name:str, project_name:str, version:str) -> Path:
    """翻译后的项目根目录，存放所有翻译后生成的文件"""
    return output_root_dir_path(version) / project_name / ai_name

@make_dir
def cfg_binary_graph_dir_path(ai_name:str, project_name:str, version:str) -> Path:
    """二进制图结构文件的存放目录"""
    return output_root_dir_path(version) / project_name / ai_name / "bin"

def cfg_binary_graph_file_path(ai_name:str, project_name:str, version:str) -> Path:
    """二进制图结构文件"""
    return cfg_binary_graph_dir_path(ai_name, project_name, version) / "nodes.pkl"


def cfg_graph_dir_path(ai_name:str, project_name:str, version:str) -> Path:
    """图结构文件的存放目录"""
    return output_root_dir_path(version) / project_name / ai_name / "graph"

@make_dir
def cfg_translate_detail_dir(ai_name:str, project_name:str, version:str) -> Path:
    """详细的翻译过程记录"""
    return output_root_dir_path(version) / project_name / ai_name / "detail"

@make_dir
def cfg_translate_result_dir_path(ai_name:str, project_name:str, version:str) -> Path:
    """翻译结果目录"""
    return output_root_dir_path(version) / project_name / ai_name / "result"

def cfg_review_dir_path(ai_name:str, project_name:str, version:str) -> Path:    
    """修改审核目录"""
    return output_root_dir_path(version) / project_name / ai_name / "review"

def cfg_review_prompt_file_path(version:str):
    """返回指定版本的评审提示词文件路径。

    Args:
        version: 版本标识（如 "v4_7"）。

    Returns:
        Path: prompts 目录下 review_prompt.md 的路径。
    """
    return project_root_dir_path / "approach"/ version / "prompts" / "review_prompt.md"

@make_dir
def cfg_eval_dir_path(ai_name:str, project_name:str, version:str) -> Path:
    """评估目录"""
    return output_root_dir_path(version) / project_name / ai_name / "eval"

@make_dir
def cfg_statistics_dir_path(version:Optional[str] = None):
    if version is None:
        return project_root_dir_path / "statistics"
    """统计目录"""
    return project_root_dir_path / "statistics" / version

@make_dir
def cfg_chart_output_dir_path():
    """返回图表输出目录路径，并确保目录存在。

    Returns:
        Path: 图表输出目录的绝对路径。
    """
    configured_dir = os.environ.get("SITP_FIGURES_DIR", "").strip()
    if configured_dir:
        return Path(configured_dir).expanduser().resolve()
    return project_root_dir_path / "figures"

def cfg_all_project_names(version:str):
    """所有所有项目的名称"""
    if version in ['v0', 'v3', 'v4', 'v4_1', 'v4_2', 'v4_3', 'v4_4', 'v4_5']:
        # return ['DebugLogExceptionModule']
        return ["Cookie","CircuitBreakerExecutor","PerMessageDeflateExtensionTest", "DebugLogExceptionModule"]
    else:
        return [
            'AdviceListenerTestCase',             'Base32Codec',                    'BulkheadBuilder',
            'CircuitBreakerExecutor',             'ClassStructureByChildClassTestCase',
            'Cookie',                             'CsvWorkbook',                     'DebugLogExceptionModule',
            'DelayablePolicy',                    'Draft_6455',                     'Draft_6455Test',
            'EventWatchBuilderTestCase',          'ExecutionImpl',
            'FailsafeExecutor',                   'FailurePolicy',                  'Hashids',
            'Head',                               'HeaderGroup',                    'HttpParser',
            'HttpState',                          'HttpURL',                         'Issue231Test',
            'Issue260Test',                       'JSONParser',                     'NTLM',
            'OrGroupFilter',
            'PerMessageDeflateExtensionTest',     'ProgressPrinter',                'RateLimiterBuilder',
            'RateLimiterExecutor',                'ReadRowHolder',                  'ReadSheetHolder',
            'RFC2965Spec',                        'RetryPolicyConfig',              'SyncExecutionImpl',
            'TestIssues217',                      'TestIssues256',                  'TimeoutExecutor',
            'UndeclaredThrowableStrategy',        'WebSocketClient',                'WebSocketServer',
            'WriteCellData']

cfg_all_ai_names = ['qwen','deepseek','gpt']

# ========== Run-aware (timestamp-grouped) paths for v4_7+ ==========

@make_dir
def cfg_runs_base_dir(ai_name: str, project_name: str, version: str) -> Path:
    """Base directory containing all runs for a (version, project, ai) combo."""
    return output_root_dir_path(version) / project_name / ai_name / "runs"


@make_dir
def cfg_run_dir(ai_name: str, project_name: str, version: str, run_id: str) -> Path:
    """Directory for a specific run."""
    return cfg_runs_base_dir(ai_name, project_name, version) / run_id


def cfg_run_graph_dir(ai_name: str, project_name: str, version: str, run_id: str) -> Path:
    """Graph state directory for a specific run."""
    return cfg_run_dir(ai_name, project_name, version, run_id) / "graph"


def cfg_run_result_dir(ai_name: str, project_name: str, version: str, run_id: str) -> Path:
    """Translation result directory for a specific run."""
    return cfg_run_dir(ai_name, project_name, version, run_id) / "result"


def cfg_new_run_id() -> str:
    """生成一个新的运行标识（run id）。

    Returns:
        str: 基于当前时间戳格式化的运行标识，形如 YYYYMMDD_HHMMSS。
    """
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def cfg_latest_run_id(ai_name: str, project_name: str, version: str) -> Optional[str]:
    """返回指定 (version, project, ai) 下最新的运行标识。

    Args:
        ai_name: AI 模型名称。
        project_name: 项目名称。
        version: 版本标识。

    Returns:
        Optional[str]: 最新运行标识；目录不存在时返回 None。
    """
    runs_dir = cfg_runs_base_dir(ai_name, project_name, version)
    if not runs_dir.exists():
        return None
    run_ids = sorted([d.name for d in runs_dir.iterdir() if d.is_dir()])
    return run_ids[-1] if run_ids else None


def cfg_best_run_id(ai_name: str, project_name: str, version: str) -> Optional[str]:
    """选择编译成功率最高的 run；无 compile report 时回退到最新 run。"""
    runs_dir = cfg_runs_base_dir(ai_name, project_name, version)
    if not runs_dir.exists():
        return None

    best_run_id: Optional[str] = None
    best_score: float = -1.0
    for run_dir in runs_dir.iterdir():
        if not run_dir.is_dir():
            continue
        report_path = run_dir / "result" / "compile_report" / "cpp_compile_summary.json"
        if not report_path.exists():
            continue
        try:
            data = json.loads(report_path.read_text(encoding="utf-8"))
            success_rate = float(data.get("success_rate", 0) or 0)
            total_count = int(data.get("total_count", 0) or 0)
        except Exception:
            continue
        score = success_rate * 1000 + total_count
        if score > best_score:
            best_score = score
            best_run_id = run_dir.name

    if best_run_id is None:
        return cfg_latest_run_id(ai_name, project_name, version)
    return best_run_id


