from pathlib import Path
import sys
p_dir = str(Path(__file__).parent)
pp_dir = str(Path(__file__).parent.parent)
if pp_dir not in sys.path:
    sys.path.append(pp_dir)
if p_dir not in sys.path:
    sys.path.append(p_dir)

import subprocess
from typing import List, Dict, Optional
from path_config import cfg_all_project_names, cfg_eval_dir_path, cfg_translate_result_dir_path, cfg_statistics_dir_path, cfg_run_result_dir, cfg_best_run_id
import json
from tqdm import tqdm
import traceback


def _resolve_result_dir(ai_name: str, project_name: str, version: str) -> Path:
    """v4_7+ 使用编译成功率最高 run 的 result；旧版本使用扁平 result 目录。"""
    run_id = cfg_best_run_id(ai_name, project_name, version)
    if run_id:
        return cfg_run_result_dir(ai_name, project_name, version, run_id)
    return cfg_translate_result_dir_path(ai_name, project_name, version)


def compile_file(file_path:Path) -> tuple:
    """
    Compile a single C++ file with -c flag (no linking).
    """
    try:
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        # Derive object file name
        obj_file = file_path.with_suffix(".o")

        # Run clang++ -c
        result = subprocess.run(
            ["clang++", "-c","-ferror-limit=5","-ftemplate-backtrace-limit=5", "-fno-caret-diagnostics","-fmacro-backtrace-limit=5", str(file_path), "-o", str(obj_file)],
            capture_output=True,
            text=True, encoding='utf-8', errors='replace',
        )

        success = result.returncode == 0
        log_output = result.stdout + result.stderr
            
        if len(log_output) > 5000:
            new_output = ""
            for line in log_output.splitlines():
                if "In file included from" in line and "error:" not in line:
                    continue
                new_output += line + "\n"
            log_output = new_output
        return success, log_output

    except Exception as e:
        return False, str(e)

def compile_header_file(header_path: Path) -> tuple:
    """
    Compile a header by generating a temporary cpp file that includes it.
    """
    temp_cpp = header_path.parent / f"__compile_header__{header_path.stem}.cpp"
    try:
        temp_cpp.write_text(f'#include "{header_path.name}"\n', encoding="utf-8")
        return compile_file(temp_cpp)
    finally:
        if temp_cpp.exists():
            temp_cpp.unlink()
        temp_obj = temp_cpp.with_suffix(".o")
        if temp_obj.exists():
            temp_obj.unlink()

def calc_cpp_compile_rate(project_name, ai_name, version:str):
    """
    Calculate compile success rate for generated .cpp files only.
    Headers and generated externals without cpp outputs are excluded.
    """

    compile_success_count = 0
    total_count = 0

    result_dir_path = _resolve_result_dir(ai_name, project_name, version)
    if not result_dir_path.exists():
        print(f"{result_dir_path} does not exist.")
        return 0, 0

    for file in sorted(result_dir_path.iterdir()):
        if file.suffix != ".cpp":
            continue
        total_count += 1
        success, log_output = compile_file(file)
        if success:
            print(f"Compiled {file.name}(cpp) successfully.")
            compile_success_count += 1
        else:
            print(f"Failed to compile {file.name}(cpp).")

    success_rate = compile_success_count / total_count if total_count > 0 else 0
    print(
        f"{project_name}-{ai_name}-{version} cpp_total_count: {total_count}, "
        f"cpp_compile_success_count: {compile_success_count}, success_rate: {success_rate:.4f}"
    )
    return total_count, compile_success_count

def calc_file_compile_rate(project_name, ai_name, version:str):
    """
    Calculate the compile success rate for each file in the project.
    """

    compile_success_count = 0
    total_count = 0

    result_dir_path = _resolve_result_dir(ai_name, project_name, version)

    for file in result_dir_path.iterdir():
        if file.suffix == ".cpp":
            total_count += 1
            success, log_output = compile_file(file)
            if success:
                print(f"Compiled {file.name}(cpp) successfully.")
                compile_success_count += 1
        elif file.suffix == ".h":
            total_count += 1
            success, log_output = compile_header_file(file)
            if success:
                print(f"Compiled {file.name}(h) successfully.")
                compile_success_count += 1
    success_rate = compile_success_count / total_count if total_count > 0 else 0
    print(f"{project_name}-{ai_name}-{version} total_count: {total_count}, compile_success_count: {compile_success_count}, success_rate: {success_rate:.4f}")
    return total_count, compile_success_count

