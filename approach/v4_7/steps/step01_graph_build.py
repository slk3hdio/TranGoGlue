import os
import shutil

from graph import Project, retrieve_project
from path_config import (
    cfg_all_project_names,
    cfg_cpp_stub_dirs,
    cfg_gradlew_file_path,
    cfg_graph_dir_path,
    cfg_method_call_file_path,
    cfg_parser_tool_path,
    cfg_source_code_dir_path,
    cfg_split_output_dir_path,
    cfg_run_graph_dir,
)

from . import version
from .manual_stub_loader import inject_manual_stubs


class GraphBuildStep:
    """Build split files and graph artifacts for v4_7."""

    def __init__(self):
        """构造函数。

        本步骤无需任何初始化状态，因此不执行额外配置。
        """
        pass

    def generate_split(self, project_name: str, version: str) -> None:
        """调用解析工具生成指定项目的 split 文件。

        :param project_name: 目标项目名称。
        :param version: 版本标识，用于定位输出目录。
        """
        command = (
            f"cd {cfg_parser_tool_path()} && {cfg_gradlew_file_path()} run --args="
            f"\"{cfg_source_code_dir_path(project_name)} {cfg_split_output_dir_path(project_name, version)}\""
        )
        print(command)
        os.system(command)

    def build_graph(self, ai_name: str, project_name: str, force_rebuild: bool = False, run_id: str = "") -> Project:
        """构建（或加载）指定项目的图产物并返回 Project 对象。

        若 split 文件不存在、目录为空或要求强制重建，则先调用
        generate_split 生成 split 文件；随后依据 graph 目录是否存在或
        是否需要强制重建来决定是重新从检索数据构造图并保存，还是直接
        从已有目录加载。

        :param ai_name: AI 名称，用于定位 graph 目录。
        :param project_name: 目标项目名称。
        :param force_rebuild: 是否强制重新生成 split 与图产物。
        :param run_id: 运行 ID；非空时图产物写入 run 对应的目录。
        :return: 构建或加载得到的 Project 对象。
        """
        split_dir = cfg_split_output_dir_path(project_name, version)
        if not split_dir.exists() or not list(split_dir.iterdir()) or force_rebuild:
            self.generate_split(project_name, version)
        else:
            print(f"Split files already exist in {split_dir}, skip split.")

        graph_dir = cfg_graph_dir_path(ai_name, project_name, version) if not run_id else cfg_run_graph_dir(ai_name, project_name, version, run_id)
        if not graph_dir.exists() or force_rebuild:
            if graph_dir.exists():
                shutil.rmtree(graph_dir)
            data = retrieve_project(ai_name, project_name, version)
            project = Project(project_name, data["method_nodes"], data["headers"])
            Project.save(project, graph_dir)
            print(f"graph files in {graph_dir} generated.")
        else:
            project = Project.load(graph_dir)

        # 注入手写 C++ 桩（manual_stub）：在 load 之后执行，旧缓存图无需重建即可
        # 获得桩节点与调用边；注入幂等，随后重新持久化。
        stub_count = inject_manual_stubs(
            project, cfg_cpp_stub_dirs(project_name), cfg_method_call_file_path(project_name)
        )
        if stub_count:
            Project.save(project, graph_dir)
            print(f"[manual_stub] 注入 {stub_count} 个手写桩节点。")

        return project


if __name__ == "__main__":
    graph_build_step = GraphBuildStep()
    for project_name in cfg_all_project_names(version):
        graph_build_step.generate_split(project_name, version)
