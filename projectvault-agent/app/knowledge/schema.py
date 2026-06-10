"""Lightweight graph schema helpers."""

from __future__ import annotations

import re
from enum import Enum
from typing import Any


class NodeType(str, Enum):
    PROJECT = "Project"
    FILE = "File"
    CONCEPT = "Concept"
    TASK = "Task"
    ERROR = "Error"
    DECISION = "Decision"
    REQUIREMENT = "Requirement"


NODE_TYPE_LABELS = {
    NodeType.PROJECT.value: "프로젝트",
    NodeType.FILE.value: "파일",
    NodeType.CONCEPT.value: "개념",
    NodeType.TASK.value: "할 일",
    NodeType.ERROR.value: "오류",
    NodeType.DECISION.value: "결정사항",
    NodeType.REQUIREMENT.value: "요구사항",
}


class EdgeType(str, Enum):
    CONTAINS = "CONTAINS"
    MENTIONS = "MENTIONS"
    REQUIRES = "REQUIRES"
    OCCURS_IN = "OCCURS_IN"
    FIXES = "FIXES"
    AFFECTS = "AFFECTS"
    DEPENDS_ON = "DEPENDS_ON"
    SUPPORTS = "SUPPORTS"


NODE_TYPES = {node_type.value for node_type in NodeType}
EDGE_TYPES = {edge_type.value for edge_type in EdgeType}


def make_node(
    node_id: str,
    label: str,
    node_type: NodeType,
    properties: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "id": node_id,
        "label": label,
        "type": node_type.value,
        "type_label": NODE_TYPE_LABELS[node_type.value],
        "properties": properties or {},
    }


def make_edge(
    source: str,
    target: str,
    relation: EdgeType,
    properties: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "source": source,
        "target": target,
        "relation": relation.value,
        "properties": properties or {},
    }


def node_id(node_type: NodeType, label: str) -> str:
    return f"{node_type.value.lower()}:{slugify(label)}"


def slugify(value: str) -> str:
    normalized = value.strip().lower()
    normalized = normalized.replace("/", "_").replace("\\", "_")
    normalized = re.sub(r"\s+", "_", normalized)
    normalized = re.sub(r"[^0-9a-zA-Z가-힣._-]+", "_", normalized)
    normalized = re.sub(r"_+", "_", normalized).strip("._-")
    return normalized[:100] or "item"


def safe_filename(value: str) -> str:
    filename = value.strip().replace("/", "_").replace("\\", "_")
    filename = re.sub(r"[:*?\"<>|#^\[\]\n\r\t]+", "_", filename)
    filename = re.sub(r"\s+", "_", filename)
    filename = re.sub(r"_+", "_", filename).strip("._ ")
    return filename[:120] or "note"