def calc_compile_rate_single(project_name, ai_name, version, file_name):
    file_name = file_name.split(".")[0]
    h_file_dir = _resolve_result_dir(ai_name, project_name, version)
    temp_file = h_file_dir / "temp.cpp"
    json_file = cfg_eval_dir_path(ai_name, project_name, version) / f"{file_name}.json"
    if not json_file.exists():
        raise FileNotFoundError(f"{json_file} does not exist.")
    json_data = json.load(open(json_file, "r", encoding="utf-8"))
    variables = json_data["variables"]
    variable_code = "\n".join([variable["variable_code"] for variable in variables])
    includes = []
    for include_file in json_data["includes"]:
        if include_file.endswith(".h"):
            includes.append(f"#include \"{include_file}\"")
        else:
            includes.append(f"#include <{include_file}>")
    include_code = "\n".join(includes) + "\n"
    compile_success_count = 0
    total_count = 0
    for function in json_data["functions"]:
        print(50*"=")
        # print(f"Compiling {function['signature']}...")
        code = include_code + variable_code + function["function_code"]
        try:
            temp_file.write_text(code, encoding="gbk")
            success, log_output = compile_file(temp_file)
            print(f"code:\n{code}")
            print(f"success: {success}")
            print(f"log_output:\n{log_output}")
        except UnicodeEncodeError as e:
            success = False
            print(f"{function['signature']} UnicodeEncodeError: {e}")
            log_output = str(e)
        except Exception as e:
            success = False
            print(f"{function['signature']} Exception: {e}")
            log_output = "Unknown error"
        if success:
            compile_success_count += 1
            function["success"] = True
            function["log_output"] = log_output
        else:
            function["success"] = False
            function["log_output"] = log_output
        total_count += 1

    return total_count, compile_success_count

def calc_method_compile_rate(project_name, ai_name, version:str):
    compile_success_count = 0
    total_count = 0
    
    # 首先计算总函数数
    all_functions = []
    h_file_dir = _resolve_result_dir(ai_name, project_name, version)
    if not h_file_dir.exists():
        print(f"{h_file_dir} does not exist. Skipping.")
        return 0, 0
    temp_file = h_file_dir / "temp.cpp"
    
    for json_file in cfg_eval_dir_path(ai_name, project_name, version).iterdir():
        if json_file.suffix == ".json":
            try:
                json_data = json.load(open(json_file, "r", encoding="utf-8"))
                all_functions.append((json_file, json_data))
                total_count += len(json_data["functions"])
            except json.JSONDecodeError as e:
                print(f"Error loading {json_file}: JSON {e}")
                raise
    
    # 使用tqdm显示进度条
    processed_count = 0
    with tqdm(total=total_count, desc=f"Compiling {project_name}-{ai_name}-{version}", unit="function") as pbar:
        for json_file, json_data in all_functions:
            # print(f"Compiling {json_file}")
            variables = json_data["variables"]
            variable_code = "\n".join([variable["variable_code"] for variable in variables])

            includes = []
            for include_file in json_data["includes"]:
                if include_file.endswith(".h"):
                    includes.append(f"#include \"{include_file}\"")
                else:
                    includes.append(f"#include <{include_file}>")
            include_code = "\n".join(includes) + "\n"

            for function in json_data["functions"]:
                code = include_code + variable_code + function["function_code"]
                try:
                    temp_file.write_text(code, encoding="utf-8")
                    success, log_output = compile_file(temp_file)
                except UnicodeEncodeError as e:
                    success = False
                    print(f"{function['signature']} UnicodeEncodeError: {e}")
                    log_output = str(e)
                except Exception as e:
                    success = False
                    print(f"{function['signature']} Exception: {e}")
                    log_output = "Unknown error"
                if success:
                    compile_success_count += 1
                    function["success"] = True
                    function["log_output"] = log_output
                else:
                    function["success"] = False
                    function["log_output"] = log_output
                
                # 更新进度条
                pbar.update(1)
                processed_count += 1

            json.dump(json_data, open(json_file, "w", encoding="utf-8"), indent=4)

    # 清除临时文件
    if temp_file.exists():
        temp_file.unlink()
    if temp_file.with_suffix(".o").exists():
        temp_file.with_suffix(".o").unlink()

    # 计算编译率
    if total_count == 0:
        print(f"{project_name}-{ai_name}-{version} has no functions to compile.")
        return 0, 0
    
    compile_rate = compile_success_count / total_count
    print(f"{project_name}-{ai_name}-{version} compile rate: {compile_rate:.4f}")
    return total_count, compile_success_count

