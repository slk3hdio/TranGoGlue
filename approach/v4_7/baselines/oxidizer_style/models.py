from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal


FragmentKind = Literal["header", "method"]


@dataclass
class CheckResult:
    success: bool
    log: str = ""
    elapsed_seconds: float = 0.0


@dataclass
class AttemptRecord:
    compile_try: int
    feature_try: int
    rules_ok: bool
    rule_failures: list[str] = field(default_factory=list)
    syntax_success: bool = False
    compile_success: bool = False
    type_compatible: bool = True
    type_errors: list[str] = field(default_factory=list)
    syntax_log: str = ""
    compile_log: str = ""


@dataclass
class FragmentRecord:
    fragment_id: str
    kind: FragmentKind
    owner: str
    source_loc: int
    applicable_rules: list[str]
    status: Literal["accepted", "stubbed"]
    attempts: list[AttemptRecord] = field(default_factory=list)
    query_count: int = 0
    first_syntax_success: bool = False
    first_compile_success: bool = False
    first_type_compatible: bool = True
    final_syntax_success: bool = False
    final_compile_success: bool = False
    final_type_compatible: bool = True
    stubbed: bool = False
    elapsed_seconds: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
