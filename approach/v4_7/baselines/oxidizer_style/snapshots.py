"""Snapshot compatibility protocol for the Oxidizer type-driven phase.

The runner is deliberately separate from this module. Java and C++ probes can
write the same JSON schema, after which this module performs the deterministic
part of the paper's round-trip check.
"""

from __future__ import annotations

import json
import math
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterable


def canonicalize_json(value: Any) -> Any:
    """Return JSON data with stable object order and numeric representation."""
    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("JSON does not permit NaN or Infinity")
        if value == 0:
            return 0
        if value.is_integer():
            return int(value)
        return value
    if isinstance(value, dict):
        return {str(key): canonicalize_json(value[key]) for key in sorted(value, key=str)}
    if isinstance(value, (list, tuple)):
        return [canonicalize_json(item) for item in value]
    raise TypeError(f"unsupported JSON value: {type(value).__name__}")


def canonical_json(value: Any) -> str:
    return json.dumps(
        canonicalize_json(value),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


@dataclass
class SnapshotValue:
    type: str
    value: Any = None
    json: Any = None

    def json_value(self) -> Any:
        return self.value if self.json is None else self.json

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SnapshotValue":
        return cls(str(data.get("type", "unknown")), data.get("value"), data.get("json"))


@dataclass
class MethodSnapshot:
    method: str
    receiver: SnapshotValue | None = None
    arguments: list[SnapshotValue] = field(default_factory=list)
    return_value: SnapshotValue | None = None
    source: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["return"] = data.pop("return_value")
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MethodSnapshot":
        receiver = data.get("receiver")
        result = data.get("return", data.get("return_value"))
        return cls(
            method=str(data["method"]),
            receiver=SnapshotValue.from_dict(receiver) if receiver else None,
            arguments=[SnapshotValue.from_dict(item) for item in data.get("arguments", [])],
            return_value=SnapshotValue.from_dict(result) if result else None,
            source=dict(data.get("source", {})),
        )


@dataclass
class SnapshotSet:
    snapshots: list[MethodSnapshot] = field(default_factory=list)

    @classmethod
    def from_json(cls, data: Any) -> "SnapshotSet":
        if isinstance(data, dict):
            data = data.get("snapshots", [])
        if not isinstance(data, list):
            raise ValueError("snapshot file must contain a list or {snapshots: [...]}")
        return cls([MethodSnapshot.from_dict(item) for item in data])

    @classmethod
    def load(cls, path: Path) -> "SnapshotSet":
        return cls.from_json(json.loads(Path(path).read_text(encoding="utf-8")))


@dataclass
class SnapshotCompatibility:
    compatible: bool
    errors: list[str] = field(default_factory=list)
    methods_checked: int = 0
    methods_covered: int = 0
    values_checked: int = 0

    @property
    def coverage(self) -> float:
        return self.methods_covered / self.methods_checked if self.methods_checked else 0.0

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["coverage"] = self.coverage
        data["available"] = True
        return data


def compare_snapshot_value(source: SnapshotValue, target: SnapshotValue, path: str) -> list[str]:
    errors: list[str] = []
    if source.type != target.type:
        # Primitive width aliases are allowed when their JSON value is equal;
        # value equality is the observable part of this phase.
        numeric = {"byte", "short", "int", "long", "float", "double", "number"}
        if source.type not in numeric or target.type not in numeric:
            errors.append(f"{path}: type {source.type} != {target.type}")
    try:
        if canonical_json(source.json_value()) != canonical_json(target.json_value()):
            errors.append(f"{path}: canonical JSON differs")
    except (TypeError, ValueError) as exc:
        errors.append(f"{path}: invalid JSON: {exc}")
    return errors


def check_snapshot_round_trip(source: SnapshotSet, target: SnapshotSet) -> SnapshotCompatibility:
    """Check source->target and target->source observable JSON round trips."""
    source_by_method = {item.method: item for item in source.snapshots}
    target_by_method = {item.method: item for item in target.snapshots}
    methods = sorted(set(source_by_method) | set(target_by_method))
    errors: list[str] = []
    covered = 0
    values = 0
    for method in methods:
        left, right = source_by_method.get(method), target_by_method.get(method)
        if left is None or right is None:
            errors.append(f"{method}: missing snapshot coverage")
            continue
        covered += 1
        if len(left.arguments) != len(right.arguments):
            errors.append(f"{method}: argument count differs")
        for index, (source_arg, target_arg) in enumerate(zip(left.arguments, right.arguments)):
            errors.extend(compare_snapshot_value(source_arg, target_arg, f"{method}.arg[{index}]"))
            values += 1
        if left.receiver and right.receiver:
            errors.extend(compare_snapshot_value(left.receiver, right.receiver, f"{method}.receiver"))
            values += 1
        elif left.receiver or right.receiver:
            errors.append(f"{method}: receiver nullability differs")
        if left.return_value and right.return_value:
            errors.extend(compare_snapshot_value(left.return_value, right.return_value, f"{method}.return"))
            values += 1
        elif left.return_value or right.return_value:
            errors.append(f"{method}: return nullability differs")
    return SnapshotCompatibility(not errors, errors, len(methods), covered, values)


def check_snapshot_files(source_path: Path, target_path: Path) -> SnapshotCompatibility:
    return check_snapshot_round_trip(SnapshotSet.load(source_path), SnapshotSet.load(target_path))
