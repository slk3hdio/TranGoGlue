"""编译并执行翻译后 C++ 项目的功能测试。"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import tempfile
from pathlib import Path
from typing import Any


TEST_COUNT_PATTERN = re.compile(r"SITP_TEST_COUNT:\s*(\d+)")
RESULT_PREFIX = "SITP_TEST_RESULT\t"
START_PREFIX = "SITP_TEST_START\t"
MAIN_FUNCTION_PATTERN = re.compile(r"\b(?:int|auto|void)\s+main\s*\(")


WINDOWS_CRASH_DESCRIPTIONS = {
    0xC0000005: "Windows access violation（非法内存访问）",
    0xC00000FD: "Windows stack overflow（栈溢出）",
    0xC0000374: "Windows heap corruption（堆损坏）",
    0xC0000409: "Windows stack buffer overrun / fast fail（栈缓冲区越界或快速失败）",
}


def functional_test_source(project: str, suite: str = "base") -> Path:
    """返回指定项目的功能测试源文件路径。

    参数:
        project: 项目名称。
        suite: 测试套件名称；base 为原测试，additional 为附加测试。
    返回:
        仓库内对应的 C++ 功能测试源文件路径。
    """
    test_root = Path(__file__).resolve().parent.parent / "functional_tests"
    if suite == "additional":
        test_root /= "additional"
    return test_root / f"{project}_test.cpp"


def parse_args() -> argparse.Namespace:
    """解析命令行参数并返回参数对象。"""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", required=True, help="项目名，例如 Cookie")
    parser.add_argument("--result-dir", required=True, type=Path, help="翻译产物 result 目录")
    parser.add_argument("--output", type=Path, help="可选的 JSON 报告输出路径")
    parser.add_argument(
        "--test-source",
        type=Path,
        help="可选的 API 适配测试源；未指定时使用仓库内统一测试源",
    )
    parser.add_argument("--compiler", default="clang++", help="C++ 编译器，默认 clang++")
    parser.add_argument("--timeout", type=int, default=30, help="测试程序超时秒数")
    parser.add_argument(
        "--suite",
        choices=("base", "additional"),
        default="base",
        help="测试套件：base 为原测试，additional 为独立附加测试",
    )
    return parser.parse_args()


def read_planned_count(test_source: Path) -> int:
    """从测试源文件读取计划测试数。

    参数:
        test_source: C++ 测试源文件。
    返回:
        测试文件声明的用例总数。
    """
    source = test_source.read_text(encoding="utf-8")
    match = TEST_COUNT_PATTERN.search(source)
    if not match:
        raise ValueError(f"测试文件缺少 SITP_TEST_COUNT: {test_source}")
    return int(match.group(1))


def parse_test_results(stdout: str) -> list[dict[str, str]]:
    """解析测试程序输出的逐用例结果。

    参数:
        stdout: 测试程序标准输出。
    返回:
        包含名称、状态和消息的测试结果列表。
    """
    results: list[dict[str, str]] = []
    for line in stdout.splitlines():
        if not line.startswith(RESULT_PREFIX):
            continue
        parts = line.split("\t", 3)
        if len(parts) < 4:
            continue
        results.append({"name": parts[1], "status": parts[2], "message": parts[3]})
    return results


def parse_last_started_test(stdout: str) -> str:
    """解析测试程序最后启动的用例名称。

    参数:
        stdout: 测试程序标准输出。
    返回:
        最后一个启动标记对应的用例名；不存在标记时返回空字符串。
    """
    started = [
        line[len(START_PREFIX):].strip()
        for line in stdout.splitlines()
        if line.startswith(START_PREFIX)
    ]
    return started[-1] if started else ""


def describe_returncode(returncode: int | None) -> str:
    """把常见进程退出码转换为可供 repair Agent 使用的诊断说明。

    参数:
        returncode: 子进程退出码，未运行时为 None。
    返回:
        包含十六进制状态码及排查建议的说明；普通退出码返回空字符串。
    """
    if returncode is None:
        return ""
    unsigned_code = returncode & 0xFFFFFFFF
    description = WINDOWS_CRASH_DESCRIPTIONS.get(unsigned_code)
    if description is None:
        return ""
    detail = f"{description}, code=0x{unsigned_code:08X}"
    if unsigned_code == 0xC0000374:
        detail += (
            "；重点检查重复释放、从借用裸指针构造 shared_ptr/reset、"
            "以及同一对象被多个独立智能指针控制块接管的问题；修复后还必须"
            "保证被保存的对象在调用结束后仍由共享所有权持有，不能用无操作删除器"
            "掩盖悬空指针"
        )
    return detail


def find_production_sources(result_dir: Path) -> list[Path]:
    """查找应与功能测试共同构建的翻译实现文件。

    参数:
        result_dir: 翻译产物目录。
    返回:
        排除链接探针入口和临时文件后的 C++ 实现文件列表。
    """
    sources: list[Path] = []
    for source in sorted(result_dir.glob("*.cpp")):
        if source.name.startswith("__"):
            continue
        content = source.read_text(encoding="utf-8", errors="replace")
        # 功能测试自带 main；排除历史运行遗留的任意链接探针入口。
        if MAIN_FUNCTION_PATTERN.search(content):
            continue
        sources.append(source)
    return sources


def build_report(
    project: str,
    result_dir: Path,
    planned_count: int,
    compile_process: subprocess.CompletedProcess[str],
    run_process: subprocess.CompletedProcess[str] | None,
    timed_out: bool,
) -> dict[str, Any]:
    """汇总编译与执行阶段，生成不忽略构建失败的严格口径报告。

    参数:
        project: 项目名称。
        result_dir: 翻译结果目录。
        planned_count: 计划执行的用例数。
        compile_process: 编译子进程结果。
        run_process: 执行子进程结果；未执行时为 None。
        timed_out: 测试程序是否超时。
    返回:
        可序列化为 JSON 的评估报告。
    """
    # 测试驱动编译或链接失败时，所有计划用例在严格口径中均计为失败。
    if compile_process.returncode != 0:
        status = "test_build_failed"
        tests: list[dict[str, str]] = []
    elif timed_out:
        status = "timeout"
        tests = []
    elif run_process is None:
        status = "not_run"
        tests = []
    else:
        tests = parse_test_results(run_process.stdout)
        all_planned_tests_passed = (
            len(tests) == planned_count
            and all(test["status"] == "PASS" for test in tests)
        )
        status = (
            "passed"
            if run_process.returncode == 0 and all_planned_tests_passed
            else "test_failed"
        )

    passed_count = sum(test["status"] == "PASS" for test in tests)
    executed_count = len(tests)
    strict_rate = passed_count / planned_count if planned_count else 0.0
    conditional_rate = passed_count / executed_count if executed_count else 0.0

    return {
        "project": project,
        "result_dir": str(result_dir.resolve()),
        "status": status,
        "test_build_success": compile_process.returncode == 0,
        "timed_out": timed_out,
        "planned_tests": planned_count,
        "executed_tests": executed_count,
        "passed_tests": passed_count,
        "strict_pass_rate": strict_rate,
        "conditional_pass_rate": conditional_rate,
        "tests": tests,
        "test_build_stdout": compile_process.stdout,
        "test_build_stderr": compile_process.stderr,
        "run_stdout": run_process.stdout if run_process else "",
        "run_stderr": run_process.stderr if run_process else "",
        "compile_returncode": compile_process.returncode,
        "run_returncode": run_process.returncode if run_process else None,
        "last_started_test": parse_last_started_test(run_process.stdout) if run_process else "",
        "run_returncode_diagnostic": (
            describe_returncode(run_process.returncode) if run_process else ""
        ),
    }


def evaluate_project(
    project: str,
    result_dir: Path,
    compiler: str = "clang++",
    timeout: int = 30,
    suite: str = "base",
    test_source: Path | None = None,
) -> dict[str, Any]:
    """编译并执行一个翻译项目的功能测试。

    参数:
        project: 项目名称。
        result_dir: 翻译产物目录。
        compiler: C++ 编译器命令。
        timeout: 测试程序运行超时秒数。
        suite: 测试套件名称；默认不改变原功能测试流程。
        test_source: 可选的 API 适配测试源；为空时使用统一测试源。
    返回:
        单项目功能评估报告。
    """
    result_dir = Path(result_dir).resolve()
    test_source = (
        Path(test_source).resolve()
        if test_source is not None
        else functional_test_source(project, suite)
    )
    test_root = test_source.parent
    harness_root = Path(__file__).resolve().parent.parent / "functional_tests"
    if not result_dir.is_dir():
        raise FileNotFoundError(f"翻译结果目录不存在: {result_dir}")
    if not test_source.is_file():
        raise FileNotFoundError(f"功能测试不存在: {test_source}")

    planned_count = read_planned_count(test_source)
    cpp_sources = find_production_sources(result_dir)

    # 在临时目录生成二进制，避免污染不可变的实验产物。
    with tempfile.TemporaryDirectory(prefix="sitp-functional-") as temp_dir:
        executable = Path(temp_dir) / f"{project}_functional_test.exe"
        compile_command = [
            compiler,
            "-std=c++17",
            "-O0",
            # 用 -iquote 而非 -I:项目头文件一律以引号方式互引,
            # 避免 Windows 大小写不敏感文件系统下项目头(如 String.h/Locale.h/Math.h)
            # 通过 -I 路径 shadow 掉 libc 的 <string.h>/<locale.h>/<math.h>。
            "-iquote",
            str(result_dir),
            "-iquote",
            str(test_root),
            "-iquote",
            str(harness_root),
            *(str(source) for source in cpp_sources),
            str(test_source),
            "-o",
            str(executable),
        ]
        compile_process = subprocess.run(
            compile_command,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )

        run_process: subprocess.CompletedProcess[str] | None = None
        timed_out = False
        if compile_process.returncode == 0:
            try:
                run_process = subprocess.run(
                    [str(executable)],
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    timeout=timeout,
                    check=False,
                )
            except subprocess.TimeoutExpired as exc:
                timed_out = True
                # 超时也保留已产生的部分输出：repair Agent 需要据此定位疑似死循环的用例。
                def _partial_text(value: Any) -> str:
                    """把 TimeoutExpired 携带的 stdout/stderr 统一转换为文本。"""
                    if value is None:
                        return ""
                    if isinstance(value, bytes):
                        return value.decode("utf-8", errors="replace")
                    return str(value)

                run_process = subprocess.CompletedProcess(
                    args=[str(executable)],
                    returncode=None,
                    stdout=_partial_text(exc.stdout),
                    stderr=_partial_text(exc.stderr),
                )

    return build_report(
        project,
        result_dir,
        planned_count,
        compile_process,
        run_process,
        timed_out,
    )


def evaluate(args: argparse.Namespace) -> dict[str, Any]:
    """按命令行参数执行功能测试并返回评估报告。

    参数:
        args: 已解析的命令行参数。
    返回:
        单项目功能评估报告。
    """
    return evaluate_project(
        args.project,
        args.result_dir,
        compiler=args.compiler,
        timeout=args.timeout,
        suite=args.suite,
        test_source=args.test_source,
    )


def format_repair_feedback(report: dict[str, Any], test_source: Path) -> str:
    """把功能测试报告格式化为可供 repair Agent 使用的反馈。

    参数:
        report: ``evaluate_project`` 返回的评估报告。
        test_source: 本次运行的功能测试源文件。
    返回:
        包含阶段、退出码、输出和测试源码的诊断文本。
    """
    lines = [
        "[functional test error] project link succeeded but functional validation failed",
        f"status={report.get('status', 'unknown')}",
        (
            f"planned={report.get('planned_tests', 0)}, "
            f"executed={report.get('executed_tests', 0)}, "
            f"passed={report.get('passed_tests', 0)}"
        ),
        f"compile_returncode={report.get('compile_returncode')}",
        f"run_returncode={report.get('run_returncode')}",
    ]
    if report.get("timed_out"):
        lines.append(
            "timed_out=true；测试程序运行超时，last_started_test 指向的用例疑似死循环。"
            "请沿该用例的调用路径检查循环退出条件，以及项目内库函数桩（如 zlib 等第三方库"
            "替代实现）是否存在未初始化状态、缓冲区不推进或死循环。"
        )
    tests = report.get("tests") or []
    finished_names = {test.get("name", "") for test in tests}
    failed_test_names = [test.get("name", "") for test in tests if test.get("status") != "PASS"]
    # 启动后没有产生结果的用例（崩溃或死循环中断），对 repair Agent 是关键线索。
    run_stdout_text = str(report.get("run_stdout", ""))
    started_names = [
        line[len(START_PREFIX):].strip()
        for line in run_stdout_text.splitlines()
        if line.startswith(START_PREFIX)
    ]
    unfinished_names = [name for name in started_names if name not in finished_names]
    if failed_test_names:
        lines.append("failed_tests=" + ", ".join(failed_test_names))
    if unfinished_names:
        lines.append(
            "unfinished_tests=" + ", ".join(unfinished_names)
            + "（这些用例启动后没有输出结果，疑似在其中崩溃或死循环，"
            "断言/异常信息见下方 test run stderr）"
        )
    last_started_test = str(report.get("last_started_test", "")).strip()
    if last_started_test:
        lines.append(f"last_started_test={last_started_test}")
    returncode_diagnostic = str(report.get("run_returncode_diagnostic", "")).strip()
    if returncode_diagnostic:
        lines.append(f"run_returncode_diagnostic={returncode_diagnostic}")
    for label, key in (
        ("test build stdout", "test_build_stdout"),
        ("test build stderr", "test_build_stderr"),
        ("test run stdout", "run_stdout"),
        ("test run stderr", "run_stderr"),
    ):
        content = str(report.get(key, "")).strip()
        if content:
            lines.extend((f"\n--- {label} ---", content))
    tests = report.get("tests") or []
    if tests:
        lines.extend(("\n--- parsed test results ---", json.dumps(tests, ensure_ascii=False, indent=2)))
    lines.extend((
        "\n--- functional test source (read-only contract; do not edit this test) ---",
        test_source.read_text(encoding="utf-8"),
    ))
    return "\n".join(lines)


def main() -> int:
    """运行评估、打印摘要并按需写入 JSON 报告。"""
    args = parse_args()
    report = evaluate(args)
    report_text = json.dumps(report, ensure_ascii=False, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(report_text + "\n", encoding="utf-8")
    print(report_text)
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
