from tqdm.asyncio import tqdm_asyncio
from openai import AsyncOpenAI
from openai.types.chat.chat_completion_message_param import ChatCompletionMessageParam
from openai.types.shared_params.response_format_json_schema import JSONSchema
from dataclasses import dataclass, field
from typing import List, Dict, Iterable, Any, Sequence, Union
import os
import random
import sys
import asyncio
import logging
import json
import time
from itertools import islice

current_path = str(os.path.dirname(os.path.dirname(__file__)))
if current_path not in sys.path:
    sys.path.append(current_path)

try:
    from utils.api import llm_api
    from utils.str_process import get_json_str
except ImportError:
    print("缺少api.py文件，请先配置api")
    exit(1)

# Configure logging
logger = logging.getLogger(__name__)

@dataclass
class GeneratorConfig:
    """Configuration for LLM Generator."""
    max_concurrent_tasks: int = 30
    initial_retry_delay: float = 2.0
    max_retry_delay: float = 60.0
    retry_multiplier: float = 2.0
    max_retries: int = 5

    @classmethod
    def from_dict(cls, config: Dict[str, Any]) -> 'GeneratorConfig':
        """Create config from dictionary."""
        return cls(**{k: v for k, v in config.items() if k in cls.__dataclass_fields__})


PromptType = Union[str, Sequence[ChatCompletionMessageParam]]
PromptsType = Union[PromptType, Sequence[PromptType], None]
JSONSchemaInput = Union[JSONSchema, Sequence[JSONSchema | None], None]
JSONValidationInput = Union[bool, Sequence[bool]]


