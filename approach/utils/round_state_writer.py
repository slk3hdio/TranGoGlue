from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any, Dict, List

from graph import FileGenerator, Header


def serialize_header_output_state(header: Header) -> str:
    """
    将单个头文件的输出状态序列化为 JSON 字符串。

    职责：
        - 汇总头文件的翻译代码 (translated_code) 及其外部头文件映射，
          供持久化或比较使用。

    参数:
        header: 待序列化的 Header 对象

    返回:
        str: 排序键后的 JSON 字符串，用于保证不同调用产生一致的输出
    """
    payload = {
        "translated_code": header.translated_code,
        "external_header_files": {
            file_name: header.external_header_files[file_name]
            for file_name in sorted(header.external_header_files.keys())
        },
    }
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)


def write_round_state(
    result_dir: Path,
    round_idx: int,
    changed_headers: List[Header],
    changed_schemes: Dict[str, str] | None = None,
    compile_outputs: Dict[str, str] | None = None,
    scheme_groups: List[Dict[str, Any]] | None = None,
) -> Path:
    """
    将某一轮迭代的状态写入磁盘目录。

    职责：
        - 在 result_dir 下创建 header_rounds/round_XX 目录（若存在则先清空）。
        - 生成改变的头文件产物（经由 FileGenerator）。
        - 落盘改写后的 scheme、编译输出与 scheme 分组文件。
        - 写入 manifest.json 汇总本轮各类文件的数量与名称。

    参数:
        result_dir: 结果的根目录，轮次目录将创建于其下
        round_idx: 当前轮次索引（会格式化为两位数）
        changed_headers: 本轮发生改变的头文件列表
        changed_schemes: 头文件名到改写后 scheme 文本的映射
        compile_outputs: 头文件名到编译输出文本的映射
        scheme_groups: 可选的 scheme 分组列表

    返回:
        Path: 本轮状态目录的路径
    """
    round_dir = result_dir / "header_rounds" / f"round_{round_idx:02d}"

    round_dir.mkdir(parents=True, exist_ok=True)
    for child in round_dir.iterdir():
        if child.is_dir():
            shutil.rmtree(child)
        else:
            child.unlink()

    if changed_headers:
        FileGenerator().generate_header_artifacts(changed_headers, str(round_dir))

    normalized_schemes = {
        header_name: _normalize_scheme_text(scheme_text)
        for header_name, scheme_text in (changed_schemes or {}).items()
        if scheme_text.strip()
    }
    for header_name, scheme_text in normalized_schemes.items():
        (round_dir / f"{header_name}.scheme.json").write_text(
            scheme_text,
            encoding="utf-8",
        )

    normalized_compile_outputs = {
        header_name: compile_output.strip()
        for header_name, compile_output in (compile_outputs or {}).items()
        if compile_output.strip()
    }
    for header_name, compile_output in normalized_compile_outputs.items():
        (round_dir / f"{header_name}.compile.txt").write_text(
            compile_output,
            encoding="utf-8",
        )

    normalized_scheme_groups = scheme_groups or []
    if normalized_scheme_groups:
        (round_dir / "scheme_groups.json").write_text(
            json.dumps(normalized_scheme_groups, ensure_ascii=False, indent=4),
            encoding="utf-8",
        )

    manifest = {
        "round": round_idx,
        "changed_headers": sorted(header.key for header in changed_headers),
        "changed_schemes": sorted(normalized_schemes.keys()),
        "compile_output_headers": sorted(normalized_compile_outputs.keys()),
        "scheme_group_count": len(normalized_scheme_groups),
        "header_count": len(changed_headers),
        "scheme_count": len(normalized_schemes),
        "compile_output_count": len(normalized_compile_outputs),
    }
    (round_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=4),
        encoding="utf-8",
    )
    return round_dir


def _normalize_scheme_text(scheme_text: str) -> str:
    """
    规范化 scheme 文本：若可解析为 JSON 则重新格式化，否则原样返回。

    参数:
        scheme_text: 原始的 scheme 文本

    返回:
        str: 规范化后的 scheme 文本
    """
    text = scheme_text.strip()
    if not text:
        return ""

    try:
        return json.dumps(json.loads(text), ensure_ascii=False, indent=4)
    except json.JSONDecodeError:
        return text
