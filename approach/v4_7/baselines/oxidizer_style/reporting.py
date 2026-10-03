from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .models import FragmentRecord


class OxidizerReportStore:
    STATE_VERSION = 1

    def __init__(self, result_dir: Path):
        self.result_dir = Path(result_dir)
        self.result_dir.mkdir(parents=True, exist_ok=True)
        self.state_path = self.result_dir / "oxidizer_state.json"
        self.fragments_path = self.result_dir / "fragments.jsonl"
        self.trace_path = self.result_dir / "llm_trace.jsonl"
        self.report_path = self.result_dir / "oxidizer_report.json"
        self.state = self._load_state()
        self.records = self._load_records()

    def is_complete(self, fragment_id: str) -> bool:
        return fragment_id in self.state["completed_fragments"]

    def stage_complete(self, stage: str) -> bool:
        return bool(self.state["stages"].get(stage))

    def mark_stage(self, stage: str) -> None:
        self.state["stages"][stage] = True
        self._write_state()

    def record_aux_query(self) -> None:
        self.state["aux_query_count"] = int(self.state.get("aux_query_count", 0)) + 1
        self._write_state()

    def save_fragment(self, record: FragmentRecord) -> None:
        data = record.to_dict()
        self.records[record.fragment_id] = data
        self.state["completed_fragments"][record.fragment_id] = {
            "status": record.status,
            "stubbed": record.stubbed,
        }
        self._rewrite_fragments()
        self._write_state()

    def trace(self, entry: dict[str, Any]) -> None:
        with open(self.trace_path, "a", encoding="utf-8") as stream:
            stream.write(json.dumps(entry, ensure_ascii=False) + "\n")

    def write_report(self, config: dict, final_evaluation: dict | None, elapsed_seconds: float) -> dict:
        records = list(self.records.values())
        total = len(records)
        total_loc = sum(record["source_loc"] for record in records)

        def metric(key: str, selected: list[dict] | None = None) -> dict:
            selected = records if selected is None else selected
            selected_total = len(selected)
            selected_loc = sum(record["source_loc"] for record in selected)
            matching = [record for record in selected if record[key]]
            matching_loc = sum(record["source_loc"] for record in matching)
            return {
                "count": len(matching),
                "total": selected_total,
                "rate": len(matching) / selected_total if selected_total else 0.0,
                "source_loc": matching_loc,
                "total_source_loc": selected_loc,
                "source_loc_rate": matching_loc / selected_loc if selected_loc else 0.0,
            }

        def metric_set(selected: list[dict]) -> dict:
            return {
                "syntax_at_1": metric("first_syntax_success", selected),
                "syntax_at_budget": metric("final_syntax_success", selected),
                "compile_at_1": metric("first_compile_success", selected),
                "compile_at_budget": metric("final_compile_success", selected),
            }

        def compatibility_metric(key: str, selected: list[dict] | None = None) -> dict:
            selected = records if selected is None else selected
            selected_loc = sum(record["source_loc"] for record in selected)
            matching = [record for record in selected if record.get(key, True)]
            matching_loc = sum(record["source_loc"] for record in matching)
            return {
                "count": len(matching),
                "total": len(selected),
                "rate": len(matching) / len(selected) if selected else 0.0,
                "source_loc": matching_loc,
                "total_source_loc": selected_loc,
                "source_loc_rate": matching_loc / selected_loc if selected_loc else 0.0,
            }

        fragment_query_total = sum(record["query_count"] for record in records)
        aux_query_total = int(self.state.get("aux_query_count", 0))
        query_total = fragment_query_total + aux_query_total
        stub_count = sum(1 for record in records if record["stubbed"])
        syntax_at_budget = metric("final_syntax_success")
        compile_at_budget = metric("final_compile_success")
        budget = int(config.get("fragment_max_tries", 15))
        report = {
            "config": config,
            "status": "complete" if self.stage_complete("final_evaluation") else "in_progress",
            "fragment_count": total,
            "source_loc": total_loc,
            "fragment_budget": budget,
            "syntax_at_1": metric("first_syntax_success"),
            "syntax_at_budget": syntax_at_budget,
            "compile_at_1": metric("first_compile_success"),
            "compile_at_budget": compile_at_budget,
            "type_compatibility_at_1": compatibility_metric("first_type_compatible"),
            "type_compatibility_at_budget": compatibility_metric("final_type_compatible"),
            "fragment_metrics": {
                "all": metric_set(records),
                "header": metric_set([record for record in records if record["kind"] == "header"]),
                "method": metric_set([record for record in records if record["kind"] == "method"]),
            },
            "stub_count": stub_count,
            "stub_rate": stub_count / total if total else 0.0,
            "query_count": query_total,
            "fragment_query_count": fragment_query_total,
            "aux_query_count": aux_query_total,
            "average_queries_per_fragment": fragment_query_total / total if total else 0.0,
            "elapsed_seconds": round(elapsed_seconds, 3),
            "token_usage": self._token_stats(),
            "final_evaluation": final_evaluation,
        }
        snapshot = (final_evaluation or {}).get("snapshot_compatibility")
        if snapshot is not None:
            report["snapshot_compatibility"] = snapshot
        report[f"syntax_at_{budget}"] = syntax_at_budget
        report[f"compile_at_{budget}"] = compile_at_budget
        if budget == 15:
            report["syntax_at_15"] = syntax_at_budget
            report["compile_at_15"] = compile_at_budget
        self.report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        return report

    def _token_stats(self) -> dict:
        """Aggregate per-call token usage and LLM time from llm_trace.jsonl.

        Entries written before usage tracking was introduced (or by failed
        calls) lack token fields and are counted under calls_without_usage.
        """
        stats: dict[str, Any] = {
            "calls_with_usage": 0,
            "calls_without_usage": 0,
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
            "cached_tokens": 0,
            "llm_elapsed_seconds": 0.0,
        }
        if not self.trace_path.exists():
            return stats
        for line in self.trace_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            stats["llm_elapsed_seconds"] += float(entry.get("elapsed_seconds") or 0.0)
            if entry.get("total_tokens") is None:
                stats["calls_without_usage"] += 1
                continue
            stats["calls_with_usage"] += 1
            stats["prompt_tokens"] += int(entry.get("prompt_tokens") or 0)
            stats["completion_tokens"] += int(entry.get("completion_tokens") or 0)
            stats["total_tokens"] += int(entry.get("total_tokens") or 0)
            stats["cached_tokens"] += int(entry.get("cached_tokens") or 0)
        stats["llm_elapsed_seconds"] = round(stats["llm_elapsed_seconds"], 3)
        return stats

    def previous_elapsed_seconds(self) -> float:
        if not self.report_path.exists():
            return 0.0
        try:
            return float(json.loads(self.report_path.read_text(encoding="utf-8")).get("elapsed_seconds", 0.0))
        except (OSError, TypeError, ValueError, json.JSONDecodeError):
            return 0.0

    def _load_state(self) -> dict:
        if not self.state_path.exists():
            return {
                "version": self.STATE_VERSION,
                "stages": {},
                "completed_fragments": {},
            }
        state = json.loads(self.state_path.read_text(encoding="utf-8"))
        if state.get("version") != self.STATE_VERSION:
            raise RuntimeError("unsupported oxidizer state version")
        state.setdefault("stages", {})
        state.setdefault("completed_fragments", {})
        return state

    def _load_records(self) -> dict[str, dict]:
        records: dict[str, dict] = {}
        if not self.fragments_path.exists():
            return records
        for line in self.fragments_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            data = json.loads(line)
            records[data["fragment_id"]] = data
        return records

    def _rewrite_fragments(self) -> None:
        with open(self.fragments_path, "w", encoding="utf-8") as stream:
            for fragment_id in sorted(self.records):
                stream.write(json.dumps(self.records[fragment_id], ensure_ascii=False) + "\n")

    def _write_state(self) -> None:
        self.state_path.write_text(json.dumps(self.state, ensure_ascii=False, indent=2), encoding="utf-8")