class Generator:
    """Asynchronous LLM text generator with batching and retry capabilities."""

    _default_config = GeneratorConfig()

    # Process-wide cumulative token usage across all Generator instances
    # (main pipeline + repair agents), for cost reporting.
    global_usage: Dict[str, int] = {
        "calls": 0,
        "prompt_tokens": 0,
        "completion_tokens": 0,
        "total_tokens": 0,
        "cached_tokens": 0,
    }

    def __init__(
        self,
        ai_name: str,
        test_mode: bool = False,
        config: GeneratorConfig | None = None,
        temperature: float | None = None,
        enable_thinking: bool | None = None,
    ) -> None:
        """初始化模型生成器与可选的单进程请求限制。

        参数:
            ai_name: 注册的模型名称。
            test_mode: 为 True 时返回测试用模拟响应。
            config: 可选生成器配置;未传入时可由环境变量覆盖并发上限。
            temperature: 可选采样温度。
            enable_thinking: 支持的模型是否启用思考模式。
        返回:
            无;初始化实例状态。
        """
        if ai_name not in llm_api:
            available = ", ".join(llm_api.keys()) or "<未加载任何模型配置>"
            raise ValueError(
                f"无效的模型名称：{ai_name}。可用模型：{available}。"
                "请通过 SITP_LLM_CONFIG_FILE 或 SITP_LLM_CONFIG_JSON 加载配置。"
            )

        api = llm_api[ai_name]
        self.client = AsyncOpenAI(api_key=api['api_key'], base_url=api['base_url'])
        self.model_name = api['model_name']
        self.test_mode = test_mode
        if config is None:
            # 并发上限仅在显式设置时覆盖默认配置,便于受限额度下控制 in-flight 请求数。
            concurrency_override = os.environ.get("SITP_LLM_MAX_CONCURRENT_TASKS")
            if concurrency_override:
                config = GeneratorConfig.from_dict({
                    "max_concurrent_tasks": int(concurrency_override)
                })
        self.config = config or self._default_config
        self.temperature = temperature
        self.enable_thinking = enable_thinking

        self._prompts: List[PromptType] = []

        # Token usage tracking: populated per call when the provider supports
        # stream_options={"include_usage": True}; disabled automatically on rejection.
        self._usage_supported = True
        self.last_usage: Dict[str, int] | None = None
        self.total_usage: Dict[str, int] = {
            "calls": 0,
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
            "cached_tokens": 0,
        }
        self._trace_path: str | None = None
        self._trace_stage = "unclassified"

    def configure_trace(self, trace_path: str | None, stage: str = "unclassified") -> None:
        """配置逐次 LLM 调用的 token 追踪位置与所属阶段。

        参数：
            trace_path: JSONL 追踪文件路径；传入 None 时关闭追踪。
            stage: 当前调用所属的流程阶段名称。
        """
        self._trace_path = trace_path
        self._trace_stage = stage

    def set_trace_stage(self, stage: str) -> None:
        """更新后续 LLM 调用的流程阶段标签。

        参数：
            stage: 将写入追踪记录的阶段名称。
        """
        self._trace_stage = stage

    def add_prompt(self, prompt: PromptType) -> None:
        """Add a prompt to the internal queue.

        Args:
            prompt: A single prompt (string or message sequence)
        """
        self._prompts.append(prompt)

    def _normalize_messages(
        self,
        prompt: PromptType
    ) -> Sequence[ChatCompletionMessageParam]:
        """Convert prompt to standardized message format.

        Args:
            prompt: String prompt or message sequence

        Returns:
            Sequence of ChatCompletionMessageParam
        """
        if isinstance(prompt, str):
            return [{"role": "user", "content": prompt}]  # type: ignore
        return prompt

    async def _generate_single(
        self,
        prompt: PromptType,
        json_schema: JSONSchema | None = None,
        require_valid_json: bool = False,
        trace_stage: str = "unclassified",
    ) -> str:
        """为单个提示生成模型响应并按配置重试。

        参数:
            prompt: 输入提示或消息序列。
            json_schema: 可选的 JSON 输出结构。
            require_valid_json: 是否校验返回内容为有效 JSON。
            trace_stage: 用量追踪中的阶段标签。
        返回:
            模型生成的文本。
        """
        if self.test_mode:
            delay = random.uniform(0.1, 0.5)
            await asyncio.sleep(delay)
            if require_valid_json:
                return '{"test": true}'
            return """
<test result>
this is a test output.
```cpp
// this is a test code block
```
```java
// this is another test code block
```"""
        messages = self._normalize_messages(prompt)
        wait_time = self.config.initial_retry_delay
        started_at = time.monotonic()
        call_usage: Dict[str, int] | None = None

        for attempt in range(self.config.max_retries):
            result = ''
            try:
                request_options: Dict[str, Any] = {}
                if self.temperature is not None:
                    request_options["temperature"] = self.temperature
                # 可由单次运行环境变量限制预留的最大输出 token,默认不改变既有请求。
                max_tokens_override = os.environ.get("SITP_LLM_MAX_TOKENS")
                if max_tokens_override:
                    request_options["max_tokens"] = int(max_tokens_override)
                if self._usage_supported:
                    request_options["stream_options"] = {"include_usage": True}
                response = await self.client.chat.completions.create( # type: ignore
                    model=self.model_name,
                    messages=messages,
                    response_format=( # type: ignore
                        {"type": "json_schema", "json_schema": json_schema}
                        if json_schema else None
                    ),
                    stream=True,
                    extra_body=(
                        # qwen/deepseek 系模型支持 enable_thinking 开关；
                        # 未显式指定时保持默认关闭，避免改变既有实验行为。
                        {"enable_thinking": bool(self.enable_thinking)}
                        if (self.model_name.startswith('qwen') or "deepseek" in self.model_name.lower())
                        else None
                    ),
                    **request_options,
                )

                async for chunk in response:
                    chunk_usage = getattr(chunk, "usage", None)
                    if chunk_usage is not None:
                        call_usage = self._record_usage(chunk_usage)
                    if chunk.choices:
                        if chunk.choices[0].delta:
                            result += chunk.choices[0].delta.content or ''
                        else:
                            # print('warning: delta content is None')
                            pass
                if require_valid_json:
                    self._validate_json_response(result)
                self._write_trace_entry(trace_stage, call_usage, time.monotonic() - started_at)
                return result

            except Exception as e:
                if self._usage_supported and ("stream_options" in str(e) or "include_usage" in str(e)):
                    self._usage_supported = False
                    logger.warning("Provider rejected stream_options; disabling usage tracking.")
                prompt_preview = str(prompt)[:100] + '...' if len(str(prompt)) > 100 else str(prompt)
                logger.warning(
                    f"Attempt {attempt + 1}/{self.config.max_retries} failed for prompt '{prompt_preview}': {e}"
                    f"\noutput: {result}"
                )

                if attempt < self.config.max_retries - 1:
                    actual_delay = min(wait_time, self.config.max_retry_delay)
                    logger.info(f"Retrying in {actual_delay:.1f} seconds...")
                    await asyncio.sleep(actual_delay)
                    wait_time *= self.config.retry_multiplier
                else:
                    logger.error(f"Max retries exceeded for prompt: {prompt_preview}")
                    raise
        return ""  # Should never reach here

    def _record_usage(self, usage: Any) -> Dict[str, int]:
        """Accumulate token usage from the final chunk of a streaming response."""
        details = getattr(usage, "prompt_tokens_details", None)
        cached_tokens = int(getattr(details, "cached_tokens", 0) or 0) if details else 0
        self.last_usage = {
            "prompt_tokens": int(getattr(usage, "prompt_tokens", 0) or 0),
            "completion_tokens": int(getattr(usage, "completion_tokens", 0) or 0),
            "total_tokens": int(getattr(usage, "total_tokens", 0) or 0),
            "cached_tokens": cached_tokens,
        }
        self.total_usage["calls"] += 1
        Generator.global_usage["calls"] += 1
        for key in ("prompt_tokens", "completion_tokens", "total_tokens", "cached_tokens"):
            self.total_usage[key] += self.last_usage[key]
            Generator.global_usage[key] += self.last_usage[key]
        return dict(self.last_usage)

    def _write_trace_entry(
        self,
        stage: str,
        usage: Dict[str, int] | None,
        elapsed_seconds: float,
    ) -> None:
        """将一次成功调用的阶段、token 和耗时追加到 JSONL 追踪文件。

        参数：
            stage: 调用所属阶段。
            usage: 服务端返回的 token 用量；不支持时为 None。
            elapsed_seconds: 本次调用的墙钟耗时（秒）。
        """
        if not self._trace_path:
            return
        entry = {
            "stage": stage,
            "model": self.model_name,
            "prompt_tokens": usage.get("prompt_tokens") if usage else None,
            "completion_tokens": usage.get("completion_tokens") if usage else None,
            "total_tokens": usage.get("total_tokens") if usage else None,
            "cached_tokens": usage.get("cached_tokens") if usage else None,
            "elapsed_seconds": round(elapsed_seconds, 3),
        }
        try:
            with open(self._trace_path, "a", encoding="utf-8") as trace_file:
                trace_file.write(json.dumps(entry, ensure_ascii=False) + "\n")
        except OSError as exc:
            logger.warning("Failed to write LLM trace: %s", exc)

    async def _generate_batch(
        self,
        prompts: Sequence[PromptType],
        json_schemas: Sequence[JSONSchema | None] | None = None,
        require_valid_json_flags: Sequence[bool] | None = None,
        trace_stage: str = "unclassified",
    ) -> List[str]:
        """Generate responses for a batch of prompts concurrently.

        Args:
            prompts: Sequence of prompts to process
            json_schemas: Optional sequence of JSON schemas (one per prompt),
                         or a single schema to apply to all prompts

        Returns:
            List of generated responses
        """
        if not prompts:
            return []

        # Normalize json_schemas to a sequence
        if json_schemas is None:
            json_schemas = [None] * len(prompts)
        elif self._is_single_schema(json_schemas):
            # Single JSONSchema object - apply to all prompts
            json_schemas = [json_schemas] * len(prompts)  # type: ignore
        if require_valid_json_flags is None:
            require_valid_json_flags = [False] * len(prompts)

        # Validate lengths match
        if len(json_schemas) != len(prompts):  # type: ignore
            raise ValueError(
                f"Number of JSON schemas ({len(json_schemas)}) must match "  # type: ignore
                f"number of prompts ({len(prompts)})"
            )
        if len(require_valid_json_flags) != len(prompts):
            raise ValueError(
                f"Number of JSON validation flags ({len(require_valid_json_flags)}) must match "
                f"number of prompts ({len(prompts)})"
            )

        # Create tasks with paired prompts and schemas
        tasks = [
            self._generate_single(prompt, schema, require_valid_json, trace_stage)
            for prompt, schema, require_valid_json in zip(prompts, json_schemas, require_valid_json_flags)  # type: ignore
        ]

        results = await tqdm_asyncio.gather(*tasks)
        return results

    def _is_single_schema(self, json_schemas: Any) -> bool:
        """Check if json_schemas is a single schema object (not a sequence).

        Args:
            json_schemas: Object to check

        Returns:
            True if it appears to be a single JSONSchema dict
        """
        # Check if it's a dict with JSONSchema-like structure
        if isinstance(json_schemas, dict):
            return True
        return False

    def _normalize_prompts(
        self,
        prompts: PromptsType
    ) -> Sequence[PromptType]:
        """Normalize various prompt input formats to a sequence.

        Args:
            prompts: Input in various formats (None, single, or sequence)

        Returns:
            Sequence of normalized prompts
        """
        if prompts is None:
            prompts = self._prompts
            self._prompts = []
        elif not prompts:
            return []

        # Handle single prompt (string or message list)
        if isinstance(prompts, str):
            return [prompts]

        # Check if it's already a sequence of message lists or strings
        try:
            first_item = list(islice(prompts, 1))[0]  # type: ignore
            # If first item is a dict (message), wrap the whole thing
            if isinstance(first_item, dict):
                return [prompts]  # type: ignore
        except (StopIteration, TypeError):
            pass

        return prompts  # type: ignore

    def generate(
        self,
        prompts: PromptsType = None,
        json_schema: JSONSchemaInput = None,
        require_valid_json: JSONValidationInput = False,
        trace_stage: str | None = None,
    ) -> List[str]:
        """Generate responses for prompts with batching.

        This method runs the async generation in an event loop and handles
        batching of large numbers of prompts to avoid overwhelming the API.

        Args:
            prompts: Prompts to generate from (uses internal queue if None)
            json_schema: JSON schema configuration. Can be:
                - None: no schema for any prompt
                - Single JSONSchema: apply to all prompts
                - Sequence of JSONSchema/None: one schema per prompt
            require_valid_json: When True, each response must contain a valid JSON
                string extractable by get_json_code(), otherwise it is retried.
                Can also be a sequence of booleans matching the prompts.

        Returns:
            List of generated responses

        Examples:
            >>> # No schema
            >>> gen.generate(["Hello", "World"])

            >>> # Same schema for all prompts
            >>> schema = JSONSchema(name="output", strict=True)
            >>> gen.generate(["Hello", "World"], json_schema=schema)

            >>> # Different schema per prompt
            >>> schemas = [schema1, schema2, None]
            >>> gen.generate(["p1", "p2", "p3"], json_schema=schemas)
        """
        normalized_prompts = self._normalize_prompts(prompts)
        current_trace_stage = trace_stage or self._trace_stage

        if not normalized_prompts:
            return []

        # Convert to list for iteration
        prompt_list = list(normalized_prompts)
        all_results = []

        # Normalize json_schemas to match prompt_list length
        json_schemas = self._normalize_json_schemas(json_schema, len(prompt_list))
        json_validation_flags = self._normalize_json_validation_flags(
            require_valid_json, len(prompt_list)
        )

        # Process in batches to avoid overwhelming the API
        batch_size = self.config.max_concurrent_tasks
        total_batches = (len(prompt_list) + batch_size - 1) // batch_size

        logger.info(f"Processing {len(prompt_list)} prompts in {total_batches} batches")

        for i in range(0, len(prompt_list), batch_size):
            batch = prompt_list[i:i + batch_size]
            batch_schemas = json_schemas[i:i + batch_size]
            batch_validation_flags = json_validation_flags[i:i + batch_size]
            batch_num = i // batch_size + 1
            logger.info(f"Processing batch {batch_num}/{total_batches} ({len(batch)} prompts)")

            batch_results = asyncio.run(
                self._generate_batch(batch, batch_schemas, batch_validation_flags, current_trace_stage)
            )
            all_results.extend(batch_results)

        logger.info(f"Completed processing {len(all_results)} prompts")
        return all_results

    def _normalize_json_schemas(
        self,
        json_schema: JSONSchemaInput,
        num_prompts: int
    ) -> Sequence[JSONSchema | None]:
        """Normalize JSON schema input to a sequence of schemas.

        Args:
            json_schema: Input in various formats
            num_prompts: Number of prompts to match

        Returns:
            Sequence of JSONSchema/None matching num_prompts length
        """
        if json_schema is None:
            return [None] * num_prompts

        # Check if it's a single JSONSchema object (not a sequence)
        if self._is_single_schema(json_schema):
            return [json_schema] * num_prompts  # type: ignore

        # It's already a sequence
        schema_list = list(json_schema)  # type: ignore

        if len(schema_list) != num_prompts:
            raise ValueError(
                f"Number of JSON schemas ({len(schema_list)}) must match "
                f"number of prompts ({num_prompts})"
            )

        return schema_list

    def _normalize_json_validation_flags(
        self,
        require_valid_json: JSONValidationInput,
        num_prompts: int
    ) -> Sequence[bool]:
        """
        将 JSON 校验标志输入统一为与提示数量匹配的标志序列。

        参数:
            require_valid_json: 单个布尔值（应用于所有提示）或与提示
                                数量一致的布尔值序列
            num_prompts: 需要匹配的提示数量

        返回:
            Sequence[bool]: 长度等于 num_prompts 的布尔标志序列

        异常:
            ValueError: 当传入序列的长度与 num_prompts 不一致时抛出
        """
        if isinstance(require_valid_json, bool):
            return [require_valid_json] * num_prompts

        flags = list(require_valid_json)
        if len(flags) != num_prompts:
            raise ValueError(
                f"Number of JSON validation flags ({len(flags)}) must match "
                f"number of prompts ({num_prompts})"
            )
        return flags

    def _validate_json_response(self, response_text: str) -> None:
        """
        校验生成结果中是否包含合法且可解析的 JSON 字符串。

        参数:
            response_text: 模型返回的原始响应文本

        异常:
            ValueError: 当响应中不包含 JSON 字符串或 JSON 无法解析时抛出
        """
        json_str = get_json_str(response_text)
        if not json_str:
            raise ValueError("Response does not contain a JSON string.")
        json.loads(json_str)


