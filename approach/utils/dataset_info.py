from pathlib import Path
import sys

# 添加父目录到路径以便导入模块
parent_dir = str(Path(__file__).parent.parent)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)
from path_config import cfg_statistics_dir_path, cfg_split_output_dir_path, cfg_all_project_names
import pandas as pd
import json

def get_dataset_info():
    """
    获取数据集信息
    """
    df = pd.read_csv(cfg_statistics_dir_path()/"dataset.csv")
    df.set_index("Main Class", drop=False, inplace=True)
    for project_name in df.index:
        if project_name not in cfg_all_project_names:
            continue
        split_dir_path = cfg_split_output_dir_path("", project_name)

        java_file_count = 0
        method_count = 0

        for split_file in split_dir_path.iterdir():
            if split_file.is_file() and split_file.suffix == ".json":
                java_file_count += 1
                
                with open(split_file, "r", encoding="utf-8") as f:
                    file_data = f.read()
                    method_count += int(json.loads(file_data)["methodCount"])

        df.loc[project_name, "Java Files"] = java_file_count
        df.loc[project_name, "Methods"] = method_count
        print(f"Project {project_name}: {java_file_count} Java files, {method_count} methods")

    df.to_csv(cfg_statistics_dir_path()/"dataset.csv", index=False)
    print(f"total_files: {df['Java Files'].sum()}")
    print(f"total_methods: {df['Methods'].sum()}")

if __name__ == "__main__":
    get_dataset_info()

        
                
        
    