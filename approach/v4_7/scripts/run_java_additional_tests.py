"""独立编译并运行 source_projects 下的 Java 附加测试。"""

from __future__ import annotations

import argparse
import locale
import shutil
import subprocess
import sys
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
SOURCE_PROJECTS_ROOT = REPOSITORY_ROOT / "source_projects"
LEGACY_ASM_PROJECTS = {"ClassStructureByChildClassTestCase"}


def parse_args() -> argparse.Namespace:
    """解析命令行参数并返回运行配置。"""
    parser = argparse.ArgumentParser(
        description="运行 additional_tests，不编译或执行原有 tests 目录中的测试源码。"
    )
    parser.add_argument(
        "--project",
        action="append",
        dest="projects",
        help="只运行指定项目；可重复传入。默认运行全部含 additional_tests 的项目。",
    )
    return parser.parse_args()


def discover_projects(selected: list[str] | None) -> list[Path]:
    """发现含附加测试的项目目录。

    Args:
        selected: 用户明确指定的项目名称列表，为空时自动发现。

    Returns:
        按项目名称排序后的目录列表。
    """
    if selected:
        projects = [SOURCE_PROJECTS_ROOT / name for name in selected]
    else:
        projects = [
            path
            for path in SOURCE_PROJECTS_ROOT.iterdir()
            if path.is_dir()
            and (path / "additional_tests").is_dir()
            and any((path / "additional_tests").rglob("*Test.java"))
        ]

    missing = [path.name for path in projects if not (path / "additional_tests").is_dir()]
    if missing:
        raise ValueError(f"以下项目不存在 additional_tests：{', '.join(missing)}")
    return sorted(projects, key=lambda path: path.name.lower())


def run_command(command: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    """在指定目录运行命令并实时输出捕获到的结果。

    Args:
        command: 不经 shell 拼接的命令参数。
        cwd: 命令的工作目录。

    Returns:
        包含退出码和输出的已完成进程。
    """
    completed = subprocess.run(
        command,
        cwd=cwd,
        text=True,
        encoding=locale.getpreferredencoding(False),
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    if completed.stdout:
        print(completed.stdout, end="" if completed.stdout.endswith("\n") else "\n")
    return completed


def class_name_from_source(source: Path, tests_root: Path) -> str:
    """根据附加测试源码相对路径生成 JUnit 类全名。

    Args:
        source: 测试源码路径。
        tests_root: additional_tests 根目录。

    Returns:
        使用点号分隔的完整类名。
    """
    return ".".join(source.relative_to(tests_root).with_suffix("").parts)


def compile_additional_tests(project: Path, sources: list[Path], build_dir: Path) -> bool:
    """仅编译 additional_tests 目录中的测试源码。

    Args:
        project: 当前项目目录。
        sources: 待编译的附加测试源码。
        build_dir: 附加测试专用输出目录。

    Returns:
        编译成功时返回 True。
    """
    if build_dir.exists():
        shutil.rmtree(build_dir)
    build_dir.mkdir(parents=True)

    classpath = f"{project / 'build'};{project / 'deps' / 'lib' / '*'};{project / 'tests' / 'lib' / '*'}"
    command = [
        "javac",
        "-encoding",
        "UTF-8",
        "-cp",
        classpath,
        "-d",
        str(build_dir),
        *[str(source) for source in sources],
    ]
    return run_command(command, project).returncode == 0


def rebuild_for_legacy_asm(project: Path) -> bool:
    """以 Java 8 字节码重建依赖旧版 ASM 的项目。

    Args:
        project: 需要兼容旧版 ASM 的项目目录。

    Returns:
        Java 8 兼容构建成功时返回 True。
    """
    if project.name not in LEGACY_ASM_PROJECTS:
        return True

    sources = sorted((project / "deps").rglob("*.java")) + sorted(project.glob("*.java"))
    classpath = str(project / "deps" / "lib" / "*")
    command = [
        "javac",
        "--release",
        "8",
        "-encoding",
        "UTF-8",
        "-cp",
        classpath,
        "-d",
        str(project / "build"),
        *[str(source) for source in sources],
    ]
    print(f"===== {project.name}: 生成旧版 ASM 可解析的 Java 8 字节码 =====")
    return run_command(command, project).returncode == 0


def run_project(project: Path) -> bool:
    """构建一个项目并运行其附加测试，且不执行原有测试。

    Args:
        project: 待测试项目目录。

    Returns:
        项目构建、附加测试编译和运行均成功时返回 True。
    """
    tests_root = project / "additional_tests"
    sources = sorted(tests_root.rglob("*.java"))
    test_sources = [source for source in sources if source.name.endswith("Test.java")]
    if not sources or not test_sources:
        print(f"[{project.name}] 未发现可运行的附加测试")
        return False

    print(f"\n===== {project.name}: 构建被测项目 =====")
    if run_command(["cmd", "/c", "build.bat"], project).returncode != 0:
        return False
    if not rebuild_for_legacy_asm(project):
        return False

    build_dir = tests_root / "build"
    print(f"===== {project.name}: 编译附加测试 =====")
    if not compile_additional_tests(project, sources, build_dir):
        return False

    classpath = f"{build_dir};{project / 'build'};{project / 'deps' / 'lib' / '*'};{project / 'tests' / 'lib' / '*'}"
    test_classes = [class_name_from_source(source, tests_root) for source in test_sources]
    print(f"===== {project.name}: 运行 {len(test_classes)} 个附加测试类 =====")
    command = ["java", "-cp", classpath, "org.junit.runner.JUnitCore", *test_classes]
    return run_command(command, project).returncode == 0


def main() -> int:
    """运行所选项目并返回适合命令行使用的总体退出码。"""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    try:
        projects = discover_projects(parse_args().projects)
    except ValueError as error:
        print(error, file=sys.stderr)
        return 2

    failures: list[str] = []
    for project in projects:
        if not run_project(project):
            failures.append(project.name)

    print("\n===== 附加测试汇总 =====")
    print(f"项目总数: {len(projects)}，通过: {len(projects) - len(failures)}，失败: {len(failures)}")
    if failures:
        print(f"失败项目: {', '.join(failures)}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
