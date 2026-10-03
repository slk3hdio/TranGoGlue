from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List
import re
import subprocess


@dataclass(frozen=True)
class ThirdPartyLibrary:
    """第三方 C++ 库的静态描述。

    职责:
        记录一个第三方库的名称、候选头文件列表以及在头文件中不可用时
        应遵循的回退指导文本。

    使用约定:
        对象为不可变 (frozen) 数据类，字段包括 name、headers、fallback_guidance。
    """
    name: str
    headers: tuple[str, ...]
    fallback_guidance: str


@dataclass
class ThirdPartyHeaderStatus:
    """某个第三方头文件的探测状态。

    职责:
        记录单个头文件在探测后的可用性、详情及回退指导。

    使用约定:
        library 为所属库名，header 为头文件名，available 表示是否可用，
        detail 存储额外说明，fallback_guidance 存储回退指导文本。
    """
    library: str
    header: str
    available: bool
    detail: str = ""
    fallback_guidance: str = ""


DEFAULT_THIRD_PARTY_LIBRARIES: tuple[ThirdPartyLibrary, ...] = (
    ThirdPartyLibrary(
        name="zlib",
        headers=("zlib.h", "zlib/zlib.h", "zconf.h"),
        fallback_guidance=(
            "Do not keep switching between zlib include paths. If zlib is unavailable, "
            "avoid depending on zlib-specific declarations in headers. Prefer a compile-safe "
            "project-local placeholder declaration, std::vector<uint8_t>-based buffers, or move "
            "compression details out of the header interface."
        ),
    ),
    ThirdPartyLibrary(
        name="GoogleTest",
        headers=("gtest/gtest.h", "gmock/gmock.h"),
        fallback_guidance=(
            "Do not switch between angle-bracket and quoted gtest includes. If GoogleTest is "
            "unavailable, do not include it and do not derive from ::testing::Test in generated "
            "headers; keep a plain compile-safe test helper class instead."
        ),
    ),
    ThirdPartyLibrary(
        name="OpenSSL",
        headers=("openssl/ssl.h", "openssl/err.h", "openssl/evp.h"),
        fallback_guidance=(
            "If OpenSSL is unavailable, do not include OpenSSL headers. Use opaque forward "
            "declarations only when unavoidable, or replace header-level APIs with standard-library "
            "types and project-local placeholders."
        ),
    ),
    ThirdPartyLibrary(
        name="libcurl",
        headers=("curl/curl.h",),
        fallback_guidance=(
            "If libcurl is unavailable, do not include curl headers. Avoid curl-specific symbols "
            "in generated headers and prefer a project-local abstraction or standard-library types."
        ),
    ),
    ThirdPartyLibrary(
        name="Boost",
        headers=("boost/asio.hpp", "boost/beast.hpp", "boost/algorithm/string.hpp"),
        fallback_guidance=(
            "If Boost is unavailable, do not introduce Boost headers or symbols. Prefer standard "
            "library containers, strings, smart pointers, and project-local helpers."
        ),
    ),
    ThirdPartyLibrary(
        name="nlohmann-json",
        headers=("nlohmann/json.hpp",),
        fallback_guidance=(
            "If nlohmann-json is unavailable, do not include it. Keep JSON values out of headers "
            "or use std::string/project-local placeholder types."
        ),
    ),
    ThirdPartyLibrary(
        name="fmt",
        headers=("fmt/format.h",),
        fallback_guidance=(
            "If fmt is unavailable, do not include it. Prefer std::string, std::ostringstream, or "
            "simple project-local formatting helpers."
        ),
    ),
    ThirdPartyLibrary(
        name="spdlog",
        headers=("spdlog/spdlog.h",),
        fallback_guidance=(
            "If spdlog is unavailable, do not include it. Avoid exposing logging library types in "
            "headers; use project-local or standard-library placeholders."
        ),
    ),
)


