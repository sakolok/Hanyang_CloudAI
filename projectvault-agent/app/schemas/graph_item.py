"""Knowledge graph schemas."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import TypeVar


@dataclass
class GraphNode:
    id: str
    type: str
    label: str
    properties: dict[str, str] = field(default_factory=dict)


@dataclass
class GraphEdge:
    source: str
    target: str
    type: str
    properties: dict[str, str] = field(default_factory=dict)


@dataclass
class KnowledgeGraph:
    nodes: list[GraphNode] = field(default_factory=list)
    edges: list[GraphEdge] = field(default_factory=list)


@dataclass
class ConceptItem:
    name: str
    description: str = ""


@dataclass
class RequirementItem:
    title: str
    source: str = ""


@dataclass
class TaskItem:
    title: str
    priority: str = "MEDIUM"
    reason: str = ""


@dataclass
class ErrorItem:
    title: str
    reason: str = ""


@dataclass
class DecisionItem:
    title: str
    reason: str = ""


@dataclass
class FileAnalysisResult:
    file_path: str
    file_type: str
    summary: str
    concepts: list[ConceptItem] = field(default_factory=list)
    requirements: list[RequirementItem] = field(default_factory=list)
    tasks: list[TaskItem] = field(default_factory=list)
    errors: list[ErrorItem] = field(default_factory=list)
    decisions: list[DecisionItem] = field(default_factory=list)

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> "FileAnalysisResult":
        return cls(
            file_path=str(payload.get("file_path", "")),
            file_type=str(payload.get("file_type", "document")),
            summary=str(payload.get("summary", "")),
            concepts=_items(payload.get("concepts"), ConceptItem),
            requirements=_items(payload.get("requirements"), RequirementItem),
            tasks=_items(payload.get("tasks"), TaskItem),
            errors=_items(payload.get("errors"), ErrorItem),
            decisions=_items(payload.get("decisions"), DecisionItem),
        )

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


T = TypeVar("T")


def _items(value: object, item_type: type[T]) -> list[T]:
    allowed_fields = item_type.__dataclass_fields__.keys()  # type: ignore[attr-defined]
    items: list[T] = []
    for item in _list_of_dicts(value):
        cleaned = {key: val for key, val in item.items() if key in allowed_fields}
        for key in allowed_fields:
            cleaned.setdefault(key, "")
        items.append(item_type(**cleaned))
    return items


def _list_of_dicts(value: object) -> list[dict[str, str]]:
    if not isinstance(value, list):
        return []

    items: list[dict[str, str]] = []
    for item in value:
        if isinstance(item, dict):
            items.append({str(key): str(val) for key, val in item.items()})
    return items