def is_compiled(project_name, ai_name, version:str):
    eval_dir_path = cfg_eval_dir_path(ai_name, project_name, version)
    if not eval_dir_path.exists():
        return False
    files = list(eval_dir_path.iterdir())
    if not files:
        return False
    for file in files:
        if file.suffix == ".json":
            try:
                json_data = json.load(open(file, "r", encoding="utf-8"))
                for function_obj in json_data["functions"]:
                    if "success" not in function_obj:
                        return False
            except Exception as e:
                print(f"{file} Exception loading {e}")
                return False
    return True

def reset_compile_output():
    for version in ['v3', 'v4']:
        for project_name in cfg_all_project_names(version):
            for ai_name in ["deepseek", "qwen", "gpt"]:
                eval_dir_path = cfg_eval_dir_path(ai_name, project_name, version)
                if not eval_dir_path.exists():
                    continue
                for file in eval_dir_path.iterdir():
                    if file.suffix == ".json":
                        data = json.load(open(file, "r", encoding="utf-8"))
                        for function_obj in data["functions"]:
                            if "success" in function_obj:
                                function_obj.pop("success")
                            if "log_output" in function_obj:
                                function_obj.pop("log_output")
                            if "errors" in function_obj:
                                function_obj.pop("errors")
                        json.dump(data, open(file, "w", encoding="utf-8"), indent=4)

if __name__ == "__main__":
    # calc_compile_rate_single("Cookie", "deepseek", "v3", "ParameterParser")
    # calc_file_compile_rate("CircuitBreakerExecutor", "gpt", "v4_2")
    calc_file_compile_rate("CircuitBreakerExecutor", "deepseek", "v4_3")
    if False:
        output_file_path = cfg_statistics_dir_path() / "compile_rate.csv"
        with open(output_file_path, "w", encoding="utf-8") as f:
            f.write("project_name,ai_name,strategy,total_cpp_count,success_file_count\n")
            for version in ['v3','v4', 'v4_1']:
                for project_name in cfg_all_project_names('v3'):
                    for ai_name in ['deepseek','qwen', 'gpt']:
                        try:
                            total_count, compile_success_count = calc_file_compile_rate(project_name, ai_name, version)
                            f.write(f"{project_name},{ai_name},{version},{total_count},{compile_success_count}\n")
                        except Exception as e:
                            print(f"{project_name}-{ai_name}-{version} compile failed")
                            traceback.print_exc()

    if False:
        reset_compile_output()
        output_file_path = cfg_statistics_dir_path() / "compile_rate_method.csv"
        with open(output_file_path, "w", encoding="utf-8") as f:
            f.write("project_name,ai_name,strategy,total_method_count,success_method_count\n")
            for version in ['v3', 'v4']:
                for project_name in cfg_all_project_names(version):
                    for ai_name in ["deepseek", "qwen", "gpt"]:
                        try:
                            if is_compiled(project_name, ai_name, version):
                                print(f"{project_name}-{ai_name}-{version} has already compiled. Skipping.")
                                continue
                            total_count, compile_success_count = calc_method_compile_rate(project_name, ai_name, version)
                            f.write(f"{project_name},{ai_name},{version},{total_count},{compile_success_count}\n")
                        except Exception as e:
                            # print(f"{project_name}-{ai_name}-{version} compile failed: {e}")
                            # traceback.print_exc()
                            print(f"{project_name}-{ai_name}-{version} compile failed.")

    # calc_compile_rate("Cookie", "gpt", "v3")


