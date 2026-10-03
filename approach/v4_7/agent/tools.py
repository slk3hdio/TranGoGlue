import subprocess
import os
import sys
from pathlib import Path

approach_dir = str(Path(__file__).resolve().parents[2])
if approach_dir not in sys.path:
    sys.path.insert(0, approach_dir)

from path_config import cfg_review_dir_path
from v4_7.steps import version


def validate_project_after_link(
    project_name: str,
    work_dir: Path,
    compile_timeout: int = 60,
    test_suites: tuple[str, ...] = ("base",),
) -> tuple[bool, str]:
    """链接项目，并在存在功能测试时构建和执行测试。

    参数:
        project_name: 当前翻译项目名称。
        work_dir: 待验证的 C++ 产物目录。
        compile_timeout: 编译及测试运行超时基准秒数。
        test_suites: 链接成功后按顺序执行的功能测试套件。
    返回:
        校验是否通过，以及可反馈给 repair Agent 的诊断日志。
    """
    from v4_7.scripts.evaluate_functional_tests import (
        evaluate_project,
        format_repair_feedback,
        functional_test_source,
    )
    from v4_7.steps.cpp_compile_step import link_project_dir

    success, link_log = link_project_dir(
        work_dir,
        compile_timeout=compile_timeout,
        link_timeout=max(compile_timeout * 2, 120),
    )
    if not success:
        return False, link_log

    validation_logs = [link_log.strip()] if link_log.strip() else []
    for suite in test_suites:
        if suite not in {"base", "additional"}:
            return False, f"[functional test configuration error] unsupported suite: {suite}"
        test_source = functional_test_source(project_name, suite=suite)
        if not test_source.is_file():
            continue

        try:
            report = evaluate_project(
                project_name,
                work_dir,
                timeout=compile_timeout,
                suite=suite,
            )
        except Exception as exc:
            return False, (
                "[functional test infrastructure error] project link succeeded, "
                f"but suite={suite} could not run: {exc}"
            )

        if report.get("status") != "passed":
            return False, (
                f"[functional test suite={suite}]\n"
                + format_repair_feedback(report, test_source)
            )
        validation_logs.append(
            f"Functional tests ({suite}) passed: {report.get('passed_tests', 0)}/"
            f"{report.get('planned_tests', 0)}"
        )
    return True, "\n".join(validation_logs)