def _run_tests() -> None:
    """使用配置中的首个模型运行 Generator 自检，无返回值。"""
    # Configure logging for tests
    logging.basicConfig(level=logging.INFO)

    if not llm_api:
        raise RuntimeError("运行自检前必须先加载至少一个 LLM 配置")
    test_generator = Generator(next(iter(llm_api)), test_mode=True)

    # Test 1: Single string prompt
    print("=== Test 1: Single String Prompt ===")
    test1 = "Who are you?"
    result1 = test_generator.generate(test1)
    print(f"Result: {result1[0][:50]}...")

    # Test 2: Single message sequence
    print("\n=== Test 2: Single Message Sequence ===")
    test2 = [
        {"role": "user", "content": "Who are you?"},
        {"role": "assistant", "content": "I am a chatbot."},
        {"role": "user", "content": "What is your name?"},
    ]
    result2 = test_generator.generate(test2)
    print(f"Result: {result2[0][:50]}...")

    # Test 3: Multiple string prompts
    print("\n=== Test 3: Multiple String Prompts ===")
    test3 = [
        "Who are you?",
        "What can you do?"
    ]
    result3 = test_generator.generate(test3)
    print(f"Results: {len(result3)} responses")

    # Test 4: Multiple message sequences
    print("\n=== Test 4: Multiple Message Sequences ===")
    test4 = [
        [
            {"role": "user", "content": "Who are you?"},
            {"role": "assistant", "content": "I am a chatbot."},
            {"role": "user", "content": "What is your name?"},
        ],
        [
            {"role": "user", "content": "What can you do?"}
        ]
    ]
    result4 = test_generator.generate(test4)
    print(f"Results: {len(result4)} responses")

    # Test 5: Using add_prompt
    print("\n=== Test 5: Using add_prompt ===")
    test_generator.add_prompt("Test prompt 1")
    test_generator.add_prompt("Test prompt 2")
    result5 = test_generator.generate()
    print(f"Results: {len(result5)} responses")

    # Test 6: Different JSON schemas per prompt
    print("\n=== Test 6: Different JSON Schemas Per Prompt ===")
    from openai.types.shared_params import FunctionDefinition

    # Create different schemas
    schema1 = JSONSchema(
        name="person",
        strict=True,
        schema=FunctionDefinition(
            name="person",
            strict=True,
            parameters={
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "age": {"type": "integer"}
                },
                "required": ["name", "age"],
                "additionalProperties": False
            }
        )
    )

    schema2 = JSONSchema(
        name="location",
        strict=True,
        schema=FunctionDefinition(
            name="location",
            strict=True,
            parameters={
                "type": "object",
                "properties": {
                    "city": {"type": "string"},
                    "country": {"type": "string"}
                },
                "required": ["city", "country"],
                "additionalProperties": False
            }
        )
    )

    test6 = [
        f"Extract person info from: John is 25 years old",
        f"Extract location from: Paris, France",
        f"This one has no schema requirement"
    ]

    result6 = test_generator.generate(test6, json_schema=[schema1, schema2, None])
    print(f"Results: {len(result6)} responses")
    print("  - Prompt 1 uses person schema")
    print("  - Prompt 2 uses location schema")
    print("  - Prompt 3 has no schema")

    # Test 7: Same schema for all prompts
    print("\n=== Test 7: Same Schema for All Prompts ===")
    test7 = [
        "Extract person from: Alice is 30",
        "Extract person from: Bob is 35"
    ]
    result7 = test_generator.generate(test7, json_schema=schema1)
    print(f"Results: {len(result7)} responses (all with person schema)")

    print("\n=== All Tests Completed ===")


   
