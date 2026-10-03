import json
import re
import sys
from typing import List, Dict, Any, Optional
from openai.types.chat.chat_completion_message_param import ChatCompletionMessageParam
from pathlib import Path

pp_dir = str(Path(__file__).parent.parent)
if pp_dir not in sys.path:
    sys.path.append(str(pp_dir))
approach_dir = str(Path(__file__).resolve().parents[2])
if approach_dir not in sys.path:
    sys.path.insert(0, approach_dir)

from utils.Generator import Generator
from path_config import cfg_review_prompt_file_path
from v4_7.steps import version

from .tools import get_all_tools


class CppCompilationAgent:
    """
    C++ Compilation and Code Repair Agent

    This agent handles multiple C++ source files and header files,
    compiling them sequentially and automatically fixing compilation errors.
    """

    def __init__(
        self,
        ai_name: str,
        project_name: str,
        file_path: Path,
        work_dir: Path | None = None,
        initial_error_log: str = "",
        history_path: Path | None = None,
        compile_timeout: int = 60,
        link_mode: bool = True,
        trace_path: Path | None = None,
        test_suites: tuple[str, ...] = ("base",),
        readonly_files: set[str] | None = None,
    ):
        """初始化 C++ 编译与代码修复 Agent。

        负责接收待编译的源文件路径、配置 LLM 生成器、加载评审提示词，
        并注册编译/读写/编辑等一系列工具，构建初始对话历史。

        Args:
            ai_name: AI 模型名称，用于创建对应的 LLM 生成器。
            project_name: 项目名称，用于定位相关配置与工具。
            file_path: 待编译的 C++ 源文件或头文件路径。
            work_dir: 工作目录，缺省时取 file_path 的父目录。
            initial_error_log: 初始编译错误日志，将注入到用户消息中指导修复。
            history_path: 对话历史保存路径，用于 save_history。
            compile_timeout: 单次编译超时时间（秒）。
            link_mode: 是否以链接模式编译整个工程。
            trace_path: LLM token 追踪 JSONL 的写入路径；为空时不额外追踪。
            test_suites: 链接成功后按顺序执行的功能测试套件。

        Raises:
            FileNotFoundError: 当 file_path 不存在时抛出。
        """
        self.ai_name = ai_name
        self.llm = Generator(ai_name)
        if trace_path is not None:
            self.llm.configure_trace(str(trace_path), "agent_repair")
        self.file_path = file_path  # <--- [新增] 保存 file_path
        self.work_dir = Path(work_dir) if work_dir is not None else file_path.parent
        self.history_path = history_path

        with open(cfg_review_prompt_file_path(version), "r", encoding="utf-8") as p:
            self.prompt = p.read()

        tools = get_all_tools(
            ai_name,
            project_name,
            work_dir=self.work_dir,
            compile_timeout=compile_timeout,
            link_mode=link_mode,
            test_suites=test_suites,
            readonly_files=readonly_files,
        )
        self.tools ={
            "compile_file":tools["compile_file"],
            "read_file":tools["read_file"],
            "write_file":tools["write_file"],
            "create_file":tools["create_file"],
            "edit_file":tools["edit_file"],
        }
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        initial_content = f"the file need to be compiles: {file_path.name}"
        if initial_error_log:
            initial_content += f"\n\nCurrent compilation errors:\n{initial_error_log}"

        self.history_messages: list[ChatCompletionMessageParam] = [
            {"role":"system", "content":self.prompt},
            {"role":"user", "content":initial_content}
        ]

    def save_history(self, file_path: Optional[Path]=None):
        """将对话历史以 UTF-8 JSON 格式保存到指定路径。

        Args:
            file_path: 保存目标路径；缺省时使用 self.history_path，
                       若仍为空则默认保存为 "history.json"。
        """
        if not file_path:
            file_path = self.history_path or Path("history.json")

        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as h:
            json.dump(self.history_messages, h, indent=4)


    def parse_response(self, response: str) -> Dict[str, Any]:
        """
        Parse the LLM response to extract tool calls and status information.
        Supports extracting JSON from ```json``` code blocks.

        Args:
            response: Raw response string from LLM

        Returns:
            Dictionary containing parsed response data
        """
        # Try to extract JSON from code blocks first
        json_content = self._extract_json_from_response(response)

        if json_content:
            try:
                parsed = json.loads(json_content)
                return self._validate_and_normalize_response(parsed)
            except json.JSONDecodeError:
                pass

        # If no valid JSON found in code blocks, try parsing the whole response
        try:
            parsed = json.loads(response)
            return self._validate_and_normalize_response(parsed)
        except json.JSONDecodeError:
            # If not JSON, create a basic response structure
            return {
                "current-file": "unknown",
                "success": False,
                "error-log": "something went wrong, please continue from the last valid information.",
                "note": "",
                "current-action": "waiting for valid response",
                "tool-calls": []
            }

    def _extract_json_from_response(self, response: str) -> str:
        """
        Extract JSON content from ```json``` code blocks in the response.

        Args:
            response: Raw response string

        Returns:
            Extracted JSON string or empty string if no JSON found
        """
        # Pattern to match ```json ... ``` blocks
        pattern = r'```json\s*(.*?)\s*```'
        matches = re.findall(pattern, response, re.DOTALL)

        if matches:
            # Return the first JSON block found
            return matches[0].strip()

        # Also try without the 'json' specifier
        pattern_generic = r'```\s*(.*?)\s*```'
        matches_generic = re.findall(pattern_generic, response, re.DOTALL)

        if matches_generic:
            # Check if the content looks like JSON
            content = matches_generic[0].strip()
            if content.startswith('{') and content.endswith('}'):
                return content

        return ""

    def _validate_and_normalize_response(self, parsed: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate and normalize the parsed response.

        Args:
            parsed: Parsed JSON response

        Returns:
            Normalized response dictionary
        """
        # Validate required fields
        required_fields = ["current-file", "success", "current-action"]
        for field in required_fields:
            if field not in parsed:
                parsed[field] = "unknown" if field == "current-file" else False

        # Ensure tool-calls is a list
        if "tool-calls" not in parsed:
            parsed["tool-calls"] = []
        elif not isinstance(parsed["tool-calls"], list):
            parsed["tool-calls"] = [parsed["tool-calls"]]

        # Normalize field names to match expected format
        field_mappings = {
            "current_file": "current-file",
            "currentFile": "current-file",
            "tool_calls": "tool-calls",
            "toolCalls": "tool-calls",
            "error_log": "error-log",
            "errorLog": "error-log",
            "current_action": "current-action",
            "currentAction": "current-action"
        }

        for old_name, new_name in field_mappings.items():
            if old_name in parsed and new_name not in parsed:
                parsed[new_name] = parsed.pop(old_name)

        return parsed
    
    def handle_tool_calls(self, tool_calls: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """依次执行 LLM 请求中解析出的工具调用并收集结果。

        根据工具名称分发到对应的已注册工具（编译、读写、创建、编辑文件），
        未知工具或执行异常会被捕获并转换为失败结果，而不会中断整体流程。

        Args:
            tool_calls: 工具调用列表，每项包含 "tool"（工具名）与
                        "args"（参数字典）字段。

        Returns:
            list[dict]: 每个工具调用的执行结果列表，每项包含 tool、
                        success 与 result 字段。
        """
        tool_results:List[Dict[str, Any]] = []
        for tool_call in tool_calls:
            tool_name = tool_call.get("tool")
            tool_args = tool_call.get("args", {})

            if tool_name not in self.tools:
                error_msg = f"Unknown tool: {tool_name}"
                print(f"Error: {error_msg}")
                tool_results.append({
                    "tool": tool_name,
                    "success": False,
                    "result": error_msg
                })
                continue

            try:
                # Call the tool with appropriate arguments
                tool_func = self.tools[tool_name]

                # Handle different tool parameter requirements
                if tool_name == "compile_file":
                    result = tool_func(tool_args.get("file", ""))
                elif tool_name == "read_file":
                    result = tool_func(tool_args.get("file", ""))
                elif tool_name == "write_file":
                    result = tool_func(
                        tool_args.get("file", ""),
                        tool_args.get("content", "")
                    )
                elif tool_name == "create_file":
                    result = tool_func(
                        tool_args.get("file", ""),
                        tool_args.get("content", "")
                    )
                elif tool_name == "edit_file":
                    result = tool_func(
                        tool_args.get("file", ""),
                        tool_args.get("old_str", ""),
                        tool_args.get("new_str", "")
                    )
                else:
                    result = {"success": False, "error": f"Unknown tool: {tool_name}"}

                tool_results.append({
                    "tool": tool_name,
                    "success": result.get("success", False),
                    "result": result
                })

                print(f"Tool {tool_name} executed successfully")

            except Exception as e:
                error_msg = f"Tool execution failed: {e}"
                print(f"Error: {error_msg}")
                tool_results.append({
                    "tool": tool_name,
                    "success": False,
                    "result": {"error": error_msg}
                })

        return tool_results



    # 历史压缩预算：约 24 万字符，保守低于 131072 token 的模型上下文上限。
    _HISTORY_CHAR_BUDGET = 240_000
    # 截断时保留完整的最近消息数（assistant/user 交替）。
    _HISTORY_KEEP_RECENT = 6
    # 早期工具结果摘要中保留的结果尾部字符数。
    _HISTORY_STUB_CHARS = 300

    def _truncate_history_if_needed(self) -> None:
        """超出字符预算时，把早期交互消息替换为简短摘要。

        保留 system 提示词、初始用户消息和最近若干轮完整内容；
        中间的工具结果消息只保留每个工具的名称、成功与否及结果尾部，
        模型响应消息只保留开头片段。就地修改 history_messages。

        返回:
            None。
        """
        def total_chars() -> int:
            """统计当前历史消息的总字符数。"""
            return sum(len(str(msg.get("content") or "")) for msg in self.history_messages)

        if total_chars() <= self._HISTORY_CHAR_BUDGET:
            return

        # 预算仍超标时逐步缩小保留窗口，直到只剩 system 与初始用户消息。
        keep_recent = self._HISTORY_KEEP_RECENT
        while keep_recent >= 0 and total_chars() > self._HISTORY_CHAR_BUDGET:
            keep_from = max(2, len(self.history_messages) - keep_recent)
            for index in range(2, keep_from):
                message = self.history_messages[index]
                content = str(message.get("content") or "")
                if len(content) <= self._HISTORY_STUB_CHARS:
                    continue
                message["content"] = self._summarize_old_message(message, content)
            keep_recent -= 2

    def _summarize_old_message(self, message: Dict[str, Any], content: str) -> str:
        """把一条早期历史消息压缩为简短摘要。

        参数:
            message: 原始历史消息（含 role）。
            content: 消息文本内容。

        返回:
            压缩后的消息文本；工具结果消息保留每个工具的名称、
            成功标记与结果尾部，其余消息保留开头片段。
        """
        if message.get("role") != "user":
            return content[: self._HISTORY_STUB_CHARS] + "\n...[truncated early interaction]"
        try:
            data = json.loads(content)
        except (json.JSONDecodeError, TypeError):
            return content[: self._HISTORY_STUB_CHARS] + "\n...[truncated early interaction]"
        tool_results = data.get("tool_results")
        if not isinstance(tool_results, list):
            return content[: self._HISTORY_STUB_CHARS] + "\n...[truncated early interaction]"
        parts = []
        for result in tool_results:
            result_text = json.dumps(result.get("result", ""), ensure_ascii=False)
            parts.append({
                "tool": result.get("tool", "unknown"),
                "success": result.get("success", False),
                "result_tail": result_text[-self._HISTORY_STUB_CHARS:],
            })
        return json.dumps(
            {
                "truncated_early_tool_results": parts,
                "summary": data.get("summary", ""),
            },
            ensure_ascii=False,
        )

    def run(self, max_attempts: int = 50, max_tool_calls: int | None = None, tool_call_counter: Dict[str, int] | None = None) -> Dict[str, Any]:
        """运行修复循环，并严格限制项目级 LLM 工具调用总数。

        Args:
            max_attempts: 最大编译尝试次数。
            max_tool_calls: 项目级 LLM 工具调用上限；为 None 时不限制。
            tool_call_counter: 多个修复 Agent 之间共享的计数器；未提供时创建局部计数器。

        Returns:
            dict: 最终状态、编译尝试次数和累计工具调用数。
        """
        if max_tool_calls is not None and max_tool_calls < 0:
            raise ValueError("max_tool_calls must be non-negative")
        if tool_call_counter is None:
            tool_call_counter = {"count": 0}

        # 将 max_attempts 理解为最大编译尝试次数
        max_compile_attempts = max_attempts
        print(f"Starting C++ Compilation Agent with {max_compile_attempts} max compilation attempts")

        compile_attempts = 0
        interaction_count = 0
        consecutive_no_tool_responses = 0
        last_compile_succeeded = False

        # --- 强制首轮编译：先拿到真实编译/链接错误再让 LLM 介入 ---
        print(f"Running initial compilation for {self.file_path}...")
        initial_result = self.tools["compile_file"](str(self.file_path))

        if initial_result.get("success"):
            self.save_history()
            return {
                "status": "success",
                "message": "Initial compilation completed successfully without AI intervention.",
                "attempts": 1
            }

        # 初始编译失败，将错误信息加入历史记录，并增加计数
        compile_attempts += 1
        self.history_messages.append({
            "role": "user",
            "content": json.dumps({
                "tool_results": [{
                    "tool": "compile_file",
                    "success": False,
                    "result": initial_result
                }],
                "summary": "Initial compilation failed. Please fix the errors based on the result."
            })
        })
        # ---------------------------

        # 不限制对话轮数；终止仅由编译尝试、工具调用预算和连续无进展控制。
        while compile_attempts < max_compile_attempts:
            # 在请求 LLM 前检查预算，避免达到上限后再产生一次无效模型调用。
            if max_tool_calls is not None and tool_call_counter["count"] >= max_tool_calls:
                self.save_history()
                return {
                    "status": "max_tool_calls_reached",
                    "attempts": compile_attempts,
                    "tool_calls": tool_call_counter["count"],
                }
            interaction_count += 1
            print(f"\n--- Interaction {interaction_count} | Compilation Attempts: {compile_attempts}/{max_compile_attempts} ---")

            # 对话历史随工具结果无界增长，超出字符预算时截断早期操作，
            # 避免请求超出模型上下文上限（如 deepseek 的 131072 token）。
            self._truncate_history_if_needed()

            # Get response from LLM
            try:
                response = self.llm.generate(self.history_messages)[0]
                print(f"LLM Response: {response}...")
                self.history_messages.append({
                    "role": "assistant",
                    "content": response
                })
            except Exception as e:
                print(f"Error getting LLM response: {e}")
                self.save_history()
                return {
                    "status": "error",
                    "error": f"LLM communication failed: {e}",
                    "attempts": compile_attempts
                }

            # Parse the response
            parsed_response = self.parse_response(response)

            if parsed_response.get("success") and last_compile_succeeded:
                self.save_history()
                return {
                    "status": "success",
                    "message": "Compilation completed successfully",
                    "attempts": compile_attempts
                }
            if parsed_response.get("success") and not last_compile_succeeded:
                # 模型不能在最近一次编译失败或尚未编译时自行宣布完成。
                parsed_response["success"] = False
                self.history_messages.append({
                    "role": "user",
                    "content": json.dumps({
                        "tool_results": [],
                        "summary": (
                            "Success cannot be accepted because the latest compile/link/test "
                            "validation did not pass. Continue repairing and call compile_file again."
                        ),
                    }),
                })

            tool_calls = parsed_response.get("tool-calls", [])
            if max_tool_calls is not None:
                remaining = max_tool_calls - tool_call_counter.get("count", 0)
                if remaining <= 0:
                    self.save_history()
                    return {
                        "status": "max_tool_calls_reached",
                        "attempts": compile_attempts,
                        "tool_calls": tool_call_counter["count"],
                    }
                tool_calls = tool_calls[:remaining]

            if not tool_calls:
                consecutive_no_tool_responses += 1
                if consecutive_no_tool_responses >= 3:
                    self.save_history()
                    return {
                        "status": "no_progress",
                        "message": "LLM returned no tool calls for three consecutive failed responses",
                        "attempts": compile_attempts,
                        "tool_calls": tool_call_counter["count"],
                    }
                self.history_messages.append({
                    "role": "user",
                    "content": json.dumps({
                        "tool_results": [],
                        "summary": (
                            "No tool call was provided, so no progress was made. "
                            "Inspect or edit a file, or compile the target; do not only announce that you are stopping."
                        ),
                    }),
                })
                continue
            consecutive_no_tool_responses = 0
            
            # 检查本次交互是否包含编译操作
            is_compiling = False
            for tool_call in tool_calls:
                if tool_call.get("tool") == "compile_file":
                    is_compiling = True
                    break
            
            # 如果包含了编译操作，则增加编译计数
            if is_compiling:
                compile_attempts += 1

            tool_results = self.handle_tool_calls(tool_calls)
            compile_results = [
                result for result in tool_results if result.get("tool") == "compile_file"
            ]
            if compile_results:
                last_compile_succeeded = all(
                    bool(result.get("success")) for result in compile_results
                )
            tool_call_counter["count"] = tool_call_counter.get("count", 0) + len(tool_calls)
            print(json.dumps(tool_results, indent=4))

            # Add tool results to history
            self.history_messages.append({
                "role": "user",
                "content": json.dumps({
                    "tool_results": tool_results,
                    "summary": f"Completed {len(tool_results)} tool calls"
                })
            })

            # 本轮恰好用尽预算时立即结束，不再进入下一轮 LLM 交互。
            if max_tool_calls is not None and tool_call_counter["count"] >= max_tool_calls:
                self.save_history()
                return {
                    "status": "max_tool_calls_reached",
                    "attempts": compile_attempts,
                    "tool_calls": tool_call_counter["count"],
                }

        # 循环自然结束只可能是编译尝试次数达到上限。
        self.save_history()
        return {
            "status": "max_compile_attempts_reached",
            "message": f"Reached maximum compilation attempts ({max_compile_attempts}) without completion",
            "attempts": compile_attempts
        }



    
    


# if __name__ == "__main__":
#     main("deepseek", "Cookie")