def get_all_tools(
    ai_name,
    project_name,
    work_dir: Path | None = None,
    compile_timeout: int = 60,
    link_mode: bool = True,
    test_suites: tuple[str, ...] = ("base",),
    readonly_files: set[str] | None = None,
):
    """创建并返回 Agent 可用的工具集合。

    提供文件的编译、读取、写入、创建与编辑五个工具，
    所有工具均基于 work_dir（缺省为评审目录）进行相对路径解析，
    并通过 _safe_path 限制路径逃逸，保证工具只在限定目录内操作。

    Args:
        ai_name: AI 模型名称，用于默认评审目录的路径构造。
        project_name: 项目名称，用于默认评审目录的路径构造。
        work_dir: 工具操作的工作目录；为 None 时使用默认评审目录。
        compile_timeout: 单次文件编译超时时间（秒）。
        link_mode: 是否以链接模式编译整个工程（仅影响 compile_file）。
        test_suites: 项目链接成功后按顺序执行的功能测试套件。
        readonly_files: 只读文件名集合（如手写桩文件），写类工具命中时拒绝修改。

    Returns:
        dict: 包含 compile_file、read_file、write_file、
              create_file、edit_file 五个工具函数的映射。
    """
    base_dir = Path(work_dir) if work_dir is not None else cfg_review_dir_path(ai_name, project_name, version)
    # 只读集合统一小写比较，规避 Windows 大小写不敏感造成的绕过
    readonly_set = {name.casefold() for name in (readonly_files or set())}

    def _readonly_error(file: str) -> dict | None:
        """若目标文件在只读集合中，返回拒绝结果；否则返回 None。"""
        if file and Path(file).name.casefold() in readonly_set:
            return {
                "success": False,
                "error": f"{file} is a read-only hand-written stub; do not modify it",
            }
        return None

    def _safe_path(file: str) -> Path | None:
        """将用户提供的文件名解析为工作目录内的安全绝对路径。

        在内部检查路径是否位于 base_dir 之下，防止任意路径访问。

        Args:
            file: 用户提供的文件名字符串。

        Returns:
            Path | None: 解析得到的绝对路径；若为空或路径越界则返回 None。
        """
        if not file:
            return None
        file_path = (base_dir / file).resolve()
        base_path = base_dir.resolve()
        if base_path != file_path and base_path not in file_path.parents:
            return None
        return file_path

    def compile_file(file: str) -> dict:
        """
        Compile a C++ source file, then (in link mode) compile and link the whole project.
        Header targets first receive a self-include check; in link mode they must then
        pass whole-project linking and every available functional test as well.
        Input:  { "file": "xxx.cpp" } or { "file": "xxx.h" }
        Output: { "success": true/false, "log": "compiler/linker output" }
        """
        try:
            file_path = _safe_path(file)
            temp_unit: Path | None = None
            obj_file: Path | None = None
            if file_path is None:
                return {"success": False, "log": f"Invalid file path: {file}"}
            if not os.path.exists(file_path):
                return {"success": False, "log": f"File not found: {file}"}

            if file_path.suffix in {".h", ".hpp"}:
                # 头文件保持自包含 -c 检查（头文件自身无法链接）。
                temp_unit = base_dir / f"__compile_header__{file_path.stem}.cpp"
                temp_unit.write_text(f'#include "{file_path.name}"\n', encoding="utf-8")
                compile_input = temp_unit
                obj_file = base_dir / f"__compile_header__{file_path.stem}.o"

                result = subprocess.run(
                    [
                        "clang++",
                        "-std=c++17",
                        "-c",
                        "-ferror-limit=5",
                        "-ftemplate-backtrace-limit=5",
                        "-fno-caret-diagnostics",
                        "-fmacro-backtrace-limit=5",
                        compile_input.name,
                        "-o",
                        obj_file.name,
                    ],
                    capture_output=True,
                    text=True, encoding='utf-8', errors='replace',
                    timeout=compile_timeout,
                    cwd=str(base_dir),
                )

                success = result.returncode == 0
                log_output = result.stdout + result.stderr
                if obj_file.exists():
                    obj_file.unlink()
                if temp_unit is not None and temp_unit.exists():
                    temp_unit.unlink()
                if not success or not link_mode:
                    return {"success": success, "log": log_output}

                # 自包含成功不代表模板实例化和功能测试能够构建，继续执行项目级验证。
                success, project_log = validate_project_after_link(
                    project_name,
                    base_dir,
                    compile_timeout=compile_timeout,
                    test_suites=test_suites,
                )
                combined_log = "\n".join(
                    part for part in (log_output.strip(), project_log.strip()) if part
                )
                return {"success": success, "log": combined_log}

            if link_mode:
                # 整体链接通过后继续执行功能测试，把语义失败也纳入修复闭环。
                success, log_output = validate_project_after_link(
                    project_name,
                    base_dir,
                    compile_timeout=compile_timeout,
                    test_suites=test_suites,
                )
                return {"success": success, "log": log_output}

            compile_input = file_path
            obj_file = file_path.with_suffix(".o")
            result = subprocess.run(
                [
                    "clang++",
                    "-std=c++17",
                    "-c",
                    "-ferror-limit=5",
                    "-ftemplate-backtrace-limit=5",
                    "-fno-caret-diagnostics",
                    "-fmacro-backtrace-limit=5",
                    compile_input.name,
                    "-o",
                    obj_file.name,
                ],
                capture_output=True,
                text=True, encoding='utf-8', errors='replace',
                timeout=compile_timeout,
                cwd=str(base_dir),
            )

            success = result.returncode == 0
            log_output = result.stdout + result.stderr
            if obj_file.exists():
                obj_file.unlink()
            return {"success": success, "log": log_output}

        except Exception as e:
            return {"success": False, "log": str(e)}
        finally:
            for temp_file in (locals().get("obj_file"), locals().get("temp_unit")):
                if temp_file is not None and temp_file.exists():
                    try:
                        temp_file.unlink()
                    except OSError:
                        pass


    def read_file(file: str) -> dict:
        """
        Read a file content.
        Input:  { "file": "xxx.cpp" }
        Output: { "success": true/false, "content": "file content" }
        """
        try:
            file_path = _safe_path(file)
            if file_path is None:
                return {"success": False, "content": f"Invalid file path: {file}"}
            if not os.path.exists(file_path):
                return {"success": False, "content": "file not found, please use single file name, for exampe: xxx.cpp. If you think the file doesn't exist, create it."}

            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            return {"success": True, "content": content}

        except Exception as e:
            return {"success": False, "content": f"[Error reading file: {e}]"}


    def write_file(file: str, content: str) -> dict:
        """
        Overwrite an existing file.
        Input:  { "file": "xxx.cpp", "content": "new content" }
        Output: { "success": true/false, "message": "" or "error message" }
        """
        try:
            file_path = _safe_path(file)
            if file_path is None:
                return {"success": False, "message": "Missing file name"}
            rejected = _readonly_error(file)
            if rejected is not None:
                return rejected

            file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)

            return {"success": True}

        except Exception as e:
            return {"success": False, "error": str(e)}


    def create_file(file: str, content: str) -> dict:
        """
        Create a new file.
        Input:  { "file": "xxx.cpp", "content": "file content" }
        Output: { "success": true/false }
        """
        try:
            file_path = _safe_path(file)
            if file_path is None:
                return {"success": False, "error": "Missing file name"}
            rejected = _readonly_error(file)
            if rejected is not None:
                return rejected

            if os.path.exists(file_path):
                return {"success": False, "error": "File already exists"}

            file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)

            return {"success": True}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def edit_file(file: str, old_str: str, new_str: str) -> dict:
        """
        Replace one exact string occurrence in an existing file.
        Input:  { "file": "xxx.cpp", "old_str": "...", "new_str": "..." }
        Output: { "success": true/false }
        """
        try:
            file_path = _safe_path(file)
            if file_path is None:
                return {"success": False, "error": "Missing file name"}
            rejected = _readonly_error(file)
            if rejected is not None:
                return rejected
            if not file_path.exists():
                return {"success": False, "error": f"File not found: {file}"}
            content = file_path.read_text(encoding="utf-8")
            if old_str not in content:
                return {"success": False, "error": "old_str not found"}
            file_path.write_text(content.replace(old_str, new_str, 1), encoding="utf-8")
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    return {
        "compile_file":compile_file,
        "read_file":read_file,
        "write_file":write_file,
        "create_file":create_file,
        "edit_file":edit_file,
    }


# -----------------------------
# Example usage
# -----------------------------
if __name__ == "__main__":
    tools = get_all_tools("deepseek", "Cookie")
    compile_file = tools["compile_file"]
    read_file = tools["read_file"]
    write_file = tools["write_file"]
    create_file = tools["create_file"]

    # Example 1: Compile file
    print(compile_file("main.cpp"))

    # Example 2: Read file
    print(read_file("main.cpp"))

    # Example 3: Write file
    print(write_file("main.cpp", "// modified code"))

    # Example 4: Create new file
    print(create_file("new.cpp", "int main() { return 0; }"))
