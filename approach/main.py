import json
import shutil
import sys
import time
from pathlib import Path

apprach_dir_path = Path(__file__).parent
if apprach_dir_path not in sys.path:
    sys.path.append(str(apprach_dir_path))

from path_config import cfg_run_dir, cfg_new_run_id, cfg_latest_run_id
from utils.Generator import Generator

from v4_7.steps.translation_pipeline import TranslationPipeline

version = 'v4_7'


def _write_llm_usage(output_dir: str, ai_name: str, temperature: float, mode: str, run_id: str, started_at: float) -> None:
    """Persist process-wide LLM token usage and wall time for cost reporting.

    When llm_usage.json already exists (e.g. a follow-up repair pass on the
    same run), token counts and wall time are accumulated so the file reflects
    the total cost of the run across processes.
    """
    try:
        usage = dict(Generator.global_usage)
        usage["wall_seconds"] = round(time.monotonic() - started_at, 3)
        usage["ai_name"] = ai_name
        usage["temperature"] = temperature
        usage["mode"] = mode
        usage["run_id"] = run_id
        result_dir = Path(output_dir) / "result"
        result_dir.mkdir(parents=True, exist_ok=True)
        usage_path = result_dir / "llm_usage.json"
        if usage_path.exists():
            try:
                previous = json.loads(usage_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                previous = {}
            for key in ("calls", "prompt_tokens", "completion_tokens", "total_tokens", "cached_tokens", "wall_seconds"):
                prev_val = previous.get(key)
                cur_val = usage.get(key)
                if isinstance(prev_val, (int, float)) and isinstance(cur_val, (int, float)):
                    usage[key] = round(prev_val + cur_val, 3)
            usage["processes"] = int(previous.get("processes", 1)) + 1
        usage_path.write_text(
            json.dumps(usage, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    except Exception as exc:
        print(f"Warning: failed to write llm_usage.json: {exc}")


def _write_stage_token_summary(output_dir: str) -> None:
    """根据逐调用 JSONL 追踪生成各阶段输入、输出 token 汇总。

    参数：
        output_dir: 当前运行输出目录，追踪和汇总文件均位于其 result 子目录。
    """
    result_dir = Path(output_dir) / "result"
    trace_path = result_dir / "llm_trace.jsonl"
    if not trace_path.exists():
        return

    stages: dict[str, dict[str, int]] = {}
    try:
        for line in trace_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            entry = json.loads(line)
            stage = str(entry.get("stage") or "unclassified")
            stats = stages.setdefault(stage, {
                "calls": 0,
                "calls_with_usage": 0,
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0,
                "cached_tokens": 0,
            })
            stats["calls"] += 1
            if entry.get("total_tokens") is None:
                continue
            stats["calls_with_usage"] += 1
            for key in ("prompt_tokens", "completion_tokens", "total_tokens", "cached_tokens"):
                stats[key] += int(entry.get(key) or 0)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"Warning: failed to summarize stage token usage: {exc}")
        return

    totals = {
        key: sum(stats[key] for stats in stages.values())
        for key in ("calls", "calls_with_usage", "prompt_tokens", "completion_tokens", "total_tokens", "cached_tokens")
    }
    for stats in stages.values():
        stats["total_token_share"] = round(
            stats["total_tokens"] / totals["total_tokens"], 6
        ) if totals["total_tokens"] else 0.0
    summary = {"stages": stages, "totals": totals}
    try:
        (result_dir / "stage_token_summary.json").write_text(
            json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    except OSError as exc:
        print(f"Warning: failed to write stage token summary: {exc}")


def main(
    ai_name: str,
    project_name: str,
    test_mode: bool = False,
    resume: bool = False,
    force_rebuild: bool = False,
    clear_method_progress: bool = False,
    skip_mapping: bool = False,
    skip_cpp_compile: bool = False,
    compile_timeout: int = 60,
    repair_after_compile: bool = False,
    max_repair_attempts: int = 10,
    apply_repair: bool = False,
    max_tool_calls: int | None = None,
    header_batch_size: int = 1,
    header_max_rounds: int = 10,
    header_translation_mode: str = "batched_iterative",
    method_translation_mode: str = "contextual",
    header_grouping_strategy: str = "dependency",
    header_grouping_seed: int | None = None,
    allow_header_failures: bool = False,
    repair_test_suites: str = "base",
    temperature: float = 0.2,
    feature_requery_budget: int = 10,
    fragment_max_tries: int = 5,
    type_compatibility: bool = True,
    snapshot_source: str = "",
    snapshot_target: str = "",
    snapshot_validation: bool = False,
    mode: str = "full",
    run_id: str = "",
    mapping_ai: str = "",
    mapping_thinking: bool = True,
):
    """执行 v4_7 翻译框架主流程的入口函数。

    负责确定运行 ID（新增、续跑或指定）、准备输出目录、按 mode 分发到
    具体的流水线阶段（full/header/mapping/method/compile/repair 以及各
    baseline），并在结束后持久化整次运行的 LLM token 用量与耗时。

    参数：
        ai_name: 使用的模型名（须在 utils/api.py 中注册）。
        project_name: 待翻译的源项目名。
        test_mode: 是否以测试模式（离线 mock 回答）运行 Generator。
        resume: 是否续跑最近一次运行。
        force_rebuild: 是否强制重建图结构与结果目录。
        clear_method_progress: 是否在运行前清空 method 映射/翻译进度。
        skip_mapping: 是否跳过基于 LLM 的 Java→C++ 方法映射步骤（消融）。
        skip_cpp_compile: 是否跳过最终的 C++ 实现文件编译检查。
        compile_timeout: 单个 C++ 文件编译检查的超时秒数。
        repair_after_compile: 编译检查后是否执行 agent 修复。
        max_repair_attempts: agent 修复时每个失败文件的最大尝试次数。
        apply_repair: 是否将修复后的 .h/.cpp 文件从 review 目录回写到 result。
        header_batch_size: header 分批翻译的批量大小。
        header_max_rounds: header 迭代反馈的最大轮数（1 表示禁用反馈）。
        header_translation_mode: header 消融模式（batched_iterative / per_file_one_shot）。
        method_translation_mode: method 消融模式（contextual / no_context）。
        header_grouping_strategy: header 分组策略（dependency / random）。
        header_grouping_seed: random 分组策略的可复现随机种子。
        allow_header_failures: header 未收敛时是否仍继续 full/header 流程。
        repair_test_suites: repair 阶段按顺序执行的测试套件，逗号分隔。
        temperature: LLM 采样温度。
        feature_requery_budget: Oxidizer baseline 单个候选的最大特性映射重试次数。
        fragment_max_tries: Oxidizer baseline 单个片段的最大编译器反馈尝试次数。
        type_compatibility: 是否启用 Oxidizer 静态类型兼容性检查。
        snapshot_source: Oxidizer 兼容性校验用的 JSON 源执行快照路径。
        snapshot_target: Oxidizer 兼容性校验用的 JSON C++ 执行快照路径。
        snapshot_validation: 是否启用可选的 canonical JSON 快照校验。
        mode: 翻译模式（full/header/mapping/method/compile/repair 或某 baseline）。
        run_id: 指定使用已有运行 ID（为空时新建或按 resume 续跑）。

    返回：
        int: 成功返回 0。
    """
    if run_id:
        print(f"Using specified run {run_id}")
    elif resume:
        run_id = cfg_latest_run_id(ai_name, project_name, version)
        if run_id is None:
            print("No previous run found, starting a new run.")
            run_id = cfg_new_run_id()
        else:
            print(f"Resuming run {run_id}")
    else:
        run_id = cfg_new_run_id()

    output_dir = str(cfg_run_dir(ai_name, project_name, version, run_id))

    print(f"Starting translation for project: {project_name}")
    print(f"Run ID: {run_id}")
    print(f"Output directory: {output_dir}")
    print(f"Using model: {ai_name}")
    print(f"Temperature: {temperature}")
    print(f"Mode: {mode}")
    if clear_method_progress:
        print("Clear method progress: enabled")
    if skip_mapping:
        print("Skip method mapping: enabled")
    if skip_cpp_compile:
        print("C++ compile check: skipped")
    if repair_after_compile:
        print("Repair after compile: enabled")
    if apply_repair:
        print("Apply repair to result: enabled")
    if allow_header_failures:
        print("Allow header failures: enabled")
    print("-" * 50)

    if force_rebuild:
        from path_config import cfg_run_graph_dir, cfg_run_result_dir
        graph_dir = cfg_run_graph_dir(ai_name, project_name, version, run_id)
        result_dir = cfg_run_result_dir(ai_name, project_name, version, run_id)
        if graph_dir.exists():
            shutil.rmtree(graph_dir)
        if result_dir.exists():
            shutil.rmtree(result_dir)

    generator = Generator(ai_name, test_mode=test_mode, temperature=temperature)
    # 方法映射属于工程辅助环节而非评测内容：默认单独使用更强的 gpt 模型并
    # 开启思考模式；可用 --mapping-ai/--no-mapping-thinking 覆盖。
    mapping_generator = None
    if mapping_ai or mapping_thinking:
        mapping_generator = Generator(
            mapping_ai or ai_name,
            test_mode=test_mode,
            temperature=temperature,
            enable_thinking=True if mapping_thinking else None,
        )
    result_trace_dir = Path(output_dir) / "result"
    standard_pipeline_modes = {"full", "header", "mapping", "method", "repair"}
    if mode in standard_pipeline_modes:
        result_trace_dir.mkdir(parents=True, exist_ok=True)
        generator.configure_trace(str(result_trace_dir / "llm_trace.jsonl"))
    started_at = time.monotonic()
    pipeline = TranslationPipeline(
        generator,
        header_batch_size=header_batch_size,
        max_header_rounds=header_max_rounds,
        cpp_compile_timeout=compile_timeout,
        header_translation_mode=header_translation_mode,
        method_translation_mode=method_translation_mode,
        header_grouping_strategy=header_grouping_strategy,
        header_grouping_seed=header_grouping_seed,
        repair_test_suites=tuple(
            suite.strip()
            for suite in repair_test_suites.split(",")
            if suite.strip()
        ),
        mapping_generator=mapping_generator,
    )

    if mode == "header":
        pipeline.run_header_translation(
            ai_name,
            project_name,
            force_rebuild=force_rebuild,
            run_id=run_id,
            allow_failures=allow_header_failures,
        )
    elif mode == "mapping":
        pipeline.run_method_mapping(ai_name, project_name, force_rebuild=force_rebuild, run_id=run_id, clear_method_progress=clear_method_progress)
    elif mode == "method":
        pipeline.run_method_translation(
            ai_name,
            project_name,
            force_rebuild=force_rebuild,
            run_id=run_id,
            clear_method_progress=clear_method_progress,
            skip_mapping=skip_mapping,
            skip_cpp_compile=skip_cpp_compile,
            repair_after_compile=repair_after_compile,
            max_repair_attempts=max_repair_attempts,
            apply_repair=apply_repair,
            max_tool_calls=max_tool_calls,
        )
    elif mode == "compile":
        pipeline.run_cpp_compile_check(ai_name, project_name, force_rebuild=force_rebuild, run_id=run_id)
    elif mode == "repair":
        pipeline.run_agent_repair(
            ai_name,
            project_name,
            force_rebuild=force_rebuild,
            run_id=run_id,
            max_repair_attempts=max_repair_attempts,
            apply_repair=apply_repair,
            max_tool_calls=max_tool_calls,
        )
    elif mode == "alphatrans-baseline":
        from v4_7.baselines.alphatrans_style.pipeline import AlphaTransStylePipeline

        baseline = AlphaTransStylePipeline(
            generator,
            max_translate_attempts=2,
            max_feedback_rounds=max_repair_attempts,
            compile_timeout=compile_timeout,
        )
        baseline.run(
            ai_name,
            project_name,
            force_rebuild=force_rebuild,
            run_id=run_id,
            max_feedback_rounds=max_repair_attempts,
        )
    elif mode == "react-baseline":
        from v4_7.baselines.react_style.pipeline import ReactStylePipeline

        baseline = ReactStylePipeline(
            generator,
            max_compile_attempts=max_repair_attempts,
            compile_timeout=compile_timeout,
        )
        baseline.run(
            ai_name,
            project_name,
            force_rebuild=force_rebuild,
            run_id=run_id,
        )
    elif mode == "direct-translation":
        from v4_7.baselines.direct_translation.pipeline import DirectTranslationPipeline

        baseline = DirectTranslationPipeline(
            generator,
            max_feedback_rounds=max_repair_attempts,
            compile_timeout=compile_timeout,
        )
        baseline.run(ai_name, project_name, run_id=run_id)
    elif mode == "oxidizer-baseline":
        from v4_7.baselines.oxidizer_style import OxidizerStylePipeline

        baseline = OxidizerStylePipeline(
            generator,
            feature_requery_budget=feature_requery_budget,
            fragment_max_tries=fragment_max_tries,
            compile_timeout=compile_timeout,
            type_compatibility=type_compatibility,
            snapshot_source=Path(snapshot_source) if snapshot_source else None,
            snapshot_target=Path(snapshot_target) if snapshot_target else None,
            snapshot_validation=snapshot_validation,
        )
        baseline.run(
            ai_name,
            project_name,
            force_rebuild=force_rebuild,
            run_id=run_id,
        )
    else:
        pipeline.run_full_translation(
            ai_name,
            project_name,
            force_rebuild=force_rebuild,
            run_id=run_id,
            clear_method_progress=clear_method_progress,
            skip_mapping=skip_mapping,
            skip_cpp_compile=skip_cpp_compile,
            repair_after_compile=repair_after_compile,
            max_repair_attempts=max_repair_attempts,
            apply_repair=apply_repair,
            max_tool_calls=max_tool_calls,
            allow_header_failures=allow_header_failures,
        )

    _write_llm_usage(output_dir, ai_name, temperature, mode, run_id, started_at)
    if mode in standard_pipeline_modes:
        _write_stage_token_summary(output_dir)
    print("Translation completed successfully!")
    print(f"Generated files are available at: {output_dir}")
    print(f"Run ID: {run_id}")
    return 0


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description="v4_7 translation pipeline")
    parser.add_argument("--ai", required=True, help="AI model name")
    parser.add_argument("--mapping-ai", default="", help="方法映射阶段单独使用的模型；默认与 --ai 一致")
    parser.add_argument("--mapping-thinking", action=argparse.BooleanOptionalAction, default=True, help="方法映射模型开启思考模式（默认开启，--no-mapping-thinking 关闭）")
    parser.add_argument("--project", required=True, help="Project name")
    parser.add_argument("--test", action="store_true", help="Test mode")
    parser.add_argument("--resume", action="store_true", help="Resume the most recent run")
    parser.add_argument("--force-rebuild", action="store_true", help="Force rebuild from scratch")
    parser.add_argument("--clear-method-progress", action="store_true", help="Clear method mapping/translation progress before running mapping or method translation")
    parser.add_argument("--skip-mapping", action="store_true", help="Skip the LLM-based Java-to-C++ method mapping step (ablation)")
    parser.add_argument("--skip-cpp-compile", action="store_true", help="Skip final C++ implementation file compile check in full or method mode")
    parser.add_argument("--compile-timeout", type=int, default=60, help="Timeout in seconds for each C++ file compile check")
    parser.add_argument("--repair-after-compile", action="store_true", help="Run agent repair after C++ compile check in full or method mode")
    parser.add_argument("--max-repair-attempts", type=int, default=5, help="Maximum compile attempts per failed C++ file during agent repair")
    parser.add_argument("--apply-repair", action="store_true", help="Copy repaired .h/.cpp files from review back to result")
    parser.add_argument("--max-tool-calls", type=int, default=None, help="Project-level maximum repair tool calls; default auto-scales with module size (max(150, 10 per header))")
    parser.add_argument("--header-batch-size", type=int, default=3, help="Header batch size")
    parser.add_argument("--header-max-rounds", type=int, default=5, help="Maximum header iteration rounds (1 disables iterative feedback)")
    parser.add_argument("--header-translation-mode", choices=["batched_iterative", "per_file_one_shot"], default="batched_iterative", help="Header ablation mode")
    parser.add_argument("--method-translation-mode", choices=["contextual", "no_context"], default="contextual", help="Method ablation mode")
    parser.add_argument("--header-grouping-strategy", choices=["dependency", "random"], default="dependency", help="Header grouping strategy")
    parser.add_argument("--header-grouping-seed", type=int, default=None, help="Reproducible seed for random header grouping")
    parser.add_argument("--allow-header-failures", action="store_true", help="Continue full/header mode after header translation fails to converge")
    parser.add_argument("--repair-test-suites", default="base", metavar="SUITES", help="Functional test suites used by repair: base or base,additional")
    parser.add_argument("--temperature", type=float, default=0.2, help="LLM sampling temperature")
    parser.add_argument("--feature-requery-budget", type=int, default=10, help="Maximum feature-mapping retries per candidate")
    parser.add_argument("--fragment-max-tries", type=int, default=5, help="Maximum compiler-feedback attempts per Oxidizer fragment")
    parser.add_argument("--disable-type-compatibility", action="store_true", help="Disable Oxidizer static type-compatibility checks")
    parser.add_argument("--snapshot-source", default="", help="JSON source execution snapshots for Oxidizer compatibility validation")
    parser.add_argument("--snapshot-target", default="", help="JSON C++ execution snapshots for Oxidizer compatibility validation")
    parser.add_argument("--snapshot-validation", action="store_true", help="Enable optional canonical JSON snapshot validation")
    parser.add_argument("--mode", choices=["full", "header", "mapping", "method", "compile", "repair", "alphatrans-baseline", "react-baseline", "direct-translation", "oxidizer-baseline"], default="full", help="Translation mode: full pipeline, focused stages, or one of the available baselines")
    parser.add_argument("--run-id", default="", help="Use a specific existing run id instead of creating a new run")
    args = parser.parse_args()
    main(args.ai, args.project, test_mode=args.test, resume=args.resume, force_rebuild=args.force_rebuild, clear_method_progress=args.clear_method_progress, skip_mapping=args.skip_mapping, skip_cpp_compile=args.skip_cpp_compile, compile_timeout=args.compile_timeout, repair_after_compile=args.repair_after_compile, max_repair_attempts=args.max_repair_attempts, apply_repair=args.apply_repair, max_tool_calls=args.max_tool_calls, header_batch_size=args.header_batch_size, header_max_rounds=args.header_max_rounds, header_translation_mode=args.header_translation_mode, method_translation_mode=args.method_translation_mode, header_grouping_strategy=args.header_grouping_strategy, header_grouping_seed=args.header_grouping_seed, allow_header_failures=args.allow_header_failures, repair_test_suites=args.repair_test_suites, temperature=args.temperature, feature_requery_budget=args.feature_requery_budget, fragment_max_tries=args.fragment_max_tries, type_compatibility=not args.disable_type_compatibility, snapshot_source=args.snapshot_source, snapshot_target=args.snapshot_target, snapshot_validation=args.snapshot_validation, mode=args.mode, run_id=args.run_id, mapping_ai=args.mapping_ai, mapping_thinking=args.mapping_thinking)
