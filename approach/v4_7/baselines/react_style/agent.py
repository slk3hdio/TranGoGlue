from __future__ import annotations

"""Single-file ReAct-style translation agent (Java class -> C++ .h + .cpp)."""

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from utils.Generator import Generator
from v4_7.agent.tools import get_all_tools

from .prompt import REACT_SYSTEM_PROMPT, build_initial_translation_message


class ReactStyleFileAgent:
    """ReAct loop for one Java file: translate, compile, observe, fix, repeat.

    Uses the same tool protocol (JSON tool-calls) as the SITP repair agent,
    but the session starts from the Java source instead of a failing C++ file.
    """

    def __init__(
        self,
        ai_name: str,
        project_name: str,
        header,
        generator: Generator,
        work_dir: Path,
        target_header_name: str,
        target_cpp_name: str,
        max_compile_attempts: int = 10,
        compile_timeout: int = 60,
        history_dir: Optional[Path] = None,
    ) -> None:
        self.ai_name = ai_name
        self.header = header
        self.generator = generator
        self.work_dir = Path(work_dir)
        self.target_header_name = target_header_name
        self.target_cpp_name = target_cpp_name
        self.max_compile_attempts = max(1, max_compile_attempts)
        self.history_path = (
            Path(history_dir) / f"{Path(target_cpp_name).stem}.json"
            if history_dir is not None
            else None
        )

        tools = get_all_tools(ai_name, project_name, work_dir=self.work_dir, compile_timeout=compile_timeout)
        self.tools = {
            "compile_file": tools["compile_file"],
            "read_file": tools["read_file"],
            "write_file": tools["write_file"],
            "create_file": tools["create_file"],
            "edit_file": tools["edit_file"],
        }

        initial_message = build_initial_translation_message(
            header, target_header_name, target_cpp_name
        )
        self.history_messages: List[Dict[str, Any]] = [
            {"role": "system", "content": REACT_SYSTEM_PROMPT},
            {"role": "user", "content": initial_message},
        ]

    def save_history(self) -> None:
        if self.history_path is None:
            return
        self.history_path.parent.mkdir(parents=True, exist_ok=True)
        self.history_path.write_text(
            json.dumps(self.history_messages, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    # -- response parsing (same protocol as the SITP repair agent) ---------

    def parse_response(self, response: str) -> Dict[str, Any]:
        json_content = self._extract_json_from_response(response)
        if json_content:
            try:
                parsed = json.loads(json_content)
                return self._validate_and_normalize_response(parsed)
            except json.JSONDecodeError:
                pass
        try:
            parsed = json.loads(response)
            return self._validate_and_normalize_response(parsed)
        except json.JSONDecodeError:
            return {
                "current-file": self.target_cpp_name,
                "success": False,
                "error-log": "something went wrong, please continue from the last valid information.",
                "note": "",
                "current-action": "waiting for valid response",
                "tool-calls": [],
            }

    def _extract_json_from_response(self, response: str) -> str:
        pattern = r"```json\s*(.*?)\s*```"
        matches = re.findall(pattern, response, re.DOTALL)
        if matches:
            return matches[0].strip()
        pattern_generic = r"```\s*(.*?)\s*```"
        matches_generic = re.findall(pattern_generic, response, re.DOTALL)
        if matches_generic:
            content = matches_generic[0].strip()
            if content.startswith("{") and content.endswith("}"):
                return content
        return ""

    def _validate_and_normalize_response(self, parsed: Dict[str, Any]) -> Dict[str, Any]:
        required_fields = ["current-file", "success", "current-action"]
        for field in required_fields:
            if field not in parsed:
                parsed[field] = "unknown" if field == "current-file" else False
        if "tool-calls" not in parsed:
            parsed["tool-calls"] = []
        elif not isinstance(parsed["tool-calls"], list):
            parsed["tool-calls"] = [parsed["tool-calls"]]
        field_mappings = {
            "current_file": "current-file",
            "currentFile": "current-file",
            "tool_calls": "tool-calls",
            "toolCalls": "tool-calls",
            "error_log": "error-log",
            "errorLog": "error-log",
            "current_action": "current-action",
            "currentAction": "current-action",
        }
        for old_name, new_name in field_mappings.items():
            if old_name in parsed and new_name not in parsed:
                parsed[new_name] = parsed.pop(old_name)
        return parsed

    # -- tool execution -----------------------------------------------------

    def handle_tool_calls(self, tool_calls: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        tool_results: List[Dict[str, Any]] = []
        for tool_call in tool_calls:
            tool_name = tool_call.get("tool")
            tool_args = tool_call.get("args", {})
            if tool_name not in self.tools:
                tool_results.append({
                    "tool": tool_name,
                    "success": False,
                    "result": f"Unknown tool: {tool_name}",
                })
                continue
            try:
                tool_func = self.tools[tool_name]
                if tool_name == "compile_file":
                    result = tool_func(tool_args.get("file", ""))
                elif tool_name == "read_file":
                    result = tool_func(tool_args.get("file", ""))
                elif tool_name in {"write_file", "create_file"}:
                    result = tool_func(
                        tool_args.get("file", ""),
                        tool_args.get("content", ""),
                    )
                elif tool_name == "edit_file":
                    result = tool_func(
                        tool_args.get("file", ""),
                        tool_args.get("old_str", ""),
                        tool_args.get("new_str", ""),
                    )
                else:
                    result = {"success": False, "error": f"Unknown tool: {tool_name}"}
                tool_results.append({
                    "tool": tool_name,
                    "success": result.get("success", False),
                    "result": result,
                })
            except Exception as exc:
                tool_results.append({
                    "tool": tool_name,
                    "success": False,
                    "result": {"error": f"Tool execution failed: {exc}"},
                })
        return tool_results

    # -- main loop ----------------------------------------------------------

    def run(self) -> Dict[str, Any]:
        """Run the ReAct loop until the target .cpp compiles or budget runs out.

        Returns dict: status, message, attempts (compile attempts), interactions.
        The `success` status is only returned after an actual successful compile.
        """
        compile_attempts = 0
        max_interactions = self.max_compile_attempts * 10
        interaction_count = 0

        while compile_attempts < self.max_compile_attempts and interaction_count < max_interactions:
            interaction_count += 1
            print(
                f"\n--- {self.target_cpp_name} | interaction {interaction_count} | "
                f"compiles {compile_attempts}/{self.max_compile_attempts} ---"
            )
            try:
                response = self.generator.generate(self.history_messages)[0]
            except Exception as exc:
                print(f"LLM call failed: {exc}")
                self.save_history()
                return {
                    "status": "error",
                    "error": f"LLM communication failed: {exc}",
                    "attempts": compile_attempts,
                    "interactions": interaction_count,
                }
            self.history_messages.append({"role": "assistant", "content": response})

            parsed = self.parse_response(response)

            if parsed.get("success"):
                # Trust but verify: the agent may claim success prematurely.
                verify = self.tools["compile_file"](self.target_cpp_name)
                compile_attempts += 1
                if verify.get("success"):
                    self.save_history()
                    return {
                        "status": "success",
                        "message": "Target .cpp compiles.",
                        "attempts": compile_attempts,
                        "interactions": interaction_count,
                    }
                print(f"Agent claimed success but compile failed; continuing: {verify.get('log', '')[:300]}")
                self.history_messages.append({
                    "role": "user",
                    "content": json.dumps({
                        "tool_results": [{
                            "tool": "compile_file",
                            "success": False,
                            "result": verify,
                        }],
                        "summary": "You reported success but the file does not compile. Fix the errors below.",
                    }),
                })
                continue

            tool_calls = parsed.get("tool-calls", [])
            is_compiling = any(
                tc.get("tool") == "compile_file" for tc in tool_calls
            )
            if is_compiling:
                compile_attempts += 1

            tool_results = self.handle_tool_calls(tool_calls)
            print(json.dumps(tool_results, indent=2)[:1500])

            self.history_messages.append({
                "role": "user",
                "content": json.dumps({
                    "tool_results": tool_results,
                    "summary": f"Completed {len(tool_results)} tool calls",
                }, ensure_ascii=False),
            })

        self.save_history()
        if compile_attempts >= self.max_compile_attempts:
            return {
                "status": "max_compile_attempts_reached",
                "message": f"Reached maximum compile attempts ({self.max_compile_attempts})",
                "attempts": compile_attempts,
                "interactions": interaction_count,
            }
        return {
            "status": "max_interactions_reached",
            "message": f"Reached maximum interactions ({max_interactions})",
            "attempts": compile_attempts,
            "interactions": interaction_count,
        }
