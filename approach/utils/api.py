"""从外部配置加载 LLM 提供商信息，避免在源码中保存凭据。"""

import json
import os
from pathlib import Path
from typing import Any


def _validate_model_config(name: str, config: Any) -> dict[str, str]:
    """校验单个模型配置。

    参数：
        name: 命令行使用的模型键。
        config: 从 JSON 配置读取的原始值。

    返回：
        dict[str, str]: 包含 api_key、base_url 和 model_name 的模型配置。

    异常：
        ValueError: 配置不是对象、缺少字段或字段值为空时抛出。
    """
    if not isinstance(config, dict):
        raise ValueError(f"模型 {name!r} 的配置必须是 JSON 对象")

    required_fields = ("api_key", "base_url", "model_name")
    missing = [field for field in required_fields if not config.get(field)]
    if missing:
        fields = ", ".join(missing)
        raise ValueError(f"模型 {name!r} 缺少必填配置：{fields}")

    return {field: str(config[field]) for field in required_fields}


def load_llm_api_config() -> dict[str, dict[str, str]]:
    """从环境变量指定的 JSON 内容或文件加载全部模型配置。

    优先读取 ``SITP_LLM_CONFIG_JSON``；未设置时读取
    ``SITP_LLM_CONFIG_FILE`` 指向的文件。两者均未设置时返回空字典，
    使帮助命令和不需要 LLM 的工具仍可正常导入模块。

    返回：
        dict[str, dict[str, str]]: 以模型键索引的已校验配置。

    异常：
        ValueError: JSON 顶层不是对象或模型配置不完整时抛出。
        OSError: 配置文件无法读取时抛出。
        json.JSONDecodeError: 配置不是合法 JSON 时抛出。
    """
    inline_config = os.environ.get("SITP_LLM_CONFIG_JSON", "").strip()
    config_file = os.environ.get("SITP_LLM_CONFIG_FILE", "").strip()

    if inline_config:
        raw_config = json.loads(inline_config)
    elif config_file:
        config_path = Path(config_file).expanduser().resolve()
        raw_config = json.loads(config_path.read_text(encoding="utf-8"))
    else:
        return {}

    if not isinstance(raw_config, dict):
        raise ValueError("LLM 配置的 JSON 顶层必须是对象")

    return {
        str(name): _validate_model_config(str(name), config)
        for name, config in raw_config.items()
    }


llm_api = load_llm_api_config()
