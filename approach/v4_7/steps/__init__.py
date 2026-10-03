"""v4_7 steps 包初始化模块。

本模块在包首次被导入时执行环境的路径配置工作：将本包父目录（v4_7）以及
approach 根目录加入到 sys.path，从而使包内模块可以方便地引用
``graph``、``path_config`` 等上层模块。

同时对外暴露 ``version`` 常量，标识当前步骤包所属的版本号（v4_7）。
"""

import sys
from pathlib import Path

steps_package_dir = Path(__file__).parent.parent
apprach_dir_path = steps_package_dir.parent
if str(steps_package_dir) not in sys.path:
    sys.path.append(str(steps_package_dir))
if str(apprach_dir_path) not in sys.path:
    sys.path.append(str(apprach_dir_path))

version = 'v4_7'
