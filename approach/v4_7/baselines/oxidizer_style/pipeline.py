from __future__ import annotations

import json
import re
import time
from pathlib import Path
from typing import Any

from graph import Header, Method, Project
from path_config import cfg_run_graph_dir, cfg_run_result_dir
from utils.Generator import Generator
from utils.str_process import get_json_str
from v4_7.steps import version
from v4_7.steps.bounded_file_generator import BoundedFileGenerator
from v4_7.steps.method_translation.mapping_step import MethodMappingStep
from v4_7.steps.method_translation.models import MethodMappingResult
from v4_7.steps.method_translation.output_parser import looks_like_expected_method
from v4_7.steps.step01_graph_build import GraphBuildStep

from .compiler import OxidizerCompiler
from .evaluator import add_coarse_method_metrics
from .feature_rules import applicable_rules, validate_rules
from .models import AttemptRecord, CheckResult, FragmentRecord
from .planner import header_dependency_groups, method_dependency_groups
from .prompts import header_prompt, method_prompt
from .reporting import OxidizerReportStore
from .snapshots import check_snapshot_files
from .type_compatibility import (
    check_header_compatibility,
    check_method_mappings,
    check_method_signature,
)


class OxidizerStylePipeline:
    """Compile-first adaptation of Oxidizer's type-driven translation phase."""

    def __init__(
        self,
        generator: Generator,
        feature_requery_budget: int = 10,
        fragment_max_tries: int = 5,
        compile_timeout: int = 60,
        type_compatibility: bool = True,
        snapshot_source: Path | None = None,
        snapshot_target: Path | None = None,
        snapshot_validation: bool = False,
    ) -> None:
        self.generator = generator
        self.feature_requery_budget = max(1, feature_requery_budget)
        self.fragment_max_tries = max(1, fragment_max_tries)
        self.graph_builder = GraphBuildStep()
        self.mapping_step = MethodMappingStep(generator)
        self.file_generator = BoundedFileGenerator()
        self.compiler = OxidizerCompiler(compile_timeout)
        self.compile_timeout = compile_timeout
        self.type_compatibility = type_compatibility
        self.snapshot_source = Path(snapshot_source) if snapshot_source else None
        self.snapshot_target = Path(snapshot_target) if snapshot_target else None
        self.snapshot_validation = snapshot_validation
        self.compiler_version = self.compiler.version()

        self.ai_name = ""
        self.project_name = ""
        self.run_id = ""
        self.graph_dir = Path()
        self.result_dir = Path()
        self.work_dir = Path()
        self.report_dir = Path()
        self.store: OxidizerReportStore
        self._run_started = 0.0
        self._elapsed_before_run = 0.0

    def run(
        self,
        ai_name: str,
        project_name: str,
        force_rebuild: bool = False,
        run_id: str = "",
    ) -> Project:
        started = time.monotonic()
        self._run_started = started
        self.ai_name = ai_name
        self.project_name = project_name
        self.run_id = run_id
        self.graph_dir = cfg_run_graph_dir(ai_name, project_name, version, run_id)
        self.result_dir = cfg_run_result_dir(ai_name, project_name, version, run_id)
        self.work_dir = self.result_dir / ".oxidizer_work"
        self.report_dir = self.result_dir / "compile_report"
        self.result_dir.mkdir(parents=True, exist_ok=True)
        self.work_dir.mkdir(parents=True, exist_ok=True)
        self.report_dir.mkdir(parents=True, exist_ok=True)
        self.store = OxidizerReportStore(self.result_dir)
        self._elapsed_before_run = self.store.previous_elapsed_seconds()

        project = self.graph_builder.build_graph(
            ai_name,
            project_name,
            force_rebuild=force_rebuild,
            run_id=run_id,
        )

        self._translate_headers(project)
        self._map_methods(project)
        self._translate_methods(project)

        self._materialize(project, self.result_dir)
        has_stubs = any(record.get("stubbed") for record in self.store.records.values())
        final_evaluation = self.compiler.evaluate_project(
            self.result_dir, self.report_dir, has_stubs=has_stubs
        )
        if self.snapshot_validation and self.snapshot_source and self.snapshot_target:
            try:
                final_evaluation["snapshot_compatibility"] = check_snapshot_files(
                    self.snapshot_source, self.snapshot_target
                ).to_dict()
            except (OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
                final_evaluation["snapshot_compatibility"] = {
                    "compatible": False,
                    "errors": [f"snapshot validation failed: {exc}"],
                    "methods_checked": 0,
                    "methods_covered": 0,
                    "values_checked": 0,
                    "coverage": 0.0,
                    "available": False,
                }
        elif self.snapshot_validation:
            final_evaluation["snapshot_compatibility"] = {
                "compatible": None,
                "errors": [],
                "methods_checked": 0,
                "methods_covered": 0,
                "values_checked": 0,
                "coverage": 0.0,
                "available": False,
            }
        stubbed_fragments = {
            fragment_id
            for fragment_id, record in self.store.records.items()
            if record.get("stubbed")
        }
        add_coarse_method_metrics(final_evaluation, project, stubbed_fragments)
        self.store.mark_stage("final_evaluation")
        Project.save(project, self.graph_dir)
        report = self.store.write_report(
            self._config(), final_evaluation, self._current_elapsed()
        )
        print(
            "Oxidizer-style baseline complete: "
            f"Compile@budget={report['compile_at_budget']['count']}/{report['fragment_count']}, "
            f"stubs={report['stub_count']}, "
            f"operational_link={final_evaluation['operational_link_success']}"
        )
        return project

    def _translate_headers(self, project: Project) -> None:
        if self.store.stage_complete("headers"):
            print("========== Oxidizer-style headers: resumed from checkpoint ==========")
            return

        print("========== Oxidizer-style: feature-mapped header fragments ==========")
        source_headers = [header for header in project.headers if not header.is_generated_external()]
        for group in header_dependency_groups(source_headers):
            peer_summary = "\n".join(f"- {header.key}" for header in group)
            for header in group:
                fragment_id = self._header_fragment_id(header)
                if self.store.is_complete(fragment_id):
                    continue
                record = self._translate_header(project, header, group, peer_summary)
                Project.save(project, self.graph_dir)
                self.store.save_fragment(record)
                self.store.write_report(self._config(), None, self._current_elapsed())

        self.store.mark_stage("headers")
        Project.save(project, self.graph_dir)

    def _translate_header(
        self,
        project: Project,
        header: Header,
        peers: list[Header],
        peer_summary: str,
    ) -> FragmentRecord:
        """翻译单个头文件片段。

        参数：project 为累计项目，header 为当前片段，peers 为同一依赖组，
        peer_summary 为组内声明摘要。返回包含尝试历史和最终状态的片段记录。
        预算耗尽时保留最后一个可解析候选，仅在没有候选时生成兜底 stub。
        """
        started = time.monotonic()
        fragment_id = self._header_fragment_id(header)
        source = self._header_source(header)
        rules = applicable_rules(source, "header")
        attempts: list[AttemptRecord] = []
        query_count = 0
        first_checked = False
        first_syntax = False
        first_compile = False
        first_type_compatible = False
        type_checked = False
        final_syntax = False
        final_compile = False
        final_type_compatible = False
        feedback = ""
        accepted = False
        feature_failures = 0
        feature_budget_exhausted = False
        last_candidate = ""
        last_candidate_output = ""

        for compile_try in range(1, self.fragment_max_tries + 1):
            candidate = ""
            candidate_output = ""
            successful_feature_try = 0
            feature_try = 0
            while True:
                feature_try += 1
                prompt = header_prompt(
                    source,
                    header.get_output_header_name(),
                    self._header_dependency_summary(header, project.headers, peers),
                    peer_summary,
                    rules,
                    feedback,
                )
                candidate_output = self._query(
                    prompt, fragment_id, "header", compile_try, feature_try
                )
                query_count += 1
                try:
                    candidate = self._parse_header_output(candidate_output)
                    last_candidate = self._ensure_header_guard(candidate)
                    last_candidate_output = candidate_output
                    failures = validate_rules(rules, source, candidate, "header")
                except Exception as exc:
                    failures = [f"output-format: {exc}"]
                    candidate = ""

                if failures:
                    attempts.append(
                        AttemptRecord(
                            compile_try=compile_try,
                            feature_try=feature_try,
                            rules_ok=False,
                            rule_failures=failures,
                        )
                    )
                    feedback = "Feature mapping validation failed:\n" + "\n".join(failures)
                    feature_failures += 1
                    if feature_failures >= self.feature_requery_budget:
                        feature_budget_exhausted = True
                        break
                    continue
                successful_feature_try = feature_try
                break

            if feature_budget_exhausted or not candidate:
                break

            previous_code = header.translated_code
            header.raw_translated_code = candidate_output
            header.translated_code = self._ensure_header_guard(candidate)

            compatibility = (
                check_header_compatibility(source, header.translated_code)
                if self.type_compatibility
                else None
            )
            if compatibility is not None:
                if not type_checked:
                    type_checked = True
                    first_type_compatible = compatibility.compatible
                final_type_compatible = compatibility.compatible
                if not compatibility.compatible:
                    attempts.append(
                        AttemptRecord(
                            compile_try=compile_try,
                            feature_try=successful_feature_try,
                            rules_ok=True,
                            type_compatible=False,
                            type_errors=compatibility.errors,
                        )
                    )
                    header.translated_code = previous_code
                    feedback = self._type_feedback(compatibility.errors)
                    continue

            syntax, compile_result = self._check_header_candidate(project, header)
            if not first_checked:
                first_checked = True
                first_syntax = syntax.success
                first_compile = compile_result.success
            final_syntax = syntax.success
            final_compile = compile_result.success
            attempts.append(
                AttemptRecord(
                    compile_try=compile_try,
                    feature_try=successful_feature_try,
                    rules_ok=True,
                    syntax_success=syntax.success,
                    compile_success=compile_result.success,
                    syntax_log=syntax.log,
                    compile_log=compile_result.log,
                )
            )
            self.compiler.write_fragment_logs(
                self.report_dir, fragment_id, compile_try, syntax, compile_result
            )
            if compile_result.success:
                header.latest_compile_status = "success"
                accepted = True
                break

            header.translated_code = previous_code
            feedback = self._compiler_feedback(syntax, compile_result)

        if not accepted:
            header.translated_code = last_candidate or self._header_stub(header)
            if last_candidate_output:
                header.raw_translated_code = last_candidate_output
            header.latest_compile_status = "stubbed"
            self._materialize(project, self.work_dir)

        return FragmentRecord(
            fragment_id=fragment_id,
            kind="header",
            owner=header.key,
            source_loc=self._source_loc(source),
            applicable_rules=[rule.rule_id for rule in rules],
            status="accepted" if accepted else "stubbed",
            attempts=attempts,
            query_count=query_count,
            first_syntax_success=first_syntax,
            first_compile_success=first_compile,
            first_type_compatible=first_type_compatible if type_checked else True,
            final_syntax_success=final_syntax,
            final_compile_success=final_compile,
            final_type_compatible=final_type_compatible if type_checked else True,
            stubbed=not accepted,
            elapsed_seconds=round(time.monotonic() - started, 3),
        )

    def _map_methods(self, project: Project) -> None:
        if self.store.stage_complete("method_mapping"):
            print("========== Oxidizer-style method mapping: resumed from checkpoint ==========")
            return

        print("========== Oxidizer-style: frozen method signature mapping ==========")
        for header in project.headers:
            if header.is_generated_external() or not header.methods:
                continue
            header_record = self.store.records.get(self._header_fragment_id(header), {})
            if header_record.get("stubbed"):
                self._mark_header_methods_unmapped(header, "owning header was stubbed")
                continue

            mapped = False
            last_error = ""
            compatibility_feedback = ""
            for attempt in range(1, self.feature_requery_budget + 1):
                prompt = self.mapping_step.build_prompt(
                    header, project.headers, compatibility_feedback
                )
                output = self._query(
                    prompt,
                    f"mapping:{header.key}",
                    "method_mapping",
                    attempt,
                    1,
                )
                self.store.record_aux_query()
                try:
                    json_str = get_json_str(output) or output
                    result = MethodMappingResult.model_validate_json(json_str)
                    warnings = self.mapping_step.apply_mapping(header, result)
                    compatibility_errors = (
                        check_method_mappings(header.methods, include_skipped=True)
                        if self.type_compatibility
                        else []
                    )
                    warnings.extend(
                        f"type-compatibility: {error}"
                        for error in compatibility_errors
                    )
                    self.mapping_step.save_mapping_report(
                        header, result, warnings, self.result_dir
                    )
                    if compatibility_errors:
                        last_error = "\n".join(compatibility_errors)
                        compatibility_feedback = (
                            "Static type-compatibility check failed for the mapping.\n"
                            + last_error
                        )
                        continue
                    mapped = True
                    break
                except Exception as exc:
                    last_error = str(exc)

            if not mapped:
                self._mark_header_methods_unmapped(
                    header, f"method mapping exhausted its budget: {last_error}"
                )
            Project.save(project, self.graph_dir)

        self.store.mark_stage("method_mapping")
        Project.save(project, self.graph_dir)

    def _translate_methods(self, project: Project) -> None:
        if self.store.stage_complete("methods"):
            print("========== Oxidizer-style methods: resumed from checkpoint ==========")
            return

        print("========== Oxidizer-style: feature-mapped method fragments ==========")
        methods = [
            method
            for header in project.headers
            if not header.is_generated_external()
            for method in header.methods
            if not method.is_added_method
        ]
        for group in method_dependency_groups(methods):
            peer_summary = "\n".join(
                f"- {method.key}: {method.translated_declaration or '(signature pending)'}"
                for method in group
            )
            for method in group:
                fragment_id = self._method_fragment_id(method)
                if self.store.is_complete(fragment_id):
                    continue

                if not self._needs_method_body(method):
                    record = self._record_nontranslated_method(method)
                else:
                    record = self._translate_method(project, method, group, peer_summary)
                Project.save(project, self.graph_dir)
                self.store.save_fragment(record)
                self.store.write_report(self._config(), None, self._current_elapsed())

        self.store.mark_stage("methods")
        Project.save(project, self.graph_dir)

    def _translate_method(
        self,
        project: Project,
        method: Method,
        peers: list[Method],
        peer_summary: str,
    ) -> FragmentRecord:
        """翻译单个方法片段。

        参数：project 为累计项目，method 为当前方法，peers 为同一依赖组，
        peer_summary 为组内签名摘要。返回包含尝试历史和最终状态的片段记录。
        预算耗尽时保留最后一个可解析方法候选，不将失败候选计为成功。
        """
        started = time.monotonic()
        fragment_id = self._method_fragment_id(method)
        rules = applicable_rules(method.code, "method")
        attempts: list[AttemptRecord] = []
        query_count = 0
        first_checked = False
        first_syntax = False
        first_compile = False
        signature_compatibility = (
            check_method_signature(
                method.key,
                method.code,
                method.translated_declaration or method.mapped_cpp_definition,
            )
            if self.type_compatibility
            and (method.translated_declaration or method.mapped_cpp_definition)
            else None
        )
        first_type_compatible = signature_compatibility is None or signature_compatibility.compatible
        final_type_compatible = first_type_compatible
        final_syntax = False
        final_compile = False
        feedback = ""
        accepted = False
        feature_failures = 0
        feature_budget_exhausted = False
        last_candidate = ""
        last_candidate_output = ""

        for compile_try in range(1, self.fragment_max_tries + 1):
            candidate = ""
            candidate_output = ""
            successful_feature_try = 0
            feature_try = 0
            while True:
                feature_try += 1
                prompt = method_prompt(
                    method.code,
                    self._truncate(method.header.translated_code, 10000),
                    method.translated_declaration or method.mapped_cpp_definition,
                    self._method_dependency_summary(method, peers),
                    peer_summary,
                    rules,
                    feedback,
                )
                candidate_output = self._query(
                    prompt, fragment_id, "method", compile_try, feature_try
                )
                query_count += 1
                try:
                    candidate = self._parse_method_output(candidate_output)
                    last_candidate = candidate
                    last_candidate_output = candidate_output
                    previous = method.translated_code
                    method.translated_code = candidate
                    matches = looks_like_expected_method(method)
                    method.translated_code = previous
                    failures = validate_rules(rules, method.code, candidate, "method")
                    if not matches:
                        failures.insert(0, "signature: target definition does not match the frozen declaration")
                except Exception as exc:
                    failures = [f"output-format: {exc}"]
                    candidate = ""

                if failures:
                    attempts.append(
                        AttemptRecord(
                            compile_try=compile_try,
                            feature_try=feature_try,
                            rules_ok=False,
                            rule_failures=failures,
                        )
                    )
                    feedback = "Feature mapping validation failed:\n" + "\n".join(failures)
                    feature_failures += 1
                    if feature_failures >= self.feature_requery_budget:
                        feature_budget_exhausted = True
                        break
                    continue
                successful_feature_try = feature_try
                break

            if feature_budget_exhausted or not candidate:
                break

            if signature_compatibility is not None and not signature_compatibility.compatible:
                attempts.append(
                    AttemptRecord(
                        compile_try=compile_try,
                        feature_try=successful_feature_try,
                        rules_ok=True,
                        type_compatible=False,
                        type_errors=signature_compatibility.errors,
                    )
                )
                final_type_compatible = False
                feedback = self._type_feedback(signature_compatibility.errors)
                continue

            previous_code = method.translated_code
            method.raw_translated_code = candidate_output
            method.translated_code = candidate
            syntax, compile_result = self._check_method_candidate(project, method)
            if not first_checked:
                first_checked = True
                first_syntax = syntax.success
                first_compile = compile_result.success
            final_syntax = syntax.success
            final_compile = compile_result.success
            attempts.append(
                AttemptRecord(
                    compile_try=compile_try,
                    feature_try=successful_feature_try,
                    rules_ok=True,
                    syntax_success=syntax.success,
                    compile_success=compile_result.success,
                    syntax_log=syntax.log,
                    compile_log=compile_result.log,
                )
            )
            self.compiler.write_fragment_logs(
                self.report_dir, fragment_id, compile_try, syntax, compile_result
            )
            if compile_result.success:
                accepted = True
                method.compile_output = ""
                break

            method.translated_code = previous_code
            method.compile_output = compile_result.log or syntax.log
            feedback = self._compiler_feedback(syntax, compile_result)

        if not accepted:
            method.translated_code = last_candidate or self._method_stub(method)
            if last_candidate_output:
                method.raw_translated_code = last_candidate_output
            method.skip_translation = False
            method.skip_translation_reason = (
                "Oxidizer budget exhausted; last parseable candidate retained"
                if last_candidate
                else "Oxidizer budget exhausted; no parseable candidate, fallback stub inserted"
            )
            self._materialize(project, self.work_dir)

        return FragmentRecord(
            fragment_id=fragment_id,
            kind="method",
            owner=method.header.key,
            source_loc=self._source_loc(method.code),
            applicable_rules=[rule.rule_id for rule in rules],
            status="accepted" if accepted else "stubbed",
            attempts=attempts,
            query_count=query_count,
            first_syntax_success=first_syntax,
            first_compile_success=first_compile,
            first_type_compatible=first_type_compatible,
            final_syntax_success=final_syntax,
            final_compile_success=final_compile,
            final_type_compatible=final_type_compatible,
            stubbed=not accepted,
            elapsed_seconds=round(time.monotonic() - started, 3),
        )

    def _record_nontranslated_method(self, method: Method) -> FragmentRecord:
        accepted_statuses = {
            "already_implemented",
            "pure_virtual",
            "defaulted_or_deleted",
        }
        accepted = method.mapping_status in accepted_statuses
        return FragmentRecord(
            fragment_id=self._method_fragment_id(method),
            kind="method",
            owner=method.header.key,
            source_loc=self._source_loc(method.code),
            applicable_rules=[
                rule.rule_id for rule in applicable_rules(method.code, "method")
            ],
            status="accepted" if accepted else "stubbed",
            first_syntax_success=accepted,
            first_compile_success=accepted,
            first_type_compatible=accepted,
            final_syntax_success=accepted,
            final_compile_success=accepted,
            final_type_compatible=accepted,
            stubbed=not accepted,
        )

    def _check_header_candidate(self, project: Project, header: Header) -> tuple[CheckResult, CheckResult]:
        self._materialize(project, self.work_dir)
        source, temporary = self.compiler.source_for_fragment(
            header.get_output_header_name(),
            header.get_output_cpp_name(),
            self.work_dir,
            in_header=True,
        )
        try:
            syntax = self.compiler.check_syntax(source, self.work_dir)
            compile_result = (
                self.compiler.check_object(source, self.work_dir)
                if syntax.success
                else CheckResult(False, syntax.log)
            )
            return syntax, compile_result
        finally:
            if temporary and source.exists():
                source.unlink()

    def _check_method_candidate(self, project: Project, method: Method) -> tuple[CheckResult, CheckResult]:
        self._materialize(project, self.work_dir)
        in_header = method.method_body_location == "header"
        source, temporary = self.compiler.source_for_fragment(
            method.header.get_output_header_name(),
            method.header.get_output_cpp_name(),
            self.work_dir,
            in_header=in_header,
        )
        try:
            syntax = self.compiler.check_syntax(source, self.work_dir)
            compile_result = (
                self.compiler.check_object(source, self.work_dir)
                if syntax.success
                else CheckResult(False, syntax.log)
            )
            return syntax, compile_result
        finally:
            if temporary and source.exists():
                source.unlink()

    def _materialize(self, project: Project, target: Path) -> None:
        target.mkdir(parents=True, exist_ok=True)
        self.file_generator.generate_files(
            self.ai_name, self.project_name, version, target, project
        )
        for header in project.headers:
            if header.translated_code.strip():
                continue
            for artifact_name in (header.get_output_header_name(), header.get_output_cpp_name()):
                artifact = target / artifact_name
                if artifact.exists():
                    artifact.unlink()

    def _query(
        self,
        prompt: str,
        fragment_id: str,
        phase: str,
        compile_try: int,
        feature_try: int,
    ) -> str:
        started = time.monotonic()
        output = ""
        error = ""
        try:
            output = self.generator.generate(prompt, require_valid_json=True)[0]
            return output
        except Exception as exc:
            error = str(exc)
            return ""
        finally:
            # On failure last_usage may be stale from a previous call; only
            # attribute usage to successful queries.
            usage = (getattr(self.generator, "last_usage", None) or {}) if not error else {}
            self.store.trace(
                {
                    "fragment_id": fragment_id,
                    "phase": phase,
                    "compile_try": compile_try,
                    "feature_try": feature_try,
                    "model": getattr(self.generator, "model_name", self.ai_name),
                    "temperature": getattr(self.generator, "temperature", None),
                    "elapsed_seconds": round(time.monotonic() - started, 3),
                    "prompt_tokens": usage.get("prompt_tokens"),
                    "completion_tokens": usage.get("completion_tokens"),
                    "total_tokens": usage.get("total_tokens"),
                    "cached_tokens": usage.get("cached_tokens"),
                    "prompt": prompt,
                    "response": output,
                    "error": error,
                }
            )

    def _header_dependency_summary(
        self, header: Header, headers: list[Header], peers: list[Header]
    ) -> str:
        peer_keys = {peer.key for peer in peers}
        dependency_names = {
            header.parent_class.split(".")[-1] if header.parent_class else "",
            *(interface.split(".")[-1] for interface in header.interfaces),
            *(imp.split(".")[-1] for imp in header.imports),
        }
        sections: list[str] = []
        for candidate in headers:
            if candidate.key in peer_keys or not candidate.translated_code.strip():
                continue
            names = {candidate.key, candidate.key.split(".")[-1], candidate.key.split("$")[-1]}
            if dependency_names & names:
                sections.append(
                    f"Header {candidate.get_output_header_name()}:\n```cpp\n"
                    f"{self._truncate(candidate.translated_code, 6000)}\n```"
                )
        return "\n\n".join(sections)

    def _method_dependency_summary(self, method: Method, peers: list[Method]) -> str:
        peer_keys = {peer.key for peer in peers}
        lines = []
        for child in sorted(method.children, key=lambda item: item.key):
            if child.key in peer_keys:
                continue
            declaration = child.translated_declaration or child.mapped_cpp_definition
            if declaration:
                lines.append(f"- {child.key} -> {declaration}")
        return "\n".join(lines)

    def _parse_header_output(self, output: str) -> str:
        json_str = get_json_str(output) or output
        data = json.loads(json_str)
        code = data.get("translated_header")
        if not isinstance(code, str) or not code.strip():
            raise ValueError("translated_header is missing or empty")
        return code.strip()

    @staticmethod
    def _header_source(header: Header) -> str:
        imports = "\n".join(f"import {item};" for item in header.imports)
        return f"{imports}\n{header.source_code}".strip()

    def _parse_method_output(self, output: str) -> str:
        json_str = get_json_str(output) or output
        data = json.loads(json_str)
        code = data.get("complete_translated_code")
        if not isinstance(code, str) or not code.strip():
            raise ValueError("complete_translated_code is missing or empty")
        return code.strip()

    def _header_stub(self, header: Header) -> str:
        name = re.sub(r"[^A-Za-z0-9_]", "_", header.key.split("$")[-1].split(".")[-1])
        if header.type == "enum":
            declaration = f"enum class {name} {{ OxidizerUntranslated }};"
        elif header.type == "interface":
            declaration = f"class {name} {{\npublic:\n    virtual ~{name}() = default;\n}};"
        else:
            declaration = f"class {name} {{\npublic:\n    {name}() = default;\n}};"
        return "#pragma once\n\n" + declaration + "\n"

    def _method_stub(self, method: Method) -> str:
        declaration = (method.translated_declaration or method.mapped_cpp_definition).strip()
        declaration = declaration.rstrip(";").strip()
        declaration = re.sub(r"\s*=\s*(?:0|default|delete)\s*$", "", declaration)
        declaration = re.sub(r"\b(?:virtual|static|override)\b", "", declaration)
        declaration = re.sub(r"\s+", " ", declaration).strip()
        if not declaration:
            return "#include <stdexcept>\nvoid oxidizer_untranslated_method() { throw std::runtime_error(\"untranslated\"); }"

        method_name = method.get_name()
        if method_name == "<init>":
            method_name = method.header.translated_class_name.split("::")[-1]
        if "::" not in declaration.split("(", 1)[0]:
            declaration = re.sub(
                rf"\b{re.escape(method_name)}\s*\(",
                f"{method.header.translated_class_name}::{method_name}(",
                declaration,
                count=1,
            )
        is_destructor = f"~{method.header.translated_class_name.split('::')[-1]}" in declaration
        if is_destructor:
            body = "{}"
        else:
            body = '{ throw std::runtime_error("Oxidizer untranslated method"); }'
        return f"#include <stdexcept>\n{declaration} {body}"

    def _mark_header_methods_unmapped(self, header: Header, reason: str) -> None:
        for method in header.methods:
            method.mapping_status = "unmapped"
            method.method_body_location = "none"
            method.skip_translation = True
            method.skip_translation_reason = reason

    @staticmethod
    def _needs_method_body(method: Method) -> bool:
        return (
            not method.is_deleted_method
            and not method.skip_translation
            and method.method_body_location in {"header", "cpp"}
            and bool(method.translated_declaration or method.mapped_cpp_definition)
        )

    @staticmethod
    def _ensure_header_guard(code: str) -> str:
        return code if "#pragma once" in code else "#pragma once\n" + code

    @staticmethod
    def _compiler_feedback(syntax: CheckResult, compile_result: CheckResult) -> str:
        if not syntax.success:
            return "Clang syntax-only check failed:\n" + syntax.log[:8000]
        return "Clang object compilation failed:\n" + compile_result.log[:8000]

    @staticmethod
    def _type_feedback(errors: list[str]) -> str:
        return "Static type-compatibility check failed:\n" + "\n".join(errors[:50])

    @staticmethod
    def _source_loc(source: str) -> int:
        return sum(1 for line in source.splitlines() if line.strip())

    @staticmethod
    def _truncate(text: str, limit: int) -> str:
        return text if len(text) <= limit else text[:limit] + "\n...[truncated]"

    @staticmethod
    def _header_fragment_id(header: Header) -> str:
        return f"header:{header.key}"

    @staticmethod
    def _method_fragment_id(method: Method) -> str:
        return f"method:{method.key}"

    def _config(self) -> dict[str, Any]:
        return {
            "approach": "oxidizer-style-type-driven",
            "source_language": "Java",
            "target_language": "C++17",
            "ai_name": self.ai_name,
            "model": getattr(self.generator, "model_name", self.ai_name),
            "temperature": getattr(self.generator, "temperature", None),
            "project": self.project_name,
            "run_id": self.run_id,
            "feature_requery_budget": self.feature_requery_budget,
            "fragment_max_tries": self.fragment_max_tries,
            "compile_timeout": self.compile_timeout,
            "compiler": "clang++",
            "compiler_version": self.compiler_version,
            "semantic_validation": False,
            "type_compatibility": self.type_compatibility,
            "type_compatibility_mode": "static-signature-and-header-shape",
            "snapshot_validation": self.snapshot_validation,
            "snapshot_source": str(self.snapshot_source) if self.snapshot_source else None,
            "snapshot_target": str(self.snapshot_target) if self.snapshot_target else None,
        }

    def _current_elapsed(self) -> float:
        current = time.monotonic() - self._run_started if self._run_started else 0.0
        return self._elapsed_before_run + current