class ThirdPartyLibraryAvailability:
    """第三方 C++ 库可用性探测与查询工具。

    职责:
        通过编写临时 cpp 文件并用编译器探测各第三方头文件是否可用，
        维护头文件状态缓存，并对外提供查询、缺失识别与提示生成能力。

    使用约定:
        先用 probe() 触发探测，再通过 is_known_header / get_status /
        unavailable_headers / feedback_for_issue / prompt_context 等接口查询。
    """
    def __init__(self, libraries: Iterable[ThirdPartyLibrary] = DEFAULT_THIRD_PARTY_LIBRARIES):
        """初始化可用性探测器。

        参数:
            libraries: 待探测的第三方库集合，默认为内置的 DEFAULT_THIRD_PARTY_LIBRARIES。
        """
        self.libraries = list(libraries)
        self._status_by_header: dict[str, ThirdPartyHeaderStatus] = {}
        self._probed = False

    @property
    def probed(self) -> bool:
        """是否已执行过探测。

        返回:
            已探测返回 True，否则 False。
        """
        return self._probed

    def probe(self, output_dir: Path, compiler: str = "clang++") -> None:
        """探测所有已注册第三方库的头文件可用性。

        参数:
            output_dir: 用于写入探测临时文件的目录。
            compiler: 使用的编译器，默认为 clang++。
        """
        if self._probed:
            return

        output_dir.mkdir(parents=True, exist_ok=True)
        for library in self.libraries:
            for header in library.headers:
                self._status_by_header[header] = self._probe_header(output_dir, compiler, library, header)
        self._probed = True

    def _probe_header(
        self,
        output_dir: Path,
        compiler: str,
        library: ThirdPartyLibrary,
        header: str,
    ) -> ThirdPartyHeaderStatus:
        """探测单个指定头文件是否可用。

        参数:
            output_dir: 临时文件写入目录。
            compiler: 使用的编译器。
            library: 所属的第三方库对象。
            header: 待探测的头文件名。

        返回:
            记录该头文件探测结果的 ThirdPartyHeaderStatus。
        """
        safe_name = re.sub(r"[^A-Za-z0-9_]", "_", header)
        cpp_path = output_dir / f"_probe_{safe_name}.cpp"
        cpp_path.write_text(f"#include <{header}>\nint main() {{ return 0; }}\n", encoding="utf-8")

        try:
            proc = subprocess.run(
                [compiler, "-std=c++17", "-fsyntax-only", str(cpp_path)],
                capture_output=True,
                text=True, encoding='utf-8', errors='replace',
                timeout=30,
                cwd=str(output_dir),
            )
            available = proc.returncode == 0
            detail = "" if available else (proc.stderr or proc.stdout or "compile failed")
        except FileNotFoundError:
            available = False
            detail = f"Compiler {compiler!r} not found."
        except subprocess.TimeoutExpired:
            available = False
            detail = "Probe timed out."
        finally:
            try:
                cpp_path.unlink()
            except OSError:
                pass

        return ThirdPartyHeaderStatus(
            library=library.name,
            header=header,
            available=available,
            detail=detail.strip(),
            fallback_guidance=library.fallback_guidance,
        )

    def is_known_header(self, header: str) -> bool:
        """判断某个头文件是否为已注册的第三方头文件。

        参数:
            header: 头文件名。

        返回:
            已注册或已在探测状态表中存在时返回 True，否则 False。
        """
        return header in self._status_by_header or any(header in library.headers for library in self.libraries)

    def get_status(self, header: str) -> ThirdPartyHeaderStatus | None:
        """获取某个头文件的探测状态。

        参数:
            header: 头文件名。

        返回:
            对应的 ThirdPartyHeaderStatus，未探测到时返回 None。
        """
        return self._status_by_header.get(header)

    def unavailable_headers(self) -> List[ThirdPartyHeaderStatus]:
        """获取所有不可用头文件的探测状态。

        返回:
            探测状态中 available 为 False 的头文件状态列表。
        """
        return [status for status in self._status_by_header.values() if not status.available]

    def available_headers(self) -> List[ThirdPartyHeaderStatus]:
        """获取所有可用头文件的探测状态。

        返回:
            探测状态中 available 为 True 的头文件状态列表。
        """
        return [status for status in self._status_by_header.values() if status.available]

    def extract_missing_include(self, text: str) -> str:
        """从编译错误文本中提取缺失的 include 头文件名。

        参数:
            text: 编译错误或源码文本。

        返回:
            提取到的头文件名，未找到时返回空字符串。
        """
        match = re.search(r"fatal error:\s*'([^']+)'\s+file not found", text or "", re.IGNORECASE)
        if match:
            return match.group(1)
        match = re.search(r"#include\s*[<\"]([^>\"]+)[>\"]", text or "")
        if match:
            return match.group(1)
        return ""

    def feedback_for_issue(self, issue_type: str, detail: str) -> str:
        """针对缺失 include 类编译问题生成第三方库回退反馈。

        参数:
            issue_type: 编译问题类型。
            detail: 编译问题详情。

        返回:
            若涉及不可用的第三方头文件，返回提示文本；否则返回空字符串。
        """
        if issue_type != "missing_include":
            return ""

        header = self.extract_missing_include(detail)
        if not header:
            return ""

        status = self.get_status(header)
        if not status or status.available:
            return ""

        return (
            f"[third_party_unavailable] `{header}` ({status.library}) is unavailable. "
            f"Use standard-library types or implement it yourself."
        )

    def prompt_context(self) -> str:
        """生成第三方库可用性状态给 LLM 提示的上下文文本。

        返回:
            描述各库头文件可用性的文本；未探测时返回提示未探测的说明。
        """
        if not self._probed:
            return "Third-party C++ library availability has not been probed yet."

        lines = ["Third-party C++ library availability detected before this run:"]
        for library in self.libraries:
            header_states = []
            for header in library.headers:
                status = self.get_status(header)
                if status is None:
                    header_states.append(f"{header}=unknown")
                else:
                    header_states.append(f"{header}={'available' if status.available else 'unavailable'}")
            lines.append(f"- {library.name}: {', '.join(header_states)}")
        lines.append(
            "If a listed third-party header is unavailable, do not introduce it, do not switch "
            "between equivalent include spellings, and use standard-library or project-local "
            "compile-safe alternatives instead."
        )
        return "\n".join(lines)

    def print_summary(self) -> None:
        """打印第三方库可用性汇总信息到控制台。"""
        print("========== Third-party C++ library availability ==========")
        if not self._probed:
            print("  Not probed.")
            return
        for library in self.libraries:
            states = []
            for header in library.headers:
                status = self.get_status(header)
                if status is None:
                    states.append(f"{header}: unknown")
                else:
                    states.append(f"{header}: {'available' if status.available else 'unavailable'}")
            print(f"  {library.name}: {', '.join(states)}")
