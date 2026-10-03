"""
生成所有版本的eval文件并执行方法级别编译

流程：
1. 序列化所有项目的CPP代码（v3, v4, v4_1）
2. 执行方法级别编译，更新success和log_output字段
"""
import sys
from pathlib import Path

p_dir = str(Path(__file__).parent)
pp_dir = str(Path(__file__).parent.parent)
if pp_dir not in sys.path:
    sys.path.append(pp_dir)
if p_dir not in sys.path:
    sys.path.append(p_dir)

from file_serialization_str import serialize_all_projects, serialize_project_from_graph, save_serialized_files
from compile import calc_method_compile_rate, is_compiled
from path_config import cfg_all_project_names, cfg_eval_dir_path
import traceback

def process_project(project_name: str, ai_name: str, version: str, force_reserialize: bool = False, run_id: str = ""):
    """
    处理单个项目的序列化和编译

    Args:
        project_name: 项目名称
        ai_name: AI名称
        version: 版本号（v3, v4, v4_1, v4_7）
        force_reserialize: 是否强制重新序列化
        run_id: 可选。v4_7+ 结构下指定 run id；为空时自动使用最新 run。
    """
    print(f"\nProcessing project: {project_name} (AI: {ai_name}, Version: {version})")

    try:
        # Step 1: 序列化
        eval_dir = cfg_eval_dir_path(ai_name, project_name, version)
        needs_serialize = force_reserialize or not eval_dir.exists() or not any(eval_dir.iterdir())

        if needs_serialize:
            print(f"Serializing...")
            try:
                serialized = serialize_project_from_graph(ai_name, project_name, version, run_id=run_id)
                if serialized:
                    save_serialized_files(ai_name, project_name, version, serialized)
                    print(f"  -> Serialized {len(serialized)} files")
                else:
                    print(f"  -> No data to serialize")
                    return
            except FileNotFoundError as e:
                print(f"  -> Skipped (no graph data): {e}")
                return
            except Exception as e:
                print(f"  -> Serialization failed: {e}")
                traceback.print_exc()
                return
        else:
            print(f"Already serialized, skipping...")

        # Step 2: 方法级别编译
        # 检查是否已编译
        if is_compiled(project_name, ai_name, version):
            print(f"Already compiled, skipping...")
            return

        print(f"Compiling methods...")
        total_count, success_count = calc_method_compile_rate(project_name, ai_name, version)

        if total_count > 0:
            rate = success_count / total_count
            print(f"  -> Compile rate: {success_count}/{total_count} = {rate:.2%}")
        else:
            print(f"  -> No methods to compile")

    except Exception as e:
        print(f"Error processing project {project_name}: {e}")
        traceback.print_exc()


def process_version(version: str, ai_names: list[str], force_reserialize: bool = False, run_id: str = ""):
    """
    处理单个版本的所有项目

    Args:
        version: 版本号（v3, v4, v4_1, v4_7）
        ai_names: AI名称列表
        force_reserialize: 是否强制重新序列化
        run_id: 可选。v4_7+ 结构下指定 run id；为空时自动使用最新 run。
    """
    print(f"\n{'='*60}")
    print(f"Processing version: {version}")
    print(f"{'='*60}")

    for ai_name in ai_names:
        print(f"\n--- AI: {ai_name} ---")
        project_names = cfg_all_project_names(version)

        for project_name in project_names:
            try:
                # Step 1: 序列化
                eval_dir = cfg_eval_dir_path(ai_name, project_name, version)
                needs_serialize = force_reserialize or not eval_dir.exists() or not any(eval_dir.iterdir())

                if needs_serialize:
                    print(f"[{version}/{ai_name}/{project_name}] Serializing...")
                    try:
                        serialized = serialize_project_from_graph(ai_name, project_name, version, run_id=run_id)
                        if serialized:
                            save_serialized_files(ai_name, project_name, version, serialized)
                            print(f"  -> Serialized {len(serialized)} files")
                        else:
                            print(f"  -> No data to serialize")
                            continue
                    except FileNotFoundError as e:
                        print(f"  -> Skipped (no graph data): {e}")
                        continue
                    except Exception as e:
                        print(f"  -> Serialization failed: {e}")
                        traceback.print_exc()
                        continue
                else:
                    print(f"[{version}/{ai_name}/{project_name}] Already serialized, skipping...")

                # Step 2: 方法级别编译
                # 检查是否已编译
                if is_compiled(project_name, ai_name, version):
                    print(f"[{version}/{ai_name}/{project_name}] Already compiled, skipping...")
                    continue

                print(f"[{version}/{ai_name}/{project_name}] Compiling methods...")
                total_count, success_count = calc_method_compile_rate(project_name, ai_name, version)

                if total_count > 0:
                    rate = success_count / total_count
                    print(f"  -> Compile rate: {success_count}/{total_count} = {rate:.2%}")
                else:
                    print(f"  -> No methods to compile")

            except Exception as e:
                print(f"[{version}/{ai_name}/{project_name}] Error: {e}")
                traceback.print_exc()
                continue


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='Generate eval files and compile methods')
    parser.add_argument('--versions', nargs='+', default=['v3', 'v4', 'v4_1'],
                        help='Versions to process (v3, v4, v4_1, v4_7)')
    parser.add_argument('--ai-names', nargs='+', default=['deepseek', 'qwen', 'gpt'],
                        help='AI names to process')
    parser.add_argument('--run-id', default='',
                        help='Optional run id for v4_7+ structure; empty uses the latest run per project.')
    parser.add_argument('--force', action='store_true', help='Force reserialization')
    args = parser.parse_args()

    # 处理所有版本
    for version in args.versions:
        try:
            process_version(version, args.ai_names, force_reserialize=args.force, run_id=args.run_id)
        except Exception as e:
            print(f"Version {version} failed: {e}")
            traceback.print_exc()
            continue

    print("\n" + "="*60)
    print("All versions processed!")
    print("="*60)


if __name__ == "__main__":
    main()